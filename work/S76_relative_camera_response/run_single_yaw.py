"""S76 single target-yaw arm, reusing immutable S70 computation and accepted A0."""
from __future__ import annotations
import ast
from datetime import datetime, timezone
import gc
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import shutil
import sys
import time
import traceback
import types

D=Path(__file__).resolve().parent
R=D.parents[1]
FIELDS=('crossattn','replace','concat','dense_vector')
HELPERS={'get_default_intrinsics','to_hom','to_hom_pose','get_image_grid',
         'img2cam','cam2world','get_center_and_ray','get_plucker_coordinates'}
METHODS={'get_translation_scaling_factor','get_cond'}


def sha(b):return hashlib.sha256(b).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def need(ok,msg):
    if not ok:raise RuntimeError(msg)
def write(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
    return dict(path=str(p),sha256=sha(p.read_bytes()),size_bytes=p.stat().st_size)

def module_from_bytes(name,path,body):
    m=types.ModuleType(name);m.__file__=path;sys.modules[name]=m
    exec(compile(body,path,'exec'),m.__dict__)
    return m

def definitions(body,path,names,env,class_name=None,constant=False):
    tree=ast.parse(body,filename=path)
    parent=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==class_name) if class_name else tree
    nodes=[n for n in parent.body if isinstance(n,ast.FunctionDef) and n.name in names]
    need({n.name for n in nodes}==names,'Missing exact original function closure')
    if constant:
        nodes=[n for n in tree.body if isinstance(n,ast.Assign) and
               any(isinstance(t,ast.Name) and t.id=='DEFAULT_FOV_RAD' for t in n.targets)]+nodes
    exec(compile(ast.Module(body=nodes,type_ignores=[]),path,'exec'),env)


