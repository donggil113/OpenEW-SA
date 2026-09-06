"""Probability-quality metrics with explicit binning and source-only temperature fitting."""
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import logsumexp
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from .contracts import validate_probabilities

def checked(labels, p):
    p = np.asarray(p, dtype=np.float64)
    validate_probabilities(np.arange(len(p)), p)
    y = np.asarray(labels)
    if y.ndim != 1 or len(y) != len(p) or y.dtype.kind not in "iu" or (y < 0).any() or (y >= p.shape[1]).any():
        raise ValueError("labels do not match probabilities")
    return y.astype(np.int64), p

def reliability(labels, p, bins=15, adaptive=False):
    y, p = checked(labels, p)
    if not isinstance(bins, int) or bins <= 0:
        raise ValueError("invalid bin count")
    confidence = p.max(1)
    correct = p.argmax(1) == y
    if adaptive:
        groups = np.array_split(np.argsort(confidence, kind="stable"), bins)
    else:
        assignment = np.minimum((confidence * bins).astype(int), bins-1)
        groups = [np.flatnonzero(assignment == i) for i in range(bins)]
    rows = []
    for i, indices in enumerate(groups):
        rows.append({"bin": i, "count": len(indices), "mass": len(indices)/len(y),
                     "confidence": float(confidence[indices].mean()) if len(indices) else None,
                     "accuracy": float(correct[indices].mean()) if len(indices) else None,
                     "lower": i/bins if not adaptive else None, "upper": (i+1)/bins if not adaptive else None})
    return rows

def probability_metrics(labels, p):
    y, p = checked(labels, p)
    conf = p.max(1)
    correct = p.argmax(1) == y
    rows = reliability(y, p)
    adaptive = reliability(y, p, adaptive=True)
    ece = lambda r: float(sum(a["mass"]*abs(a["confidence"]-a["accuracy"]) for a in r if a["count"]))
    logp = np.log(np.clip(p, 1e-12, 1))
    one_hot = np.eye(p.shape[1])[y]
    return {"macro_f1": float(f1_score(y, p.argmax(1), average="macro", zero_division=0)),
            "accuracy": float(accuracy_score(y, p.argmax(1))),
            "balanced_accuracy": float(balanced_accuracy_score(y, p.argmax(1))),
            "ece": ece(rows), "adaptive_ece": ece(adaptive),
            "nll": float(-logp[np.arange(len(y)), y].mean()),
            "brier": float(np.square(p-one_hot).sum(1).mean()),
            "mean_confidence": float(conf.mean()), "mean_correctness": float(correct.mean()),
            "confidence_accuracy_gap": float(conf.mean()-correct.mean()),
            "entropy": float(-(p*logp).sum(1).mean())}

def apply_temperature(p, temperature):
    p = np.asarray(p, dtype=np.float64)
    validate_probabilities(np.arange(len(p)), p)
    if not np.isfinite(temperature) or temperature <= 0:
        raise ValueError("temperature must be finite positive")
    logp = np.log(np.clip(p, 1e-12, 1)) / temperature
    return np.exp(logp - logsumexp(logp, axis=1, keepdims=True))

def fit_source_temperature(labels, probabilities, receivers, *, role):
    if role != "source_validation":
        raise ValueError("temperature fitting is source-validation only")
    y, p = checked(labels, probabilities)
    r = np.asarray(receivers).astype(str)
    if r.ndim != 1 or len(r) != len(y) or len(set(r)) < 2:
        raise ValueError("multiple source validation receiver groups required")
    logp = np.log(np.clip(p, 1e-12, 1))
    groups = [np.flatnonzero(r == value) for value in sorted(set(r))]
    def objective(log_t):
        scores = logp / np.exp(log_t)
        losses = logsumexp(scores, axis=1)-scores[np.arange(len(y)), y]
        return float(np.mean([losses[g].mean() for g in groups]))
    result = minimize_scalar(objective, bounds=(np.log(.05), np.log(20)), method="bounded",
                             options={"xatol": 1e-8})
    if not result.success:
        raise RuntimeError("source temperature optimization failed")
    return {"temperature": float(np.exp(result.x)), "source_nll_before": objective(0),
            "source_nll_after": float(result.fun), "role": role, "receiver_count": len(groups),
            "bounds": [.05,20], "target_labels_used": False}
