from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, urllib.request, concurrent.futures
out=Path(__file__).parent
sources=[
('monst3r_evaluation.md','https://raw.githubusercontent.com/Junyi42/monst3r/main/data/evaluation_script.md'),
('cut3r_eval_listing.html','https://github.com/CUT3R/CUT3R/tree/main/eval'),
('monst3r_prepare_bonn.py','https://raw.githubusercontent.com/Junyi42/monst3r/main/datasets_preprocess/prepare_bonn.py'),
('cut3r_video_launch.py','https://raw.githubusercontent.com/CUT3R/CUT3R/main/eval/video_depth/launch.py'),
('cut3r_video_eval_depth.py','https://raw.githubusercontent.com/CUT3R/CUT3R/main/eval/video_depth/eval_depth.py'),
('cut3r_video_metadata.py','https://raw.githubusercontent.com/CUT3R/CUT3R/main/eval/video_depth/metadata.py')]
def now():return datetime.now(timezone.utc).isoformat()
def fetch(spec):
    name,url=spec;r={'name':name,'url':url,'start_utc':now()}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'GeometryResearch-source-audit/1.0'})
        with urllib.request.urlopen(req,timeout=20) as h:
            b=h.read(2000001)
            if len(b)>2000000:raise ValueError('Source exceeds 2 MB limit')
            r.update(status=h.status,bytes=len(b),final_url=h.url)
        (out/name).write_bytes(b);r['sha256']=hashlib.sha256(b).hexdigest();r['outcome']='SUCCESS'
    except Exception as e:r.update(outcome='FAIL',error=repr(e))
    r['end_utc']=now();return r
start=now()
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:r=list(pool.map(fetch,sources))
(out/'source_access.json').write_text(json.dumps({'start_utc':start,'end_utc':now(),'max_distinct_sources':6,'data_members_requested':0,'sources':r},indent=2)+'\n')
print(json.dumps(r,indent=2))
