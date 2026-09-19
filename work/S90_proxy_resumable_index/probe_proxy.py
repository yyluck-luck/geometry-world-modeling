"""Run one frozen 512-byte RTMV tar-header request through a local proxy."""
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import hashlib
import json
import re
import subprocess
import tarfile
import time


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "S89_matched_view_index" / "INDEX_PLAN.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def scrub(value: str) -> str:
    return re.sub(r"(https?://[^\s?]+)\?[^\s]+", r"\1?[REDACTED_QUERY]", value)


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def decode_tar_header(raw: bytes, offset: int) -> dict:
    item = tarfile.TarInfo.frombuf(raw, encoding="utf-8", errors="strict")
    if item.type not in (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE):
        raise ValueError("unsupported tar extension/type")
    if item.isdir() and item.size != 0:
        raise ValueError("non-empty directory entry")
    path = PurePosixPath(item.name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("unsafe or empty tar member name")
    return {
        "header_offset": offset,
        "content_offset": offset + 512,
        "name": item.name,
        "normalized_name": str(path),
        "size": item.size,
        "type": item.type.decode("ascii"),
        "is_regular": item.isfile(),
        "is_directory": item.isdir(),
        "header_sha256": sha256(raw),
    }


def main() -> None:
    plan_bytes = (HERE / "PROBE_PLAN.json").read_bytes()
    plan = json.loads(plan_bytes)
    source_bytes = SOURCE.read_bytes()
    if sha256(source_bytes) != plan["source_plan_sha256"]:
        raise RuntimeError("bound S89 plan changed")
    source = json.loads(source_bytes)
    if source["archive_bytes"] != plan["archive_bytes"]:
        raise RuntimeError("archive size identity mismatch")
    if source["start_offset"] != plan["offset"]:
        raise RuntimeError("resume offset identity mismatch")
    if plan["length"] != 512 or plan["offset"] % 512:
        raise RuntimeError("probe must be one aligned tar header")

    out = HERE / "probe_01"
    out.mkdir(exist_ok=False)
    body = out / "header.bin"
    receipt = {
        "schema": "s90-proxy-range-probe-receipt-v1",
        "started_utc": utc_now(),
        "status": "RUNNING",
        "plan_sha256": sha256(plan_bytes),
        "code_sha256": sha256(Path(__file__).read_bytes()),
        "source_plan_sha256": sha256(source_bytes),
        "request_count": 1,
        "offset": plan["offset"],
        "length": plan["length"],
        "proxy_host": "127.0.0.1",
        "proxy_port": 7897,
        "tls_verification_disabled": False,
        "system_proxy_modified": False,
        "credentials_read": False,
        "automatic_retries": 0,
        "image_or_depth_payloads_requested": 0,
        "json_payloads_requested": 0,
        "new_model_runs": 0,
        "scientific_result": False,
    }
    write_json(out / "RECEIPT.json", receipt)
    start = time.monotonic()
    command = [
        "/usr/bin/curl",
        "--connect-timeout", str(plan["connect_timeout_seconds"]),
        "--max-time", str(plan["wall_timeout_seconds"]),
        "--max-filesize", str(plan["transport_body_cap_bytes"]),
        "--retry", "0",
        "--max-redirs", str(plan["redirect_cap"]),
        "--proxy", plan["proxy"],
        "-L", "-sS",
        "-H", f"Range: bytes={plan['offset']}-{plan['offset'] + plan['length'] - 1}",
        "-D", "-",
        "-o", str(body),
        "-w", "\nS90_HTTP_CODE:%{http_code}\nS90_SSL_VERIFY:%{ssl_verify_result}\n",
        source["url"],
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    raw = body.read_bytes() if body.exists() else b""
    statuses = re.findall(r"S90_HTTP_CODE:(\d+)", result.stdout)
    verifies = re.findall(r"S90_SSL_VERIFY:(\d+)", result.stdout)
    ranges = re.findall(
        r"(?im)^content-range:\s*bytes\s+(\d+)-(\d+)/(\d+)", result.stdout
    )
    safe_headers = [
        scrub(line)
        for line in result.stdout.splitlines()
        if line.lower().startswith(
            (
                "http/", "content-range:", "content-length:", "content-type:",
                "accept-ranges:", "etag:", "last-modified:", "location:",
                "s90_http_code:", "s90_ssl_verify:",
            )
        )
    ]
    receipt.update(
        completed_utc=utc_now(),
        elapsed_seconds=time.monotonic() - start,
        curl_returncode=result.returncode,
        http_code=int(statuses[-1]) if statuses else None,
        ssl_verify_result=int(verifies[-1]) if verifies else None,
        safe_response_headers=safe_headers,
        stderr=scrub(result.stderr),
        body_bytes=len(raw),
        body_sha256=sha256(raw),
    )
    try:
        if result.returncode != 0:
            raise RuntimeError(f"curl transport return code {result.returncode}")
        if receipt["http_code"] != plan["expected_http"]:
            raise RuntimeError("final HTTP status is not exact 206")
        expected = [plan["offset"], plan["offset"] + 511, plan["archive_bytes"]]
        if not ranges or list(map(int, ranges[-1])) != expected:
            raise RuntimeError("final Content-Range identity mismatch")
        if len(raw) != 512:
            raise RuntimeError("body is not exactly one 512-byte tar header")
        receipt["tar_member"] = decode_tar_header(raw, plan["offset"])
        receipt["status"] = "VALIDATED_TAR_HEADER"
    except Exception as exc:
        receipt["status"] = "STOPPED"
        receipt["error_type"] = type(exc).__name__
        receipt["error"] = scrub(str(exc))
    write_json(out / "RECEIPT.json", receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k != "safe_response_headers"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
