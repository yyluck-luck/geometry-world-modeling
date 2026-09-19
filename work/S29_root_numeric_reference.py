"""Independent root reference: saved initialization algebra, no GT or Torch.
Uses a float64 linear solve for local camera coordinates, not matrix inversion.
Prepared before S29 results; one-shot output directory, fixed pixel tolerance.
"""
import argparse,hashlib,io,json,math,time
from pathlib import Path
from datetime import datetime,timezone

def utc(): return datetime.now(timezone.utc).isoformat()
def digest(raw): return hashlib.sha256(raw).hexdigest()
def read(p): return json.loads(Path(p).read_text())
def need(x,msg):
    if not x: raise RuntimeError(msg)
def write(p,obj): Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def run(args):
    cp=Path(args.contract);need(digest(cp.read_bytes())==args.sha256,'Contract SHA')
    need(digest(Path(__file__).read_bytes())==args.self_sha256,'Reference source SHA')
    c=read(cp);need(c['status']=='FROZEN' and c['arms']==['C2t','C2a'],'Exact two controls')
    need(c['tolerance']==dict(atol=1e-5,rtol=1e-5),'Original fixed pixel tolerance')
    out=Path(__file__).parent/'S29_root_numeric_review';need(not out.exists(),'Never repeat reference');out.mkdir()
    start=utc();tick=time.monotonic();write(out/'attempt.json',dict(started_utc=start,contract_sha256=args.sha256,self_sha256=args.self_sha256))
    try:
        identities={str(cp):args.sha256,str(Path(__file__)):args.self_sha256};blobs={}
        for arm in c['arms']:
            d=Path(c['output_root'])/arm;rp=d/'receipt.json';r=read(rp)
            need(r['status']=='PASS_INITIALIZATION_EXECUTED' and r['contract_sha256']==args.sha256 and r['counts']==c['counts_per_arm'],'Complete zero-step producer')
            identities[str(rp)]=digest(rp.read_bytes());blobs[arm]={}
            for name in ['prefix_raw.npz','alignment.npz','initial_decoded.npz']:
                p=d/name;raw=p.read_bytes();need(digest(raw)==r['outputs'][name],'Sealed producer: '+str(p));identities[str(p)]=digest(raw);blobs[arm][name]=raw
        rp=Path(c['reference_B']['receipt']);r=read(rp);need(r['status']=='PASS' and r['s28_contract_sha256']==c['s28_contract_sha256'],'Historical B completed')
        identities[str(rp)]=digest(rp.read_bytes());item=c['reference_B']['files']['initial_decoded.npz'];raw=Path(item['path']).read_bytes()
        need(digest(raw)==item['sha256']==r['outputs']['initial_decoded.npz'],'Sealed historical B');identities[item['path']]=digest(raw);blobs['B']={'initial_decoded.npz':raw}
        vr=Path(c['output_root'])/'validation/receipt.json';v=read(vr);need(v['status']=='PASS_VALIDATION_EXECUTED' and v['contract_sha256']==args.sha256,'Primary comparison complete')
        identities[str(vr)]=digest(vr.read_bytes())
        write(out/'pre_decode_seal.json',dict(utc=utc(),identities=identities,arrays_decoded=False,GT_reads=0))
        import numpy as np
        need(np.__version__=='1.26.4','Expected NumPy')
        d={}
        for arm,files in blobs.items():
            d[arm]={}
            for name,raw in files.items():
                with np.load(io.BytesIO(raw),allow_pickle=False) as z:d[arm][name]={k:z[k].copy() for k in z.files}
        del blobs
        t,a=d['C2t'],d['C2a'];pt,pa=t['prefix_raw.npz'],a['prefix_raw.npz']
        need(set(pt)==set(pa) and len(pt)>8,'Complete prefix key set')
        need(all(pt[k].shape==pa[k].shape and pt[k].dtype==pa[k].dtype and pt[k].tobytes()==pa[k].tobytes() for k in pt),'Every prefix tensor exact')
        s=float(t['alignment.npz']['s0']);need(math.isfinite(s) and s>0,'Recorded scale positive')
        local=[]
        for i in range(4):
            pose=pt['local::poses'][i].astype(np.float64);points=pt['local::points.'+str(i)].astype(np.float64)
            need(points.shape==(384,512,3),'Complete expected grid')
            xyz=np.linalg.solve(pose[:3,:3],(points-pose[:3,3]).reshape(-1,3).T)
            local.append(xyz[2].reshape(384,512))
        z=np.stack(local);dt=t['initial_decoded.npz'];da=a['initial_decoded.npz'];checks=[]
        for name,actual,expected in [('C2t_prelog_vs_s_z',dt['prelog_depth'],s*z),('C2a_prelog_vs_z',da['prelog_depth'],z),('C2a_prelog_vs_C2t_div_s',da['prelog_depth'],dt['prelog_depth'].astype(np.float64)/s),('C2t_stored_vs_historical_B',dt['depth'],d['B']['initial_decoded.npz']['depth'])]:
            need(actual.shape==expected.shape==(4,384,512),'Complete comparison grid')
            x=actual.astype(np.float64);y=expected.astype(np.float64);diff=np.abs(x-y);valid=np.isfinite(x)&np.isfinite(y)
            bad=(~valid)|(diff>1e-5+1e-5*np.abs(y))
            checks.append(dict(name=name,pixels=int(x.size),nonfinite_pairs=int((~valid).sum()),outside_tolerance=int(bad.sum()),max_abs=float(diff[valid].max()) if valid.any() else None,per_frame_max_abs=[float(f[np.isfinite(f)].max()) if np.isfinite(f).any() else None for f in diff],passed=bool(not bad.any())))
        domains={arm:{key:dict(nonfinite=int((~np.isfinite(d[arm]['initial_decoded.npz'][key])).sum()),nonpositive=int((np.isfinite(d[arm]['initial_decoded.npz'][key])&(d[arm]['initial_decoded.npz'][key]<=0)).sum())) for key in ['prelog_depth','depth']} for arm in c['arms']}
        for p,h in identities.items():need(digest(Path(p).read_bytes())==h,'Input changed: '+p)
        result=dict(status='PASS_REFERENCE_EXECUTED',started_utc=start,completed_utc=utc(),wall_seconds=time.monotonic()-tick,contract_sha256=args.sha256,self_sha256=args.self_sha256,prefix_tensors_exact=len(pt),linear_solve_points=4*384*512,checks=checks,domains=domains,all_algebra_checks_passed=all(x['passed'] for x in checks),primary_hypothesis_passed=v['hypothesis_passed'],GT=0,MST=0,model=0,Adam=0,backward=0,evidence_scope='Different root implementation of complete saved-array algebra via linear solve; not a new model experiment, sensor accuracy, or numerical gradient replay')
        write(out/'receipt.json',result);print(json.dumps(result))
    except BaseException as e:
        write(out/'receipt.json',dict(status='FAILED',started_utc=start,failed_utc=utc(),error=repr(e)));raise
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--sha256',required=True);p.add_argument('--self-sha256',required=True);run(p.parse_args())
