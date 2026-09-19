"""One saved-data audit: independent scalar pixel loop, no author score import."""
import argparse, csv, hashlib, io, json, math, statistics, time
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
CONTRACT_SHA = "f570b7d02ec7343cb8db3f48fcc292f4ad45aac8fa4a17355e632d8b6e9cd98e"
RUNNER_SHA = "2bd6f28fb23cf4c2e4b938fbdf191ebe0f674973bd6c50609926ba28c9f20edb"
RECEIPT_SHA = "66d3441383c3de32f57f1d4fb737b2eedac6e7790dea9128932b31bbd395ca53"
N = 384 * 512

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def close(actual, expected, atol, rtol):
    if isinstance(expected, (bool,int)):
        assert actual == expected, (actual,expected)
    elif math.isnan(expected):
        assert math.isnan(actual)
    elif math.isinf(expected):
        assert actual == expected
    else:
        assert math.isclose(actual,expected,abs_tol=atol,rel_tol=rtol), (actual,expected)

def compare_tree(actual, expected, atol, rtol):
    if isinstance(expected,dict):
        assert set(actual)==set(expected)
        for k in expected: compare_tree(actual[k],expected[k],atol,rtol)
    elif isinstance(expected,(float,int,bool)):
        close(actual,expected,atol,rtol)
    else:
        assert actual==expected,(actual,expected)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--receipt-sha256",required=True)
    args=ap.parse_args();assert args.receipt_sha256==RECEIPT_SHA
    started=datetime.now(timezone.utc).isoformat();clock=time.monotonic();reads=[]
    cbytes=(HERE/"CONTRACT.json").read_bytes();assert sha(cbytes)==CONTRACT_SHA
    c=json.loads(cbytes);assert sha((HERE/"score_anchor_depth.py").read_bytes())==RUNNER_SHA
    atol,rtol=c["numeric"]["independent_scalar_atol_m"],c["numeric"]["independent_scalar_rtol"]
    assert (atol,rtol)==(1e-10,1e-12)
    out=HERE/"execution_01";rbytes=(out/"RECEIPT.json").read_bytes();assert sha(rbytes)==RECEIPT_SHA
    r=json.loads(rbytes)
    assert r["contract_sha256"]==CONTRACT_SHA and r["status"]=="COMPLETED_PENDING_INDEPENDENT_RECOMPUTE"
    assert r["rows_written"]==N and r["model_calls"]==r["optimizer_calls"]==0
    assert r["sensor_png_decode_attempts"]==r["sensor_png_decodes"]==1
    assert r["scientific_acceptance"] is False and r["new_method_validated"] is False
    assert len(r["reads"])==3 and len(r["outputs"])==3 and len(r["decoded_state_fields"])==2
    assert r["elapsed_seconds"]<=c["resources"]["wall_seconds"]
    assert r["peak_self_rss_bytes"]<=c["resources"]["rss_bytes"]
    for read,spec in zip(r["reads"],c["inputs"]):
        assert read==dict(path=spec["path"],bytes=spec["bytes"],sha256=spec["sha256"])

    def read(spec):
        raw=Path(spec["path"]).read_bytes()
        assert len(raw)==spec["bytes"] and sha(raw)==spec["sha256"]
        reads.append(dict(path=spec["path"],bytes=len(raw),sha256=sha(raw)))
        return raw

    depths=[];cameras=[]
    for index,spec in enumerate(c["inputs"][:2]):
        raw=read(spec)
        with np.load(io.BytesIO(raw),allow_pickle=False) as z:
            assert len(z.files)==len(set(z.files))
            a={k:z[k] for k in ["depth","history_ids","K","c2w"]}
        for k,v in a.items():
            meta=spec["tensors"][k]
            assert list(v.shape)==meta["shape"] and str(v.dtype)==meta["dtype"]
            assert sha(v.tobytes(order="C"))==meta["body_sha256"]
        assert a["history_ids"].tolist()==[12,13,18,19]
        history_row=a["history_ids"].tolist().index(19)
        depths.append(a["depth"][history_row].astype(np.float64))
        assert np.isfinite(a["K"]).all() and np.isfinite(a["c2w"]).all()
        assert np.max(np.abs(a["K"].astype(np.float64)-np.asarray(c["K_512_nominal"])))<=c["numeric"]["K_atol_px"]
        cameras.append((a["K"],a["c2w"]))
        logged=r["decoded_state_fields"][index]
        assert logged["path"]==spec["path"] and logged["fields_decoded"]==logged["fields_attempted"]==spec["decode_fields"]
        assert logged["depth_maps_decoded"]==4 and logged["scored_history_id"]==19
    assert all(np.array_equal(x,y) for x,y in zip(cameras[0],cameras[1]))
    raw=read(c["inputs"][2])
    assert raw[:8]==b"\x89PNG\r\n\x1a\n" and raw[12:16]==b"IHDR" and raw[24:26]==bytes([16,0])
    with Image.open(io.BytesIO(raw)) as im:
        assert im.size==(640,480) and im.format=="PNG"
        sensor=np.asarray(im).copy()
    assert sensor.dtype.kind in "iu" and sensor.min()>=0 and sensor.max()<=65535
    output_specs={Path(x["path"]).name:x for x in r["outputs"]}
    assert set(output_specs)=={"ALL_PIXELS.npz","ALL_PIXELS.csv","SUMMARY.json"}
    assert all(Path(x["path"]).parent==out for x in output_specs.values())
    with np.load(io.BytesIO(read(output_specs["ALL_PIXELS.npz"])),allow_pickle=False) as z:
        assert len(z.files)==len(set(z.files));saved={k:z[k] for k in z.files}
    csv_reader=csv.reader(io.StringIO(read(output_specs["ALL_PIXELS.csv"]).decode("utf-8")))
    reported=json.loads(read(output_specs["SUMMARY.json"]))
    columns=["index","u","v","native_u","native_v","sensor_u","sensor_v","in_domain","sensor_raw","reference_valid","reference_z_m"]
    for stage in ["initial","final"]:
        columns += [stage+s for s in ["_z_m","_nonfinite","_nonpositive","_valid","_abs_error_m","_absrel"]]
    columns += ["error_change_m"]
    assert next(csv_reader)==columns and set(saved)==set(columns)
    integer={"index","u","v","sensor_u","sensor_v","sensor_raw"}
    boolean={"in_domain","reference_valid"}|{s+t for s in ["initial","final"] for t in ["_nonfinite","_nonpositive","_valid"]}
    discrete=integer|boolean
    for k,v in saved.items():
        assert v.shape==(N,) and str(v.dtype)==("int64" if k in integer else "bool" if k in boolean else "float64")
    V=outside=missing=0;bad=[[0,0],[0,0]];errors=[[],[]];relative=[[],[]]
    counts=dict(decreased=0,unchanged=0,increased=0,unavailable=0);maxdiff=0.
    for i in range(N):
        v,u=divmod(i,512)
        # Exact integer arithmetic implements half-up nearest sampling independently.
        ix,iy=(5*u+2)//4,(5*v+2)//4
        x,y=5*u/4,5*v/4
        inside=0<=x<=639 and 0<=y<=479 and 0<=ix<640 and 0<=iy<480
        q=int(sensor[iy,ix]) if inside else -1
        valid=inside and q>0;ref=q/5000 if valid else math.nan
        outside+=not inside;missing+=inside and q==0;V+=valid
        expected=dict(index=i,u=u,v=v,native_u=x,native_v=y,sensor_u=ix,sensor_v=iy,
                      in_domain=inside,sensor_raw=q,reference_valid=valid,reference_z_m=ref)
        good=[];point_errors=[]
        for j,stage in enumerate(["initial","final"]):
            z=float(depths[j][v,u]);nf=not math.isfinite(z);np_=not nf and z<=0;ok=not(nf or np_)
            err=abs(z-ref) if valid and ok else math.nan
            rel=err/ref if valid and ok else math.nan
            expected.update({stage+"_z_m":z,stage+"_nonfinite":nf,stage+"_nonpositive":np_,
                             stage+"_valid":ok,stage+"_abs_error_m":err,stage+"_absrel":rel})
            good.append(ok);point_errors.append(err)
            if valid:
                bad[j][0]+=nf;bad[j][1]+=np_
                if ok:errors[j].append(err);relative[j].append(rel)
        change=point_errors[1]-point_errors[0] if valid and all(good) else math.nan
        expected["error_change_m"]=change
        if valid:
            label="unavailable" if not all(good) else "decreased" if change<0 else "increased" if change>0 else "unchanged"
            counts[label]+=1
        csv_row=next(csv_reader);assert len(csv_row)==len(columns)
        for k,cell in zip(columns,csv_row):
            value=saved[k][i].item();want=expected[k]
            close(value,want,atol,rtol)
            parsed=int(cell) if k in discrete else float(cell)
            close(parsed,value,0.,0.)  # .17g should round-trip the stored float exactly.
            if isinstance(want,float) and math.isfinite(want):maxdiff=max(maxdiff,abs(value-want))
    assert next(csv_reader,None) is None and outside+missing+V==N and sum(counts.values())==V
    stages={}
    for j,stage in enumerate(["initial","final"]):
        complete=V>0 and sum(bad[j])==0
        stages[stage]=dict(prediction_nonfinite_on_V=bad[j][0],prediction_nonpositive_on_V=bad[j][1],
            prediction_valid_on_V=len(errors[j]),denominator=V,
            status="COMPLETE" if complete else "NO_REFERENCE" if V==0 else "INVALID_PREDICTION",
            mae_m=math.fsum(errors[j])/V if complete else None,
            mae_extended="finite" if complete else "undefined" if V==0 else "+Infinity",
            absrel_mean=math.fsum(relative[j])/V if complete else None,
            absolute_error_median_m=statistics.median(errors[j]) if complete else None)
    complete=all(s["status"]=="COMPLETE" for s in stages.values())
    delta=stages["final"]["mae_m"]-stages["initial"]["mae_m"] if complete else None
    eps=c["numeric"]["decision_tolerance_m"]
    outcome="UNSCORABLE" if delta is None else "REFERENCE_MAE_DECREASE" if delta < -eps else "REFERENCE_MAE_INCREASE" if delta>eps else "NO_RESOLVABLE_CHANGE"
    expected_summary=dict(N=N,V=V,V_over_N=V/N,outside_domain=outside,missing_sensor_zero=missing,stages=stages,
        pixel_counts_descriptive_only=dict(denominator=V,paired_valid=V-counts["unavailable"],**counts),delta_mae_m=delta,
        decision_tolerance_m=eps,local_outcome=outcome,independent_recompute_required=True,scientific_acceptance=False,
        new_method_validated=False,proxy_receipt_context=c["proxy_receipt_context"])
    compare_tree(reported,expected_summary,atol,rtol);assert r["local_outcome"]==outcome
    result=dict(status="PASS_INDEPENDENT_ALL_PIXEL_SCALAR_RECOMPUTATION",started_utc=started,
        completed_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-clock,
        checker_sha256=sha(Path(__file__).read_bytes()),contract_sha256=CONTRACT_SHA,runner_sha256=RUNNER_SHA,
        receipt_sha256=RECEIPT_SHA,actual_reads=reads,npz_rows_checked=N,csv_rows_checked=N,columns_checked=columns,
        scalar_pixel_max_abs_difference=maxdiff,atol=atol,rtol=rtol,independent_summary=expected_summary,
        summary_mae_differences={s:reported["stages"][s]["mae_m"]-stages[s]["mae_m"] if complete else None for s in stages},
        source_sensor_decodes=1,source_depth_maps_decoded=8,scored_history_ids=[19],model_calls=0,optimizer_calls=0,
        scope="Whole fixed source archives read and depth/history_ids/K/c2w decoded; independent integer-map scalar loop. No author score import or other image/depth/model input.",
        boundary="Single exposed anchor;1.25 nominal mapping and17.126ms association unchanged. Conditional reference error, not physical truth, independent pixels, generation benefit or novelty.")
    with (HERE/"INDEPENDENT_OUTPUT_REVIEW.json").open("x") as f:
        json.dump(result,f,indent=2,allow_nan=False);f.write("\n")
    print(json.dumps(result))

if __name__=="__main__":main()
