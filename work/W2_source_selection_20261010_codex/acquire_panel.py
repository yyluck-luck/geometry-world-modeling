#!/usr/bin/env python3
"""Bounded ZIP metadata catalog and separately authorized member acquisition.

Catalog never reads local member headers or compressed member contents. Fetch
decompresses only the frozen members, verifies CRC/SHA, and never decodes images.
Existing paths are never overwritten. Requires the existing requests package.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import struct
import threading
import time
import traceback
from urllib.parse import urlparse
import uuid
import zlib

import requests


STEMS = "3dvision.princeton.edu/projects/2016/3DMatch/downloads/rgbd-datasets/"
HEADERS = ("Content-Length", "Content-Range", "Content-Encoding", "ETag", "Last-Modified", "Accept-Ranges", "Content-Type")
STARTS = (0, 120, 240, 360)
SOURCE_OFFSETS = (0, 15, 30, 45)
TARGET_OFFSETS = (60, 75, 90, 105)


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def publish(path, data):
    """Atomic publication without replacing an existing path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    try:
        with temporary.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def save(path, value):
    publish(path, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())


def safe_name(name):
    path = PurePosixPath(name)
    require(name and not path.is_absolute() and ".." not in path.parts and "\\" not in name and "\x00" not in name, "Unsafe archive member name")
    return path


class Access:
    """Thread-local reusable HTTP sessions, explicit ranges, bounded retries."""

    def __init__(self, receipt, max_bytes, retries=2, max_requests=None):
        require(0 <= retries <= 2, "At most two retries are allowed")
        self.receipt = receipt
        self.max_bytes = max_bytes
        self.retries = retries
        self.max_requests = max_requests
        self.local = threading.local()
        self.lock = threading.Lock()
        self.failures = {}

    def session(self):
        if not hasattr(self.local, "session"):
            session = requests.Session()
            session.max_redirects = 4
            session.headers.update({"Accept-Encoding": "identity", "User-Agent": "BoundedResearchArchive/2.0"})
            self.local.session = session
        return self.local.session

    def request(self, method, url, headers=None, start=None, length=None, identity=None):
        require(urlparse(url).scheme in ("http", "https"), "Only HTTP(S) archive URLs are accepted")
        expected_end = None if start is None else start + length - 1
        for attempt in range(self.retries + 1):
            with self.lock:
                require(self.failures.get(url, 0) < 3, "Stopped after three failures for URL")
                require(self.max_requests is None or len(self.receipt["requests"]) < self.max_requests, "Frozen request budget exhausted")
                row = dict(method=method, requested_url=url, attempt=attempt + 1, started_utc=now(), body_bytes=0)
                if start is not None:
                    row["requested_range"] = f"bytes={start}-{expected_end}"
                self.receipt["requests"].append(row)
            try:
                with self.session().request(method, url, headers=headers, timeout=30, allow_redirects=(method == "HEAD"), stream=True) as response:
                    row.update(status=response.status_code, final_url=response.url, headers={key: response.headers.get(key) for key in HEADERS})
                    row["redirects"] = [dict(status=item.status_code, url=item.url, location=item.headers.get("Location")) for item in response.history]
                    # Authentication, rate limiting and explicit denial are final.
                    require(response.status_code not in (401, 403, 429), "Access denied or rate limited; no alternate transport bypass")
                    if response.status_code >= 500:
                        raise requests.HTTPError(f"Transient server status {response.status_code}")
                    if method == "HEAD":
                        require(response.status_code == 200, f"HEAD status {response.status_code}; no body read")
                        require(response.headers.get("Content-Encoding") in (None, "identity"), "Encoded archive identity")
                        size = int(response.headers.get("Content-Length", "0"))
                        require(size >= 22, "Missing or invalid archive Content-Length")
                        result = dict(requested_url=url, url=response.url, archive_total_bytes=size, etag=response.headers.get("ETag"), last_modified=response.headers.get("Last-Modified"), headers=row["headers"])
                        require(result["etag"] or result["last_modified"], "Archive has no identity validator")
                        return result
                    require(response.status_code == 206 and response.url == url, "Range not honored or redirected; body not read")
                    require(response.headers.get("Content-Range") == f"bytes {start}-{expected_end}/{identity['archive_total_bytes']}", "Content-Range mismatch; body not read")
                    require(response.headers.get("Content-Encoding") in (None, "identity"), "Encoded range; body not read")
                    require(response.headers.get("Content-Length") == str(length), "Range length mismatch or missing; body not read")
                    require(response.headers.get("ETag") == identity["etag"] and response.headers.get("Last-Modified") == identity["last_modified"], "Archive identity changed; body not read")
                    with self.lock:
                        require(self.receipt["body_bytes"] + length <= self.max_bytes, "Total network body budget exceeded")
                        self.receipt["body_bytes"] += length  # Reserve before parallel reads.
                    data = bytearray()
                    try:
                        while len(data) < length:
                            block = response.raw.read(min(65536, length - len(data)), decode_content=False)
                            require(block, "Truncated exact range")
                            data.extend(block)
                    finally:
                        with self.lock:
                            self.receipt["body_bytes"] -= length - len(data)
                        row["body_bytes"] = len(data)
                        row["sha256"] = sha(data)
                    require(len(data) == length, "Range body length mismatch")
                    return bytes(data)
            except Exception as error:
                row["error"] = f"{type(error).__name__}: {error}"
                with self.lock:
                    self.failures[url] = self.failures.get(url, 0) + 1
                retryable = isinstance(error, requests.RequestException) and not isinstance(error, requests.exceptions.SSLError)
                if not retryable or attempt >= self.retries or self.failures[url] >= 3:
                    raise
                time.sleep(min(attempt + 1, 2))
            finally:
                row["ended_utc"] = now()

    def range(self, identity, start, length, upper):
        require(length > 0 and 0 <= start <= start + length - 1 < upper, "Range exceeds frozen bounds")
        headers = {"Range": f"bytes={start}-{start + length - 1}"}
        etag = identity.get("etag")
        if etag and not etag.startswith("W/"):
            headers.update({"If-Match": etag, "If-Range": etag})
        elif identity.get("last_modified"):
            headers.update({"If-Unmodified-Since": identity["last_modified"], "If-Range": identity["last_modified"]})
        else:
            raise ValueError("No strong ETag or Last-Modified validator")
        return self.request("GET", identity["url"], headers, start, length, identity)


