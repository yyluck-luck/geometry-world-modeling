"""Offline regression checks for the S90 transport repair; never contacts the URL."""
import importlib.util
import json
import pathlib
import subprocess
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "index_rtmv_resumable.py"
spec = importlib.util.spec_from_file_location("s90_index", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_timeout_receipt():
    module.OUT = pathlib.Path(tempfile.mkdtemp(prefix="s90_timeout_"))
    plan = {"connect_timeout_seconds": 1, "request_timeout_seconds": 1,
            "redirect_cap": 1, "proxy": "http://127.0.0.1:9", "archive_bytes": 1024,
            "allowed_final_hosts": ["huggingface.co", "us.aws.cdn.hf.co"]}
    state = {"successful_requests": [], "failed_requests": []}
    original = subprocess.run

    def timeout(*args, **kwargs):
        (module.OUT / "001_0_header.bin.part").write_bytes(b"x" * 700)
        raise subprocess.TimeoutExpired("curl", kwargs.get("timeout"), output="leak", stderr="err")

    subprocess.run = timeout
    try:
        try:
            module.request_header("https://huggingface.co/x", plan, state, 0, 1)
        except RuntimeError as error:
            receipt = json.loads(str(error))
            assert receipt["kind"] == "timeout"
            assert receipt["body_bytes_before_cleanup"] == 700
            assert receipt["part_cleanup"] == "removed"
            assert not list(module.OUT.glob("*.part"))
        else:
            raise AssertionError("timeout was not converted to a structured receipt")
    finally:
        subprocess.run = original


def test_reconcile_and_allowlist():
    module.OUT = pathlib.Path(tempfile.mkdtemp(prefix="s90_reconcile_"))
    raw = b"\0" * 512
    body = module.OUT / "001_0_header.bin"
    body.write_bytes(raw)
    record = {"schema": "s90-transport-receipt-v2", "kind": "range_header", "offset": 0,
              "length": 512, "body": body.name, "body_sha256": module.sha256(raw)}
    state = {"schema": "test", "status": "READY", "next_header_offset": 0, "members": [],
             "seed_member_count": 0, "successful_requests": [], "failed_requests": [],
             "downloaded_header_bytes": 0}
    real_plan = json.loads((ROOT / "INDEX_PLAN.json").read_text())
    plan = {"scene": real_plan["scene"], "start_offset": 0, "archive_name": real_plan["archive_name"],
            "archive_commit": real_plan["archive_commit"], "archive_bytes": real_plan["archive_bytes"]}
    binding = {"archive_name": real_plan["archive_name"], "archive_commit": real_plan["archive_commit"],
               "archive_bytes": real_plan["archive_bytes"], "scene": real_plan["scene"]}
    journal = {"schema": "s90-inflight-v1", "plan_sha256": module.sha256((ROOT / "INDEX_PLAN.json").read_bytes()),
               "code_sha256": module.sha256(SOURCE.read_bytes()), "archive_identity": binding,
               "offset": 0, "body": body.name, "body_sha256": module.sha256(raw), "record": record}
    (module.OUT / "INFLIGHT.json").write_text(json.dumps(journal))
    module.reconcile_inflight(state, plan)
    assert state["status"] == "FIRST_ZERO_TAR_BLOCK"
    assert len(state["successful_requests"]) == 1
    assert not (module.OUT / "INFLIGHT.json").exists()
    # Terminal zero keeps next_header_offset unchanged; an orphan journal
    # after checkpoint persistence must still be removed without duplication.
    (module.OUT / "INFLIGHT.json").write_text(json.dumps(journal))
    module.reconcile_inflight(state, plan)
    assert len(state["successful_requests"]) == 1
    assert not (module.OUT / "INFLIGHT.json").exists()
    stale = dict(journal)
    stale["offset"] = 512
    stale["record"] = dict(record, offset=512)
    (module.OUT / "INFLIGHT.json").write_text(json.dumps(stale))
    try:
        module.reconcile_inflight(state, plan)
    except RuntimeError as error:
        assert "offset" in str(error)
    else:
        raise AssertionError("stale terminal inflight journal was accepted")
    malformed = dict(journal)
    malformed["record"] = dict(record, kind="WRONG", length=999)
    (module.OUT / "INFLIGHT.json").write_text(json.dumps(malformed))
    try:
        module.reconcile_inflight(state, plan)
    except RuntimeError as error:
        assert "receipt" in str(error)
    else:
        raise AssertionError("malformed inflight receipt was accepted")
    module.assert_canonical_source_url(
        "https://huggingface.co/datasets/TontonTremblay/RTMV/resolve/"
        f"{real_plan['archive_commit']}/{real_plan['archive_name']}", real_plan)
    for suffix in ("?download=1", "#fragment"):
        try:
            module.assert_canonical_source_url(
                "https://huggingface.co/datasets/TontonTremblay/RTMV/resolve/"
                f"{real_plan['archive_commit']}/{real_plan['archive_name']}" + suffix, real_plan)
        except RuntimeError:
            pass
        else:
            raise AssertionError("canonical URL query or fragment was accepted")
    bad_schema = dict(journal, schema="wrong-schema")
    (module.OUT / "INFLIGHT.json").write_text(json.dumps(bad_schema))
    try:
        module.reconcile_inflight(state, plan)
    except RuntimeError as error:
        assert "schema" in str(error)
    else:
        raise AssertionError("wrong inflight schema was accepted")
    bad_record = dict(journal, record=dict(record, schema="wrong-receipt-schema"))
    (module.OUT / "INFLIGHT.json").write_text(json.dumps(bad_record))
    try:
        module.reconcile_inflight(state, plan)
    except RuntimeError as error:
        assert "receipt" in str(error)
    else:
        raise AssertionError("wrong transport receipt schema was accepted")
    assert module.host_allowed("us.aws.cdn.hf.co", ["huggingface.co", "us.aws.cdn.hf.co"])
    assert not module.host_allowed("evil.example", ["huggingface.co", "us.aws.cdn.hf.co"])


if __name__ == "__main__":
    test_timeout_receipt()
    test_reconcile_and_allowlist()
    print("S90_TRANSPORT_REPAIR_OFFLINE_PASS")
