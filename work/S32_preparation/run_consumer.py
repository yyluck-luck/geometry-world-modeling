"""S32 B draft: each fresh4 window's same-state C2a 0/400/one-scalar endpoints.

Runtime requires its own frozen contract and all stage-A sealed producers.
Original GA and numerical references are reused; no model or sensor GT is read.
"""
from __future__ import annotations
import argparse
import ast
import copy
import importlib
from pathlib import Path
import sys
import traceback

# Same-directory utility source is itself bound by the B contract.
from run_inference import utc, read, sha, require, write, module

ENDPOINTS = ('initial_0step', 'corrected_getter_400', 'global_rescaled_400')


def contract(path, expected):
    require(sha(path)==expected,'Exact frozen S32 B contract SHA')
    c=read(path)
    require(c['status']=='FROZEN' and c['schema']=='s32-same-window-c2a-consumer-v1','B candidate cannot execute')
    require(c['limits']==dict(threads=8,seconds_per_window=120,rss_bytes_per_window=4*1024**3),'Fixed B budget')
    require(c['endpoints']==list(ENDPOINTS) and c['steps']==400,'Only the three predefined endpoints')
    for p,h in c['identities'].items():require(sha(p)==h,'Changed B source/input metadata: '+p)
    require(sha(c['selection'])==c['selection_sha256'],'Same root-sealed fixed selection')
    selected=read(c['selection'])['windows']
    require([w['id'] for w in selected]==[w['id'] for w in c['windows']],'All selected windows in original order')
    for old,new in zip(selected,c['windows']):
        require(old==new,'B cannot alter selected rows, associations or exposure')
    require(sha(c['A_contract'])==c['A_contract_sha256'],'Actual A frozen contract')
    for window in c['windows']:
        entry=c['A_receipts'][window['id']]
        require(sha(entry['path'])==entry['sha256'],'Bound A producer receipt')
        r=read(entry['path'])
        require(r['status']=='PASS_INFERENCE_SEALED' and r['contract_sha256']==c['A_contract_sha256'] and r['window']==window['id'],'Full A producer, including unavailable-pose window')
    c['_sha']=expected;c['_path']=str(Path(path).resolve())
    return c


def derive_observer(s30, s28_path):
    """The S30 observer becomes a same-current-window checkpoint observer.

    Only the historical-reference callback and truthful report names change;
    inherited getter, original MST, all gradient checks and all 400 steps stay.
    """
    _,old,_=s30.derive_observer(s28_path);new=copy.deepcopy(old)
    counts=dict(callback=0,reference_label=0,initialization_label=0)
    labels={'s30_initialization':'s32_initialization','s30_gradient_steps':'s32_gradient_steps',
            's30_objective_forward_counts':'s32_objective_forward_counts','S30_first_step_gate_passed':'S32_same_window_first_step_gate_passed'}
    class Rename(ast.NodeTransformer):
        def visit_Name(self,node):
            if node.id=='verify_s29_initial_state':node.id='verify_window_initial_state';counts['callback']+=1
            return node
        def visit_keyword(self,node):
            if node.arg=='reference_S29_raw_exact':node.arg='same_window_initial_state_saved';counts['reference_label']+=1
            if node.arg=='s29_initialization_path_preserved':node.arg='C2a_initialization_path_preserved';counts['initialization_label']+=1
            return self.generic_visit(node)
        def visit_Constant(self,node):
            if isinstance(node.value,str) and node.value in labels:node.value=labels[node.value]
            return node
    new=Rename().visit(new);ast.fix_missing_locations(new)
    require(counts==dict(callback=1,reference_label=1,initialization_label=1),'Bound observer identity-only adaptation')
    return old,new


def verify_window_initial_state(observer,c,arm,loss_before,np):
    require(arm=='C2a' and observer.mst_calls==1 and observer.steps==observer.adam_steps==0,'Same-window snapshot strictly before optimization')
    require(len(observer.initial_arrays)==len(observer.initial_meta)==33,'Complete original common4 raw checkpoint')
    require(read(observer.out/'initial_raw_metadata.json')==observer.initial_meta,'Complete saved raw metadata')
    with np.load(observer.out/'initial_raw.npz',allow_pickle=False) as archive:
        require(set(archive.files)==set(observer.initial_arrays),'Complete serialized raw tensor names')
        for name,initial in observer.initial_arrays.items():
            actual=archive[name]
            require(actual.dtype==initial.dtype and actual.shape==initial.shape and actual.tobytes()==initial.tobytes(),'Same live initial checkpoint bytes: '+name)
    with np.load(observer.out/'initial_decoded.npz',allow_pickle=False) as archive:
        actual=archive['objective']
        require(actual.dtype==loss_before.dtype and actual.shape==loss_before.shape and actual.tobytes()==loss_before.tobytes(),'Same live initial objective')
    write(observer.out/'same_window_initial_gate.json',dict(status='PASS',window_id=c['_window_id'],contract_sha256=c['_sha'],
        raw_count=33,raw_and_objective_serialization_exact=True,meaning='Own same-memory MST snapshot, not equality with any historical common4 or another window'))


