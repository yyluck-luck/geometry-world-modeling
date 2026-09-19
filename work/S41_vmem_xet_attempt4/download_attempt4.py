"""One fresh, bounded official-Xet transfer after attempt3 timed out."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
import queue
import shutil
import signal
import subprocess
import sys
import threading
import time

S39 = Path(__file__).resolve().parents[1] / "S39_auth_recovery"
spec = importlib.util.spec_from_file_location("s39_download_original", S39 / "download_original.py")
helper = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(helper)

ROOT = helper.ROOT
SIZE = helper.SIZE
SHA = helper.SHA
REVISION = helper.REVISION
safe = helper.safe

HERE = Path(__file__).resolve().parent
OUT = HERE / "execution_01"
TARGET_DIR = ROOT / "data/vmem_recovery/xet_attempt4_01"
TARGET = TARGET_DIR / "vmem_weights.pth"
BUDGET = 5400
SETTINGS = {
    "HF_HUB_DISABLE_XET": "0",
    "HF_XET_HIGH_PERFORMANCE": "0",
    "HF_XET_FIXED_DOWNLOAD_CONCURRENCY": "1",
    "HF_XET_DATA_MAX_CONCURRENT_FILE_DOWNLOADS": "1",
    "HF_XET_CLIENT_RETRY_MAX_ATTEMPTS": "5",
}


class ExternalTermination(Exception):
    pass


def utc():
    return datetime.now(timezone.utc).isoformat()


def process_group_alive(pgid):
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False


def main():
    OUT.mkdir(exist_ok=False)
    receipt = {
        "started_utc": utc(),
        "status": "PRECHECK",
        "attempt": 4,
        "transport": "official huggingface_hub plus hf_xet",
        "repo": "liguang0115/vmem",
        "revision": REVISION,
        "target": str(TARGET),
        "expected_bytes": SIZE,
        "expected_sha256": SHA,
        "external_total_seconds": BUDGET,
        "settings": SETTINGS,
        "fresh_unique_output": True,
        "partial_or_cache_reuse_assumed": False,
        "no_outer_retry": True,
        "internal_retry_scope": "initial request plus at most five retries per wrapped Xet request; not a whole-file restart",
        "scientific_execution": False,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "imported_helper_sha256": hashlib.sha256((S39 / "download_original.py").read_bytes()).hexdigest(),
    }

    def save():
        temp = OUT / "receipt.tmp"
        temp.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
        temp.replace(OUT / "receipt.json")

    save()
    previous_sigterm = signal.getsignal(signal.SIGTERM)
    child = None
    reader = None
    start = None

    def handle_sigterm(signum, _frame):
        receipt["received_signal"] = signal.Signals(signum).name
        raise ExternalTermination("Wrapper received SIGTERM")

    try:
        signal.signal(signal.SIGTERM, handle_sigterm)
        receipt["sigterm_handler_installed"] = True
        attempt3_path = S39 / "vmem_low_concurrency_attempt3/receipt.json"
        attempt3 = json.loads(attempt3_path.read_text())
        expected_attempt3 = (
            attempt3.get("repo") == "liguang0115/vmem"
            and attempt3.get("revision") == REVISION
            and attempt3.get("expected_bytes") == SIZE
            and attempt3.get("expected_sha256") == SHA
        )
        if not expected_attempt3 or attempt3.get("status") != "TIMED_OUT" or attempt3.get("child_still_alive") or attempt3.get("group_still_alive"):
            raise RuntimeError("Attempt3 is not a clean terminal timeout")
        if process_group_alive(int(attempt3["process_group"])):
            raise RuntimeError("Attempt3 process group still exists")
        recovery_path = ROOT / "data/vmem_recovery/http_recovery_01/receipt.json"
        recovery = json.loads(recovery_path.read_text())
        expected_recovery = (
            recovery.get("repo") == "liguang0115/vmem"
            and recovery.get("revision") == REVISION
            and recovery.get("expected_bytes") == SIZE
            and recovery.get("expected_sha256") == SHA
            and recovery.get("received_range_bytes") == 0
            and recovery.get("canonical_target_modified") is False
            and recovery.get("source_partial_modified") is False
        )
        if not expected_recovery or recovery.get("status") != "FAILED_RETAIN_UNVERIFIED_CANDIDATE":
            raise RuntimeError("HTTP recovery is not in the expected terminal failure state")
        receipt["attempt3_receipt_sha256"] = hashlib.sha256(attempt3_path.read_bytes()).hexdigest()
        receipt["http_recovery_receipt_sha256"] = hashlib.sha256(recovery_path.read_bytes()).hexdigest()

        companion_path = S39 / "companion_download_receipt.json"
        companion = json.loads(companion_path.read_text())
        if companion.get("status") != "ALL_COMPANIONS_VERIFIED":
            raise RuntimeError("Companion components are not verified terminal")
        for asset in companion["assets"]:
            path = Path(asset["path"])
            if not path.is_file() or path.stat().st_size != asset["bytes"] or asset["actual_sha256"] != asset["sha256"]:
                raise RuntimeError("Companion receipt or current file size is inconsistent")
        receipt["companion_receipt_sha256"] = hashlib.sha256(companion_path.read_bytes()).hexdigest()

        canonical = ROOT / "data/vmem_original/vmem_weights.pth"
        if canonical.exists():
            raise RuntimeError("Canonical target unexpectedly exists; inspect it before another transfer")
        if TARGET_DIR.exists():
            raise RuntimeError("Fresh attempt4 target directory already exists")
        free_bytes = shutil.disk_usage(ROOT).free
        receipt["free_bytes_prelaunch"] = free_bytes
        if free_bytes < SIZE + 2 * 1024**3:
            raise RuntimeError("Insufficient free space for a fresh verified transfer")
        TARGET_DIR.mkdir(parents=True, exist_ok=False)

        cli = S39 / "cli-env/bin/hf"
        cli_version = subprocess.run([str(cli), "--version"], text=True, capture_output=True, check=True).stdout.strip()
        receipt["hf_cli_version"] = cli_version
        if cli_version != "1.30.0":
            raise RuntimeError("Unexpected official HF CLI version")
        xet_version = subprocess.run(
            [
                str(S39 / "cli-env/bin/python"),
                "-c",
                "import importlib.metadata as m; print(m.version('hf-xet'))",
            ],
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        receipt["hf_xet_version"] = xet_version
        if xet_version != "1.6.0":
            raise RuntimeError("Unexpected hf_xet version")

        env = os.environ.copy()
        env.update(SETTINGS)
        env.update({
            "HF_HOME": "/Users/rocket/.cache/huggingface-research-s39",
            "HF_ENDPOINT": "https://huggingface.co",
            "HF_HUB_OFFLINE": "0",
            "HF_DEBUG": "0",
            "HF_HUB_DISABLE_TELEMETRY": "1",
            "HF_HUB_DISABLE_UPDATE_CHECK": "1",
            "HTTPS_PROXY": "http://127.0.0.1:7897",
            "HTTP_PROXY": "http://127.0.0.1:7897",
        })
        command = [
            str(cli), "download", "liguang0115/vmem", "vmem_weights.pth",
            "--revision", REVISION, "--local-dir", str(TARGET_DIR), "--max-workers", "1",
        ]
        start = time.monotonic()
        receipt.update(status="RUNNING", download_started_utc=utc())
        child = subprocess.Popen(
            command,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
        receipt["child_pid"] = child.pid
        receipt["process_group"] = child.pid
        save()

        lines = queue.Queue()

        def collect():
            try:
                for line in child.stdout:
                    lines.put(safe(line))
            finally:
                lines.put(None)

        reader = threading.Thread(target=collect, daemon=True)
        reader.start()
        eof = False
        with (OUT / "download_redacted.log").open("x") as log:
            while not (eof and child.poll() is not None):
                if time.monotonic() - start >= BUDGET:
                    raise TimeoutError("External total deadline reached; no automatic restart")
                try:
                    line = lines.get(timeout=0.25)
                except queue.Empty:
                    continue
                if line is None:
                    eof = True
                    continue
                log.write(line)
                log.flush()
                print(line, end="", flush=True)

        code = child.wait()
        receipt.update(
            download_exit_code=code,
            download_finished_utc=utc(),
            download_wall_seconds=time.monotonic() - start,
            status="DOWNLOAD_FAILED",
        )
        if code != 0:
            return 1
        if not TARGET.is_file():
            raise RuntimeError("CLI exited successfully but target is absent")

        before = TARGET.stat()
        receipt["actual_bytes"] = before.st_size
        digest = hashlib.sha256()
        with TARGET.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
                if time.monotonic() - start >= BUDGET:
                    raise TimeoutError("Total deadline reached during whole-file SHA")
                digest.update(chunk)
        after = TARGET.stat()
        if time.monotonic() - start >= BUDGET:
            raise TimeoutError("Total deadline reached immediately after whole-file SHA")
        stable = (before.st_size, before.st_mtime_ns, before.st_ino, before.st_ctime_ns) == (
            after.st_size, after.st_mtime_ns, after.st_ino, after.st_ctime_ns
        )
        receipt.update(
            actual_sha256=digest.hexdigest(),
            hash_finished_utc=utc(),
            file_stable_during_hash=stable,
        )
        receipt["status"] = (
            "VERIFIED_COMPLETE_ORIGINAL_WEIGHT"
            if stable and before.st_size == SIZE and digest.hexdigest() == SHA
            else "FILE_IDENTITY_MISMATCH"
        )
        return 0 if receipt["status"] == "VERIFIED_COMPLETE_ORIGINAL_WEIGHT" else 1
    except BaseException as exc:
        receipt.update(
            status=(
                "TIMED_OUT" if isinstance(exc, TimeoutError)
                else "INTERRUPTED" if isinstance(exc, (KeyboardInterrupt, ExternalTermination))
                else "FAILED"
            ),
            error_type=type(exc).__name__,
            error=safe(str(exc)),
        )
        return 1
    finally:
        # Keep a second SIGTERM from interrupting process-group cleanup and the
        # terminal receipt after the first one has already entered this block.
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        if child is not None:
            signals = []
            for sig, wait_seconds in ((signal.SIGTERM, 5), (signal.SIGKILL, 10)):
                child.poll()
                if not process_group_alive(child.pid):
                    break
                try:
                    os.killpg(child.pid, sig)
                    signals.append(signal.Signals(sig).name)
                except ProcessLookupError:
                    break
                until = time.monotonic() + wait_seconds
                while time.monotonic() < until:
                    child.poll()
                    if not process_group_alive(child.pid):
                        break
                    time.sleep(0.1)
            receipt.update(
                cleanup_signals=signals,
                child_exit_code=child.poll(),
                child_still_alive=child.poll() is None,
                group_still_alive=process_group_alive(child.pid),
            )
        if reader is not None:
            reader.join(timeout=1)
        receipt.update(finished_utc=utc(), total_wall_seconds=time.monotonic() - start if start else 0)
        if receipt.get("group_still_alive") or receipt.get("child_still_alive"):
            receipt["status_before_cleanup_failure"] = receipt["status"]
            receipt["status"] = "CLEANUP_FAILED"
        save()
        signal.signal(signal.SIGTERM, previous_sigterm)
        print(json.dumps(receipt, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
