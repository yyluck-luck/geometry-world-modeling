"""S20 opt-in observation only; never imports VMem or runs a model.

The integration caller must supply live objects from the actual pipeline. A trace
is evidence of observed conditioning, not a causal intervention or model-quality
test. See docs/S20_GENERATION_TRACE_CONTRACT.md before integrating.
"""
from __future__ import annotations

import datetime as dt
import fcntl
import hashlib
import inspect
import json
import numbers
import os
from pathlib import Path
import random
import re
import sys
import threading
from typing import Any

import numpy as np

SCHEMA = "s20-generation-trace-v1"
HEX = re.compile(r"^[0-9a-f]{64}$")
EVENTS = {"session", "batch_begin", "sample_call", "sampler_enter", "denoiser_call",
          "sampler_return", "sample_return", "cache_commit", "map_commit",
          "batch_complete", "failure", "operation_failure", "observation", "session_end"}


def _json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _tensor_bytes(value: Any) -> tuple[dict, bytes]:
    """Canonical little-endian C-order bits; dtype/shape are part of identity."""
    if type(value).__module__.startswith("torch"):
        import torch
        _require(value.layout == torch.strided and not value.is_quantized,
                 "only dense nonquantized tensors are supported")
        v = value.detach().cpu().contiguous().resolve_conj().resolve_neg()
        _require(sys.byteorder == "little", "Torch canonicalization requires little-endian host")
        dtype = str(v.dtype).removeprefix("torch.")
        shape = list(v.shape)
        raw = v.reshape(-1).view(torch.uint8).numpy().tobytes()
    else:
        v = np.asarray(value)
        _require(v.dtype.kind in "biufc", "unsupported/object/string tensor dtype")
        dtype, shape = v.dtype.name, list(v.shape)
        raw = np.ascontiguousarray(v.astype(v.dtype.newbyteorder("<"), copy=False)).tobytes()
    desc = {"kind": "tensor", "dtype": dtype, "shape": shape,
            "byteorder": "little", "order": "C", "nbytes": len(raw),
            "bytes_sha256": _sha(raw)}
    desc["sha256"] = _sha(_json(desc) + b"\0" + raw)
    return desc, raw


def tensor_identity(value: Any) -> dict:
    return _tensor_bytes(value)[0]


def _mask_list(value: Any) -> list[bool]:
    if type(value).__module__.startswith("torch"):
        v = value.detach().cpu().numpy()
    else:
        v = np.asarray(value)
    _require(v.ndim == 1 and v.dtype == np.bool_, "input mask must be one-dimensional bool")
    return v.tolist()


def _cache_identity(pipeline: Any) -> list[dict]:
    n = len(pipeline.pil_frames)  # Count only; do not inspect/decode image objects.
    attrs = ("latents", "encoder_embeddings", "c2ws", "Ks")
    _require(all(len(getattr(pipeline, key)) == n for key in attrs), "cache lengths disagree")
    return [{"frame_id": i, **{key: tensor_identity(getattr(pipeline, key)[i])
                              for key in attrs}} for i in range(n)]


