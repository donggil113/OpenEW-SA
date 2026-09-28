#!/usr/bin/env python3
"""Read frozen composition diagnostics and render a small, source-backed table.

This program never evaluates RF data or changes the frozen PR87/V2 analyses.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from openew.paper3.wisig_v2.hashing import stable_digest

SEEDS = (829, 1829, 2829, 3829, 4829)
METHODS = ("T3A", "P2", "RX-NORM")
ORACLES = (
    "SAME_CLASS_EXCLUDED_ORACLE",
    "SAME_CLASS_ONLY_ORACLE",
    "TRANSMITTER_PURE_ORACLE",
)
FIELDS = ("protocol_id", "receiver_id", "seed", "method", "condition")
QUERY_METHOD = {"T3A": "t3a", "P2": "p2", "RX-NORM": "rx_norm"}


def file_sha(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def frozen_hash(path: Path, manifest: Path) -> str:
    data = json.loads(manifest.read_text(encoding="utf-8"))["files"]
    if isinstance(data, list):
        mapping = {row["relative_path"]: row["sha256"] for row in data}
    else:
        mapping = data
    expected = mapping.get(path.name)
    actual = file_sha(path)
    if expected != actual:
        raise ValueError(f"frozen source SHA mismatch or unlisted source: {path}")
    return actual


def aggregate(primary: pd.DataFrame, oracle: pd.DataFrame, *, receivers: int = 32,
              seeds: tuple[int, ...] = SEEDS) -> pd.DataFrame:
    """Receiver-equal means; one primary/oracle observation per receiver and seed."""
    required_primary = {"protocol_id", "receiver_id", "seed", "model",
                        "query_count", "macro_f1"}
    required_oracle = set(FIELDS) | {"query_count", "evaluable_query_count",
                                      "macro_f1", "evidence_category", "mean_peer_count"}
    if required_primary - set(primary) or required_oracle - set(oracle):
        raise ValueError("composition or primary table has missing required columns")
    natural = primary[primary.model.isin(("T3A", "P2", "RX_NORM"))].copy()
    natural["method"] = natural.model.replace({"RX_NORM": "RX-NORM"})
    natural["condition"] = "NATURAL"
    natural["evaluable_query_count"] = natural.query_count
    natural["mean_peer_count"] = np.nan
    natural["evidence_category"] = "DEPLOYABLE_METHOD"
    combined = pd.concat([natural, oracle], ignore_index=True)
    wanted = {(method, condition) for method in METHODS
              for condition in ("NATURAL", *ORACLES)}
    if set(zip(combined.method, combined.condition)) != wanted:
        raise ValueError("missing or unexpected composition method/condition")
    if combined.duplicated(FIELDS).any():
        raise ValueError("duplicate receiver/seed/method/condition")
    if set(combined.seed.astype(int)) != set(seeds):
        raise ValueError("unexpected seed set")
    if oracle.evidence_category.ne("ORACLE_DIAGNOSTIC").any():
        raise ValueError("oracle rows lack diagnostic labeling")
    if (combined.query_count <= 0).any() or (
        (combined.evaluable_query_count <= 0) |
        (combined.evaluable_query_count > combined.query_count)
    ).any():
        raise ValueError("invalid query coverage")
    if not np.isfinite(combined.macro_f1.to_numpy(dtype=float)).all():
        raise ValueError("nonfinite macro-F1")
    pair_counts = combined.groupby(["method", "condition"], sort=False).size()
    if not pair_counts.eq(receivers * len(seeds)).all():
        raise ValueError("incomplete receiver/seed grid")
    for _, part in combined.groupby(["method", "condition"], sort=False):
        if part.receiver_id.nunique() != receivers or (
            part.groupby("receiver_id").seed.nunique() != len(seeds)
        ).any():
            raise ValueError("receiver or seed omitted")
    query = combined.pivot(index=["protocol_id", "receiver_id", "seed"],
                           columns=["method", "condition"], values="query_count")
    if query.isna().any().any() or query.nunique(axis=1).ne(1).any():
        raise ValueError("composition conditions do not share query counts")
    if combined.groupby(["method", "condition"]).evaluable_query_count.sum().ne(
        combined.groupby(["method", "condition"]).query_count.sum()
    ).any():
        raise ValueError("condition lost query coverage; detailed subset audit required")
    result = []
    for (method, condition), part in combined.groupby(["method", "condition"], sort=True):
        by_rx = part.groupby("receiver_id", sort=True).macro_f1.mean()
        result.append({
            "method": method,
            "condition": condition,
            "receiver_count": int(part.receiver_id.nunique()),
            "seed_count": int(part.seed.nunique()),
            "query_records": int(part.query_count.sum()),
            "evaluable_query_records": int(part.evaluable_query_count.sum()),
            "query_coverage": float(part.evaluable_query_count.sum() / part.query_count.sum()),
            "receiver_equal_macro_f1": float(by_rx.mean()),
            "label_dependent": condition != "NATURAL",
            "source_bank": 128,
            "peer_policy": "P2 k=32; T3A/RX-NORM full 128" if condition == "NATURAL"
                           else "at most 32 label-selected peers",
            "mean_peer_count_min": float(part.mean_peer_count.min()) if condition != "NATURAL" else None,
            "mean_peer_count_max": float(part.mean_peer_count.max()) if condition != "NATURAL" else None,
        })
    return pd.DataFrame(result).sort_values(["method", "condition"]).reset_index(drop=True)


def verify_pr87_sources(oracle: pd.DataFrame, p2: pd.DataFrame,
                        tta: pd.DataFrame) -> None:
    """Check the archived PR87 concatenation against both of its frozen inputs."""
    combined = pd.concat([
        p2.assign(method="P2", evidence_category="ORACLE_DIAGNOSTIC"),
        tta,
    ], ignore_index=True)
    keys = list(FIELDS)
    left = oracle.sort_values(keys).reset_index(drop=True)
    right = combined.sort_values(keys).reset_index(drop=True)
    if len(left) != len(right) or left[keys].astype(str).ne(right[keys].astype(str)).any().any():
        raise ValueError("PR87 source rows or identifiers disagree")
    for name in ("macro_f1", "query_count", "evaluable_query_count", "mean_peer_count"):
        if not np.allclose(left[name], right[name], rtol=0, atol=1e-12):
            raise ValueError(f"PR87 combined {name} differs from source rows")


def verify_natural_query_archives(primary: pd.DataFrame, split_root: Path,
                                  run_root: Path, *, receivers: int = 32,
                                  seeds: tuple[int, ...] = SEEDS) -> dict:
    """Match every archived natural prediction to the frozen label-free query rule."""
    reference = primary[primary.model.eq("P2")]
    if len(reference) != receivers * len(seeds):
        raise ValueError("primary reference grid is incomplete")
    digest = hashlib.sha256()
    checked = 0
    for protocol, part in reference.groupby("protocol_id", sort=True):
        test_ids = []
        with (split_root / protocol / "split_manifest.csv").open(
            encoding="utf-8", newline=""
        ) as stream:
            for row in csv.DictReader(stream):
                if row["split"] == "test":
                    test_ids.append(row["sample_id"])
        if not test_ids or len(set(test_ids)) != len(test_ids):
            raise ValueError(f"bad test split: {protocol}")
        for record in part.itertuples(index=False):
            seed, receiver = int(record.seed), str(record.receiver_id)
            ordered = sorted(test_ids, key=lambda sample: stable_digest(
                seed, receiver, sample, namespace="wisig-v2-support"))
            query = np.asarray(ordered[128:], dtype=str)
            if len(query) != int(record.query_count):
                raise ValueError(f"query count mismatch: {protocol}/{seed}")
            digest.update(protocol.encode())
            digest.update(str(seed).encode())
            digest.update(hashlib.sha256("\n".join(query).encode()).digest())
            for method in QUERY_METHOD.values():
                archive = (run_root / "runs" /
                           f"{protocol}__{method}__s{seed}__b128__k32__r100__raw" /
                           "predictions_blind.npz")
                with np.load(archive, allow_pickle=False) as blind:
                    actual = blind["sample_ids"]
                    if not np.array_equal(actual, query):
                        raise ValueError(f"natural query IDs differ: {protocol}/{seed}/{method}")
                checked += 1
    return {"natural_prediction_archives_exact_query_match": checked,
            "protocol_seed_query_sets": len(reference),
            "reconstructed_query_digest": digest.hexdigest()}


def latex_table(summary: pd.DataFrame) -> str:
    lookup = summary.set_index(["method", "condition"])
    labels = {
        "NATURAL": "Natural",
        "SAME_CLASS_EXCLUDED_ORACLE": "Same-class excluded",
        "SAME_CLASS_ONLY_ORACLE": "Same-class only",
        "TRANSMITTER_PURE_ORACLE": "Transmitter pure",
    }
    lines = [
        r"\begingroup\scriptsize\setlength{\tabcolsep}{3pt}",
        r"\begin{tabularx}{\textwidth}{lrrrccXccc}",
        r"\toprule",
        r"Condition & T3A & P2 & RX-NORM & Rx & Seeds & Support & Coverage & Same Q & Labels\\",
        r"\midrule",
    ]
    for condition, label in labels.items():
        values = [lookup.loc[(method, condition)] for method in METHODS]
        if len({int(value.receiver_count) for value in values}) != 1 or len(
            {int(value.seed_count) for value in values}
        ) != 1:
            raise ValueError("inconsistent method coverage")
        support = r"128 bank; P2 $k=32$" if condition == "NATURAL" \
            else r"128 bank; $\leq32$ selected"
        lines.append(
            f"{label} & {values[0].receiver_equal_macro_f1:.4f} & "
            f"{values[1].receiver_equal_macro_f1:.4f} & "
            f"{values[2].receiver_equal_macro_f1:.4f} & "
            f"{int(values[0].receiver_count)} & {int(values[0].seed_count)} & "
            f"{support} & 100\\% & Yes & "
            f"{'No' if condition == 'NATURAL' else 'Yes'}" + r"\\"
        )
    lines += [
        r"\midrule",
        r"\multicolumn{10}{l}{EMB-STD and SAR-GN: NOT EVALUATED under oracle composition.}\\",
        r"\bottomrule",
        r"\end{tabularx}\endgroup",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v2-analysis", type=Path, required=True)
    parser.add_argument("--pr87-analysis", type=Path, required=True)
    parser.add_argument("--split-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--table-output", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists() or args.table_output.exists():
        raise FileExistsError("composition evidence/table are create-once")
    v2_manifest = args.v2_analysis / "analysis_manifest.json"
    pr87_manifest = args.pr87_analysis / "analysis_manifest.json"
    input_paths = {
        "v2_primary": (args.v2_analysis / "primary_receiver_seed_results.csv", v2_manifest),
        "v2_p2_oracle": (args.v2_analysis / "composition_oracle_results.csv", v2_manifest),
        "pr87_combined": (args.pr87_analysis / "analysis_composition_stress.csv", pr87_manifest),
        "pr87_tta": (args.pr87_analysis / "tta_rxnorm_composition_receiver_seed_results.csv", pr87_manifest),
    }
    hashes = {name: frozen_hash(path, manifest) for name, (path, manifest) in input_paths.items()}
    primary = pd.read_csv(input_paths["v2_primary"][0])
    p2 = pd.read_csv(input_paths["v2_p2_oracle"][0])
    oracle = pd.read_csv(input_paths["pr87_combined"][0])
    tta = pd.read_csv(input_paths["pr87_tta"][0])
    verify_pr87_sources(oracle, p2, tta)
    summary = aggregate(primary, oracle)
    query_check = verify_natural_query_archives(primary, args.split_root, args.run_root)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    summary_path = args.output_dir / "composition_receiver_equal_summary.csv"
    summary.to_csv(summary_path, index=False, lineterminator="\n")
    text = latex_table(summary)
    args.table_output.write_text(text, encoding="utf-8")
    manifest = {
        "status": "DERIVED_FROM_FROZEN_POSTHOC_SOURCE",
        "source_sha256": hashes,
        "pr87_manifest_sha256": file_sha(pr87_manifest),
        "v2_manifest_sha256": file_sha(v2_manifest),
        "query_audit": query_check,
        "summary_sha256": file_sha(summary_path),
        "table_sha256": file_sha(args.table_output),
        "description": "Receiver equal after five seed values within each receiver; all oracle rows label-dependent.",
        "oracle_query_identity_limit": "Oracle CSVs omit sample IDs; frozen source uses the same deterministic support/query function and all row counts match. Natural prediction archives were checked byte-for-byte against reconstructed query IDs.",
    }
    (args.output_dir / "composition_source_manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"rows": len(summary), **query_check, "summary": str(summary_path)}))


if __name__ == "__main__":
    main()
