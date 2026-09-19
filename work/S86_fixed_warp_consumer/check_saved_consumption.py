"""Independent NumPy review of sealed S86 consumption; no author imports/models/GT.

Execution requires root's exact post-completion binding; this file alone never
finds a newer receipt or substitutes another run. One create-only review output.
"""
import argparse
import datetime as dt
import hashlib
import io
import json
from pathlib import Path
import resource
import signal
import sys
import time
import traceback
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / 'execution_01'
GENERATION_CONTRACT = '954c4353745280d5d3f48ac9db124b8a23aa877e1c59e9ecdd13f399416e844f'
LATENT = (8, 4, 72, 72)
RGB = (4, 3, 576, 576)
LAST_KEYS = {'sigma', 'next_sigma', 'x_tilde', 'sigma_hat', 'raw_clean', 'used_clean', 'output'}
READS, CHECKS = [], []
STARTED = time.monotonic()


def require(ok, message):
    if not bool(ok):
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def budget():
    require(time.monotonic()-STARTED < 300, 'review wall budget')
    require(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < 4*1024**3, 'review RSS budget')


def read(path, expected=None, size=None):
    budget()
    path = Path(path)
    blob = path.read_bytes()
    row = dict(path=str(path), sha256=digest(blob), bytes=len(blob))
    READS.append(row)
    require(expected is None or row['sha256'] == expected, 'file SHA: '+str(path))
    require(size is None or len(blob) == size, 'file size: '+str(path))
    return blob


def meta(path, expected=None):
    return json.loads(read(path, expected))


def info(a):
    a = np.ascontiguousarray(a)
    return dict(shape=list(a.shape), dtype=str(a.dtype), body_bytes=a.nbytes,
                body_sha256=digest(a.tobytes()))


def shape(a, dims, dtype, label):
    require(a.shape == tuple(dims) and a.dtype == np.dtype(dtype), 'schema: '+label)
    require(np.isfinite(a).all(), 'finite: '+label)


def equal(label, actual, expected):
    require(actual.shape == expected.shape and actual.dtype == expected.dtype, 'schema: '+label)
    ok = np.ascontiguousarray(actual).tobytes() == np.ascontiguousarray(expected).tobytes()
    CHECKS.append(dict(label=label, rule='exact_bytes', elements=actual.size, pass_check=ok))
    require(ok, 'byte mismatch: '+label)


def numerical(label, actual, expected, magnitude):
    shape(actual, expected.shape, 'float32', label)
    require(np.isfinite(expected).all(), 'nonfinite independent calculation: '+label)
    error = np.abs(actual.astype(np.float64)-expected.astype(np.float64))
    # Fixed FP32 arithmetic envelope, never a scientific quality threshold.
    bound = 8*np.finfo(np.float32).eps*np.asarray(magnitude, dtype=np.float64)
    bound += 8*np.finfo(np.float32).smallest_subnormal
    ok = bool((error <= bound).all())
    CHECKS.append(dict(label=label, rule='8eps_operand_magnitude_plus_8minsubnormal',
        elements=actual.size, nonzero_differences=int(np.count_nonzero(error)),
        max_abs_difference=float(error.max(initial=0)), max_bound=float(np.max(bound)), pass_check=ok))
    require(ok, 'arithmetic mismatch: '+label)


def array(spec, path, dims, dtype):
    require(spec['path'] == str(path), 'array fixed path')
    a = np.load(io.BytesIO(read(path, spec['file_sha256'])), allow_pickle=False)
    shape(a, dims, dtype, str(path))
    require(info(a) == {k:spec[k] for k in info(a)}, 'array descriptor: '+str(path))
    return a


def archive(spec, path, expected_schema):
    require(spec['path'] == str(path), 'archive fixed path')
    blob = read(path, spec['sha256'], spec['bytes'])
    with np.load(io.BytesIO(blob), allow_pickle=False) as z:
        require(set(z.files) == set(expected_schema) == set(spec['fields']), 'archive exact keys')
        arrays = {k:z[k] for k in z.files}
    for k, a in arrays.items():
        shape(a, *expected_schema[k], str(path)+'/'+k)
        require(info(a) == spec['fields'][k], 'archive field descriptor')
    return arrays


def blend(raw, warp, mask, history):
    weight = mask * (~history).reshape(8,1,1,1) * np.float32(.25)
    left = (np.float32(1)-weight)*raw
    right = weight*warp
    result = np.where(weight>0, left+right, raw)
    magnitude = np.abs(left.astype(np.float64))+np.abs(right.astype(np.float64))
    return result, magnitude


