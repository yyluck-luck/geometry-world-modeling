#!/usr/bin/env python3
"""Freeze S15A samples using timestamp text only; never decode images."""
import argparse
from bisect import bisect_left
from decimal import Decimal
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import traceback


def now(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,msg):
    if not ok: raise ValueError(msg)
def save(p,obj): Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')


def parse_index(text, kind, inventory):
    result=[]
    for line in text.splitlines():
        line=line.strip()
        if not line or line.startswith('#'): continue
        fields=line.split()
        require(len(fields)==2,'index must contain exactly two columns')
        t=Decimal(fields[0]); p=PurePosixPath(fields[1])
        require(t.is_finite(),'nonfinite timestamp')
        require(not p.is_absolute() and '..' not in p.parts and '\\' not in fields[1] and len(p.parts)==2 and p.parts[0]==kind and p.suffix=='.png','index path/type')
        name='rgbd_bonn_static_close_far/'+str(p)
        # Preserve every timestamp row, including absent members. Never retime
        # a sample by removing a missing-depth row before nearest selection.
        require(not result or t>result[-1][0],'strict timestamp ordering')
        result.append((t,name))
    require(len(result)>=24,'at least 24 index rows')
    require(len({p for _,p in result})==len(result),'duplicate index paths')
    return result


def nearest(rows,q):
    times=[x[0] for x in rows]
    i=bisect_left(times,q)
    candidates=[j for j in (i-1,i) if 0<=j<len(rows)]
    return rows[min(candidates,key=lambda j:(abs(times[j]-q),times[j]))]


def select(rgb,depth):
    out=[]
    for i in range(24):
        desired=rgb[0][0]+Decimal('1.0')+Decimal('0.4')*i
        tr,pr=nearest(rgb,desired)
        td,pd=nearest(depth,tr)
        require(abs(tr-desired)<=Decimal('0.025'),'RGB desired-time gap')
        require(abs(td-tr)<=Decimal('0.025'),'RGB-depth timestamp gap')
        out.append(dict(index=i,role='history' if i<20 else 'future_target',desired_timestamp=str(desired),rgb_timestamp=str(tr),rgb_member=pr,depth_timestamp=str(td),depth_member=pd,rgb_sampling_gap_seconds=str(abs(tr-desired)),rgb_depth_gap_seconds=str(abs(td-tr))))
    require(len({r['rgb_member'] for r in out})==24 and len({r['depth_member'] for r in out})==24,'24 distinct RGB and depth selections')
    require(all(Decimal(a['rgb_timestamp'])<Decimal(b['rgb_timestamp']) for a,b in zip(out,out[1:])),'selected RGB ordering')
    return out


def main():
    p=argparse.ArgumentParser();p.add_argument('--metadata-receipt',required=True);p.add_argument('--metadata-receipt-sha256',required=True);p.add_argument('--inventory',required=True);p.add_argument('--inventory-sha256',required=True);p.add_argument('--protocol',required=True);p.add_argument('--protocol-sha256',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();o=Path(a.output);require(not o.exists(),'preserve previous output');o.mkdir(parents=True)
    receipt=dict(schema='s15a-sampling-receipt-v1',started_utc=now(),status='RUNNING',image_decodes=0,trajectory_rows_read=0,model_calls=0,source_sha256=sha(__file__))
    try:
        for path,h in [(a.metadata_receipt,a.metadata_receipt_sha256),(a.inventory,a.inventory_sha256),(a.protocol,a.protocol_sha256)]:require(sha(path)==h,'frozen metadata identity')
        r=json.loads(Path(a.metadata_receipt).read_text());require(r['status']=='PASS','metadata fetch success')
        rows={x['name']:x for x in r['members']};prefix='rgbd_bonn_static_close_far/'
        require(len(rows)==len(r['members']),'duplicate fetched member names')
        require(set(rows)=={prefix+'rgb.txt',prefix+'depth.txt'},'only two timestamp indices')
        inventory_rows=json.loads(Path(a.inventory).read_text())['entries']
        inventory={x['name']:x for x in inventory_rows}
        require(len(inventory)==len(inventory_rows),'duplicate inventory names')
        parsed={}
        for kind in ('rgb','depth'):
            entry=rows[prefix+kind+'.txt'];require(sha(entry['path'])==entry['sha256'],'index member identity')
            parsed[kind]=parse_index(Path(entry['path']).read_text(),kind,inventory)
        missing={k:[dict(timestamp=str(t),member=n) for t,n in v if n not in inventory] for k,v in parsed.items()}
        save(o/'metadata_missing_members.json',missing)
        selected=select(parsed['rgb'],parsed['depth'])
        save(o/'selected_candidates_before_presence_gate.json',selected)
        require(all(row[k+'_member'] in inventory for row in selected for k in ('rgb','depth')),'selected member missing; no replacement permitted')
        payload=dict(schema='s15a-fixed-samples-v1',frozen_utc=now(),source='Bonn static_close_far',protocol_path=str(Path(a.protocol).resolve()),protocol_sha256=a.protocol_sha256,metadata_receipt_sha256=a.metadata_receipt_sha256,inventory_sha256=a.inventory_sha256,selector_sha256=sha(__file__),index_rows={k:len(v) for k,v in parsed.items()},unselected_missing_members=missing,first_rgb_timestamp=str(parsed['rgb'][0][0]),samples=selected)
        save(o/'samples.json',payload)
        receipt.update(status='PASS',sample_sha256=sha(o/'samples.json'),history_count=20,future_target_count=4,metadata_files_read=2,index_rows=payload['index_rows'])
    except Exception as e:receipt.update(status='FAIL',error=repr(e),traceback=traceback.format_exc())
    receipt['ended_utc']=now();save(o/'receipt.json',receipt);print(json.dumps(receipt));return int(receipt['status']!='PASS')


if __name__=='__main__':raise SystemExit(main())
