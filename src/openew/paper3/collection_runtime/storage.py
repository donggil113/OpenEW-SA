"""Durable JSON transactions with explicit recovery and process serialization."""
from __future__ import annotations
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
from typing import Any

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()

def sync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)

def atomic_bytes(path: Path, payload: bytes, *, failpoint: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".partial")
    with temp.open("xb") as stream:
        if failpoint == "disk_full":
            stream.write(payload[:max(1, len(payload)//2)])
            stream.flush(); os.fsync(stream.fileno())
            raise OSError(28, "synthetic disk-full injection")
        stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    if failpoint == "before_rename":
        raise InterruptedError("synthetic power failure before rename")
    os.replace(temp, path)
    sync_directory(path.parent)

def atomic_json(path: Path, value: Any, **kwargs: Any) -> None:
    atomic_bytes(path, canonical(value), **kwargs)

def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

@contextlib.contextmanager
def locked(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".lock").open("a+b") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)

class Store:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.path = self.root / "state.json"
        self.journal = self.root / "journal"

    def state(self) -> dict:
        if not self.path.exists():
            raise FileNotFoundError("campaign not initialized; use campaign-init or recover")
        return read_json(self.path)

    def pending(self) -> list[Path]:
        return sorted(self.journal.glob("*.pending.json"))

    def commit(self, state: dict, operation: str, *, failpoint: str | None = None) -> None:
        if self.pending():
            raise RuntimeError("pending transaction; recover before mutations")
        state["revision"] = int(state.get("revision", 0)) + 1
        self.journal.mkdir(parents=True, exist_ok=True)
        event = self.journal / f'{state["revision"]:08d}.pending.json'
        envelope = {"operation": operation, "revision": state["revision"], "state": state,
                    "state_sha256": hashlib.sha256(canonical(state)).hexdigest()}
        atomic_json(event, envelope)
        if failpoint == "after_journal":
            raise InterruptedError("synthetic power failure after journal")
        atomic_json(self.path, state, failpoint="disk_full" if failpoint == "disk_full" else None)
        if failpoint == "after_state":
            raise InterruptedError("synthetic power failure after state")
        os.replace(event, event.with_name(event.name.replace(".pending.", ".committed.")))
        sync_directory(self.journal)

    def recover_transactions(self) -> list[str]:
        actions = []
        partial = self.path.with_name("state.json.partial")
        # An incomplete state write is never promoted. Preserve it as evidence.
        if partial.exists():
            quarantine = self.root / "recovery"
            quarantine.mkdir(exist_ok=True)
            destination = quarantine / f"state-{sha256(partial)}.partial"
            if destination.exists():
                raise RuntimeError("identical recovery evidence already exists; operator review required")
            os.replace(partial, destination)
            actions.append("quarantined_partial_state")
        for event in self.pending():
            envelope = read_json(event)
            if hashlib.sha256(canonical(envelope["state"])).hexdigest() != envelope["state_sha256"]:
                raise RuntimeError("corrupt pending transaction")
            current = self.state() if self.path.exists() else {"revision": 0}
            revision = int(envelope["revision"])
            if current["revision"] == revision:
                if canonical(current) != canonical(envelope["state"]):
                    raise RuntimeError("conflicting committed state")
            elif current["revision"] == revision - 1:
                atomic_json(self.path, envelope["state"])
                actions.append(f"replayed_revision_{revision}")
            else:
                raise RuntimeError("journal revision gap")
            os.replace(event, event.with_name(event.name.replace(".pending.", ".committed.")))
            sync_directory(self.journal)
        return actions
