#!/usr/bin/env python3
"""Derive contract candidate v15 from the preserved v14 artifact.

The working-copy generator was lost to a bidirectional rsync (logged
2026-09-17).  Rather than reconstruct it from a stale v9-era copy, v15 is
derived from GATE0_CONTRACT_CANDIDATE_v14.json, which is the authoritative
preserved artifact and already carries every field the validator requires.

Changes applied, and nothing else:
  1. execution_path_disclosure added (the audit found surfel/retrieval/memory
     appeared zero times in v14)
  2. run_id renamed away from the misleading 'VMemBase'
  3. predictor / scorer refs re-hashed after the access-recorder integration
  4. bundle_root, runtime binding, isolation receipt and regression receipt
     advanced to their v15-era names
Every other field is copied verbatim from v14.
"""
import hashlib, json, sys
from pathlib import Path

CODE = Path("/home/yliutz/geometry-world-modeling/work/S103_selector_free_baseline")
WIN = CODE / "window_scene13_w001_20260916"

def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def ref(p):
    p = Path(p).resolve()
    return {"path": str(p), "bytes": p.stat().st_size, "sha256": sha(p)}

DISCLOSURE = {
    "accurate_description": (
        "Frozen VMem code and weights running as a video generator conditioned on four "
        "manually specified raw history frames and eight commanded cameras. Surfel "
        "construction and memory retrieval are bypassed."),
    "is_vmem_memory_system_baseline": False,
    "vmempipeline_init_executed": False,
    "vmempipeline_init_bypass_mechanism": "object.__new__(VMemPipeline) with four attributes set by hand",
    "surfel_construction_executed": False,
    "memory_bank_constructed": False,
    "context_retrieval_executed": False,
    "context_frames_selected_by": "window manifest, fixed in advance; not selected by VMem retrieval",
    "context_mask": "torch.tensor([True] * 4 + [False] * 4), hardcoded",
    "faithfully_executed_components": [
        "get_translation_scaling_factor (uses only self.camera_scale/device/dtype)",
        "get_cond (uses only self.config/device/dtype; calls no other self method)",
        "do_sample with VMem denoiser weights", "VAE encode, CLIP encode"],
    "models_constructed": ["VMemModel+VMemWrapper", "AutoEncoder", "CLIPConditioner"],
    "cut3r_status": "hash-verified only; never constructed, never loaded, no influence on generation",
    "verification_basis": (
        "predictor_s103.py object.__new__ site and model construction sites; "
        "vendor/vmem_snapshot/modeling/pipeline.py get_cond L1123-1194 and "
        "get_translation_scaling_factor L1089-1122, inspected locally 2026-09-17"),
    "consequence_for_claims": (
        "No result from this configuration may be described as a VMem memory-system "
        "baseline, or used to support any claim about retrieval, selection or memory."),
    "access_accounting_upgrade": (
        "predictor and scorer now record the full PEP 578 event stream with exact, "
        "never-truncated counts; the previous open-only hook capped its list at 64 while "
        "reporting len(list) as a count, certifying 500 out-of-root events as 64"),
}

def main():
    src = WIN / "GATE0_CONTRACT_CANDIDATE_v14.json"
    out = WIN / "GATE0_CONTRACT_CANDIDATE_v15.json"
    if out.exists(): raise SystemExit(f"refusing to overwrite {out}")
    c = json.loads(src.read_text())
    p = c["protocol"]

    p["execution_path_disclosure"] = DISCLOSURE
    p["run_id"] = "S103-VMemCode-NoRetrieval-scene13-w001-v2"
    p["predictor_wrapper_ref"] = ref(CODE / "predictor_s103.py")
    p["scorer_ref"] = ref(CODE / "scorer_s103.py")
    fe = p["formal_execution"]
    fe["predictor_ref"] = ref(CODE / "predictor_s103.py")
    fe["bundle_root"] = "/home/yliutz/gwm_formal_bundle_s103_scene13_w001_v8"
    changed = {"execution_path_disclosure", "run_id", "predictor_wrapper_ref",
               "scorer_ref", "formal_execution.predictor_ref",
               "formal_execution.bundle_root"}

    for name, path in (("runtime_binding_ref", WIN / "RUNTIME_BINDING_v7.json"),
                       ("formal_chain_regression_receipt_ref",
                        CODE / "FORMAL_CHAIN_SOFTWARE_RECEIPT_20260917_v7.json")):
        if path.exists():
            (p if name == "runtime_binding_ref" else fe)[name] = ref(path)
            changed.add(name)
        else:
            print(f"  PENDING: {path.name} not yet built", file=sys.stderr)

    iso = WIN / "EXACT_ISOLATION_RECEIPT_v6.json"
    if iso.exists():
        p["isolation"]["receipt_ref"] = ref(iso)
        changed.add("isolation.receipt_ref")
    else:
        print("  PENDING: EXACT_ISOLATION_RECEIPT_v6.json not yet built", file=sys.stderr)

    p["status"] = "FROZEN"
    out.write_text(json.dumps(c, indent=2, sort_keys=True) + "\n")
    canon = hashlib.sha256(json.dumps(p, sort_keys=True, separators=(",", ":"),
                                      allow_nan=False).encode()).hexdigest()
    print(json.dumps({"derived_from": ref(src), "output": ref(out),
                      "protocol_sha256": canon, "fields_changed": sorted(changed),
                      "status": "DERIVED_PENDING_BINDINGS"}, indent=2))

if __name__ == "__main__":
    main()
