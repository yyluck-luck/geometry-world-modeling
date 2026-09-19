"""Independent sealed S86 score review: integer histograms and exact Fractions.

No scorer/consumer imports, raw emission re-run, model, image decoder or geometry.
Root must bind the final source, generation, scoring receipt and input binding.
"""
import argparse
import csv
import datetime as dt
from fractions import Fraction
import hashlib
import io
import json
import math
import os
from pathlib import Path
import resource
import signal
import sys
import time
import traceback

for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[key]='1'
import numpy as np

HERE=Path(__file__).resolve().parent
GEN=HERE/'execution_01'
SCORES=HERE/'scoring_01'
SCORER_SHA='1ec930bf6f3bb24265efbae3c5095a563d74a14d9451bb23c628625b803ac055'
SCORE_CONTRACT_SHA='7cebfeb86b3e86b68fede211c5da496367746227eeddfc709b19ad060a25c787'
GEN_CONTRACT_SHA='954c4353745280d5d3f48ac9db124b8a23aa877e1c59e9ecdd13f399416e844f'
ARMS=('G0','Gpaste','Gterminal','Gguide')
TARGETS=(20,21,22,23)
REGIONS=('full','support','hole')
READS, FLOAT_CHECKS, EXACT_DIRECTIONS = [], [], []
COUNTS={'exact_scalar_comparisons':0}
STARTED=time.monotonic()


def require(ok,why):
    if not bool(ok): raise ValueError(why)


def sha(data): return hashlib.sha256(data).hexdigest()


def read(path,digest=None,size=None):
    require(time.monotonic()-STARTED<120,'review wall budget')
    require(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<1024**3,'review sampled RSS budget')
    path=Path(path);data=path.read_bytes()
    READS.append(dict(path=str(path),bytes=len(data),sha256=sha(data)))
    require(digest is None or sha(data)==digest,'file SHA: '+str(path))
    require(size is None or len(data)==size,'file size: '+str(path))
    return data


def parse(data):
    def invalid(x): raise ValueError('nonfinite JSON '+x)
    return json.loads(data,parse_constant=invalid)


def meta(path,digest=None): return parse(read(path,digest))


def exact(actual,expected,label):
    COUNTS['exact_scalar_comparisons']+=1
    require(type(actual) is type(expected) and actual==expected,'exact mismatch: '+label)


def float_value(actual,expected,label,scale=None):
    if expected is None:
        exact(actual,None,label);return
    require(type(actual) in (int,float) and math.isfinite(actual),'finite display: '+label)
    value=float(expected)
    # Four-term means and their subtraction are allowed bounded binary64 rounding.
    magnitude=abs(value) if scale is None else float(scale)
    bound=16*sys.float_info.epsilon*magnitude+16*float.fromhex('0x0.0000000000001p-1022')
    error=abs(actual-value)
    FLOAT_CHECKS.append(dict(field=label,numerator=expected.numerator,denominator=expected.denominator,
        expected_float=value,actual=actual,max_allowed_abs_error=bound,abs_error=error))
    require(error<=bound,'display rounding mismatch: '+label)


def ratio(sse,channels):
    require(channels>=0 and sse>=0,'negative region total')
    require(channels or sse==0,'nonzero SSE for empty region')
    return Fraction(sse,channels*65025) if channels else None


def histogram_sse(pred,ref,selection):
    # Counts of signed differences; Python integers accumulate the weighted bins.
    # This does not use scorer's int64 difference-square-array/sum algorithm.
    total=0
    for c in range(3):
        difference=pred[:,:,c].astype(np.int16)-ref[:,:,c].astype(np.int16)
        bins=np.bincount(difference[selection].astype(np.int32)+255,minlength=511)
        require(len(bins)==511,'8bit difference bounds')
        total+=sum(int(count)*(index-255)**2 for index,count in enumerate(bins))
    return total


def frame(arm,target,pred,ref,mask):
    row=dict(arm=arm,target_id=target)
    selections={'full':np.ones(mask.shape,dtype=np.bool_),'support':mask,'hole':~mask}
    for region,select in selections.items():
        pixels=int(np.count_nonzero(select));channels=3*pixels
        sse=histogram_sse(pred,ref,select)
        row.update({region+'_pixels':pixels,region+'_channels':channels,
                    region+'_sse':sse,region+'_mse':ratio(sse,channels),region+'_empty':channels==0})
    require(row['full_sse']==row['support_sse']+row['hole_sse'],'independent SSE partition')
    return row


