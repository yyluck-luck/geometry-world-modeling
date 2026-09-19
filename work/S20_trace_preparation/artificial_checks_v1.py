"""Synthetic-only bounded S20 observer tests. Never imports VMem/loads images."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import random
import signal
import sys
import time
from types import SimpleNamespace

START = time.monotonic()
UTC = dt.datetime.now(dt.timezone.utc).isoformat()
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("55 second synthetic budget")))
signal.alarm(55)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
import torch
from s20_generation_trace import TraceWriter, tensor_identity, verify_trace

torch.set_num_threads(2)
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=False)
checks = []


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    checks.append(name)


def rejects(name, callback):
    try:
        callback()
    except (ValueError, RuntimeError, OSError):
        checks.append(name)
    else:
        raise AssertionError(name)


def pipeline():
    return SimpleNamespace(pil_frames=[None], latents=[np.zeros((1, 2, 2), np.float32)],
        encoder_embeddings=[np.arange(3, dtype=np.float32)], c2ws=[np.eye(4, dtype=np.float32)],
        Ks=[np.eye(3, dtype=np.float32)], surfels=[], surfel_to_timestep={}, surfel_Ks=[])


def context(p, ids):
    d = {"context_time_indices": ids}
    for a, b in (("latents", "context_latents"), ("encoder_embeddings", "context_encoder_embeddings"),
                 ("c2ws", "context_c2ws"), ("Ks", "context_Ks")):
        d[b] = torch.stack([torch.from_numpy(getattr(p, a)[i]) for i in ids])
    return d


def fake_sampler(denoiser, noise, **kwargs):
    z = noise.clone()
    for i in range(3):
        z = z + torch.randn_like(z) * 0  # Consumes RNG even with zero coefficient.
        z = denoiser(z, torch.full((len(z),), 3 - i, dtype=z.dtype), kwargs["cond"])
    return z


def fake_do_sample(model, ae, denoiser, sampler, c, uc, c2w, K, cond_frames_mask,
                   H=4, W=4, C=1, F=2, T=8, cfg=1.2, return_latents=True, device="cpu"):
    z = sampler(lambda x, sigma, cond: x + 0.1, torch.randn((T, C, H // F, W // F)),
                scale=cfg, cond=c, uc=uc, c2w=c2w, K=K, input_frame_mask=cond_frames_mask)
    if z is None:
        return None
    return z.repeat(1, 3, 1, 1), z


def seed():
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)


SOURCES = {"synthetic_fixture": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "trace_module": hashlib.sha256((ROOT / "src/s20_generation_trace.py").read_bytes()).hexdigest()}


def execute(p, ids, padding, batch=None):
    nt = 8 - len(ids)
    tc = torch.eye(4).repeat(nt, 1, 1)
    tk = torch.eye(3).repeat(nt, 1, 1)
    mask = torch.tensor([True] * len(ids) + [False] * nt)
    c = {"vector": torch.zeros(8, 2)}
    args = (None, None, None, fake_sampler, c, c, torch.eye(4).repeat(8, 1, 1),
            torch.eye(3).repeat(8, 1, 1), mask)
    sample = batch.sample(fake_do_sample, *args) if batch else fake_do_sample(*args)
    emb = torch.arange(nt * 3, dtype=torch.float32).reshape(nt, 3)
    for j in range(nt - padding):
        p.latents.append(sample[1][len(ids) + j].numpy().copy())
        p.encoder_embeddings.append(emb[j].numpy().copy())
        p.c2ws.append(tc[j].numpy().copy())
        p.Ks.append(tk[j].numpy().copy())
        p.pil_frames.append(None)
    if batch:
        batch.commit_cache(target_encoder_embeddings=emb)
    p.surfels = [SimpleNamespace(position=np.array([0., 0., 1.], np.float32),
                   normal=np.array([0., 0., -1.], np.float32), radius=np.float32(.1), color=None)]
    p.surfel_to_timestep = {0: list(range(len(p.pil_frames)))}
    p.surfel_Ks.extend(p.Ks)
    if batch:
        batch.commit_map()
    return sample


try:
    x = torch.arange(12, dtype=torch.float32).reshape(3, 4)
    check("noncontiguous canonical bits equal", tensor_identity(x.T) == tensor_identity(x.T.contiguous()))
    check("NumPy/Torch same dtype bits equal", tensor_identity(x) == tensor_identity(x.numpy()))
    check("dtype part of SHA", tensor_identity(x)["sha256"] != tensor_identity(x.double())["sha256"])
    check("shape part of SHA", tensor_identity(x)["sha256"] != tensor_identity(x.reshape(2, 6))["sha256"])
    check("content part of SHA", tensor_identity(x)["sha256"] != tensor_identity(x + 1)["sha256"])
    check("half bool int64 bfloat16 accepted", all(tensor_identity(x.to(d))["nbytes"] > 0 for d in
          (torch.float16, torch.bool, torch.int64, torch.bfloat16)))
    big_endian = x.numpy().astype(">f4")
    check("NumPy big-endian canonicalized", tensor_identity(big_endian) == tensor_identity(x))
    rejects("object array rejected", lambda: tensor_identity(np.array([{}], dtype=object)))
    rejects("recorded execution needs manifest", lambda: TraceWriter(OUT / "invalid_real", evidence_kind="recorded_execution", source_identities=SOURCES))
    seed()
    plain = pipeline()
    plain_out = execute(plain, [0], 3)
    plain_rng = torch.get_rng_state().clone()
    seed()
    p = pipeline()
    w = TraceWriter(OUT / "two_batches", evidence_kind="synthetic_test", source_identities=SOURCES)
    grad = torch.is_grad_enabled()
    with w.batch("batch0", p, context(p, [0]), torch.eye(4).repeat(7, 1, 1),
                 torch.eye(3).repeat(7, 1, 1), padding_size=3) as b:
        traced_out = execute(p, [0], 3, b)
    check("observer leaves returned samples exact", torch.equal(plain_out[0], traced_out[0]))
    check("observer leaves returned latents exact", torch.equal(plain_out[1], traced_out[1]))
    check("observer consumes no CPU RNG", torch.equal(torch.get_rng_state(), plain_rng))
    check("observer leaves grad mode unchanged", torch.is_grad_enabled() == grad)
    with w.batch("batch1", p, context(p, [0, 2, 2, 4]), torch.eye(4).repeat(4, 1, 1),
                 torch.eye(3).repeat(4, 1, 1), padding_size=0) as b:
        execute(p, [0, 2, 2, 4], 0, b)
    w.close()
    verified = verify_trace(OUT / "two_batches")
    check("two batches full lifecycle validates", verified["status"] == "VALID_CLOSED_TRACE" and len(verified["batches"]) == 2)
    rows = [json.loads(v) for v in (OUT / "two_batches/events.jsonl").read_text().splitlines()]
    begin = [r["payload"] for r in rows if r["event"] == "batch_begin"]
    commits = [r["payload"] for r in rows if r["event"] == "cache_commit"]
    check("duplicate ordered selected IDs preserved", begin[1]["selected_context_ids"] == [0, 2, 2, 4])
    check("history 1 to 5 to 9 exact", [len(v["history_before"]) for v in begin] == [1, 5] and [v["history_after_length"] for v in commits] == [5, 9])
    check("first padded slots no IDs", commits[0]["padding_slots_without_frame_id"] == [5, 6, 7])
    check("CLIP rows include padded inputs", [v["clip_target_rows_including_padding"] for v in commits] == [7, 4])
    check("second joint output all same parents", all(v["conditioning_parent_ids"] == [0, 2, 2, 4] for v in commits[1]["retained"]))
    noise_event = next(v for v in rows if v["event"] == "sampler_enter")
    seed()
    expected_noise = torch.randn(8, 1, 2, 2)
    check("actual initial noise bits saved", tensor_identity(expected_noise)["sha256"] == noise_event["payload"]["noise"]["sha256"])
    check("original-style extra map K history retained", [v["payload"]["map_after"]["surfel_Ks_length"] for v in rows if v["event"] == "map_commit"] == [5, 14])
    check("actual callback counters exact", all(v["denoiser_callbacks"] == 3 for v in verified["batches"].values()))
    rejects("fresh path cannot overwrite old trace", lambda: TraceWriter(OUT / "two_batches", evidence_kind="synthetic_test", source_identities=SOURCES))
    # A genuine exception from delegated code must leave a failure and be reraised.
    fp = pipeline()
    fw = TraceWriter(OUT / "failed_sampler", evidence_kind="synthetic_test", source_identities=SOURCES)
    def sampler_broken(*a, **k):
        raise RuntimeError("synthetic injected sampler failure")
    try:
        with fw.batch("failed0", fp, context(fp, [0]), torch.eye(4).repeat(7, 1, 1), torch.eye(3).repeat(7, 1, 1), padding_size=3) as b:
            mask = torch.tensor([True] + [False] * 7)
            b.sample(fake_do_sample, None, None, None, sampler_broken, {}, {}, torch.eye(4).repeat(8, 1, 1), torch.eye(3).repeat(8, 1, 1), mask)
    except RuntimeError as error:
        check("delegated failure preserved", "synthetic injected" in str(error))
    fw.close()
    check("failed lifecycle retained", verify_trace(OUT / "failed_sampler")["batches"]["failed0"]["state"] == "failure")
    wp = TraceWriter(OUT / "rejected_context", evidence_kind="synthetic_test", source_identities=SOURCES)
    wrong = context(fp, [0])
    wrong["context_latents"] += 1
    rejects("actual cache mismatch rejected", lambda: wp.batch("wrong", fp, wrong, torch.eye(4)[None], torch.eye(3)[None], padding_size=0))
    wp.close()
    check("rejected creation leaves observation", verify_trace(OUT / "rejected_context")["events"] == 3)
    # Preserve tampered copies in separate folders; never alter the valid traces.
    import shutil
    shutil.copytree(OUT / "two_batches", OUT / "tampered_event")
    path = OUT / "tampered_event/events.jsonl"
    path.write_bytes(path.read_bytes().replace(b'"joint_batch":true', b'"joint_batch":false', 1))
    rejects("event hash tampering detected", lambda: verify_trace(path.parent))
    shutil.copytree(OUT / "two_batches", OUT / "tampered_blob")
    bp = OUT / "tampered_blob" / noise_event["payload"]["noise"]["blob"]
    data = bytearray(bp.read_bytes())
    data[0] ^= 1
    bp.write_bytes(data)
    rejects("noise bytes tampering detected", lambda: verify_trace(bp.parent.parent))
    final = {"status": "PASS_SYNTHETIC_ONLY_NOT_CONNECTED_TO_GENERATOR", "started_utc": UTC,
             "completed_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "seconds": time.monotonic() - START,
             "checks": checks, "check_count": len(checks), "source_sha256": SOURCES,
             "torch": torch.__version__, "numpy": np.__version__, "independent_implementation": False,
             "real_models": 0, "real_images": 0, "real_npz": 0, "GT": 0,
             "two_batch_verification": verified, "synthetic_batches": 2, "synthetic_sampler_steps_per_batch": 3}
except BaseException as error:
    final = {"status": "FAIL_SYNTHETIC", "started_utc": UTC, "completed_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
             "seconds": time.monotonic() - START, "checks_passed": checks, "source_sha256": SOURCES,
             "error": repr(error)}
    (OUT / "receipt.json").write_text(json.dumps(final, indent=2) + "\n")
    raise
else:
    (OUT / "receipt.json").write_text(json.dumps(final, indent=2) + "\n")
    print(json.dumps({k: final[k] for k in ("status", "seconds", "check_count")}))
finally:
    signal.alarm(0)
