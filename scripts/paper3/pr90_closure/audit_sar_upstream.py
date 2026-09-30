"""Compare frozen local state transitions with official SAR commit on synthetic inputs."""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from copy import deepcopy
import importlib.util
import io
import json
from pathlib import Path

import numpy as np
import torch

from openew.paper3.pr90_closure.sar_diagnostic import TraceConfig, adapt_with_trace, state_comparison
from openew.paper3.reviewer_remediation.contracts import file_sha
from openew.paper3.wisig.models import IndependentClassifier


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source(bias):
    torch.manual_seed(1)
    model = IndependentClassifier(6).eval()
    with torch.no_grad():
        model.classifier.weight.mul_(0.05)
        model.classifier.bias.zero_()
        model.classifier.bias[0] = bias
    return model, torch.randn(128, 256, 2)


def upstream_adapter(sar, sam, model, reset_constant):
    copied = sar.configure_model(deepcopy(model))
    selected, _ = sar.collect_params(copied)
    adapter = sar.SAR(copied, sam.SAM(selected, torch.optim.SGD, lr=0.00025, momentum=0.9),
                      margin_e0=0.4*np.log(6), reset_constant_em=reset_constant)
    return adapter


def run(official):
    sar_path = official / "sar.py"
    sam_path = official / "sam.py"
    sar = load("official_sar_pr90", sar_path)
    sam = load("official_sam_pr90", sam_path)
    nonreset, support = source(3.5)
    ours, own_trace, _ = adapt_with_trace(nonreset, support, 6, TraceConfig())
    adapter = upstream_adapter(sar, sam, nonreset, reset_constant=0.9)
    with redirect_stdout(io.StringIO()):
        first_return = adapter(support[:64])
        adapter(support[64:])
    nonreset_comparison = state_comparison(ours.state_dict(), adapter.model.state_dict())
    if not nonreset_comparison["exact"] or own_trace["resets"] != 0:
        raise AssertionError("two-minibatch noncollapse parity failed")
    if adapter.ema is None or adapter.ema >= 0.9:
        raise AssertionError("unexpected upstream EMA")
    # The official wrapper returns logits computed before its optimizer step.
    with torch.no_grad():
        returned_output_equals_prestep = torch.equal(first_return, nonreset(support[:64]))
    low_entropy, support = source(6)
    adapter_reset = upstream_adapter(sar, sam, low_entropy, reset_constant=0.1)
    with redirect_stdout(io.StringIO()):
        adapter_reset(support[:64])
    upstream_momentum_after_reset = sum(
        "momentum_buffer" in item for item in adapter_reset.optimizer.base_optimizer.state.values()
    )
    wrapper_momentum_after_reset = sum(
        "momentum_buffer" in item for item in adapter_reset.optimizer.state.values()
    )
    if upstream_momentum_after_reset <= 0 or wrapper_momentum_after_reset:
        raise AssertionError("upstream SAM/base-SGD reset asymmetry not reproduced")
    high_threshold, support = source(3.5)
    adapter_parameter = upstream_adapter(sar, sam, high_threshold, reset_constant=0.9)
    with redirect_stdout(io.StringIO()):
        adapter_parameter(support[:64])
    threshold_ignored = state_comparison(adapter_parameter.model.state_dict(), high_threshold.state_dict())["changed_tensors"] > 0
    if not threshold_ignored:
        raise AssertionError("official reset_constant branch behavior changed; re-audit")
    return {
        "official_commit_expected": "20f6e24b17525f34503510afccedc0629b67b7c4",
        "sar_sha256": file_sha(sar_path), "sam_sha256": file_sha(sam_path),
        "scope": "synthetic two-minibatch noncollapse parity plus one-reset optimizer/threshold probes",
        "noncollapse_local_vs_upstream": nonreset_comparison,
        "official_returned_logits_are_preupdate": returned_output_equals_prestep,
        "official_reset_constant_0_9_ignored_by_branch": threshold_ignored,
        "official_base_sgd_momentum_buffers_after_wrapper_reset": upstream_momentum_after_reset,
        "official_sam_wrapper_momentum_buffers_after_wrapper_reset": wrapper_momentum_after_reset,
        "official_ema_retained_after_wrapper_reset": adapter_reset.ema is not None,
        "empty_reliable_subset_parity_tested": False,
        "upstream_online_query_protocol_parity_tested": False,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--official", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    payload = run(args.official)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(payload, indent=2))
