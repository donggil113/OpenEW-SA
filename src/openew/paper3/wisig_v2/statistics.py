"""Receiver-level paired inference; packets are never resampling units."""

from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np


def receiver_average(differences_by_receiver_seed: Mapping[str, Sequence[float]]) -> dict[str, float]:
    result = {str(receiver): float(np.mean(np.asarray(values, dtype=float))) for receiver, values in differences_by_receiver_seed.items()}
    if not result or any(not np.isfinite(value) for value in result.values()):
        raise ValueError("receiver differences must be finite and nonempty")
    return result


def receiver_bootstrap(values: Sequence[float], *, replicates: int = 10_000, seed: int = 20_260_903) -> dict[str, float | int]:
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("bootstrap needs at least two finite receiver values")
    if replicates <= 0:
        raise ValueError("bootstrap replicates must be positive")
    rng = np.random.default_rng(seed)
    means = np.empty(replicates, dtype=np.float64)
    for offset in range(0, replicates, 1_000):
        count = min(1_000, replicates - offset)
        samples = rng.integers(0, len(values), size=(count, len(values)))
        means[offset : offset + count] = values[samples].mean(axis=1)
    lower, upper = np.quantile(means, [0.025, 0.975])
    return {
        "receiver_count": len(values),
        "replicates": replicates,
        "mean_difference": float(values.mean()),
        "ci95_lower": float(lower),
        "ci95_upper": float(upper),
        "rng_seed": seed,
    }


def clustered_bootstrap(
    values_by_cluster: Mapping[str, Sequence[float]],
    *,
    replicates: int = 10_000,
    seed: int = 20_260_903,
) -> dict[str, float | int | list[str]]:
    """Secondary top-level cluster bootstrap, preserving receivers in a family.

    Hardware families are sampled with replacement.  Every selected family
    contributes all of its receiver-level differences; packets and seeds are
    never sampled as independent observations.
    """

    if len(values_by_cluster) < 2:
        raise ValueError("cluster bootstrap needs at least two clusters")
    clusters = sorted(str(value) for value in values_by_cluster)
    arrays = {key: np.asarray(values_by_cluster[key], dtype=np.float64) for key in clusters}
    if any(value.ndim != 1 or not len(value) or not np.isfinite(value).all() for value in arrays.values()):
        raise ValueError("every cluster must contain finite receiver values")
    if replicates <= 0:
        raise ValueError("bootstrap replicates must be positive")
    observed = np.concatenate([arrays[key] for key in clusters])
    rng = np.random.default_rng(seed)
    means = np.empty(replicates, dtype=np.float64)
    for index in range(replicates):
        sampled = rng.choice(clusters, size=len(clusters), replace=True)
        means[index] = np.concatenate([arrays[str(key)] for key in sampled]).mean()
    lower, upper = np.quantile(means, [0.025, 0.975])
    return {
        "cluster_count": len(clusters),
        "clusters": clusters,
        "receiver_count": len(observed),
        "replicates": replicates,
        "mean_difference": float(observed.mean()),
        "ci95_lower": float(lower),
        "ci95_upper": float(upper),
        "rng_seed": seed,
    }


def receiver_sign_flip(values: Sequence[float], *, permutations: int = 100_000, seed: int = 20_260_903) -> dict[str, float | int | str]:
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("sign-flip test needs at least two finite receiver values")
    if permutations <= 0:
        raise ValueError("permutations must be positive")
    observed = abs(float(values.mean()))
    extreme = 0
    rng = np.random.default_rng(seed)
    for offset in range(0, permutations, 5_000):
        count = min(5_000, permutations - offset)
        signs = rng.choice(np.asarray([-1.0, 1.0]), size=(count, len(values)))
        permuted = np.abs((signs * values).mean(axis=1))
        extreme += int((permuted >= observed - 1e-15).sum())
    return {
        "receiver_count": len(values),
        "method": "two-sided Monte Carlo receiver sign flip",
        "permutations": permutations,
        "observed_mean_difference": float(values.mean()),
        "p_value": float((extreme + 1) / (permutations + 1)),
        "rng_seed": seed,
    }


def holm_adjust(p_values: Mapping[str, float]) -> dict[str, float]:
    if not p_values:
        return {}
    if any(not 0.0 <= float(value) <= 1.0 for value in p_values.values()):
        raise ValueError("p-values must be within [0,1]")
    ordered = sorted(p_values, key=lambda key: (float(p_values[key]), key))
    adjusted: dict[str, float] = {}
    running = 0.0
    total = len(ordered)
    for index, key in enumerate(ordered):
        candidate = min(1.0, (total - index) * float(p_values[key]))
        running = max(running, candidate)
        adjusted[key] = running
    return adjusted


def descriptive_summary(values: Sequence[float]) -> dict[str, float | int]:
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all():
        raise ValueError("summary needs finite values")
    return {
        "count": len(values),
        "mean": float(values.mean()),
        "std": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
        "median": float(np.median(values)),
        "min": float(values.min()),
        "max": float(values.max()),
    }
