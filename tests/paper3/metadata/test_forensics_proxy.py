from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from openew.paper3.metadata.inventory import INVENTORY_COLUMNS, build_source_inventory
from openew.paper3.metadata.leakage import default_eligibility_engine
from openew.paper3.metadata.proxy_audit import audit_field
from openew.paper3.metadata.schema import AnnotationRecord

from common import records


class ForensicsProxyTests(unittest.TestCase):
    def test_inventory_schema_is_stable(self) -> None:
        self.assertEqual(len(INVENTORY_COLUMNS), 12)
        self.assertIn("scientifically_trustworthy_mtime", INVENTORY_COLUMNS)

    def test_inventory_does_not_mutate_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.bin"; path.write_bytes(b"immutable")
            before = (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
            rows = build_source_inventory(directory)
            after = (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(before, after)
            self.assertEqual(len(rows), 1)

    def test_inventory_excludes_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / "source").mkdir(); (root / "generated").mkdir()
            (root / "source" / "a.bin").write_bytes(b"a")
            (root / "generated" / "b.csv").write_text("x\n", encoding="utf-8")
            rows = build_source_inventory(root, excluded_roots=(root / "generated",))
            self.assertEqual([row["relative_path"] for row in rows], ["source/a.bin"])

    def test_proxy_audit_detects_target_mapping(self) -> None:
        acquisition = records()
        annotations = [AnnotationRecord(row.sample_id, "task", row.receiver_id or "", "fixture") for row in acquisition]
        result = audit_field(acquisition, annotations, "receiver_id", eligibility=default_eligibility_engine())
        self.assertEqual(result.classification, "FORBIDDEN_TARGET_PROXY")

    def test_proxy_audit_uses_labels_only_as_diagnostic(self) -> None:
        acquisition = records(); before = tuple(row.to_mapping() for row in acquisition)
        annotations = [AnnotationRecord(row.sample_id, "task", str(index % 2), "fixture") for index, row in enumerate(acquisition)]
        audit_field(acquisition, annotations, "site_id", eligibility=default_eligibility_engine())
        self.assertEqual(before, tuple(row.to_mapping() for row in acquisition))

    def test_incomplete_annotation_pairing_is_explicit(self) -> None:
        acquisition = records()
        annotations = [AnnotationRecord(acquisition[0].sample_id, "task", "x", "fixture")]
        result = audit_field(acquisition, annotations, "receiver_id", eligibility=default_eligibility_engine())
        self.assertEqual(result.total_count, 1)


if __name__ == "__main__":
    unittest.main()
