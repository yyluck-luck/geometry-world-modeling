"""Independent NumPy review of saved S83 outputs; no model or optimizer imports."""
import argparse, hashlib, io, json, math, re, time
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

HERE = Path(__file__).resolve().parent
RUNNER_SHA = "76c5a6a4a67a391e97e6ebaa7c13cc0a520092be563a10f27a8cebad3f33afc3"
CONTRACT_SHA = "0ff3a1f1c4aeaadb455ec6a3e832217978148172ae0018a5bf97b53859a7be5a"
SUPERVISION_SHA = "9ba9c706475ff5d6cfa3c9de41757a880df7287744bb4f709a5d35b89a9fd42b"
IDS = [12, 13, 18, 19]
H, W = 384, 512
# Numerical agreement only: float32 saved operators against independent float64 arithmetic.
ATOL, RTOL = 2e-5, 1e-5

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def body(a):
    return sha(a.tobytes(order="C"))

def same(a, b):
    assert np.array_equal(a, b)

def shape_type(a, shape, dtype="float32"):
    assert a.shape == tuple(shape) and str(a.dtype) == dtype, (a.shape, a.dtype, shape, dtype)
    assert np.isfinite(a).all()

def world_from_depth(depth, K, c2w):
    """Z-depth at integer image grid, optical c2w: world = R @ [x,y,z] + t."""
    yy, xx = np.indices(depth.shape, dtype=np.float64)
    z = depth.astype(np.float64)
    local = np.stack(((xx-K[0,2])*z/K[0,0], (yy-K[1,2])*z/K[1,1], z), axis=-1)
    return np.einsum("ij,hwj->hwi", c2w[:3,:3].astype(np.float64), local) + c2w[:3,3]

def summary_check(x):
    assert x["is_none"] is False and x["finite"] is True
    assert x["shape"] == [H,W] and x["dtype"] == "torch.float32"
    assert re.fullmatch(r"[0-9a-f]{64}", x["body_sha256"])
    assert 0 <= x["nonzero"] <= H*W
    assert math.isfinite(x["max_abs"]) and math.isfinite(x["l2"])
    assert x["max_abs"] >= 0 and x["l2"] >= 0