def aggregate(rows):
    summary={}
    for arm in ARMS:
        four=[r for r in rows if r['arm']==arm]
        require(len(four)==4 and [r['target_id'] for r in four]==list(TARGETS),'complete fixed4 targets')
        summary[arm]={}
        for region in REGIONS:
            sse=sum(r[region+'_sse'] for r in four)
            channels=sum(r[region+'_channels'] for r in four)
            complete=all(r[region+'_channels']>0 for r in four)
            mean=sum((r[region+'_mse'] for r in four),Fraction())/4 if complete else None
            summary[arm][region]=dict(total_sse=sse,total_channels=channels,complete_four_frames=complete,
                                      equal_frame_mean_mse=mean,pooled_mse=ratio(sse,channels))
    return summary


def tree(actual,expected,label,scales=None):
    if isinstance(expected,Fraction):
        float_value(actual,expected,label,None if scales is None else scales.get(label));return
    if isinstance(expected,dict):
        require(type(actual) is dict and set(actual)==set(expected),'dict fields: '+label)
        for k,v in expected.items(): tree(actual[k],v,label+'/'+k,scales)
    elif isinstance(expected,list):
        require(type(actual) is list and len(actual)==len(expected),'list count: '+label)
        for i,v in enumerate(expected): tree(actual[i],v,label+'/'+str(i),scales)
    else: exact(actual,expected,label)


def contrasts(rows,summary):
    indexed={(r['arm'],r['target_id']):r for r in rows};overall=[];per_target=[];scales={}
    for ci,control in enumerate(('Gterminal','G0','Gpaste')):
        comparison='Gguide-'+control;o=dict(comparison=comparison,negative_favors='Gguide')
        for region in REGIONS:
            g,b=summary['Gguide'][region],summary[control][region]
            require(g['total_channels']==b['total_channels'],'contrast same pooled denominator')
            delta=g['total_sse']-b['total_sse'];n=g['total_channels']
            gm,bm=g['equal_frame_mean_mse'],b['equal_frame_mean_mse']
            pooled=Fraction(delta,n*65025) if n else None
            mean=None if gm is None or bm is None else gm-bm
            o[region+'_total_sse_difference']=delta;o[region+'_pooled_mse_difference']=pooled
            o[region+'_mean_mse_difference']=mean
            if region!='full' and mean is not None:
                scales[f'contrasts/overall/{ci}/{region}_mean_mse_difference']=abs(gm)+abs(bm)
        overall.append(o)
        for target in TARGETS:
            p=dict(comparison=comparison,target_id=target)
            for region in REGIONS:
                g,b=indexed['Gguide',target],indexed[control,target]
                require(g[region+'_channels']==b[region+'_channels'],'contrast same target denominator')
                delta=g[region+'_sse']-b[region+'_sse'];n=g[region+'_channels']
                p[region+'_sse_difference']=delta
                p[region+'_mse_difference']=Fraction(delta,n*65025) if n else None
            per_target.append(p)
    warning='Descriptive one-scene comparisons. Region total SSE differences describe pooled error; their sign need not equal the sign of an equally weighted four-frame regional mean.'
    return dict(overall=overall,per_target=per_target,warning=warning),scales


def load_npy(desc,path,dims,dtype):
    exact(desc['path'],str(path),'fixed array path')
    a=np.load(io.BytesIO(read(path,desc['file_sha256'])),allow_pickle=False)
    require(isinstance(a,np.ndarray) and a.shape==dims and a.dtype==np.dtype(dtype) and a.flags.c_contiguous,'array schema')
    expected=dict(shape=list(dims),dtype=dtype,body_bytes=a.nbytes,body_sha256=sha(a.tobytes()))
    tree({k:desc[k] for k in expected},expected,'array/body')
    a.flags.writeable=False
    return a


