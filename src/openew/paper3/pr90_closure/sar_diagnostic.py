"""Instrumented SAR state machine. New diagnostics; frozen PR90 implementation is untouched.

One pass at threshold 0.2 intentionally reproduces the frozen local execution.
Differences from upstream are documented in sar_state_machine_fidelity.md.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import math

import torch

from openew.paper3.reviewer_remediation.methods import entropy, finite_tensor, norm_parameters


@dataclass(frozen=True)
class TraceConfig:
    passes: int = 1
    reset_threshold: float = 0.2
    learning_rate: float = 0.00025
    margin_fraction: float = 0.4
    rho: float = 0.05
    momentum: float = 0.9

    def validate(self) -> "TraceConfig":
        if self.passes not in (1, 5, 20):
            raise ValueError("passes outside source-only plan")
        if not (0 < self.reset_threshold < 1):
            raise ValueError("invalid reset threshold")
        if self.learning_rate <= 0 or self.rho < 0 or not (0 < self.margin_fraction < 1):
            raise ValueError("invalid SAR parameters")
        return self


def tensor_state_sha256(state: dict[str, torch.Tensor]) -> str:
    """Deterministic tensor-content digest, independent of torch ZIP metadata."""
    h = hashlib.sha256()
    for name, tensor in sorted(state.items()):
        value = tensor.detach().cpu().contiguous()
        h.update(name.encode("utf-8"))
        h.update(str(value.dtype).encode("ascii"))
        h.update(repr(tuple(value.shape)).encode("ascii"))
        h.update(value.numpy().tobytes())
    return h.hexdigest()


def state_comparison(left: dict[str, torch.Tensor], right: dict[str, torch.Tensor]) -> dict:
    if set(left) != set(right):
        raise ValueError("model state keys differ")
    exact = True
    max_abs = 0.0
    changed = 0
    for key in sorted(left):
        x, y = left[key].detach().cpu(), right[key].detach().cpu()
        if x.shape != y.shape or x.dtype != y.dtype:
            raise ValueError(f"model state shape/dtype differs at {key}")
        same = torch.equal(x, y)
        exact &= same
        changed += not same
        max_abs = max(max_abs, float((x-y).abs().max()) if x.numel() else 0.0)
    return {"exact": bool(exact), "changed_tensors": changed, "max_abs": max_abs}


def adapt_with_trace(source, support: torch.Tensor, class_count: int,
                     config: TraceConfig = TraceConfig()):
    """Support-only SAR with per-minibatch states; query/labels are absent from API."""
    config.validate()
    finite_tensor(support, 3)
    if class_count < 2 or len(support) < 1:
        raise ValueError("nonempty support and >=2 classes required")
    model = deepcopy(source).train()
    model.requires_grad_(False)
    named = norm_parameters(model)
    params = [p for _, p in named]
    for p in params:
        p.requires_grad_(True)
    initial = deepcopy(model.state_dict())
    optimizer = torch.optim.SGD(params, lr=config.learning_rate, momentum=config.momentum)
    margin = config.margin_fraction * math.log(class_count)
    ema = None
    rows = []
    for pass_index in range(config.passes):
        for offset in range(0, len(support), 64):
            batch = support[offset:offset+64]
            lr = config.learning_rate if len(batch) >= 32 else config.learning_rate/64*len(batch)*2
            for group in optimizer.param_groups:
                group["lr"] = lr
            optimizer.zero_grad(set_to_none=True)
            first_entropy = entropy(model(batch))
            keep = first_entropy < margin
            row = {"pass": pass_index+1, "offset": offset, "batch_size": len(batch),
                   "first_retained": int(keep.sum()), "second_retained": 0,
                   "first_backward": False, "second_backward": False,
                   "optimizer_step": False, "reset": False,
                   "empty_first": False, "empty_second": False,
                   "ema_before": ema, "ema_after": ema,
                   "momentum_before": sum("momentum_buffer" in optimizer.state.get(p,{}) for p in params),
                   "momentum_after": None}
            if not keep.any():
                row["empty_first"] = True
                row["momentum_after"] = row["momentum_before"]
                rows.append(row)
                continue
            first_entropy[keep].mean().backward()
            row["first_backward"] = True
            norm = torch.linalg.vector_norm(torch.stack([p.grad.norm() for p in params if p.grad is not None]))
            originals = [p.detach().clone() for p in params]
            with torch.no_grad():
                for p in params:
                    if p.grad is not None:
                        p.add_(p.grad * (config.rho/(norm+1e-12)))
            optimizer.zero_grad(set_to_none=True)
            try:
                second = entropy(model(batch))[keep]
                reliable = second < margin
                row["second_retained"] = int(reliable.sum())
                if not reliable.any():
                    row["empty_second"] = True
                    row["momentum_after"] = row["momentum_before"]
                    rows.append(row)
                    continue
                loss = second[reliable].mean()
                if not torch.isfinite(loss):
                    raise FloatingPointError("nonfinite second-pass entropy")
                loss.backward()
                row["second_backward"] = True
                current = float(loss.detach())
                ema = current if ema is None else .9*ema+.1*current
            finally:
                with torch.no_grad():
                    for p, original in zip(params, originals):
                        p.copy_(original)
            optimizer.step()
            row["optimizer_step"] = True
            if ema is not None and ema < config.reset_threshold:
                model.load_state_dict(initial)
                optimizer.state.clear()
                row["reset"] = True
            row["ema_after"] = ema
            row["momentum_after"] = sum("momentum_buffer" in optimizer.state.get(p,{}) for p in params)
            rows.append(row)
    model.eval().requires_grad_(False)
    summary = {"attempted_updates": len(rows),
               "completed_optimizer_updates": sum(r["optimizer_step"] for r in rows),
               "resets": sum(r["reset"] for r in rows),
               "empty_first": sum(r["empty_first"] for r in rows),
               "empty_second": sum(r["empty_second"] for r in rows),
               "first_retained_total": sum(r["first_retained"] for r in rows),
               "second_retained_total": sum(r["second_retained"] for r in rows),
               "first_retained_min": min(r["first_retained"] for r in rows),
               "second_retained_min": min(r["second_retained"] for r in rows),
               "first_retained_max": max(r["first_retained"] for r in rows),
               "second_retained_max": max(r["second_retained"] for r in rows),
               "final_ema": ema, "final_state_sha256": tensor_state_sha256(model.state_dict()),
               "source_state_sha256": tensor_state_sha256(initial),
               "source_state_comparison": state_comparison(model.state_dict(), initial),
               "final_momentum_buffers": sum("momentum_buffer" in optimizer.state.get(p,{}) for p in params),
               "adapted_parameter_names": [name for name,_ in named]}
    return model, summary, rows
