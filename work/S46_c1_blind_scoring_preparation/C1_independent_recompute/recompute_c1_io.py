#!/usr/bin/env python3
"""Identity-only C1 recomputation I/O; mathematics stays in the sealed kernel."""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys

HERE = Path(__file__).resolve().parent
PREPARATION = HERE.parent
ROOT = PREPARATION.parents[1]
SELF = Path(__file__).resolve()
KERNEL = PREPARATION / "recompute_c1_independent_candidate.py"
KERNEL_SHA = "9373fd035b18ccc81dc848e18612f906a7d32a44cd1c7d2903eb67b7627e9b8f"
TEMPLATE = PREPARATION / "C1_INDEPENDENT_RECOMPUTE_BINDING_TEMPLATE.json"
TEMPLATE_SHA = "dda75a1d6cf590972ea2b33d547e9a94efb6b68dacfa85917f86f8ece20fd0aa"
CONTRACT_TEMPLATE = PREPARATION / "C1_SCORING_CONTRACT_TEMPLATE.json"
CONTRACT_TEMPLATE_SHA = "79299749250c22dd9719d93964b9c179a8884f01c530bf07a45625c59395ab7b"
PRIMARY_KERNEL_SHA = "ada2ba80eceebe83a514fd929c6cc82b69669e6525e261ff4729064f2bac3f1a"
PRIMARY_DIR = PREPARATION / "C1_score_attempt_01"
PRIMARY_BINDING = ROOT / "work/S46_c1_blind_scoring_wrapper_v3/WRAPPER_EXECUTION_BINDING.json"
TENSOR_DIR = ROOT / "results/S44_C1_confirmation_generation/archive/tensors"
OUTPUT = HERE / "execution_01"
STAGE = HERE / ".execution_01.staging"
LOCK = HERE / ".independent_recompute.lock"
AUTHOR = "/root/execution_resumption_audit"
KERNEL_AUTHOR = "/root/c1_blind_score_builder"
HEX = re.compile(r"^[0-9a-f]{64}$")
SHAPE = (576, 576, 3)
NBYTES = 995328


