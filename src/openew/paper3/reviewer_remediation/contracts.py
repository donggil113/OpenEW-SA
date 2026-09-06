"""Frozen grid, path boundaries, strict prediction and create-once contracts."""
import hashlib
import json
import os
from pathlib import Path
import numpy as np

SEEDS = (829, 1829, 2829, 3829, 4829)
METHODS = ("SAR_GN", "EMB_STD", "SUP_FT_FULL_128")
BUDGETS = (0, 16, 32, 64, 128, 256)
EVIDENCE = "POST_HOC_BASELINE_COMPLETENESS"
PREREG_COMMIT = "f30b658ff40f4d8ec3770be4c7c2b4692e5814da"
FROZEN_SHA = "7b83dbcf25dc05f9130b75fdb92ce2d3ce225e92"

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()

def file_sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(2**20), b""):
            h.update(chunk)
    return h.hexdigest()

def grid():
    return [(f"receiver_loso_{r:02d}", s, m, b, scope)
            for r in range(32) for s in SEEDS
            for m in METHODS
            for scope, budgets in (("primary", (128,)), ("budget", BUDGETS if m != "SUP_FT_FULL_128" else ()))
            for b in budgets]

def key(protocol, seed, method, budget, scope):
    item = (protocol, seed, method, budget, scope)
    if item not in grid():
        raise ValueError("condition outside frozen addendum grid")
    return f"{protocol}__s{seed}__{method.lower()}__b{budget}__{scope}"

def output_boundary(output, frozen_roots):
    out = Path(output).resolve()
    for root in frozen_roots:
        frozen = Path(root).resolve()
        if out == frozen or out.is_relative_to(frozen) or frozen.is_relative_to(out):
            raise ValueError("output overlaps a frozen root")
    return out

def validate_probabilities(ids, p):
    ids, p = np.asarray(ids), np.asarray(p)
    if ids.ndim != 1 or p.ndim != 2 or len(ids) != len(p) or not len(ids) or p.shape[1] < 2:
        raise ValueError("invalid prediction shape")
    if len(set(map(str, ids))) != len(ids):
        raise ValueError("duplicate query ID")
    if not np.isfinite(p).all() or (p < 0).any() or (p > 1).any():
        raise ValueError("invalid probabilities")
    if not np.allclose(p.sum(1), 1, atol=2e-6):
        raise ValueError("probabilities do not sum to one")
    return p

def create_once(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return file_sha(path)
