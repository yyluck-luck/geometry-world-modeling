#!/usr/bin/env python3
"""Run frozen S5 RGB blocks sequentially with unchanged per-block CUT3R runner.

Input manifest paths are relative to --data. Depth files are integrity-checked
but never passed to the model subprocess. Every block gets a fresh process.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
INPUT_SHA="7ffa1467f5640bee2013a1ed1d30313be14da339ab28f7c364cfc2790f16f126"
RUNNER_SHA="efb3c8b72ada668818d4211e6d5bb4aa357a3404778cf29d849f8551160bf923"
CHECKPOINT_SHA="7a7d83e47f822e040980c8f5aff4c15aa94366d469d3ceae51fa30cc2f62327d"
COMMIT="8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf"


def now():return datetime.now(timezone.utc).isoformat()


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(2**20),b""):h.update(b)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",required=True,type=Path)
    p.add_argument("--data",required=True,type=Path)
    p.add_argument("--checkpoint",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--manifest",type=Path,default=ROOT/"data/cut3r/S5_inputs.json")
    p.add_argument("--protocol",type=Path,default=ROOT/"docs/S5_SEQUENCE_PROTOCOL.md")
    p.add_argument("--selection-manifest",type=Path,default=ROOT/"results/S3_rgbd_memory/selection_manifest.json")
    p.add_argument("--signed-rope-check",type=Path,default=ROOT/"results/CUT3R_signed_rope_compat/check.json")
    p.add_argument("--timeout-seconds",type=float,default=900)
    p.add_argument("--max-rss-gib",type=float,default=16)
    args=p.parse_args()
    if args.output.exists():p.error("Choose a new output directory; previous attempts are preserved")
    args.output.mkdir(parents=True)
    shutil.copy2(__file__,args.output/"sequence_runner_snapshot.py")
    report={"started_utc":now(),"ok":False,"phase":"preflight","blocks":[],
            "sequence_runner_sha256":sha(__file__),"runner_sha256":RUNNER_SHA,
            "precision_semantics":"Parameters, inputs and saved outputs FP32; official encoder internally casts Q/K to FP16 for RoPE and restores the original dtype",
            "resource_policy":{"timeout_seconds_per_block":args.timeout_seconds,
                               "observed_rss_limit_bytes":int(args.max_rss_gib*1024**3),
                               "rss_sample_interval_seconds":0.5,"limit_kind":"sampled soft budget"},
            "view_policy":{"reset":False,"update":True,"img_mask":True,"ray_mask":False,
                           "new_process_per_block":True,"depth_sent_to_model":False}}
    def save():
        temp=args.output/"sequence_metadata.json.tmp"
        temp.write_text(json.dumps(report,indent=2)+"\n");temp.replace(args.output/"sequence_metadata.json")
    def event(name,**extra):
        value={"utc":now(),"event":name,**extra}
        with (args.output/"events.jsonl").open("a") as f:f.write(json.dumps(value)+"\n")
        print(json.dumps(value),flush=True)
    try:
        if sha(args.manifest)!=INPUT_SHA:raise RuntimeError("Frozen S5 manifest hash changed")
        manifest=json.loads(args.manifest.read_text())
        if sha(args.protocol)!=manifest["protocol_sha256"]:raise RuntimeError("Frozen S5 protocol hash changed")
        if sha(args.selection_manifest)!=manifest["source_selection_sha256"]:raise RuntimeError("S3 selection hash changed")
        selection=json.loads(args.selection_manifest.read_text())
        if sha(ROOT/"scripts/run_cut3r_local.py")!=RUNNER_SHA:raise RuntimeError("Per-block runner changed")
        if sha(args.checkpoint)!=CHECKPOINT_SHA:raise RuntimeError("Checkpoint hash changed")
        git="/usr/bin/git" if sys.platform=="darwin" else "git"
        if subprocess.check_output([git,"-C",str(args.repo),"rev-parse","HEAD"],text=True).strip()!=COMMIT:
            raise RuntimeError("Official source commit differs")
        if subprocess.check_output([git,"-C",str(args.repo),"status","--porcelain","--untracked-files=no"],text=True).strip():
            raise RuntimeError("Official tracked source changed")
        if [b["block"] for b in manifest["blocks"]]!=[0,1,2]:raise RuntimeError("Expected exactly three ordered blocks")
        data=args.data.resolve();blocks=[]
        for block in manifest["blocks"]:
            bid=block["block"];frames=block["frames"]
            if len(frames)!=24 or [f["frame"] for f in frames]!=list(range(24)):
                raise RuntimeError("Expected 24 ordered frames in each block")
            if [f["match_index"] for f in frames]!=selection["blocks"][bid]:
                raise RuntimeError("S5 indices differ from frozen S3 blocks")
            if any(a["rgb"]["timestamp"]>=b["rgb"]["timestamp"] for a,b in zip(frames,frames[1:])):
                raise RuntimeError("RGB timestamps are not strictly ordered")
            images=[]
            for frame in frames:
                original=selection["matches"][frame["match_index"]]
                for kind in ("rgb","depth"):
                    if frame[kind]!=original[kind]:raise RuntimeError("S5 association changed")
                    relative=Path(frame[kind]["path"])
                    if relative.is_absolute() or ".." in relative.parts:raise RuntimeError("Expected safe relative data path")
                    target=(data/relative).resolve()
                    if not target.is_relative_to(data) or sha(target)!=frame[kind+"_sha256"]:
                        raise RuntimeError(f"Input integrity mismatch: {relative}")
                    if kind=="rgb":images.append(target)
            blocks.append((bid,images))
        shutil.copy2(args.manifest,args.output/"frozen_inputs.json")
        shutil.copy2(args.protocol,args.output/"frozen_protocol.md")
        report.update(manifest_sha256=INPUT_SHA,protocol_sha256=manifest["protocol_sha256"],
                      source_selection_sha256=manifest["source_selection_sha256"],
                      checkpoint_sha256=CHECKPOINT_SHA,commit=COMMIT,preflight_completed_utc=now())
        save();event("preflight_verified",rgb_images=72,depth_files_integrity_checked=72)
        for bid,images in blocks:
            out=args.output/f"block{bid}"
            command=[sys.executable,str(ROOT/"scripts/run_cut3r_local.py"),"--repo",str(args.repo.resolve()),
                     "--checkpoint",str(args.checkpoint.resolve()),"--images",*[str(x) for x in images],
                     "--device","cpu","--threads","8","--output",str(out.resolve()),
                     "--input-source",f"S5 frozen S3 block{bid}:24 chronological RGB; all reset=False/update=True; manifest {INPUT_SHA}",
                     "--signed-rope-check",str(args.signed_rope_check.resolve())]
            entry={"block":bid,"started_utc":now(),"output":f"block{bid}","log":f"block{bid}.log"}
            report["blocks"].append(entry);report["phase"]=f"block{bid}";save()
            with (args.output/f"block{bid}.log").open("x") as log:
                process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
                entry["pid"]=process.pid;save();event("block_started",block=bid,pid=process.pid,output=str(out))
                started=time.monotonic();observed_peak=0;stopped=None
                while process.poll() is None:
                    rss=subprocess.run(["ps","-o","rss=","-p",str(process.pid)],capture_output=True,text=True)
                    if rss.returncode==0 and rss.stdout.strip():
                        observed_peak=max(observed_peak,int(rss.stdout.strip())*1024)
                    if observed_peak>report["resource_policy"]["observed_rss_limit_bytes"]:
                        stopped="observed_rss_budget_exceeded"
                    elif time.monotonic()-started>args.timeout_seconds:stopped="timeout"
                    if stopped:
                        process.terminate()
                        try:process.wait(timeout=10)
                        except subprocess.TimeoutExpired:process.kill();process.wait()
                        break
                    time.sleep(0.5)
                entry.update(returncode=process.returncode,observed_peak_rss_bytes=observed_peak,completed_utc=now())
                if stopped:entry["stop_reason"]=stopped
                save()
                if process.returncode or stopped:raise RuntimeError(f"Block {bid} failed; previous output and logs retained")
            raw=json.loads((out/"run_metadata.json").read_text())
            if raw.get("peak_process_rss_bytes",0)>report["resource_policy"]["observed_rss_limit_bytes"]:
                entry["stop_reason"]="completed_process_peak_exceeded_soft_budget"
                raise RuntimeError(f"Block {bid} peak RSS exceeded the budget between samples; remaining blocks stopped")
            if raw.get("ok") is not True or raw.get("views")!=24 or raw.get("runner_sha256")!=RUNNER_SHA:
                raise RuntimeError(f"Block {bid} incomplete or unexpected runner")
            expected_images=[{"path":str(path),"sha256":sha(path)} for path in images]
            if raw["images"]!=expected_images:raise RuntimeError("Saved image identity/order differs")
            if sha(out/"predictions.npz")!=raw["predictions_sha256"]:raise RuntimeError("Saved predictions hash differs")
            entry.update(ok=True,inference_seconds=raw["inference_seconds"],predictions_sha256=raw["predictions_sha256"],
                         process_peak_rss_bytes=raw["peak_process_rss_bytes"],model_completed_utc=raw["completed_utc"])
            save();event("block_verified",**entry)
        report.update(ok=True,phase="complete",completed_utc=now());save();event("complete",blocks=3,images=72)
    except Exception:
        report.update(ok=False,phase="failed",completed_utc=now(),error=traceback.format_exc());save()
        event("failed",error=report["error"]);return 1
    return 0


if __name__=="__main__":raise SystemExit(main())
