from __future__ import annotations

import unittest

from openew.paper3.metadata.dynamic_snapshot import build_dynamic_snapshots
from openew.paper3.metadata.enums import TemporalVerdict
from openew.paper3.metadata.episodes import build_episodes
from openew.paper3.metadata.leakage import default_eligibility_engine
from openew.paper3.metadata.temporal import TemporalEvidence, audit_temporal_field
from openew.paper3.metadata.temporal_neighbors import build_temporal_neighbors

from common import changed, record, records


class TemporalEpisodeTests(unittest.TestCase):
    def evidence(self, **updates: object) -> TemporalEvidence:
        values = dict(
            field="timestamp_utc",
            physical_order_verified=True,
            session_reset_semantics_verified=True,
            gaps_have_defined_meaning=True,
            inference_time_available=True,
            container_target_pure=False,
            mixed_target_episode_fraction=1.0,
        )
        values.update(updates)
        return TemporalEvidence(**values)

    def test_monotonic_valid_temporal_context(self) -> None:
        self.assertIs(audit_temporal_field(records(), self.evidence()).verdict, TemporalVerdict.VALID_TEMPORAL_CONTEXT)

    def test_clock_reset_segments_are_isolated(self) -> None:
        rows = [record(0), changed(record(1), clock_reset_id="reset-02", timestamp_utc="2025-01-01T00:00:00Z")]
        self.assertEqual(audit_temporal_field(rows, self.evidence()).negative_gap_count, 0)

    def test_negative_gap_is_unresolved(self) -> None:
        rows = [record(0), changed(record(1), timestamp_utc="2025-01-01T00:00:00Z")]
        self.assertIs(audit_temporal_field(rows, self.evidence()).verdict, TemporalVerdict.UNRESOLVED)

    def test_coarse_date_only(self) -> None:
        evidence = self.evidence(field="campaign_id", coarse_date_only=True)
        rows = [changed(record(0), campaign_id="day1")]
        self.assertIs(audit_temporal_field(rows, evidence).verdict, TemporalVerdict.COARSE_DATE_ONLY)

    def test_target_nested_order(self) -> None:
        self.assertIs(audit_temporal_field(records(), self.evidence(container_target_pure=True)).verdict, TemporalVerdict.TARGET_NESTED_ORDER)

    def test_filesystem_timestamp_only(self) -> None:
        self.assertIs(audit_temporal_field(records(), self.evidence(filesystem_timestamp_only=True)).verdict, TemporalVerdict.SYSTEM_TIMESTAMP_ONLY)

    def test_temporal_neighbors_causal_no_future(self) -> None:
        plan = build_temporal_neighbors(records(), causal=True)
        self.assertTrue(all(source < destination for source, destination in zip(plan.source_indices, plan.destination_indices)))

    def test_temporal_neighbors_session_isolation(self) -> None:
        rows = records()
        plan = build_temporal_neighbors(rows, causal=False)
        self.assertTrue(all(rows[s].acquisition_session_id == rows[d].acquisition_session_id for s, d in zip(plan.source_indices, plan.destination_indices)))

    def test_missing_timestamp_rejected(self) -> None:
        with self.assertRaises(ValueError): build_temporal_neighbors([changed(record(), timestamp_utc=None)])

    def test_dynamic_requires_valid_verdict(self) -> None:
        with self.assertRaises(ValueError): build_dynamic_snapshots(records(), temporal_verdict=TemporalVerdict.UNRESOLVED, window_seconds=2)

    def test_dynamic_window_boundaries(self) -> None:
        snapshots = build_dynamic_snapshots(records(), temporal_verdict=TemporalVerdict.VALID_TEMPORAL_CONTEXT, window_seconds=2)
        self.assertGreaterEqual(len(snapshots), 4)

    def test_episode_deterministic_chunking(self) -> None:
        rows = [changed(record(i), receiver_id="same") for i in range(10)]
        kwargs = dict(eligibility=default_eligibility_engine(), explicit_whitelist=["receiver_id"], max_episode_size=3, seed=7)
        first = build_episodes(rows, ["receiver_id"], **kwargs)
        second = build_episodes(rows, ["receiver_id"], **kwargs)
        self.assertEqual(first.episodes, second.episodes)
        self.assertEqual([len(item.sample_indices) for item in first.episodes], [3, 3, 3, 1])

    def test_missing_episode_field_isolated(self) -> None:
        rows = [changed(record(0), receiver_id=None), record(1)]
        plan = build_episodes(rows, ["receiver_id"], eligibility=default_eligibility_engine(), explicit_whitelist=["receiver_id"], max_episode_size=10, seed=1)
        self.assertEqual(plan.isolated_indices, (0,))

    def test_episode_partition_isolation(self) -> None:
        rows = [changed(record(i), receiver_id="same") for i in range(4)]
        partitions = {row.sample_id: "train" if i < 2 else "test" for i, row in enumerate(rows)}
        plan = build_episodes(rows, ["receiver_id"], eligibility=default_eligibility_engine(), explicit_whitelist=["receiver_id"], max_episode_size=10, seed=1, partition_by_sample=partitions)
        self.assertEqual({episode.partition for episode in plan.episodes}, {"train", "test"})


if __name__ == "__main__":
    unittest.main()