def observer_type(b,r,s30,c):
    _,node=derive_observer(s30,c['s28_runner'])
    namespace=dict(vars(r));namespace['verify_window_initial_state']=verify_window_initial_state
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(Path(__file__))+'::same_window_observer','exec'),namespace)
    Parent=namespace['observer_type'](b,c,'C2a')
    class C2aObserver(Parent):
        def install(self):
            super().install()
            init=importlib.import_module('cloud_opt.dust3r_opt.init_im_poses')
            calls=0
            def alignment(old):
                def call(src,target):
                    nonlocal calls
                    require(calls==0,'One original alignment only');calls+=1
                    source=b.array(src);given=b.array(target)
                    s0,R0,T0=old(src,target)
                    s=1.0 if isinstance(s0,float) else s0.new_tensor(1.0)
                    T=target[:,:3,3].mean(0)-s*(R0@src[:,:3,3].mean(0))
                    self.alignment_values=dict(source_c2w=source,target_c2w=given,s0=b.array(s0),R0=b.array(R0),T0=b.array(T0),s_used=b.array(s),R_used=b.array(R0),T_used=b.array(T))
                    np=importlib.import_module('numpy')
                    np.savez_compressed(self.out/'controlled_alignment.npz',**self.alignment_values)
                    self.report['s32_alignment_calls']=calls
                    return s,R0,T
                return call
            self.patch(init,'align_multiple_poses',alignment)
    return C2aObserver


def derive_worker(r,parent_source):
    old,node=r.derive_worker(parent_source)
    node.body[0]=ast.parse("require(mode == 'C2a', 'S32 one same-window unit-scale control')").body[0]
    matches=[n for n in ast.walk(node) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='name' for t in n.targets)]
    require(len(matches)==1 and ast.unparse(matches[0].value)=="'common_old_depth_original4'",'Inherited four-head archive dispatch')
    matches[0].value=ast.Constant('selected_window_cut3r')
    ast.fix_missing_locations(node)
    return old,node


def controls_and_compatibility(c,window,b,m):
    """Allowed selected camera coordinates; never opens sensor depth images."""
    np,torch,a,ns,views,proof=b.original_context(m)
    condition=window['given_pose_condition'];source=Path(condition['source'])
    require(sha(source)==condition['expected_sha256'],'Selected original optical camera text SHA')
    selected={f['gt_time'] for f in window['frames']};require(None not in selected,'All four camera matches required')
    from scipy.spatial.transform import Rotation
    camera_rows={}
    for line in source.read_text().splitlines():
        fields=line.split()
        if not fields or fields[0].startswith('#'):continue
        timestamp=float(fields[0])
        if timestamp in selected:
            require(timestamp not in camera_rows,'Unique selected timestamp')
            camera_rows[timestamp]=[float(v) for v in fields[1:]]
    cameras=np.repeat(np.eye(4,dtype=np.float64)[None],4,axis=0)
    for index,frame in enumerate(window['frames']):
        row=camera_rows[frame['gt_time']]
        require(len(row)==7 and np.isfinite(row).all() and abs(np.linalg.norm(row[3:])-1)<1e-3,'Original selected camera/quaternion domain')
        cameras[index,:3,:3]=Rotation.from_quat(row[3:]).as_matrix();cameras[index,:3,3]=row[:3]
    np.save(b.WORK/'control_c2w.npy',cameras.astype(np.float32))
    write(b.WORK/'control_receipt.json',dict(status='PASS',completed_utc=utc(),manifest_sha256=c['_sha'],window_id=window['id'],
        selection_sha256=c['selection_sha256'],frame_count=4,output_sha256=sha(b.WORK/'control_c2w.npy'),sensor_depth_used=False,
        source_sha256=condition['expected_sha256'],coordinates='TUM optical c2w directly, absolute metric world; no additional flip',role=condition['role']))
    A_path=Path(c['A_receipts'][window['id']]['path']);A=read(A_path);folder=A_path.parent
    require(sha(folder/'preprocessing.npz')==A['outputs']['preprocessing.npz'],'A preprocessing sealed')
    with np.load(folder/'preprocessing.npz',allow_pickle=False) as archive:
        require(set(archive.files)=={f'{kind}_{i}' for kind in ('img','shape') for i in range(4)},'Complete four A preprocessed images/shapes')
        for i,view in enumerate(views):
            for key,name in [('img','img'),('shape','true_shape')]:
                actual=b.array(view[name]);old=archive[f'{key}_{i}']
                require(actual.dtype==old.dtype and actual.shape==old.shape and actual.tobytes()==old.tobytes(),'A/B original PIL bytes: '+key)
    predictions=a.load_saved_predictions(m['candidate']['archives']['selected_window_cut3r'])
    output=a.assemble_saved_output(ns,views,predictions)
    expected={'view1':ns['collate_with_cat']([views[0]]*3),'view2':ns['collate_with_cat'](views[1:]),
              'pred1':ns['collate_with_cat']([predictions[0]]*3),'pred2':ns['collate_with_cat'](predictions[1:])}
    b.compare_nested(output,expected,torch)
    write(b.WORK/'compatibility_receipt.json',dict(status='PASS',completed_utc=utc(),manifest_sha256=c['_sha'],window_id=window['id'],
        source_proof=proof,checks=['all4_original_PIL_bytes_equal_A','original_allhead_star_equal_explicit_star'],
        model_forwards=0,GA_runs=0,sensor_depth_used=False,scope='This window actual A/B saved-head and PIL integration, not imported old common4 compatibility'))
    # Preserve these exact already checked views for the unchanged producer.
    b.original_context=lambda unused:(np,torch,a,ns,views,proof)
    return np


