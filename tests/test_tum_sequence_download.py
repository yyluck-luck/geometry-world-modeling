"""Local-only adversarial downloader tests. No official data requests or image decoding."""
import gzip
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import io
import json
from pathlib import Path
import random
import socketserver
import subprocess
import sys
import tarfile
import tempfile
import threading
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/download_tum_sequence.py"
spec = importlib.util.spec_from_file_location("tum_sequence_downloader", SCRIPT)
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)
SEQUENCE = "rgbd_dataset_local_test"
ETAG = '"local-pinned-identity"'


def archive_bytes(members=None):
    payload = io.BytesIO()
    with tarfile.open(fileobj=payload, mode="w") as tar:
        if members is None:
            root = tarfile.TarInfo(SEQUENCE)
            root.type = tarfile.DIRTYPE
            tar.addfile(root)
            content = random.Random(137).randbytes(95000)
            info = tarfile.TarInfo(SEQUENCE + "/rgb.txt")
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
            info = tarfile.TarInfo(SEQUENCE + "/depth.txt")
            info.size = 10
            tar.addfile(info, io.BytesIO(b"local data"))
        else:
            for name, kind, content in members:
                info = tarfile.TarInfo(name)
                info.type = kind
                info.size = len(content) if kind == tarfile.REGTYPE else 0
                if kind in (tarfile.SYMTYPE, tarfile.LNKTYPE):
                    info.linkname = "../../outside"
                tar.addfile(info, io.BytesIO(content) if info.isfile() else None)
    return gzip.compress(payload.getvalue(), mtime=0)


