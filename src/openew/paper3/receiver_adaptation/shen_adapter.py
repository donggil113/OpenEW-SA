"""Fail-closed, synthetic-tested adapter for the documented Shen HDF5 schema."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

import numpy as np

EXPECTED_KEYS = frozenset({"data", "label", "SNR", "CFO"})
FROZEN_TRANSFER_RULE = "C2_CENTERED_256"
SHEN_RECEIVERS = (
    "rtl_1", "rtl_2", "rtl_3", "rtl_4", "rtl_5", "rtl_6", "rtl_7", "rtl_8", "rtl_9",
    "pluto_1", "pluto_2", "b200_1", "b200_2", "b200mini_1", "b200mini_2",
    "b210_1", "b210_2", "n210_1", "n210_2", "n210_3",
)
SHEN_HARDWARE = {
    "rtl": "RTL-SDR", "pluto": "ADALM-PLUTO", "b200": "USRP-B200",
    "b200mini": "USRP-B200mini", "b210": "USRP-B210", "n210": "USRP-N210",
}


@dataclass(frozen=True)
class ShenHDF5Schema:
    path: str
    row_count: int
    packed_width: int
    complex_width: int
    data_dtype: str
    label_dtype: str
    snr_dtype: str
    cfo_dtype: str
    receiver_id: str
    hardware_family: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ShenSample:
    sample_id: str
    receiver_id: str
    hardware_family: str
    source_record_index: int
    transmitter_id: str
    snr: float
    cfo: float

    def acquisition_dict(self) -> dict[str, object]:
        return {
            "sample_id": self.sample_id,
            "receiver_id": self.receiver_id,
            "hardware_family": self.hardware_family,
            "source_record_index": self.source_record_index,
            "sample_rate_hz": 1_000_000,
            "center_frequency_hz": 868_100_000,
        }

    def annotation_dict(self) -> dict[str, object]:
        return {"sample_id": self.sample_id, "task_name": "transmitter_identification", "transmitter_id": self.transmitter_id}


def receiver_hardware(receiver_id: str) -> str:
    receiver_id = str(receiver_id)
    if receiver_id not in SHEN_RECEIVERS:
        raise ValueError(f"unknown physical receiver: {receiver_id}")
    return SHEN_HARDWARE[receiver_id.rsplit("_", 1)[0]]


def _h5py():
    try:
        import h5py
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Shen HDF5 adapter requires h5py>=3.10") from exc
    return h5py


def inspect_shen_hdf5(path: str | Path, receiver_id: str) -> ShenHDF5Schema:
    h5py = _h5py()
    path = Path(path)
    hardware = receiver_hardware(receiver_id)
    with h5py.File(path, "r") as handle:
        keys = frozenset(handle.keys())
        if keys != EXPECTED_KEYS:
            raise ValueError(f"unexpected Shen HDF5 keys: {sorted(keys)}")
        data = handle["data"]
        if data.ndim != 2 or data.shape[1] < 512 or data.shape[1] % 2:
            raise ValueError("data must be [rows, even packed real/imag width >=512]")
        if data.dtype.kind not in "fiu":
            raise TypeError("data must have a numeric primitive dtype")
        rows, packed_width = int(data.shape[0]), int(data.shape[1])
        dtypes: dict[str, str] = {"data": str(data.dtype)}
        for name in ("label", "SNR", "CFO"):
            item = handle[name]
            if item.dtype.kind not in "fiu":
                raise TypeError(f"{name} must have a numeric primitive dtype")
            if item.size != rows:
                raise ValueError(f"{name} row count differs from data")
            dtypes[name] = str(item.dtype)
    return ShenHDF5Schema(str(path), rows, packed_width, packed_width // 2, dtypes["data"], dtypes["label"], dtypes["SNR"], dtypes["CFO"], str(receiver_id), hardware)


def reconstruct_complex(packed: np.ndarray) -> np.ndarray:
    values = np.asarray(packed)
    if values.ndim != 2 or values.shape[1] % 2 or values.dtype.kind not in "fiu":
        raise ValueError("packed data must be numeric [rows, real-half + imaginary-half]")
    half = values.shape[1] // 2
    result = values[:, :half].astype(np.float32) + 1j * values[:, half:].astype(np.float32)
    if not np.isfinite(result).all():
        raise FloatingPointError("Shen complex reconstruction produced non-finite data")
    return result.astype(np.complex64, copy=False)


def transfer_crops(signals: np.ndarray, strategy: str = FROZEN_TRANSFER_RULE) -> np.ndarray:
    values = np.asarray(signals)
    if values.ndim != 2 or not np.iscomplexobj(values) or values.shape[1] < 256:
        raise ValueError("transfer expects complex [rows, samples] with at least 256 samples")
    width = values.shape[1]
    if strategy == "C1_FIRST_256":
        return values[:, :256]
    if strategy == "C2_CENTERED_256":
        offset = (width - 256) // 2
        return values[:, offset : offset + 256]
    if strategy == "C3_ENERGY_256":
        kernel = np.ones(256, dtype=np.float32)
        starts = [int(np.argmax(np.convolve(np.abs(row) ** 2, kernel, mode="valid"))) for row in values]
        return np.stack([values[row, start : start + 256] for row, start in enumerate(starts)])
    if strategy == "C4_THREE_CROPS":
        starts = (0, (width - 256) // 2, width - 256)
        return np.stack([values[:, start : start + 256] for start in starts], axis=1)
    raise ValueError(f"unknown transfer strategy: {strategy}")


def opaque_sample_id(source_sha256: str, receiver_id: str, row_index: int) -> str:
    if not re.fullmatch(r"[0-9a-f]{64}", str(source_sha256)):
        raise ValueError("source SHA256 must be lowercase hexadecimal")
    receiver_hardware(receiver_id)
    if int(row_index) < 0:
        raise ValueError("row index must be nonnegative")
    payload = f"shen-adapter-v1\0{source_sha256}\0{receiver_id}\0{int(row_index)}".encode()
    return hashlib.sha256(payload).hexdigest()[:32]


def load_shen_rows(path: str | Path, receiver_id: str, indices: Sequence[int] | None = None) -> tuple[np.ndarray, list[ShenSample]]:
    schema = inspect_shen_hdf5(path, receiver_id)
    h5py = _h5py()
    selected = np.arange(schema.row_count, dtype=np.int64) if indices is None else np.asarray(indices, dtype=np.int64)
    if selected.ndim != 1 or len(np.unique(selected)) != len(selected) or (len(selected) and (selected.min() < 0 or selected.max() >= schema.row_count)):
        raise ValueError("row indices must be unique and in range")
    source_sha = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    with h5py.File(path, "r") as handle:
        packed = np.asarray(handle["data"][selected])
        labels = np.asarray(handle["label"]).reshape(-1)[selected]
        snr = np.asarray(handle["SNR"]).reshape(-1)[selected]
        cfo = np.asarray(handle["CFO"]).reshape(-1)[selected]
    crops = transfer_crops(reconstruct_complex(packed), FROZEN_TRANSFER_RULE)
    features = np.stack([crops.real, crops.imag], axis=-1).astype(np.float32)
    samples = [ShenSample(opaque_sample_id(source_sha, receiver_id, int(index)), receiver_id, receiver_hardware(receiver_id), int(index), str(int(labels[position])), float(snr[position]), float(cfo[position])) for position, index in enumerate(selected)]
    return features, samples


def write_mock_shen_hdf5(path: str | Path, *, rows: int = 40, complex_width: int = 1024, transmitter_count: int = 10, seed: int = 829) -> Path:
    if rows <= 0 or complex_width < 256 or transmitter_count <= 1:
        raise ValueError("invalid mock fixture dimensions")
    h5py = _h5py()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    real = rng.normal(size=(rows, complex_width)).astype(np.float32)
    imag = rng.normal(size=(rows, complex_width)).astype(np.float32)
    labels = (np.arange(rows) % transmitter_count + 1).astype(np.int16)
    with h5py.File(path, "w") as handle:
        handle.create_dataset("data", data=np.concatenate([real, imag], axis=1))
        handle.create_dataset("label", data=labels.reshape(-1, 1))
        handle.create_dataset("SNR", data=np.full((rows, 1), 25.0, dtype=np.float32))
        handle.create_dataset("CFO", data=np.linspace(-100, 100, rows, dtype=np.float32).reshape(-1, 1))
    return path