def worker(c,window_id):
    matches=[w for w in c['windows'] if w['id']==window_id];require(len(matches)==1,'Fixed window only')
    window=matches[0];out=Path(c['output_root'])/window_id
    require(not out.exists(),'Never repeat or overwrite a B window');out.mkdir(parents=True)
    record=dict(status='RUNNING',started_utc=utc(),window_id=window_id,contract_sha256=c['_sha'],selection_sha256=c['selection_sha256'],
                outputs={},sensor_depth_bytes_read=0,new_model_forwards=0,all_three_endpoints_available=False)
    write(out/'receipt.json',record)
    missing=[f['index'] for f in window['frames'] if f['gt_time'] is None]
    if missing:
        record.update(status='UNAVAILABLE',completed_utc=utc(),reason='MISSING_GIVEN_CAMERA_ASSOCIATION',missing_pose_frame_indices=missing,
            all_three_endpoints_available=False,GT_pose_bytes_read=0,new_MST=0,new_Adam=0)
        write(out/'receipt.json',record);return
    try:
        b=module(c['parent_runner'],'s32_B_original_producer');r=module(c['s28_runner'],'s32_B_s28_observer');s30=module(c['s30_runner'],'s32_B_s30_adapter')
        m=read(c['parent_manifest']);m['candidate']=dict(frames=window['frames'],archives={})
        A_path=Path(c['A_receipts'][window_id]['path']);A=read(A_path);A_root=A_path.parent
        require(sha(A_root/'head_archive_records.json')==A['outputs']['head_archive_records.json'],'A archive list seal')
        heads=read(A_root/'head_archive_records.json')
        require(len(heads)==4,'Fresh four head archives')
        for i,head in enumerate(heads):
            require(head['index']==i and head['source_rgb_sha256']==window['frames'][i]['sha256'] and head['anchor_local_index']==0,'Own window fresh anchor/source identity')
            require(Path(head['path']).parent==A_root and sha(head['path'])==head['sha256']==A['outputs'][Path(head['path']).name],'Bound actual A head bytes')
        m['candidate']['archives']['selected_window_cut3r']=heads
        b.WORK=out/'control';b.WORK.mkdir();b.MANIFEST=Path(c['_path']);b.OUT=out/'GA';b.OUT.mkdir()
        local=dict(c,_window_id=window_id)
        b.SceneObserver=observer_type(b,r,s30,local)
        np=controls_and_compatibility(c,window,b,m)
        _,node=derive_worker(r,c['parent_runner'])
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(Path(__file__))+'::original_ga','exec'),vars(b))
        b.ga_worker(m,'C2a')
        producer=read(b.OUT/'C2a/receipt.json')
        require(producer['status']=='PASS' and producer['manifest_sha256']==c['_sha'],'Complete inherited producer seal')
        require(producer['iterations']==producer['adam_steps']==400 and producer['clean_calls']==1,'Original full400 and clean')
        require(producer['observer']['s32_gradient_steps']==400 and producer['observer']['s32_alignment_calls']==1 and len(producer['observer']['pnp_calls'])==3,'Actual same-window original counts')
        endpoints=[]
        for filename in ('initial_decoded.npz','output.npz'):
            p=b.OUT/'C2a'/filename;require(sha(p)==producer['outputs'][filename],'Complete initial/final sealed file')
            with np.load(p,allow_pickle=False) as archive:depth=archive['depth'].copy()
            require(depth.shape==(4,384,512) and depth.dtype==np.float32 and np.isfinite(depth).all() and (depth>0).all(),'Complete positive FP32 endpoint')
            endpoints.append(depth)
        normalizer=module(c['s31_normalizer'],'s32_B_original_S31_normalizer')
        decomposition,arrays=normalizer.decompose(*endpoints)
        require(arrays['depth'].shape==(4,384,512) and arrays['depth'].dtype==np.float64,'Full FP64 normalized endpoint')
        np.savez_compressed(out/'initial_0step.npz',depth=endpoints[0])
        np.savez_compressed(out/'corrected_getter_400.npz',depth=endpoints[1])
        np.savez_compressed(out/'global_rescaled_400.npz',depth=arrays['depth'])
        np.savez_compressed(out/'normalization_arrays.npz',**arrays)
        write(out/'decomposition.json',decomposition)
        for p,h in c['identities'].items():require(sha(p)==h,'B source/input metadata changed')
        require(sha(A_path)==c['A_receipts'][window_id]['sha256'],'A receipt changed during B')
        require(sha(window['given_pose_condition']['source'])==window['given_pose_condition']['expected_sha256'],'Given camera source unchanged during B')
        record.update(status='PASS',completed_utc=utc(),all_three_endpoints_available=True,
            new_MST=1,new_PnP=3,new_Adam=400,new_backward=400,original_clean_calls=1,
            endpoint_files={name:name+'.npz' for name in ENDPOINTS},
            outputs={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and p!=out/'receipt.json'},
            raw_initial_state_count=33,normalization=dict(k=decomposition['k'],source='original S31, own complete initial/final predictions only; no GT/pose/conf selection'),
            evidence_scope='Whole-window ordinary three-control producer; output normalization is depth only, not new world/optimizer state')
        write(out/'receipt.json',record)
    except BaseException as error:
        record.update(status='FAILED',failed_utc=utc(),reason=repr(error),all_three_endpoints_available=False,
            endpoint_policy='All three unavailable to scoring; partial GA files retained without upgrading zero-step to PASS')
        write(out/'receipt.json',record);(out/'traceback.txt').write_text(traceback.format_exc());raise


