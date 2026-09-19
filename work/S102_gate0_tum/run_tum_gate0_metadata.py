import argparse, io, json, tarfile, hashlib
from pathlib import Path
from PIL import Image
import numpy as np

def parse_index(raw):
    rows=[]
    for line in raw.decode('utf-8','replace').splitlines():
        line=line.strip()
        if not line or line.startswith('#'): continue
        a=line.split(); rows.append((float(a[0]),a[1]))
    return rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--archive',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); args=ap.parse_args()
    sha=hashlib.sha256(args.archive.read_bytes()).hexdigest()
    with tarfile.open(args.archive,'r:gz') as tf:
        names={Path(m.name).name:m for m in tf.getmembers() if m.isfile()}
        required=['rgb.txt','depth.txt','groundtruth.txt']
        missing=[x for x in required if x not in names]
        if missing: raise RuntimeError(f'missing {missing}')
        idx={k:parse_index(tf.extractfile(names[k]).read()) for k in required}
        depth_members=[m for m in tf.getmembers() if m.isfile() and '/depth/' in ('/'+m.name)]
        sample=None
        if depth_members:
            sample_member=depth_members[len(depth_members)//2]
            with Image.open(io.BytesIO(tf.extractfile(sample_member).read())) as im:
                arr=np.asarray(im); sample={'member':sample_member.name,'size':list(im.size),'mode':im.mode,'dtype':str(arr.dtype),'nonzero_median_raw':float(np.median(arr[arr>0])) if np.any(arr>0) else None}
    def stats(rows):
        ts=[r[0] for r in rows]; return {'rows':len(rows),'strictly_increasing':all(b>a for a,b in zip(ts,ts[1:])),'unique':len(set(ts))==len(ts),'start':ts[0],'end':ts[-1],'span_seconds':ts[-1]-ts[0]}
    rgb,dep,gt=idx['rgb.txt'],idx['depth.txt'],idx['groundtruth.txt']
    pairs=[]; j=0
    for t,p in rgb:
        while j+1<len(dep) and abs(dep[j+1][0]-t)<=abs(dep[j][0]-t): j+=1
        if dep and abs(dep[j][0]-t)<=0.02: pairs.append((t,p,dep[j][0],dep[j][1]))
    report={'schema':'s102-tum-fr3-gate0-metadata-v1','archive':str(args.archive),'archive_bytes':args.archive.stat().st_size,'archive_sha256':sha,'index_stats':{k:stats(v) for k,v in idx.items()},'pair_tolerance_seconds':0.02,'rgb_depth_pairs_within_tolerance':len(pairs),'rgb_depth_pair_rate':len(pairs)/len(rgb),'depth_sample':sample,'future_gt_isolation':'NOT_YET_FROZEN','independent_heldout_scene':'NOT_YET_ACQUIRED','gate0_status':'CONDITIONAL_DATA_QUALIFICATION_ONLY','notes':['Metadata and one depth sample were inspected; no model inference.','TUM timestamps and RGB-D pairing are suitable for a candidate Gate0 contract.','A separate held-out scene and frozen future-GT isolation are still required before formal baseline.']}
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__': main()