def review(receipt_sha256):
    start = time.monotonic()
    contract_raw = (HERE/"CONTRACT.json").read_bytes()
    assert sha(contract_raw) == CONTRACT_SHA
    c = json.loads(contract_raw)
    assert sha((HERE/"run_fixed_geometry.py").read_bytes()) == c["runner_sha256"] == RUNNER_SHA
    out = HERE/"execution_01"
    raw = (out/"RECEIPT.json").read_bytes()
    assert sha(raw) == receipt_sha256
    r = json.loads(raw)
    assert r["status"] == "COMPLETED_FIXED_BUDGET_DIAGNOSTIC"
    assert r["contract_sha256"] == CONTRACT_SHA and r["runner_sha256"] == RUNNER_SHA
    supervisor_raw = (HERE/"supervision_01/SUPERVISION.json").read_bytes()
    assert sha(supervisor_raw) == SUPERVISION_SHA
    sup = json.loads(supervisor_raw)
    assert sup["worker_receipt_sha256"] == receipt_sha256
    assert sup["status"] == "COMPLETE" and sup["returncode"] == 0 and not sup["actual_signals_sent"]
    assert sup["runner_sha256"] == RUNNER_SHA and sup["contract_sha256"] == CONTRACT_SHA
    assert sup["supervisor_sha256"] == c["root_supervisor"]["sha256"]
    assert sup["limits"] == dict(wall_seconds=300,rss_bytes=8*1024**3,poll_seconds=.1)
    assert sup["elapsed_seconds"] <= 300 and sup["peak_tree_rss_bytes"] <= 8*1024**3
    assert r["peak_self_rss_bytes"] <= 8*1024**3 and r["elapsed_seconds"] <= 300
    assert r["iterations_completed"] == 100 and r["initializer_calls"] == r["clean_calls"] == 1
    for k in ["model_loads","model_forwards","new_RGB_decodes","sensor_depth_reads","renders","generation_calls"]:
        assert r[k] == 0
    assert r["new_method_validated"] is False
    assert len(r["reads"]) == 6 and [x["role"] for x in r["reads"]] == [x["role"] for x in c["inputs"]]
    for read, spec in zip(r["reads"], c["inputs"]):
        assert (read["path"],read["sha256"],read["bytes"]) == (spec["path"],spec["sha256"],spec["size_bytes"])
    assert r["actual_scientific_file_open_order"] == [x["path"] for x in c["inputs"]]
    selection = r["camera_archive_selection"]
    assert selection["consumed_ids"] == IDS and selection["other_camera_rows_used_in_computation"] is False
    assert [selection["archive_ids"][i] for i in selection["selected_rows"]] == IDS
    fields = r["actual_fields"]
    assert fields["edges"] == [[0,1],[0,2],[0,3]] and fields["imshapes"] == [[H,W]]*4
    assert fields["norm_pw_scale"] is False
    flags = fields["parameter_flags"]
    trainable = {"pw_poses"} | {f"im_depthmaps.{i}" for i in range(4)}
    assert {k for k,v in flags.items() if v} == set(r["adam_parameter_names"]) == trainable
    for k in ["preset_readback","after_MST_readback","final_readback","after_clean_readback"]:
        a = r[k]
        assert a["encoded_frozen_exact"] is True
        assert 0 <= a["P_max_abs"] <= c["tolerances"]["P_absolute"]
        assert 0 <= a["K_max_abs_px"] <= c["tolerances"]["K_absolute_px"]

    expected = {c["outputs"][k] for k in ["initial_full","final_full_before_clean","final_full_after_clean","given","fixed","observations"]}
    assert len(r["artifacts"]) == 6
    assert {Path(a["path"]).name for a in r["artifacts"]} == expected
    arrays, archive_log = {}, []
    for a in r["artifacts"]:
        path = Path(a["path"])
        assert path.parent == out
        archive_raw = path.read_bytes()
        assert len(archive_raw) == a["bytes"] and sha(archive_raw) == a["sha256"]
        with np.load(io.BytesIO(archive_raw), allow_pickle=False) as z:
            assert set(z.files) == set(a["tensors"])
            values = {k:z[k].copy() for k in z.files}
        for k,v in values.items():
            meta = a["tensors"][k]
            assert list(v.shape) == meta["shape"] and str(v.dtype) == meta["dtype"]
            assert body(v) == meta["body_sha256"] and np.isfinite(v).all() and meta["finite"] is True
        arrays[path.name] = values
        archive_log.append(dict(name=path.name,bytes=len(archive_raw),sha256=a["sha256"],keys=sorted(values)))
    given = arrays["GIVEN_P_K.npz"]
    assert set(given) == {"c2w_input_float64","c2w_input_fp32","K_input_fp32","history_ids"}
    shape_type(given["c2w_input_float64"],[4,4,4],"float64")
    shape_type(given["c2w_input_fp32"],[4,4,4]); shape_type(given["K_input_fp32"],[4,3,3])
    shape_type(given["history_ids"],[4],"int64"); same(given["history_ids"],IDS)
    same(given["c2w_input_float64"].astype(np.float32),given["c2w_input_fp32"])
    same(given["K_input_fp32"],np.repeat(np.asarray(c["K_512_nominal"],dtype=np.float32)[None],4,axis=0))
    fixed = arrays["FROZEN_PARAMETERS.npz"]
    assert set(fixed) == {k for k,v in flags.items() if not v and not k.startswith("im_conf.")}
    for k,s in {"im_poses":[4,7],"im_focals":[4,1],"im_pp":[4,2],"pw_adaptors":[3,2]}.items():
        shape_type(fixed[k],s)
    obs = arrays["CONSUMED_OBSERVATIONS.npz"]
    assert set(obs) == {"pred_i","pred_j","weight_i","weight_j","edge_i","edge_j"}
    for k in ["pred_i","pred_j"]: shape_type(obs[k],[3,H*W,3])
    for k in ["weight_i","weight_j"]: shape_type(obs[k],[3,H*W])
    for k,values in [("edge_i",[0,0,0]),("edge_j",[1,2,3])]:
        shape_type(obs[k],[3],"int64"); same(obs[k],values)
    states = [arrays[x] for x in ["INITIALIZED_STATE.npz","FINAL_BEFORE_CLEAN.npz","FINAL_AFTER_CLEAN.npz"]]
    state_shapes = dict(depth=[4,H,W],log_depth=[4,H,W],confidence=[4,H,W],world_points=[4,H,W,3],
                        c2w=[4,4,4],K=[4,3,3],pw_poses=[3,8],pw_adaptors=[3,2],colors=[4,H,W,3],history_ids=[4])
    calculations = []
    for label,state in zip(["initial","final_before_clean","final_after_clean"],states):
        assert set(state) == set(state_shapes)
        for k,s in state_shapes.items(): shape_type(state[k],s,"int64" if k=="history_ids" else "float32")
        same(state["history_ids"],IDS)
        np.testing.assert_allclose(state["c2w"],given["c2w_input_fp32"],rtol=0,atol=c["tolerances"]["P_absolute"])
        np.testing.assert_allclose(state["K"],given["K_input_fp32"],rtol=0,atol=c["tolerances"]["K_absolute_px"])
        np.testing.assert_allclose(np.exp(state["log_depth"].astype(np.float64)),state["depth"],rtol=RTOL,atol=ATOL)
        assert (state["depth"]>0).all()
        np.testing.assert_allclose(state["c2w"][:,3,:],np.tile([0,0,0,1],(4,1)),rtol=0,atol=1e-6)
        errs = []
        for i in range(4):
            predicted = world_from_depth(state["depth"][i],state["K"][i],state["c2w"][i])
            np.testing.assert_allclose(predicted,state["world_points"][i],atol=ATOL,rtol=RTOL)
            errs.append(float(np.abs(predicted-state["world_points"][i]).max()))
        calculations.append(dict(state=label,history_ids=IDS,all_pixels_per_history=H*W,
            max_abs_world_reconstruction_error_by_history=errs,depth_min=float(state["depth"].min()),
            depth_max=float(state["depth"].max()),confidence_min=float(state["confidence"].min()),
            confidence_max=float(state["confidence"].max())))
    for k in ["c2w","K","pw_adaptors","colors"]:
        same(states[0][k],states[1][k]); same(states[1][k],states[2][k])
    for k in set(state_shapes)-{"confidence"}: same(states[1][k],states[2][k])
    changed_conf = states[1]["confidence"] != states[2]["confidence"]
    assert (states[2]["confidence"][changed_conf]==0).all()

    steps_raw = (out/"STEPS.jsonl").read_bytes()
    assert sha(steps_raw) == r["step_log_sha256"]
    rows = [json.loads(x) for x in steps_raw.splitlines()]
    assert len(rows) == 100 and [x["step"] for x in rows] == list(range(100))
    for n,row in enumerate(rows):
        assert row["registered_leaf_ids_unchanged"] is True and math.isfinite(row["loss_before_step"])
        assert abs(row["lr"]-(.01+(1e-6-.01)*(n/100))) <= 1e-15
        for key in ["depth_gradients","depth_deltas"]:
            assert len(row[key]) == 4
            for x in row[key]: summary_check(x)
    assert rows[0]["loss_before_step"] == r["initial_loss"]
    assert rows[-1]["loss_before_step"] == r["last_pre_step_loss"]
    assert math.isfinite(r["final_loss_after_100_updates"])
    assert len(r["total_registered_depth_deltas"]) == 4
    delta_review = []
    for i,meta in enumerate(r["total_registered_depth_deltas"]):
        summary_check(meta)
        delta = states[1]["log_depth"][i] - states[0]["log_depth"][i]
        assert body(delta)==meta["body_sha256"] and int(np.count_nonzero(delta))==meta["nonzero"]
        assert float(np.abs(delta).max())==meta["max_abs"]
        np.testing.assert_allclose(np.linalg.norm(delta.astype(np.float64)),meta["l2"],atol=1e-10,rtol=1e-10)
        delta_review.append(dict(history_id=IDS[i],nonzero=int(np.count_nonzero(delta)),max_abs=float(np.abs(delta).max())))
    return dict(status="PASS_SAVED_OUTPUT_ARITHMETIC_AND_RECORD_REVIEW",reviewed_utc=datetime.now(timezone.utc).isoformat(),
        elapsed_seconds=time.monotonic()-start,checker_sha256=sha(Path(__file__).read_bytes()),
        runner_sha256=RUNNER_SHA,contract_sha256=CONTRACT_SHA,receipt_sha256=receipt_sha256,
        supervision_sha256=sha(supervisor_raw),archives=archive_log,step_log_sha256=sha(steps_raw),
        independent_backprojection=calculations,arithmetic_tolerances=dict(atol=ATOL,rtol=RTOL,meaning="float32 numerical agreement; not geometry quality"),
        steps_reviewed=100,gradient_summaries_reviewed=400,delta_summaries_reviewed=400,
        gradient_summaries_with_nonzero=sum(x["nonzero"]>0 for row in rows for x in row["depth_gradients"]),
        delta_summaries_with_nonzero=sum(x["nonzero"]>0 for row in rows for x in row["depth_deltas"]),
        independently_recomputed_total_log_depth_deltas=delta_review,
        initial_loss_record=r["initial_loss"],final_loss_record=r["final_loss_after_100_updates"],
        clean_changed_confidence_pixels_by_history=[int(x.sum()) for x in changed_conf],
        scope="Six saved S83 archives only; NumPy all-pixel arithmetic, frozen P/K across snapshots, input identity records and100-step records. No fresh model/optimizer/RGB/sensor-depth/raw-head reads.",
        limitations=["Per-step gradients and intermediate encoded frozen values are runtime records; their full arrays were not retained for independent recomputation.",
                     "Original S82 and S69 input identities are checked through frozen contract and runtime read hashes; original archives are not reopened.",
                     "Loss values are checked as records, not independently recalculated; no convergence or physical/GT/generation quality judgment."])

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--receipt-sha256",required=True)
    args=ap.parse_args()
    result=review(args.receipt_sha256)
    with (HERE/"OUTPUT_REVIEW.json").open("x") as f:
        json.dump(result,f,indent=2,allow_nan=False);f.write("\n")
    print(json.dumps(result))

if __name__=="__main__": main()