class TraceWriter:
    """Single active batch, fresh directory, fsync'ed append-only hash chain.

    The file lock prevents simultaneous writes. This class deliberately does not
    resume an old directory: a crashed prefix remains evidence, not overwritten.
    """
    def __init__(self, directory: str | Path, *, evidence_kind: str,
                 source_identities: dict[str, str], manifest_sha256: str | None = None,
                 rng_devices: tuple[str, ...] = ()):
        _require(evidence_kind in ("synthetic_test", "recorded_execution"), "invalid evidence_kind")
        _require(bool(source_identities) and all(isinstance(k, str) and HEX.fullmatch(v)
                 for k, v in source_identities.items()), "source identities require SHA256")
        _require(manifest_sha256 is None or bool(HEX.fullmatch(manifest_sha256)), "invalid manifest SHA")
        _require(evidence_kind != "recorded_execution" or manifest_sha256 is not None,
                 "recorded execution requires separately frozen manifest identity")
        _require(all(x == "cuda" or x == "mps" for x in rng_devices), "unsupported RNG device")
        self.root = Path(directory)
        self.root.mkdir(parents=True, exist_ok=False)
        (self.root / "blobs").mkdir()
        self.path = self.root / "events.jsonl"
        self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_APPEND, 0o600)
        self.lock = threading.RLock()
        self.seq, self.previous, self.active, self.closed = 0, "0" * 64, None, False
        self.batch_ids: set[str] = set()
        self.evidence_kind, self.rng_devices = evidence_kind, rng_devices
        self.emit("session", {
            "source_identities": source_identities, "manifest_sha256": manifest_sha256,
            "rng_devices": list(rng_devices), "pid": os.getpid(),
            "python": sys.version, "numpy": np.__version__,
            "claim": "observed conditioning dependencies only; no causal or quality proof",
            "initial_noise_is_not_all_randomness": True,
            "rng_scope": "Python global, NumPy legacy global, Torch CPU and explicit device states; custom Generators excluded",
        })

    def tree(self, value: Any, *, save: bool = False) -> Any:
        if type(value).__module__ == "torch" and type(value).__name__ in ("device", "dtype"):
            return str(value)
        if isinstance(value, np.ndarray) or type(value).__module__.startswith("torch"):
            desc, raw = _tensor_bytes(value)
            if save:
                rel = "blobs/" + desc["sha256"] + ".bin"
                path = self.root / rel
                try:
                    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                except FileExistsError:
                    _require(path.read_bytes() == raw, "existing blob differs")
                else:
                    with os.fdopen(fd, "wb") as handle:
                        handle.write(raw)
                        handle.flush()
                        os.fsync(handle.fileno())
                desc["blob"] = rel
            return desc
        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, dict):
            _require(all(isinstance(k, str) for k in value), "dictionary keys must be strings")
            return {k: self.tree(v, save=save) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [self.tree(v, save=save) for v in value]
        _require(value is None or isinstance(value, (str, bool, int, float)), "unsupported tree object")
        _json(value)
        return value

    def rng(self) -> dict:
        import torch
        result = {"python": self.tree(random.getstate()),
                  "numpy_legacy": self.tree(np.random.get_state(), save=True),
                  "torch_cpu": self.tree(torch.get_rng_state(), save=True),
                  "torch_version": torch.__version__, "devices": {}}
        for device in self.rng_devices:
            if device == "cuda":
                # Never initialize CUDA merely to log RNG state.
                result["devices"][device] = (self.tree(torch.cuda.get_rng_state_all(), save=True)
                    if torch.cuda.is_initialized() else {"status": "not_initialized_not_captured"})
            else:
                _require(torch.backends.mps.is_available(), "requested MPS RNG unavailable")
                result["devices"][device] = self.tree(torch.mps.get_rng_state(), save=True)
        return result

    def map_snapshot(self, pipeline: Any) -> dict:
        surfels, sources = pipeline.surfels, pipeline.surfel_to_timestep
        _require(set(sources) == set(range(len(surfels))), "map source keys differ from surfel indices")
        entries = [{"position": self.tree(s.position, save=True),
                    "normal": self.tree(s.normal, save=True),
                    "radius": self.tree(np.asarray(s.radius), save=True),
                    "color": self.tree(s.color, save=True),
                    "source_ids": [int(i) for i in sources[j]]}
                   for j, s in enumerate(surfels)]
        _require(all(0 <= k < len(pipeline.pil_frames) for e in entries for k in e["source_ids"]),
                 "map contains nonexistent frame ID")
        # S20 full-content encoding, deliberately not the older S18 hash format.
        return {"encoding": "s20-full-surfel-list-v1", "count": len(entries), "entries": entries,
                "version_sha256": _sha(_json(entries)),
                "surfel_Ks_length": len(pipeline.surfel_Ks) if hasattr(pipeline, "surfel_Ks") else None}

    def emit(self, event: str, payload: dict, *, batch_id: str | None = None) -> dict:
        _require(event in EVENTS and isinstance(payload, dict), "invalid event schema")
        _require(not self.closed, "writer already closed")
        with self.lock:
            fcntl.flock(self.fd, fcntl.LOCK_EX)
            try:
                record = {"schema": SCHEMA, "seq": self.seq, "previous_sha256": self.previous,
                          "utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                          "evidence_kind": self.evidence_kind, "event": event,
                          "batch_id": batch_id, "payload": payload}
                record["sha256"] = _sha(_json(record))
                data = _json(record) + b"\n"
                while data:
                    size = os.write(self.fd, data)
                    _require(size > 0, "append write failed")
                    data = data[size:]
                os.fsync(self.fd)
                self.seq += 1
                self.previous = record["sha256"]
                return record
            finally:
                fcntl.flock(self.fd, fcntl.LOCK_UN)

    def observe(self, name: str, *, values: Any, batch_id: str | None = None) -> None:
        self.emit("observation", {"name": name, "values": self.tree(values)}, batch_id=batch_id)

    def failed_operation(self, phase: str, error: BaseException) -> None:
        """For initialize/context-selection failures before a batch can be opened."""
        _require(self.active is None, "active batch context manager records its own failure")
        self.emit("operation_failure", {"phase": phase, "exception_type": type(error).__name__,
                                         "message": str(error), "rng": self.rng()})

    def batch(self, batch_id: str, pipeline: Any, context_info: dict,
              target_c2ws: Any, target_Ks: Any, *, padding_size: int) -> "GenerationBatch":
        try:
            return GenerationBatch(self, batch_id, pipeline, context_info, target_c2ws,
                                   target_Ks, padding_size=padding_size)
        except Exception as error:
            self.observe("batch_creation_rejected", values={"requested_id": batch_id,
                "exception_type": type(error).__name__, "message": str(error)})
            raise

    def close(self) -> None:
        _require(self.active is None, "active batch must finish/fail before closing")
        self.emit("session_end", {"batches": len(self.batch_ids)})
        os.close(self.fd)
        self.closed = True


class GenerationBatch:
    def __init__(self, writer: TraceWriter, batch_id: str, pipeline: Any,
                 context_info: dict, target_c2ws: Any, target_Ks: Any, *, padding_size: int):
        _require(writer.active is None and isinstance(batch_id, str) and bool(batch_id)
                 and batch_id not in writer.batch_ids, "batch IDs must be unique and sequential")
        self.w, self.id, self.pipeline = writer, batch_id, pipeline
        self.phase, self.sampler_calls, self.denoiser_calls = "begin", 0, 0
        self.before = _cache_identity(pipeline)
        raw_ids = context_info["context_time_indices"]
        _require(all(isinstance(i, numbers.Integral) and not isinstance(i, (bool, np.bool_)) for i in raw_ids),
                 "context IDs must be integer indices, not coercible floats/bools")
        self.ids = [int(i) for i in raw_ids]
        _require(self.ids and all(0 <= i < len(self.before) for i in self.ids), "invalid selected context IDs")
        self.ntarget = len(target_c2ws)
        _require(len(target_Ks) == self.ntarget and isinstance(padding_size, int)
                 and 0 <= padding_size < self.ntarget, "invalid targets/padding")
        self.nkeep = self.ntarget - padding_size
        self.mask = [True] * len(self.ids) + [False] * self.ntarget
        self.target_cameras = [tensor_identity(v) for v in target_c2ws]
        self.target_Ks = [tensor_identity(v) for v in target_Ks]
        import torch
        # Verify supplied cast tensors against the actual selected cached entries.
        for cache, info in (("latents", "context_latents"), ("encoder_embeddings", "context_encoder_embeddings"),
                            ("c2ws", "context_c2ws"), ("Ks", "context_Ks")):
            v = context_info[info]
            _require(len(v) == len(self.ids), "context tensor/ID length mismatch")
            for j, i in enumerate(self.ids):
                expected = torch.as_tensor(getattr(pipeline, cache)[i]).to(device=v.device, dtype=v.dtype)
                _require(tensor_identity(v[j]) == tensor_identity(expected), "selected context does not match live cache")
        self.slots = ([{"slot": j, "role": "context", "frame_id": i} for j, i in enumerate(self.ids)] +
                      [{"slot": len(self.ids) + j, "role": "target_padding" if j >= self.nkeep else "target_retained",
                        "frame_id": None} for j in range(self.ntarget)])
        self._emit("batch_begin", {"selected_context_ids": self.ids, "history_before": self.before,
            "context_tensors": writer.tree({k: context_info[k] for k in
                ("context_latents", "context_encoder_embeddings", "context_c2ws", "context_Ks")}),
            "target_cameras": self.target_cameras, "target_Ks": self.target_Ks,
            "slots": self.slots, "padding_size": padding_size, "retained_count": self.nkeep,
            "input_mask": self.mask, "map_before": writer.map_snapshot(pipeline),
            "joint_batch": True, "dependency_interpretation": "all outputs share ordered context parents; no within-batch ancestry"})
        writer.active = self
        writer.batch_ids.add(batch_id)

    def _emit(self, event: str, payload: dict) -> None:
        self.w.emit(event, payload, batch_id=self.id)

    def __enter__(self) -> "GenerationBatch":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc is not None or self.phase != "map_committed":
            error = exc if exc is not None else RuntimeError("batch exited without map commit")
            self._emit("failure", {"phase": self.phase, "exception_type": type(error).__name__,
                                   "message": str(error), "sampler_calls": self.sampler_calls,
                                   "denoiser_calls": self.denoiser_calls, "rng": self.w.rng()})
            self.w.active = None
            if exc is None:
                raise error
        else:
            self._emit("batch_complete", {"joint_batch": True, "retained_frame_ids": self.retained_ids})
            self.w.active = None
        return False

    def sample(self, do_sample, *args, **kwargs):
        """Delegate original function; replace only its sampler callable argument."""
        _require(self.phase == "begin", "sample must be called exactly once")
        bound = inspect.signature(do_sample).bind(*args, **kwargs)
        bound.apply_defaults()
        a = bound.arguments
        _require(_mask_list(a["cond_frames_mask"]) == self.mask, "actual do_sample mask differs from slots")
        _require(a["return_latents"] is True and a["T"] == len(self.mask), "sample contract requires all-slot latent return")
        self._emit("sample_call", {"inputs": self.w.tree({k: a[k] for k in
            ("c", "uc", "c2w", "K", "cond_frames_mask", "H", "W", "C", "F", "T", "cfg", "device")}),
            "rng": self.w.rng()})
        self.phase = "sampling"
        sampler = a["sampler"]

        def observed_sampler(denoiser, noise, *sa, **sk):
            self.sampler_calls += 1
            _require(self.sampler_calls == 1 and not sa, "unexpected sampler invocation layout")
            _require(_mask_list(sk["input_frame_mask"]) == self.mask, "actual sampler mask mismatch")
            self._emit("sampler_enter", {"noise": self.w.tree(noise, save=True),
                "inputs": self.w.tree({k: sk[k] for k in ("scale", "cond", "uc", "c2w", "K", "input_frame_mask")}),
                "rng": self.w.rng(), "initial_noise_only": True})

            def observed_denoiser(*da, **dk):
                self.denoiser_calls += 1
                # Preserve the original callable and invocation exactly. Callback
                # count is not asserted equal to sampler/model-forward steps.
                self._emit("denoiser_call", {"callback_index": self.denoiser_calls - 1,
                    "positional_inputs": self.w.tree(list(da)), "keyword_inputs": self.w.tree(dk)})
                return denoiser(*da, **dk)

            result = sampler(observed_denoiser, noise, **sk)
            self._emit("sampler_return", {"output": self.w.tree(result), "rng": self.w.rng(),
                                          "denoiser_calls": self.denoiser_calls})
            return result

        a["sampler"] = observed_sampler
        result = do_sample(*bound.args, **bound.kwargs)
        _require(self.sampler_calls == 1 and isinstance(result, tuple) and len(result) == 2,
                 "do_sample did not return (samples, latents)")
        _require(all(len(v) == len(self.mask) for v in result), "output slot count mismatch")
        self.samples_z = result[1]
        self._emit("sample_return", {"samples": self.w.tree(result[0]), "samples_z": self.w.tree(result[1]),
                                     "rng": self.w.rng(), "all_output_slots": len(self.mask)})
        self.phase = "sample_returned"
        return result

    def commit_cache(self, *, target_encoder_embeddings: Any) -> None:
        """Call AFTER original append loop, with actual CLIP target-batch output."""
        _require(self.phase == "sample_returned", "cache commit order invalid")
        after = _cache_identity(self.pipeline)
        _require(len(after) == len(self.before) + self.nkeep and after[:len(self.before)] == self.before,
                 "actual cache length or old entries changed")
        _require(len(target_encoder_embeddings) == self.ntarget, "CLIP rows must include padded targets")
        offset = len(self.ids)
        rows = []
        for j in range(self.nkeep):
            frame = after[len(self.before) + j]
            _require(frame["latents"] == tensor_identity(self.samples_z[offset + j]), "appended latent mismatch")
            _require(frame["encoder_embeddings"] == tensor_identity(target_encoder_embeddings[j]), "appended embedding mismatch")
            _require(frame["c2ws"] == self.target_cameras[j] and frame["Ks"] == self.target_Ks[j], "appended camera mismatch")
            rows.append({"slot": offset + j, "frame_id": frame["frame_id"], "conditioning_parent_ids": self.ids,
                         "joint_batch_id": self.id, "cache": frame})
        self.retained_ids = [r["frame_id"] for r in rows]
        self._emit("cache_commit", {"history_after_length": len(after), "retained": rows,
            "padding_slots_without_frame_id": list(range(offset + self.nkeep, len(self.mask))),
            "clip_target_rows_including_padding": self.ntarget,
            "target_encoder_embeddings": self.w.tree(target_encoder_embeddings)})
        del self.samples_z
        self.phase = "cache_committed"

    def commit_map(self) -> None:
        """Call AFTER original construct_and_store_scene returns successfully."""
        _require(self.phase == "cache_committed", "map commit order invalid")
        self._emit("map_commit", {"map_after": self.w.map_snapshot(self.pipeline),
                                  "history_length": len(self.pipeline.pil_frames)})
        self.phase = "map_committed"


def verify_trace(directory: str | Path) -> dict:
    """Offline chain/blob/ordering validation; not proof the callback ran VMem."""
    root = Path(directory)
    records, previous, batches, closed, mode = [], "0" * 64, {}, False, None
    transitions = {"sample_call": ("batch_begin", "sample_call"),
                   "sampler_enter": ("sample_call", "sampler_enter"),
                   "sampler_return": ("sampler_enter", "sampler_return"),
                   "sample_return": ("sampler_return", "sample_return"),
                   "cache_commit": ("sample_return", "cache_commit"),
                   "map_commit": ("cache_commit", "map_commit"),
                   "batch_complete": ("map_commit", "batch_complete")}
    blob_count = 0

    def check_tree(value):
        nonlocal blob_count
        if isinstance(value, dict):
            if value.get("encoding") == "s20-full-surfel-list-v1":
                _require(value["count"] == len(value["entries"]) and
                         _sha(_json(value["entries"])) == value["version_sha256"], "map version mismatch")
            if value.get("kind") == "tensor":
                _require(set(value) in ({"kind", "dtype", "shape", "byteorder", "order", "nbytes", "bytes_sha256", "sha256"},
                    {"kind", "dtype", "shape", "byteorder", "order", "nbytes", "bytes_sha256", "sha256", "blob"}), "tensor schema invalid")
                _require(value["byteorder"] == "little" and value["order"] == "C" and
                         all(isinstance(i, int) and i >= 0 for i in value["shape"]) and
                         HEX.fullmatch(value["sha256"]) and HEX.fullmatch(value["bytes_sha256"]), "tensor identity invalid")
                if "blob" in value:
                    _require(value["blob"] == "blobs/" + value["sha256"] + ".bin", "unsafe blob path")
                    raw = (root / value["blob"]).read_bytes()
                    base = {k: v for k, v in value.items() if k not in ("sha256", "blob")}
                    _require(len(raw) == value["nbytes"] and _sha(raw) == value["bytes_sha256"] and
                             _sha(_json(base) + b"\0" + raw) == value["sha256"], "blob identity mismatch")
                    blob_count += 1
            else:
                for x in value.values():
                    check_tree(x)
        elif isinstance(value, list):
            for x in value:
                check_tree(x)

    with (root / "events.jsonl").open("rb") as stream:
        for i, line in enumerate(stream):
            _require(line.endswith(b"\n") and not closed, "truncated line or append after session end")
            r = json.loads(line)
            _require(set(r) == {"schema", "seq", "previous_sha256", "utc", "evidence_kind", "event", "batch_id", "payload", "sha256"}, "event field schema invalid")
            _require(r["schema"] == SCHEMA and r["seq"] == i and r["previous_sha256"] == previous and
                     r["event"] in EVENTS and isinstance(r["payload"], dict), "event schema/sequence mismatch")
            claimed = r["sha256"]
            _require(_sha(_json({k: v for k, v in r.items() if k != "sha256"})) == claimed, "event hash mismatch")
            previous = claimed
            event, bid, p = r["event"], r["batch_id"], r["payload"]
            if i == 0:
                _require(event == "session" and bid is None, "missing session header")
                mode = r["evidence_kind"]
                _require(mode in ("synthetic_test", "recorded_execution"), "bad evidence kind")
                _require(mode != "recorded_execution" or HEX.fullmatch(p["manifest_sha256"]), "missing execution manifest")
            else:
                _require(event != "session" and r["evidence_kind"] == mode, "session/evidence kind changed")
            if event == "batch_begin":
                _require(bid not in batches and isinstance(bid, str) and bool(bid), "duplicate batch")
                _require(not any(v["state"] not in ("batch_complete", "failure") for v in batches.values()), "overlapping batches")
                ids, slots = p["selected_context_ids"], p["slots"]
                n = len(p["history_before"])
                _require(ids and all(isinstance(v, int) and 0 <= v < n for v in ids), "bad context IDs")
                _require(p["joint_batch"] is True and p["input_mask"] == [True] * len(ids) + [False] * (len(slots) - len(ids)), "bad joint/mask schema")
                _require([s["slot"] for s in slots] == list(range(len(slots))) and
                         [s["frame_id"] for s in slots[:len(ids)]] == ids and
                         all(s["frame_id"] is None for s in slots[len(ids):]), "bad output slot IDs")
                _require(p["retained_count"] + p["padding_size"] == len(slots) - len(ids), "padding count mismatch")
                batches[bid] = {"state": event, "begin": p, "callbacks": 0}
            elif event == "denoiser_call":
                _require(bid in batches and batches[bid]["state"] == "sampler_enter", "denoiser outside sampler")
                _require(p["callback_index"] == batches[bid]["callbacks"], "callback index gap")
                batches[bid]["callbacks"] += 1
            elif event in transitions:
                old, new = transitions[event]
                _require(bid in batches and batches[bid]["state"] == old, "invalid batch transition")
                b = batches[bid]
                if event == "sampler_return":
                    _require(p["denoiser_calls"] == b["callbacks"], "callback count mismatch")
                if event == "cache_commit":
                    begin, rows = b["begin"], p["retained"]
                    start, offset = len(begin["history_before"]), len(begin["selected_context_ids"])
                    _require(len(rows) == begin["retained_count"] and p["history_after_length"] == start + len(rows), "retained count mismatch")
                    _require([v["frame_id"] for v in rows] == list(range(start, start + len(rows))) and
                             [v["slot"] for v in rows] == list(range(offset, offset + len(rows))) and
                             all(v["joint_batch_id"] == bid and v["conditioning_parent_ids"] == begin["selected_context_ids"] for v in rows), "false serial ancestry or retained IDs")
                    b["retained_ids"] = [v["frame_id"] for v in rows]
                if event == "batch_complete":
                    _require(p["joint_batch"] is True and p["retained_frame_ids"] == b["retained_ids"], "completion mismatch")
                b["state"] = new
            elif event == "failure":
                _require(bid in batches and batches[bid]["state"] not in ("failure", "batch_complete"), "failure without active batch")
                batches[bid]["state"] = "failure"
            elif event == "session_end":
                _require(bid is None and p["batches"] == len(batches) and
                         all(v["state"] in ("failure", "batch_complete") for v in batches.values()), "unfinished session")
                closed = True
            elif event == "observation":
                _require(bid is None or bid in batches, "unknown observation batch")
            elif event == "operation_failure":
                _require(bid is None and isinstance(p["phase"], str) and "exception_type" in p
                         and not any(v["state"] not in ("failure", "batch_complete") for v in batches.values()),
                         "operation failure overlaps active batch")
            check_tree(p)
            records.append(r)
    _require(bool(records), "empty trace")
    return {"status": "VALID_CLOSED_TRACE" if closed else "VALID_INCOMPLETE_PREFIX",
            "evidence_kind": mode, "events": len(records), "last_sha256": previous,
            "blob_references_checked": blob_count,
            "batches": {k: {"state": v["state"], "denoiser_callbacks": v["callbacks"]} for k, v in batches.items()},
            "causal_or_quality_verification": False}
