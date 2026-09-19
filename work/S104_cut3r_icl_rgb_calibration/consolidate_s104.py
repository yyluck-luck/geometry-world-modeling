#!/usr/bin/env python3
"""Consolidate the 2026-09-15 SuperPOD work (S101-S104) into this batch directory.

Context
-------
On 2026-09-15 a full day of SuperPOD work was performed with its scripts, SLURM
job outputs and receipts left loose in the cluster home directory
(/home/yliutz).  The project's canonical ledger stopped at 2026-09-15T02:33:48
+08:00, so none of that work was recorded.  This script copies the loose files
into the project tree verbatim and records, for every copied file, its absolute
source path, byte size, SHA-256 and mtime.

Guarantees
----------
* Read-only with respect to every source path: nothing outside this batch
  directory is created, modified, moved or deleted.
* Verbatim copies (``shutil.copy2``), so bytes and mtimes are preserved.
* Idempotent: re-running overwrites the archive copies with the same bytes.
* Large or third-party assets (model weights, the dataset archive, the Vmem
  source tree) are NOT copied; they are recorded in EXTERNAL_ASSETS.json with
  absolute path, size and SHA-256 instead.
"""
from __future__ import annotations

import hashlib
import json
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

HOME = Path("/home/yliutz")
BATCH = Path(__file__).resolve().parent
ART = BATCH / "artifacts"

# --- explicit source inventories -------------------------------------------

AUTHORED_SCRIPTS = [
    HOME / "S101_gpu_probe.sh",
    HOME / "fetch_icl_nuim.sh",
    HOME / "audit_icl_nuim_archive.py",
    HOME / "gwm_source_transport_20260915" / "gpu_env_import_smoke.sh",
    HOME / "gwm_source_transport_20260915" / "remote_project_import_probe.py",
    HOME / "gwm_source_transport_20260915" / "icl_sample_decode_audit.py",
    HOME / "gwm_source_transport_20260915" / "run_icl_sample_decode_audit.sh",
    HOME / "gwm_source_transport_20260915" / "run_cut3r_rgb_only.py",
    HOME / "gwm_source_transport_20260915" / "run_s104.slurm",
    HOME / "gwm_source_transport_20260915" / "build_curope.slurm",
]

JOB_DIRS = [
    "S104_curope_build_586684",
    "S104_curope_build_586691",
    "S104_curope_build_586699",
    "S104_cut3r_calibration_586628",
    "S104_cut3r_calibration_586634",
    "S104_cut3r_calibration_586719",
]

SLURM_LOGS = [
    "slurm-584274.out", "slurm-585714.out", "slurm-585900.out",
    "slurm-585928.out", "slurm-585971.out", "slurm-586074.out",
    "slurm-586628.out", "slurm-586634.out", "slurm-586684.out",
    "slurm-586691.out", "slurm-586699.out", "slurm-586719.out",
    "gwm_s101_smoke_583967.out", "gwm_s101_smoke2_583968.out",
    "gwm_gpu_probe_584004.out", "gwm_icl_download_583984.out",
    "gwm_icl_audit_584012.out", "gwm_icl_audit2_584045.out",
]

DATA_RECEIPTS = [
    HOME / "datasets/icl_nuim/icl_nuim_download_receipt.txt",
    HOME / "datasets/icl_nuim/ICL_NUIM_ARCHIVE_AUDIT_v2.json",
    HOME / "gwm_source_transport_20260915/remote_project_import_probe_20260915.json",
    HOME / "gwm_source_transport_20260915/remote_project_import_probe_after_direct_20260915.json",
    HOME / "gwm_source_transport_20260915/gpu_env_smoke_585900.log",
    HOME / "gwm_source_transport_20260915/gpu_env_smoke_585928.log",
    HOME / "gwm_source_transport_20260915/gpu_env_smoke_585971.log",
    HOME / "gwm_source_transport_20260915/icl_gate0_sample_586074.log",
]