def parse_eocd(raw, archive_size, maximum):
    require(len(raw) == 22, "EOCD must be exactly 22 bytes")
    signature, disk, cd_disk, count_disk, count, size, offset, comment = struct.unpack("<4s4H2IH", raw)
    require(signature == b"PK\x05\x06" and comment == 0, "No zero-comment EOCD at final 22 bytes; stop without scanning payload")
    require(disk == cd_disk == 0 and count_disk == count, "Multi-disk ZIP is unsupported")
    require(count != 65535 and size != 0xffffffff and offset != 0xffffffff, "ZIP64 is outside this metadata scope")
    require(offset + size == archive_size - 22 and 0 < size <= maximum - 22, "Central-directory bounds/budget mismatch")
    return dict(member_count=count, central_directory_bytes=size, central_directory_offset=offset)


def parse_central(raw, metadata):
    offset = 0
    entries = []
    while offset < len(raw):
        require(offset + 46 <= len(raw), "Truncated central header")
        fields = struct.unpack_from("<4s6H3I5H2I", raw, offset)
        signature, made, needed, flags, method, mt, md, crc, compressed, uncompressed, nlen, xlen, clen, disk, ia, ea, local_offset = fields
        require(signature == b"PK\x01\x02", "Invalid central signature")
        end = offset + 46 + nlen + xlen + clen
        require(end <= len(raw), "Truncated central member")
        name = raw[offset + 46:offset + 46 + nlen].decode("utf-8" if flags & 0x800 else "cp437")
        safe_name(name)
        require(disk == 0 and 0xffffffff not in (compressed, uncompressed, local_offset), "ZIP64/split member unsupported")
        require(local_offset < metadata["central_directory_offset"], "Local header outside payload region")
        entries.append(dict(name=name, compressed_bytes=compressed, uncompressed_bytes=uncompressed, compression_method=method, crc32=crc, local_header_offset=local_offset, flags=flags, external_attributes=ea, is_directory=name.endswith("/")))
        offset = end
    require(len(entries) == metadata["member_count"] and len({entry["name"] for entry in entries}) == len(entries), "Central member count mismatch or duplicate names")
    return entries