class LocalHTTP:
    def __init__(self, payload, mode="ok"):
        self.payload, self.mode, self.gets, self.heads = payload, mode, 0, 0
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_HEAD(self):
                owner.heads += 1
                self.send_response(200)
                self.send_header("Content-Length", str(len(owner.payload)))
                self.send_header("ETag", '"changed"' if owner.mode == "head_changed" else ETAG)
                self.end_headers()

            def do_GET(self):
                owner.gets += 1
                if self.headers.get("If-Match") != ETAG:
                    self.send_error(412)
                    return
                if owner.mode == "transient" and owner.gets == 1:
                    self.send_error(503)
                    return
                start, end = map(int, self.headers["Range"].removeprefix("bytes=").split("-"))
                data = owner.payload[start:end + 1]
                self.send_response(200 if owner.mode == "status_200" else 206)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("ETag", '"changed"' if owner.mode == "get_changed" else ETAG)
                actual_start = start + 1 if owner.mode == "wrong_range" else start
                self.send_header("Content-Range", f"bytes {actual_start}-{end}/{len(owner.payload)}")
                self.end_headers()
                try:
                    self.wfile.write(data[:-1] if owner.mode == "short" else data)
                except (BrokenPipeError, ConnectionResetError):
                    pass

        class LoopbackServer(ThreadingHTTPServer):
            def server_bind(self):
                socketserver.TCPServer.server_bind(self)
                self.server_name = "localhost"
                self.server_port = self.server_address[1]

        self.server = LoopbackServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/local.tgz"

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.http = LocalHTTP(archive_bytes())

    def tearDown(self):
        self.http.close()
        self.temp.cleanup()

    def downloader(self, **kwargs):
        return d.Downloader(self.http.url, len(self.http.payload), ETAG, SEQUENCE,
                            self.root / "download", chunk_bytes=32768, workers=2,
                            retry_delay=False, **kwargs)

    def test_complete_then_verified_resume_without_get(self):
        first = self.downloader().run()
        gets = self.http.gets
        second = self.downloader().run()
        self.assertEqual(first["archive"]["sha256"], hashlib.sha256(self.http.payload).hexdigest())
        self.assertEqual(self.http.gets, gets)
        self.assertTrue(second["extraction"]["reused_verified_tree"])
        manifest = json.loads((self.root / "download/download_manifest.json").read_text())
        self.assertTrue(all(c["reused"] for c in manifest["chunks"].values()))
        self.assertEqual(manifest["progress"]["bytes_checked"], len(self.http.payload))
        self.assertEqual(manifest["status"], "complete")

    def test_same_length_corrupt_cache_is_quarantined_and_refetched(self):
        self.downloader().run()
        gets = self.http.gets
        chunk = self.root / "download/chunks/000000.bin"
        bad = bytearray(chunk.read_bytes())
        bad[12] ^= 0xFF
        chunk.write_bytes(bad)
        self.downloader().run()
        self.assertEqual(self.http.gets, gets + 1)
        preserved = list((self.root / "download/failed_cache").rglob("000000.bin"))
        self.assertEqual(len(preserved), 1)
        self.assertEqual(preserved[0].read_bytes(), bad)

    def test_invalid_ranges_and_statuses_have_finite_attempts(self):
        for mode in ("wrong_range", "status_200", "short"):
            with self.subTest(mode=mode):
                self.http.mode = mode
                dest = self.root / mode
                obj = d.Downloader(self.http.url, len(self.http.payload), ETAG, SEQUENCE, dest,
                                   chunk_bytes=d.CHUNK_BYTES, workers=1, attempts=2, retry_delay=False)
                before = self.http.gets
                with self.assertRaises(d.DownloadError):
                    obj.run()
                self.assertEqual(self.http.gets - before, 2)
                self.assertEqual(len(list(dest.rglob("chunk*.response.json"))), 2)
                self.assertFalse((dest / (SEQUENCE + ".tgz")).exists())

    def test_changed_get_etag_is_fatal_without_retry_or_assembly(self):
        self.http.mode = "get_changed"
        obj = d.Downloader(self.http.url, len(self.http.payload), ETAG, SEQUENCE,
                           self.root / "changed", workers=1, retry_delay=False)
        with self.assertRaises(d.IdentityError):
            obj.run()
        self.assertEqual(self.http.gets, 1)
        self.assertFalse((obj.output / (SEQUENCE + ".tgz")).exists())

    def test_changed_head_etag_refuses_all_cached_chunks(self):
        self.downloader().run()
        gets = self.http.gets
        self.http.mode = "head_changed"
        with self.assertRaises(d.IdentityError):
            self.downloader().run()
        self.assertEqual(self.http.gets, gets)

    def test_transient_http_error_keeps_failure_and_can_finish(self):
        self.http.mode = "transient"
        obj = d.Downloader(self.http.url, len(self.http.payload), ETAG, SEQUENCE,
                           self.root / "transient", workers=1, attempts=2, retry_delay=False)
        self.assertEqual(obj.run()["status"], "complete")
        self.assertEqual(self.http.gets, 2)
        response = list(obj.output.rglob("chunk000000_attempt1.response.json"))[0]
        self.assertEqual(json.loads(response.read_text())["status"], 503)

    def test_existing_extraction_conflict_is_not_overwritten(self):
        self.downloader().run()
        existing = self.root / "download/extracted" / SEQUENCE / "depth.txt"
        existing.write_text("preserve me")
        with self.assertRaises(d.DownloadError):
            self.downloader().run()
        self.assertEqual(existing.read_text(), "preserve me")

    def test_config_change_preserves_manifest_and_records_failure(self):
        self.downloader().run()
        before = (self.root / "download/download_manifest.json").read_bytes()
        obj = self.downloader()
        obj.config["etag"] = '"different"'
        with self.assertRaises(d.IdentityError):
            obj.run()
        self.assertEqual((self.root / "download/download_manifest.json").read_bytes(), before)
        runs = [json.loads(p.read_text()) for p in (obj.output / "runs").glob("*.json")]
        self.assertEqual(sum(x["status"] == "failed" for x in runs), 1)

    def test_subprocess_deadline_is_45_seconds_and_attempts_are_bounded(self):
        obj = self.downloader()
        obj.output.mkdir()
        with patch.object(d.subprocess, "run", side_effect=subprocess.TimeoutExpired("local-only-mock", 45)) as mocked:
            with self.assertRaises(d.DownloadError):
                obj.request("head", method="HEAD")
        self.assertEqual(mocked.call_count, 6)
        self.assertTrue(all(call.kwargs["timeout"] == 45 for call in mocked.call_args_list))
        self.assertEqual(len(list(obj.output.rglob("*.deadline.json"))), 6)

    def test_help_and_invalid_args_do_not_make_output_directory(self):
        output = self.root / "never-created"
        for extra, status in ((["--help"], 0), (["--unrecognized"], 2)):
            result = subprocess.run([sys.executable, str(SCRIPT), "--output-dir", str(output)] + extra,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, status)
            self.assertFalse(output.exists())
        self.assertEqual(self.http.heads + self.http.gets, 0)