# Assets deliberately NOT copied.  sha256 is None where hashing is impractical
# or pointless; those rows record why.
EXTERNAL_ASSETS = [
    (HOME / "gwm_weights_20260915/cut3r_512_dpt_4_64.pth", "model weight (CUT3R 512)"),
    (HOME / "gwm_weights_20260915/vmem_weights.pth", "model weight (Vmem)"),
    (HOME / "gwm_weights_20260915/open_clip_model.safetensors", "model weight (OpenCLIP)"),
    (HOME / "gwm_weights_20260915/diffusion_pytorch_model.safetensors", "model weight (VAE)"),
    (HOME / "gwm_weights_20260915/config.json", "model config"),
    (HOME / "datasets/icl_nuim/living_room_traj0_frei_png.tar.gz", "ICL-NUIM dataset archive (official)"),
    (HOME / "gwm_source_transport_20260915/vmem_source_only.tar.gz", "frozen Vmem source snapshot used for S104"),
]


def sha256(path: Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def copy_one(src: Path, dest_dir: Path) -> dict:
    if not src.is_file():
        raise FileNotFoundError(src)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.copy2(src, dest)
    st = src.stat()
    return {
        "archived_as": str(dest.relative_to(BATCH)),
        "source_path": str(src),
        "bytes": st.st_size,
        "sha256": sha256(dest),
        "sha256_matches_source": sha256(dest) == sha256(src),
        "source_mtime_utc": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(timespec="seconds"),
    }


def main() -> int:
    rows: list[dict] = []

    for src in AUTHORED_SCRIPTS:
        rows.append(copy_one(src, ART / "scripts"))

    for name in JOB_DIRS:
        job = HOME / "gwm_source_transport_20260915" / name
        if not job.is_dir():
            raise FileNotFoundError(job)
        for f in sorted(job.rglob("*")):
            if f.is_file():
                rows.append(copy_one(f, ART / "jobs" / name))

    for name in SLURM_LOGS:
        rows.append(copy_one(HOME / name, ART / "slurm_logs"))

    for src in DATA_RECEIPTS:
        rows.append(copy_one(src, ART / "data_receipts"))

    boot = HOME / "gwm_env_bootstrap_20260915"
    for f in sorted(boot.rglob("*")):
        if f.is_file():
            rows.append(copy_one(f, ART / "env_bootstrap"))

    manifest = {
        "schema": "s104-consolidation-manifest-v1",
        "batch": "S104_cut3r_icl_rgb_calibration",
        "purpose": "Archive the loose 2026-09-15 SuperPOD artefacts into the project tree.",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generated_local": datetime.now().astimezone().isoformat(timespec="seconds"),
        "host": platform.node(),
        "policy": {
            "sources_modified": False,
            "copies_are_verbatim": True,
            "large_assets_copied": False,
            "originals_left_in_place": True,
        },
        "counts": {"files_archived": len(rows)},
        "files": rows,
    }
    (BATCH / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    ext = []
    for path, role in EXTERNAL_ASSETS:
        exists = path.exists()
        st = path.stat() if exists else None
        ext.append({
            "path": str(path),
            "role": role,
            "exists": exists,
            "bytes": st.st_size if st else None,
            "sha256": sha256(path) if exists else None,
            "source_mtime_utc": (datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(timespec="seconds")
                                 if st else None),
            "copied_into_batch": False,
            "reason_not_copied": "large binary / third-party source; referenced in place by absolute path",
        })
    vm = HOME / "gwm_source_transport_20260915/vmem"
    vm_files = sorted(p for p in vm.rglob("*") if p.is_file()) if vm.is_dir() else []
    (BATCH / "EXTERNAL_ASSETS.json").write_text(json.dumps({
        "schema": "s104-external-assets-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": ("These paths are on the SuperPOD shared NFS home and are referenced "
                 "in place.  The frozen source snapshot is vmem_source_only.tar.gz; the "
                 "extracted tree additionally contains build artefacts (.so, __pycache__)."),
        "assets": ext,
        "vmem_extracted_tree": {
            "path": str(vm),
            "file_count": len(vm_files),
            "curope_extension": str(vm / "extern/CUT3R/src/croco/models/curope/curope.cpython-311-x86_64-linux-gnu.so"),
            "sha256_files": {str(p.relative_to(vm)): sha256(p)
                             for p in vm_files if p.suffix in {".so"} or p.name == "setup.py"},
        },
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"archived {len(rows)} files into {ART}")
    print(f"external assets recorded: {len(ext)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