def require(ok, message):
    if not ok:
        raise ValueError(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def timestamp(raw):
    require(type(raw) is str, "UTC timestamp is missing")
    value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    require(value.tzinfo is not None and value.utcoffset() == timezone.utc.utcoffset(value), "UTC timestamp differs")
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def identity(value):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_nlink, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


class Snapshot:
    """Retain one read-only FD, consume/hash its bytes, then verify before close."""
    def __init__(self, path, expected_sha, size=None):
        self.path = Path(path)
        require(self.path.is_absolute() and self.path.resolve() == self.path and not self.path.is_symlink(), "Noncanonical input path")
        require(HEX.fullmatch(expected_sha or "") is not None, "Missing exact input SHA")
        flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
        self.fd = os.open(self.path, flags)
        self.bytes_read = 0
        try:
            self.before = identity(os.fstat(self.fd))
            require(stat.S_ISREG(self.before[2]) and self.before[3] == 1, "Input is not a single-link regular file")
            require(self.before == identity(os.stat(self.path, follow_symlinks=False)), "Opened input/path identity differs")
            require(0 < self.before[4] <= 16 * 1024 * 1024, "Input size exceeds bounded scope")
            require(size is None or self.before[4] == size, "Input exact byte size differs")
            self.raw = self.read()
            self.sha = hashlib.sha256(self.raw).hexdigest()
            require(self.sha == expected_sha, "Input SHA differs: " + str(self.path))
            self.verify()
        except BaseException:
            os.close(self.fd)
            raise

    def read(self):
        pieces = []
        offset = 0
        while offset < self.before[4]:
            block = os.pread(self.fd, min(1024 * 1024, self.before[4] - offset), offset)
            require(bool(block), "Unexpected input EOF")
            pieces.append(block)
            self.bytes_read += len(block)
            offset += len(block)
        require(os.pread(self.fd, 1, offset) == b"", "Input grew beyond bound")
        return b"".join(pieces)

    def verify(self):
        require(identity(os.fstat(self.fd)) == self.before and identity(os.stat(self.path, follow_symlinks=False)) == self.before, "Retained input identity changed")
        require(hashlib.sha256(self.read()).hexdigest() == self.sha, "Retained input bytes changed")
        require(identity(os.fstat(self.fd)) == self.before, "Input changed during closing rehash")

    def close(self):
        if self.fd >= 0:
            descriptor, self.fd = self.fd, -1
            os.close(descriptor)


def metadata(handles, path, sha):
    item = Snapshot(path, sha)
    handles.append(item)
    value = json.loads(item.raw)
    require(type(value) is dict, "Metadata must be an object")
    return value


def load_independent_kernel(handles):
    item = Snapshot(KERNEL, KERNEL_SHA)
    handles.append(item)
    namespace = {"__name__": "s46_independent_kernel", "__file__": str(KERNEL)}
    exec(compile(item.raw, str(KERNEL), "exec"), namespace)
    require(callable(namespace.get("recompute_frames")), "Independent kernel interface missing")
    return namespace


def check_binding_and_review(args, handles):
    source = Snapshot(SELF, args.source_sha256)
    handles.append(source)
    template = metadata(handles, TEMPLATE, TEMPLATE_SHA)
    binding = metadata(handles, args.binding, args.binding_sha256)
    expected = dict(template)
    override = ("sealed_score_attempt", "sealed_score_receipt_path", "sealed_score_receipt_sha256", "sealed_score_report_path", "sealed_score_report_sha256", "recompute_source_path", "recompute_source_sha256", "authorized_output_path")
    expected.update({key: binding.get(key) for key in override})
    expected.update(schema="s46-c1-independent-recompute-bound-binding-v1", status="BOUND_C1_RECOMPUTE_CANDIDATE_AWAITING_DIFFERENT_AUTHOR_SOURCE_REVIEW", template_path=str(TEMPLATE), template_sha256=TEMPLATE_SHA, identity_binding_path=binding.get("identity_binding_path"), identity_binding_sha256=binding.get("identity_binding_sha256"), binding_completed_utc=binding.get("binding_completed_utc"))
    require(binding == expected, "Binding differs from original identity-only renderer shape")
    require(binding["recompute_source_path"] == str(SELF) and binding["recompute_source_sha256"] == args.source_sha256, "Binding must name this exact I/O source")
    require(binding["recompute_source_review_path"] is None and binding["recompute_source_review_sha256"] is None, "Keep original candidate review slots null; actual review is caller-bound")
    require(type(binding["sealed_score_attempt"]) is int and binding["sealed_score_attempt"] == 1 and binding["authorized_output_path"] == str(OUTPUT), "Fixed recompute attempt differs")
    require(binding["sealed_score_receipt_path"] == str(PRIMARY_DIR / "receipt.json") and binding["sealed_score_report_path"] == str(PRIMARY_DIR / "report.json"), "Primary attempt paths differ")
    identity_binding = metadata(handles, binding["identity_binding_path"], binding["identity_binding_sha256"])
    require(identity_binding.get("schema") == "s46-c1-recompute-identity-binding-v1" and identity_binding.get("status") == "READY_TO_BIND_AFTER_SEALED_C1_PRIMARY_SCORE" and identity_binding.get("row") == "C1", "Identity-only input header differs")
    require(all(identity_binding.get(key) == binding[key] for key in override) and identity_binding.get("completed_utc") == binding["binding_completed_utc"], "Rendered input identities differ")
    review = metadata(handles, args.source_review, args.source_review_sha256)
    require(review.get("schema") == template["required_review_schema"] and review.get("status") == template["required_review_status"], "Actual different-author source review PASS missing")
    for key, value in {"row": "C1", "source_path": str(SELF), "source_sha256": args.source_sha256, "kernel_path": str(KERNEL), "kernel_sha256": KERNEL_SHA, "bound_binding_path": str(Path(args.binding)), "bound_binding_sha256": args.binding_sha256, "source_author_role": AUTHOR, "kernel_author_role": KERNEL_AUTHOR}.items():
        require(review.get(key) == value, "Review exact identity differs: " + key)
    require(type(review.get("reviewer_role")) is str and bool(review["reviewer_role"]) and review["reviewer_role"] not in (AUTHOR, KERNEL_AUTHOR), "Review author is not independent")
    require(all(review.get(key) is False for key in ("executed", "images_viewed", "tensor_or_image_payload_bodies_read")) and review.get("blocking_findings") == [], "Source review scope or blockers differ")
    require(timestamp(binding["binding_completed_utc"]) <= timestamp(review.get("completed_utc")) <= datetime.now(timezone.utc), "Review must follow binding and precede execution")
    return binding, review


def load_primary_chain(binding, handles):
    receipt = metadata(handles, binding["sealed_score_receipt_path"], binding["sealed_score_receipt_sha256"])
    report = metadata(handles, binding["sealed_score_report_path"], binding["sealed_score_report_sha256"])
    require(receipt.get("schema") == "s46-c1-blind-score-receipt-v1" and receipt.get("status") == "PASS_C1_BLIND_SCORE_TERMINAL" and receipt.get("technically_valid") is True and type(receipt.get("attempt")) is int and receipt["attempt"] == 1, "Primary receipt is not technically valid attempt 1")
    require(receipt.get("out") == str(PRIMARY_DIR) and receipt.get("report_sha256") == binding["sealed_score_report_sha256"], "Primary receipt/report binding differs")
    require(report.get("schema") == "s46-c1-blind-score-report-v1" and report.get("status") == "PASS_C1_BLIND_SCORE_TECHNICALLY_VALID" and report.get("row") == "C1" and report.get("frozen_scorer_sha256") == PRIMARY_KERNEL_SHA, "Primary report identity differs")
    require(report.get("c1_pixel_bodies_read") == 9 and report.get("images_rendered_or_viewed") == 0, "Primary report I/O scope differs")
    require(receipt.get("binding_path") == report.get("binding_path") == str(PRIMARY_BINDING) and receipt.get("binding_sha256") == report.get("binding_sha256"), "Primary report/receipt execution binding differs")
    require(timestamp(receipt.get("completed_utc")) <= timestamp(binding["binding_completed_utc"]), "Recompute binding predates sealed primary receipt")
    execution = metadata(handles, report["binding_path"], report["binding_sha256"])
    require(execution.get("schema") == "s46-c1-blind-scoring-wrapper-execution-binding-v1" and execution.get("status") == "BOUND_C1_BLIND_SCORING_WRAPPER_EXECUTION_AWAITING_EXACT_GATE_VALIDATION" and execution.get("row") == "C1" and execution.get("authorized_output_path") == str(PRIMARY_DIR), "Primary execution binding header differs")
    contract_record = execution.get("bound_contract")
    require(type(contract_record) is dict and set(contract_record) == {"path", "sha256"}, "Bound contract record differs")
    contract = metadata(handles, contract_record["path"], contract_record["sha256"])
    require(contract.get("schema") == "s46-c1-blind-scoring-bound-contract-v1" and contract.get("status") == "BOUND_C1_IDENTITY_CANDIDATE_AWAITING_DUAL_SOURCE_REVIEW_AND_BLINDNESS_ATTESTATION" and contract.get("row") == "C1", "Primary contract header differs")
    require(contract.get("template_path") == str(CONTRACT_TEMPLATE) and contract.get("template_sha256") == CONTRACT_TEMPLATE_SHA, "Primary contract template identity differs")
    original = metadata(handles, CONTRACT_TEMPLATE, CONTRACT_TEMPLATE_SHA)
    require(contract.get("frozen_math") == original["frozen_math"] and contract.get("frozen_math_sha256") == original["frozen_math_sha256"], "Primary frozen mathematics differs")
    slots = contract.get("binding_slots")
    require(type(slots) is dict and type(slots.get("authorized_attempt")) is int and slots["authorized_attempt"] == 1 and slots.get("authorized_output_path") == str(PRIMARY_DIR) and slots.get("archive_tensor_directory") == str(TENSOR_DIR), "Primary contract pixel domain differs")
    identities = slots.get("authoritative_pixel_identities")
    require(type(identities) is list and len(identities) == 9, "Exactly nine contract-bound identities required")
    for frame_id, item in enumerate(identities):
        require(type(item) is dict and set(item) == {"id", "tensor_descriptor_sha256", "tensor_body_sha256", "blob"}, "Pixel identity keys differ")
        require(type(item["id"]) is int and item["id"] == frame_id, "Pixel identity order differs")
        require(all(HEX.fullmatch(item[key] or "") is not None for key in ("tensor_descriptor_sha256", "tensor_body_sha256")), "Pixel identity SHA missing")
        require(item["blob"] == str(TENSOR_DIR / (item["tensor_descriptor_sha256"] + ".bin")), "Pixel identity path differs")
    expected_math = report.get("math_result")
    require(type(expected_math) is dict and expected_math.get("schema") == "s46-c1-blind-score-math-candidate-v1" and expected_math.get("row") == "C1" and expected_math.get("primary_pair") == [0, 8], "Primary math report header differs")
    return expected_math, identities


def compare_math(actual, expected):
    mismatches = []
    pairs = [("primary", actual["primary"], expected.get("primary")), ("full_frame_diagnostic", actual["full_frame_diagnostic"], expected.get("full_frame_diagnostic"))]
    for field, keys in (("per_region_diagnostic", ("R1", "R2", "R3", "R4")), ("generated_only_pair_diagnostic_no_GT", ("1_7", "2_6", "3_5"))):
        records = expected.get(field)
        if type(records) is not dict or set(records) != set(keys):
            mismatches.append({"field": field, "reason": "Diagnostic names differ"})
            records = {}
        pairs.extend((field + "/" + key, actual[field][key], records.get(key)) for key in keys)
    for field, measured, sealed in pairs:
        equal = type(sealed) is dict and set(sealed) == set(measured)
        if equal:
            mse = sealed["mse_float64"]
            psnr = sealed["psnr_db_float64"]
            equal = (type(mse) in (float, int) and math.isfinite(mse) and float(mse).hex() == sealed["mse_float64_hex"] == measured["mse_float64_hex"])
            equal = equal and (psnr is None and measured["psnr_db_float64"] is None or type(psnr) in (float, int) and measured["psnr_db_float64"] is not None and math.isfinite(psnr) and float(psnr).hex() == measured["psnr_db_float64"].hex())
            equal = equal and sealed["psnr_db_display_when_zero"] == measured["psnr_db_display_when_zero"]
            equal = equal and all(type(sealed[key]) is int and sealed[key] == measured[key] for key in ("pixels", "rgb_scalars"))
        if not equal:
            mismatches.append({"field": field, "reason": "Exact numeric record differs", "recomputed": measured, "sealed": sealed})
    for field in ("event_MSE_gt_0_01", "equality_is_not_event", "row_status"):
        if type(expected.get(field)) is not type(actual[field]) or expected.get(field) != actual[field]:
            mismatches.append({"field": field, "reason": "Event/status differs", "recomputed": actual[field], "sealed": expected.get(field)})
    return mismatches


def write_new(path, value):
    raw = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode() + b"\n"
    with path.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    return hashlib.sha256(raw).hexdigest()


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def publish():
    require(not os.path.lexists(OUTPUT), "Recompute destination already exists")
    libc = ctypes.CDLL(None, use_errno=True)
    rename = libc.renamex_np
    rename.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
    rename.restype = ctypes.c_int
    if rename(os.fsencode(STAGE), os.fsencode(OUTPUT), 4) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(OUTPUT))
    sync_dir(HERE)


