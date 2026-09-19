"""Resumably index a frozen RTMV tar prefix using exact 512-byte requests."""
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import hashlib
import json
import re
import subprocess
import tarfile
import time
import atexit
import fcntl
from urllib.parse import urlparse


HERE = Path(__file__).resolve().parent
OUT = HERE / "index_03"
_LOCK_HANDLE = None


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def scrub(value: str) -> str:
    return re.sub(r"(https?://[^\s?]+)\?[^\s]+", r"\1?[REDACTED_QUERY]", value)


def host_allowed(host: str, allowed: list[str]) -> bool:
    """Allow the frozen source host and its explicitly listed CDN suffixes."""
    host = (host or "").lower().rstrip(".")
    for entry in allowed:
        entry = entry.lower().rstrip(".")
        if entry.startswith("*."):
            suffix = entry[1:]
            if host.endswith(suffix) and host != suffix[1:]:
                return True
        elif host == entry:
            return True
    return False


def assert_canonical_source_url(url: str, plan: dict) -> None:
    parsed = urlparse(url)
    expected_path = f"/datasets/TontonTremblay/RTMV/resolve/{plan['archive_commit']}/{plan['archive_name']}"
    if (parsed.scheme != "https" or parsed.hostname != "huggingface.co"
            or parsed.path != expected_path or parsed.query or parsed.fragment):
        raise RuntimeError("source URL is not the frozen canonical HTTPS archive URL")


def acquire_output_lock() -> None:
    """Keep one invocation from interleaving checkpoint writes."""
    global _LOCK_HANDLE
    OUT.mkdir(exist_ok=True)
    handle = (OUT / ".LOCK").open("a+")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        handle.close()
        raise RuntimeError("another index invocation owns the output lock") from exc
    _LOCK_HANDLE = handle
    def release() -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()
    atexit.register(release)


