"""S75 saved-array/PNG/coordinate audit only. No author, VAE, or CV imports."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,io,json,math,sys,time,traceback
O=Path(__file__).resolve().parent
D=O.parent
BINDING_SHA='a061f8e74553c164ca249c6d196345724bbb827ce1ff53d13f973d8a3b3c40de'

def utc():return datetime.now(timezone.utc).isoformat()
def quantile(values,q):
    v=sorted(values);at=(len(v)-1)*q;lo,hi=math.floor(at),math.ceil(at)
    return v[lo] if lo==hi else (hi-at)*v[lo]+(at-lo)*v[hi]
def flatten(a):return [v for x in a for v in flatten(x)] if isinstance(a,list) else [a]
def coverage(x):
    return dict(span_xy_fraction=[(max(p[j] for p in x)-min(p[j] for p in x))/575 for j in [0,1]] if x else None,occupied_4x4_cells=len({tuple(max(0,min(3,math.floor(v/144))) for v in p) for p in x}))
def run(r):
    import numpy as np
    from PIL import Image
    r['numpy_version']=np.__version__
    def check(name,ok,detail=None):r['checks'].append({'name':name,'pass':bool(ok),'detail':detail})
    def read(p,h=None,kind='metadata'):
        p=Path(p);b=p.read_bytes();digest=hashlib.sha256(b).hexdigest();r['reads'].append(dict(path=str(p),bytes=len(b),sha256=digest,kind=kind))
        if h:
            check('pin/'+str(p),digest==h)
            if digest!=h:raise ValueError('Pinned identity changed '+str(p))
        return b
    bb=read(O/'BINDING.json',BINDING_SHA,'binding');binding=json.loads(bb)
    def js(p,h=None):return json.loads(read(p,h))
    evid={p:read(p,h,'source_identity_only' if p.endswith('.py') else 'metadata') for p,h in binding['evidence_pins'].items()}
    def obj(rel):return json.loads(evid[str(D/rel)])
    w,c,outer,st,root=obj('execution_01/receipt.json'),obj('CONTRACT.json'),obj('external_01/receipt.json'),obj('external_01/started.json'),obj('ROOT_SOURCE_REVIEW.json')
    rawtol=binding['tolerances']['raw_mse_mae'];coordtol=binding['tolerances']['coordinate_statistics']
    def cmp(name,a,b,tol=coordtol):
        if a is None or b is None:check(name,a is None and b is None);return
        av,bv=flatten(a),flatten(b);bad=[i for i,(x,y) in enumerate(zip(av,bv)) if not(math.isfinite(x) and math.isfinite(y) and math.isclose(x,y,abs_tol=tol['absolute'],rel_tol=tol['relative']))]
        check(name,len(av)==len(bv) and not bad,dict(count=len(av),saved_count=len(bv),mismatch_indices=bad,max_abs_difference=max((abs(x-y) for x,y in zip(av,bv)),default=0),tolerance=tol))
    ids=c['history_ids'];check('fixed_five',ids==[12,13,14,18,19] and [p['history_id'] for p in w['rows']]==ids and not w['unrun_history_ids'])
    stdout=obj('external_01/stdout.txt');stderr=evid[str(D/'external_01/stderr.txt')]
    check('terminal',outer['returncode']==0 and outer['stop_reason'] is None and not stderr and w['status']=='COMPLETE_FIVE_HISTORY_VAE_ROUNDTRIP' and stdout['status']==w['status'] and stdout['completed_histories']==5)
    check('lexical_venv_command',st['argv']==[str(D.parents[1]/'.venv-cut3r/bin/python'),'-B',str(D/'decode_history.py'),w['contract_sha256']] and st['wall_seconds']==180)
    check('source_review_bindings',root['files_sha256']['decode_history.py']==w['source_sha256']==binding['evidence_pins'][str(D/'decode_history.py')] and root['files_sha256']['CONTRACT.json']==w['contract_sha256']==binding['evidence_pins'][str(D/'CONTRACT.json')])
    check('version_scope',w['versions']==c['versions'] and np.__version__==c['versions']['numpy'] and all(w[x]==0 for x in ['new_encode_calls','clip_calls','vmem_calls','sampling_calls']) and not w['new_method_validated'])
    check('time_order',outer['started_utc']==st['started_utc'] and outer['started_utc']<=w['started_utc']<=w['loaded_utc']<=w['completed_utc']<=outer['completed_utc'])
    check('resource_receipts',outer['monitor_samples']>0 and outer['peak_sampled_process_tree_rss_bytes']<=st['sampled_tree_rss_limit']==c['limits']['rss_bytes'] and w['peak_self_rss_bytes']<=c['limits']['rss_bytes'])
    old=js(c['s68_receipt']['path'],c['s68_receipt']['sha256']);accepted=js(c['s68_acceptance']['path'],c['s68_acceptance']['sha256'])
    check('S68_accepted',accepted['review_identity']['execution_01/receipt.json']==c['s68_receipt']['sha256'] and accepted['status']=='ACCEPTED_FIVE_REAL_HISTORY_APPEARANCE_CACHE_ONLY')
    progress=[json.loads(x) for x in evid[str(D/'execution_01/progress.jsonl')].decode().splitlines()]
    check('progress_sequence',[(x['event'],x.get('history_id')) for x in progress]==[('vae_loaded',None)]+[(name,hid) for hid in ids for name in ['decode_start','decode_return','history_completed']])
    check('recorded_five_decode_calls',[x['history_id'] for x in w['decode_calls']]==ids)
    check('one_bound_weight_consumption',len(w['vae_weight_decoder_calls'])==1 and w['vae_weight_decoder_calls'][0]==str(D/'execution_01/local_vae/diffusion_pytorch_model.safetensors') and all(not w['vae_loading_info'][k] for k in ['missing_keys','unexpected_keys','mismatched_keys','error_msgs']))
    weightreads=[x for x in w['reads'] if x['kind']=='vae_weight'];check('recorded_one_weight_read',len(weightreads)==1 and weightreads[0]['sha256']==c['components']['vae_weight']['sha256'] and weightreads[0]['bytes']==c['components']['vae_weight']['size'])
    original_meta={x['history_id']:x for x in old['rows']}
    read(c['sources']['autoencoder']['path'],c['sources']['autoencoder']['sha256'],'original_wrapper_source')
    for index,(p,history,call) in enumerate(zip(w['rows'],c['histories'],w['decode_calls'])):
        hid=p['history_id'];tag=str(hid)+'/'
        meta=js(history['metadata']['path'],history['metadata']['sha256']);check(tag+'S68_row_identity',meta==original_meta[hid])
        check(tag+'per_history_receipt',obj(f'execution_01/history_{hid:02d}/receipt.json')==p and p['status']=='COMPLETE_HISTORY_ROUNDTRIP')
        check(tag+'recorded_decode_input_and_time',call['input_latent_body_sha256']==meta['tensors']['latent']['body_sha256'] and call['scale_factor']==.18215 and p['started_utc']<=call['started_utc']<=call['completed_utc']<=p['completed_utc'])
        events=progress[1+index*3:4+index*3];check(tag+'progress_call_times',call['started_utc']<=events[0]['utc']<=call['completed_utc']<=events[1]['utc']<=p['completed_utc']<=events[2]['utc'])
        arrays={}
        for name,desc in p['arrays'].items():
            body=read(desc['path'],binding['saved_payload_pins_from_worker_receipt'][desc['path']],'saved_FP32_NPY')
            a=np.load(io.BytesIO(body),allow_pickle=False)
            check(tag+name+'_descriptor',list(a.shape)==desc['shape']==[3,576,576] and str(a.dtype)==desc['dtype']=='float32' and a.nbytes==desc['body_bytes']==3981312 and hashlib.sha256(a.tobytes(order='C')).hexdigest()==desc['body_sha256'])
            channels=a.reshape(3,-1).tolist();check(tag+name+'_finite',all(math.isfinite(v) for ch in channels for v in ch));arrays[name]=channels
            r['decoded_payloads'].append(dict(path=desc['path'],kind='FP32',body_bytes=a.nbytes))
            if name=='reference_fp32':check(tag+'exact_reference_S68_tensor',desc['body_sha256']==p['reference_tensor_sha256']==meta['image_tensor_sha256'])
        ref,rec=arrays['reference_fp32'],arrays['reconstruction_raw_fp32'];nr=sum(len(ch) for ch in ref)
        differences=[y-x for ca,cb in zip(ref,rec) for x,y in zip(ca,cb)]
        mse=math.fsum(v*v for v in differences)/nr;mae=math.fsum(abs(v) for v in differences)/nr
        saved=p['raw_error_minus1_plus1'];cmp(tag+'raw_mse',mse,saved['mse'],rawtol);cmp(tag+'raw_mae',mae,saved['mae'],rawtol)
        lo=min(min(ch) for ch in rec);hi=max(max(ch) for ch in rec);below=sum(v < -1 for ch in rec for v in ch);above=sum(v > 1 for ch in rec for v in ch)
        check(tag+'raw_count_range_exact',nr==saved['pixel_channel_count']==995328 and lo==saved['reconstruction_min'] and hi==saved['reconstruction_max'] and below==saved['below_minus1_count'] and above==saved['above_plus1_count'])
        check(tag+'reference_declared_range',all(-1<=v<=1 for ch in ref for v in ch))
        pngchecks={}
        for name,channels in [('reference',ref),('reconstruction',rec)]:
            desc=p['pngs'][name];pb=read(desc['path'],binding['saved_payload_pins_from_worker_receipt'][desc['path']],'saved_PNG')
            with Image.open(io.BytesIO(pb)) as image:
                check(tag+name+'_PNG_shape',image.mode=='RGB' and image.size==(576,576) and desc['shape']==[576,576,3]);actual=image.tobytes()
            # Algebraically independent scalar form of fixed nearest uint8 quantizer.
            expected=bytes(int(math.floor(min(255.,max(0.,v*127.5+128.)))) for pixel in zip(*channels) for v in pixel)
            check(tag+name+'_PNG_fixed_quantization',expected==actual and hashlib.sha256(actual).hexdigest()==desc['pixel_sha256'])
            pngchecks[name]=dict(pixel_count=576*576,pixel_channel_bytes=len(actual),exact_fixed_quantization=expected==actual)
            r['decoded_payloads'].append(dict(path=desc['path'],kind='PNG_RGB',body_bytes=len(actual)))
        m=p['matching'];N=m['source_feature_count'];M=m['match_count'];sx,tx,idx=m['source_xy'],m['reconstruction_xy'],m['match_keypoint_ids']
        check(tag+'match_counts_ID_domains',len(sx)==len(tx)==len(idx)==M and len({a for a,b in idx})==M and len({b for a,b in idx})==M and all(type(a) is int and type(b) is int and 0<=a<N and 0<=b<m['reconstruction_feature_count'] for a,b in idx))
        check(tag+'coordinate_shape_domain',all(len(a)==2 and all(math.isfinite(v) and 0<=v<576 for v in a) for a in sx+tx))
        dist=[math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(sx,tx)]
        cmp(tag+'all_displacements',dist,m['displacements_px']);qs=[quantile(dist,q) for q in c['quantiles']] if dist else None
        cmp(tag+'displacement_quantiles',qs,m['quantiles_px']);cmp(tag+'displacement_max',max(dist) if dist else None,m['maximum_px'])
        check(tag+'availability_denominators',m['unmatched_count']==N-M and m['match_fraction']==(M/N if N else None) and m['unmatched_fraction']==((N-M)/N if N else None))
        check(tag+'match_status',m['status']==('MATCHES_AVAILABLE' if M else 'NO_ACCEPTED_MATCHES'))
        counts={str(q):sum(v<=q for v in dist) for q in c['cutoffs_px']}
        check(tag+'cutoff_counts_denominators',counts==m['cutoff_counts'] and m['cutoff_fraction_of_source']=={k:v/N if N else None for k,v in counts.items()} and m['cutoff_fraction_of_matches']=={k:v/M if M else None for k,v in counts.items()})
        for name,xy in [('source',sx),('reconstruction',tx)]:
            cov=coverage(xy);cmp(tag+name+'_span',cov['span_xy_fraction'],m[name+'_coverage']['span_xy_fraction']);check(tag+name+'_cells',cov['occupied_4x4_cells']==m[name+'_coverage']['occupied_4x4_cells'])
        r['rows'].append(dict(history_id=hid,mse=mse,mae=mae,pixel_channel_count=nr,reconstruction_min=lo,reconstruction_max=hi,below_minus1_count=below,above_plus1_count=above,source_feature_count=N,match_count=M,match_fraction=M/N if N else None,displacements_px=dist,displacement_quantiles=qs,cutoff_counts=counts,source_coverage=coverage(sx),reconstruction_coverage=coverage(tx),png_quantization=pngchecks))
        del arrays,ref,rec,differences,expected,actual,channels,a
    expected=[]
    expected += [(c[n]['path'],c[n]['sha256'],kind) for n,kind in [('s68_acceptance','accepted_S68_metadata'),('s68_receipt','accepted_S68_result_metadata')]]
    expected += [(h['metadata']['path'],h['metadata']['sha256'],'history_metadata') for h in c['histories']]
    expected += [(v['path'],v['sha256'],'original_source') for v in c['sources'].values()]
    expected += [(c['components'][n]['path'],c['components'][n]['sha256'],n) for n in ['vae_config','vae_weight']]
    expected += [(h[k]['path'],h[k]['sha256'],kind) for h in c['histories'] for k,kind in [('npz','S68_cached_npz_latent_only_decoded'),('png','historical_RGB_png')]]
    check('worker_readlist_exact',[(x['path'],x['sha256'],x['kind']) for x in w['reads']]==expected)
    r['model_observation_boundary']=dict(recorded_wrapper_decode_calls=5,recorded_weight_bytes_consumer_calls=1,recorded_weight_sha256=c['components']['vae_weight']['sha256'],scope='Source/receipt/progress consistency only. No live independent observation or weight-body/model rerun; original SD2.1 VAE identity remains UNKNOWN.')

if __name__=='__main__':
    started=utc();timer=time.perf_counter();r=dict(schema='s75-independent-saved-result-verification-v1',status='RUNNING',reviewer_role='/root/c2_v9_source_primary',started_utc=started,python=sys.version,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),binding_sha256=BINDING_SHA,reads=[],decoded_payloads=[],checks=[],rows=[],blockers=[],new_method_validated=False,scope='Saved FP32/PNG/coordinate verification only, math.fsum raw errors and scalar fixed quantizer/hypot. No neural model, SIFT, weight, original-photo or latent-body read.')
    with (O/'receipt.json').open('x') as f:
        try:
            run(r);r['blockers']=[x['name'] for x in r['checks'] if not x['pass']];r['status']='PASS_S75_INDEPENDENT_SAVED_RESULTS' if not r['blockers'] else 'DISCREPANCY_PRESERVED'
        except BaseException:r['status']='FAILED_PRESERVED';r['exception']=traceback.format_exc();r['blockers'].append('exception')
        r.update(completed_utc=utc(),elapsed_seconds=time.perf_counter()-timer,checks_passed=sum(x['pass'] for x in r['checks']),input_file_count=len(r['reads']),input_bytes=sum(x['bytes'] for x in r['reads']),decoded_payload_bytes=sum(x['body_bytes'] for x in r['decoded_payloads']))
        json.dump(r,f,indent=2,allow_nan=False);f.write('\n')
    (O/'receipt.json').chmod(0o444)
    print(json.dumps({k:r[k] for k in ['status','checks_passed','blockers','elapsed_seconds','input_file_count','input_bytes','decoded_payload_bytes']}))
    raise SystemExit(0 if not r['blockers'] else 1)
