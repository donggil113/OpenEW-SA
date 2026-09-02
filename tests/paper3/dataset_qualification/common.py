from __future__ import annotations


def candidate_mapping() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "candidate_id": "cand-001",
        "dataset_name": "Fixture RF",
        "task": "RF fingerprinting",
        "official_source": "https://example.edu/dataset",
        "official_paper": "https://doi.org/10.0000/example",
        "license": "CC-BY-4.0",
        "license_verified": "TRUE",
        "download_size_bytes": 1000,
        "receiver_count": 2,
        "site_count": 2,
        "day_count": 3,
        "session_count": 10,
        "timestamp_available": "TRUE",
        "order_available": "TRUE",
        "frequency_available": "TRUE",
        "sample_rate_available": "TRUE",
        "annotation_separated": "TRUE",
        "target_field": "transmitter_id",
        "target_proxy_fields": ["transmitter_id"],
        "relation_allowed_fields": ["receiver_id", "site_id"],
        "temporal_status": "VALID_TEMPORAL_CONTEXT",
        "metadata_readiness": "DYNAMIC_HYPERGRAPH",
        "access_status": "PUBLIC_DIRECT",
        "adoption_status": "GO",
        "evidence_confidence": "VERIFIED",
    }