def run(args):
    handles = []
    body_handles = []
    receipt = {"schema": "s46-c1-independent-recompute-receipt-v1", "row": "C1", "started_utc": utc(), "source_sha256": args.source_sha256, "kernel_sha256": KERNEL_SHA, "binding_path": str(args.binding), "binding_sha256": args.binding_sha256, "source_review_path": str(args.source_review), "source_review_sha256": args.source_review_sha256, "audit_completed": False, "exact_match": False, "body_count": 0, "body_snapshot_bytes": 0, "body_bytes_read": 0, "images_viewed_or_emitted": 0, "primary_scorer_or_wrapper_imports": 0, "model_generation_or_readback_calls": 0}
    descriptor = os.open(LOCK, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "r+b") as lock:
        require(stat.S_ISREG(os.fstat(lock.fileno()).st_mode), "Recompute lock is not regular")
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(not os.path.lexists(OUTPUT) and not os.path.lexists(STAGE), "Recompute attempt or retained staging exists")
        STAGE.mkdir(mode=0o700)
        try:
            binding, _ = check_binding_and_review(args, handles)
            expected, identities = load_primary_chain(binding, handles)
            kernel = load_independent_kernel(handles)
            import numpy as np
            require(np.__version__ == "1.26.4", "Recompute requires NumPy 1.26.4")
            frames = []
            for item in identities:
                body = Snapshot(item["blob"], item["tensor_body_sha256"], NBYTES)
                handles.append(body)
                body_handles.append(body)
                receipt["body_count"] += 1
                receipt["body_snapshot_bytes"] += len(body.raw)
                frame = np.frombuffer(body.raw, dtype=np.uint8).reshape(SHAPE)
                require(frame.flags.c_contiguous and not frame.flags.writeable, "Immutable pixel view differs")
                frames.append(frame)
            actual = kernel["recompute_frames"](frames, np)
            mismatches = compare_math(actual, expected)
            for item in handles:
                item.verify()
            for item in handles:
                item.close()
            receipt["body_bytes_read"] = sum(item.bytes_read for item in body_handles)
            receipt.update(status="PASS_EXACT_C1_NUMERIC_RECOMPUTE" if not mismatches else "MISMATCH_C1_NUMERIC_RECOMPUTE", audit_completed=True, exact_match=not mismatches)
            report = {"schema": "s46-c1-independent-recompute-report-v1", "row": "C1", "status": receipt["status"], "completed_utc": utc(), "sealed_primary_report_sha256": binding["sealed_score_report_sha256"], "authoritative_pixel_identities": identities, "math_result": actual, "mismatches": mismatches, "claim_boundary": "Arithmetic for one baseline row only; no visual quality, camera obedience, cohort, causality, method gain or novelty claim."}
            receipt["report_sha256"] = write_new(STAGE / "report.json", report)
            receipt["completed_utc"] = utc()
            write_new(STAGE / "receipt.json", receipt)
            sync_dir(STAGE)
            publish()
            return 0 if not mismatches else 1
        except Exception as error:
            receipt["body_bytes_read"] = sum(item.bytes_read for item in body_handles)
            receipt.update(status="FAILED_C1_INDEPENDENT_RECOMPUTE", audit_completed=False, exact_match=False, completed_utc=utc(), error={"type": type(error).__name__, "message": str(error)[:512]})
            if STAGE.exists() and not (STAGE / "receipt.json").exists():
                write_new(STAGE / "receipt.json", receipt)
                sync_dir(STAGE)
            print(json.dumps({"status": receipt["status"], "error": receipt["error"]}), file=sys.stderr, flush=True)
            return 2
        finally:
            for item in handles:
                item.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binding", required=True, type=Path)
    parser.add_argument("--binding-sha256", required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--source-review", required=True, type=Path)
    parser.add_argument("--source-review-sha256", required=True)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
