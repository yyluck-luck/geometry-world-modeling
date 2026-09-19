#!/usr/bin/env python3
"""Prediction-only descriptive commit consistency; explicit caller hashes required.

Preparation does not execute this entry point. No GT/RGB/model/GA loaders.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "protocol.md"
OUT = HERE / "results"
PARENT = ROOT / "work/S26B_preparation/run_manifest.json"
BASE = ROOT / "results/S26B_consumer_baseline"
RUNNER = ROOT / "scripts/s26b_consumer_baseline.py"
IMPORTER = ROOT / "work/S26B_preparation/import_previous.py"
MODES = {"common_old": 4, "cut3r": 8, "ttt3r": 8, "filt3r": 8}
METHODS = ("cut3r", "ttt3r", "filt3r")
H, W = 384, 512
DEPTH_TOL = {"atol": 1e-6, "rtol": 1e-6}
POSE_TOL = {"atol": 1e-5, "rtol": 1e-6}
WORLD_TOL = {"atol": 1e-5, "rtol": 1e-5}


def utc(): return datetime.now(timezone.utc).isoformat()
def digest(data): return hashlib.sha256(data).hexdigest()
def require(ok, message):
    if not ok: raise ValueError(message)
def write(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def summary(a):
    import numpy as np
    a = np.asarray(a, dtype=np.float64)
    require(a.size > 0 and np.isfinite(a).all(), "Summary requires the complete finite domain")
    return {"count": int(a.size), "mean": float(a.mean()), "median": float(np.median(a)),
            "p95_linear": float(np.percentile(a, 95, method="linear")), "min": float(a.min()),
            "max": float(a.max()), "rmse": float(np.sqrt(np.mean(a*a)))}


def difference(a, b, tolerance):
    """b is the fixed reference; no alignment or masking."""
    import numpy as np
    d = np.asarray(a, dtype=np.float64) - np.asarray(b, dtype=np.float64)
    limit = tolerance["atol"] + tolerance["rtol"] * np.abs(np.asarray(b, dtype=np.float64))
    outside = np.abs(d) > limit
    return {"bitwise_equal": a.dtype == b.dtype and a.shape == b.shape and a.tobytes() == b.tobytes(),
            "numeric_equal": bool(np.array_equal(a, b)), "abs_difference": summary(np.abs(d)),
            "outside_tolerance_component_count": int(outside.sum()), "component_count": int(d.size),
            "within_tolerance": bool(not outside.any()), "tolerance": tolerance}, outside


def world_from_fields(depth, c2w, pp, focal):
    import numpy as np
    yy, xx = np.indices(depth.shape, dtype=np.float64)
    z = depth.astype(np.float64)
    x, y = (xx-float(pp[0])) * z / float(focal), (yy-float(pp[1])) * z / float(focal)
    # Component expression avoids calling the original optimizer/backprojection.
    return np.stack([float(c2w[k, 0])*x + float(c2w[k, 1])*y + float(c2w[k, 2])*z + float(c2w[k, 3]) for k in range(3)], axis=-1)


def vector_norm(a):
    import numpy as np
    return np.sqrt(np.sum(np.asarray(a, dtype=np.float64)**2, axis=-1))


def run(parent_sha, script_sha, protocol_sha):
    for value in (parent_sha, script_sha, protocol_sha):
        require(isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value), "Caller SHA required")
    require(not OUT.exists(), "Refuse existing diagnostic results directory")
    identities = {}
    def read(path, expected=None):
        path = Path(path); raw = path.read_bytes(); h = digest(raw)
        if expected is not None: require(h == expected, "SHA mismatch: " + str(path))
        identities[str(path)] = h
        return raw
    read(__file__, script_sha); read(PROTOCOL, protocol_sha)
    manifest = json.loads(read(PARENT, parent_sha))
    require(manifest["candidate"]["prefix_length"] == 4 and manifest["candidate"]["new_frame_indices"] == [4,5,6,7], "Parent old/new partition differs")
    frames = manifest["candidate"]["frames"]
    require(len(frames) == 8 and [f["index"] for f in frames] == list(range(8)), "Complete ordered 8-frame parent required")
    # Existing frozen source identity is evidence for producer fixed-parameter checks.
    for source in (RUNNER, IMPORTER):
        require(str(source) in manifest["identities"], "Producer source not bound in parent")
        read(source, manifest["identities"][str(source)])
    OUT.mkdir(parents=True, exist_ok=False)
    receipt = {"status":"RUNNING", "started_utc":utc(), "parent_manifest_sha256":parent_sha,
               "script_sha256":script_sha, "protocol_sha256":protocol_sha,
               "prediction_arrays_decode_attempted":False, "prediction_arrays_decoded":False,
               "decoded_modes":[], "sensor_gt_read":False, "new_models":0, "new_GA":0,
               "actual_Surfel_or_cache_instantiated":False, "description_only":True}
    write(OUT/"receipt.json", receipt)
    try:
        receipts, seals, event_records = {}, {}, {}
        for mode,n in MODES.items():
            r = json.loads(read(BASE/mode/"receipt.json")); receipts[mode]=r
            require(r["status"] == "PASS" and r["manifest_sha256"] == parent_sha and r["mode"] == mode and r["frame_count"] == n, "Producer domain/PASS: "+mode)
            seal = json.loads(read(BASE/mode/"inputs_seal.json", r["inputs_seal_sha256"])); seals[mode]=seal
            require(seal["manifest_sha256"] == parent_sha and seal["mode"] == mode and seal["frame_count"] == n and seal["sensor_depth_used"] is False, "Input seal domain: "+mode)
            archive_key = "common_old_depth_original4" if mode == "common_old" else mode
            require(seal["saved_heads"] == manifest["candidate"]["archives"][archive_key], "Parent ordered head source differs: "+mode)
            if mode == "common_old":
                require(r.get("producer_kind") == "IMPORT_VALIDATED_SAVED_ORIGINAL_GA" and r.get("validation_status") == "IMPORT_VALIDATED", "Common old import scope not disclosed")
                require("historical_observations_not_recorded" in r, "Common import historical gaps omitted")
                recovery_path = manifest["continuation"]["recovery_receipt_path"]
                recovery = json.loads(read(recovery_path, manifest["continuation"]["recovery_receipt_sha256"]))
                require(recovery["status"] == "IMPORT_VALIDATED" and recovery["passed"] is True and r["recovery_receipt_sha256"] == identities[str(Path(recovery_path))], "Common recovery binding")
                require(r["new_GA_runs"] == r["new_optimizer_steps"] == 0 and r["historical_GA_steps"] == 400, "Common old is an import, not a new GA")
                require(seal["recovery_receipt_sha256"] == r["recovery_receipt_sha256"], "Common seal recovery identity")
                require(r["outputs"]["output.npz"] == recovery["old_output_npz_sha256"] == manifest["continuation"]["common_files"]["output.npz"]["sha256"], "Common saved output differs from frozen import")
            else:
                require(r["iterations"] == r["adam_steps"] == 400 and r["clean_calls"] == 1, "Incomplete original GA: "+mode)
                flags = r["observer"]["parameter_flags"]
                require(flags["im_poses"] is False and flags["im_focals"] is True and flags["im_pp"] is False, "Pose/focal/pp policy: "+mode)
                require([flags["im_depthmaps."+str(i)] for i in range(8)] == [False]*4+[True]*4, "Old/new depth trainability: "+mode)
                raw = read(BASE/mode/"observer_events.jsonl", r["outputs"]["observer_events.jsonl"])
                events = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
                required = {"post_MST_constraints", "post_GA_constraints", "post_clean_constraints", "GA_call_exit"}
                require(required.issubset({e["stage"] for e in events}), "Incomplete constraint events: "+mode)
                require(all(e["report"].get("parameter_flags") == flags for e in events if e["stage"] in required), "Event flags differ: "+mode)
                event_records[mode] = {"stages":[e["stage"] for e in events], "parameter_flags":flags,
                    "interpretation":"Inherits source-bound producer bitwise checks before recorded stages; this diagnostic does not reread all internal parameter snapshots."}
        for mode in METHODS:
            require(seals[mode]["control_c2w_sha256"] == seals["common_old"]["control_c2w_sha256"], "Different given camera identity")
            require(seals[mode]["compatibility_receipt_sha256"] == seals["common_old"]["compatibility_receipt_sha256"], "Different compatibility receipt identity")
            require(seals[mode]["common_old_receipt_sha256"] == identities[str(BASE/"common_old"/"receipt.json")], "Different common old producer")
            require(receipts[mode]["control_pose_prefix_tensor_sha256"] == receipts["common_old"]["control_pose_prefix_tensor_sha256"], "Different old pose tensor identity")
        buffers = {m:read(BASE/m/"output.npz", receipts[m]["outputs"]["output.npz"]) for m in MODES}
        write(OUT/"input_seal.json", {"utc":utc(), "identities":dict(identities), "all_four_producers_sealed":True, "arrays_decoded":False,
            "common_old_scope":"IMPORT_VALIDATED only; original S26 remains FAILED", "observer_records":event_records,
            "historical_observations_not_recorded":receipts["common_old"]["historical_observations_not_recorded"]})
        import numpy as np
        arrays = {}
        receipt.update(prediction_arrays_decode_attempted=True, arrays_decode_started_utc=utc())
        write(OUT/"receipt.json", receipt)
        for mode,n in MODES.items():
            shapes={"depth":(n,H,W),"point_cloud":(n,H,W,3),"conf":(n,H,W),"focal":(n,1),"pp":(n,2),"c2w":(n,4,4)}
            with np.load(io.BytesIO(buffers[mode]),allow_pickle=False) as z:
                require(len(z.files)==6 and set(z.files)==set(shapes), "Output keys: "+mode)
                arrays[mode] = {k:z[k] for k in shapes}
            receipt["decoded_modes"].append(mode)
            write(OUT/"receipt.json", receipt)
            for key,a in arrays[mode].items():
                require(a.shape==shapes[key] and a.dtype==np.float32 and np.isfinite(a).all(), "Finite FP32 schema: "+mode+"/"+key)
            require((arrays[mode]["depth"]>0).all() and (arrays[mode]["focal"]>0).all() and (arrays[mode]["conf"]>=0).all(), "Depth/focal/conf domain: "+mode)
        del buffers
        receipt.update(prediction_arrays_decoded=True, arrays_decoded_utc=utc());write(OUT/"receipt.json",receipt)
        A=arrays["common_old"]
        fixed={}
        for mode in METHODS:
            B=arrays[mode]
            d,_=difference(B["depth"][:4],A["depth"],DEPTH_TOL)
            p,_=difference(B["c2w"][:4],A["c2w"],POSE_TOL)
            fixed[mode]={"old_depth":d,"old_pose":p,"old_pp_numeric_equal":bool(np.array_equal(B["pp"][:4],A["pp"]))}
        write(OUT/"fixed_conditions.json",fixed)
        require(all(v["old_depth"]["within_tolerance"] and v["old_pose"]["within_tolerance"] and v["old_pp_numeric_equal"] for v in fixed.values()), "Fixed old conditions failed; do not interpret focal/world difference")
        # Saved worlds must obey their own depth/pose/pp/focal before decomposition.
        reconstruction={}
        for mode,n in MODES.items():
            reconstruction[mode]=[]
            for i in range(n):
                B=arrays[mode]; rebuilt=world_from_fields(B["depth"][i],B["c2w"][i],B["pp"][i],B["focal"][i,0])
                check,_=difference(rebuilt,B["point_cloud"][i],WORLD_TOL)
                reconstruction[mode].append(check)
        write(OUT/"world_reconstruction_checks.json",reconstruction)
        require(all(c["within_tolerance"] for rows in reconstruction.values() for c in rows), "Saved world fails own-field reconstruction")
        result={"scope":"Saved-prediction descriptive diagnostics, not true map commits or GT errors", "old4":{}, "new4":{}, "focal_pool_arithmetic_replay":{},
                "denominator_per_old_frame":H*W,"old_frames_each_method":[0,1,2,3],"new_frames_each_method":[4,5,6,7],
                "no_confidence_mask":True,"no_alignment":True,"no_automatic_event_or_method_selection":True}
        for mode in METHODS:
            B=arrays[mode]; pixel={}; rows=[]
            for i in range(4):
                a=world_from_fields(A["depth"][i],A["c2w"][i],A["pp"][i],A["focal"][i,0])
                b=world_from_fields(B["depth"][i],B["c2w"][i],B["pp"][i],B["focal"][i,0])
                af=world_from_fields(A["depth"][i],A["c2w"][i],A["pp"][i],B["focal"][i,0])
                actual=B["point_cloud"][i].astype(np.float64)-A["point_cloud"][i].astype(np.float64)
                focal=af-a; nonfocal=b-af
                store=(B["point_cloud"][i].astype(np.float64)-b)-(A["point_cloud"][i].astype(np.float64)-a)
                residual=actual-focal
                _,outside=difference(B["point_cloud"][i],A["point_cloud"][i],WORLD_TOL)
                values={"depth_delta":B["depth"][i].astype(np.float64)-A["depth"][i].astype(np.float64),
                    "world_delta":actual,"world_delta_norm":vector_norm(actual),"focal_only_delta":focal,"focal_only_norm":vector_norm(focal),
                    "remaining_delta":residual,"remaining_norm":vector_norm(residual),"nonfocal_field_delta":nonfocal,"stored_reconstruction_residual_delta":store,
                    "common_reconstruction_residual":A["point_cloud"][i].astype(np.float64)-a,"current_reconstruction_residual":B["point_cloud"][i].astype(np.float64)-b,
                    "world_outside_component_tolerance":outside,"world_any_component_outside_tolerance":outside.any(axis=-1)}
                for key,value in values.items():pixel.setdefault(key,[]).append(value)
                fa,fb=float(A["focal"][i,0]),float(B["focal"][i,0])
                rows.append({"frame_index":i,"all_pixels":H*W,"all_pixels_retained":True,
                    "focal_common_px":fa,"focal_current_px":fb,"focal_signed_delta_px":fb-fa,"focal_abs_relative_delta":abs(fb-fa)/fa,
                    "pp_common":A["pp"][i].tolist(),"pp_current":B["pp"][i].tolist(),"pp_delta":(B["pp"][i]-A["pp"][i]).tolist(),
                    "c2w_common":A["c2w"][i].tolist(),"c2w_current":B["c2w"][i].tolist(),"c2w_delta":(B["c2w"][i].astype(float)-A["c2w"][i]).tolist(),
                    "pose_translation_displacement_m":float(np.linalg.norm(B["c2w"][i,:3,3].astype(float)-A["c2w"][i,:3,3])),
                    "depth_signed_delta":summary(values["depth_delta"]),"depth_abs_delta":summary(np.abs(values["depth_delta"])),
                    "world_displacement_m":summary(values["world_delta_norm"]),"focal_only_displacement_m":summary(values["focal_only_norm"]),
                    "remaining_displacement_m":summary(values["remaining_norm"]),
                    "world_outside_numerical_tolerance_pixels":int(outside.any(axis=-1).sum()),
                    "world_outside_numerical_tolerance_fraction":float(outside.any(axis=-1).mean()),
                    "decomposition_closure_max_abs":float(np.abs(actual-focal-nonfocal-store).max())})
            np.savez_compressed(OUT/(mode+"_old_pixel_diagnostics.npz"),**{k:np.stack(v) for k,v in pixel.items()})
            result["old4"][mode]={"frames":rows,"all4_world_displacement_m":summary(np.stack(pixel["world_delta_norm"])),
                "all4_focal_only_displacement_m":summary(np.stack(pixel["focal_only_norm"])),"all4_remaining_displacement_m":summary(np.stack(pixel["remaining_norm"])),
                "meaning":"focal-only is an algebraic field substitution, not a rerun, intervention outcome, or proof of harm"}
            result["new4"][mode]=[{"frame_index":i,"all_pixels":H*W,"depth_m":summary(B["depth"][i]),"world_xyz_m":[summary(B["point_cloud"][i,:,:,k]) for k in range(3)],
                "focal_px":float(B["focal"][i,0]),"pp":B["pp"][i].tolist(),"c2w":B["c2w"][i].tolist(),
                "scope":"No common_old new-frame counterpart; descriptive levels only, no gain claim"} for i in range(4,8)]
            fa=A["focal"][:,0].astype(float);fb=B["focal"][:,0].astype(float)
            pool=.65*float(np.concatenate([fa,fb]).mean());current=.65*float(fb.mean())
            result["focal_pool_arithmetic_replay"][mode]={"historical_four":fa.tolist(),"current_eight":fb.tolist(),"snapshot_counts_per_frame":[2,2,2,2,1,1,1,1],
                "pool12_query_focal_px":pool,"current8_query_focal_px":current,"signed_difference_px":pool-current,"abs_relative_difference":abs(pool-current)/current,
                "historical_mean_minus_current_mean_term":.65*(float(fa.mean())-float(fb.mean()))/3,
                "actual_cache_event":False,"actual_query_or_Surfel":False,"same_pool_policy_for_all_methods":True,
                "meaning":"Hypothetical exactly two calls, full 4 then full 8; source arithmetic replay only; current8 is a comparison policy, not established truth"}
        result["limits"]=["common original4 to CUT8 changes source implementation boundary, head context 4/8, 3/7 edges, initialization and joint objective; not one-variable causality",
            "TTT/FILT use CUT common-old depth; larger displacement is not automatically worse geometry",
            "Old depth/pose fixed does not fix focal; measured field substitution is algebra, not a controlled GA intervention",
            "No actual Surfel/map commit/cache/query was instantiated in S26B",
            "No sensor GT, visibility or generated-image error is measured; no harmful-failure or innovation conclusion",
            "A common frozen-focal or cache-maintenance fix is an ordinary control, not novel merely because a discrepancy exists",
            "Imported common-old has disclosed historical missing observations; this review does not reconstruct those events"]
        write(OUT/"summary.json",result)
        for path,expected in identities.items():require(digest(Path(path).read_bytes())==expected,"Input changed during diagnostic: "+path)
        receipt.update(status="PASS",completed_utc=utc(),input_sha256_before_after=identities,all_pixels_retained=True,
            original_s26_status="FAILED_UNCHANGED",new_Surfel_or_cache_events=0,
            outputs={p.name:digest(p.read_bytes()) for p in OUT.iterdir() if p.is_file() and p.name!="receipt.json"},
            pass_meaning="Source/identity/fixed-field and descriptive arithmetic checks completed; no scientific success or harm claim")
        write(OUT/"receipt.json",receipt)
        return receipt
    except Exception as e:
        receipt.update(status="FAIL",failed_utc=utc(),error=repr(e));write(OUT/"receipt.json",receipt);raise


if __name__ == "__main__":
    for key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
        os.environ[key]="1"
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-manifest-sha256",required=True)
    parser.add_argument("--script-sha256",required=True)
    parser.add_argument("--protocol-sha256",required=True)
    args=parser.parse_args()
    print(json.dumps(run(args.parent_manifest_sha256,args.script_sha256,args.protocol_sha256),ensure_ascii=False,indent=2))