def main():
    if sys.argv[1:]==['--compile-only']:
        compile(Path(__file__).read_bytes(),__file__,'exec');print('COMPILE_ONLY_NO_SCIENTIFIC_READ');return 0
    cb=(D/'RUN_CONTRACT.json').read_bytes()
    need(len(sys.argv)==2 and sha(cb)==sys.argv[1],'Expected frozen contract SHA')
    c=json.loads(cb);out=D/'execution_01';out.mkdir(exist_ok=False)
    begin=time.monotonic();reads=[]
    r=dict(schema='s76-single-yaw-generation-v1',started_utc=utc(),status='RUNNING',
           contract_sha256=sha(cb),source_sha256=sha(Path(__file__).read_bytes()),reads=reads,steps=[],
           arrays={},new_generation_arms=1,reused_baseline='S70_A0',new_method_validated=False)
    write(out/'started.json',dict(started_utc=r['started_utc'],pid=os.getpid(),contract_sha256=sha(cb)))
    model=ae=baseline=None;s70=None;success=False
    def progress(phase,**detail):
        with (out/'progress.jsonl').open('a') as f:
            f.write(json.dumps(dict(utc=utc(),phase=phase,elapsed_seconds=time.monotonic()-begin,pid=os.getpid(),**detail))+'\n');f.flush()
    def read(item,kind):
        b=Path(item['path']).read_bytes();h=sha(b)
        reads.append(dict(path=item['path'],kind=kind,bytes=len(b),sha256=h))
        need(h==item['sha256'] and ('size' not in item or len(b)==item['size']),'Input identity differs: '+item['path'])
        return b
    def budget():
        need(time.monotonic()-begin<=c['limits']['worker_seconds'],'Worker wall budget exceeded')
        need(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<=c['limits']['rss_bytes'],'Self RSS budget exceeded')
        need(shutil.disk_usage(out).free>=c['limits']['minimum_free_bytes'],'Free disk below fixed minimum')
    try:
        progress('start');need(sys.platform=='darwin' and sys.version.split()[0]==c['python_version'],'Runtime differs')
        accepted=json.loads(read(c['old_acceptance'],'S70_accepted_metadata'))
        verified=json.loads(read(c['old_generation_review'],'S70_generation_review'))
        old=json.loads(read(c['old_worker_receipt'],'S70_worker_metadata'))
        need(accepted['status']=='ACCEPTED_S70_INDEPENDENT_GENERATION_AND_FIXED_RGB_SCORE'
             and accepted['replay_pass'] is True,'Old A0 acceptance/replay unavailable')
        need(accepted['files_sha256']['generation_verification_01/receipt.json']==c['old_generation_review']['sha256'],
             'Old verification binding differs')
        need(verified['status']=='PASS_S70_INDEPENDENT_GENERATION_RESULT_REVIEW' and not verified['blockers']
             and verified['evidence']['worker_receipt']['sha256']==c['old_worker_receipt']['sha256'],
             'Old worker accepted identity differs')
        need(old['status']=='COMPLETE_THREE_FIXED_GENERATION_ARMS' and old['exact_replay_pass']
             and old['shared_actual_random_stream_pass'],'Old A0 stream/replay unavailable')
        a0=old['arms']['A0'];need(a0['status']=='COMPLETE_ARM' and len(a0['steps'])==50,'Old A0 incomplete')
        s70=module_from_bytes('s76_reused_s70',c['s70_source']['path'],read(c['s70_source'],'immutable_S70_worker_source'))
        rules=module_from_bytes('s76_pilot_rules',c['rules_source']['path'],read(c['rules_source'],'frozen_pilot_rules'))
        old_manifest=json.loads(read(c['s70_manifest'],'S70_input_metadata'))
        need(verified['evidence']['reviewed_source_sha256']['generate_fixed_contexts.py']==c['s70_source']['sha256']
             and old['input_sha256']==c['s70_manifest']['sha256'],'Original source/input binding differs')
        np,torch,modules,util,versions=s70.load_code(old_manifest,reads)
        torch.set_num_threads(8);torch.set_num_interop_threads(1);torch.set_default_dtype(torch.float32)
        r.update(versions=versions,variant=old_manifest['variant'])
        manifest=dict(old_manifest);manifest['conditions']={'geometry':old_manifest['conditions']['geometry']}
        data=s70.read_conditions(manifest,reads,np)['geometry']
        need(data['ordered_ids'].tolist()==rules.ORDERED_IDS,'Unexpected A0 slots')
        from einops import repeat
        env=dict(torch=torch,np=np,repeat=repeat)
        definitions(read(c['camera_util_source'],'original_camera_helpers'),c['camera_util_source']['path'],HELPERS,env,constant=True)
        definitions(read(c['pipeline_source'],'original_consumer_methods'),c['pipeline_source']['path'],METHODS,env,class_name='VMemPipeline')
        Consumer=type('OriginalConsumerMethods',(),{k:env[k] for k in METHODS})
        consumer=Consumer();consumer.device='cpu';consumer.dtype=torch.float32;consumer.camera_scale=2.0
        consumer.config=types.SimpleNamespace(model=types.SimpleNamespace(num_frames=8))
        original=torch.from_numpy(data['optical_c2ws_fp32'].copy())
        with torch.inference_mode():
            changed,Q=rules.target_local_yaw(original,data['ordered_ids'].tolist(),torch)
            raw=changed @ torch.diag(torch.tensor([1.,-1.,-1.,1.],dtype=torch.float32))
            scale,centered=consumer.get_translation_scaling_factor(raw.clone())
            need(torch.equal(torch.as_tensor(scale).reshape(()),torch.from_numpy(data['scale'].copy()).reshape(())),'Natural scale changed')
            result=consumer.get_cond(torch.from_numpy(data['context_latents'].copy()),centered,
                torch.from_numpy(data['K_pixels_576'].copy()),scale,
                torch.from_numpy(data['context_embeddings'].copy()),torch.from_numpy(data['input_masks'].copy()))
        need(set(result)=={'c','uc','all_c2ws','all_Ks','input_masks','num_cameras'} and result['num_cameras']==8,'Consumer schema differs')
        need(torch.equal(result['all_c2ws'][:4],torch.from_numpy(data['post_cond_optical_c2ws'][:4].copy()))
             and torch.equal(result['all_c2ws'][:,:3,3],torch.from_numpy(data['post_cond_optical_c2ws'][:,:3,3].copy()))
             and torch.equal(result['all_Ks'],torch.from_numpy(data['K_pixels_576'].copy()))
             and torch.equal(result['input_masks'],torch.from_numpy(data['input_masks'].copy())),
             'History camera, center, K or mask changed')
        for group in ['c','uc']:
            need(set(result[group])==set(FIELDS),'Condition keys differ')
            for field in FIELDS:
                value=result[group][field];prior=torch.from_numpy(data[group+'__'+field].copy())
                need(value.shape==prior.shape and value.dtype==torch.float32 and bool(torch.isfinite(value).all()),'Invalid new condition')
                if field in ['crossattn','replace']:
                    need(torch.equal(value,prior),'Appearance condition changed')
                else:
                    need(torch.equal(value[:4],prior[:4]),'History rays changed')
                    if field=='concat':need(torch.equal(value[:,0],prior[:,0]),'Mask channel changed')
        need(torch.equal(result['c']['dense_vector'],result['uc']['dense_vector']),'c/uc ray mismatch')
        need(not torch.equal(result['c']['dense_vector'][4:],torch.from_numpy(data['c__dense_vector'][4:].copy())),'Yaw did not change target rays')
        Hs=rules.prescribed_homographies(data['optical_c2ws_fp32'],changed.numpy(),data['K_pixels_576'],np)
        pre=dict(old_optical=data['optical_c2ws_fp32'],new_optical=changed.numpy(),K_pixels_576=data['K_pixels_576'],
                 H_old_to_new=np.stack(Hs),ordered_ids=data['ordered_ids'],local_yaw_Q=Q.numpy())
        before=dict(post_cond_optical_c2ws=result['all_c2ws'].numpy(),K_pixels_576=result['all_Ks'].numpy(),
                    input_masks=result['input_masks'].numpy())
        for group in ['c','uc']:before.update({group+'__'+field:result[group][field].numpy() for field in FIELDS})
        masks=[];fov=[]
        for hid,H in zip(rules.TARGET_IDS,Hs):
            ma,mb=rules.common_fov_masks(H,np);masks.append((ma,mb))
            fov.append(dict(target_id=hid,H=H.tolist(),old_common_pixels=int(ma.sum()),new_common_pixels=int(mb.sum()),
                            total_pixels=576*576,old_fraction=float(ma.mean()),new_fraction=float(mb.mean())))
        pre['old_common_fov_masks']=np.stack([a for a,b in masks]);pre['new_common_fov_masks']=np.stack([b for a,b in masks])
        for name,arrays in [('prescribed_geometry',pre),('new_conditions',before)]:
            with (out/(name+'.npz')).open('xb') as f:np.savez(f,**arrays)
            r[name]=dict(path=str(out/(name+'.npz')),sha256=sha((out/(name+'.npz')).read_bytes()),
                        fields={k:s70.array_info(np.ascontiguousarray(v)) for k,v in arrays.items()})
        r['fov']=fov;r['all_nonintervened_conditions_exact']=True
        write(out/'PRE_GENERATION_GEOMETRY.json',dict(completed_utc=utc(),prescribed_geometry=r['prescribed_geometry'],
            new_conditions=r['new_conditions'],fov=fov,nonintervened_conditions_exact=True))
        budget();progress('geometry_prepared')
        model,ae=s70.load_models(old_manifest,reads,modules,torch,out,r,progress)
        baseline=s70.model_snapshot({'vmem':model,'vae':ae},torch)
        need(baseline['value_sha256']==a0['model_before']['value_sha256'] and baseline['modes_sha256']==a0['model_before']['modes_sha256'],
             'Cross-process model value/modes differ from A0')
        r['model_before']={k:baseline[k] for k in ['value_sha256','identity_sha256','modes_sha256']}
        r['model_baseline']=s70.write_json(out/'model_baseline.json',baseline)
        budget()
        common_item=dict(path=old['common_rng']['path'],sha256=old['common_rng']['sha256'],size=old['common_rng']['size_bytes'])
        common=json.loads(read(common_item,'S70_actual_pre_sampling_RNG_state'))
        sampling=modules['modeling.sampling'];discretization=sampling.DDPMDiscretization()
        denoiser=sampling.DiscreteDenoiser(discretization,num_idx=1000,device='cpu')
        sampler=sampling.create_samplers(guider_types=1,discretization=discretization,num_frames=8,num_steps=50,cfg_min=1.2,device='cpu')[0]
        need(type(sampler.guider).__name__=='MultiviewCFG','Wrong original guidance')
        original_step=sampler.sampler_step
        def observed_step(*args,**kwargs):
            budget();step=len(r['steps'])+1;need(step<=50,'Extra sampler step')
            item=dict(step=step,started_utc=utc(),rng_before=s70.rng_sha(np,torch))
            progress('step_start',step=step,rng_before=item['rng_before'])
            need(item['rng_before']==a0['steps'][step-1]['rng_before'],'Step entry RNG differs')
            try:
                value=original_step(*args,**kwargs)
            except Exception as error:
                item.update(failed_utc=utc(),rng_after=s70.rng_sha(np,torch),
                            error_type=type(error).__name__,error=str(error))
                with (out/'steps.jsonl').open('a') as f:f.write(json.dumps(item)+'\n');f.flush()
                r['failed_step']=item
                raise
            item.update(completed_utc=utc(),rng_after=s70.rng_sha(np,torch),finite=bool(torch.isfinite(value).all()))
            r['steps'].append(item)
            with (out/'steps.jsonl').open('a') as f:f.write(json.dumps(item)+'\n');f.flush()
            need(item['rng_after']==a0['steps'][step-1]['rng_after'] and item['finite'],'Step RNG/finite mismatch')
            progress('step',step=step);budget();return value
        sampler.sampler_step=observed_step;calls=[]
        def observed_sampler(denoiser_call,noise,**kwargs):
            need(not calls,'Repeated sampler invocation');calls.append(1)
            r['noise']=s70.save_array(out/'noise.npy',noise.detach().cpu().numpy().copy(),np)
            r['sampler_entry_rng_state_sha256']=s70.rng_sha(np,torch)
            need(r['noise']['body_sha256']==a0['noise']['body_sha256']
                 and r['sampler_entry_rng_state_sha256']==a0['sampler_entry_rng_state_sha256'],'Initial noise or sampler-entry state differs')
            s70.write_json(out/'sampler_entry_rng.json',s70.rng_json(s70.rng_capture(np,torch)))
            value=sampler(denoiser_call,noise,**kwargs)
            r['arrays']['all8_latents']=s70.save_array(out/'all8_latents.npy',value.detach().cpu().numpy(),np)
            return value
        r['sampling_started_utc']=utc();progress('sampling_start')
        rules.restore_common_rng(common,old['common_rng_state_sha256'],np,torch,
                                 lambda:s70.rng_json(s70.rng_capture(np,torch)))
        r['restored_common_rng_state_sha256']=s70.rng_sha(np,torch)
        samples,latents=util['do_sample'](model,ae,denoiser,observed_sampler,result['c'],result['uc'],
            result['all_c2ws'],result['all_Ks'],result['input_masks'],H=576,W=576,C=4,F=8,T=8,cfg=2.0,
            decoding_t=1,verbose=True,global_pbar=None,return_latents=True,device='cpu')
        r['terminal_rng_state_sha256']=s70.rng_sha(np,torch)
        r['terminal_rng']=s70.write_json(out/'terminal_rng.json',s70.rng_json(s70.rng_capture(np,torch)))
        target=samples[~result['input_masks']]
        r['arrays']['targets_fp32']=s70.save_array(out/'targets_fp32.npy',target.detach().cpu().numpy(),np)
        need(samples.shape==(8,3,576,576) and samples.dtype==torch.float32 and bool(torch.isfinite(samples).all()),'Invalid full8 decoded output')
        need(latents.shape==(8,4,72,72) and latents.dtype==torch.float32 and bool(torch.isfinite(latents).all()),'Invalid latent output')
        quantized=np.stack([np.array(util['tensor_to_pil'](frame)) for frame in target])
        r['arrays']['targets_uint8']=s70.save_array(out/'targets_uint8.npy',quantized,np)
        r['quantizer']=[dict(target_id=i,raw_min=float(frame.min()),maps_minus1_plus1=bool(frame.min()<-.1))
                        for i,frame in zip(rules.TARGET_IDS,target)]
        need(r['terminal_rng_state_sha256']==a0['terminal_rng_state_sha256'],'Terminal RNG differs')
        need(len(r['steps'])==50 and len(calls)==1,'Incomplete original sampling')
        after=s70.model_snapshot({'vmem':model,'vae':ae},torch)
        r['model_after']={k:after[k] for k in r['model_before']}
        need(r['model_after']==r['model_before'],'New process model changed')
        r.update(status='COMPLETE_SINGLE_YAW_FIXED_STREAM',stream_identity_pass=True,model_unchanged=True,
                 target_ids=rules.TARGET_IDS,generated_images_viewed=False,all4_targets_preserved=True)
        budget();success=True;progress('complete')
    except Exception as e:
        r.update(status='FAILED_SINGLE_YAW',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc())
        progress('failure',error_type=type(e).__name__,error=str(e))
    finally:
        r.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-begin,
                 peak_self_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                 no_new_baseline=True,reference_RGB_or_depth_bytes=0)
        write(out/'receipt.json',r)
        for p in out.rglob('*'):
            if p.is_file() and not p.is_symlink():p.chmod(0o444)
    print(json.dumps(dict(status=r['status'],output=str(out),elapsed_seconds=r['elapsed_seconds'])),flush=True)
    return 0 if success else 1

if __name__=='__main__':raise SystemExit(main())
