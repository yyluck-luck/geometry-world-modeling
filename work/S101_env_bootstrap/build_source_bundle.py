"""Package the complete pinned source tree, not the seven-file reading snapshot.

No dependency import, data/weights access, network, or model execution.
"""
import ast
import hashlib
import json
from pathlib import Path
import tarfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "work/S20_environment/isolated_vmem_source"
OUT = ROOT / "work/S101_env_bootstrap/source_transport_v1"
SUFFIXES = {".py", ".yaml", ".yml", ".cpp", ".cu", ".cuh", ".h", ".md", ".txt"}
EXCLUDED = {".git", "__pycache__", "weights", "checkpoints", "test_samples", "data", ".venv"}
REQUIRED = {"modeling/__init__.py", "modeling/pipeline.py", "modeling/modules/conditioner.py", "modeling/modules/autoencoder.py", "extern/CUT3R/src/dust3r/model.py", "LICENSE"}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    OUT.mkdir(exist_ok=False)
    old = json.loads((ROOT / "work/S40_declared_variant_generation/freeze_attempt_01/manifest_core.json").read_text())
    # Locate hash-valued path records without depending on a producer schema key.
    recorded = {}
    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(v, str) and len(v) == 64 and k.startswith(str(SOURCE)):
                    recorded[k] = v
                walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(old)
    entries, imports, symlinks = [], {}, []
    for p in sorted(SOURCE.rglob("*")):
        rel = p.relative_to(SOURCE)
        if set(rel.parts) & EXCLUDED:
            continue
        if p.is_symlink():
            symlinks.append(str(rel))
            continue
        if not p.is_file() or (p.suffix not in SUFFIXES and p.name not in {"LICENSE", "NOTICE", "COPYING"}):
            continue
        data = p.read_bytes()
        digest = sha(data)
        entries.append({"path": str(rel), "bytes": len(data), "sha256": digest,
                        "s40_recorded_sha256": recorded.get(str(p)),
                        "s40_matches": None if str(p) not in recorded else digest == recorded[str(p)]})
        if p.suffix == ".py":
            tree = ast.parse(data, filename=str(rel))
            for node in ast.walk(tree):
                names = [a.name for a in node.names] if isinstance(node, ast.Import) else ([node.module] if isinstance(node, ast.ImportFrom) and node.module and node.level == 0 else [])
                for name in names:
                    imports.setdefault(name.split(".")[0], set()).add(str(rel))
    paths = {e["path"] for e in entries}
    assert REQUIRED <= paths, REQUIRED - paths
    assert not symlinks, symlinks
    assert all(e["s40_matches"] is not False for e in entries), "Source differs from S40 identity"
    archive = OUT / "vmem_source_only.tar.gz"
    with tarfile.open(archive, "w:gz") as tf:
        for e in entries:
            tf.add(SOURCE / e["path"], arcname="vmem/" + e["path"], recursive=False)
    with tarfile.open(archive, "r:gz") as tf:
        assert len(tf.getmembers()) == len(entries)
        for e in entries:
            f = tf.extractfile("vmem/" + e["path"])
            assert f is not None and sha(f.read()) == e["sha256"]
    manifest = {"created_utc": datetime.now(timezone.utc).isoformat(), "source": str(SOURCE),
                "archive_sha256": sha(archive.read_bytes()), "archive_bytes": archive.stat().st_size,
                "file_count": len(entries), "s40_matched_count": sum(e["s40_matches"] is True for e in entries),
                "entries": entries, "imports": {k: sorted(v) for k, v in sorted(imports.items())},
                "data_access": False, "weight_access": False, "model_execution": False,
                "remote_uploaded": False, "project_import_execution": False}
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: manifest[k] for k in ["archive_sha256", "archive_bytes", "file_count", "s40_matched_count"]}))

if __name__ == "__main__":
    main()
