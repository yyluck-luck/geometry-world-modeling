"""S86: original VMem + one frozen warp; two chains and two derived controls.

No reference images, geometry recomputation, retrieval, or parameter search.
Uses verified S70 helpers without invoking its original experiment entrypoint.
"""
import datetime as dt
import gc
import hashlib
import io
import json
import os
from pathlib import Path
import random
import resource
import shutil
import signal
import sys
import time
import traceback
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def require(ok, why):
    if not bool(ok):
        raise RuntimeError(why)


def write(path, obj):
    with path.open('x') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def main():
    raw_contract = (HERE/'CONTRACT.json').read_bytes()
    cfg = json.loads(raw_contract)
    require(sha(Path(__file__).read_bytes()) == cfg['runner_sha256'], 'runner identity')
    require(cfg['strengths'] == [0.25]*50 and cfg['final_strength'] == 0.25, 'fixed exploratory strength')
    require([s['target_id'] for s in cfg['warps']]==[20,21,22,23], 'fixed warp order')
    out = HERE/'execution_01'
    require(str(out) == cfg['output_directory'], 'fixed output directory')
    out.mkdir(exist_ok=False)
    started = time.monotonic()
    reads, arms = [], {}
    report = dict(status='STARTED', started_utc=now(), contract_sha256=sha(raw_contract),
                  reads=reads, arms=arms, new_method_validated=False,
                  reference_RGB_reads=0, sensor_depth_reads=0,
                  geometry_or_retrieval_calls=0, optimizer_calls=0,
                  full_chain_calls=0, warp_encoder_calls=0, derived_decoder_calls=0,
                  component_load_events=[], components_loaded=[])
    log = (out/'progress.jsonl').open('x', buffering=1)
    arm_name, arm_start = None, None

    def progress(phase, step=None, **kw):
        if phase == 'load':
            report['component_load_events'].append(dict(utc=now(), **kw))
        log.write(json.dumps(dict(phase=phase, utc=now(), pid=os.getpid(),
                                 arm=arm_name, step=step,
                                 elapsed_seconds=time.monotonic()-started,
                                 arm_elapsed_seconds=None if arm_start is None else time.monotonic()-arm_start,
                                 **kw), allow_nan=False)+'\n')

    def budget():
        require(time.monotonic()-started < cfg['budget']['total_seconds'], 'total wall budget')
        require(arm_start is None or time.monotonic()-arm_start < cfg['budget']['per_arm_seconds'], 'arm wall budget')
        require(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < cfg['budget']['rss_bytes'], 'sampled self RSS')
        require(shutil.disk_usage(out).free >= cfg['budget']['minimum_free_bytes'], 'disk reserve')

    def bound(spec, kind):
        p = Path(spec['path']); data = p.read_bytes()
        actual = dict(path=str(p), sha256=sha(data), bytes=len(data), kind=kind)
        reads.append(actual)
        require(actual['sha256'] == spec['sha256'] and len(data) == spec['bytes'], 'input identity: '+str(p))
        return data

    def module(spec, name):
        data = bound(spec, 'source')
        obj = types.ModuleType(name); obj.__file__ = spec['path']
        sys.modules[name] = obj
        exec(compile(data, spec['path'], 'exec'), obj.__dict__)
        return obj

    try:
        def terminated(signum, frame):
            raise RuntimeError('external termination signal '+str(signum))
        signal.signal(signal.SIGTERM, terminated)
        progress('start')
        prior = module(cfg['s70_helper'], 's86_verified_s70_helpers')
        original_manifest = json.loads(bound(cfg['s70_inputs'], 'source_manifest'))
        manifest = dict(original_manifest)
        manifest['conditions'] = {'geometry': original_manifest['conditions']['geometry']}
        np, torch, modules, util, versions = prior.load_code(manifest, reads)
        report.update(versions=versions, python=sys.version, variant=manifest['variant'],
                      controls=cfg['controls'], claim_boundary=cfg['claim_boundary'])
        torch.set_num_threads(8); torch.set_num_interop_threads(1)
        torch.set_default_dtype(torch.float32)
        hooks = module(cfg['hooks'], 's86_sampler_hooks')
        fusion = module(cfg['fusion'], 's86_original_pure_fusion').fuse_clean_prediction
        for spec in cfg['acceptance_metadata']:
            bound(spec, 'accepted_metadata')
        conditions = prior.read_conditions(manifest, reads, np)['geometry']
        require(conditions['ordered_ids'].tolist() == [19,18,13,12,20,21,22,23], 'fixed slot identities')
        require(conditions['input_masks'].tolist() == [True]*4+[False]*4, 'fixed slots')

        def save_array(path, array):
            return prior.save_array(path, np.ascontiguousarray(array), np)

        def tensor_info(tensor):
            return prior.array_info(np.ascontiguousarray(tensor.detach().cpu().numpy()))

        def save_npz(path, tensors):
            arrays = {k: np.ascontiguousarray(v.detach().cpu().numpy()) for k,v in tensors.items()}
            with path.open('xb') as f:
                np.savez(f, **arrays)
            return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path.read_bytes()),
                        fields={k:prior.array_info(v) for k,v in arrays.items()})

        rgb, masks = [], []
        for spec in cfg['warps']:
            raw = bound(spec, 'saved_warp_rgb_and_mask')
            with np.load(io.BytesIO(raw), allow_pickle=False) as z:
                a, m = z['warp_rgb'], z['mask']
            require(a.shape == (576,576,3) and a.dtype == np.float32, 'warp RGB schema')
            require(m.shape == (576,576) and m.dtype == np.bool_, 'warp mask schema')
            require(np.isfinite(a).all() and ((a>=0)&(a<=1)).all() and (a[~m]==0).all(), 'warp range/hole fill')
            rgb.append(a); masks.append(m)
        warp_rgb = torch.from_numpy(np.stack(rgb)).permute(0,3,1,2).contiguous()
        image_mask = torch.from_numpy(np.stack(masks))[:,None].contiguous()
        del rgb, masks, raw, a, m
        report['warp_rgb'] = save_array(out/'warp_rgb01.npy', warp_rgb.numpy())
        report['image_mask'] = save_array(out/'image_mask.npy', image_mask.numpy())
        budget()
        model, ae = prior.load_models(manifest, reads, modules, torch, out, report, progress)
        report['components_loaded'] = ['VMem', 'VAE']
        baseline = prior.model_snapshot({'vmem':model,'vae':ae}, torch)
        write(out/'model_baseline.json', baseline)
        baseline_keys = ('value_sha256','identity_sha256','modes_sha256')
        baseline_id = {k:baseline[k] for k in baseline_keys}
        del baseline
        encode_start = time.monotonic(); progress('encode_warp')
        with torch.inference_mode(), torch.autocast(device_type='cpu', enabled=False):
            encoder_input = warp_rgb*2-1
            require((encoder_input.permute(0,2,3,1)[~image_mask[:,0]] == -1).all(), 'black holes encode as -1')
            report['encoder_input'] = save_array(out/'encoder_input.npy', encoder_input.numpy())
            report['warp_encoder_calls'] += 1
            encoded = ae.encode(encoder_input, 1)
            require(encoded.shape == (4,4,72,72) and encoded.dtype == torch.float32 and torch.isfinite(encoded).all(), 'warp encoded output')
            warp_latents = torch.cat([torch.zeros_like(encoded), encoded], 0)
            area = torch.nn.functional.avg_pool2d(image_mask.float(), 8, 8)
            latent_mask = torch.cat([torch.zeros_like(area), area], 0)
            history = torch.from_numpy(conditions['input_masks'].copy())
        report['encoded_warp'] = save_npz(out/'ENCODED_WARP.npz', dict(warp_latents=warp_latents, support_mask=latent_mask, history_slots=history))
        report['warp_encode_seconds'] = time.monotonic()-encode_start
        report['warp_encode_chunks'] = 4
        del encoded, encoder_input, area
        progress('encoded_warp', seconds=report['warp_encode_seconds'])
        # Compare one complete snapshot, not a separate weight pass for each key.
        snap = prior.model_snapshot({'vmem':model,'vae':ae}, torch)
        require({k:snap[k] for k in baseline_keys} == baseline_id, 'model changed by warp encoding')
        del snap
        random.seed(44); np.random.seed(44); torch.manual_seed(44)
        common = prior.rng_capture(np, torch)
        write(out/'common_rng.json', prior.rng_json(common))
        report['common_rng_sha256'] = prior.sha(prior.encoded(prior.rng_json(common)))
        sampling = modules['modeling.sampling']
        saved_g0 = None

        def emit(adir, targets):
            require(targets.shape == (4,3,576,576) and targets.dtype == torch.float32 and torch.isfinite(targets).all(), 'target RGB schema')
            arrays = dict(targets_fp32=save_array(adir/'targets_fp32.npy', targets.numpy()))
            quantized = np.stack([np.array(util['tensor_to_pil'](frame)) for frame in targets])
            arrays['targets_uint8'] = save_array(adir/'targets_uint8.npy', quantized)
            branches = [dict(target_id=t, raw_min=float(f.min()), raw_max=float(f.max()), maps_minus1_plus1=bool(f.min() < -.1)) for t,f in zip([20,21,22,23],targets)]
            return arrays, branches

        for arm_name in ('G0','Gguide'):
            arm_start = time.monotonic(); adir = out/arm_name; adir.mkdir()
            result = dict(status='STARTED', started_utc=now(), arrays={}, steps=[], clean_trace=[], model_before=baseline_id)
            arms[arm_name] = result; progress('arm_start', step=0)
            data = {k:torch.from_numpy(v.copy()) for k,v in conditions.items()}
            c = {k:data['c__'+k] for k in prior.FIELDS}; uc = {k:data['uc__'+k] for k in prior.FIELDS}
            disc = sampling.DDPMDiscretization()
            denoiser = sampling.DiscreteDenoiser(disc, num_idx=1000, device='cpu')
            sampler = sampling.create_samplers(guider_types=1, discretization=disc, num_frames=8, num_steps=50, cfg_min=1.2, device='cpu')[0]
            require(type(sampler.guider).__name__ == 'MultiviewCFG', 'original guider type')
            if arm_name == 'Gguide':
                (adir/'clean_steps').mkdir()

            def on_clean(step, raw_clean, used_clean):
                callback_rng = prior.rng_sha(np,torch)
                row = dict(step=int(step), original_object=raw_clean is used_clean,
                           raw=tensor_info(raw_clean), used=tensor_info(used_clean))
                protected = ((latent_mask == 0) | history[:,None,None,None]).expand_as(raw_clean)
                raw_bytes = raw_clean[protected].contiguous().numpy().tobytes()
                used_bytes = used_clean[protected].contiguous().numpy().tobytes()
                require(raw_bytes == used_bytes, 'direct fusion changed protected clean values')
                row['protected_clean_exact'] = True
                if arm_name == 'G0':
                    require(raw_clean is used_clean and row['raw']==row['used'], 'G0 hook altered CFG output')
                else:
                    row['archive'] = save_npz(adir/'clean_steps'/f'step_{step:03d}.npz', dict(raw_clean=raw_clean, used_clean=used_clean))
                require(prior.rng_sha(np,torch)==callback_rng, 'clean callback changed RNG')
                row['callback_rng_unchanged'] = True
                result['clean_trace'].append(row)

            controller = hooks.install_hooks(sampler, mode=arm_name, expected_steps=50,
                fusion_fn=fusion, warp_latents=warp_latents, support_mask=latent_mask,
                history_slots=history, strengths=cfg['strengths'] if arm_name=='Gguide' else None,
                on_clean=on_clean)
            hooked_step = sampler.sampler_step

            def observed_step(*args, **kwargs):
                budget(); step = len(result['steps'])+1
                row = dict(step=step, started_utc=now(), rng_before=prior.rng_sha(np,torch))
                try:
                    value = hooked_step(*args, **kwargs)
                    require(torch.isfinite(value).all(), 'nonfinite sampler output')
                    row.update(status='COMPLETE', completed_utc=now(), rng_after=prior.rng_sha(np,torch))
                    return value
                except Exception as e:
                    row.update(status='FAILED', completed_utc=now(), rng_after=prior.rng_sha(np,torch), error=str(e)); raise
                finally:
                    result['steps'].append(row)
                    with (adir/'steps.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
                    progress('step', step=step, status=row['status'])
            sampler.sampler_step = observed_step
            calls = []

            def observed_sampler(denoiser_call, noise, **kwargs):
                require(not calls, 'multiple sampler calls');calls.append(1)
                result['noise'] = save_array(adir/'noise.npy', noise.detach().numpy())
                result['entry_rng'] = prior.rng_sha(np,torch)
                write(adir/'entry_rng.json',prior.rng_json(prior.rng_capture(np,torch)))
                report['full_chain_calls'] += 1
                value = sampler(denoiser_call, noise, **kwargs)
                result['arrays']['all8_latents'] = save_array(adir/'all8_latents.npy',value.detach().numpy())
                return value

            try:
                snap = prior.model_snapshot({'vmem':model,'vae':ae}, torch)
                require({k:snap[k] for k in baseline_keys} == baseline_id, 'model changed before arm'); del snap
                random.setstate(common[0]);np.random.set_state(common[1]);torch.set_rng_state(common[2].clone())
                result['restored_rng'] = prior.rng_sha(np,torch)
                require(result['restored_rng']==report['common_rng_sha256'], 'common RNG restore')
                samples, latents = util['do_sample'](model,ae,denoiser,observed_sampler,c,uc,
                    data['post_cond_optical_c2ws'],data['K_pixels_576'],data['input_masks'],
                    H=576,W=576,C=4,F=8,T=8,cfg=2.0,decoding_t=1,
                    verbose=False,global_pbar=None,return_latents=True,device='cpu')
                controller.assert_complete()
                require(len(result['clean_trace'])==50 and len(result['steps'])==50, 'full step capture')
                require(samples.shape==(8,3,576,576) and samples.dtype==torch.float32 and torch.isfinite(samples).all(), 'full8 decode')
                more, branches = emit(adir,samples[~history]);result['arrays'].update(more);result['quantizer']=branches
                last = controller.last
                result['last_step'] = save_npz(adir/'LAST_STEP.npz',{k:v for k,v in last.items() if isinstance(v,torch.Tensor)})
                result['hook_steps'] = controller.steps
                result['last_metadata'] = {k:v for k,v in last.items() if not isinstance(v,torch.Tensor)}
                if arm_name=='G0':
                    saved_g0 = dict(last=last, targets=samples[~history].clone(), latents=latents.clone())
                result['status']='COMPLETE_CHAIN'
                del samples,latents
            except BaseException as e:
                result.update(status='FAILED_CHAIN',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),hook_steps=controller.steps)
                if controller.last:
                    result['partial_last_metadata']={k:v for k,v in controller.last.items() if not isinstance(v,torch.Tensor)}
                    result['partial_last_step']=save_npz(adir/'PARTIAL_LAST_STEP.npz',{k:v for k,v in controller.last.items() if isinstance(v,torch.Tensor)})
                raise
            finally:
                result['hook_steps']=controller.steps
                result['terminal_rng']=prior.rng_sha(np,torch)
                write(adir/'terminal_rng.json',prior.rng_json(prior.rng_capture(np,torch)))
                snap=prior.model_snapshot({'vmem':model,'vae':ae},torch)
                result['model_after']={k:snap[k] for k in baseline_keys};del snap
                result['model_unchanged']=result['model_after']==baseline_id
                result.update(completed_utc=now(),elapsed_seconds=time.monotonic()-arm_start)
                write(adir/'receipt.json',result)
            require(result['model_unchanged'], 'model state prevents further arms')
            require(result['status']=='COMPLETE_CHAIN', 'incomplete full chain')
            progress('arm_complete',step=50)
            budget();gc.collect()

        arm_name,arm_start=None,None
        def signature(a):
            return dict(noise=a['noise']['body_sha256'],entry=a['entry_rng'],
                steps=[(v['rng_before'],v['rng_after']) for v in a['steps']],terminal=a['terminal_rng'])
        report['shared_actual_random_stream']=signature(arms['G0'])==signature(arms['Gguide'])
        require(report['shared_actual_random_stream'],'actual random streams differ')
        progress('derived_controls')
        with torch.inference_mode(),torch.autocast(device_type='cpu',enabled=False):
            before_rng=prior.rng_sha(np,torch)
            zero=hooks.replay_last(sampling,saved_g0['last'])
            require(tensor_info(zero['latents'])==tensor_info(saved_g0['latents']),'unfused last Euler replay differs')
            report['G0_last_replay_exact']=True
            for arm_name in ('Gpaste','Gterminal'):
                arm_start=time.monotonic();adir=out/arm_name;adir.mkdir()
                result=dict(status='STARTED',started_utc=now(),full_chain_calls=0,arrays={});arms[arm_name]=result
                try:
                    if arm_name=='Gpaste':
                        target_rgb01=torch.stack([(f+1)/2 if f.min()<-.1 else f for f in saved_g0['targets']]).clamp(0,1)
                        w=image_mask.to(torch.float32)*cfg['final_strength']
                        targets=torch.where(w>0,(1-w)*target_rgb01+w*warp_rgb,target_rgb01)
                        result['RGB_domain']='RGB01; G0 branch conversion then clamp before composition'
                    else:
                        terminal=hooks.replay_last(sampling,saved_g0['last'],fusion_fn=fusion,
                            warp_latents=warp_latents,support_mask=latent_mask,history_slots=history,strength=cfg['final_strength'])
                        result['replayed_state']=save_npz(adir/'TERMINAL_STATE.npz',terminal)
                        result['arrays']['all8_latents']=save_array(adir/'all8_latents.npy',terminal['latents'].numpy())
                        report['derived_decoder_calls']+=1
                        targets=ae.decode(terminal['latents'],1)[~history]
                        result['decode_chunks']=8
                    result['arrays'].update(emit(adir,targets)[0])
                    result['quantizer']=[dict(target_id=i,raw_min=float(f.min()),raw_max=float(f.max()),maps_minus1_plus1=bool(f.min()<-.1)) for i,f in zip([20,21,22,23],targets)]
                    result['status']='COMPLETE_DERIVED'
                except BaseException as e:
                    result.update(status='FAILED_DERIVED',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc())
                    raise
                finally:
                    result.update(completed_utc=now(),elapsed_seconds=time.monotonic()-arm_start)
                    write(adir/'receipt.json',result)
                progress('derived_complete');budget()
            require(prior.rng_sha(np,torch)==before_rng,'derived controls changed RNG')
            report['derived_rng_unchanged']=True
        arm_name,arm_start=None,None
        snap=prior.model_snapshot({'vmem':model,'vae':ae},torch)
        report['final_model_state']={k:snap[k] for k in baseline_keys}
        require(report['final_model_state']==baseline_id,'final model changed')
        report['status']='COMPLETE_FOUR_FIXED_CONSUMER_ARMS_PENDING_REVIEW'
    except BaseException as e:
        report.update(status='FAILED_PARTIAL_PRESERVED',error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc())
        progress('failure',error=str(e))
    finally:
        report.update(completed_utc=now(),elapsed_seconds=time.monotonic()-started,
            peak_self_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            unrun_arms=[a for a in ('G0','Gguide','Gpaste','Gterminal') if a not in arms])
        progress('complete',status=report['status']);log.close()
        report['progress_sha256']=sha((out/'progress.jsonl').read_bytes())
        write(out/'RECEIPT.json',report)
    print(json.dumps(dict(status=report['status'],path=str(out/'RECEIPT.json'))),flush=True)
    return 0 if report['status']=='COMPLETE_FOUR_FIXED_CONSUMER_ARMS_PENDING_REVIEW' else 1


if __name__=='__main__':
    raise SystemExit(main())