def panel(entries, scene):
    names = {entry["name"] for entry in entries}
    intrinsics = [name for name in names if name.endswith("/camera-intrinsics.txt")]
    require(len(intrinsics) == 1, "Expected one archive camera-intrinsics.txt")
    root = str(PurePosixPath(intrinsics[0]).parent)
    indexes = {}
    pattern = re.compile(re.escape(root) + r"/(seq-\d+)/frame-(\d+)\.(color\.png|depth\.png|pose\.txt)$")
    for name in sorted(names):
        match = pattern.fullmatch(name)
        if match:
            sequence, index, kind = match.groups()
            indexes.setdefault(sequence, {}).setdefault(kind, []).append(int(index))
    for kinds in indexes.values():
        for kind in kinds:
            kinds[kind] = sorted(set(kinds[kind]))
    sources = [start + delta for start in STARTS for delta in SOURCE_OFFSETS]
    all_frames = [start + delta for start in STARTS for delta in SOURCE_OFFSETS + TARGET_OFFSETS]
    selected = [intrinsics[0]]
    selected += [f"{root}/seq-01/frame-{index:06d}.color.png" for index in sources]
    selected += [f"{root}/seq-01/frame-{index:06d}.pose.txt" for index in all_frames]
    selected += [f"{root}/seq-01/frame-{index:06d}.depth.png" for index in all_frames]
    require(len(selected) == len(set(selected)) == 81, "Fixed panel selection is not 81 unique members")
    missing = [name for name in selected if name not in names]
    selection = dict(scene=scene, root=root, sequence="seq-01", starts=list(STARTS), source_offsets=list(SOURCE_OFFSETS), target_offsets=list(TARGET_OFFSETS), source_indexes=sources, all_pose_depth_indexes=all_frames, required_members=selected, missing_members=missing, fixed_panel_available=not missing, available_frame_indexes=indexes, target_rgb_selected=False)
    if not missing:
        by_name = {entry["name"]: entry for entry in entries}
        selection["selected_compressed_bytes"] = sum(by_name[name]["compressed_bytes"] for name in selected)
        selection["selected_uncompressed_bytes"] = sum(by_name[name]["uncompressed_bytes"] for name in selected)
    return selection


def catalog_scene(scene, out, args):
    out.mkdir(parents=True, exist_ok=False)
    receipt = dict(schema="w2-zip-catalog-receipt-v1", status="RUNNING", started_utc=now(), scene=scene, metadata_only=True, image_decodes=0, member_payload_bytes=0, body_bytes=0, requests=[], helper_sha256=sha(Path(__file__).read_bytes()))
    try:
        access = Access(receipt, args.max_metadata_bytes, args.retries)
        suffix = f"rgbd-scenes-v2-scene_{scene:02d}.zip"
        urls = ["https://" + STEMS + suffix, "http://" + STEMS + suffix]
        identity = None
        for url in urls:
            try:
                identity = access.request("HEAD", url)
                break
            except Exception as error:
                if any(row.get("status") in (401, 403, 429) for row in receipt["requests"]):
                    raise
                receipt.setdefault("identity_attempt_errors", []).append(dict(url=url, error=repr(error)))
        require(identity is not None, "All allowed archive URL variants failed")
        receipt["identity"] = identity
        size = identity["archive_total_bytes"]
        footer = access.range(identity, size - 22, 22, size)
        publish(out / "eocd.bin", footer)
        metadata = parse_eocd(footer, size, args.max_metadata_bytes)
        receipt["eocd"] = metadata
        raw = access.range(identity, metadata["central_directory_offset"], metadata["central_directory_bytes"], size - 22)
        publish(out / "central_directory.bin", raw)
        entries = parse_central(raw, metadata)
        selection = panel(entries, f"scene_{scene:02d}")
        inventory = dict(schema="w2-zip-catalog-v1", identity=identity, **metadata, entries=entries, panel=selection, eocd_sha256=sha(footer), central_directory_sha256=sha(raw))
        save(out / "catalog.json", inventory)
        receipt.update(status="PASS_METADATA_ONLY", catalog_sha256=sha((out / "catalog.json").read_bytes()), fixed_panel_available=selection["fixed_panel_available"], member_count=len(entries), missing_members=selection["missing_members"], selected_compressed_bytes=selection.get("selected_compressed_bytes"))
    except Exception as error:
        receipt.update(status="FAIL_PRESERVED", error=repr(error), traceback=traceback.format_exc())
    receipt["ended_utc"] = now()
    save(out / "receipt.json", receipt)
    print(json.dumps({key: receipt.get(key) for key in ("scene", "status", "fixed_panel_available", "member_count", "body_bytes", "selected_compressed_bytes", "error")}))
    return receipt


