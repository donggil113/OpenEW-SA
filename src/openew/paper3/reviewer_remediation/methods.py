"""Frozen support-only controls. No query or annotation inputs in deployable adapters.

SAR equations and parameter policy: Niu et al. ICLR2023, official SAR
20f6e24b17525f34503510afccedc0629b67b7c4. Independently expressed here;
bounded-support prediction protocol differs from original online evaluation.
"""
from copy import deepcopy
import math
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

ORACLE_GRID = tuple((lr, steps) for lr in (1e-5, 1e-4, 5e-4) for steps in (5, 20))

def finite_tensor(x, ndim=None):
    if ndim is not None and x.ndim != ndim:
        raise ValueError("tensor dimension mismatch")
    if not torch.isfinite(x).all():
        raise ValueError("nonfinite input")
    return x

def norm_parameters(model):
    selected = []
    for name, module in model.named_modules():
        if any(t in name for t in ("layer4", "blocks.9", "blocks.10", "blocks.11", "norm.")) or name == "norm":
            continue
        if isinstance(module, nn.GroupNorm):
            for param_name, param in module.named_parameters(recurse=False):
                if param_name in ("weight", "bias"):
                    selected.append((name + "." + param_name, param))
    if not selected:
        raise ValueError("SAR-GN requires existing GroupNorm affine parameters")
    return selected

def entropy(logits):
    return -(logits.softmax(-1) * logits.log_softmax(-1)).sum(-1)

def sar_adapt(source, support, class_count):
    """Copy source, adapt GN affine on support only, return frozen model + diagnostics."""
    finite_tensor(support, 3)
    model = deepcopy(source)
    model.train()
    model.requires_grad_(False)
    named = norm_parameters(model)
    params = [p for _, p in named]
    for p in params:
        p.requires_grad_(True)
    if class_count < 2:
        raise ValueError("class count must exceed one")
    initial = deepcopy(model.state_dict())
    optimizer = torch.optim.SGD(params, lr=.00025, momentum=.9)
    ema = None
    report = {"gradient_steps": 0, "sam_backward_passes": 0, "recoveries": 0,
              "empty_first_filter": 0, "empty_second_filter": 0,
              "adapted_parameters": sum(p.numel() for p in params), "parameter_names": [n for n, _ in named]}
    for offset in range(0, len(support), 64):
        batch = support[offset:offset + 64]
        rate = .00025 if len(batch) >= 32 else .00025 / 64 * len(batch) * 2
        for group in optimizer.param_groups:
            group["lr"] = rate
        optimizer.zero_grad(set_to_none=True)
        values = entropy(model(batch))
        keep = values < .4 * math.log(class_count)
        if not keep.any():
            report["empty_first_filter"] += 1
            continue
        values[keep].mean().backward()
        report["sam_backward_passes"] += 1
        norm = torch.linalg.vector_norm(torch.stack([p.grad.norm() for p in params if p.grad is not None]))
        originals = [p.detach().clone() for p in params]
        with torch.no_grad():
            for p in params:
                if p.grad is not None:
                    p.add_(p.grad * (.05 / (norm + 1e-12)))
        optimizer.zero_grad(set_to_none=True)
        try:
            second = entropy(model(batch))[keep]
            reliable = second < .4 * math.log(class_count)
            if not reliable.any():
                report["empty_second_filter"] += 1
                continue
            loss = second[reliable].mean()
            if not torch.isfinite(loss):
                raise FloatingPointError("nonfinite SAR entropy")
            loss.backward()
            report["sam_backward_passes"] += 1
            current = float(loss.detach())
            ema = current if ema is None else .9 * ema + .1 * current
        finally:
            with torch.no_grad():
                for p, value in zip(params, originals):
                    p.copy_(value)
        optimizer.step()
        report["gradient_steps"] += 1
        if ema is not None and ema < .2:
            model.load_state_dict(initial)
            optimizer.state.clear()
            report["recoveries"] += 1
            # Official SAR.forward retains returned EMA after reset.
    model.eval()
    model.requires_grad_(False)
    report["entropy_ema"] = ema
    return model, report

def moments(embeddings):
    a = np.asarray(embeddings, dtype=np.float64)
    if a.ndim != 2 or len(a) < 1 or not np.isfinite(a).all():
        raise ValueError("moments require nonempty finite embeddings")
    return a.mean(0), np.maximum(a.std(0, ddof=0), 1e-6)

def transport_embeddings(query_embeddings, support_embeddings, source_moments):
    q = np.asarray(query_embeddings, dtype=np.float64)
    if q.ndim != 2 or not np.isfinite(q).all():
        raise ValueError("invalid query embeddings")
    if len(support_embeddings) == 0:
        return q.astype(np.float32)
    mu, sigma = moments(support_embeddings)
    source_mu, source_sigma = map(np.asarray, source_moments)
    if source_mu.shape != mu.shape or source_sigma.shape != sigma.shape or q.shape[1] != len(mu):
        raise ValueError("source/target embedding dimensions mismatch")
    if not np.isfinite(source_mu).all() or not np.isfinite(source_sigma).all() or (source_sigma <= 0).any():
        raise ValueError("invalid source moments")
    result = ((q - mu) / sigma * source_sigma + source_mu).astype(np.float32)
    if not np.isfinite(result).all():
        raise FloatingPointError("nonfinite transported embeddings")
    return result

def supervised_full(source, support, labels, recipe):
    """LABEL-DEPENDENT ORACLE. No query input; never a deployable method."""
    if tuple(recipe) not in ORACLE_GRID:
        raise ValueError("oracle recipe outside frozen source-only grid")
    finite_tensor(support, 3)
    if labels.ndim != 1 or len(labels) != len(support) or not len(labels):
        raise ValueError("oracle label alignment")
    model = deepcopy(source).train()
    model.requires_grad_(True)
    if labels.dtype != torch.long or labels.min() < 0 or labels.max() >= model.classifier.out_features:
        raise ValueError("invalid oracle class labels")
    optimizer = torch.optim.AdamW(model.parameters(), lr=recipe[0], weight_decay=0)
    losses = []
    for _ in range(recipe[1]):
        optimizer.zero_grad(set_to_none=True)
        loss = F.cross_entropy(model(support), labels)
        if not torch.isfinite(loss):
            raise FloatingPointError("nonfinite oracle loss")
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach()))
    model.eval()
    model.requires_grad_(False)
    return model, {"gradient_steps": recipe[1], "adapted_parameters": sum(p.numel() for p in model.parameters()), "losses": losses,
                   "oracle": True, "support_labels_revealed": True}
