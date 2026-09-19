"""S22 FILT scoring with the same frozen metric definitions as S21."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,csv,hashlib,importlib.util,json,sys
ROOT=Path(__file__).resolve().parents[1]
W=ROOT/'work/S22_filt_shared_precision'
B=ROOT/'results/S22_filt_shared_precision'
R=ROOT/'work/S21_baseline_preparation/ttt3r_original'
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def matrix_metrics(P,G):
    import numpy as np
    X=P[:,:3,3];Y=G[:,:3,3];xc=X-X.mean(0);yc=Y-Y.mean(0)
    U,s,Vt=np.linalg.svd(yc.T@xc/len(X));D=np.ones(3);D[-1]=np.linalg.det(U@Vt)
    rot=U@np.diag(D)@Vt;scale=float((s*D).sum()/(xc**2).sum()*len(X));trans=Y.mean(0)-scale*rot@X.mean(0)
    A=P.copy();A[:,:3,:3]=rot@P[:,:3,:3];A[:,:3,3]=(scale*rot@X.T).T+trans
    ate=np.linalg.norm(A[:,:3,3]-G[:,:3,3],axis=1)
    rgt=np.linalg.inv(G[:-1])@G[1:];rest=np.linalg.inv(A[:-1])@A[1:]
    err=np.linalg.inv(rgt)@rest
    et=np.linalg.norm(err[:,:3,3],axis=1)
    er=np.rad2deg(np.arccos(np.clip((np.trace(err[:,:3,:3],axis1=1,axis2=2)-1)/2,-1,1)))
    metrics=[float(np.sqrt(np.mean(z*z)))for z in [ate,et,er]]
    return metrics,dict(scale=scale,rotation=rot.tolist(),translation=trans.tolist()),A,ate,et,er
def score():
    sys.path.append(str(ROOT/'work/S17C_environment/site-packages'));sys.path.insert(0,str(R))
    import numpy as np
    from scipy.spatial.transform import Rotation
    from eval.relpose.evo_utils import eval_metrics,load_traj
    from eval.relpose.utils import get_tum_poses
    comp=json.loads((B/'compatibility.json').read_text());assert comp['passed'],'Original-source compatibility unresolved'
    m=json.loads((W/'run_manifest.json').read_text())
    seals={}
    for name in m['methods']:
        report=B/name/'receipt.json';s=json.loads(report.read_text());c=json.loads((ROOT/'work/S22_shared_execution'/name/'receipt.json').read_text())
        assert s['status']==c['status']=='PASS'and s['frames_completed']==300 and s['manifest_sha256']==sha(W/'run_manifest.json')
        assert sha(B/name/'poses.npy')==s['poses_sha256']
        for f in s['outputs']:assert sha(B/name/f['file'])==f['sha256']
        seals[name]=dict(receipt_sha256=sha(report),poses_sha256=s['poses_sha256'],outputs=len(s['outputs']))
    out=B/'scoring';assert not out.exists();out.mkdir()
    write(out/'pre_score_seal.json',dict(utc=utc(),methods=seals,script_sha256=sha(__file__),gt_coordinates_read=False))
    assert sha(m['gt_file'])==m['gt_sha256']
    # S22 coordinate scoring follows its output seal; S21 has already used this known scene.
    gtraw={float(s.split()[0]):s.split()for s in Path(m['gt_file']).read_text().splitlines()if s.strip()and not s.startswith('#')}
    chosen=[gtraw[f['gt_time']]for f in m['frames']]
    (out/'groundtruth_300.txt').write_text('\n'.join(' '.join(r)for r in chosen)+'\n')
    gt=load_traj(str(out/'groundtruth_300.txt'),traj_format='tum')
    gtarr=np.array(chosen,dtype=np.float64)
    G=np.repeat(np.eye(4)[None],300,axis=0);G[:,:3,3]=gtarr[:,1:4];G[:,:3,:3]=Rotation.from_quat(gtarr[:,4:8]).as_matrix()
    report=dict(started_utc=utc(),scope='previously exposed fr2_desk first 300 timestamp-associated frames; one sequence; partial geometry baseline reproduction',metrics=['ATE_RMSE_m','RPE_translation_RMSE_m','RPE_rotation_RMSE_deg'],methods={},new_method=False,independent_author_review=False)
    for name in m['methods']:
        P=np.load(B/name/'poses.npy').astype(np.float64);assert P.shape==(300,4,4)and np.isfinite(P).all()
        official=list(map(float,eval_metrics(get_tum_poses(P),copy.deepcopy(gt),seq='fr2_desk_300_'+name,filename=str(out/(name+'_evo.txt')))))
        # The official evaluator converts matrices through SciPy quaternions.
        # Use the same SO(3) normalization; alignment and SE(3) error algebra below
        # are independently implemented, not a second call into evo.
        normalized=P.copy();normalized[:,:3,:3]=Rotation.from_matrix(P[:,:3,:3]).as_matrix()
        independent,alignment,A,ate,et,er=matrix_metrics(normalized,G)
        check=bool(np.allclose(official,independent,atol=1e-6,rtol=1e-5))
        np.savez_compressed(out/(name+'_aligned.npz'),pred=A,gt=G,ate_m=ate,rpe_translation_m=et,rpe_rotation_deg=er)
        blocks=[dict(start=k,end_exclusive=k+60,ate_rmse_m=float(np.sqrt(np.mean(ate[k:k+60]**2))))for k in range(0,300,60)]
        r=dict(official=official,independent_matrix=independent,metric_check_passed=check,alignment=alignment,
               all_five_blocks=blocks,worst_indices_descending=np.argsort(-ate).tolist()[:10],frame_count=300,rpe_pair_count=299)
        report['methods'][name]=r
        with (out/(name+'_per_frame.csv')).open('w')as f:
            writer=csv.writer(f);writer.writerow(['index','rgb_timestamp','gt_timestamp','ate_m','rpe_to_next_translation_m','rpe_to_next_rotation_deg'])
            for i,frame in enumerate(m['frames']):writer.writerow([i,frame['rgb_time'],frame['gt_time'],ate[i],et[i]if i<299 else '',er[i]if i<299 else ''])
    report.update(completed_utc=utc(),passed=all(x['metric_check_passed']for x in report['methods'].values()),
                  prediction_and_score_order='FILT output sealed before S22 scoring; public configuration frozen before S21 scoring; previously seen scene',compatibility_sha256=sha(B/'compatibility.json'))
    write(out/'metrics.json',report);print(json.dumps(report,ensure_ascii=False))
    assert report['passed'],'Keep mismatch; do not change frozen metric tolerance'
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['score']);a=p.parse_args()
    score()
