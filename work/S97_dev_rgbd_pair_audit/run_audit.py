#!/usr/bin/env python3
import hashlib,json,statistics,sys,time
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from PIL import Image
BASE=Path(__file__).resolve().parent
PROJECT=BASE.parents[1]
CASES={
 'fr1_xyz':PROJECT/'data/tum/rgbd_dataset_freiburg1_xyz',
 'fr2_desk_guard':PROJECT/'data/tum/fr2_desk_timestamp_guard/rgbd_dataset_freiburg2_desk',
}
SLOP=0.02
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(path):
 out=[]
 for line in Path(path).read_text().splitlines():
  if not line or line.startswith('#'): continue
  a=line.split(); out.append((float(a[0]),a[1]))
 return out
def nearest(t,items):
 return min(items,key=lambda z:(abs(z[0]-t),z[0],z[1]))
def main():
 start=datetime.now(timezone.utc).isoformat(); result={'status':'EXECUTED_DEVELOPMENT_ONLY','started_utc':start,'slop_seconds':SLOP,'cases':[],'formal_s91_run':False,'model_inferences':0}
 for name,root in CASES.items():
  rgb=rows(root/'rgb.txt'); dep=rows(root/'depth.txt'); gt=[]
  for line in (root/'groundtruth.txt').read_text().splitlines():
   if line and not line.startswith('#'): gt.append((float(line.split()[0]),line))
  matched=[];missing=0;gt_missing=0;used_depth={};used_gt={}
  for tr,path in rgb:
   d=nearest(tr,dep); g=nearest(tr,gt)
   if abs(d[0]-tr)>SLOP: missing+=1; continue
   if abs(g[0]-tr)>SLOP: gt_missing+=1
   used_depth[d[1]]=used_depth.get(d[1],0)+1;used_gt[g[0]]=used_gt.get(g[0],0)+1
   matched.append({'rgb_t':tr,'rgb_path':path,'depth_t':d[0],'depth_path':d[1],'rgb_depth_dt':abs(tr-d[0]),'gt_t':g[0],'rgb_gt_dt':abs(tr-g[0]),'depth_abs_path':str(root/d[1]),'rgb_abs_path':str(root/path)})
  mode_counts={};size_counts={};depth_nonzero=[];bad=[]
  for m in matched:
   try:
    with Image.open(root/m['rgb_path']) as im:
     key=(im.mode,tuple(im.size));size_counts[str(key)]=size_counts.get(str(key),0)+1
    with Image.open(root/m['depth_path']) as im:
     key=(im.mode,tuple(im.size));mode_counts[str(key)]=mode_counts.get(str(key),0)+1
     a=np.asarray(im);depth_nonzero.append(float(np.count_nonzero(a)/a.size))
   except Exception as e: bad.append({'pair':m,'error':repr(e)})
  timestamps={'rgb_rows':len(rgb),'depth_rows':len(dep),'gt_rows':len(gt)}
  result['cases'].append({'id':name,'root':str(root),'exposure_state':'DEVELOPMENT_SEEN','source_shas':{f:sha(root/f) for f in ['rgb.txt','depth.txt','groundtruth.txt']},'counts':timestamps,'matched_pairs':len(matched),'unmatched_rgb_over_slop':missing,'matched_gt_over_slop':gt_missing,'unique_depth_files_used':len(used_depth),'duplicate_depth_reuse_count':sum(v-1 for v in used_depth.values() if v>1),'unique_gt_timestamps_used':len(used_gt),'rgb_header_modes_sizes':size_counts,'depth_header_modes_sizes':mode_counts,'bad_image_reads':len(bad),'depth_nonzero_fraction_summary':{'min':min(depth_nonzero),'median':statistics.median(depth_nonzero),'max':max(depth_nonzero)} if depth_nonzero else None,'first_pair':matched[0] if matched else None,'last_pair':matched[-1] if matched else None,'bad_examples':bad[:3]})
 result['completed_utc']=datetime.now(timezone.utc).isoformat();result['status']='PASS_DEVELOPMENT_PAIR_AUDIT_NOT_HELDOUT'
 (BASE/'RESULTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':result['status'],'cases':[(c['id'],c['matched_pairs'],c['unmatched_rgb_over_slop'],c['bad_image_reads'],c['depth_header_modes_sizes']) for c in result['cases']]},ensure_ascii=False))
if __name__=='__main__':main()
