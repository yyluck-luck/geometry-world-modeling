#!/usr/bin/env python3
"""Download the official public CUT3R 224 checkpoint with validated ranges.

Retains partial chunks on errors and never replaces an unrelated existing file.
No account, credentials, gated model requests, or executable checkpoint load.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "cut3r"
URL = "https://drive.usercontent.google.com/download?id=11dAgFkWHpaOHsR6iuitlB_v4NFFBrWjy&export=download&confirm=t"
PUBLIC_PAGE = "https://drive.google.com/file/d/11dAgFkWHpaOHsR6iuitlB_v4NFFBrWjy/view"
SIZE = 2994205002
CHUNK = 8 * 1024 * 1024
WORKERS = 32
LAST_MODIFIED = "Fri, 07 Feb 2025 20:32:21 GMT"
TARGET = DEST / "cut3r_224_linear_4.pth"


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(2**20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, obj):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def emit(**values):
    print(json.dumps({"utc": now(), **values}), flush=True)


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    manifest_path = DEST / "download_manifest.json"
    with (DEST / ".download.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if TARGET.exists():
            if not manifest_path.exists():
                raise RuntimeError("Existing checkpoint has no local manifest; refusing to overwrite.")
            previous = json.loads(manifest_path.read_text())
            if TARGET.stat().st_size != SIZE or sha(TARGET) != previous.get("sha256"):
                raise RuntimeError("Existing checkpoint does not match its manifest; refusing to overwrite.")
            emit(event="already_verified", path=str(TARGET))
            return

        chunks = DEST / "chunks"
        chunks.mkdir(exist_ok=True)
        disk = shutil.disk_usage(DEST)
        if disk.free < 2 * SIZE + 1024**3:
            raise RuntimeError("Insufficient free space for checkpoint, chunks, and 1 GiB reserve.")
        state_path = DEST / "download_state.json"
        previous_state = json.loads(state_path.read_text()) if state_path.exists() else {}
        for key, expected in (("source_url",URL), ("expected_size",SIZE), ("chunk_bytes",CHUNK)):
            if key in previous_state and previous_state[key] != expected:
                raise RuntimeError(f"Resume identity mismatch for {key}")
        with urllib.request.urlopen(urllib.request.Request(URL,method="HEAD"),timeout=45) as response:
            if int(response.headers.get("Content-Length",0)) != SIZE or response.headers.get("Last-Modified") != LAST_MODIFIED:
                raise RuntimeError("Remote checkpoint identity changed; refusing mixed-version resume")
        metadata = {
            "started_utc": previous_state.get("started_utc", now()),
            "latest_attempt_started_utc": now(),
            "source_url": URL,
            "official_public_page": PUBLIC_PAGE,
            "official_repository": "https://github.com/CUT3R/CUT3R",
            "license": "CC BY-NC-SA 4.0; preserve upstream and inherited file notices",
            "license_source": "https://github.com/CUT3R/CUT3R/blob/main/LICENSE",
            "expected_size": SIZE,
            "workers": WORKERS,
            "chunk_bytes": CHUNK,
            "disk_free_before_bytes": disk.free,
            "status": "downloading",
            "checkpoint_loaded": False,
            "http_last_modified": LAST_MODIFIED,
            "publisher_sha256_available": False,
            "http_validator_pin_note": "Early chunks predate this pin; their hashes remain recorded and the final ZIP CRC is checked.",
        }
        write_json(state_path, metadata)
        with (DEST / "download_attempts.jsonl").open("a") as stream:
            stream.write(json.dumps({"utc": now(), "workers":WORKERS, "event":"start_or_resume"})+"\n")
        emit(event="start_or_resume", workers=WORKERS, expected_bytes=SIZE)

        def download_chunk(index):
            start = index * CHUNK
            end = min(SIZE, (index + 1) * CHUNK) - 1
            required = end - start + 1
            complete = chunks / f"{index:04}.part"
            partial = chunks / f"{index:04}.incomplete"
            record = chunks / f"{index:04}.json"
            if complete.exists() and complete.stat().st_size == required and record.exists():
                old = json.loads(record.read_text())
                if old.get("sha256") == sha(complete):
                    return {**old, "reused": True}
                raise RuntimeError(f"Chunk {index} hash mismatch; refusing silent replacement")
            for attempt in range(8):
                try:
                    offset = partial.stat().st_size if partial.exists() else 0
                    if offset > required:
                        raise RuntimeError(f"Oversized partial chunk {index}")
                    if offset < required:
                        request_start = start + offset
                        req = urllib.request.Request(URL, headers={
                            "Range": f"bytes={request_start}-{end}",
                            "Accept-Encoding": "identity",
                            "If-Range": LAST_MODIFIED,
                        })
                        with urllib.request.urlopen(req, timeout=60) as response:
                            expected_range = f"bytes {request_start}-{end}/{SIZE}"
                            if response.status != 206 or response.headers.get("Content-Range") != expected_range:
                                raise RuntimeError(f"Unexpected range response {response.status} {response.headers.get('Content-Range')}")
                            if response.headers.get("Last-Modified") != LAST_MODIFIED:
                                raise RuntimeError("Remote checkpoint modification time changed")
                            with partial.open("ab") as stream:
                                remaining = required - offset
                                while remaining:
                                    block = response.read(min(2**20, remaining))
                                    if not block:
                                        raise EOFError("Transfer ended before requested byte range completed")
                                    stream.write(block)
                                    remaining -= len(block)
                    if partial.stat().st_size != required:
                        raise RuntimeError("Incorrect partial length")
                    partial.replace(complete)
                    result = {"index": index, "bytes": required, "sha256": sha(complete), "completed_utc": now(), "reused": False, "http_validator_pinned": True}
                    write_json(record, result)
                    return result
                except Exception as error:
                    emit(event="retry", chunk=index, attempt=attempt+1, error=repr(error))
                    if attempt == 7:
                        raise
                    time.sleep(min(2**attempt, 15))

        records = []
        count = (SIZE + CHUNK - 1) // CHUNK
        try:
            with ThreadPoolExecutor(max_workers=WORKERS) as executor:
                futures = [executor.submit(download_chunk, i) for i in range(count)]
                for future in as_completed(futures):
                    records.append(future.result())
                    if len(records) % 5 == 0 or len(records) == count:
                        metadata.update(chunks_complete=len(records), total_chunks=count, updated_utc=now())
                        write_json(state_path, metadata)
                        emit(event="progress", chunks_complete=len(records), chunks_total=count, verified_chunk_bytes=sum(r["bytes"] for r in records))
            assembled = DEST / "cut3r_224_linear_4.pth.assembling"
            with assembled.open("wb") as stream:
                for i in range(count):
                    with (chunks / f"{i:04}.part").open("rb") as part:
                        shutil.copyfileobj(part, stream, length=2**20)
            if assembled.stat().st_size != SIZE:
                raise RuntimeError("Assembled checkpoint has unexpected size")
            metadata["assembled_utc"] = now()
            with zipfile.ZipFile(assembled) as archive:
                bad_member = archive.testzip()
                if bad_member is not None:
                    raise RuntimeError(f"Checkpoint ZIP CRC failed for {bad_member}")
                metadata["zip_members"] = len(archive.namelist())
                metadata["zip_crc_all_valid"] = True
            digest = sha(assembled)
            metadata.update(status="verified_download", completed_utc=now(), actual_size=assembled.stat().st_size,
                            sha256=digest, chunks=sorted(records, key=lambda r:r["index"]))
            if TARGET.exists():
                raise RuntimeError("Target appeared during download; refusing overwrite")
            assembled.replace(TARGET)
            write_json(manifest_path, metadata)
            write_json(state_path, {k:v for k,v in metadata.items() if k != "chunks"})
            emit(event="completed", bytes=SIZE, sha256=metadata["sha256"], path=str(TARGET))
        except Exception as error:
            metadata.update(status="incomplete", last_error=repr(error), failed_utc=now())
            write_json(state_path, metadata)
            raise


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    main()
