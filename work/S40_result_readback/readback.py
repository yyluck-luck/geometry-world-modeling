"""Read-only S40 saved-output identities and actual cross-batch cache consumption.

Preparation only until a real completed S40 run and external review contract
exist. No Torch/model/codec/renderer import. NumPy is deferred to saved tensors.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import struct
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
S40 = ROOT/'work/S40_declared_variant_generation'
PINS = {'launch_generation.py':'8ade694bc750f9693fc461257437af7b919b0c46755fc0eef2e21096d31e8860',
        'generation_gate.py':'ca16d8be631898e0200b14fcd0a19fd2d8bc6b91f32da4f5ada6038103ba7b14',
        'runtime_adapter.py':'d26f7e8990fd218273361c04484c8c0ea499a693486fd7bb040e3b03306a79c4',
        'PROTOCOL_DRAFT.md':'2c026b3dff79ca9155e5ad86a8c539b6597b6be7ed73b2c407b3d83ce75d7ced'}
WIDTHS = dict(bool=1,uint8=1,int8=1,uint16=2,int16=2,float16=2,bfloat16=2,
              uint32=4,int32=4,float32=4,uint64=8,int64=8,float64=8,complex64=8,complex128=16)
FIELDS = {'latents':'context_latents','encoder_embeddings':'context_encoder_embeddings',
          'c2ws':'context_c2ws','Ks':'context_Ks'}


class TensorDescriptor(dict):
    """Marks a descriptor that came from a raw archival kind=tensor node."""


def utc(): return datetime.now(timezone.utc).isoformat()
def require(ok, message):
    if not ok: raise ValueError(message)
def canonical(x):
    return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def core(x): return hashlib.sha256(canonical({k:v for k,v in x.items() if k!='review_receipts'})).hexdigest()
def write_new(path, x):
    with Path(path).open('x') as f:
        json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def signature(path):
    s=path.stat();return (s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_dev,s.st_ino)


class Reader:
    def __init__(self, seconds):
        self.started=time.monotonic();self.seconds=seconds;self.files={};self.tensor_files={}
        self.trace_descriptors_without_blob=0;self.np=None;self.groups=defaultdict(list)
    def tick(self): require(time.monotonic()-self.started<=self.seconds,'Readback time limit reached')
    def path(self, directory, name):
        p=(directory/name).resolve();require(p.is_relative_to(directory.resolve()),'Archive path escapes root')
        require(p.is_file(),'Missing saved file: '+str(p));return p
    def hash(self, path, expected=None, prefix=b''):
        self.tick();path=Path(path).resolve();before=signature(path)
        if not prefix and str(path) in self.files:
            old=self.files[str(path)]
            require(list(before)==old['stat'] and (expected is None or old['sha256']==expected),'Cached file changed')
            return old['sha256']
        h=hashlib.sha256(prefix);raw_h=hashlib.sha256();count=0
        with path.open('rb') as f:
            while b:=f.read(8*1024*1024): h.update(b);raw_h.update(b);count+=len(b);self.tick()
        value=h.hexdigest();require(signature(path)==before and count==before[0],'File changed while read')
        require(expected is None or value==expected,'Saved file SHA differs: '+str(path))
        item={'sha256':raw_h.hexdigest(),'bytes':count,'stat':list(before)}
        require(str(path) not in self.files or self.files[str(path)]==item,'Saved identity changed')
        self.files[str(path)]=item
        return value
    def doc(self,path,expected=None):
        path=Path(path).resolve();self.hash(path,expected)
        require(path.stat().st_size<256*1024**2,'JSON exceeds bounded reader memory scope')
        x=json.loads(path.read_text());require(list(signature(path))==self.files[str(path)]['stat'],'JSON changed')
        return x
    def chain(self,path,schema):
        self.hash(path);rows=[];previous='0'*64
        with Path(path).open('r') as f:
            for line in f:
                self.tick();require(line.endswith('\n'),'Unfinished event line')
                r=json.loads(line);h=r['sha256'];data={k:v for k,v in r.items() if k!='sha256'}
                require(r['schema']==schema and r['seq']==len(rows) and r['previous_sha256']==previous
                        and hashlib.sha256(canonical(data)).hexdigest()==h,'Broken event hash chain')
                require(r['evidence_kind']=='recorded_execution','Synthetic events cannot satisfy S40')
                previous=h;rows.append(r)
        require(rows,'Empty event chain');return rows
    def descriptor(self,d,directory,require_blob=True):
        require(d['kind']=='tensor' and d['byteorder']=='little' and d['order']=='C','Wrong tensor codec')
        shape=d['shape'];require(all(type(n) is int and n>=0 for n in shape),'Invalid tensor shape')
        require(d['dtype'] in WIDTHS and math.prod(shape)*WIDTHS[d['dtype']]==d['nbytes'],'Tensor byte count differs')
        if 'blob' not in d:
            require(not require_blob,'Full archive tensor has no payload')
            self.trace_descriptors_without_blob+=1;return
        p=self.path(directory,d['blob']);base={k:v for k,v in d.items() if k not in ('blob','sha256')}
        if str(p) in self.tensor_files:
            require(self.tensor_files[str(p)]==d,'Contradictory tensor descriptors');return
        require(p.stat().st_size==d['nbytes'],'Tensor size differs')
        self.hash(p,d['sha256'],prefix=canonical(base)+b'\0')
        require(self.files[str(p)]['sha256']==d['bytes_sha256'],'Tensor body hash differs')
        self.tensor_files[str(p)]=d
    def tree(self,node,directory,archive=True):
        if isinstance(node,dict):
            if node.get('kind')=='tensor':self.descriptor(node,directory,archive);return node
            for value in node.values():self.tree(value,directory,archive)
        elif isinstance(node,list):
            for value in node:self.tree(value,directory,archive)
        return node
    def metadata(self,n):
        k=n['kind']
        if k=='dict':
            pairs=[(self.metadata(x['key']),self.metadata(x['value'])) for x in n['items']]
            require(len(dict(pairs))==len(pairs),'Duplicate archival metadata keys');return dict(pairs)
        if k=='list':return [self.metadata(x) for x in n['items']]
        if k=='tuple':return tuple(self.metadata(x) for x in n['items'])
        if k=='scalar':
            scalar_types={'str':str,'int':int,'bool':bool,'NoneType':type(None)}
            require(n.get('type') in scalar_types and type(n.get('value')) is scalar_types[n['type']],
                    'Scalar archival type label differs from its JSON value')
            return n['value']
        if k=='python_float64':return struct.unpack('<d',bytes.fromhex(n['little_endian_hex']))[0]
        if k=='tensor':return TensorDescriptor(n)
        if k=='pil_image':
            image=dict(n);image['pixels']=self.metadata(n['pixels']);return image
        return n
    def array(self,d,ad):
        require(type(d) is TensorDescriptor,'Comparison input did not originate from a tensor archive node')
        require(self.tensor_files.get(str(self.path(ad,d['blob'])))==dict(d),'Comparison tensor descriptor not verified exactly')
        if self.np is None:
            import numpy as np
            require(np.__version__=='1.26.4','Use the existing frozen NumPy environment');self.np=np
        require(d['dtype']!='bfloat16','No BF16 numeric conversion in CPU-FP32 S40 comparisons')
        dtype=self.np.dtype(d['dtype']).newbyteorder('<')
        if d['nbytes']==0:return self.np.empty(d['shape'],dtype=dtype)
        return self.np.memmap(ad/d['blob'],mode='r',dtype=dtype,shape=tuple(d['shape']),order='C')
    def equal(self,a,b,label,cast=False):
        require(a.shape==b.shape,'Shape differs: '+label)
        converted=False
        if a.dtype!=b.dtype:
            require(cast and a.dtype==self.np.dtype('<f8') and b.dtype==self.np.dtype('<f4'),
                    'Unexpected dtype change: '+label)
            require(a.size<=8*16,'Only small original camera/K FP64→FP32 casts allowed')
            a=a.astype('<f4');converted=True
        av=a.reshape(-1).view('u1');bv=b.reshape(-1).view('u1')
        for i in range(0,av.size,1024*1024):
            self.tick();require(self.np.array_equal(av[i:i+1024*1024],bv[i:i+1024*1024]),'Actual bytes differ: '+label)
        return {'comparison':label,'bytes':int(av.size),'shape':list(a.shape),
                'mode':'FP64_to_FP32_then_bitwise' if converted else 'same_dtype_bitwise'}
    def same_desc(self,a,b,label,ad,cast=False):
        return self.equal(self.array(a,ad),self.array(b,ad),label,cast)
    def same_scalar(self,a,b,label,ad):
        if isinstance(a,dict) or isinstance(b,dict):
            require(isinstance(a,dict) and isinstance(b,dict) and
                    a.get('kind')==b.get('kind')=='tensor' and
                    math.prod(a['shape'])==math.prod(b['shape'])==1,'Scalar descriptor differs: '+label)
            return self.same_desc(a,b,label,ad)
        require(type(a) is type(b) and type(a) in (float,int),'Scalar type differs: '+label)
        require(struct.pack('<d',a)==struct.pack('<d',b) if type(a) is float else a==b,'Scalar bits differ: '+label)
        return {'comparison':label,'mode':'same_python_scalar_bits','type':type(a).__name__}


def trace_states(rows):
    """Saved-event semantics only; do not import/execute the original verifier."""
    order=('batch_begin','sample_call','sampler_enter','sampler_return','sample_return',
           'cache_commit','map_commit','batch_complete')
    batches={};active=None;closed=False
    for i,row in enumerate(rows):
        require(not closed,'Trace event follows session closure')
        ev,bid,p=row['event'],row['batch_id'],row['payload']
        if ev=='session':
            require(i==0 and bid is None,'Duplicate/misplaced trace session');continue
        require(i>0,'Trace must begin with its single session')
        if ev=='batch_begin':
            require(active is None and isinstance(bid,str) and bid and bid not in batches
                    and len(batches)<2,'Duplicate/overlapping trace batch')
            active=bid;batches[bid]={'state':ev,'callbacks':0,'event_sequences':{ev:row['seq']}}
        elif ev=='denoiser_call':
            require(bid==active and batches[bid]['state']=='sampler_enter','Callback outside its active sampler')
            require(p['callback_index']==batches[bid]['callbacks'],'Denoiser callback index differs')
            batches[bid]['callbacks']+=1
        elif ev in order[1:]:
            require(bid==active and batches[bid]['state']==order[order.index(ev)-1],'Wrong per-batch event transition')
            if ev=='sampler_return':require(p['denoiser_calls']==batches[bid]['callbacks'],'Denoiser callback total differs')
            batches[bid]['state']=ev;batches[bid]['event_sequences'][ev]=row['seq']
            if ev=='batch_complete':active=None
        elif ev=='observation':
            require(bid is None or bid==active,'Observation refers to inactive/unknown batch')
        elif ev=='session_end':
            require(i==len(rows)-1 and bid is None and active is None and p['batches']==len(batches)==2
                    and all(x['state']=='batch_complete' for x in batches.values()),'Incomplete/duplicate trace closure')
            closed=True
        else:raise ValueError('Unexpected failed/unknown trace event: '+str(ev))
    require(closed and len(batches)==2,'Two closed distinct trace batches required')
    return batches


def run(a,r):
    m=r.doc(a.manifest,a.manifest_sha256)
    require(m['schema']=='s40-declared-variant-two-batch-v1' and
            m['status']=='FROZEN_DECLARED_VARIANT_TWO_BATCH_EXECUTION','Real frozen S40 manifest required')
    require(m['variant']['exact_original_baseline'] is False and
            m['variant']['repo']=='stabilityai/sd-vae-ft-mse','Wrong declared component version')
    for name,pin in PINS.items():
        require(m['source_identities'][str(S40/name)]==pin,'Unreviewed S40 source version');r.hash(S40/name,pin)
    require(len(m['source_identities'])==218,'Unexpected source domain')
    for path,h in m['source_identities'].items():r.hash(path,h)
    for role,status in [('source_review','PASS_S40_GENERATION_SOURCE_REVIEW'),
                        ('runtime_freeze','READY_TO_ATTEMPT_S40_DECLARED_GENERATION')]:
        ref=m['review_receipts'][role];v=r.doc(ref['path'],ref['sha256'])
        require(v['status']==status and v['core_sha256']==core(m) and v['variant']==m['variant'],'Unbound S40 approval')
    ex=Path(a.execution_directory).resolve();output=Path(m['output_root']).resolve()
    launch=r.doc(ex/'receipt.json',a.launch_receipt_sha256)
    require(launch['status']=='DECLARED_VARIANT_EXTERNAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW'
            and launch['manifest_sha256']==a.manifest_sha256 and launch['returncode']==0
            and launch['worker_spawned'] is True and launch['source_unchanged_at_close'] is True
            and launch['source_sha256']==PINS['launch_generation.py']
            and not any(k in launch for k in ['limit_exceeded','unexpected_live_descendants']),'External run incomplete')
    worker=r.doc(ex/'worker_receipt.json',launch['worker_receipt_sha256'])
    require(worker['status']==launch['worker_status']=='DECLARED_VARIANT_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW'
            and worker['manifest_sha256']==a.manifest_sha256 and worker['source_sha256']==PINS['launch_generation.py']
            and worker['source_unchanged_at_close'] is True and worker['runtime_factory_calls']==1
            and worker['full_resource_checks']==1,'Worker scope/identity mismatch')
    load=r.doc(output/'runtime_loading.json')
    require(load['status']=='PASS_S40_DECLARED_VARIANT_COMPONENT_LOADING_ONLY' and
            load['manifest_sha256']==a.manifest_sha256 and load['variant']==m['variant'],'Wrong current runtime load')
    require(load['state_dict_loads'] and all(x['missing_keys']==[] and x['unexpected_keys']==[]
            for x in load['state_dict_loads']),'Incomplete current load records')
    summary=r.doc(output/'observation_summary.json',worker['observation_summary_sha256'])
    arref=worker['archive_receipt'];ad=output/'archive';td=output/'trace'
    require(Path(arref['path']).resolve()==ad/'manifest.json','Archive path mismatch')
    am=r.doc(arref['path'],arref['sha256'])
    require(am['status']==arref['status']=='ARCHIVE_COMPLETE' and am['evidence_kind']=='recorded_execution'
            and am['caller_manifest_sha256']==a.manifest_sha256 and am['source_identities']==m['source_identities']
            and not am['missing_required_names'] and am['failed_captures']==0,'Archive is not complete')
    actual={str(p.relative_to(ad)) for p in ad.rglob('*') if p.is_file() and p!=ad/'manifest.json'}
    require(actual==set(am['files']),'Archive physical inventory differs')
    for name,desc in am['tensor_descriptors'].items():
        require(desc['blob']==name,'Tensor manifest key differs');r.descriptor(desc,ad)
        require(r.doc(ad/name.replace('.bin','.json'))==desc,'Tensor sidecar differs')
    for name,item in am['files'].items():
        p=r.path(ad,name);r.hash(p,item['sha256']);require(p.stat().st_size==item['bytes'],'Archive payload size differs')
    ar=r.chain(ad/'events.jsonl','s35-full-original-output-archive-v1')
    require(len(ar)==am['event_count'] and ar[-1]['sha256']==am['last_event_sha256']
            and ar[0]['event']=='archive_start' and ar[-1]['event']=='archive_finalize','Archive event closure differs')
    pending={}
    for row in ar:
        p=row['payload'];ev=row['event']
        if ev=='capture_begin':pending[row['seq']]=(p['name'],p['occurrence'])
        elif ev=='capture_complete':
            require(pending.pop(p['begin_seq'])==(p['name'],p['occurrence']),'Broken capture pair')
            require(p['occurrence']==len(r.groups[p['name']]),'Capture occurrence order differs')
            r.tree(p['tree'],ad);r.groups[p['name']].append((row['seq'],r.metadata(p['tree'])))
        else:require(ev in ('archive_start','archive_finalize'),'Unexpected failed archive event')
    require(not pending and {k:len(v) for k,v in r.groups.items()}==am['archived_name_counts'],'Capture coverage differs')
    tr=r.chain(td/'events.jsonl','s20-generation-trace-v1');r.hash(td/'events.jsonl',worker['trace_events_sha256'])
    require(tr[0]['event']=='session' and tr[0]['payload']['manifest_sha256']==a.manifest_sha256
            and tr[0]['payload']['source_identities']==m['source_identities'] and tr[-1]['event']=='session_end','Wrong trace session')
    for row in tr:
        require(row['event'] not in ('failure','operation_failure'),'Trace recorded failure');r.tree(row['payload'],td,False)
    states=trace_states(tr)
    blobset={str(Path(p).relative_to(td)) for p in r.tensor_files if Path(p).is_relative_to(td)}
    require(blobset=={str(p.relative_to(td)) for p in (td/'blobs').rglob('*') if p.is_file()},'Unreferenced trace blob')
    def groups(name,n):
        v=r.groups[name];require(len(v)==n,'Missing/repeated actual event: '+name);return v
    init=groups('initial_output',1)[0][1]['cache']
    contexts=groups('context_output',2);commits=groups('cache_commit',2);maps=groups('map_commit',2)
    samples=groups('sample_output',2);batches=groups('batch_input',2)
    condin=groups('condition_input',2);condout=groups('condition_output',2);samplers=groups('sampler_input',2)
    samplerouts=groups('sampler_output',2)
    translations_in=groups('translation_input',2);translations_out=groups('translation_output',2)
    begin=[x for x in tr if x['event']=='batch_begin'];end=[x for x in tr if x['event']=='batch_complete']
    tc=[x for x in tr if x['event']=='cache_commit'];require(len(begin)==len(end)==len(tc)==2,'Trace needs two complete batches')
    require(list(states)==[x['batch_id'] for x in begin]==[x['batch_id'] for x in end]
            ==[x['batch_id'] for x in tc],'Trace batch identity order differs')
    def batch_capture(name,bid):
        found=[item for item in r.groups[name] if item[1].get('metadata',{}).get('batch_id')==bid]
        require(len(found)==1,'Expected one actual '+name+' in '+bid);return found[0]
    require(len(init['pil_frames'])==1,'Initial cache is not one frame')
    checks=[];selected=[]
    for j in range(2):
        bid=begin[j]['batch_id']
        for name,items in [('batch_input',batches),('cache_commit',commits),('map_commit',maps),
                ('sample_output',samples),('condition_input',condin),('condition_output',condout),
                ('sampler_input',samplers),('sampler_output',samplerouts),
                ('translation_input',translations_in),('translation_output',translations_out)]:
            require(items[j][0]==batch_capture(name,bid)[0],'Archive/trace batch correspondence differs: '+name)
        c=contexts[j][1];cc=commits[j][1];mc=maps[j][1];sample=samples[j][1]
        info=c['context_info'];raw_ids=info['context_time_indices']
        if j==0:
            require(type(raw_ids) is list and raw_ids==[0] and all(type(x) is int for x in raw_ids),
                    'First-batch context IDs are not the original Python [0] list')
            ids=list(raw_ids)
        else:
            require(isinstance(raw_ids,dict) and raw_ids.get('kind')=='tensor',
                    'Second-batch context IDs are not the original tensor descriptor')
            idarr=r.array(raw_ids,ad)
            require(idarr.ndim==1 and idarr.dtype.kind in 'iu','Context IDs are not integer vector')
            ids=[int(x) for x in idarr]
        selected.append(ids);history=1+4*j;newids=list(range(history,history+4))
        require(ids and len(set(ids))==len(ids) and all(0<=i<history for i in ids),'Invalid actual selected IDs')
        require(ids==begin[j]['payload']['selected_context_ids']==cc['selected_context_ids'],'Selected ordering differs')
        require(cc['retained_ids']==end[j]['payload']['retained_frame_ids']==newids,'Actual retained IDs differ')
        require(contexts[j][0]<batches[j][0]<condin[j][0]<condout[j][0]<samplers[j][0]<samples[j][0]<commits[j][0]<maps[j][0],
                'Archive causal event order differs')
        require(len(c['cache']['pil_frames'])==history and len(cc['cache']['pil_frames'])==history+4
                and len(mc['cache']['pil_frames'])==history+4,'Actual history 1/5/9 absent')
        require(len(mc['map']['surfel_Ks'])==[5,14][j] and len(mc['map']['surfel_depths'])==history+4,'Original map cache counts differ')
        require(sample['samples']['shape']==[8,3,576,576] and sample['samples_z']['shape']==[8,4,72,72],
                'Not original full-size all-eight outputs')
        require(cc['target_encoder_embeddings']['shape'][0]==8-len(ids) and cc['padding_size']==4-len(ids),
                'Padding/all-target CLIP rows differ')
        ei,eo=batch_capture('encode_image_input',bid),batch_capture('encode_image_output',bid)
        require(samplers[j][0]<samplerouts[j][0]<samples[j][0]<ei[0]<eo[0]<commits[j][0],
                'Sampler/sample/actual target encoding/commit order differs')
        checks.append(r.same_desc(samplerouts[j][1]['output'],sample['samples_z'],f'{bid}:sampler_output->all_samples_z',ad))
        checks.append(r.equal(r.array(sample['samples'],ad)[len(ids):],r.array(ei[1]['image'],ad),f'{bid}:all_target_samples->actual_encode_image_input'))
        checks.append(r.same_desc(eo[1]['result'],cc['target_encoder_embeddings'],f'{bid}:actual_encode_image_output->all_commit_embeddings',ad))
        for key,field in FIELDS.items():
            context_array=r.array(info[field],ad);require(context_array.shape[0]==len(ids),'Context row count differs')
            require(info[field]['sha256']==begin[j]['payload']['context_tensors'][field]['sha256'],'Trace/archive context identity differs')
            for slot,i in enumerate(ids):
                checks.append(r.equal(r.array(c['cache'][key][i],ad),context_array[slot],f'b{j+1}:{key}:cache{i}->context{slot}',cast=key in ('c2ws','Ks')))
            for i in range(history):checks.append(r.same_desc(c['cache'][key][i],cc['cache'][key][i],f'b{j+1}:old{key}{i}',ad))
            for i in range(history+4):checks.append(r.same_desc(cc['cache'][key][i],mc['cache'][key][i],f'b{j+1}:map_preserves_{key}{i}',ad))
        for k,i in enumerate(newids):
            checks.append(r.equal(r.array(sample['samples_z'],ad)[len(ids)+k],r.array(cc['cache']['latents'][i],ad),f'b{j+1}:sample_slot_to_latent{i}'))
            checks.append(r.equal(r.array(cc['target_encoder_embeddings'],ad)[k],r.array(cc['cache']['encoder_embeddings'][i],ad),f'b{j+1}:actual_clip_to_cache{i}'))
            for key,target in [('c2ws','target_c2ws'),('Ks','target_Ks')]:
                checks.append(r.equal(r.array(batches[j][1][target],ad)[k],r.array(cc['cache'][key][i],ad),f'b{j+1}:target_{key}->cache{i}'))
            for key in FIELDS:require(cc['cache'][key][i]['sha256']==tc[j]['payload']['retained'][k]['cache'][key]['sha256'],'Trace commit identity differs')
        args=condin[j][1]['args'];require(len(args)==6 and not condin[j][1]['kwargs'],'Unexpected original get_cond signature')
        for position,field in [(0,'context_latents'),(4,'context_encoder_embeddings')]:
            checks.append(r.same_desc(info[field],args[position],f'b{j+1}:{field}->actual_get_cond',ad))
        tin=translations_in[j][1];tout=translations_out[j][1]
        require(translations_in[j][0]<translations_out[j][0]<condin[j][0],'Translation/get_cond ordering differs')
        checks.append(r.equal(r.array(info['context_c2ws'],ad),r.array(tin['args'][0],ad)[:len(ids)],f'b{j+1}:context_cameras->translation_input'))
        checks.append(r.equal(r.array(batches[j][1]['target_c2ws'],ad),r.array(tin['args'][0],ad)[len(ids):],f'b{j+1}:all_target_cameras->translation_input'))
        checks.append(r.same_desc(tout['result'][1],args[1],f'b{j+1}:translated_cameras->get_cond',ad))
        checks.append(r.same_scalar(tout['result'][0],args[3],f'b{j+1}:translation_scalar->get_cond',ad))
        checks.append(r.equal(r.array(info['context_Ks'],ad),r.array(args[2],ad)[:len(ids)],f'b{j+1}:context_Ks->get_cond'))
        checks.append(r.equal(r.array(batches[j][1]['target_Ks'],ad),r.array(args[2],ad)[len(ids):],f'b{j+1}:all_target_Ks->get_cond'))
        mask=r.array(args[5],ad);require(mask.dtype.kind=='b' and mask.tolist()==[True]*len(ids)+[False]*(8-len(ids)),'get_cond mask differs')
        finalcond=condout[j][1]['result'];sampler=samplers[j][1]['inputs']
        for name in ('c','uc'):
            target='cond' if name=='c' else 'uc'
            for key,desc in finalcond[name].items():checks.append(r.same_desc(desc,sampler[target][key],f'b{j+1}:{name}.{key}->sampler',ad))
        for key,target in [('all_c2ws','c2w'),('all_Ks','K'),('input_masks','input_frame_mask')]:
            checks.append(r.same_desc(finalcond[key],sampler[target],f'b{j+1}:{key}->sampler',ad))
        replacement=r.array(sampler['cond']['replace'],ad);latent=r.array(info['context_latents'],ad)
        require(replacement.shape== (8,5,72,72),'Actual sampler replacement shape differs')
        for slot in range(len(ids)):
            checks.append(r.equal(latent[slot],replacement[slot,:4],f'b{j+1}:selected_latent{slot}->sampler_channels'))
            require(r.np.all(replacement[slot,4]==1),'Context mask channel not one')
    require(any(i>0 for i in selected[1]),'Second batch consumed no generated context')
    require(maps[0][0]<contexts[1][0],'First committed map does not precede second context')
    for key in FIELDS:
        checks.append(r.same_desc(init[key][0],contexts[0][1]['cache'][key][0],f'initial:{key}0',ad))
        for i in range(5):checks.append(r.same_desc(commits[0][1]['cache'][key][i],contexts[1][1]['cache'][key][i],f'cross_batch:{key}{i}',ad))
    for i in range(5):checks.append(r.same_desc(commits[0][1]['cache']['pil_frames'][i]['pixels'],contexts[1][1]['cache']['pil_frames'][i]['pixels'],f'cross_batch:pixels{i}',ad))
    require(summary['batches']==[{'batch_id':begin[j]['batch_id'],'selected_context_ids':selected[j],
            'retained_ids':list(range(1+4*j,5+4*j))} for j in range(2)],'Summary differs from real saved chain')
    counters=Counter();batch_euler=Counter()
    for row in tr:
        if row['event']=='observation' and row['payload'].get('name')=='actual_call':
            v=row['payload']['values'];counters[v['label']]+=1;require(v['ordinal']==counters[v['label']],'Observed call ordinal differs')
            if v['label']=='euler_step':batch_euler[row['batch_id']]+=1
    require(batch_euler==Counter({x['batch_id']:50 for x in begin}) and
            counters['main_model_forward']>0,'Original two 50-step calls absent')
    require(all(summary['counts'][k]==v for k,v in counters.items()),'Summary counters differ from trace')
    for path,item in r.files.items():require(list(signature(Path(path)))==item['stat'],'Input changed before readback seal')
    return {'variant':m['variant'],'manifest_sha256':a.manifest_sha256,'archive_files':len(am['files']),
            'archive_bytes':sum(x['bytes'] for x in am['files'].values()),'trace_events':len(tr),'archive_events':len(ar),
            'actual_selected_context_ids':selected,'verified_generated_ids_in_second_context':[i for i in selected[1] if i>0],
            'comparisons':checks,'actual_call_counts':dict(counters),'euler_steps_by_batch':dict(batch_euler),
            'trace_batch_states':states,'actual_archive_capture_counts':{k:len(v) for k,v in r.groups.items()},
            'trace_descriptors_without_saved_blob':r.trace_descriptors_without_blob,
            'scope':'Saved complete archive identities and actual first-output/cache/second-condition/sampler latent chain; no model, rendering or video quality recomputation'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['manifest','manifest-sha256','execution-directory','launch-receipt-sha256','out']:p.add_argument('--'+name,required=True)
    p.add_argument('--seconds',type=int,default=300);a=p.parse_args()
    require(a.seconds==300,'Freeze the 300-second readback budget; no automatic expansion')
    out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False)
    r=Reader(a.seconds);record={'schema':'s40-real-saved-output-readback-v1','status':'CHECKING',
        'started_utc':utc(),'readback_source_sha256':r.hash(Path(__file__)),
        'new_model_or_ga_runs':0,'weights_original_photo_gt_read':False,'quality_status':'NOT_EVALUATED'}
    try:
        result=run(a,r);write_new(out/'report.json',result)
        record.update(status='PASS_SAVED_S40_IDENTITIES_AND_CACHE_CONSUMPTION_ONLY',passed=True,
                      report_sha256=r.hash(out/'report.json'))
    except BaseException as exc:
        record.update(status='FAILED_OR_PARTIAL_S40_READBACK',passed=False,error_type=type(exc).__name__,
                      error=str(exc),traceback=traceback.format_exc())
    finally:
        record.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-r.started,identities=r.files,
            limitations=['No independent neural, renderer or GA recomputation; no visual-quality judgement.',
                'FP64 camera/K conversion is separately labelled; all remaining comparisons require identical dtype and bits.',
                'Trace descriptors lacking payloads are metadata only; complete raw archive and saved trace blobs are verified.',
                'Memory/RNG pointer restoration and mathematical correctness of the original model are not reconstructed.'])
        write_new(out/'receipt.json',record)
    return 0 if record['passed'] else 2


if __name__=='__main__':raise SystemExit(main())
