"""Synthetic original-CPU-do_sample interface probe, no model/image loading."""
import ast
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import random
import signal
import sys
import time
from types import SimpleNamespace

START = time.monotonic()
UTC = dt.datetime.now(dt.timezone.utc).isoformat()
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("55s interface budget")))
signal.alarm(55)
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
import torch
from s20_generation_trace import TraceWriter, verify_trace, tensor_identity

torch.set_num_threads(2)
SRC = ROOT / "work/S20_environment/isolated_vmem_source/utils/util.py"
MODULE = ROOT / "src/s20_generation_trace.py"
identities = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (SRC, MODULE, Path(__file__))}
checks, modes = [], []


def check(name, cond):
    if not cond:
        raise AssertionError(name)
    checks.append(name)


def seed():
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)


def state():
    return {"torch": tensor_identity(torch.get_rng_state()), "python": random.getstate(),
            "np_name": np.random.get_state()[0], "np_array": tensor_identity(np.random.get_state()[1]),
            "np_other": np.random.get_state()[2:]}


class AE:
    def decode(self, z, decoding_t):
        modes.append({"grad": torch.is_grad_enabled(), "inference": torch.is_inference_mode_enabled(),
                      "input_shape": list(z.shape), "decoding_t": decoding_t})
        return z.repeat(1, 3, 1, 1)


def denoiser(model, x, sigma, cond, num_frames):
    if num_frames != 8:
        raise ValueError("unexpected frame count")
    return x + .01


def sampler(callback, noise, **kw):
    check_name = None  # No test counter side effects in the delegated mathematics.
    if kw["c2w"].device.type != "cpu" or kw["K"].device.type != "cpu":
        raise ValueError("CPU adapter transfer not used")
    z = noise.clone()
    for i in range(3):
        z = callback(z + torch.randn_like(z) * 0, torch.full((8,), float(3 - i)), kw["cond"])
    return z


def make_pipeline():
    return SimpleNamespace(pil_frames=[None] * 5,
        latents=[np.full((1, 2, 2), i, np.float32) for i in range(5)],
        encoder_embeddings=[np.full(3, i, np.float32) for i in range(5)],
        c2ws=[np.eye(4, dtype=np.float32) for _ in range(5)],
        Ks=[np.eye(3, dtype=np.float32) for _ in range(5)],
        surfels=[], surfel_to_timestep={}, surfel_Ks=[None] * 5)


def context(p, ids):
    d = {"context_time_indices": ids}
    for a, b in (("latents", "context_latents"), ("encoder_embeddings", "context_encoder_embeddings"),
                 ("c2ws", "context_c2ws"), ("Ks", "context_Ks")):
        d[b] = torch.stack([torch.from_numpy(getattr(p, a)[int(i)]) for i in ids])
    return d


