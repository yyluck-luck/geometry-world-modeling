#!/usr/bin/env python3
"""Bounded, resumable TUM TGZ downloader; no image decoding or model execution.

Each network request runs in a child process with a 45-second wall-clock limit.
Six total attempts per request (five retries), at most six 4-MiB workers.
Example defaults target fr2/desk in its own new download directory.
"""
import argparse
import concurrent.futures
from datetime import datetime, timezone
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
import threading
import time
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEQUENCE = "rgbd_dataset_freiburg2_desk"
DEFAULT_URL = "https://webshare.cvg.cit.tum.de/g/rgbd/dataset/freiburg2/rgbd_dataset_freiburg2_desk.tgz"
DEFAULT_BYTES = 1893351095
DEFAULT_ETAG = '"70da3eb7-4ae2a1e2d7e40"'
CHUNK_BYTES = 4 * 1024 * 1024
REQUEST_SECONDS = 45
ATTEMPTS = 6
MAX_MEMBERS = 100000
MAX_UNPACKED_BYTES = 32 * 1024 ** 3


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def atomic_json(path, data):
    path = Path(path)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temporary.open("x", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


class DownloadError(RuntimeError):
    pass


class IdentityError(DownloadError):
    """Fatal identity change: never join bytes from differing versions."""


def request_worker(spec_path):
    """Internal subprocess entry point. Never used by a --help invocation."""
    spec = json.loads(Path(spec_path).read_text())
    response_record = {"started_utc": now(), "request": spec}
    started = time.monotonic()
    try:
        headers = {"Accept-Encoding": "identity", "User-Agent": "TUM-research-downloader/1"}
        if spec["method"] == "GET":
            headers.update(Range=f'bytes={spec["start"]}-{spec["end"]}',
                           **{"If-Match": spec["etag"]})
        req = urllib.request.Request(spec["url"], headers=headers, method=spec["method"])
        with urllib.request.urlopen(req, timeout=REQUEST_SECONDS) as response:
            response_record.update(status=response.status, final_url=response.url,
                                   headers=dict(response.headers))
            atomic_json(spec["response_path"], response_record)
            if response.headers.get("ETag") != spec["etag"]:
                raise IdentityError("ETag differs from the pinned archive identity")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise DownloadError("Unexpected content encoding")
            if spec["method"] == "HEAD":
                if response.status != 200 or response.headers.get("Content-Length") != str(spec["total"]):
                    raise IdentityError("HEAD status or total size differs from the pinned archive")
            else:
                expected_range = f'bytes {spec["start"]}-{spec["end"]}/{spec["total"]}'
                if response.status != 206 or response.headers.get("Content-Range") != expected_range:
                    raise DownloadError("GET must return exact 206 Content-Range: " + expected_range)
                count = spec["end"] - spec["start"] + 1
                if response.headers.get("Content-Length") not in (None, str(count)):
                    raise DownloadError("Range Content-Length mismatch")
                remaining = count + 1
                with Path(spec["payload_path"]).open("xb") as handle:
                    while remaining:
                        block = response.read(min(64 * 1024, remaining))
                        if not block:
                            break
                        handle.write(block)
                        remaining -= len(block)
                    handle.flush()
                    os.fsync(handle.fileno())
                if Path(spec["payload_path"]).stat().st_size != count:
                    raise DownloadError("Range payload is short or overlong")
        response_record.update(status_result="ok", completed_utc=now(),
                               elapsed_seconds=time.monotonic() - started)
        atomic_json(spec["response_path"], response_record)
        return 0
    except Exception as exc:
        if isinstance(exc, urllib.error.HTTPError):
            response_record.update(status=exc.code, headers=dict(exc.headers))
        response_record.update(status_result="failed", completed_utc=now(),
                               error_type=type(exc).__name__, error=str(exc),
                               elapsed_seconds=time.monotonic() - started)
        if isinstance(exc, IdentityError) or isinstance(exc, urllib.error.HTTPError) and exc.code == 412:
            response_record["identity_failure"] = True
        atomic_json(spec["response_path"], response_record)
        return 2


def checked_members(archive, sequence, max_unpacked=MAX_UNPACKED_BYTES):
    """Validate gzip CRC to EOF, every tar member, full file data and SHA256."""
    decompressed_bytes = 0
    with gzip.open(archive, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            decompressed_bytes += len(block)
            if decompressed_bytes > max_unpacked:
                raise DownloadError("Decompressed tar exceeds the declared safety limit")
    records, seen, file_names = [], set(), set()
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar:
            if len(records) >= MAX_MEMBERS:
                raise DownloadError("Tar member count exceeds the declared safety limit")
            raw = member.name
            parts = PurePosixPath(raw).parts
            if (not parts or raw.startswith("/") or ".." in parts or "\\" in raw
                    or "\x00" in raw or len(raw) > 4096 or parts[0] != sequence):
                raise DownloadError("Unsafe tar path or unexpected dataset root: " + repr(raw))
            name = "/".join(parts)
            if name in seen or not (member.isfile() or member.isdir()):
                raise DownloadError("Duplicate path or non-ordinary tar member: " + repr(raw))
            if len(parts) == 1 and not member.isdir():
                raise DownloadError("Dataset root must be a directory")
            if member.size < 0 or any("/".join(parts[:i]) in file_names for i in range(1, len(parts))):
                raise DownloadError("Invalid tar size or file used as parent directory")
            if member.isfile() and any(p.startswith(name + "/") for p in seen):
                raise DownloadError("File collides with an existing directory subtree")
            seen.add(name)
            record = {"name": name, "type": "directory" if member.isdir() else "file", "bytes": member.size}
            if member.isfile():
                file_names.add(name)
                h, actual = hashlib.sha256(), 0
                with tar.extractfile(member) as source:
                    for block in iter(lambda: source.read(1024 * 1024), b""):
                        h.update(block)
                        actual += len(block)
                if actual != member.size:
                    raise DownloadError("Truncated tar member: " + name)
                record["sha256"] = h.hexdigest()
            records.append(record)
        # tarfile tolerates a missing terminator and can ignore trailing bytes.
        # Require the full remainder after the final member to be zero padding.
        tar.fileobj.seek(tar.offset)
        padding = 0
        for block in iter(lambda: tar.fileobj.read(1024 * 1024), b""):
            if any(block):
                raise DownloadError("Nonzero bytes after the final tar member")
            padding += len(block)
        if padding < 1024 or decompressed_bytes % 512:
            raise DownloadError("Missing tar terminator or incomplete tar block")
    if not records or not file_names:
        raise DownloadError("Archive contains no regular dataset files")
    return {"gzip_validated_to_eof": True, "decompressed_tar_bytes": decompressed_bytes,
            "tar_members": len(records), "files": len(file_names), "members": records}


def verify_existing_extraction(target, sequence, records):
    """Reuse only a byte-identical existing tree; never overwrite its contents."""
    if target.is_symlink() or not target.is_dir():
        raise DownloadError("Existing extraction root is not an ordinary directory")
    expected = {r["name"][len(sequence) + 1:]: r for r in records if r["type"] == "file"}
    expected_dirs = {""}
    for r in records:
        relative = PurePosixPath(r["name"]).relative_to(sequence)
        if r["type"] == "directory":
            expected_dirs.add("" if str(relative) == "." else relative.as_posix())
        for parent in relative.parents:
            expected_dirs.add("" if str(parent) == "." else parent.as_posix())
    actual, actual_dirs = set(), set()
    for directory, dirs, files in os.walk(target, followlinks=False):
        directory_relative = Path(directory).relative_to(target).as_posix()
        actual_dirs.add("" if directory_relative == "." else directory_relative)
        for name in dirs + files:
            if (Path(directory) / name).is_symlink():
                raise DownloadError("Existing extraction contains a symlink")
        for name in files:
            path = Path(directory) / name
            relative = path.relative_to(target).as_posix()
            actual.add(relative)
            r = expected.get(relative)
            if not path.is_file() or not r or path.stat().st_size != r["bytes"] or digest(path) != r["sha256"]:
                raise DownloadError("Existing extraction differs; refusing overwrite: " + relative)
    if actual != set(expected) or actual_dirs != expected_dirs:
        raise DownloadError("Existing extraction is incomplete; refusing overwrite")


def safe_extract(archive, output, sequence, validated, run_id):
    extract_root = output / "extracted"
    if extract_root.is_symlink():
        raise DownloadError("Extraction directory must not be a symlink")
    extract_root.mkdir(exist_ok=True)
    target = extract_root / sequence
    if target.exists() or target.is_symlink():
        verify_existing_extraction(target, sequence, validated["members"])
        return {"root": str(target), "reused_verified_tree": True, "completed_utc": now()}
    stage = output / ("extraction_stage_" + run_id)
    stage.mkdir()  # Failed staging directories are intentionally retained.
    expected = {r["name"]: r for r in validated["members"]}
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar:
            parts = PurePosixPath(member.name).parts
            name = "/".join(parts)
            r = expected.get(name)
            if r is None or r["type"] != ("directory" if member.isdir() else "file"):
                raise DownloadError("Archive changed after validation")
            path = stage.joinpath(*parts)
            if member.isdir():
                path.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                path.parent.mkdir(parents=True, exist_ok=True)
                h, count = hashlib.sha256(), 0
                with tar.extractfile(member) as source, path.open("xb") as destination:
                    for block in iter(lambda: source.read(1024 * 1024), b""):
                        destination.write(block)
                        h.update(block)
                        count += len(block)
                if count != r["bytes"] or h.hexdigest() != r["sha256"]:
                    raise DownloadError("Extracted bytes differ from preflight validation")
            else:
                raise DownloadError("Unsafe member in extraction pass")
    if target.exists() or target.is_symlink():
        raise DownloadError("Target appeared during extraction; refusing overwrite")
    (stage / sequence).rename(target)
    stage.rmdir()
    return {"root": str(target), "reused_verified_tree": False, "completed_utc": now()}


class Downloader:
    def __init__(self, url, size, etag, sequence, output, workers=6,
                 chunk_bytes=CHUNK_BYTES, attempts=ATTEMPTS, retry_delay=True):
        if not 1 <= workers <= 6 or not 1 <= chunk_bytes <= CHUNK_BYTES or not 1 <= attempts <= ATTEMPTS:
            raise ValueError("Workers, chunk size or attempts exceed the bounded policy")
        if size <= 0 or not re.fullmatch(r"rgbd_dataset_[A-Za-z0-9_]+", sequence):
            raise ValueError("Invalid total size or dataset name")
        if not re.fullmatch(r'"[^"\r\n]+"', etag):
            raise ValueError("A pinned strong HTTP ETag is required")
        if not url.startswith(("https://", "http://")):
            raise ValueError("URL must use HTTP(S)")
        self.config = dict(source_url=url, expected_bytes=size, etag=etag, sequence=sequence,
                           chunk_bytes=chunk_bytes)
        self.output = Path(output).resolve()
        self.workers, self.attempts, self.retry_delay = workers, attempts, retry_delay
        self.run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8]
        self.stop = threading.Event()
        self.meta = {}

    def checkpoint(self):
        self.meta["updated_utc"] = now()
        atomic_json(self.output / "download_manifest.json", self.meta)

    def request(self, label, **fields):
        attempts_dir = self.output / "request_attempts" / self.run_id
        attempts_dir.mkdir(parents=True, exist_ok=True)
        for attempt in range(1, self.attempts + 1):
            if self.stop.is_set():
                raise DownloadError("Cancelled after another worker's failure")
            stem = attempts_dir / f"{label}_attempt{attempt}"
            spec = dict(url=self.config["source_url"], total=self.config["expected_bytes"],
                        etag=self.config["etag"], response_path=str(stem) + ".response.json",
                        payload_path=str(stem) + ".part", **fields)
            atomic_json(str(stem) + ".request.json", spec)
            try:
                process = subprocess.run([sys.executable, str(Path(__file__).resolve()), "_request", str(stem) + ".request.json"],
                                         capture_output=True, text=True, timeout=REQUEST_SECONDS)
                (Path(str(stem) + ".log")).write_text(process.stdout + process.stderr)
                response_path = Path(spec["response_path"])
                record = json.loads(response_path.read_text()) if response_path.exists() else {}
                if process.returncode == 0 and record.get("status_result") == "ok":
                    return spec, record
                if record.get("identity_failure"):
                    self.stop.set()
                    raise IdentityError(record.get("error", "Remote identity changed"))
                failure = record.get("error", f"Request process exit {process.returncode}")
            except subprocess.TimeoutExpired as exc:
                timeout_record = dict(status_result="failed", error="45-second request wall-clock deadline",
                                      completed_utc=now(), timeout_seconds=REQUEST_SECONDS)
                atomic_json(str(stem) + ".deadline.json", timeout_record)
                failure = timeout_record["error"]
                (Path(str(stem) + ".log")).write_text(str(exc))
            print(json.dumps({"event": "request_failed", "label": label, "attempt": attempt,
                              "max_attempts": self.attempts, "error": failure, "utc": now()}), flush=True)
            if attempt == self.attempts:
                raise DownloadError(f"{label}: exhausted {self.attempts} attempts: {failure}")
            if self.retry_delay and self.stop.wait(min(2 ** (attempt - 1), 8)):
                raise DownloadError("Cancelled during bounded retry backoff")
        raise AssertionError("Bounded loop exhausted without return or failure")

    def chunk(self, index, old):
        start = index * self.config["chunk_bytes"]
        end = min(self.config["expected_bytes"], start + self.config["chunk_bytes"]) - 1
        path = self.output / "chunks" / f"{index:06d}.bin"
        if path.exists() or path.is_symlink():
            if (not path.is_symlink() and path.is_file() and old and old.get("start") == start
                    and old.get("end") == end and old.get("etag") == self.config["etag"]
                    and path.stat().st_size == end - start + 1
                    and digest(path) == old.get("sha256")):
                return dict(old, reused=True, cache_rechecked_utc=now())
            quarantine = self.output / "failed_cache" / self.run_id
            quarantine.mkdir(parents=True, exist_ok=True)
            path.rename(quarantine / path.name)
        spec, response = self.request(f"chunk{index:06d}", method="GET", start=start, end=end)
        temporary = Path(spec["payload_path"])
        record = dict(index=index, start=start, end=end, bytes=temporary.stat().st_size,
                      sha256=digest(temporary), etag=self.config["etag"], reused=False,
                      completed_utc=now(), response_path=str(Path(spec["response_path"]).relative_to(self.output)))
        if path.exists() or path.is_symlink():
            raise DownloadError("Chunk destination unexpectedly exists; refusing overwrite")
        temporary.rename(path)
        return record

    def run(self):
        self.output.mkdir(parents=True, exist_ok=True)
        with (self.output / ".download.lock").open("a+") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise DownloadError("Another downloader holds this directory lock") from exc
            run = dict(run_id=self.run_id, started_utc=now(), config=self.config, workers=self.workers,
                       request_wall_seconds=REQUEST_SECONDS, max_total_attempts=self.attempts)
            runs = self.output / "runs"
            runs.mkdir(exist_ok=True)
            run_path = runs / (self.run_id + ".json")
            atomic_json(run_path, run)
            active_meta = False
            try:
                manifest_path = self.output / "download_manifest.json"
                if manifest_path.exists():
                    self.meta = json.loads(manifest_path.read_text())
                    if self.meta.get("config") != self.config:
                        raise IdentityError("Existing manifest identity/config differs; use a new directory")
                    self.meta["previous_run_status"] = self.meta.get("status")
                else:
                    self.meta = dict(schema_version=1, config=self.config, first_started_utc=now(), chunks={})
                active_meta = True
                self.meta.update(status="checking_remote", current_run=self.run_id)
                self.checkpoint()
                _, head = self.request("head", method="HEAD")
                self.meta.update(head=head, status="downloading")
                (self.output / "chunks").mkdir(exist_ok=True)
                self.checkpoint()
                total = (self.config["expected_bytes"] + self.config["chunk_bytes"] - 1) // self.config["chunk_bytes"]
                old = dict(self.meta["chunks"])
                completed, checked_bytes = 0, 0
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as pool:
                    futures = {pool.submit(self.chunk, i, old.get(str(i))): i for i in range(total)}
                    try:
                        for future in concurrent.futures.as_completed(futures):
                            result = future.result()
                            self.meta["chunks"][str(result["index"])] = result
                            completed += 1
                            checked_bytes += result["bytes"]
                            self.meta["progress"] = dict(chunks_checked=completed, chunks_total=total,
                                                         bytes_checked=checked_bytes)
                            self.checkpoint()
                            if completed == total or completed % 10 == 0:
                                print(json.dumps({"event": "progress", "utc": now(), **self.meta["progress"]}), flush=True)
                    except BaseException:
                        self.stop.set()
                        for future in futures:
                            future.cancel()
                        raise
                self.meta.update(status="assembling", download_completed_utc=now())
                self.checkpoint()
                assembled = self.output / ("assembly_" + self.run_id + ".tgz.part")
                h = hashlib.sha256()
                with assembled.open("xb") as destination:
                    for i in range(total):
                        path = self.output / "chunks" / f"{i:06d}.bin"
                        if digest(path) != self.meta["chunks"][str(i)]["sha256"]:
                            raise DownloadError("Chunk changed after its cached/downloaded SHA verification")
                        with path.open("rb") as source:
                            for block in iter(lambda: source.read(1024 * 1024), b""):
                                destination.write(block)
                                h.update(block)
                    destination.flush()
                    os.fsync(destination.fileno())
                if assembled.stat().st_size != self.config["expected_bytes"]:
                    raise DownloadError("Assembled archive size mismatch")
                archive = self.output / (self.config["sequence"] + ".tgz")
                if archive.exists() or archive.is_symlink():
                    if archive.is_symlink() or archive.stat().st_size != assembled.stat().st_size or digest(archive) != h.hexdigest():
                        raise DownloadError("Existing archive differs; refusing overwrite")
                    assembled.unlink()  # Identical successful temporary copy only.
                else:
                    assembled.rename(archive)
                self.meta.update(status="validating_archive", archive=dict(path=archive.name,
                                 bytes=archive.stat().st_size, sha256=h.hexdigest(), assembled_utc=now()))
                self.checkpoint()
                validated = checked_members(archive, self.config["sequence"])
                atomic_json(self.output / ("archive_integrity_" + self.run_id + ".json"), validated)
                self.meta.update(status="extracting", integrity=dict(gzip_validated_to_eof=True,
                                 tar_members=validated["tar_members"], files=validated["files"],
                                 record="archive_integrity_" + self.run_id + ".json"))
                self.checkpoint()
                self.meta["extraction"] = safe_extract(archive, self.output, self.config["sequence"], validated, self.run_id)
                self.meta.update(status="complete", completed_utc=now())
                self.checkpoint()
                run.update(status="complete", completed_utc=now(), archive=self.meta["archive"],
                           integrity=self.meta["integrity"], extraction=self.meta["extraction"])
                atomic_json(run_path, run)
                return run
            except BaseException as exc:
                self.stop.set()
                run.update(status="failed", completed_utc=now(), error_type=type(exc).__name__, error=str(exc))
                atomic_json(run_path, run)
                if active_meta:
                    self.meta.update(status="failed", failed_utc=now(), last_error=run)
                    self.checkpoint()
                raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--expected-bytes", type=int, default=DEFAULT_BYTES)
    parser.add_argument("--etag", default=DEFAULT_ETAG)
    parser.add_argument("--sequence", default=DEFAULT_SEQUENCE)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/tum/fr2_desk_download")
    parser.add_argument("--workers", type=int, choices=range(1, 7), default=6)
    args = parser.parse_args(argv)
    downloader = Downloader(args.url, args.expected_bytes, args.etag, args.sequence, args.output_dir, args.workers)
    print(json.dumps(downloader.run(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "_request":
        raise SystemExit(request_worker(sys.argv[2]))
    main()
