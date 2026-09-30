"""Read-only PR90 manifest recheck; writes only to a new closure output file."""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_map(root: Path, entries: dict[str, str]) -> tuple[int, list[str]]:
    failures: list[str] = []
    for relative, expected in sorted(entries.items()):
        path = root / relative
        if not path.is_file():
            failures.append(f"missing:{relative}")
        elif sha256(path) != expected:
            failures.append(f"sha256:{relative}")
    return len(entries), failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    repo = args.repository.resolve()
    paper3 = args.data_root.resolve() / "paper3"
    root = paper3 / "reviewer_remediation"
    package_path = root / "final_package_manifest.json"
    prediction_path = root / "prediction_manifest.json"
    package = json.loads(package_path.read_text())
    predictions = json.loads(prediction_path.read_text())
    assert package["file_count"] == len(package["files"])
    assert predictions["complete"] == 2400 and predictions["failed"] == 0
    assert len(package["run_registry"]) == 2400
    assert len(predictions["prediction_hashes"]) == 2400
    counts = {}
    failures = []
    for name, mapping in (
        ("package_files", package["files"]),
        ("run_json", package["run_registry"]),
        ("blind_predictions", predictions["prediction_hashes"]),
    ):
        counts[name], errors = verify_map(root, mapping)
        failures.extend(errors)
    for name, expected in (
        ("final_execution_integrity.json", package["files"]["final_execution_integrity.json"]),
        ("prediction_manifest.json", package["files"]["prediction_manifest.json"]),
        ("unblinding_manifest.json", package["files"]["unblinding_manifest.json"]),
    ):
        if sha256(root / name) != expected:
            failures.append(f"manifest:{name}")
    checkpoint_count = 0
    for relative in sorted(package["run_registry"]):
        record = json.loads((root / relative).read_text())
        if record.get("status") != "COMPLETE" or record.get("target_metrics") is not None:
            failures.append(f"run_status_or_blinding:{relative}")
        expected = record.get("checkpoint_sha256")
        if expected:
            checkpoint_count += 1
            checkpoint = (root / relative).parent / "adapted.pt"
            if not checkpoint.is_file() or sha256(checkpoint) != expected:
                failures.append(f"checkpoint:{relative}")
    counts["adapted_checkpoints"] = checkpoint_count
    # The official ManyRx compact archive is the one-time source identified by PR90.
    raw_files = list((paper3 / "wisig" / "raw").glob("**/*"))
    raw_archives = [p for p in raw_files if p.is_file() and p.suffix.lower() in {".zip", ".rar", ".7z"}]
    raw_status = "NOT_FOUND"
    raw_sha = None
    if len(raw_archives) == 1:
        raw_sha = sha256(raw_archives[0])
        raw_status = "PASS" if raw_sha == "d2b23108c3f6f63a10ebbb149d7b08d6e1c1961cf5184926fbab452def3049de" else "FAIL"
    elif len(raw_archives) > 1:
        raw_status = "AMBIGUOUS"
    if raw_status != "PASS":
        failures.append(f"raw_archive:{raw_status}")
    changed = subprocess.check_output(["git", "diff", "--name-only", "68198ab324c2bf5a6b4d97df0d3abcfcc7d64dfd"], cwd=repo, text=True).splitlines()
    permitted = ("configs/paper3/pr90_closure/", "papers/paper3_pr90_closure/", "scripts/paper3/pr90_closure/", "src/openew/paper3/pr90_closure/", "tests/paper3/pr90_closure/", "papers/paper3_reviewer_remediation/manuscript/")
    out_of_scope = [name for name in changed if not name.startswith(permitted)]
    failures.extend(f"git_scope:{name}" for name in out_of_scope)
    report = {
        "status": "PASS" if not failures else "FAIL",
        "utc": datetime.now(timezone.utc).isoformat(),
        "pr90_head_reference": "68198ab324c2bf5a6b4d97df0d3abcfcc7d64dfd",
        "pr90_package_sha256": sha256(package_path),
        "pr90_prediction_manifest_sha256": sha256(prediction_path),
        "pr90_core_analysis_manifest_sha256": sha256(root / "analysis" / "core_analysis_manifest.json"),
        "counts": counts,
        "raw_archive_status": raw_status,
        "raw_archive_sha256": raw_sha,
        "out_of_scope_tracked_changes": out_of_scope,
        "failures": failures,
        "scope_note": "Rehashed listed PR90 package files, 2400 run JSON, 2400 blind predictions, and every adapted checkpoint declared by run records; earlier PR80-89 deep audit is retained as its frozen report, not rerun here.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "counts": counts, "raw_archive_status": raw_status, "failures": len(failures)}))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
