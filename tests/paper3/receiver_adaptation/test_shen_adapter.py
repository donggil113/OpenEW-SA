from __future__ import annotations

import h5py
import numpy as np
import pytest

from openew.paper3.receiver_adaptation.shen_adapter import FROZEN_TRANSFER_RULE, SHEN_RECEIVERS, inspect_shen_hdf5, load_shen_rows, opaque_sample_id, receiver_hardware, reconstruct_complex, transfer_crops, write_mock_shen_hdf5
from openew.paper3.receiver_adaptation.shen_splits import build_loso_splits, freeze_support_query, support_ids_from_acquisition_rows


@pytest.mark.parametrize("receiver", SHEN_RECEIVERS)
def test_all_documented_receivers_map_to_hardware(receiver: str) -> None:
    assert receiver_hardware(receiver)


@pytest.mark.parametrize("receiver", ["rtl_0", "rtl_10", "pluto", "n210_4", "target_1", "", "01"])
def test_unknown_receiver_fails_closed(receiver: str) -> None:
    with pytest.raises(ValueError, match="unknown physical receiver"):
        receiver_hardware(receiver)


@pytest.mark.parametrize("strategy", ["C1_FIRST_256", "C2_CENTERED_256", "C3_ENERGY_256"])
def test_single_crop_strategies_shape(strategy: str) -> None:
    values = np.arange(2 * 1024, dtype=np.float32).reshape(2, 1024).astype(np.complex64)
    assert transfer_crops(values, strategy).shape == (2, 256)


def test_three_crop_strategy_shape() -> None:
    assert transfer_crops(np.ones((3, 512), dtype=np.complex64), "C4_THREE_CROPS").shape == (3, 3, 256)


@pytest.mark.parametrize("strategy", ["", "center", "C5", "label_based", "best_accuracy"])
def test_unknown_crop_strategy_rejected(strategy: str) -> None:
    with pytest.raises(ValueError, match="unknown transfer strategy"):
        transfer_crops(np.ones((2, 512), dtype=np.complex64), strategy)


@pytest.mark.parametrize("shape", [(4,), (2, 511), (2, 2, 4)])
def test_bad_packed_shape_rejected(shape: tuple[int, ...]) -> None:
    with pytest.raises(ValueError):
        reconstruct_complex(np.ones(shape, dtype=np.float32))


@pytest.mark.parametrize("width", [256, 512, 1024, 2048])
def test_complex_reconstruction(width: int) -> None:
    packed = np.concatenate([np.ones((2, width)), np.full((2, width), 2.0)], axis=1)
    result = reconstruct_complex(packed)
    assert result.shape == (2, width)
    assert np.all(result == 1 + 2j)


def test_nonfinite_complex_rejected() -> None:
    values = np.ones((2, 512), dtype=np.float32)
    values[0, 0] = np.nan
    with pytest.raises(FloatingPointError):
        reconstruct_complex(values)


@pytest.mark.parametrize("row", [0, 1, 9, 100, 2**31])
def test_opaque_id_deterministic(row: int) -> None:
    source = "a" * 64
    value = opaque_sample_id(source, "rtl_1", row)
    assert value == opaque_sample_id(source, "rtl_1", row)
    assert len(value) == 32 and "rtl" not in value


@pytest.mark.parametrize("source", ["", "a" * 63, "A" * 64, "g" * 64, "target"])
def test_opaque_id_requires_sha(source: str) -> None:
    with pytest.raises(ValueError, match="SHA256"):
        opaque_sample_id(source, "rtl_1", 0)


def test_mock_schema_and_load(tmp_path) -> None:
    path = write_mock_shen_hdf5(tmp_path / "rtl_1.h5", rows=20, complex_width=512)
    schema = inspect_shen_hdf5(path, "rtl_1")
    assert (schema.row_count, schema.complex_width) == (20, 512)
    features, rows = load_shen_rows(path, "rtl_1")
    assert features.shape == (20, 256, 2)
    assert len({row.sample_id for row in rows}) == 20
    assert all("transmitter_id" not in row.acquisition_dict() for row in rows)
    assert all("transmitter_id" in row.annotation_dict() for row in rows)


@pytest.mark.parametrize("missing", ["data", "label", "SNR", "CFO"])
def test_missing_hdf5_key_rejected(tmp_path, missing: str) -> None:
    path = write_mock_shen_hdf5(tmp_path / f"{missing}.h5")
    with h5py.File(path, "a") as handle:
        del handle[missing]
    with pytest.raises(ValueError, match="keys"):
        inspect_shen_hdf5(path, "rtl_1")


def test_extra_hdf5_key_rejected(tmp_path) -> None:
    path = write_mock_shen_hdf5(tmp_path / "extra.h5")
    with h5py.File(path, "a") as handle:
        handle.create_dataset("timestamp", data=np.arange(40))
    with pytest.raises(ValueError, match="keys"):
        inspect_shen_hdf5(path, "rtl_1")


@pytest.mark.parametrize("key", ["label", "SNR", "CFO"])
def test_companion_row_mismatch_rejected(tmp_path, key: str) -> None:
    path = tmp_path / f"bad-{key}.h5"
    with h5py.File(path, "w") as handle:
        handle.create_dataset("data", data=np.ones((5, 512), dtype=np.float32))
        for name in ("label", "SNR", "CFO"):
            handle.create_dataset(name, data=np.ones((4 if name == key else 5, 1), dtype=np.float32))
    with pytest.raises(ValueError, match="row count"):
        inspect_shen_hdf5(path, "rtl_1")


def test_default_transfer_is_centered() -> None:
    values = np.arange(512, dtype=np.float32).reshape(1, -1).astype(np.complex64)
    assert FROZEN_TRANSFER_RULE == "C2_CENTERED_256"
    assert np.array_equal(transfer_crops(values), values[:, 128:384])


def test_loso_has_all_twenty_receivers_once() -> None:
    splits = build_loso_splits()
    assert len(splits) == 20 and {row.test_receiver for row in splits} == set(SHEN_RECEIVERS)
    assert all(len(row.validation_receivers) == 3 and len(row.train_receivers) == 16 for row in splits)


def test_loso_deterministic() -> None:
    assert build_loso_splits() == build_loso_splits()


@pytest.mark.parametrize("count", [0, 19, 20, -1])
def test_invalid_validation_count(count: int) -> None:
    with pytest.raises(ValueError):
        build_loso_splits(count)


def test_support_query_disjoint_and_label_independent(tmp_path) -> None:
    path = write_mock_shen_hdf5(tmp_path / "rx.h5", rows=140)
    _, rows = load_shen_rows(path, "rtl_1")
    original = freeze_support_query(rows, "rtl_1", budget=128, seed=829)
    permuted = [type(row)(row.sample_id, row.receiver_id, row.hardware_family, row.source_record_index, str((int(row.transmitter_id) + 3) % 10), row.snr, row.cfo) for row in rows]
    changed = freeze_support_query(permuted, "rtl_1", budget=128, seed=829)
    assert original.support_sample_ids == changed.support_sample_ids
    assert not (set(original.support_sample_ids) & set(original.query_sample_ids))


@pytest.mark.parametrize("field", ["label", "transmitter_id", "target", "prediction", "correctness", "source_path"])
def test_acquisition_support_api_rejects_annotation_fields(field: str) -> None:
    rows = [{"sample_id": f"s{index}", "receiver_id": "rtl_1", field: "x"} for index in range(130)]
    with pytest.raises(ValueError, match="fail closed"):
        support_ids_from_acquisition_rows(rows, "rtl_1")
