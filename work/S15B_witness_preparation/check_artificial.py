"""Small deterministic artificial checks; no real experiment files are opened."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("witness", ROOT / "scripts/s15b_witness_costs.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
OUT = Path(__file__).resolve().parent


def ident(p):
    return {"path": str(p.resolve()), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}


def main():
    start = datetime.now(timezone.utc).isoformat()
    cases = []
    gray = np.zeros((224, 224), dtype=np.uint8)
    assert module.census5(gray).max() == 0
    gray[100, 100] = 10
    assert module.census5(gray)[100, 100] == (1 << 24)-1
    gray[98, 98] = 10
    assert module.census5(gray)[100, 100] == (1 << 24)-2
    values = np.array([0, 1, 0xFFFFFF, 0x555555, 0xABCDEF], dtype=np.uint32)
    assert np.array_equal(module.popcount24(values), [int(x).bit_count() for x in values])
    cases.append("strict Census ties and independent integer bit_count agree")

    K = np.array([[100., 0, 112.], [0, 100., 112.], [0, 0, 1.]])
    pose = np.eye(4)
    z = np.full((224, 224), 2.)
    world, valid = module.source_world(z, pose, K)
    row, col, projected = module.project_rounded(world, pose, K, valid)
    assert (row[100, 100], col[100, 100]) == (100, 100)
    assert projected.sum() == 220*220
    shifted_pose = pose.copy(); shifted_pose[0, 3] = 0.5
    row, col, projected = module.project_rounded(world, shifted_pose, K, valid)
    assert col[100, 100] == 75
    half = np.array([[[20.5, 30.5, 1.], [20.4999999, 30.5, 1.], [0, 0, -1.], [np.nan, 0, 1.]]])
    hr, hc, hv = module.project_rounded(half, pose, np.eye(3), np.ones((1, 4), dtype=bool))
    assert list(hc[0, :2]) == [21, 20] and list(hr[0, :2]) == [31, 31]
    assert not hv[0, 2:].any()
    z[100, 100] = np.inf; z[101, 100] = np.nan; z[102, 100] = -1
    _, invalid = module.source_world(z, pose, K)
    assert not invalid[100:103, 100].any()
    cases.append("physical pose inverse, half-pixel rounding, borders and invalid geometry")

    shape = (4, 8, 224, 224)
    valid = np.zeros(shape, dtype=bool)
    old = np.full(shape, 255, dtype=np.uint8); new = old.copy()
    for patch_col, old_cost, new_cost in [(0, 10, 8), (1, 0, 1), (2, 2, 2)]:
        sl = (0, slice(None), slice(2, 6), slice(16*patch_col+2, 16*patch_col+6))
        valid[sl] = True; old[sl] = old_cost; new[sl] = new_cost
    rows, masks = module.aggregate_rules(valid, old, new)
    assert len(rows) == 784 and rows[0]["split_new"] and not rows[1]["split_new"]
    assert not rows[0]["matched_absolute_new"] and rows[1]["matched_absolute_new"]
    assert rows[0]["group0_count"] == rows[0]["group1_count"] == 64
    assert sum(r["matched_absolute_new"] for r in rows) == sum(r["split_new"] for r in rows) == 1
    assert not rows[2]["pool_new"] and not rows[2]["split_new"]
    assert all(r["pool_new"] == r["pool_argmin_new"] for r in rows)
    assert int(masks["split_new"].sum()) == 256
    cases.append("784 rows, integer argmin equivalence, threshold64, matched K and distinct selections")

    # Exact mean tie across unequal counts, source/patch lexicographic tie-break.
    sl = (0, slice(None), slice(2, 10), slice(18, 22))
    valid[sl] = True; old[sl] = 0; new[sl] = 8
    # Keep the third eligible patch from legitimately outranking the intended tie.
    third = (0, slice(None), slice(2, 6), slice(34, 38))
    old[third] = 20; new[third] = 20
    rows, masks = module.aggregate_rules(valid, old, new)
    assert rows[0]["new_hamming_sum"] * rows[1]["paired_observations"] == rows[1]["new_hamming_sum"] * rows[0]["paired_observations"]
    assert rows[0]["matched_absolute_new"] and not rows[1]["matched_absolute_new"]
    cases.append("rational absolute-cost ranking ties use frozen source/patch order")

    data = OUT / "artificial_inputs"
    data.mkdir(exist_ok=False)
    np.savez(data / "proposal.npz", old_self_z=np.full((4,224,224),2.), new_self_z=np.full((4,224,224),3.),
             source_c2w=np.repeat(np.eye(4)[None],4,axis=0), witness_c2w=np.repeat(np.eye(4)[None],8,axis=0),
             K=K, scale_model_per_meter=np.array(1.))
    (data / "seal.json").write_text(json.dumps({"artificial": True, "proposal": ident(data/"proposal.npz")}))
    sources=[]; witnesses=[]
    for frame_id in module.SOURCE_IDS + module.WITNESS_IDS:
        path = data / f"artificial_frame_{frame_id:02}.png"
        Image.new("RGB", (640,480), (80,80,80)).save(path)
        item=ident(path)
        if frame_id in module.SOURCE_IDS: item["source_id"]=frame_id; sources.append(item)
        else: item["frame_id"]=frame_id; witnesses.append(item)
    manifest={"schema":"s15b-witness-costs-v1", "contract":module.CONTRACT,
              "proposal_seal":ident(data/"seal.json"), "proposal_npz":ident(data/"proposal.npz"),
              "source_images":sources,"witness_images":witnesses}
    path=data/"manifest.json"; path.write_text(json.dumps(manifest,indent=2)+"\n")
    result=module.run(path,OUT/"artificial_success")
    assert result["status"]=="SUCCESS" and result["counters"]["rgb_images_decoded"]==12
    summary=json.loads((OUT/"artificial_success/summary.json").read_text())
    assert summary["paired_observations"]==4*8*220*220 and summary["old_hamming_sum"]==summary["new_hamming_sum"]==0
    assert set(summary["action_counts"].values())=={0}
    manifest["source_images"][0]["sha256"]="0"*64
    bad=data/"bad_hash_manifest.json"; bad.write_text(json.dumps(manifest,indent=2)+"\n")
    try: module.run(bad,OUT/"artificial_bad_hash")
    except ValueError: pass
    else: raise AssertionError("Bad hash was accepted")
    failed=json.loads((OUT/"artificial_bad_hash/run_metadata.json").read_text())
    assert failed["status"]=="FAIL" and failed["counters"]["proposal_arrays_decoded"]==failed["counters"]["rgb_images_decoded"]==0
    try: module.run(path,OUT/"artificial_success")
    except ValueError: pass
    else: raise AssertionError("Existing output was overwritten")
    cases.append("artificial full IO, predecode hash rejection, fail receipt and fresh output preservation")
    receipt={"schema":"s15b-witness-artificial-check-v1","started_at_utc":start,
             "completed_at_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS","cases":cases,
             "evidence_kind":"artificial software checks only; no real RGB/GT/NPZ or model access",
             "runner":ident(ROOT/"scripts/s15b_witness_costs.py"),"check_script":ident(Path(__file__))}
    (OUT/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt,indent=2))


if __name__=="__main__": main()
