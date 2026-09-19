#!/usr/bin/env python3
"""One author-only batch: original sampler + tiny deterministic stub; no model."""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time
import traceback
import types
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS"):
    os.environ[key] = "1"
sys.dont_write_bytecode = True


def sha(data):
    return hashlib.sha256(data).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def main():
    contract_raw = (BASE / "HOOK_SYNTHETIC_CONTRACT.json").read_bytes()
    contract = json.loads(contract_raw)
    out = BASE / "synthetic_hooks_01"
    out.mkdir(exist_ok=False)
    began = time.monotonic()
    result = dict(status="STARTED", started_utc=utc(), reads=[], checks=[],
                  contract_sha256=sha(contract_raw), model_instances=0,
                  real_array_reads=0, real_RGB_reads=0, learned_model_forwards=0)
    code = 1

    def check(name, passed):
        result["checks"].append(dict(name=name, passed=bool(passed)))
        if not passed:
            raise AssertionError(name)

    def load(name, item):
        path = Path(item["path"])
        data = path.read_bytes()
        result["reads"].append(dict(path=str(path), bytes=len(data), sha256=sha(data)))
        if sha(data) != item["sha256"]:
            raise ValueError("source identity mismatch " + name)
        module = types.ModuleType(name)
        module.__file__ = str(path)
        sys.modules[name] = module
        exec(compile(data, str(path), "exec"), module.__dict__)
        return module

    def timeout(signum, frame):
        raise TimeoutError("90 second artificial batch exceeded")

    previous = signal.signal(signal.SIGALRM, timeout)
    signal.alarm(90)
    try:
        check("checker source identity", sha(Path(__file__).read_bytes()) == contract["checker_sha256"])
        import torch
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        torch.set_default_dtype(torch.float32)
        check("Torch version", torch.__version__ == contract["torch_version"])
        sampling = load("s86_original_sampling", contract["sources"]["sampling"])
        hooks = load("s86_hooks", contract["sources"]["hooks"])
        fusion = load("s86_pure_fusion", contract["sources"]["fusion"])
        body = lambda t: t.detach().cpu().contiguous().numpy().tobytes()
        rng = lambda: body(torch.get_rng_state())
        hist = torch.tensor([True] * 4 + [False] * 4)
        mask = torch.ones(8, 1, 2, 3)
        mask[:, :, 0, 0] = 0
        warp = torch.linspace(-0.75, 0.75, 96).reshape(8, 2, 2, 3)
        c = {"crossattn": torch.arange(96, dtype=torch.float32).reshape(8, 2, 2, 3) / 1000}
        uc = {"crossattn": torch.zeros_like(c["crossattn"])}
        poses = torch.eye(4).repeat(8, 1, 1)
        poses[:, 0, 3] = torch.arange(8, dtype=torch.float32) / 10
        K = torch.eye(3).repeat(8, 1, 1)
        torch.manual_seed(86)
        common = torch.get_rng_state().clone()
        all_stub_calls = []
        records = {}
        protected = (hist[:, None, None, None] | (mask == 0)).expand_as(warp)

        def trajectory(label, mode=None, fail_callback=False):
            sampler = sampling.create_samplers(
                guider_types=1, discretization=sampling.DDPMDiscretization(),
                num_frames=8, num_steps=3, cfg_min=1.2, device="cpu")[0]
            callbacks = []

            def on_clean(step, raw, used):
                callbacks.append(dict(step=step, same_object=raw is used,
                                      raw_sha=sha(body(raw)), used_sha=sha(body(used))))
                if fail_callback:
                    raise RuntimeError("intentional artificial callback failure")
                check(label + f" step {step} protected clean bytes",
                      body(raw[protected]) == body(used[protected]))

            controller = None
            if mode is not None:
                options = dict(mode=mode, expected_steps=3, on_clean=on_clean)
                if mode == "Gguide":
                    options.update(fusion_fn=fusion.fuse_clean_prediction,
                                   warp_latents=warp, support_mask=mask,
                                   history_slots=hist, strengths=[0.0, 0.25, 0.25])
                controller = hooks.install_hooks(sampler, **options)
            delegate = sampler.sampler_step
            trace = []

            def observed(*args, **kwargs):
                entry = dict(rng_before=sha(rng()))
                try:
                    value = delegate(*args, **kwargs)
                    entry["output_sha"] = sha(body(value))
                    return value
                finally:
                    entry["rng_after"] = sha(rng())
                    trace.append(entry)

            sampler.sampler_step = observed

            def stub(x, sigma, cond):
                all_stub_calls.append(label)
                return x * 0.2 + cond["crossattn"]

            torch.set_rng_state(common.clone())
            noise = torch.randn(8, 2, 2, 3)
            initial_sha = sha(body(noise))
            value = None
            failure = None
            try:
                value = sampler(stub, noise, scale=2.0, cond=c, uc=uc,
                                verbose=False, c2w=poses, K=K, input_frame_mask=hist)
            except RuntimeError as error:
                if not fail_callback:
                    raise
                failure = str(error)
            records[label] = dict(initial_noise_sha=initial_sha, trace=trace,
                                  terminal_rng_sha=sha(rng()), callbacks=callbacks,
                                  hook_steps=[] if controller is None else controller.steps,
                                  expected_failure=failure)
            if fail_callback:
                check("callback exception propagated", failure == "intentional artificial callback failure")
                check("callback failure preserved", controller.steps[0]["status"] == "FAILED"
                      and controller.steps[0]["callback_calls"] == 1 and len(controller.steps) == 1)
            elif controller is not None:
                controller.assert_complete()
            return value, controller

        with torch.inference_mode(), torch.autocast(device_type="cpu", enabled=False):
            baseline, _ = trajectory("original")
            g0, control = trajectory("G0", "G0")
            check("G0 all returned bytes exact", body(g0) == body(baseline))
            check("G0 all per-step bytes and RNG exact", records["G0"]["trace"] == records["original"]["trace"])
            check("G0 initial noise exact", records["G0"]["initial_noise_sha"] == records["original"]["initial_noise_sha"])
            check("G0 raw object transparent", all(r["same_object"] for r in records["G0"]["callbacks"]))
            check("G0 full last output exact", body(control.last["output"]) == body(g0))
            prior = rng()
            zero = hooks.replay_last(sampling, control.last)
            check("zero fusion replay exact", body(zero["latents"]) == body(g0))
            check("zero fusion replay raw object", zero["clean_used"] is control.last["raw_clean"])
            terminal = hooks.replay_last(
                sampling, control.last, fusion_fn=fusion.fuse_clean_prediction,
                warp_latents=warp, support_mask=mask, history_slots=hist, strength=0.25)
            check("replay consumes no Torch RNG", prior == rng())
            check("terminal protected clean exact", body(terminal["clean_used"][protected])
                  == body(control.last["raw_clean"][protected]))
            check("terminal has nonzero effect", body(terminal["latents"]) != body(g0))
            guide, guide_control = trajectory("Gguide", "Gguide")
            check("Gguide hook count", len(records["Gguide"]["callbacks"]) == 3)
            check("Gguide preserves original RNG stream",
                  [(r["rng_before"], r["rng_after"]) for r in records["Gguide"]["trace"]]
                  == [(r["rng_before"], r["rng_after"]) for r in records["original"]["trace"]])
            check("zero step preserves object", records["Gguide"]["callbacks"][0]["same_object"])
            check("nonzero guide effect", body(guide) != body(g0))
            trajectory("callback_failure", "G0", fail_callback=True)
        result["records"] = records
        result["actual_stub_calls"] = len(all_stub_calls)
        check("planned stub calls", len(all_stub_calls) == 10)
        result["last_tensor_schema"] = {
            k: dict(shape=list(v.shape), dtype=str(v.dtype), device=str(v.device), body_sha256=sha(body(v)))
            for k, v in control.last.items() if isinstance(v, torch.Tensor)}
        result["last_tensor_schema_Gguide"] = {
            k: dict(shape=list(v.shape), dtype=str(v.dtype), device=str(v.device), body_sha256=sha(body(v)))
            for k, v in guide_control.last.items() if isinstance(v, torch.Tensor)}
        check("artificial RSS budget", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= 1024**3)
        result["status"] = "AUTHOR_ARTIFICIAL_PASS_NOT_REAL_MODEL_VALIDATION"
        code = 0
    except Exception:
        result["status"] = "FAILED_NO_AUTOMATIC_RETRY"
        result["traceback"] = traceback.format_exc()
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
        result["completed_utc"] = utc()
        result["elapsed_seconds"] = time.monotonic() - began
        result["peak_self_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        (out / "RECEIPT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(dict(status=result["status"], receipt=str(out / "RECEIPT.json"))))
    return code


if __name__ == "__main__":
    sys.exit(main())