def main(binding):
    exact(np.__version__,'1.26.4','NumPy');exact(sys.platform,'darwin','platform')
    exact(sha(read(Path(__file__))),binding['checker_sha256'],'checker SHA')
    exact(binding['scorer_sha256'],SCORER_SHA,'bound scorer');read(HERE/'score_outputs.py',SCORER_SHA)
    exact(binding['scoring_contract_sha256'],SCORE_CONTRACT_SHA,'bound score contract')
    cfg=meta(HERE/'SCORING_CONTRACT.json',SCORE_CONTRACT_SHA)
    require(cfg['arm_order']==list(ARMS) and cfg['target_order']==list(TARGETS),'fixed arm/target order')
    require(cfg['generation_contract']['sha256']==GEN_CONTRACT_SHA,'generation contract identity')
    gc=meta(HERE/'CONTRACT.json',GEN_CONTRACT_SHA)
    tree(cfg['generation_scoring_rules'],gc['scoring'],'frozen scoring rules')
    generation=meta(GEN/'RECEIPT.json',binding['generation_receipt_sha256'])
    score=meta(SCORES/'RECEIPT.json',binding['scoring_receipt_sha256'])
    exact(generation['status'],'COMPLETE_FOUR_FIXED_CONSUMER_ARMS_PENDING_REVIEW','generation complete')
    exact(score['status'],'COMPLETE_DESCRIPTIVE_SCORES_PENDING_INDEPENDENT_REVIEW','score complete')
    exact(score['rows_completed'],16,'all score rows');exact(score['scoring_contract_sha256'],SCORE_CONTRACT_SHA,'score receipt source')
    exact(score['generation_final_sha256'],binding['generation_receipt_sha256'],'score generation identity')
    for k in ['model_calls','original_RGB_reads','projection_calls']:exact(score[k],0,'score isolation '+k)
    exact(score['full_channel_denominator_per_frame'],995328,'frame denominator')
    exact(score['full_channel_denominator_all_four_frames'],3981312,'four frame denominator')
    artifact_map={Path(x['path']).name:x for x in score['artifacts']}
    expected_files={'INPUT_BINDING.json','FRAME_SCORES.csv','FRAME_SCORES.json','ARM_SUMMARY.json','CONTRASTS.json'}
    require(len(artifact_map)==len(score['artifacts'])==5 and set(artifact_map)==expected_files,'five unique scoring artifacts')
    blobs={}
    for name,spec in artifact_map.items():
        exact(spec['path'],str(SCORES/name),'score artifact fixed path')
        blobs[name]=read(SCORES/name,spec['sha256'],spec['bytes'])
    exact(sha(blobs['INPUT_BINDING.json']),binding['scoring_input_binding_sha256'],'pre-score input binding SHA')
    inputs=parse(blobs['INPUT_BINDING.json'])
    exact(inputs['generation_receipt_sha256'],binding['generation_receipt_sha256'],'input bound generation SHA')
    exact(inputs['generation_contract_sha256'],GEN_CONTRACT_SHA,'input bound generation contract')
    exact(inputs['generation_receipt_path'],str(GEN/'RECEIPT.json'),'input bound generation path')
    exact(inputs['generation_completed_utc'],generation['completed_utc'],'input generation completed time')
    tree(inputs['prediction_descriptors'],{a:generation['arms'][a]['arrays'] for a in ARMS},'prediction binding')
    tree(inputs['mask_descriptor'],generation['image_mask'],'mask binding')
    for a in ARMS:
        arm=meta(GEN/a/'receipt.json',inputs['arm_receipt_sha256'][a])
        require(arm==generation['arms'][a],'arm receipt body equals sealed generation')
        exact(arm['status'],'COMPLETE_CHAIN' if a in ('G0','Gguide') else 'COMPLETE_DERIVED','arm terminal state')
    checks=score['emission_checks'];require(len(checks)==16,'all16 emission prerequisite records')
    for i,(arm,target) in enumerate((a,t) for a in ARMS for t in TARGETS):
        c=checks[i];exact(c['arm'],arm,'emission arm');exact(c['target_id'],target,'emission target')
        exact(c['mismatching_channels'],0,'sealed emission check');exact(c['exact_uint8_match'],True,'sealed emission check')
    # Inspect all prediction bytes and identities before this review reads reference.
    mask=load_npy(inputs['mask_descriptor'],GEN/'image_mask.npy',(4,1,576,576),'bool')[:,0]
    predictions={a:load_npy(inputs['prediction_descriptors'][a]['targets_uint8'],GEN/a/'targets_uint8.npy',(4,576,576,3),'uint8') for a in ARMS}
    ref=cfg['reference'];require(ref['path']==gc['scoring']['reference_path'] and ref['sha256']==gc['scoring']['reference_sha256'] and ref['bytes']==gc['scoring']['reference_bytes'],'fixed reference identity')
    reference=np.load(io.BytesIO(read(ref['path'],ref['sha256'],ref['bytes'])),allow_pickle=False)
    require(reference.shape==(4,576,576,3) and reference.dtype==np.uint8 and reference.flags.c_contiguous,'reference schema')
    rows=[frame(arm,target,predictions[arm][i],reference[i],mask[i]) for arm in ARMS for i,target in enumerate(TARGETS)]
    tree(parse(blobs['FRAME_SCORES.json']),rows,'frames')
    csv_reader=csv.DictReader(io.StringIO(blobs['FRAME_SCORES.csv'].decode()))
    exact(csv_reader.fieldnames,list(rows[0]),'CSV complete ordered17 fields')
    csv_rows=list(csv_reader);exact(len(csv_rows),16,'CSV complete16 rows')
    for i,(row,want) in enumerate(zip(csv_rows,rows)):
        require(set(row)==set(want),'CSV no extra cells')
        for key,value in want.items():
            text=row[key]
            if isinstance(value,Fraction):float_value(float(text),value,f'CSV/{i}/{key}')
            else:exact(text,'' if value is None else str(value),f'CSV/{i}/{key}')
    summary=aggregate(rows);tree(parse(blobs['ARM_SUMMARY.json']),summary,'summary')
    expected,scales=contrasts(rows,summary);actual=parse(blobs['CONTRASTS.json'])
    tree(actual,expected,'contrasts',scales)
    for group in ['overall','per_target']:
        for i,row in enumerate(expected[group]):
            for key,value in row.items():
                if key.endswith('_mse_difference'):
                    display=actual[group][i][key];label=f'contrasts/{group}/{i}/{key}'
                    sign=None if value is None else (1 if value>0 else -1 if value<0 else 0)
                    display_sign=None if display is None else (1 if display>0 else -1 if display<0 else 0)
                    # Exact rational directions are authoritative; cancellation-level
                    # float display cannot replace them and is explicitly reported.
                    scale=scales.get(label,abs(value) if value is not None else 0)
                    bound=16*sys.float_info.epsilon*float(scale)+16*float.fromhex('0x0.0000000000001p-1022')
                    resolved=value is not None and (value==0 or abs(float(value))>bound)
                    if resolved and value!=0:require(display_sign==sign,'resolved contrast direction: '+label)
                    EXACT_DIRECTIONS.append(dict(field=label,exact_direction='NA' if sign is None else {-1:'Gguide_lower',0:'equal',1:'Gguide_higher'}[sign],display_sign=display_sign,display_agrees=sign==display_sign,display_resolves_nonzero_direction=resolved and value!=0))
    read(GEN/'RECEIPT.json',binding['generation_receipt_sha256']);read(SCORES/'RECEIPT.json',binding['scoring_receipt_sha256'])
    return dict(status='PASS',frame_rows=16,region_rows=48,arms=4,targets=[20,21,22,23],
        integer_algorithm='Per-channel 511-bin signed uint8 difference histograms, weighted and summed using Python arbitrary-precision integers.',
        exact_fraction_scalars=len(FLOAT_CHECKS),directions=EXACT_DIRECTIONS,model_calls=0,geometry_calls=0,
        raw_emission_recomputed=False,reference_array_reads=1,
        scope='Sealed-data score arithmetic only. Full/support/hole integers, NA,4-frame means/pooled and3 overall+12target contrasts checked. Original emission was validated by the bound scoring run; this checker does not claim a second raw-to-uint8 verification. One already exposed scene/4 correlated targets; no statistical superiority, perceptual/geometry accuracy or novelty claim.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--binding-sha256',required=True);args=parser.parse_args()
    output=HERE/'INDEPENDENT_SCORE_REVIEW.json';require(not output.exists(),'review already exists: no retry/overwrite')
    report=dict(status='STARTED',started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),reads=READS,float_checks=FLOAT_CHECKS)
    def timeout(signum,frame):raise TimeoutError('120-second score review budget')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(120)
    try:
        binding=meta(HERE/'SCORE_REVIEW_BINDING.json',args.binding_sha256)
        report['binding_sha256']=args.binding_sha256;report.update(main(binding))
    except BaseException as error:
        report.update(status='FAIL_PARTIAL_PRESERVED',error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc())
    finally:
        signal.alarm(0);report.update(completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-STARTED,read_events=len(READS),peak_self_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,**COUNTS)
        with output.open('x') as f:json.dump(report,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:report[k] for k in ['status','elapsed_seconds','exact_scalar_comparisons']}))
    raise SystemExit(0 if report['status']=='PASS' else 1)
