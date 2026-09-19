"""Independent sealed S87 score review: integer histograms and exact Fractions.

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
SCORER_SHA='eaf4239615a5ead812c77013791bb5135f510142cfa8eb55e43c2881e956c089'
SCORE_CONTRACT_SHA='eb9052a4b0d39df1da2e7e03f6da5a8347f39a1b3e9fe513c61fedd6a95e02dc'
GEN_CONTRACT_SHA='337982b200182b50ade46aee4625c5c7ff3d87f5acce01bd48343451015c2538'
STRATEGIES=tuple((f'{f}_l{tag}',f,s) for tag,s in [('050',.5),('075',.75),('100',1.)] for f in ('Gpaste','Gterminal'))
ARMS=tuple(a for a,f,s in STRATEGIES)
ARM_META={a:(f,s) for a,f,s in STRATEGIES}
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
    family,strength=ARM_META[arm]
    row=dict(batch='S87',arm=arm,family=family,strength=strength,target_id=target,status='COMPLETE',missing_reason='')
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
        family,strength=ARM_META[arm]
        summary[arm]=dict(family=family,strength=strength,status='COMPLETE')
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


def load_npy(desc,path,dims,dtype):
    exact(desc['path'],str(path),'fixed array path')
    a=np.load(io.BytesIO(read(path,desc['file_sha256'])),allow_pickle=False)
    require(isinstance(a,np.ndarray) and a.shape==dims and a.dtype==np.dtype(dtype) and a.flags.c_contiguous,'array schema')
    expected=dict(shape=list(dims),dtype=dtype,body_bytes=a.nbytes,body_sha256=sha(a.tobytes()))
    tree({k:desc[k] for k in expected},expected,'array/body')
    a.flags.writeable=False
    return a


def guide_reference(old_rows, old_summary):
    selected=[r for r in old_rows if r['arm']=='Gguide']
    require([r['target_id'] for r in selected]==list(TARGETS),'old four guide targets')
    rows=[];summary={}
    for row in selected:
        want=dict(row)
        for region in REGIONS:
            want[region+'_mse']=ratio(row[region+'_sse'],row[region+'_channels'])
        tree(row,want,'old_guide/'+str(row['target_id']))
        rows.append(want)
    for region in REGIONS:
        sse=sum(r[region+'_sse'] for r in rows);n=sum(r[region+'_channels'] for r in rows)
        complete=all(r[region+'_channels']>0 for r in rows)
        summary[region]=dict(total_sse=sse,total_channels=n,complete_four_frames=complete,
            equal_frame_mean_mse=sum((r[region+'_mse'] for r in rows),Fraction())/4 if complete else None,
            pooled_mse=ratio(sse,n))
    tree(old_summary['Gguide'],summary,'old_guide_summary')
    exact(summary['full']['total_sse'],13571317266,'fixed old Gguide comparator SSE')
    return rows,summary


def contrasts(rows,summary,old_rows,old_summary):
    indexed={r['target_id']:r for r in old_rows};overall=[];pairs=[];scales={}
    for ci,(arm,family,strength) in enumerate(STRATEGIES):
        item=dict(arm=arm,family=family,strength=strength,comparison=arm+'-S86_Gguide')
        for region in REGIONS:
            a,b=summary[arm][region],old_summary[region]
            exact(a['total_channels'],b['total_channels'],'overall same region denominator')
            delta=a['total_sse']-b['total_sse'];n=a['total_channels']
            am,bm=a['equal_frame_mean_mse'],b['equal_frame_mean_mse']
            item[region+'_total_sse_difference']=delta
            item[region+'_pooled_mse_difference']=Fraction(delta,n*65025) if n else None
            mean=am-bm if am is not None and bm is not None else None
            item[region+'_mean_mse_difference']=mean
            if region!='full' and mean is not None:
                scales[f'contrasts/overall/{ci}/{region}_mean_mse_difference']=abs(am)+abs(bm)
        overall.append(item)
        for row in [r for r in rows if r['arm']==arm]:
            other=indexed[row['target_id']];pair=dict(arm=arm,target_id=row['target_id'])
            for region in REGIONS:
                n=row[region+'_channels'];exact(n,other[region+'_channels'],'target same denominator')
                delta=row[region+'_sse']-other[region+'_sse']
                pair[region+'_sse_difference']=delta
                pair[region+'_mse_difference']=Fraction(delta,n*65025) if n else None
            pairs.append(pair)
    return dict(overall=overall,per_target=pairs),scales


def decision(summary):
    envelope={}
    for family in ('Gpaste','Gterminal','all_six_new'):
        subset=[a for a,f,s in STRATEGIES if family=='all_six_new' or f==family]
        minimum=min(summary[a]['full']['total_sse'] for a in subset)
        envelope[family]=dict(candidate_arms=subset,min_total_sse=minimum,
            min_mse=Fraction(minimum,3981312*65025),
            tied_minimum_arms=[a for a in subset if summary[a]['full']['total_sse']==minimum])
    hits=[a for a in ARMS if summary[a]['full']['total_sse']<=13571317266]
    return dict(status='COMPLETE_SIX_STRATEGIES',all_six_complete=True,counterexample_arms=hits,
        multistep_necessary_for_this_MSE_refuted=bool(hits),
        decision='STOP_NECESSITY_CLAIM' if hits else 'FINITE_CONTROL_FAMILY_NOT_SUFFICIENT',envelope=envelope,
        selection='Retrospective already-seen-reference envelope; no validation result.',
        old_references='S86 Gpaste(.25)/Gterminal(.25) separate; G0 original chain once, not lambda0 replay.',
        limits='No perceptual/geometric/long-horizon/novelty inference; visible ghosting remains.')


def main(binding):
    exact(binding['accepted'],True,'root binding acceptance')
    exact(np.__version__,'1.26.4','NumPy');exact(sys.platform,'darwin','platform')
    exact(sha(read(Path(__file__))),binding['checker_sha256'],'checker SHA')
    read(HERE/'SCORE_REVIEW_PLAN.md',binding['review_plan_sha256'])
    exact(binding['scorer_sha256'],SCORER_SHA,'frozen scorer');read(HERE/'score_saved_controls.py',SCORER_SHA)
    exact(binding['scoring_contract_sha256'],SCORE_CONTRACT_SHA,'frozen score contract')
    cfg=meta(HERE/'SCORING_CONTRACT.json',SCORE_CONTRACT_SHA)
    exact(cfg['scorer_sha256'],SCORER_SHA,'contract scorer')
    exact(cfg['generation_contract']['sha256'],GEN_CONTRACT_SHA,'generation contract')
    gc=meta(HERE/'GENERATION_CONTRACT.json',GEN_CONTRACT_SHA)
    exact(gc['order'],list(ARMS),'six fixed order');exact(gc['target_ids'],list(TARGETS),'four fixed targets')
    generation=meta(GEN/'RECEIPT.json',binding['generation_receipt_sha256'])
    score=meta(SCORES/'RECEIPT.json',binding['scoring_receipt_sha256'])
    derivative=meta(HERE/'INDEPENDENT_DERIVATIVE_REVIEW.json',binding['derivative_review_sha256'])
    exact(derivative['status'],'PASS','derivative PASS')
    require(any(r['path']==str(GEN/'RECEIPT.json') and r['sha256']==binding['generation_receipt_sha256']
                for r in derivative['reads']),'derivative reviewed same generation')
    exact(generation['status'],'COMPLETE_SIX_DERIVED_CONTROLS_PENDING_REVIEW','generation complete')
    exact(generation['unrun_arms'],[],'no missing strategies')
    exact(generation['contract_sha256'],GEN_CONTRACT_SHA,'generation source')
    exact(score['status'],'COMPLETE_24_NEW_16_HISTORICAL_SCORES_PENDING_REVIEW','score complete')
    exact(score['scoring_contract_sha256'],SCORE_CONTRACT_SHA,'score bound source')
    exact(score['generation_receipt_sha256'],binding['generation_receipt_sha256'],'score same generation')
    for k,want in [('new_rows',24),('historical_rows',16),('rows_computed',24),
                   ('model_calls',0),('geometry_calls',0),('reference_reads',1),('new_method_validated',False)]:
        exact(score[k],want,'score metadata '+k)
    expected_files={'INPUT_BINDING.json','FRAME_SCORES.csv','FRAME_SCORES.json','ARM_SUMMARY.json',
        'CONTRASTS.json','DECISION.json','HISTORICAL_S86_FRAME_SCORES.csv',
        'HISTORICAL_S86_FRAME_SCORES.json','HISTORICAL_S86_ARM_SUMMARY.json'}
    amap={Path(s['path']).name:s for s in score['artifacts']}
    require(len(amap)==len(score['artifacts'])==9 and set(amap)==expected_files,'all nine unique artifacts')
    blobs={}
    for name,spec in amap.items():
        exact(spec['path'],str(SCORES/name),'artifact path')
        blobs[name]=read(SCORES/name,spec['sha256'],spec['bytes'])
    exact(sha(blobs['INPUT_BINDING.json']),binding['scoring_input_binding_sha256'],'input binding SHA')
    inputs=parse(blobs['INPUT_BINDING.json'])
    exact(inputs['generation_receipt_sha256'],binding['generation_receipt_sha256'],'input generation')
    exact(inputs['derivative_review_sha256'],binding['derivative_review_sha256'],'input derivative PASS')
    rootbind=meta(HERE/'ROOT_SCORING_BINDING.json',inputs['root_binding_sha256'])
    for k in ('scoring_contract_sha256','generation_receipt_sha256','derivative_review_sha256'):
        exact(rootbind[k],binding[k],'root scoring binding '+k)
    exact(rootbind['accepted'],True,'root accepted scoring')
    tree(inputs['prediction_descriptors'],{a:generation['arms'][a]['arrays'] for a in ARMS},'predictions binding')
    tree(inputs['mask_descriptor'],generation['image_mask'],'mask binding')
    old_rows=meta(cfg['old_rows']['path'],cfg['old_rows']['sha256'])
    old_summary=meta(cfg['old_summary']['path'],cfg['old_summary']['sha256'])
    old_csv=read(cfg['old_csv']['path'],cfg['old_csv']['sha256'])
    exact(len(old_rows),16,'historical row count')
    exact([(x['arm'],x['target_id']) for x in old_rows],
          [(a,t) for a in ('G0','Gpaste','Gterminal','Gguide') for t in TARGETS],'historical row identities')
    exact(blobs['HISTORICAL_S86_FRAME_SCORES.csv'],old_csv,'historical CSV unchanged bytes')
    tree(parse(blobs['HISTORICAL_S86_FRAME_SCORES.json']),old_rows,'historical JSON unchanged')
    tree(parse(blobs['HISTORICAL_S86_ARM_SUMMARY.json']),old_summary,'historical summary unchanged')
    guide_rows,guide_summary=guide_reference(old_rows,old_summary)
    emissions=score['emission_checks'];exact(len(emissions),24,'all24 emission records')
    for i,(arm,target) in enumerate((a,t) for a in ARMS for t in TARGETS):
        c=emissions[i];exact(c['arm'],arm,'emission arm');exact(c['target_id'],target,'emission target')
        exact(c['exact_uint8_match'],True,'emission exact')
    E=HERE.parent/'S86_fixed_warp_consumer/execution_01'
    exact(cfg['mask_path'],str(E/'image_mask.npy'),'original mask path')
    mask=load_npy(inputs['mask_descriptor'],E/'image_mask.npy',(4,1,576,576),'bool')[:,0]
    exact([int(m.sum()) for m in mask],[312396,292217,267572,263594],'fixed support counts')
    predictions={}
    for arm,family,strength in STRATEGIES:
        a=generation['arms'][arm];spec=generation['arm_receipts'][arm]
        exact(spec['path'],str(GEN/arm/'receipt.json'),'fixed arm receipt')
        require(meta(spec['path'],spec['sha256'])==a,'sealed arm body')
        exact(a['status'],'COMPLETE_DERIVED','complete arm')
        predictions[arm]=load_npy(inputs['prediction_descriptors'][arm]['targets_uint8'],
                                 GEN/arm/'targets_uint8.npy',(4,576,576,3),'uint8')
    ref=cfg['reference']
    exact(ref['path'],str(HERE.parent/'S70_fixed_context_generation/scoring_01/transformed_targets_uint8.npy'),'fixed reference path')
    exact(ref['sha256'],'e144e842fc36c795baa05841761670555a21bc7b9c36e0a56b8440b6a2324442','fixed reference SHA')
    exact(ref['bytes'],3981440,'fixed reference bytes')
    reference=np.load(io.BytesIO(read(ref['path'],ref['sha256'],ref['bytes'])),allow_pickle=False)
    require(reference.shape==(4,576,576,3) and reference.dtype==np.uint8
            and reference.flags.c_contiguous,'reference schema')
    rows=[frame(a,t,predictions[a][i],reference[i],mask[i]) for a in ARMS for i,t in enumerate(TARGETS)]
    tree(parse(blobs['FRAME_SCORES.json']),rows,'frames')
    reader=csv.DictReader(io.StringIO(blobs['FRAME_SCORES.csv'].decode()))
    exact(reader.fieldnames,list(rows[0]),'complete ordered CSV fields')
    csv_rows=list(reader);exact(len(csv_rows),24,'CSV all24 rows')
    for i,(row,want) in enumerate(zip(csv_rows,rows)):
        require(set(row)==set(want),'CSV no extra columns/cells')
        for k,v in want.items():
            if isinstance(v,Fraction):float_value(float(row[k]),v,f'CSV/{i}/{k}')
            else:exact(row[k],'' if v is None else str(v),f'CSV/{i}/{k}')
    summary=aggregate(rows);tree(parse(blobs['ARM_SUMMARY.json']),summary,'summary')
    expected,scales=contrasts(rows,summary,guide_rows,guide_summary)
    actual=parse(blobs['CONTRASTS.json']);tree(actual,expected,'contrasts',scales)
    for group in ('overall','per_target'):
        for i,row in enumerate(expected[group]):
            for key,value in row.items():
                if not key.endswith('_mse_difference'):continue
                label=f'contrasts/{group}/{i}/{key}';display=actual[group][i][key]
                sign=None if value is None else (1 if value>0 else -1 if value<0 else 0)
                dsign=None if display is None else (1 if display>0 else -1 if display<0 else 0)
                scale=scales.get(label,abs(value) if value is not None else 0)
                bound=16*sys.float_info.epsilon*float(scale)+16*float.fromhex('0x0.0000000000001p-1022')
                resolved=value is not None and abs(float(value))>bound
                if resolved:require(sign==dsign,'resolved contrast sign '+label)
                EXACT_DIRECTIONS.append(dict(field=label,exact_direction='NA' if sign is None else
                    {-1:'new_lower',0:'equal',1:'new_higher'}[sign],display_sign=dsign,
                    display_agrees=sign==dsign,display_resolves_nonzero_direction=resolved))
    expected_decision=decision(summary);tree(parse(blobs['DECISION.json']),expected_decision,'decision')
    read(GEN/'RECEIPT.json',binding['generation_receipt_sha256'])
    read(SCORES/'RECEIPT.json',binding['scoring_receipt_sha256'])
    return dict(status='PASS',new_frame_rows=24,new_region_rows=72,historical_rows_preserved=16,
        strategies=6,targets=list(TARGETS),overall_contrasts=6,per_target_contrasts=24,
        integer_algorithm='Per-channel511-bin signed-difference histograms; Python integer weighted sum, exact Fraction ratios/means/deltas.',
        exact_fraction_scalars=len(FLOAT_CHECKS),directions=EXACT_DIRECTIONS,
        exact_counterexample_arms=expected_decision['counterexample_arms'],
        all_new_envelope_ties=expected_decision['envelope']['all_six_new']['tied_minimum_arms'],
        model_calls=0,geometry_calls=0,reference_array_reads=1,raw_emission_recomputed=False,
        limits='Saved-data descriptive scores only.24 new frames from6 controls/4 correlated targets,16 historical rows unchanged. Raw emission checked by bound derivative/scorer, not rerun here. No perceptual, geometry, pure timing/dose, cross-scene or novelty conclusion.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--binding-sha256',required=True);args=parser.parse_args()
    output=HERE/'INDEPENDENT_SCORE_REVIEW.json';require(not output.exists(),'review exists: no retry/overwrite')
    report=dict(status='STARTED',started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),reads=READS,float_checks=FLOAT_CHECKS)
    def timeout(signum,frame):raise TimeoutError('120-second score review budget')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(120)
    try:
        binding=meta(HERE/'SCORE_REVIEW_BINDING.json',args.binding_sha256)
        report['binding_sha256']=args.binding_sha256;report.update(main(binding))
    except BaseException as exc:
        report.update(status='FAIL_PARTIAL_PRESERVED',error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc())
    finally:
        signal.alarm(0)
        report.update(completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-STARTED,
                      read_events=len(READS),peak_self_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,**COUNTS)
        with output.open('x') as handle:
            json.dump(report,handle,ensure_ascii=False,indent=2,allow_nan=False);handle.write('\n')
    print(json.dumps({k:report[k] for k in ('status','elapsed_seconds','exact_scalar_comparisons')}))
    raise SystemExit(0 if report['status']=='PASS' else 1)