try:
    source = SRC.read_text()
    definitions = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "do_sample"]
    check("unique actual adapter function", len(definitions) == 1)
    node = definitions[0]
    extracted = ast.get_source_segment(source, node)
    (OUT / "extracted_do_sample.py").write_text(extracted + "\n")
    namespace = {"torch": torch, "math": math}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(SRC), "exec"), namespace)
    do_sample = namespace["do_sample"]
    check("extracted CPU function retains inference scope", 'torch.inference_mode()' in extracted and 'device = torch.device(device)' in extracted)
    ids = torch.tensor([0, 2, 2, 4], dtype=torch.int64)
    p = make_pipeline()
    tc, tk = torch.eye(4).repeat(4, 1, 1), torch.eye(3).repeat(4, 1, 1)
    c = {"vector": torch.zeros(8, 2)}
    mask = torch.tensor([True] * 4 + [False] * 4)
    args = (None, AE(), denoiser, sampler, c, c, torch.eye(4).repeat(8, 1, 1), torch.eye(3).repeat(8, 1, 1), mask)
    kwargs = dict(H=4, W=4, C=1, F=2, T=8, cfg=1.2, return_latents=True, device=torch.device("cpu"), verbose=False)
    outer_mode = (torch.is_grad_enabled(), torch.is_inference_mode_enabled())
    seed()
    plain = do_sample(*args, **kwargs)
    plain_state = state()
    check("plain restores outer grad/inference scope", outer_mode == (torch.is_grad_enabled(), torch.is_inference_mode_enabled()))
    seed()
    w = TraceWriter(OUT / "actual_function_synthetic_trace", evidence_kind="synthetic_test", source_identities=identities)
    with w.batch("second_batch_tensor_ids", p, context(p, ids), tc, tk, padding_size=0) as batch:
        traced = batch.sample(do_sample, *args, **kwargs)
        traced_state = state()
        check("actual do_sample samples identical", torch.equal(plain[0], traced[0]))
        check("actual do_sample latents identical", torch.equal(plain[1], traced[1]))
        check("all captured CPU random states unchanged by observation", plain_state == traced_state)
        check("wrapped restores outer grad/inference scope", outer_mode == (torch.is_grad_enabled(), torch.is_inference_mode_enabled()))
        embedding = torch.arange(12, dtype=torch.float32).reshape(4, 3)
        for j in range(4):
            p.latents.append(traced[1][4 + j].detach().cpu().numpy())
            p.encoder_embeddings.append(embedding[j].numpy())
            p.c2ws.append(tc[j].numpy())
            p.Ks.append(tk[j].numpy())
            p.pil_frames.append(None)
        batch.commit_cache(target_encoder_embeddings=embedding)
        # Empty synthetic map. No original construction, geometry or model run.
        p.surfel_Ks.extend(p.Ks)
        batch.commit_map()
    w.close()
    verified = verify_trace(w.root)
    check("complete interface trace valid", verified["status"] == "VALID_CLOSED_TRACE")
    check("callee inference scope unchanged", modes == [{"grad": False, "inference": True, "input_shape": [8, 1, 2, 2], "decoding_t": 1}] * 2)
    rows = [json.loads(v) for v in w.path.read_text().splitlines()]
    begin = next(r["payload"] for r in rows if r["event"] == "batch_begin")
    check("actual Torch int64 ID layout preserves order and duplicate", begin["selected_context_ids"] == [0, 2, 2, 4])
    noise = next(r["payload"]["noise"] for r in rows if r["event"] == "sampler_enter")
    seed()
    check("actual adapter initial randn exact", tensor_identity(torch.randn(8, 1, 2, 2))["sha256"] == noise["sha256"])
    bad = TraceWriter(OUT / "bad_torch_ids", evidence_kind="synthetic_test", source_identities=identities)
    for label, invalid in (("float", ids.float()), ("bool", torch.tensor([True] * 4)), ("rank2", ids.reshape(2, 2))):
        info = context(p, ids)
        info["context_time_indices"] = invalid
        try:
            bad.batch(label, p, info, tc, tk, padding_size=0)
        except ValueError:
            checks.append(label + " context ID tensor rejected")
        else:
            raise AssertionError("invalid Torch IDs accepted")
    bad.close()
    check("rejected Tensor IDs leave intact trace", verify_trace(bad.root)["status"] == "VALID_CLOSED_TRACE")
    result = {"status": "PASS_ORIGINAL_CPU_DO_SAMPLE_INTERFACE_SYNTHETIC_ONLY", "started_utc": UTC,
              "completed_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "seconds": time.monotonic() - START,
              "checks": checks, "check_count": len(checks), "identities": identities,
              "adapter_function_ast_sha256": hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest(),
              "torch": torch.__version__, "numpy": np.__version__, "verification": verified,
              "original_cpu_do_sample_calls": 2, "actual_generator_model_calls": 0, "real_images": 0,
              "GT": 0, "NPZ_reads": 0, "sampler_ae_denoiser": "synthetic replacements", "actual_vmem_loop_connected": False}
except BaseException as error:
    result = {"status": "FAIL_SYNTHETIC_INTERFACE", "error": repr(error), "checks_passed": checks,
              "identities": identities, "seconds": time.monotonic() - START}
    (OUT / "receipt.json").write_text(json.dumps(result, indent=2) + "\n")
    raise
else:
    (OUT / "receipt.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "seconds", "check_count")}))
finally:
    signal.alarm(0)
