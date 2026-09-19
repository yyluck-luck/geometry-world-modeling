#!/usr/bin/env python3
"""Generate deterministic S103 source/runtime identity manifests (no model/data access)."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path


ROOT = Path("/home/yliutz/geometry-world-modeling")
RUN = Path("/home/yliutz/gwm_source_transport_20260915/vmem")
WEIGHTS = Path("/home/yliutz/gwm_weights_20260915")
STAGE = Path("/home/yliutz/gwm_stages/S103_SCENE13_W001_20260916")
IMAGE = Path("/home/yliutz/gwm-images/nvidia-cuda-12.6.3-runtime-ubuntu22.04.sif")
OUT = ROOT / "work/S103_selector_free_baseline/window_scene13_w001_20260916"
BOUNDARY_ID = "s103-scene13-w001-vmem-base-v2-k-consistent"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ref(path: Path, *, expected_sha: str | None = None) -> dict:
    actual = sha(path)
    if expected_sha is not None and actual != expected_sha:
        raise RuntimeError(f"identity mismatch for {path}: {actual} != {expected_sha}")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": actual}


def dump(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main() -> None:
    generated = dt.datetime.now(dt.timezone.utc).isoformat()
    extensions = {".py", ".json", ".yaml", ".yml"}
    files = [p for p in RUN.rglob("*") if p.is_file() and p.suffix.lower() in extensions
             and "__pycache__" not in p.parts]
    source_path = OUT / "SOURCE_MANIFEST_v1.json"
    if source_path.exists():
        source = json.loads(source_path.read_text())
        if [ref(Path(item["path"])) for item in source["files"]] != source["files"]:
            raise RuntimeError("existing frozen source manifest no longer matches its files")
    else:
        source = {
            "schema": "gwm-s103-source-manifest-v1",
            "generated_utc": generated,
            "upstream_commit_provenance": "39291e4f272f6b4f270691d930926ab5930f942e",
            "source_root": str(RUN),
            "scope": "complete Python/JSON/YAML identity set under the frozen VMem transport tree",
            "files": [ref(p) for p in sorted(files)],
        }
        dump(source_path, source)

    known = {
        "vmem": (WEIGHTS / "vmem_weights.pth", "675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4"),
        "vae": (WEIGHTS / "diffusion_pytorch_model.safetensors", "a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815"),
        "clip": (WEIGHTS / "open_clip_model.safetensors", "0084e75319a50ad85ef45377bad5bc38f2f58824459eb690048d51c9f8863be5"),
        "cut3r": (WEIGHTS / "cut3r_512_dpt_4_64.pth", "45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103"),
        "vae_config": (WEIGHTS / "config.json", None),
    }
    checkpoint_refs = {name: ref(path, expected_sha=expected) for name, (path, expected) in known.items()}
    config = RUN / "configs/inference/inference.yaml"
    predictor = ROOT / "work/S103_selector_free_baseline/predictor_s103.py"
    scorer = ROOT / "work/S103_selector_free_baseline/scorer_s103.py"
    verifier = ROOT / "work/S103_selector_free_baseline/verify_s103_scores.py"
    runtime = {
        "schema": "gwm-s103-runtime-binding-v2",
        "generated_utc": generated,
        "execution_boundary_id": BOUNDARY_ID,
        "predictor_root": str(STAGE),
        "predictor_outside_project_required": True,
        "effective_config": ref(config),
        "effective_config_sha256": sha(config),
        "source_manifest": ref(source_path),
        "source_manifest_sha256": sha(source_path),
        "predictor_wrapper": ref(predictor),
        "predictor_wrapper_sha256": sha(predictor),
        "scorer": ref(scorer),
        "verifier": ref(verifier),
        "predictor_inputs": ref(STAGE / "predictor_inputs.json"),
        "scorer_inputs": ref(OUT / "scorer_inputs.json"),
        "checkpoint_paths": {name: str(item[0]) for name, item in known.items() if name != "vae_config"},
        "checkpoints": checkpoint_refs,
        "python": "/home/yliutz/.conda/envs/gwm-cut3r-py311-20260915/bin/python3.11",
        "container_image": ref(IMAGE, expected_sha="5a79221373914393c844cc92c32c89e722003591431f3545fc674c0739c59dd0"),
        "container_image_registry_identity": "docker://nvidia/cuda@sha256:63a18dd805367dacfb077aeced8384ab2fb569598ec5f5f5220c3f90a5c23650",
        "container_policy": ["--nv", "--containall", "--no-home", "--cleanenv"],
        "claim_boundary": "runtime identity only; no model forward and no scientific result",
    }
    runtime_path = OUT / "RUNTIME_BINDING_v2.json"
    dump(runtime_path, runtime)
    print(json.dumps({"source_manifest": ref(source_path), "runtime_binding": ref(runtime_path)}, indent=2))


if __name__ == "__main__":
    main()
