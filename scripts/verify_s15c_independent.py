#!/usr/bin/env python3
"""Different-author real-data remeasurement with integer resize and scalar reductions."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,statistics,math,time,traceback
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1]
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def main():
    out=R/'results/S15C_independent';assert not out.exists();out.mkdir(parents=True)
    report=dict(started_utc=utc(),status='RUNNING',checks=0,depth_decodes=0,rgb_decodes=0,model_calls=0,method='No producer imports; integer nearest coordinates; Python statistics median and math.fsum errors; separate NumPy environment')
    def check(ok,label):
        report['checks']+=1
        if not ok:raise AssertionError(label)
    def close(a,b,label):
        check((a is None and b is None) or (a is not None and b is not None and math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=1e-10)),label)
    try:
        mp=R/'docs/S15C_OBSERVED_DEPTH_EXECUTION_MANIFEST.json';m=json.loads(mp.read_text());caldir=R/'results/S15C_bonn_calibration';score=R/'results/S15C_bonn_scores'
        cm=json.loads((caldir/'run_metadata.json').read_text());sm=json.loads((score/'run_metadata.json').read_text());check(cm['status']==sm['status']=='SUCCESS','producer completion')
        sealpath=R/'docs/S15C_CALIBRATED_PREDICTION_SEAL.json';seal=json.loads(sealpath.read_text());check(seal['manifest_sha256']==sha(mp)==cm['manifest_sha256']==sm['manifest_sha256'],'manifest binding')
        for p,h in seal['identities'].items():check(sha(p)==h,'sealed output')
        for meta,base in [(cm,caldir),(sm,score)]:
            for name,h in meta['output_sha256'].items():check(sha(base/name)==h,'output identity')
        evpaths={x['depth_path'] for x in m['samples'][4:]};check(not evpaths&{x['path'] for x in cm['reads']+cm['identity_hashes']},'no eval reads during calibration')
        gt=[];rawcounts=[]
        # floor((u+0.5)*640/299), floor((v+0.5)*480/224), with integer arithmetic.
        x=((2*(np.arange(224)+37)+1)*640)//(2*299);y=((2*np.arange(224)+1)*480)//(2*224)
        for s in m['samples']:
            check(sha(s['depth_path'])==s['depth_sha256'],'real sensor SHA')
            with Image.open(s['depth_path']) as image:raw=np.array(image)
            report['depth_decodes']+=1;check(raw.shape==(480,640),'native depth shape');rawcounts.append(int((raw>0).sum()))
            gt.append(raw[np.ix_(y,x)].astype(np.float64)/5000)
        gt=np.stack(gt)
        with np.load(m['history_predictions'],allow_pickle=False) as z:pred=np.stack([z[f'frame{i}_pts3d_in_self_view'][0,:,:,2].astype(np.float64) for i in range(20)])
        valid=(gt[:4]>0)&np.isfinite(gt[:4])&(pred[:4]>0)&np.isfinite(pred[:4]);ratios=(pred[:4][valid]/gt[:4][valid]).tolist()
        scale=statistics.median(ratios);constant=statistics.median(gt[:4][gt[:4]>0].tolist());c=json.loads((caldir/'calibration.json').read_text())
        close(scale,c['s_model_per_meter'],'independent median scale');close(constant,c['constant_depth_m'],'independent median constant')
        with np.load(caldir/'calibrated_predictions.npz',allow_pickle=False) as z:check(np.array_equal(z['model_depth_m'],pred/scale),'every scaled prediction');close(float(z['constant_depth_m']),constant,'constant array')
        with np.load(caldir/'calibration_gt.npz',allow_pickle=False) as z:check(np.array_equal(z['calibration_gt_depth_m'],gt[:4]),'integer resize all calibration pixels')
        with np.load(score/'arrays.npz',allow_pickle=False) as z:stored={k:z[k] for k in z.files}
        check(np.array_equal(stored['gt_depth_m'],gt[4:]),'integer resize all evaluation pixels')
        results=json.loads((score/'scores.json').read_text());rows=[];permethod={'model':[], 'constant':[]};pooled={name:dict(errors=[],relative=[],hits=0,total=0) for name in permethod}
        for j in range(16):
            g=gt[j+4];gv=np.isfinite(g)&(g>0);p=np.stack([pred[j+4]/scale,np.full_like(g,constant)]);pv=np.isfinite(p)&(p>0);own=pv&gv[None];common=own.all(axis=0);success=np.zeros_like(own)
            for k,name in enumerate(permethod):
                mask=own[k];pp=p[k][mask].tolist();gg=g[mask].tolist();hits=sum(max(a/b,b/a)<1.25 for a,b in zip(pp,gg));success[k,mask]=[max(a/b,b/a)<1.25 for a,b in zip(pp,gg)]
                n=int(gv.sum());row={'index':j+4,'method':name,'gt_valid_count':n,'own_valid_count':len(pp),'common_valid_count':int(common.sum()),'delta1_success_count':hits,'delta1_all_gt':hits/n if n else None,'coverage':len(pp)/n if n else None}
                for dom,dommask in [('own',mask),('common',common)]:
                    pairs=list(zip(p[k][dommask].tolist(),g[dommask].tolist()));err=[abs(a-b) for a,b in pairs];rel=[abs(a-b)/b for a,b in pairs];nn=len(err)
                    row.update({dom+'_mae_m':math.fsum(err)/nn if nn else None,dom+'_abs_rel':math.fsum(rel)/nn if nn else None,dom+'_rmse_m':math.sqrt(math.fsum(e*e for e in err)/nn) if nn else None})
                    if dom=='own':pooled[name]['errors'].extend(err);pooled[name]['relative'].extend(rel)
                pooled[name]['hits']+=hits;pooled[name]['total']+=n
                expected=next(x for x in results['rows'] if x['index']==j+4 and x['method']==name)
                for key,value in row.items():
                    if key not in ('index','method'):close(value,expected[key],'real scalar '+name+' '+str(j+4)+' '+key)
                rows.append(row);permethod[name].append(row)
            for key,value in [('prediction_depth_m',p),('gt_valid_mask',gv),('prediction_positive_finite_mask',pv),('own_valid_mask',own),('common_valid_mask',common),('delta1_success_mask',success)]:check(np.array_equal(stored[key][j],value),'every array '+key)
        for name,rs in permethod.items():
            main=next(x for x in results['means'] if x['method']==name);pool=next(x for x in results['pixel_weighted'] if x['method']==name);pp=pooled[name]
            for key in main['means']:
                vals=[x[key] for x in rs if x[key] is not None];v=math.fsum(vals)/len(vals) if vals else None
                close(v if len(vals)==16 else None,main['means'][key],'complete16 '+key);close(v,main['available_frame_descriptive_means'][key],'available only '+key)
            close(pp['hits']/pp['total'],pool['delta1_all_gt'],'pooled hits');nn=len(pp['errors'])
            for dom in ['own','common']:
                # All real methods have identical valid domains, checked above and per row.
                check(all(x['own_valid_count']==x['common_valid_count'] for x in rs),'actual common equals own')
                for key,v in [('mae_m',math.fsum(pp['errors'])/nn),('abs_rel',math.fsum(pp['relative'])/nn),('rmse_m',math.sqrt(math.fsum(e*e for e in pp['errors'])/nn))]:close(v,pool[dom+'_'+key],'pooled scalar '+dom+' '+key)
        report.update(status='PASS',scale=scale,constant_m=constant,raw_positive_depth_counts=rawcounts,cropped_positive_depth_counts=[int((g>0).sum()) for g in gt],empty_evaluation_indices=[i for i in range(4,20) if not (gt[i]>0).any()],primary_16_frame_means='undefined because a predeclared frame has no GT',source_prediction_self_arrays_decoded=20,manifest_sha256=sha(mp),prediction_seal_sha256=sha(sealpath),numpy_version=np.__version__)
    except BaseException as e:report.update(status='FAIL',error=repr(e),traceback=traceback.format_exc())
    report.update(completed_utc=utc(),verifier_sha256=sha(__file__));(out/'verification.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');print(json.dumps(report,indent=2));return int(report['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
