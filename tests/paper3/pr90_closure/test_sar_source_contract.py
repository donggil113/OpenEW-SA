"""Source-only diagnostic plan and crash-resume checkpoint contracts."""
import importlib.util
import json
import math
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[3] / "scripts/paper3/pr90_closure/run_sar_source_only.py"
SPEC = importlib.util.spec_from_file_location("sar_source_only_contract", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_candidate_order_and_normalized_threshold():
    candidates = MODULE.candidates(6)
    assert [name for name, _ in candidates] == ["A_1", "A_5", "A_20", "B_1", "B_5", "B_20"]
    assert [candidate.passes for _, candidate in candidates] == [1, 5, 20, 1, 5, 20]
    assert all(candidate.reset_threshold == 0.2 for _, candidate in candidates[:3])
    assert all(math.isclose(candidate.reset_threshold, 0.2*math.log(6)/math.log(1000))
               for _, candidate in candidates[3:])


def test_candidate_checkpoint_create_once_and_validate(tmp_path):
    destination = tmp_path / "candidate.json"
    rows = [{"protocol": "receiver_loso_00", "seed": 829, "candidate": "A_1",
             "source_validation_receiver": receiver, "macro_f1": 0.5}
            for receiver in ("r1", "r2", "r3")]
    MODULE.save_candidate_checkpoint(destination, {"freeze_sha256": "frozen", "rows": rows})
    assert MODULE.read_candidate_checkpoint(destination, "receiver_loso_00", 829, "A_1",
                                             ["r1", "r2", "r3"], "frozen") == rows
    with pytest.raises(FileExistsError):
        MODULE.save_candidate_checkpoint(destination, {"freeze_sha256": "new", "rows": rows})


@pytest.mark.parametrize("change", ["freeze", "receiver", "candidate", "count"])
def test_corrupt_checkpoint_fails_closed(tmp_path, change):
    rows = [{"protocol": "receiver_loso_00", "seed": 829, "candidate": "A_1",
             "source_validation_receiver": receiver, "macro_f1": 0.5}
            for receiver in ("r1", "r2", "r3")]
    payload = {"freeze_sha256": "frozen", "rows": rows}
    if change == "freeze":
        payload["freeze_sha256"] = "wrong"
    elif change == "receiver":
        rows[0]["source_validation_receiver"] = "target"
    elif change == "candidate":
        rows[0]["candidate"] = "B_20"
    else:
        rows.pop()
    destination = tmp_path / "candidate.json"
    destination.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        MODULE.read_candidate_checkpoint(destination, "receiver_loso_00", 829, "A_1",
                                         ["r1", "r2", "r3"], "frozen")
