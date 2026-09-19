#!/usr/bin/env python3
"""Independent sealed S15A output verification, no model or image decoder imports."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import resource
import signal
import time
import traceback
import zipfile

import numpy as np
from scipy.spatial.transform import Rotation

COMMIT = '8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf'
CHECKPOINT_SHA = '7a7d83e47f822e040980c8f5aff4c15aa94366d469d3ceae51fa30cc2f62327d'
SECONDS = 600
RSS_BYTES = 34359738368
ATOL, RTOL = 1e-6, 1e-5
PAYLOADS = {'predictions.npz', 'state.npz', 'history_poses.npz', 'frozen_manifest.json', 'source_snapshot.py', 'checkpoint_load.txt'}
PRED = {'pts3d_in_self_view': (1,224,224,3), 'pts3d_in_other_view': (1,224,224,3), 'conf_self': (1,224,224), 'conf': (1,224,224), 'camera_pose': (1,7), 'rgb': (1,224,224,3)}
STATE = {'state_feat': ((1,768,768),'float32'), 'state_pos': ((1,768,2),'int64'), 'init_state_feat': ((1,768,768),'float32'), 'mem': ((1,256,1536),'float32'), 'init_mem': ((1,256,1536),'float32')}
POSES = {'history_pose_encodings': ((20,7),'float32'), 'history_poses': ((20,4,4),'float32')}
CONTRACT = dict(history_count=20,query_count=0,history_flags=dict(img_mask=True,ray_mask=False,update=True,reset=False),device='cpu',cpu_threads=8,seed=0,size=[224,224],dtype='float32',wall_seconds=SECONDS,monitored_rss_bytes=RSS_BYTES,external_monitor_required=True,history_rgb_allowed=True,target_rgb_allowed=False,target_depth_allowed=False)


def utc(): return datetime.now(timezone.utc).isoformat()
def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def array_sha(a): return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def require(ok, message):
    if not ok: raise ValueError(message)
def timestamp(s): return datetime.fromisoformat(s)


class Audit:
    def __init__(self): self.started=time.monotonic(); self.checks=[]
    def check(self, ok, name):
        self.checks.append(dict(name=name,passed=bool(ok)))
        require(ok,name)
        self.resource_check()
    def resource_check(self):
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if platform.system()=='Darwin' else 1024)
        require(time.monotonic()-self.started < SECONDS,'Verifier 600 second bound')
        require(rss < RSS_BYTES,'Verifier 32 GiB RSS bound')


def inspect_npz(path, schema, ids, audit):
    """Check NPY member declarations before bounded per-array loading."""
    audit.check(set(ids)==set(schema),'Array ID keys '+path.name)
    with zipfile.ZipFile(path) as archive:
        entries=archive.infolist()
        audit.check(len(entries)==len(schema) and {e.filename for e in entries}=={k+'.npy' for k in schema},'NPZ exact members '+path.name)
        for e in entries:
            shape,dtype=schema[e.filename[:-4]]
            maximum=int(np.prod(shape))*np.dtype(dtype).itemsize+16384
            audit.check(0 <= e.file_size <= maximum and not e.flag_bits&1,'Bounded NPY member '+e.filename)
    arrays={}
    with np.load(path,allow_pickle=False) as archive:
        for key,(shape,dtype) in schema.items():
            a=archive[key]
            audit.check(a.shape==shape and a.dtype==np.dtype(dtype),'Schema '+key)
            audit.check(bool(np.isfinite(a).all()),'Finite '+key)
            identity=ids[key]
            audit.check(identity.get('shape')==list(shape) and identity.get('dtype')==dtype,'Recorded array schema '+key)
            audit.check(identity.get('sha256')==array_sha(a),'Contiguous byte SHA '+key)
            arrays[key]=a
    return arrays


def inspect_poses(pred, encoded, poses, audit):
    for i in range(20):
        audit.check(encoded[i:i+1].tobytes()==pred[f'frame{i}_camera_pose'].tobytes(),'Encoding equals frame pose '+str(i))
    audit.check(np.ascontiguousarray(poses[:,:3,3]).tobytes()==np.ascontiguousarray(encoded[:,:3]).tobytes(),'Translation bytes equal encoding')
    audit.check(np.array_equal(poses[:,3,:],np.tile([0,0,0,1],(20,1))),'Exact homogeneous bottom row')
    q=encoded[:,3:7].astype(np.float64)
    audit.check(bool(np.all(np.linalg.norm(q,axis=1)>0)),'Nonzero quaternion norm')
    # SciPy uses xyzw. It normalizes nonunit quaternions independently of the
    # official Torch two_s quaternion polynomial; no runner import is used.
    independent=Rotation.from_quat(q[:,[1,2,3,0]]).as_matrix()
    error=float(np.max(np.abs(independent-poses[:,:3,:3])))
    audit.check(np.allclose(independent,poses[:,:3,:3],atol=ATOL,rtol=RTOL),'Independent SciPy quaternion rotation')
    rr=poses[:,:3,:3].astype(np.float64)
    audit.check(np.allclose(np.swapaxes(rr,1,2)@rr,np.eye(3),atol=1e-4,rtol=0) and np.allclose(np.linalg.det(rr),1,atol=1e-4,rtol=0),'Proper rotation completion gate')
    return error


def verify(seal_path, expected_sha, output):
    out=Path(output)
    require(not out.exists(),'Fresh verification output required')
    out.mkdir(parents=True)
    audit=Audit()
    report=dict(schema='s15a-history-independent-verification-v1',started_utc=utc(),status='RUNNING',checks=audit.checks,limits=dict(seconds=SECONDS,rss_bytes=RSS_BYTES),tolerances=dict(atol=ATOL,rtol=RTOL),real_model_calls=0,image_decodes=0,depth_decodes=0,trajectory_decodes=0,checkpoint_deserializations=0,accuracy_evaluated=False,video_generated=False,files_verified=0,arrays_verified=0,implementation='Independent NumPy/SciPy verifier; no runner or model imports',numpy_version=np.__version__)
    previous_handler=signal.getsignal(signal.SIGALRM)
    def deadline(signum,frame): raise TimeoutError('Verifier hard 600 second alarm')
    signal.signal(signal.SIGALRM,deadline);signal.alarm(SECONDS)
    try:
        seal_path=Path(seal_path).resolve()
        audit.check(digest(seal_path)==expected_sha,'Externally supplied seal SHA')
        seal=json.loads(seal_path.read_text())
        audit.check(seal['schema']=='s15a-history-combined-seal-v1','Seal schema')
        report['seal_sha256']=expected_sha
        ids=seal['identities']
        for p,h in ids.items():
            audit.check(Path(p).is_absolute() and str(Path(p).resolve())==p and len(h)==64 and all(x in '0123456789abcdef' for x in h),'Canonical identity '+p)
        for role in ('manifest','caller_receipt','verifier'):
            audit.check(seal[role] in ids,'Seal role identity '+role)
        audit.check(str(Path(__file__).resolve())==seal['verifier'],'Verifier path')
        # Hash all sources/inputs and all successful outputs before any NPZ decode.
        for p,h in ids.items():
            audit.check(digest(p)==h,'File SHA '+p);report['files_verified']+=1
        manifest_path=Path(seal['manifest']);m=json.loads(manifest_path.read_text());run=Path(seal['run_dir'])
        audit.check(run.is_absolute() and run.resolve()==run,'Canonical run directory')
        audit.check(m['schema']=='s15-history-manifest-v1' and m['commit']==COMMIT,'Pinned manifest/commit')
        audit.check(all(m['contract'].get(k)==v for k,v in CONTRACT.items()),'History-only fixed contract')
        history=m['history_images'];paths=[x['path'] for x in history]
        audit.check(len(history)==20 and [x['index'] for x in history]==list(range(20)) and len(set(paths))==20,'Twenty ordered history identities')
        mids=m['identities'];repo=Path(m['repo'])
        for x in history:audit.check(mids.get(x['path'])==x['sha256'] and Path(x['path']).suffix.lower() in {'.png','.jpg','.jpeg'},'History identity '+str(x['index']))
        upstream={p for p in mids if Path(p).is_relative_to(repo) and Path(p).suffix=='.py'}
        controls=set(m.get('control_files',[]));adapter=str(Path(m['runner']).parent/'cut3r_rope_compat.py')
        audit.check(len(upstream)==99,'Ninety-nine upstream sources')
        audit.check(len(controls)==len(m.get('control_files',[])) and all(Path(p).suffix in {'.md','.json','.py'} for p in controls),'Distinct allowed control files')
        audit.check(set(mids)==upstream|controls|set(paths)|{m['runner'],m['checkpoint'],m['rope_check'],adapter},'Input allowlist excludes other scene data')
        audit.check(all(Path(p).name not in {'rgb.txt','depth.txt','groundtruth.txt'} for p in mids),'No raw trajectory or dataset index input')
        audit.check(mids[m['checkpoint']]==CHECKPOINT_SHA,'Pinned weight digest')
        audit.check(all(ids.get(p)==h for p,h in mids.items()),'Manifest input identities bind seal')
        expected_files=PAYLOADS|{'run_metadata.json'}
        audit.check({p.name for p in run.iterdir()}==expected_files and all((run/n).is_file() for n in expected_files),'Exact seven output files')
        exact_ids=set(mids)|{str(run/n) for n in expected_files}|{seal['manifest'],seal['caller_receipt'],seal['verifier']}
        audit.check(set(ids)==exact_ids,'Exact combined identity set')
        meta=json.loads((run/'run_metadata.json').read_text());caller=json.loads(Path(seal['caller_receipt']).read_text())
        audit.check(meta['schema']=='s15-history-run-v1' and meta['status']=='SUCCESS' and meta['phase']=='complete','Successful history metadata')
        audit.check(meta['manifest_sha256']==ids[seal['manifest']] and caller['manifest_sha256']==ids[seal['manifest']],'Manifest digest in both receipts')
        audit.check(digest(run/'frozen_manifest.json')==ids[seal['manifest']] and digest(run/'source_snapshot.py')==mids[m['runner']],'Frozen input/source byte copies')
        audit.check(set(meta['output_sha256'])==PAYLOADS,'Recorded payload inventory')
        for n,h in meta['output_sha256'].items():audit.check(h==ids[str(run/n)],'Recorded payload SHA '+n)
        audit.check(all(meta[x] is False for x in ('video_generated','new_model_trained','accuracy_evaluated')),'No video/training/accuracy claim')
        audit.check(meta['history_images']==history and meta['image_open_attempt_paths']==paths and meta['image_opened_paths']==paths,'Exact actual history image open paths')
        c=meta['counters'];expected=dict(history_image_open_attempts=20,history_images_opened=20,history_rgb_decoded=20,target_rgb_decoded=0,target_depth_decoded=0,history_forward_attempts=1,history_forward_calls=1,history_image_encoder_calls=1,history_image_encoder_frames=20,history_ray_encoder_calls=1,history_frames_saved=20,query_calls=0,identity_hash_attempts=2*len(mids),identity_hash_successes=2*len(mids))
        audit.check(all(c.get(k)==v for k,v in expected.items()),'Recorded exact decode and runtime call counts')
        attempted=[x['path'] for x in meta['identity_hash_attempts']]
        audit.check(attempted==list(mids)*2,'Both full identity pass orders')
        audit.check(meta['before_after_identity_pass'] is True and meta['raw_predictions_saved_before_gates'] is True,'Identity and evidence persistence gates')
        audit.check(meta['checkpoint_all_keys_matched'] is True and meta['weights_only'] is True,'Recorded safe matched checkpoint load')
        audit.check(meta['device']=='cpu' and meta['cpu_threads']==8 and meta['seed']==0 and meta['commit']==COMMIT,'Recorded fixed runtime')
        props=meta['raw_image_properties']
        audit.check(len(props)==20 and [p['index'] for p in props]==list(range(20)) and [p['path'] for p in props]==paths,'Native image properties order')
        audit.check(all(isinstance(p['size'],list) and len(p['size'])==2 and all(isinstance(x,int) and x>0 for x in p['size']) and isinstance(p['mode'],str) and p['mode'] for p in props),'Native sizes and modes recorded without guessing')
        report['reported_native_image_properties']=props
        reads=meta['input_reads']
        audit.check(len(reads)==2 and reads[0]['role']=='manifest' and reads[0]['path']==seal['manifest'] and reads[1]['role']=='rope_check' and reads[1]['path']==m['rope_check'],'Explicit JSON input read roles')
        loaded=meta['loaded_upstream_modules']
        audit.check(bool(loaded) and all(v['path'] in upstream and mids[v['path']]==v['sha256'] for v in loaded.values()),'Recorded imported sources frozen')
        audit.check(meta['elapsed_seconds']<SECONDS and 0<meta['peak_rss_bytes']<RSS_BYTES,'Runner completion resource bounds')
        audit.check(caller['schema']=='s14d-caller-v1' and caller['status']=='PASS' and caller['returncode']==0 and caller['monitor_ok'] and caller['before_after_identity_pass'] and not caller['timed_out'] and not caller['rss_limit_exceeded'],'External caller passed live monitoring')
        audit.check(caller['limits']=={'seconds':SECONDS,'rss_bytes':RSS_BYTES} and 0<caller['maxrss']<=RSS_BYTES and caller['elapsed_seconds']<SECONDS,'Caller fixed resource bounds')
        cmd=caller['command']
        audit.check(len(cmd)==6 and cmd[0]==m['python'] and cmd[1]==m['runner'] and cmd[2]=='--manifest' and Path(cmd[3]).resolve()==manifest_path and cmd[4]=='--output' and Path(cmd[5]).resolve()==run,'Actual caller command')
        audit.check(timestamp(caller['started_utc'])<=timestamp(meta['started_utc'])<=timestamp(meta['completed_utc'])<=timestamp(caller['completed_utc'])<=timestamp(seal['sealed_utc']),'Run/caller/seal time order')
        pred_schema={f'frame{i}_{k}':(shape,'float32') for i in range(20) for k,shape in PRED.items()}
        pred=inspect_npz(run/'predictions.npz',pred_schema,meta['history_output_ids'],audit)
        state=inspect_npz(run/'state.npz',STATE,meta['state_final'],audit)
        poses=inspect_npz(run/'history_poses.npz',POSES,meta['history_pose_ids'],audit)
        report['arrays_verified']=len(pred)+len(state)+len(poses)
        report['independent_rotation_max_absolute_error']=inspect_poses(pred,poses['history_pose_encodings'],poses['history_poses'],audit)
        description=[]
        for i in range(20):
            z=pred[f'frame{i}_pts3d_in_self_view'][0,:,:,2];positive=z>0
            description.append(dict(frame=i,total_pixels=int(z.size),positive_pixels=int(positive.sum()),minimum=float(z.min()),maximum=float(z.max()),units='unaligned model units, not certified meters'))
        report['self_z_numerical_description']=description
        audit.check(digest(seal_path)==expected_sha,'Seal remained unchanged')
        report.update(status='PASS',interpretation='Input/output identity, numerical integrity, and recorded runtime behavior verified; no accuracy or generalization conclusion.')
    except BaseException as e:
        report.update(status='FAIL',error=repr(e),traceback=traceback.format_exc())
    finally:
        signal.alarm(0);signal.signal(signal.SIGALRM,previous_handler)
        report.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-audit.started,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if platform.system()=='Darwin' else 1024))
        (out/'verification.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(status=report['status'],files=report['files_verified'],arrays=report['arrays_verified'],checks=len(audit.checks),result=str(out/'verification.json'))))
    return 0 if report['status']=='PASS' else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seal',required=True);p.add_argument('--seal-sha256',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    raise SystemExit(verify(a.seal,a.seal_sha256,a.output))
