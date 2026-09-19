#!/usr/bin/env python3
"""Synthetic allow/deny/escape + CUDA probe executed INSIDE the pinned GPU image.

No model, checkpoint, dataset, future outcome or ground truth is read. All outputs are
infrastructure evidence for the gwm-image-isolation-probe-v1 receipt.
"""
import json
import os
import platform
import socket
import subprocess
import sys

STAGE_MARKER = sys.argv[1] if len(sys.argv) > 1 else "/mnt/stage/stage_history_marker.txt"
DENY_SENTINEL = sys.argv[2] if len(sys.argv) > 2 else "/home/yliutz/gwm_isolation_deny_20260916/DO_NOT_READ.txt"
PROJECT_ROOT = "/home/yliutz/geometry-world-modeling"

out = {}
out["hostname"] = socket.gethostname()
out["python"] = sys.version.split()[0]
out["platform"] = platform.platform()
out["executable"] = sys.executable
out["cwd"] = os.getcwd()

# 1. ALLOW: the staged read-only input must be readable.
try:
    with open(STAGE_MARKER) as fh:
        out["allow_read"] = True
        out["allow_content"] = fh.read().strip()[:200]
except Exception as exc:  # noqa: BLE001
    out["allow_read"] = False
    out["allow_error"] = f"{type(exc).__name__}: {exc}"

# 2. DENY: unbound sentinel and the project tree must be invisible.
out["deny_visible"] = os.path.exists(DENY_SENTINEL)
out["project_root_visible"] = os.path.exists(PROJECT_ROOT)
out["home_visible"] = os.path.exists("/home/yliutz")
out["deny_probe"] = {"sentinel": DENY_SENTINEL, "project_root": PROJECT_ROOT, "home": "/home/yliutz"}

# 3. ESCAPE: binds must be read-only; record every bind from mountinfo.
write_probe = {}
for target in ("/mnt/stage", "/tmp", "/"):
    path = os.path.join(target, "gwm_write_probe.tmp")
    try:
        with open(path, "w") as fh:
            fh.write("probe")
        write_probe[target] = True
        try:
            os.remove(path)
        except OSError:
            pass
    except Exception as exc:  # noqa: BLE001
        write_probe[target] = f"{type(exc).__name__}: {exc}"
out["write_allowed"] = write_probe
out["write_allowed_stage"] = write_probe.get("/mnt/stage") is True

mountinfo = []
try:
    with open("/proc/self/mountinfo") as fh:
        for line in fh:
            if "gwm" in line or "/mnt/stage" in line:
                mountinfo.append(line.strip()[:400])
except Exception as exc:  # noqa: BLE001
    mountinfo.append(f"mountinfo_error: {type(exc).__name__}: {exc}")
out["mountinfo_gwm_lines"] = mountinfo

# 4. CUDA through the bound conda interpreter.
try:
    import torch

    out["torch"] = torch.__version__
    out["cuda_available"] = bool(torch.cuda.is_available())
    if torch.cuda.is_available():
        out["device_count"] = torch.cuda.device_count()
        out["device_name"] = torch.cuda.get_device_name(0)
        a = torch.randn(1024, 1024, device="cuda")
        b = torch.randn(1024, 1024, device="cuda")
        c = a @ b
        out["matmul_shape"] = list(c.shape)
        out["matmul_finite"] = bool(torch.isfinite(c).all().item())
        out["peak_allocated_bytes"] = int(torch.cuda.max_memory_allocated())
    else:
        out["device_name"] = None
except Exception as exc:  # noqa: BLE001
    out["torch"] = None
    out["cuda_available"] = False
    out["cuda_error"] = f"{type(exc).__name__}: {exc}"

# nvidia-smi, informational (the runtime image may not ship the binary).
try:
    out["nvidia_smi"] = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
        capture_output=True, text=True, timeout=30).stdout.strip()[:300]
except Exception as exc:  # noqa: BLE001
    out["nvidia_smi"] = f"{type(exc).__name__}: {exc}"

# 5. EGRESS, informational only.
try:
    import urllib.request

    req = urllib.request.Request("https://registry-1.docker.io/v2/", method="HEAD")
    with urllib.request.urlopen(req, timeout=8) as resp:
        out["egress"] = f"HTTP {resp.status}"
except Exception as exc:  # noqa: BLE001
    out["egress"] = f"{type(exc).__name__}: {exc}"

# Environment boundary, keys only.
out["env_keys_present"] = sorted(k for k in os.environ if k in ("PATH", "LD_LIBRARY_PATH", "HOME", "CUDA_VISIBLE_DEVICES", "APPTAINER_CONTAINER"))
out["home_env"] = os.environ.get("HOME")

print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