def local_header(raw, entry):
    require(len(raw) == 30, "Local header must be 30 bytes")
    sig, version, flags, method, mt, md, crc, compressed, uncompressed, nlen, xlen = struct.unpack("<4s5H3I2H", raw)
    require(sig == b"PK\x03\x04" and not flags & (1 | 64 | 8192), "Invalid/encrypted local member")
    require(method in (0, 8) and method == entry["compression_method"], "Unsupported or inconsistent compression")
    require(0 < nlen <= 1024 and xlen <= 65535, "Local name/extra bounds")
    expected = (entry["crc32"], entry["compressed_bytes"], entry["uncompressed_bytes"])
    actual = (crc, compressed, uncompressed)
    require(all(value in (0, wanted) for value, wanted in zip(actual, expected)) if flags & 8 else actual == expected, "Local/central metadata mismatch")
    return flags, nlen, xlen


def unpack(header, raw, entry, cap):
    flags, nlen, xlen = local_header(header, entry)
    require(len(raw) == nlen + xlen + entry["compressed_bytes"], "Member range size mismatch")
    require(raw[:nlen].decode("utf-8" if flags & 0x800 else "cp437") == entry["name"], "Local member name mismatch")
    safe_name(entry["name"])
    require(not entry["name"].endswith("/") and 0 <= entry["uncompressed_bytes"] <= cap, "Directory or uncompressed size outside cap")
    compressed = raw[nlen + xlen:]
    if entry["compression_method"] == 8:
        decoder = zlib.decompressobj(-15)
        data = decoder.decompress(compressed, entry["uncompressed_bytes"] + 1)
        require(decoder.eof and not decoder.unconsumed_tail and not decoder.unused_data, "Deflate budget/termination mismatch")
    else:
        data = compressed
    require(len(data) == entry["uncompressed_bytes"] and zlib.crc32(data) & 0xffffffff == entry["crc32"], "Uncompressed size or CRC32 mismatch")
    return data