class ArchiveSafetyTests(unittest.TestCase):
    def test_only_ordinary_single_root_unique_members_are_accepted(self):
        cases = [
            [(SEQUENCE + "/../../outside", tarfile.REGTYPE, b"x")],
            [("/" + SEQUENCE + "/file", tarfile.REGTYPE, b"x")],
            [("other_root/file", tarfile.REGTYPE, b"x")],
            [(SEQUENCE + "/link", tarfile.SYMTYPE, b"")],
            [(SEQUENCE + "/link", tarfile.LNKTYPE, b"")],
            [(SEQUENCE + "/fifo", tarfile.FIFOTYPE, b"")],
            [(SEQUENCE + "/file", tarfile.REGTYPE, b"x"), (SEQUENCE + "/file", tarfile.REGTYPE, b"y")],
            [(SEQUENCE + "/file", tarfile.REGTYPE, b"x"), (SEQUENCE + "/file/child", tarfile.REGTYPE, b"y")],
        ]
        with tempfile.TemporaryDirectory() as folder:
            for index, members in enumerate(cases):
                with self.subTest(index=index):
                    path = Path(folder) / f"case{index}.tgz"
                    path.write_bytes(archive_bytes(members))
                    with self.assertRaises(d.DownloadError):
                        d.checked_members(path, SEQUENCE)
            self.assertFalse((Path(folder).parent / "outside").exists())

    def test_full_gzip_crc_and_tar_termination_are_checked(self):
        original = archive_bytes()
        crc = bytearray(original)
        crc[-8] ^= 0xFF
        raw = gzip.decompress(original)
        first_without_ending = raw.rstrip(b"\x00")
        first_without_ending += b"\x00" * ((-len(first_without_ending)) % 512)
        candidates = [bytes(crc), original[:-5], gzip.compress(first_without_ending), gzip.compress(raw + b"garbage")]
        with tempfile.TemporaryDirectory() as folder:
            for index, payload in enumerate(candidates):
                with self.subTest(index=index):
                    path = Path(folder) / f"broken{index}.tgz"
                    path.write_bytes(payload)
                    with self.assertRaises((d.DownloadError, gzip.BadGzipFile, EOFError, tarfile.ReadError)):
                        d.checked_members(path, SEQUENCE)

    def test_extracted_tree_reuse_rejects_extra_directory_or_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            path = output / "archive.tgz"
            path.write_bytes(archive_bytes())
            checked = d.checked_members(path, SEQUENCE)
            result = d.safe_extract(path, output, SEQUENCE, checked, "test1")
            target = Path(result["root"])
            (target / "extra").mkdir()
            with self.assertRaises(d.DownloadError):
                d.safe_extract(path, output, SEQUENCE, checked, "test2")
            (target / "extra").rmdir()
            (target / "link").symlink_to(target / "rgb.txt")
            with self.assertRaises(d.DownloadError):
                d.safe_extract(path, output, SEQUENCE, checked, "test3")


if __name__ == "__main__":
    unittest.main()
