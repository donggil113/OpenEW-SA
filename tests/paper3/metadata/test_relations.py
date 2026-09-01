from __future__ import annotations

import inspect
import unittest

from openew.paper3.metadata.enums import Eligibility
from openew.paper3.metadata.hypergraph_incidence import to_typed_hypergraph
from openew.paper3.metadata.leakage import EligibilityEngine, default_eligibility_engine
from openew.paper3.metadata.relation_builder import (
    build_equality_relations,
    build_frequency_overlap_relations,
)

from common import changed, record, records


class RelationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = default_eligibility_engine()

    def test_receiver_equality(self) -> None:
        plan = build_equality_relations(records(), ["receiver_id"], eligibility=self.engine, explicit_whitelist=["receiver_id"])
        self.assertEqual(plan.relation_types[0].group_count, 2)

    def test_site_equality(self) -> None:
        plan = build_equality_relations(records(), ["site_id"], eligibility=self.engine, explicit_whitelist=["site_id"])
        self.assertEqual(plan.relation_types[0].group_count, 2)

    def test_multiple_relation_types_remain_separate(self) -> None:
        plan = build_equality_relations(records(), ["receiver_id", "site_id"], eligibility=self.engine, explicit_whitelist=["receiver_id", "site_id"])
        self.assertEqual(tuple(item.relation_type for item in plan.relation_types), ("receiver_id", "site_id"))

    def test_missing_identifier_preserves_isolated_node(self) -> None:
        rows = records(); rows[0] = changed(rows[0], receiver_id=None)
        plan = build_equality_relations(rows, ["receiver_id"], eligibility=self.engine, explicit_whitelist=["receiver_id"])
        self.assertIn(0, plan.relation_types[0].isolated_nodes)

    def test_deterministic(self) -> None:
        kwargs = dict(eligibility=self.engine, explicit_whitelist=["receiver_id"])
        first = build_equality_relations(records(), ["receiver_id"], **kwargs)
        second = build_equality_relations(records(), ["receiver_id"], **kwargs)
        self.assertEqual(first.relation_types[0].group_value_hashes, second.relation_types[0].group_value_hashes)
        self.assertEqual(first.relation_types[0].node_indices.tolist(), second.relation_types[0].node_indices.tolist())

    def test_partition_boundaries_split_groups(self) -> None:
        rows = records(4)
        partitions = {row.sample_id: ("train" if i < 2 else "test") for i, row in enumerate(rows)}
        plan = build_equality_relations(rows, ["receiver_id"], eligibility=self.engine, explicit_whitelist=["receiver_id"], partition_by_sample=partitions)
        for group in plan.relation_types[0].groups():
            self.assertEqual(len({partitions[rows[i].sample_id] for i in group}), 1)

    def test_missing_partition_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_equality_relations(records(), ["receiver_id"], eligibility=self.engine, explicit_whitelist=["receiver_id"], partition_by_sample={})

    def test_large_group_storage_is_linear_not_clique(self) -> None:
        rows = [changed(record(i), receiver_id="one") for i in range(1000)]
        plan = build_equality_relations(rows, ["receiver_id"], eligibility=self.engine, explicit_whitelist=["receiver_id"])
        self.assertLess(plan.storage_entries, 3 * len(rows))

    def test_duplicate_sample_rejected(self) -> None:
        rows = records(); rows[1] = changed(rows[1], sample_id=rows[0].sample_id)
        with self.assertRaises(ValueError):
            build_equality_relations(rows, ["receiver_id"], eligibility=self.engine, explicit_whitelist=["receiver_id"])

    def test_frequency_overlap_requires_custom_reviewed_policy(self) -> None:
        with self.assertRaises(ValueError):
            build_frequency_overlap_relations(records(), eligibility=self.engine, explicit_whitelist=["lower_frequency_hz", "upper_frequency_hz"])

    def test_frequency_overlap_components(self) -> None:
        policy = dict(self.engine.policy)
        policy["lower_frequency_hz"] = Eligibility.RELATION_ALLOWED
        policy["upper_frequency_hz"] = Eligibility.RELATION_ALLOWED
        rows = records(4)
        rows[2] = changed(rows[2], lower_frequency_hz=200.0, upper_frequency_hz=201.0, center_frequency_hz=200.5)
        rows[3] = changed(rows[3], lower_frequency_hz=200.5, upper_frequency_hz=202.0, center_frequency_hz=201.0)
        plan = build_frequency_overlap_relations(rows, eligibility=EligibilityEngine(policy), explicit_whitelist=["lower_frequency_hz", "upper_frequency_hz"])
        self.assertEqual(plan.relation_types[0].group_count, 2)

    def test_typed_hypergraph_incidence_correct(self) -> None:
        plan = build_equality_relations(records(), ["receiver_id", "site_id"], eligibility=self.engine, explicit_whitelist=["receiver_id", "site_id"])
        hyper = to_typed_hypergraph(plan)
        self.assertEqual(hyper.node_count, len(records()))
        self.assertEqual(hyper.type_offsets.tolist(), [0, 2, 4])

    def test_hypergraph_has_no_pairwise_edge_matrix(self) -> None:
        plan = build_equality_relations(records(), ["receiver_id"], eligibility=self.engine, explicit_whitelist=["receiver_id"])
        hyper = to_typed_hypergraph(plan)
        self.assertFalse(hasattr(hyper, "adjacency_matrix"))

    def test_relation_builder_signature_has_no_annotations(self) -> None:
        self.assertNotIn("annotations", inspect.signature(build_equality_relations).parameters)


if __name__ == "__main__":
    unittest.main()
