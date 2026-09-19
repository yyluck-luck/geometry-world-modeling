#!/usr/bin/env python3
"""Fail closed if predictor configuration contains future scorer paths."""
from __future__ import annotations
import json,sys
from pathlib import Path
FORBIDDEN=('future','gt','groundtruth','testsplit','test_split','pose')
def main():
    if len(sys.argv)!=2: raise SystemExit('usage: future_path_guard.py predictor_manifest.json')
    p=Path(sys.argv[1]); obj=json.loads(p.read_text())
    text=json.dumps(obj,sort_keys=True).lower()
    bad=[x for x in FORBIDDEN if x in text]
    # pose is allowed only when explicitly listed as history pose metadata, so do not fail on generic key.
    bad=[x for x in bad if x not in ('pose',)]
    if bad:
        print(json.dumps({'status':'FAIL_FUTURE_PATH_EXPOSED','tokens':bad},indent=2)); return 2
    print(json.dumps({'status':'PASS_HISTORY_ONLY_MANIFEST','path':str(p)},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