def atomic_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def decode_tar_header(raw: bytes, offset: int) -> dict:
    if len(raw) != 512:
        raise ValueError("tar header is not 512 bytes")
    item = tarfile.TarInfo.frombuf(raw, encoding="utf-8", errors="strict")
    if item.size < 0:
        raise ValueError("negative tar member size")
    if item.type not in (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE):
        raise ValueError("unsupported tar extension/type")
    if item.isdir() and item.size != 0:
        raise ValueError("non-empty directory entry")
    path = PurePosixPath(item.name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("unsafe or empty member name")
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


def next_header_offset(item: dict) -> int:
    return item["content_offset"] + ((item["size"] + 511) // 512) * 512


def matched_views(members: list[dict], scene: str) -> dict:
    groups: dict[str, dict[str, list[dict]]] = {}
    pattern = re.compile(re.escape(scene) + r"/(\d{5})\.(json|depth\.exr|seg\.exr|exr)")
    for item in members:
        match = pattern.fullmatch(item["normalized_name"])
        if match and item["is_regular"]:
            view_id, suffix = match.groups()
            groups.setdefault(view_id, {}).setdefault(suffix, []).append(item)
    complete = sorted(
        view_id
        for view_id, suffixes in groups.items()
        if all(len(suffixes.get(suffix, [])) == 1 for suffix in ("json", "exr", "depth.exr"))
        and all(suffixes[suffix][0]["size"] > 0 for suffix in ("json", "exr", "depth.exr"))
    )
    return {
        "scene": scene,
        "scope": "verified scanned archive prefix, not whole scene",
        "selection_rule": "smallest complete five-digit ID in scanned prefix for format development only",
        "complete_view_ids": complete,
        "selected_development_view": complete[0] if complete else None,
        "all_views": groups,
        "body_contents_verified": False,
        "static_multiview_verified": False,
        "scientific_method_validated": False,
    }


def load_bound(path: Path, expected_sha: str) -> bytes:
    data = path.read_bytes()
    if sha256(data) != expected_sha:
        raise RuntimeError(f"bound evidence changed: {path.name}")
    return data


def seed_members(plan: dict) -> tuple[list[dict], str]:
    s89_path = HERE / plan["bindings"]["s89_plan"]["relative_path"]
    s89 = json.loads(load_bound(s89_path, plan["bindings"]["s89_plan"]["sha256"]))
    if s89["archive_bytes"] != plan["archive_bytes"] or s89["scene"] != plan["scene"]:
        raise RuntimeError("S89 archive identity changed")
    assert_canonical_source_url(s89["url"], plan)

    s88_path = HERE / plan["bindings"]["s88_receipt"]["relative_path"]
    s88 = json.loads(load_bound(s88_path, plan["bindings"]["s88_receipt"]["sha256"]))
    if s88["status"] != "FIRST_JSON_CAMERA_FIELDS_OBTAINED":
        raise RuntimeError("S88 seed receipt is not accepted state")
    members: list[dict] = []
    s88_dir = s88_path.parent
    for old in s88["members"]:
        request = next(
            item for item in s88["requests"]
            if item.get("kind") == "header" and item["offset"] == old["header_offset"]
        )
        raw = (s88_dir / request["body"]).read_bytes()
        if sha256(raw) != request["sha256"]:
            raise RuntimeError("S88 seed header hash changed")
        decoded = decode_tar_header(raw, old["header_offset"])
        if any(decoded[key] != old[key] for key in old):
            raise RuntimeError("S88 seed header decodes differently")
        members.append(decoded)

    probe_path = HERE / plan["bindings"]["s90_probe_receipt"]["relative_path"]
    probe = json.loads(load_bound(probe_path, plan["bindings"]["s90_probe_receipt"]["sha256"]))
    raw = load_bound(
        HERE / plan["bindings"]["s90_probe_header"]["relative_path"],
        plan["bindings"]["s90_probe_header"]["sha256"],
    )
    if probe["status"] != "VALIDATED_TAR_HEADER":
        raise RuntimeError("S90 probe is not validated")
    decoded = decode_tar_header(raw, probe["offset"])
    if decoded != probe["tar_member"]:
        raise RuntimeError("S90 probe header decodes differently")
    if next_header_offset(decoded) != plan["start_offset"]:
        raise RuntimeError("S90 start offset does not follow probe member")
    members.append(decoded)
    return members, s89["url"]


def verify_member_chain(state: dict, plan: dict) -> None:
    """Verify sparse seed members and the contiguous post-seed scan."""
    members = state["members"]
    if len(members) < state["seed_member_count"]:
        raise RuntimeError("checkpoint lost a seed member")
    names = [member["normalized_name"] for member in members]
    if len(set(names)) != len(names):
        raise RuntimeError("checkpoint contains duplicate member names")
    seeds = members[:state["seed_member_count"]]
    if any(member["header_offset"] < 0 or member["header_offset"] % 512 for member in seeds):
        raise RuntimeError("seed member offset is invalid")
    scanned = members[state["seed_member_count"]:]
    requests = state["successful_requests"]
    no_member_indices = [i for i, request in enumerate(requests) if "tar_member" not in request]
    terminal_zero = bool(no_member_indices == [len(requests) - 1]
                         and state["status"] == "FIRST_ZERO_TAR_BLOCK")
    if terminal_zero:
        expected_zero = plan["start_offset"] if not scanned else next_header_offset(scanned[-1])
        if requests[-1]["offset"] != expected_zero or state["next_header_offset"] != expected_zero:
            raise RuntimeError("zero tar block is not at the expected chain offset")
        requests = requests[:-1]
    elif no_member_indices:
        raise RuntimeError("a non-terminal successful request lacks a tar member")
    if len(scanned) != len(requests):
        raise RuntimeError("members and successful request counts differ")
    for request, member in zip(requests, scanned):
        if request["offset"] != member["header_offset"] or request["tar_member"] != member:
            raise RuntimeError("member/request chain mismatch")
    for left, right in zip(scanned, scanned[1:]):
        if next_header_offset(left) != right["header_offset"]:
            raise RuntimeError("scanned member chain has a gap")
    if scanned and state["next_header_offset"] != next_header_offset(scanned[-1]):
        raise RuntimeError("checkpoint next offset does not follow last member")
    if scanned and scanned[0]["header_offset"] != plan["start_offset"]:
        raise RuntimeError("scanned chain does not start at frozen offset")


def verify_checkpoint_headers(state: dict) -> None:
    previous = -1
    names = set()
    for request in state["successful_requests"]:
        if request["offset"] <= previous or request["offset"] % 512:
            raise RuntimeError("checkpoint header offsets are not increasing/aligned")
        previous = request["offset"]
        path = OUT / request["body"]
        raw = path.read_bytes()
        if len(raw) != 512 or sha256(raw) != request["body_sha256"]:
            raise RuntimeError("saved successful header changed")
        if "tar_member" not in request:
            if state["status"] == "FIRST_ZERO_TAR_BLOCK" and raw == b"\0" * 512:
                continue
            raise RuntimeError("successful request lacks tar member")
        decoded = decode_tar_header(raw, request["offset"])
        if decoded != request["tar_member"]:
            raise RuntimeError("saved successful header decodes differently")
        if decoded["normalized_name"] in names:
            raise RuntimeError("checkpoint contains duplicate tar member")
        names.add(decoded["normalized_name"])


def persist(state: dict, plan: dict) -> None:
    manifest = matched_views(state["members"], plan["scene"])
    atomic_json(OUT / "MATCHED_VIEWS.json", manifest)
    state["complete_view_ids"] = manifest["complete_view_ids"]
    state["selected_development_view"] = manifest["selected_development_view"]
    state["matched_manifest_sha256"] = sha256((OUT / "MATCHED_VIEWS.json").read_bytes())
    atomic_json(OUT / "CHECKPOINT.json", state)


def reconcile_inflight(state: dict, plan: dict) -> None:
    """Reconcile a request that finished before its checkpoint was persisted.

    This closes the common crash window without claiming exactly-once network
    semantics. A missing journal can still cause at-least-once re-requesting;
    a present journal is either committed once or rejected on mismatch.
    """
    path = OUT / "INFLIGHT.json"
    if not path.exists():
        return
    inflight = json.loads(path.read_text())
    if inflight.get("schema") != "s90-inflight-v1":
        raise RuntimeError("inflight journal schema is not s90-inflight-v1")
    expected_identity = {
        "archive_name": plan["archive_name"], "archive_commit": plan["archive_commit"],
        "archive_bytes": plan["archive_bytes"], "scene": plan["scene"],
    }
    if inflight.get("plan_sha256") != sha256((HERE / "INDEX_PLAN.json").read_bytes()):
        raise RuntimeError("inflight journal plan binding changed")
    if inflight.get("code_sha256") != sha256(Path(__file__).read_bytes()):
        raise RuntimeError("inflight journal code binding changed")
    if inflight.get("archive_identity") != expected_identity:
        raise RuntimeError("inflight journal archive identity changed")
    offset = inflight.get("offset")
    body_name = inflight.get("body")
    if not body_name or Path(body_name).name != body_name:
        raise RuntimeError("inflight journal body path is unsafe")
    record = dict(inflight.get("record") or {})
    if (record.get("schema") != "s90-transport-receipt-v2"
            or record.get("offset") != offset or record.get("body") != body_name
            or record.get("body_sha256") != inflight.get("body_sha256")
            or record.get("kind") != "range_header" or record.get("length") != 512):
        raise RuntimeError("inflight journal and transport receipt disagree")
    # A checkpoint may already contain this request (notably the terminal
    # zero block, whose next offset intentionally does not advance). In that
    # case the journal is only an orphan cleanup record; never append twice.
    existing = [item for item in state["successful_requests"] if item.get("offset") == offset]
    if existing:
        if any(item.get("body_sha256") == inflight.get("body_sha256") for item in existing):
            path.unlink()
            return
        raise RuntimeError("inflight journal collides with a different committed header hash")
    if offset != state["next_header_offset"]:
        raise RuntimeError("inflight journal offset does not match checkpoint next offset")
    body_path = OUT / body_name
    raw = body_path.read_bytes() if body_path.exists() else b""
    if len(raw) != 512 or sha256(raw) != inflight.get("body_sha256"):
        raise RuntimeError("inflight body is missing or changed")
    record["reconciled_after_restart"] = True
    if raw == b"\0" * 512:
        state["successful_requests"].append(record)
        state["downloaded_header_bytes"] += 512
        state["status"] = "FIRST_ZERO_TAR_BLOCK"
    else:
        item = decode_tar_header(raw, offset)
        if record.get("tar_member") != item:
            raise RuntimeError("inflight tar member does not match body")
        if item["normalized_name"] in {m["normalized_name"] for m in state["members"]}:
            raise RuntimeError("inflight tar member duplicates checkpoint")
        state["successful_requests"].append(record)
        state["members"].append(item)
        state["next_header_offset"] = next_header_offset(item)
        state["downloaded_header_bytes"] += 512
    state["updated_utc"] = utc_now()
    persist(state, plan)
    path.unlink()


def _parse_last_header_block(text: str) -> list[str]:
    """Return lines from the last HTTP response block only."""
    blocks = re.split(r"(?im)(?=^HTTP/\S+\s+\d+)", text)
    return blocks[-1].splitlines() if blocks else []


def _run_redirect_probe(url: str, plan: dict, remaining: float, probe_path: Path) -> tuple[str, dict]:
    """Read redirect headers with HEAD only; never follow or save a body."""
    timeout_seconds = max(0.01, min(plan["request_timeout_seconds"], remaining))
    command = [
        "/usr/bin/curl", "--connect-timeout", str(plan["connect_timeout_seconds"]),
        "--max-time", str(timeout_seconds), "--max-redirs", "0", "--max-filesize", "512", "--retry", "0",
        "--proxy", plan["proxy"], "--proto", "=https", "-sS", "--ignore-content-length", "-X", "HEAD",
        "-D", "-", "-o", str(probe_path),
        "-w", "\nS90_REDIRECT_HTTP_CODE:%{http_code}\nS90_REDIRECT_SSL_VERIFY:%{ssl_verify_result}\nS90_REDIRECT_URL_EFFECTIVE:%{url_effective}\n",
        url,
    ]
    began = utc_now()
    started = time.monotonic()
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        had_probe = probe_path.exists()
        if had_probe:
            probe_path.unlink()
        raise RuntimeError(json.dumps({
            "schema": "s90-transport-receipt-v2", "kind": "timeout",
            "stage": "redirect_headers", "started_utc": began, "completed_utc": utc_now(),
            "elapsed_seconds": time.monotonic() - started, "offset": None, "length": 512,
            "timeout_seconds": timeout_seconds, "partial_body_discarded": had_probe,
            "timeout_output": scrub(str(exc.output or ""))[:2000],
            "timeout_stderr": scrub(str(exc.stderr or ""))[:2000],
        }, ensure_ascii=False)) from exc
    raw = probe_path.read_bytes() if probe_path.exists() else b""
    if probe_path.exists():
        probe_path.unlink()
    lines = _parse_last_header_block(result.stdout)
    status = re.findall(r"S90_REDIRECT_HTTP_CODE:(\d+)", result.stdout)
    verify = re.findall(r"S90_REDIRECT_SSL_VERIFY:(\d+)", result.stdout)
    location = next((line.split(":", 1)[1].strip() for line in lines
                     if line.lower().startswith("location:")), None)
    effective = (re.findall(r"(?m)^S90_REDIRECT_URL_EFFECTIVE:(.*)$", result.stdout) or [""])[-1].strip()
    if result.returncode != 0:
        raise RuntimeError(json.dumps({"schema": "s90-transport-receipt-v2", "kind": "transport_failure",
                                       "stage": "redirect_headers", "curl_returncode": result.returncode,
                                       "http_code": int(status[-1]) if status else None,
                                       "ssl_verify_result": int(verify[-1]) if verify else None,
                                       "body_bytes": len(raw), "stderr": scrub(result.stderr)}, ensure_ascii=False))
    if raw:
        raise RuntimeError(json.dumps({"schema": "s90-transport-receipt-v2", "kind": "redirect_body",
                                       "stage": "redirect_headers", "body_bytes": len(raw),
                                       "body_sha256": sha256(raw), "error": "HEAD returned a body; headers-only rule"}, ensure_ascii=False))
    if not status or int(status[-1]) != 302:
        raise RuntimeError(json.dumps({"schema": "s90-transport-receipt-v2", "kind": "redirect_status",
                                       "stage": "redirect_headers", "http_code": int(status[-1]) if status else None,
                                       "ssl_verify_result": int(verify[-1]) if verify else None,
                                       "safe_response_headers": [scrub(x) for x in lines]}, ensure_ascii=False))
    if not verify or int(verify[-1]) != 0:
        raise RuntimeError(json.dumps({"schema": "s90-transport-receipt-v2", "kind": "tls_failure",
                                       "stage": "redirect_headers", "ssl_verify_result": int(verify[-1]) if verify else None}, ensure_ascii=False))
    if not location:
        raise RuntimeError(json.dumps({"schema": "s90-transport-receipt-v2", "kind": "redirect_missing_location",
                                       "stage": "redirect_headers", "safe_response_headers": [scrub(x) for x in lines]}, ensure_ascii=False))
    from urllib.parse import urljoin
    final_url = urljoin(url, location)
    parsed = urlparse(final_url)
    source_host = (urlparse(url).hostname or "").lower()
    final_host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host_allowed(final_host, plan["allowed_final_hosts"]):
        raise RuntimeError(json.dumps({"schema": "s90-transport-receipt-v2", "kind": "redirect_host",
                                       "stage": "redirect_headers", "final_host": final_host,
                                       "final_scheme": parsed.scheme}, ensure_ascii=False))
    if final_host == source_host:
        raise RuntimeError(json.dumps({"schema": "s90-transport-receipt-v2", "kind": "redirect_not_final_host",
                                       "stage": "redirect_headers", "final_host": final_host}, ensure_ascii=False))
    return final_url, {
        "stage": "redirect_headers", "curl_returncode": result.returncode,
        "http_code": int(status[-1]), "ssl_verify_result": int(verify[-1]),
        "url_effective": scrub(effective), "location": scrub(location),
        "final_url": scrub(final_url), "final_host": final_host,
        "body_bytes": 0, "safe_response_headers": [scrub(x) for x in lines],
    }


def request_header(url: str, plan: dict, state: dict, offset: int, remaining: float) -> tuple[dict, bytes]:
    attempt = len(state["successful_requests"]) + len(state["failed_requests"]) + 1
    part = OUT / f"{attempt:03d}_{offset}_header.bin.part"
    final = OUT / f"{attempt:03d}_{offset}_header.bin"
    began = utc_now()
    start = time.monotonic()
    probe_path = OUT / f"{attempt:03d}_{offset}_redirect_probe.part"
    final_url, redirect = _run_redirect_probe(url, plan, remaining, probe_path)
    timeout_seconds = max(0.01, min(plan["request_timeout_seconds"], remaining))
    command = [
        "/usr/bin/curl", "--connect-timeout", str(plan["connect_timeout_seconds"]),
        "--max-time", str(timeout_seconds), "--max-filesize", "512", "--retry", "0",
        "--proxy", plan["proxy"], "--proto", "=https", "-sS", "-D", "-",
        "-H", f"Range: bytes={offset}-{offset + 511}", "-o", str(part),
        "-w", "\nS90_HTTP_CODE:%{http_code}\nS90_SSL_VERIFY:%{ssl_verify_result}\nS90_URL_EFFECTIVE:%{url_effective}\n",
        final_url,
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        raw = part.read_bytes() if part.exists() else b""
        if part.exists():
            part.unlink()
        raise RuntimeError(json.dumps({"schema": "s90-transport-receipt-v2", "kind": "timeout",
                                       "stage": "range_header", "started_utc": began,
                                       "completed_utc": utc_now(), "elapsed_seconds": time.monotonic() - start,
                                       "offset": offset, "length": 512, "timeout_seconds": timeout_seconds,
                                       "body_bytes_before_cleanup": len(raw), "partial_body_discarded": bool(raw),
                                       "timeout_output": scrub(str(exc.output or ""))[:2000],
                                       "timeout_stderr": scrub(str(exc.stderr or ""))[:2000],
                                       "redirect": redirect}, ensure_ascii=False)) from exc
    raw = part.read_bytes() if part.exists() else b""
    statuses = re.findall(r"S90_HTTP_CODE:(\d+)", result.stdout)
    verifies = re.findall(r"S90_SSL_VERIFY:(\d+)", result.stdout)
    ranges = re.findall(r"(?im)^content-range:\s*bytes\s+(\d+)-(\d+)/(\d+)", result.stdout)
    record = {"started_utc": began, "completed_utc": utc_now(), "elapsed_seconds": time.monotonic() - start,
              "offset": offset, "length": 512, "schema": "s90-transport-receipt-v2", "kind": "range_header",
              "stage": "range_header", "curl_returncode": result.returncode,
              "http_code": int(statuses[-1]) if statuses else None, "ssl_verify_result": int(verifies[-1]) if verifies else None,
              "url_effective": scrub((re.findall(r"(?m)^S90_URL_EFFECTIVE:(.*)$", result.stdout) or [""])[-1].strip()),
              "final_host": (urlparse(final_url).hostname or "").lower(), "body_bytes": len(raw),
              "body_sha256": sha256(raw), "redirect": redirect,
              "safe_response_headers": [scrub(line) for line in result.stdout.splitlines()
                 if line.lower().startswith(("http/", "content-range:", "content-length:", "content-type:",
                    "accept-ranges:", "etag:", "last-modified:", "location:", "s90_http_code:",
                    "s90_ssl_verify:", "s90_url_effective:"))]}
    try:
        effective = urlparse(record["url_effective"])
        expected_host = (urlparse(final_url).hostname or "").lower()
        if effective.scheme != "https" or (effective.hostname or "").lower() != expected_host:
            raise RuntimeError("effective URL host differs from parsed redirect host")
        if result.returncode != 0:
            raise RuntimeError(f"curl transport return code {result.returncode}")
        if record["http_code"] != 206:
            raise RuntimeError("final HTTP status is not 206")
        if record["ssl_verify_result"] != 0:
            raise RuntimeError("TLS verification did not succeed")
        expected = [offset, offset + 511, plan["archive_bytes"]]
        if not ranges or list(map(int, ranges[-1])) != expected:
            raise RuntimeError("Content-Range identity mismatch")
        if len(raw) != 512:
            raise RuntimeError("response body is not 512 bytes")
        if raw != b"\0" * 512:
            record["tar_member"] = decode_tar_header(raw, offset)
        if final.exists():
            existing = final.read_bytes()
            if existing != raw:
                raise RuntimeError("refusing to overwrite an existing header with different bytes")
            part.unlink()
            record["existing_final_reused"] = True
        else:
            part.replace(final)
        record["body"] = final.name
        return record, raw
    except Exception:
        if part.exists():
            if part.stat().st_size > 512:
                part.unlink()
                record["partial_body_discarded"] = True
            elif part.exists():
                record["partial_body"] = part.name
        raise RuntimeError(json.dumps(record, ensure_ascii=False))

def main() -> None:
    plan_bytes = (HERE / "INDEX_PLAN.json").read_bytes()
    plan = json.loads(plan_bytes)
    code_sha = sha256(Path(__file__).read_bytes())
    OUT.mkdir(exist_ok=True)
    acquire_output_lock()
    checkpoint = OUT / "CHECKPOINT.json"
    if not checkpoint.exists() and any(path.name != ".LOCK" for path in OUT.iterdir()):
        raise RuntimeError("output directory is non-empty without a checkpoint; use a new reviewed run")
    if checkpoint.exists():
        state = json.loads(checkpoint.read_text())
        if state["plan_sha256"] != sha256(plan_bytes) or state["code_sha256"] != code_sha:
            raise RuntimeError("plan/code changed; checkpoint resume refused")
        identity = state.get("archive_identity", {})
        if identity != {
            "archive_name": plan["archive_name"],
            "archive_commit": plan["archive_commit"],
            "archive_bytes": plan["archive_bytes"],
            "scene": plan["scene"],
        }:
            raise RuntimeError("checkpoint archive identity is not bound to plan")
        if state["status"] in ("STOPPED_TRANSPORT", "STOPPED_ERROR"):
            raise RuntimeError("previous failure requires a new reviewed invocation plan")
        verify_checkpoint_headers(state)
        reconcile_inflight(state, plan)
        verify_checkpoint_headers(state)
        expected_seed, _ = seed_members(plan)
        if state["members"][:state["seed_member_count"]] != expected_seed:
            raise RuntimeError("checkpoint seed members differ from bound evidence")
        verify_member_chain(state, plan)
        # Revalidate the bound plan on every resume; a checkpoint alone must
        # not authorize a changed archive URL or commit.
        bound_path = HERE / plan["bindings"]["s89_plan"]["relative_path"]
        bound = json.loads(load_bound(bound_path, plan["bindings"]["s89_plan"]["sha256"]))
        if bound["archive_bytes"] != plan["archive_bytes"] or bound["scene"] != plan["scene"]:
            raise RuntimeError("resume archive identity changed")
        assert_canonical_source_url(bound["url"], plan)
        url = bound["url"]
    else:
        members, url = seed_members(plan)
        state = {
            "schema": "s90-resumable-tar-index-checkpoint-v1",
            "created_utc": utc_now(),
            "updated_utc": utc_now(),
            "status": "READY",
            "plan_sha256": sha256(plan_bytes),
            "code_sha256": code_sha,
            "archive_identity": {
                "archive_name": plan["archive_name"],
                "archive_commit": plan["archive_commit"],
                "archive_bytes": plan["archive_bytes"],
                "scene": plan["scene"],
            },
            "next_header_offset": plan["start_offset"],
            "seed_member_count": len(members),
            "members": members,
            "successful_requests": [],
            "failed_requests": [],
            "invocations": [],
            "downloaded_header_bytes": 0,
            "image_or_depth_payloads_requested": 0,
            "json_payloads_requested": 0,
            "new_model_runs": 0,
            "scientific_method_validated": False,
        }
        persist(state, plan)

    if state["selected_development_view"] is not None or state["status"] in ("SCENE_BOUNDARY", "FIRST_ZERO_TAR_BLOCK"):
        print(json.dumps({"status": state["status"], "no_op": True}, ensure_ascii=False))
        return
    if len(state["successful_requests"]) >= plan["max_new_headers_total"]:
        state["status"] = "TOTAL_HEADER_BUDGET_STOP"
        persist(state, plan)
        print(json.dumps({"status": state["status"]}, ensure_ascii=False))
        return

    invocation = {
        "started_utc": utc_now(),
        "start_offset": state["next_header_offset"],
        "successful_headers_before": len(state["successful_requests"]),
        "status": "RUNNING",
    }
    state["invocations"].append(invocation)
    state["status"] = "RUNNING"
    persist(state, plan)
    began = time.monotonic()
    successful_this_invocation = 0
    names = {member["normalized_name"] for member in state["members"]}

    while successful_this_invocation < plan["max_new_headers_per_invocation"]:
        if len(state["successful_requests"]) >= plan["max_new_headers_total"]:
            state["status"] = "TOTAL_HEADER_BUDGET_STOP"
            break
        remaining = plan["wall_seconds_per_invocation"] - (time.monotonic() - began)
        if remaining <= 0:
            state["status"] = "INVOCATION_WALL_BUDGET_STOP"
            break
        offset = state["next_header_offset"]
        try:
            record, raw = request_header(url, plan, state, offset, remaining)
            atomic_json(OUT / "INFLIGHT.json", {
                "schema": "s90-inflight-v1",
                "created_utc": utc_now(),
                "plan_sha256": state["plan_sha256"],
                "code_sha256": state["code_sha256"],
                "archive_identity": state["archive_identity"],
                "offset": offset,
                "body": record["body"],
                "body_sha256": record["body_sha256"],
                "record": record,
            })
            state["successful_requests"].append(record)
            state["downloaded_header_bytes"] += len(raw)
            successful_this_invocation += 1
            if raw == b"\0" * 512:
                state["status"] = "FIRST_ZERO_TAR_BLOCK"
                break
            item = record["tar_member"]
            following = next_header_offset(item)
            if following > plan["archive_bytes"]:
                raise RuntimeError("member extends beyond frozen archive size")
            if item["normalized_name"] in names:
                raise RuntimeError("duplicate member name; ambiguity retained and scan stopped")
            names.add(item["normalized_name"])
            state["members"].append(item)
            state["next_header_offset"] = following
            state["updated_utc"] = utc_now()
            persist(state, plan)
            (OUT / "INFLIGHT.json").unlink(missing_ok=True)
            if PurePosixPath(item["normalized_name"]).parts[0] != plan["scene"]:
                state["status"] = "SCENE_BOUNDARY"
                break
            if state["selected_development_view"] is not None:
                state["status"] = "FIRST_COMPLETE_VIEW"
                break
        except Exception as exc:
            message = str(exc)
            try:
                failed = json.loads(message)
            except json.JSONDecodeError:
                failed = {"offset": offset, "error": scrub(message)}
            state["failed_requests"].append(failed)
            transport_kinds = {"timeout", "range_header", "transport_failure"}
            state["status"] = (
                "STOPPED_TRANSPORT"
                if failed.get("kind") in transport_kinds
                or "curl" in message or "HTTP" in message or "Content-Range" in message
                else "STOPPED_ERROR"
            )
            break
    else:
        state["status"] = "INVOCATION_HEADER_BUDGET_STOP"

    invocation.update(
        completed_utc=utc_now(),
        elapsed_seconds=time.monotonic() - began,
        successful_headers_after=len(state["successful_requests"]),
        successful_this_invocation=successful_this_invocation,
        end_offset=state["next_header_offset"],
        status=state["status"],
    )
    state["updated_utc"] = utc_now()
    persist(state, plan)
    atomic_json(OUT / "RECEIPT.json", state)
    print(json.dumps({
        "status": state["status"],
        "successful_this_invocation": successful_this_invocation,
        "successful_total": len(state["successful_requests"]),
        "failed_total": len(state["failed_requests"]),
        "next_header_offset": state["next_header_offset"],
        "complete_view_ids": state["complete_view_ids"],
        "selected_development_view": state["selected_development_view"],
        "downloaded_header_bytes": state["downloaded_header_bytes"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
