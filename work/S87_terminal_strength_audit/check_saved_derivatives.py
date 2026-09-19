"""Independent S87 sealed-data arithmetic; no author/model imports or GT reads.

Requires root's exact final-receipt/source/plan binding. Create-only output;
never discovers a newer run, loads a model, or retries a failed review.
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
LATENT = (8, 4, 72, 72)
RGB = (4, 3, 576, 576)
TARGETS = (20, 21, 22, 23)
STRATEGIES = tuple((f'{family}_l{tag}', family, strength)
                  for tag, strength in [('050', .5), ('075', .75), ('100', 1.)]
                  for family in ('Gpaste', 'Gterminal'))
LAST_KEYS = {'sigma', 'next_sigma', 'x_tilde', 'sigma_hat',
             'raw_clean', 'used_clean', 'output'}
READS, CHECKS = [], []
STARTED = time.monotonic()


def require(ok, why):
    if not bool(ok):
        raise ValueError(why)


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def budget():
    require(time.monotonic()-STARTED < 120, '120-second review budget')
    require(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < 1024**3,
            '1-GiB self RSS budget')


def read(path, expected=None, size=None):
    budget()
    path = Path(path)
    blob = path.read_bytes()
    row = dict(path=str(path), sha256=digest(blob), bytes=len(blob))
    READS.append(row)
    require(expected is None or row['sha256'] == expected, 'file SHA: '+str(path))
    require(size is None or len(blob) == size, 'file bytes: '+str(path))
    return blob


def meta(path, expected=None):
    return json.loads(read(path, expected))


def info(a):
    a = np.ascontiguousarray(a)
    return dict(shape=list(a.shape), dtype=str(a.dtype), body_bytes=a.nbytes,
                body_sha256=digest(a.tobytes()))


def schema(a, dims, dtype, label):
    require(type(a) is np.ndarray and a.shape == tuple(dims)
            and a.dtype == np.dtype(dtype), 'schema: '+label)
    require(a.flags.c_contiguous, 'contiguous archive: '+label)
    require(np.isfinite(a).all(), 'finite: '+label)


def exact(label, actual, expected):
    require(actual.shape == expected.shape and actual.dtype == expected.dtype,
            'comparison schema: '+label)
    ok = np.ascontiguousarray(actual).tobytes() == np.ascontiguousarray(expected).tobytes()
    row = dict(label=label, rule='exact_bytes', elements=actual.size, pass_check=ok)
    if np.issubdtype(actual.dtype, np.floating):
        require(np.isfinite(actual).all() and np.isfinite(expected).all(),
                'comparison finite: '+label)
        delta = np.abs(actual.astype(np.float64)-expected.astype(np.float64))
        row.update(nonzero_value_differences=int(np.count_nonzero(delta)),
                   max_abs_difference=float(delta.max(initial=0)))
    CHECKS.append(row)
    require(ok, 'exact byte mismatch: '+label)


def array(spec, path, dims, dtype):
    require(spec['path'] == str(path), 'fixed array path')
    a = np.load(io.BytesIO(read(path, spec['file_sha256'])), allow_pickle=False)
    schema(a, dims, dtype, str(path))
    require(info(a) == {k:spec[k] for k in info(a)}, 'array body descriptor')
    a.flags.writeable = False
    return a


def archive(spec, path, expected):
    require(spec['path'] == str(path), 'fixed archive path')
    blob = read(path, spec['sha256'], spec['bytes'])
    with np.load(io.BytesIO(blob), allow_pickle=False) as z:
        require(set(z.files) == set(expected) == set(spec['fields']), 'archive exact keys')
        arrays = {k:z[k] for k in z.files}
    for k,a in arrays.items():
        schema(a, *expected[k], str(path)+'/'+k)
        require(info(a) == spec['fields'][k], 'archive body descriptor: '+k)
        a.flags.writeable = False
    return arrays


def blend(raw, warp, mask, history, strength):
    weight = mask * (~history).reshape(-1,1,1,1) * np.float32(strength)
    left = (np.float32(1)-weight)*raw
    right = weight*warp
    return np.where(weight>0, left+right, raw)


def euler(last, clean):
    x = last['x_tilde']
    sigma = last['sigma_hat'].reshape(-1,1,1,1)
    derivative = (x-clean)/sigma
    step = (last['next_sigma']-last['sigma_hat']).reshape(-1,1,1,1)
    return x+step*derivative


def clamp_rgb(x):
    # Torch clamp preserves -0. np.clip in NumPy 1.26.4 does not.
    # Strict comparisons are the same clipping rule and retain original zero bytes.
    return np.where(x < np.float32(0), np.float32(0),
                    np.where(x > np.float32(1), np.float32(1), x))


def paste(raw, warp, mask, strength):
    # Torch compares against a scalar converted to its tensor dtype. The
    # original NumPy emission below instead uses the Python-float threshold.
    base = np.stack([(x+np.float32(1))/np.float32(2) if x.min()<np.float32(-.1) else x
                     for x in raw])
    base = clamp_rgb(base)
    weight = mask.astype(np.float32)*np.float32(strength)
    left = (np.float32(1)-weight)*base
    right = weight*warp
    return np.where(weight>0, left+right, base), base


def quantize(raw):
    image = raw.transpose(1,2,0)
    branch = bool(image.min()<-.1)
    if branch:
        image = (image+np.float32(1))/np.float32(2)
    return np.clip(image*np.float32(255), 0, 255).astype(np.uint8), branch


def hash_file(spec):
    path = Path(spec['path']); hasher = hashlib.sha256(); size = 0
    with path.open('rb') as handle:
        while True:
            budget(); part = handle.read(8*1024**2)
            if not part: break
            hasher.update(part); size += len(part)
    actual = dict(path=str(path),sha256=hasher.hexdigest(),bytes=size)
    READS.append(actual)
    require(actual['sha256']==spec['sha256'] and size==spec.get('bytes',spec.get('size')),
            'streamed identity: '+str(path))
    return actual


def rng(spec, label):
    a = array(spec['torch_cpu'],OUT/f'rng_{label}_torch.npy',(5056,),'uint8')
    m = spec['python_numpy']
    require(m['path']==str(OUT/f'rng_{label}.json'),'RNG metadata path')
    blob = read(m['path'],m['sha256'],m['bytes']); value=json.loads(blob)
    require(set(value)=={'python','numpy'},'RNG kinds')
    py=value['python']; n=value['numpy']
    require(len(py)==3 and py[0]==3 and len(py[1])==625,'Python full RNG state')
    require(set(n)=={'engine','keys','position','has_gauss','cached_gaussian'}
            and n['engine']=='MT19937' and len(n['keys'])==624
            and 0<=n['position']<=624 and n['has_gauss'] in (0,1),'NumPy full RNG state')
    encoded=(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
    require(encoded==blob and digest(encoded+a.tobytes())==spec['state_sha256'],
            'combined full RNG state SHA')
    return a,value


def main(binding):
    require(binding['accepted'] is True,'root accepted binding required')
    require(np.__version__=='1.26.4' and sys.platform=='darwin','frozen NumPy/macOS runtime')
    require(digest(read(Path(__file__)))==binding['checker_sha256'],'checker identity')
    read(HERE/'DERIVATIVE_REVIEW_PLAN.md',binding['review_plan_sha256'])
    cfg=meta(HERE/'GENERATION_CONTRACT.json',binding['generation_contract_sha256'])
    require(cfg['runner_sha256']==binding['runner_sha256'],'runner binding')
    read(HERE/'generate_terminal_controls.py',binding['runner_sha256'])
    names=[a for a,f,s in STRATEGIES]
    require(cfg['order']==names and cfg['strengths']==[.5,.75,1.], 'fixed six grid/order')
    require(cfg['strategies']==[dict(name=a,family=f,strength=s) for a,f,s in STRATEGIES],
            'fixed strategy identities')
    require(cfg['history_ids']==[19,18,13,12] and cfg['target_ids']==list(TARGETS),'fixed slot identities')
    r=meta(OUT/'RECEIPT.json',binding['generation_receipt_sha256'])
    require(r['status']=='COMPLETE_SIX_DERIVED_CONTROLS_PENDING_REVIEW'
            and bool(r['completed_utc']) and not r['unrun_arms'],'complete generation')
    require(r['contract_sha256']==binding['generation_contract_sha256']
            and r['executable_sha256']==binding['runner_sha256'],'generation source binding')
    require(r['order']==names and r['target_ids']==list(TARGETS)
            and set(r['arms'])==set(r['arm_receipts'])==set(names),'complete six identities')
    counts=dict(vae_loads=1,encoder_calls=0,denoiser_calls=0,decoder_calls=3,
                decoder_chunks=24,completed_decoder_chunks=24,paste_calls=3)
    require(r['counts']==cfg['expected_counts']==counts,'exact call census')
    require(r['reference_reads']==0 and r['new_method_validated'] is False,'generation isolation/limits')
    require(r['runtime']==dict(device='cpu',dtype='float32',threads=8,interop=1)
            and r['versions']==cfg['versions'],'actual frozen runtime metadata')
    require(r['source_inputs']==cfg['inputs'] and r['source_bindings']==cfg['sources']
            and r['vae_identity']==cfg['vae'] and r['variant']==cfg['variant'],'reported frozen identities')
    require(r['model_identity_versions_unchanged'] is True,'model identity/version record')
    require(not any(r['vae_loading_info'].get(k) for k in
            ('missing_keys','unexpected_keys','mismatched_keys','error_msgs')),'complete VAE load metadata')
    require(len(r['vae_weight_consumers'])==1,'one bound VAE deserialization record')
    supervision=None
    if 'supervision' in binding:
        s=binding['supervision']
        require(s['path']==str(HERE/'supervision_01/SUPERVISION.json'),'supervision fixed path')
        supervision=meta(s['path'],s['sha256'])
    metadata={}
    for k,spec in cfg['metadata'].items():
        blob=read(spec['path'],spec['sha256'],spec['bytes'])
        if k in ('S86_receipt','G0_receipt','S86_acceptance'): metadata[k]=json.loads(blob)
    require(metadata['S86_acceptance']['accepted'] is True,'accepted S86 source')
    for spec in cfg['sources'].values(): read(spec['path'],spec['sha256'],spec['bytes'])
    vae=cfg['vae']
    require(vae['repo']=='stabilityai/sd-vae-ft-mse' and vae['revision']=='31f26fdeee1355a5c34592e401dd41e45d25a493'
            and vae['scale_factor']==.18215 and vae['chunk_size']==1 and vae['full_slots']==8,
            'declared VAE variant/scale/full8')
    for spec in (vae['config'],vae['weight']): hash_file(spec)
    required_reads=[]
    for group in ('metadata','sources','inputs'):
        for spec in cfg[group].values():
            required_reads.append((spec['path'],spec.get('sha256',spec.get('file_sha256'))))
    required_reads += [(spec['path'],spec['sha256']) for spec in (vae['config'],vae['weight'])]
    actual_reads=[(x['path'],x['sha256']) for x in r['reads']]
    require(len(actual_reads)==len(required_reads) and sorted(actual_reads)==sorted(required_reads),
            'complete exact generation read set, no extra scientific input')
    old=metadata['S86_receipt']; g0=metadata['G0_receipt']; inp=cfg['inputs']
    require(old['arms']['G0']==g0 and g0['last_metadata']==cfg['last_metadata'],'original G0 receipt metadata')
    for key,desc in [('last_step',g0['last_step']),('encoded_warp',old['encoded_warp'])]:
        require(inp[key]==desc,'original NPZ descriptor '+key)
    for key,desc in [('g0_raw',g0['arrays']['targets_fp32']),('g0_latents',g0['arrays']['all8_latents']),
                     ('warp_rgb',old['warp_rgb']),('image_mask',old['image_mask'])]:
        require({k:v for k,v in inp[key].items() if k!='bytes'}==desc,'original NPY descriptor '+key)
    E=HERE.parent/'S86_fixed_warp_consumer/execution_01'
    last=archive(inp['last_step'],E/'G0/LAST_STEP.npz',
          {k:((8,) if k in ('sigma','sigma_hat','next_sigma') else LATENT,'float32') for k in LAST_KEYS})
    encoded=archive(inp['encoded_warp'],E/'ENCODED_WARP.npz',
          {'warp_latents':(LATENT,'float32'),'support_mask':((8,1,72,72),'float32'),'history_slots':((8,),'bool')})
    raw=array(inp['g0_raw'],E/'G0/targets_fp32.npy',RGB,'float32')
    old_latents=array(inp['g0_latents'],E/'G0/all8_latents.npy',LATENT,'float32')
    warp_rgb=array(inp['warp_rgb'],E/'warp_rgb01.npy',RGB,'float32')
    mask_rgb=array(inp['image_mask'],E/'image_mask.npy',(4,1,576,576),'bool')
    require(r['image_mask']==inp['image_mask'],'same image mask for scorer')
    W,m,history=(encoded[k] for k in ('warp_latents','support_mask','history_slots'))
    exact('history slots',history,np.array([True]*4+[False]*4))
    exact('history warp zero',W[:4],np.zeros_like(W[:4]))
    require(((m>=0)&(m<=1)).all() and ((warp_rgb>=0)&(warp_rgb<=1)).all(),'warp/mask ranges')
    require((warp_rgb[np.broadcast_to(~mask_rgb,RGB)]==0).all(),'black warp holes')
    area=mask_rgb.reshape(4,1,72,8,72,8).sum(axis=(3,5),dtype=np.int64).astype(np.float32)/np.float32(64)
    exact('fixed avg8 fractional support',m,np.concatenate([np.zeros_like(area),area]))
    require((last['sigma']>0).all() and (last['sigma_hat']>0).all()
            and (last['next_sigma']==0).all(),'actual final Euler endpoints')
    exact('sigma_hat includes original epsilon',last['sigma_hat'],last['sigma']+np.float32(1e-6))
    exact('G0 raw clean transparent',last['used_clean'],last['raw_clean'])
    exact('G0 archived final output',last['output'],old_latents)
    exact('G0 saved last Euler no new decode',last['output'],euler(last,last['raw_clean']))
    protected=np.broadcast_to((m==0)|history[:,None,None,None],LATENT)
    after=rng(r['rng_after_load'],'after_load'); end=rng(r['rng_end'],'end')
    exact('full Torch CPU derived RNG unchanged',after[0],end[0])
    require(after[1]==end[1] and r['rng_after_load']['state_sha256']==r['rng_end']['state_sha256']
            and r['derived_rng_unchanged'] is True,'full Python/NumPy/RNG identity')
    progress=[json.loads(x) for x in read(OUT/'progress.jsonl',r['progress_sha256']).decode().splitlines()]
    require([x['arm'] for x in progress if x['event']=='arm_start']==names
            and [x['arm'] for x in progress if x['event']=='arm_complete']==names,'actual complete order')
    require(sum(x['event']=='vae_load_start' for x in progress)==1
            and sum(x['event']=='vae_loaded' for x in progress)==1
            and sum(x['event']=='complete' for x in progress)==1,'load/complete progress counts')
    for name,family,strength in STRATEGIES:
        a=r['arms'][name]; adir=OUT/name; spec=r['arm_receipts'][name]
        require(spec['path']==str(adir/'receipt.json'),'arm receipt path')
        require(json.loads(read(spec['path'],spec['sha256'],spec['bytes']))==a,'arm receipt exact body')
        require(a['family']==family and a['strength']==strength and a['status']=='COMPLETE_DERIVED'
                and bool(a['completed_utc']),'arm identity/state')
        n=8 if family=='Gterminal' else 0
        require(a['decoder_calls']==int(n>0) and a['decoder_chunks']==a['completed_decoder_chunks']==n,
                'per-arm decoder counts')
        starts=[x for x in progress if x['arm']==name and x['event']=='decoder_chunk_start']
        ends=[x for x in progress if x['arm']==name and x['event']=='decoder_chunk_end']
        require([x['chunk'] for x in starts]==list(range(1,n+1)) and len(ends)==n,'all actual decode chunks')
        require(set(a['arrays'])=={'targets_fp32','targets_uint8'},'exact emitted array keys')
        emitted_raw=array(a['arrays']['targets_fp32'],adir/'targets_fp32.npy',RGB,'float32')
        uint8=array(a['arrays']['targets_uint8'],adir/'targets_uint8.npy',(4,576,576,3),'uint8')
        require(len(a['quantizer'])==4,'all four quantizer records')
        for i,target in enumerate(TARGETS):
            expected,branch=quantize(emitted_raw[i])
            exact(f'{name} target{target} raw-to-uint8',uint8[i],expected)
            require(a['quantizer'][i]==dict(target_id=target,raw_min=float(emitted_raw[i].min()),
                    raw_max=float(emitted_raw[i].max()),maps_minus1_plus1=branch),'quantizer exact metadata')
        if family=='Gpaste':
            require(a['terminal']=={},'paste has no latent/decode output')
            expected,base=paste(raw,warp_rgb,mask_rgb,strength)
            exact(name+' FP32 RGB mixture',emitted_raw,expected)
            p=np.broadcast_to(~mask_rgb,RGB)
            exact(name+' protected RGB bytes',emitted_raw[p],base[p])
        else:
            require(set(a['terminal'])=={'clean_used','all8_latents'},'terminal exact keys')
            clean=array(a['terminal']['clean_used'],adir/'clean_used.npy',LATENT,'float32')
            latents=array(a['terminal']['all8_latents'],adir/'all8_latents.npy',LATENT,'float32')
            expected=blend(last['raw_clean'],W,m,history,strength)
            exact(name+' clean fusion',clean,expected)
            exact(name+' protected clean',clean[protected],last['raw_clean'][protected])
            exact(name+' true saved G0 Euler',latents,euler(last,expected))
            exact(name+' protected final latent',latents[protected],old_latents[protected])
            require(a['protected_clean_bytes_exact'] is True and a['protected_latent_bytes_exact'] is True,
                    'protection metadata')
    read(OUT/'RECEIPT.json',binding['generation_receipt_sha256'])
    return dict(status='PASS',strategies=6,new_target_frames=24,terminal_fusions_recomputed=3,
        terminal_Euler_recomputed=3,G0_saved_Euler_recomputed=1,new_lambda_zero_decodes=0,
        RGB_mixtures_recomputed=3,raw_to_uint8_frames=24,reference_reads=0,model_calls=0,
        actual_generation_counts=counts,supervision_metadata_status=None if supervision is None else supervision.get('status'),
        limits='Independent saved-data arithmetic/storage consistency only, exact FP32 operation bytes. VAE decoding is not reevaluated: its actual calls, identity and unchanged state use source and sealed metadata. RNG compares complete after-load/end Python, NumPy and Torch CPU states, not per-call RNG histories. No quality, geometry, independent-scene or novelty conclusion.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--binding-sha256',required=True);args=parser.parse_args()
    output=HERE/'INDEPENDENT_DERIVATIVE_REVIEW.json'
    require(not output.exists(),'review already exists: no retry/overwrite')
    report=dict(status='STARTED',started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),reads=READS,checks=CHECKS)
    def timeout(signum,frame): raise TimeoutError('120-second derivative review alarm')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(120)
    try:
        binding=meta(HERE/'DERIVATIVE_REVIEW_BINDING.json',args.binding_sha256)
        report['binding_sha256']=args.binding_sha256;report.update(main(binding))
    except BaseException as exc:
        report.update(status='FAIL_PARTIAL_PRESERVED',error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc())
    finally:
        signal.alarm(0)
        report.update(completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-STARTED,
            read_events=len(READS),comparison_fields=len(CHECKS),peak_self_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        with output.open('x') as handle:
            json.dump(report,handle,ensure_ascii=False,indent=2,allow_nan=False);handle.write('\n')
    print(json.dumps({k:report[k] for k in ('status','elapsed_seconds','comparison_fields')}))
    raise SystemExit(0 if report['status']=='PASS' else 1)
