#!/usr/bin/env python3
"""One disposable integration exercise; all score records and bodies are synthetic."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    import numpy as np
    io = load("synthetic_recompute_io", HERE / "recompute_c1_io.py")
    assert np.__version__ == "1.26.4" and sha(io.KERNEL) == io.KERNEL_SHA
    assert not io.OUTPUT.exists() and not io.STAGE.exists() and not io.LOCK.exists()
    real_formal_paths = (io.OUTPUT, io.STAGE, io.LOCK)
    independent = load("synthetic_independent_math", io.KERNEL)
    math_selftest = independent.synthetic_self_test()
    binder = load("synthetic_identity_renderer", io.PREPARATION / "bind_identity_only.py")
    recompute_template = json.loads(io.TEMPLATE.read_text())
    contract_template = json.loads(io.CONTRACT_TEMPLATE.read_text())
    with tempfile.TemporaryDirectory(prefix="s46-independent-io-synthetic-") as raw:
        temporary = Path(raw).resolve()
        io.HERE = temporary / "C1_independent_recompute"
        io.HERE.mkdir()
        io.PRIMARY_DIR = temporary / "C1_score_attempt_01"
        io.PRIMARY_DIR.mkdir()
        io.PRIMARY_BINDING = temporary / "WRAPPER_EXECUTION_BINDING.json"
        io.TENSOR_DIR = temporary / "tensors"
        io.TENSOR_DIR.mkdir()
        io.OUTPUT, io.STAGE, io.LOCK = (io.HERE / name for name in ("execution_01", ".execution_01.staging", ".independent_recompute.lock"))
        frames = [np.full(io.SHAPE, 255 if frame_id == 8 else frame_id, dtype=np.uint8) for frame_id in range(9)]
        identities = []
        for frame_id, frame in enumerate(frames):
            descriptor = hashlib.sha256(("synthetic-independent-id-%d" % frame_id).encode()).hexdigest()
            blob = io.TENSOR_DIR / (descriptor + ".bin")
            blob.write_bytes(frame.tobytes())
            identities.append({"id": frame_id, "tensor_descriptor_sha256": descriptor, "tensor_body_sha256": sha(blob), "blob": str(blob)})
        # The expected synthetic report comes from the same independent kernel.
        # This tests I/O/identity/comparison plumbing, not independent mathematics.
        expected = independent.recompute_frames(frames, np)
        expected.update(schema="s46-c1-blind-score-math-candidate-v1", primary_pair=[0, 8], cohort_status="INCOMPLETE_C2_STILL_REQUIRED", images_opened_or_emitted=0)
        expected.pop("images_viewed_or_emitted")
        contract = dict(contract_template)
        contract.update(schema="s46-c1-blind-scoring-bound-contract-v1", status="BOUND_C1_IDENTITY_CANDIDATE_AWAITING_DUAL_SOURCE_REVIEW_AND_BLINDNESS_ATTESTATION", template_path=str(io.CONTRACT_TEMPLATE), template_sha256=io.CONTRACT_TEMPLATE_SHA)
        contract["binding_slots"] = {"authorized_attempt": 1, "authorized_output_path": str(io.PRIMARY_DIR), "archive_tensor_directory": str(io.TENSOR_DIR), "authoritative_pixel_identities": identities}
        contract_path = temporary / "CONTRACT.json"
        io.write_new(contract_path, contract)
        execution = {"schema": "s46-c1-blind-scoring-wrapper-execution-binding-v1", "status": "BOUND_C1_BLIND_SCORING_WRAPPER_EXECUTION_AWAITING_EXACT_GATE_VALIDATION", "completed_utc": io.utc(), "row": "C1", "bound_contract": {"path": str(contract_path), "sha256": sha(contract_path)}, "authorized_output_path": str(io.PRIMARY_DIR)}
        io.write_new(io.PRIMARY_BINDING, execution)
        report = {"schema": "s46-c1-blind-score-report-v1", "status": "PASS_C1_BLIND_SCORE_TECHNICALLY_VALID", "row": "C1", "completed_utc": io.utc(), "binding_path": str(io.PRIMARY_BINDING), "binding_sha256": sha(io.PRIMARY_BINDING), "frozen_scorer_sha256": io.PRIMARY_KERNEL_SHA, "math_result": expected, "c1_pixel_bodies_read": 9, "images_rendered_or_viewed": 0}
        report_path = io.PRIMARY_DIR / "report.json"
        receipt_path = io.PRIMARY_DIR / "receipt.json"
        io.write_new(report_path, report)
        io.write_new(receipt_path, {"schema": "s46-c1-blind-score-receipt-v1", "status": "PASS_C1_BLIND_SCORE_TERMINAL", "technically_valid": True, "attempt": 1, "out": str(io.PRIMARY_DIR), "completed_utc": io.utc(), "binding_path": str(io.PRIMARY_BINDING), "binding_sha256": sha(io.PRIMARY_BINDING), "report_sha256": sha(report_path)})
        identity_input = {"schema": "s46-c1-recompute-identity-binding-v1", "status": "READY_TO_BIND_AFTER_SEALED_C1_PRIMARY_SCORE", "row": "C1", "completed_utc": io.utc(), "sealed_score_attempt": 1, "sealed_score_receipt_path": str(receipt_path), "sealed_score_receipt_sha256": sha(receipt_path), "sealed_score_report_path": str(report_path), "sealed_score_report_sha256": sha(report_path), "recompute_source_path": str(io.SELF), "recompute_source_sha256": sha(io.SELF), "authorized_output_path": str(io.OUTPUT)}
        identity_path = temporary / "IDENTITY_INPUT.json"
        io.write_new(identity_path, identity_input)
        rendered = binder.bind_recompute(recompute_template, identity_input, identity_path, sha(identity_path))
        binding_path = temporary / "BOUND_RECOMPUTE.json"
        io.write_new(binding_path, rendered)
        assert rendered["recompute_source_review_path"] is None and rendered["recompute_source_review_sha256"] is None
        review_path = temporary / "SYNTHETIC_REVIEW.json"
        io.write_new(review_path, {"schema": "s46-c1-independent-recompute-source-review-v1", "status": "PASS_S46_C1_INDEPENDENT_RECOMPUTE_SOURCE_REVIEW", "row": "C1", "source_path": str(io.SELF), "source_sha256": sha(io.SELF), "kernel_path": str(io.KERNEL), "kernel_sha256": io.KERNEL_SHA, "bound_binding_path": str(binding_path), "bound_binding_sha256": sha(binding_path), "source_author_role": io.AUTHOR, "kernel_author_role": io.KERNEL_AUTHOR, "reviewer_role": "/synthetic/disposable_reviewer_not_actual_authority", "executed": False, "images_viewed": False, "tensor_or_image_payload_bodies_read": False, "blocking_findings": [], "completed_utc": io.utc()})
        previous_argv = sys.argv
        try:
            sys.argv = [str(io.SELF), "--binding", str(binding_path), "--binding-sha256", sha(binding_path), "--source-sha256", sha(io.SELF), "--source-review", str(review_path), "--source-review-sha256", sha(review_path)]
            code = io.main()
        finally:
            sys.argv = previous_argv
        assert code == 0 and io.OUTPUT.is_dir() and not io.STAGE.exists()
        actual_receipt = json.loads((io.OUTPUT / "receipt.json").read_text())
        actual_report = json.loads((io.OUTPUT / "report.json").read_text())
        assert actual_receipt["exact_match"] is True and actual_receipt["audit_completed"] is True
        assert actual_receipt["report_sha256"] == sha(io.OUTPUT / "report.json")
        assert actual_report["mismatches"] == [] and actual_report["math_result"]["primary"]["mse_float64_hex"] == float(1.0).hex()
        assert actual_receipt["body_count"] == 9 and actual_receipt["body_snapshot_bytes"] == 8957952 and actual_receipt["body_bytes_read"] == 26873856
        assert all(not path.exists() for path in real_formal_paths)
        print(json.dumps({"status": "PASS_EXISTING_MATH_AND_ONE_SYNTHETIC_IDENTITY_IO_INTEGRATION_ONLY", "python": sys.version, "numpy": np.__version__, "io_source_sha256": sha(io.SELF), "kernel_sha256": io.KERNEL_SHA, "math_selftest": math_selftest, "actual_main_returncode": code, "synthetic_receipt": actual_receipt, "synthetic_report": actual_report, "real_body_bytes_read": 0, "real_score_records_read": 0, "formal_binding_created": False, "formal_recompute_executed": False, "primary_scorer_or_wrapper_imports": 0, "scope": "Original binder pure renderer and same production main/run; only disposable path constants are overridden. Expected fixture uses the same independent kernel and is not independent mathematical validation."}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