def euler(last, clean):
    x = last['x_tilde']; s = last['sigma_hat'].reshape(8,1,1,1)
    d = (x-clean)/s
    step = (last['next_sigma']-last['sigma_hat']).reshape(8,1,1,1)
    result = x+step*d
    # Includes both subtraction operands so cancellation does not shrink the bound.
    magnitude = np.abs(x.astype(np.float64)) + np.abs(step.astype(np.float64)/s)*(np.abs(x.astype(np.float64))+np.abs(clean.astype(np.float64)))
    return result, magnitude


def main(binding):
    require(np.__version__ == '1.26.4' and sys.platform == 'darwin', 'frozen local NumPy runtime')
    require(binding['checker_sha256'] == digest(read(Path(__file__))), 'checker identity')
    cfg = meta(HERE/'CONTRACT.json', GENERATION_CONTRACT)
    require(binding['generation_contract_sha256'] == GENERATION_CONTRACT, 'generation contract binding')
    r = meta(OUT/'RECEIPT.json', binding['generation_receipt_sha256'])
    supervision = meta(HERE/'supervision_01/SUPERVISION.json', binding['supervision_sha256'])
    require(r['status'] == 'COMPLETE_FOUR_FIXED_CONSUMER_ARMS_PENDING_REVIEW', 'complete generation required')
    require(r['contract_sha256'] == GENERATION_CONTRACT, 'receipt contract')
    read(OUT/'progress.jsonl',r['progress_sha256'])
    require(r['controls']==cfg['controls'], 'reported frozen controls')
    # Supervisor metadata is preserved for root's independent status/limit review.
    require(cfg['controls']['history_order'] == [19,18,13,12] and cfg['controls']['target_order'] == [20,21,22,23], 'fixed slots')
    require(cfg['strengths'] == [.25]*50 and cfg['final_strength'] == .25, 'fixed strengths')
    require(r['full_chain_calls'] == 2 and r['warp_encoder_calls'] == 1 and r['warp_encode_chunks'] == 4 and r['derived_decoder_calls'] == 1, 'actual call counts')
    require(r['components_loaded'] == ['VMem','VAE'] and not r['unrun_arms'], 'loaded components and complete arms')
    for k in ['reference_RGB_reads','sensor_depth_reads','geometry_or_retrieval_calls','optimizer_calls']:
        require(r[k] == 0, 'isolated generation metadata: '+k)
    require(set(r['arms']) == {'G0','Gguide','Gpaste','Gterminal'}, 'four arms')
    originals, masks = [], []
    for spec in cfg['warps']:
        require(spec['target_id'] == 20+len(originals), 'warp order')
        blob = read(spec['path'], spec['sha256'], spec['bytes'])
        with np.load(io.BytesIO(blob), allow_pickle=False) as z:
            rgb, m = z['warp_rgb'], z['mask']
        shape(rgb,(576,576,3),'float32','original warp');shape(m,(576,576),'bool','original mask')
        require(((rgb>=0)&(rgb<=1)).all() and (rgb[~m]==0).all(), 'original warp range/black holes')
        originals.append(rgb.transpose(2,0,1));masks.append(m[None])
    del blob, rgb, m
    warp_rgb = np.ascontiguousarray(np.stack(originals)); image_mask = np.stack(masks)
    equal('source warp -> saved RGB',array(r['warp_rgb'],OUT/'warp_rgb01.npy',RGB,'float32'),warp_rgb)
    equal('source mask -> saved mask',array(r['image_mask'],OUT/'image_mask.npy',(4,1,576,576),'bool'),image_mask)
    equal('source RGB -> encoder input',array(r['encoder_input'],OUT/'encoder_input.npy',RGB,'float32'),warp_rgb*np.float32(2)-np.float32(1))
    enc = archive(r['encoded_warp'],OUT/'ENCODED_WARP.npz',{'warp_latents':(LATENT,'float32'),'support_mask':((8,1,72,72),'float32'),'history_slots':((8,),'bool')})
    history=np.array([True]*4+[False]*4);warp=enc['warp_latents'];mask=enc['support_mask']
    equal('history slots',enc['history_slots'],history)
    equal('history warp zeros',warp[:4],np.zeros((4,4,72,72),np.float32))
    # Integer counts make the denominator explicit; count/64 is exactly binary FP32.
    area=image_mask.reshape(4,1,72,8,72,8).sum(axis=(3,5),dtype=np.int64).astype(np.float32)/np.float32(64)
    expected_mask=np.concatenate([np.zeros_like(area),area])
    equal('8x8 source support fractions including protected history',mask,expected_mask)
    protected=np.broadcast_to((mask==0)|history[:,None,None,None],LATENT)
    baseline=meta(OUT/'model_baseline.json')
    baseline_id={k:baseline[k] for k in ('value_sha256','identity_sha256','modes_sha256')}
    for key, content in [('value_sha256','values'),('identity_sha256','identity'),('modes_sha256','modes')]:
        require(digest(canonical(baseline[content]))==baseline[key], 'model metadata self hash')
    require(r['final_model_state']==baseline_id, 'final model identity metadata')
    common=meta(OUT/'common_rng.json');common_sha=digest(canonical(common))
    require(common_sha==r['common_rng_sha256'], 'common actual RNG file')
    arm_data={}
    for name in ['G0','Gguide']:
        a=r['arms'][name];adir=OUT/name
        require(meta(adir/'receipt.json')==a and a['status']=='COMPLETE_CHAIN', 'arm receipt/complete')
        require(a['model_unchanged'] and a['model_after']==baseline_id, 'model unchanged metadata')
        require(a['restored_rng']==common_sha, 'restored common RNG')
        for tag in ['entry','terminal']:
            require(digest(canonical(meta(adir/(tag+'_rng.json'))))==a[tag+'_rng'], 'full RNG file: '+tag)
        steps=[json.loads(x) for x in read(adir/'steps.jsonl').decode().splitlines()]
        require(steps==a['steps'] and len(steps)==50 and len(a['hook_steps'])==50 and len(a['clean_trace'])==50, '50 actual records')
        previous=a['entry_rng']
        for i,(s,h,t) in enumerate(zip(steps,a['hook_steps'],a['clean_trace']),1):
            require(s['step']==h['step']==t['step']==i and s['status']=='COMPLETE' and h['status']=='COMPLETED', 'step ordinal/status')
            require(s['rng_before']==previous, 'RNG adjacency');previous=s['rng_after']
            require(h['prepare_calls']==h['cfg_calls']==h['callback_calls']==1 and h['fusion_calls']==int(name=='Gguide'), 'hook call counts')
            require(h['strength']==(.25 if name=='Gguide' else 0) and t['protected_clean_exact'] and t['callback_rng_unchanged'], 'hook strength/protection')
            require(h['clean_returned_same_object']==t['original_object'], 'transparent object metadata')
            for key in ['raw','used']:
                require(t[key]['shape']==list(LATENT) and t[key]['dtype']=='float32' and t[key]['body_bytes']==663552, 'clean metadata schema')
            if name=='G0':
                require(t['original_object'] and t['raw']==t['used'] and 'archive' not in t, 'G0 transparent clean metadata')
            else:
                require(not t['original_object'], 'Gguide allocated fusion')
                c=archive(t['archive'],adir/'clean_steps'/f'step_{i:03d}.npz',{'raw_clean':(LATENT,'float32'),'used_clean':(LATENT,'float32')})
                require(info(c['raw_clean'])==t['raw'] and info(c['used_clean'])==t['used'], 'clean trace matches actual archive')
                expected, mag=blend(c['raw_clean'],warp,mask,history)
                numerical(f'Gguide step{i:02d} fusion',c['used_clean'],expected,mag)
                equal(f'Gguide step{i:02d} protected clean',c['used_clean'][protected],c['raw_clean'][protected])
        require(previous==a['terminal_rng'], 'terminal RNG after last step')
        noise=array(a['noise'],adir/'noise.npy',LATENT,'float32')
        latents=array(a['arrays']['all8_latents'],adir/'all8_latents.npy',LATENT,'float32')
        rgb=array(a['arrays']['targets_fp32'],adir/'targets_fp32.npy',RGB,'float32')
        schema={k:((8,),'float32') if k in {'sigma','sigma_hat','next_sigma'} else (LATENT,'float32') for k in LAST_KEYS}
        last=archive(a['last_step'],adir/'LAST_STEP.npz',schema)
        require(a['last_metadata']==dict(mode=name,step=50,gamma=0.0,complete=True), 'last complete metadata')
        require((last['sigma']>0).all() and (last['sigma_hat']>0).all() and (last['next_sigma']==0).all(), 'last sigma endpoint')
        equal(name+' original sigma_hat including 1e-6',last['sigma_hat'],last['sigma']+np.float32(1e-6))
        equal(name+' actual last output vs all8 latents',last['output'],latents)
        for key,tag in [('raw_clean','raw'),('used_clean','used')]:
            require(info(last[key])==a['clean_trace'][-1][tag], 'last vs actual callback')
        if name=='G0': equal('G0 last clean transparent',last['used_clean'],last['raw_clean'])
        else:
            equal('guide last archive vs step50 raw',last['raw_clean'],c['raw_clean'])
            equal('guide last archive vs step50 used',last['used_clean'],c['used_clean'])
        expected,mag=euler(last,last['used_clean'])
        numerical(name+' actual final Euler',last['output'],expected,mag)
        arm_data[name]=(noise,last,latents,rgb)
    g0,guide=r['arms']['G0'],r['arms']['Gguide']
    equal('shared actual initial noise',arm_data['G0'][0],arm_data['Gguide'][0])
    require(g0['entry_rng']==guide['entry_rng'] and g0['terminal_rng']==guide['terminal_rng'], 'shared actual endpoint RNG')
    require([(x['rng_before'],x['rng_after']) for x in g0['steps']]==[(x['rng_before'],x['rng_after']) for x in guide['steps']], 'shared actual50step RNG')
    require(r['shared_actual_random_stream'] and r['derived_rng_unchanged'] and r['G0_last_replay_exact'], 'runtime replay/RNG assertions')
    for name in ['Gpaste','Gterminal']:
        a=r['arms'][name];adir=OUT/name
        require(meta(adir/'receipt.json')==a and a['status']=='COMPLETE_DERIVED' and a['full_chain_calls']==0, 'derived receipt and zero denoiser chains')
        actual=array(a['arrays']['targets_fp32'],adir/'targets_fp32.npy',RGB,'float32')
        if name=='Gpaste':
            base=np.stack([(x+np.float32(1))/np.float32(2) if x.min()<-.1 else x for x in arm_data['G0'][3]])
            base=np.clip(base,0,1);weight=image_mask.astype(np.float32)*np.float32(.25)
            left=(np.float32(1)-weight)*base;right=weight*warp_rgb
            expected=np.where(weight>0,left+right,base)
            numerical('Gpaste actual RGB composition',actual,expected,np.abs(left.astype(np.float64))+np.abs(right.astype(np.float64)))
            p=np.broadcast_to(~image_mask,RGB);equal('Gpaste unsupported RGB exact',actual[p],base[p])
        else:
            require(a['decode_chunks']==8, 'terminal full8 decoding count')
            terminal=archive(a['replayed_state'],adir/'TERMINAL_STATE.npz',{'clean_used':(LATENT,'float32'),'latents':(LATENT,'float32')})
            expected,mag=blend(arm_data['G0'][1]['raw_clean'],warp,mask,history)
            numerical('Gterminal clean fusion from actual G0',terminal['clean_used'],expected,mag)
            equal('terminal protected clean',terminal['clean_used'][protected],arm_data['G0'][1]['raw_clean'][protected])
            expected,mag=euler(arm_data['G0'][1],expected)
            numerical('Gterminal Euler from actual G0',terminal['latents'],expected,mag)
            latents=array(a['arrays']['all8_latents'],adir/'all8_latents.npy',LATENT,'float32')
            equal('terminal state vs decoded-input archive',terminal['latents'],latents)
            equal('terminal protected final latents',latents[protected],arm_data['G0'][2][protected])
    return dict(status='PASS',full_chains=2,derived_controls=2,guide_steps_recomputed=50,
        all7_last_tensors_checked_per_chain=True,reference_reads=0,model_calls=0,
        supervisor_status=supervision.get('status'),generation_elapsed_seconds=r['elapsed_seconds'],
        limits='Saved-data arithmetic/storage consistency only. No VAE encoder/decoder or denoiser reevaluation; their provenance/counts use sealed metadata. G0 all50 raw clean tensors were not archived; transparency is checked against live trace hashes/object flags plus actual final tensors. RNG intermediate states are collected hashes, not reconstructed PRNG states. No image quality, geometry accuracy, novel method, or independent-scene claim.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--binding-sha256',required=True);args=parser.parse_args()
    destination=HERE/'INDEPENDENT_CONSUMPTION_REVIEW.json'
    require(not destination.exists(),'review output already exists; no retry/overwrite')
    result=dict(status='STARTED',started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),reads=READS,checks=CHECKS)
    def timeout(signum,frame): raise TimeoutError('300-second review alarm')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(300)
    try:
        binding=meta(HERE/'CONSUMPTION_REVIEW_BINDING.json',args.binding_sha256)
        result['binding_sha256']=args.binding_sha256
        result.update(main(binding))
    except BaseException as exc:
        result.update(status='FAIL',error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc())
    finally:
        signal.alarm(0)
        result.update(completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-STARTED,
                      read_events=len(READS),comparison_fields=len(CHECKS),peak_self_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        with destination.open('x') as f: json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:result[k] for k in ['status','elapsed_seconds','comparison_fields']}))
    raise SystemExit(0 if result['status']=='PASS' else 1)
