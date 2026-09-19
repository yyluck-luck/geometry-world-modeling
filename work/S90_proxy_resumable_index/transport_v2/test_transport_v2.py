"""Offline tests for S90 transport_v2. No network is used."""
import importlib.util
import json
import pathlib
import tempfile
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("transport_v2", ROOT / "index_rtmv_transport_v2.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)


def run():
    mod.OUT = pathlib.Path(tempfile.mkdtemp(prefix="s90_transport_v2_"))
    plan = {"connect_timeout_seconds": 1, "request_timeout_seconds": 5,
            "redirect_cap": 5, "proxy": "http://127.0.0.1:9", "archive_bytes": 1024,
            "allowed_final_hosts": ["huggingface.co", "us.aws.cdn.hf.co"]}
    state = {"successful_requests": [], "failed_requests": []}
    calls = []
    original = subprocess.run
    final = "https://us.aws.cdn.hf.co/xet-bridge/test?X-Amz-Signature=secret"
    def fake(command, **kwargs):
        calls.append(command)
        out = command[command.index("-o") + 1]
        if "-X" in command:
            pathlib.Path(out).write_bytes(b"")
            return subprocess.CompletedProcess(command, 0,
                stdout="HTTP/2 302\r\nLocation: " + final + "\r\ncontent-length: 1034\r\n"
                       "S90_REDIRECT_HTTP_CODE:302\nS90_REDIRECT_SSL_VERIFY:0\n"
                       "S90_REDIRECT_URL_EFFECTIVE:https://huggingface.co/datasets/a\n",
                stderr="")
        pathlib.Path(out).write_bytes(b"\0" * 512)
        return subprocess.CompletedProcess(command, 0,
            stdout="HTTP/2 206\r\nContent-Range: bytes 0-511/1024\r\n"
                   "S90_HTTP_CODE:206\nS90_SSL_VERIFY:0\nS90_URL_EFFECTIVE:" + final + "\n",
            stderr="")
    subprocess.run = fake
    try:
        record, raw = mod.request_header("https://huggingface.co/datasets/a", plan, state, 0, 5)
    finally:
        subprocess.run = original
    assert len(calls) == 2
    assert "-X" in calls[0] and "-L" not in calls[0]
    assert "-L" not in calls[1] and "Range: bytes=0-511" in calls[1]
    assert record["http_code"] == 206 and record["body_bytes"] == 512
    assert record["redirect"]["final_host"] == "us.aws.cdn.hf.co"
    assert len(raw) == 512

    # A redirect response body is rejected and never treated as archive bytes.
    def bad_probe(command, **kwargs):
        out = command[command.index("-o") + 1]
        pathlib.Path(out).write_bytes(b"x")
        return subprocess.CompletedProcess(command, 0,
            stdout="HTTP/2 302\nLocation: " + final + "\nS90_REDIRECT_HTTP_CODE:302\nS90_REDIRECT_SSL_VERIFY:0\n",
            stderr="")
    mod.OUT = pathlib.Path(tempfile.mkdtemp(prefix="s90_transport_v2_body_"))
    subprocess.run = bad_probe
    try:
        try:
            mod.request_header("https://huggingface.co/datasets/a", plan, state, 0, 5)
        except RuntimeError as exc:
            info = json.loads(str(exc)); assert info["kind"] == "redirect_body"
        else:
            raise AssertionError("redirect body was accepted")
    finally:
        subprocess.run = original
    print("S90_TRANSPORT_V2_OFFLINE_PASS")

if __name__ == "__main__":
    run()
