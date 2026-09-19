#!/usr/bin/env python3
"""Reproduce asynchronous CPU-source lifetime corruption, then test blocking staging.

This uses synthetic tensors only and does not load or evaluate a model.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np
import torch


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    if args.output.exists():p.error("Refusing to overwrite an earlier check")
    report={"started_utc":datetime.now(timezone.utc).isoformat(),
            "evidence_level":"synthetic_device_transfer_check","images_processed":0,"checkpoint_loaded":False,
            "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "torch_version":torch.__version__,"trials_per_mode":50,"modes":{}}
    for label,nonblocking in (("async_replacing_cpu_sources",True),("blocking_staging",False)):
        failures=[]
        for trial in range(50):
            views=[{"img":torch.zeros(1,3,224,224),
                    "ray_map":torch.full((1,6,224,224),torch.nan),
                    "camera_pose":torch.eye(4).unsqueeze(0),
                    "img_mask":torch.tensor([True]),"ray_mask":torch.tensor([False]),
                    "update":torch.tensor([True]),"reset":torch.tensor([False])} for _ in range(2)]
            # Copies preserve expected values without extending source storage lifetime.
            expected=[{key:value.numpy().copy() for key,value in view.items()} for view in views]
            for view in views:
                for key in list(view):view[key]=view[key].to("mps",non_blocking=nonblocking)
            torch.mps.synchronize()
            for i,view in enumerate(views):
                for key,value in view.items():
                    got=value.cpu().numpy()
                    if not np.array_equal(got,expected[i][key],equal_nan=True):
                        failures.append({"trial":trial,"view":i,"field":key,
                                         "shape":list(got.shape)})
        report["modes"][label]={"trials_with_mismatch":len({item["trial"] for item in failures}),
                                "field_mismatch_count":len(failures),"failures":failures}
    report["ok"]=report["modes"]["blocking_staging"]["field_mismatch_count"]==0
    report["completed_utc"]=datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="modes"},indent=2))
    print(json.dumps({k:{kk:vv for kk,vv in v.items() if kk!="failures"} for k,v in report["modes"].items()},indent=2))
    return 0 if report["ok"] else 1


if __name__=="__main__":raise SystemExit(main())