def dispatch(c,path):
    b=module(c['parent_runner'],'s32_B_existing_supervisor');b.WORK=Path(c['execution_root']);b.WORK.mkdir(parents=True,exist_ok=True)
    target=b.WORK/'dispatch_receipt.json';require(not target.exists(),'No repeated B dispatch')
    receipt=dict(status='RUNNING',started_utc=utc(),contract_sha256=c['_sha'],selection_sha256=c['selection_sha256'],windows={})
    write(target,receipt)
    for window in c['windows']:
        name=window['id'];command=[sys.executable,str(Path(__file__).resolve()),'worker','--window',name,'--contract',str(path),'--sha256',c['_sha']]
        try:b.supervised(command,name,120,4*1024**3)
        except Exception as error:
            out=Path(c['output_root'])/name;out.mkdir(parents=True,exist_ok=True);file=out/'receipt.json'
            old=read(file) if file.exists() else {}
            if old.get('status') not in ('FAILED','UNAVAILABLE'):
                write(file,dict(status='FAILED',window_id=name,contract_sha256=c['_sha'],selection_sha256=c['selection_sha256'],
                    completed_utc=utc(),reason='External worker failure: '+repr(error),outputs={},all_three_endpoints_available=False,
                    partial_artifacts_retained=True,previous_nonterminal_receipt=old))
        actual=read(Path(c['output_root'])/name/'receipt.json')
        require(actual['status'] in ('PASS','FAILED','UNAVAILABLE'),'Terminal whole-window state required')
        receipt['windows'][name]=dict(status=actual['status'],receipt_sha256=sha(Path(c['output_root'])/name/'receipt.json'))
        write(target,receipt)
    receipt.update(status='COMPLETE_FIXED_WINDOW_MATRIX_SEALED',completed_utc=utc(),sensor_depth_read=False,
                   success_windows=sum(x['status']=='PASS' for x in receipt['windows'].values()),
                   next='Separate frozen scorer now eligible; all four windows and all three endpoints retained')
    write(target,receipt)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['dispatch','worker'])
    parser.add_argument('--window');parser.add_argument('--contract',required=True);parser.add_argument('--sha256',required=True)
    args=parser.parse_args();c=contract(args.contract,args.sha256)
    if args.command=='worker':worker(c,args.window)
    else:dispatch(c,args.contract)