def fetch(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    receipt = dict(schema="w2-range-member-receipt-v1", started_utc=now(), status="RUNNING", requests=[], members=[], body_bytes=0, image_decodes=0, model_calls=0, helper_sha256=sha(Path(__file__).read_bytes()))
    try:
        require(1 <= args.max_workers <= 4, "Workers must be 1 through 4")
        raw = Path(args.contract).read_bytes()
        require(sha(raw) == args.contract_sha256, "Frozen contract SHA mismatch")
        c = json.loads(raw)
        require(c["schema"] == "w2-range-member-contract-v1", "Contract schema mismatch")
        require(c["fetcher_sha256"] == receipt["helper_sha256"], "Frozen helper SHA mismatch")
        require(sha(Path(args.protocol).read_bytes()) == args.protocol_sha256 == c["protocol_sha256"], "Frozen protocol SHA mismatch")
        inventory_raw = Path(c["inventory_path"]).read_bytes()
        require(sha(inventory_raw) == c["inventory_sha256"], "Frozen catalog SHA mismatch")
        inventory = json.loads(inventory_raw)
        require(c["identity"] == inventory["identity"], "Contract/archive identity mismatch")
        entries = {entry["name"]: entry for entry in inventory["entries"]}
        names = c["members"]
        require(len(names) == len(set(names)) > 0 and all(name in entries for name in names), "Unknown, duplicate or empty selected member list")
        require(set(names) <= set(inventory["panel"]["required_members"]), "Member list exceeds fixed panel; target RGB prohibited")
        require(c["max_workers"] == args.max_workers, "Worker count differs from frozen contract")
        require(c["max_requests"] >= 2 * len(names) and c["max_requests"] <= 6 * len(names), "Request budget outside retry bounds")
        receipt.update(contract_sha256=args.contract_sha256, protocol_sha256=args.protocol_sha256, inventory_sha256=c["inventory_sha256"], identity=c["identity"], max_workers=args.max_workers)
        access = Access(receipt, c["max_response_bytes"], args.retries, c["max_requests"])
        lock = threading.Lock()
        stopped = threading.Event()

        def one(name):
            require(not stopped.is_set(), "Acquisition stopped after a member failure")
            entry = entries[name]
            require(entry["uncompressed_bytes"] <= c["max_member_uncompressed_bytes"], "Member exceeds declared decompression cap")
            require(not entry["flags"] & (1 | 64 | 8192), "Encrypted member prohibited")
            with lock:
                require(len(receipt["requests"]) + 2 <= c["max_requests"], "Request budget exhausted")
            header = access.range(c["identity"], entry["local_header_offset"], 30, inventory["central_directory_offset"])
            flags, nlen, xlen = local_header(header, entry)
            require(not stopped.is_set(), "Acquisition stopped after a member failure")
            body = access.range(c["identity"], entry["local_header_offset"] + 30, nlen + xlen + entry["compressed_bytes"], inventory["central_directory_offset"])
            data = unpack(header, body, entry, c["max_member_uncompressed_bytes"])
            destination = out / "members" / name
            publish(destination, data)
            item = dict(**entry, path=str(destination.resolve()), sha256=sha(data), bytes=len(data), zip_crc32_verified=True)
            with lock:
                receipt["members"].append(item)
            return item

        with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
            futures = [pool.submit(one, name) for name in names]
            try:
                for future in as_completed(futures):
                    future.result()
            except Exception:
                stopped.set()
                for future in futures:
                    future.cancel()
                raise
        require(len(receipt["requests"]) <= c["max_requests"], "Request budget exceeded")
        receipt["members"].sort(key=lambda item: item["name"])
        receipt["status"] = "PASS"
    except Exception as error:
        receipt.update(status="FAIL_PRESERVED", error=repr(error), traceback=traceback.format_exc())
    receipt["ended_utc"] = now()
    save(out / "receipt.json", receipt)
    print(json.dumps(dict(status=receipt["status"], members=len(receipt["members"]), body_bytes=receipt["body_bytes"], receipt=str(out / "receipt.json"))))
    return int(receipt["status"] != "PASS")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("catalog", help="HEAD and ZIP metadata only")
    p.add_argument("--scenes", default="1,2,3,4")
    p.add_argument("--out", required=True)
    p.add_argument("--retries", type=int, default=2)
    p.add_argument("--max-metadata-bytes", type=int, default=4 * 1024 * 1024)
    p = commands.add_parser("fetch", help="Only after explicit protocol freeze")
    p.add_argument("--contract", required=True)
    p.add_argument("--contract-sha256", required=True)
    p.add_argument("--protocol", required=True)
    p.add_argument("--protocol-sha256", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--max-workers", type=int, default=4)
    p.add_argument("--retries", type=int, default=2)
    args = parser.parse_args()
    if args.command == "fetch":
        return fetch(args)
    scenes = [int(value) for value in args.scenes.split(",")]
    require(len(set(scenes)) == len(scenes) > 0 and all(1 <= scene <= 14 for scene in scenes), "Invalid scene list")
    root = Path(args.out)
    root.mkdir(parents=True, exist_ok=False)
    results = [catalog_scene(scene, root / f"scene_{scene:02d}", args) for scene in scenes]
    return int(any(result["status"] != "PASS_METADATA_ONLY" for result in results))


if __name__ == "__main__":
    raise SystemExit(main())
