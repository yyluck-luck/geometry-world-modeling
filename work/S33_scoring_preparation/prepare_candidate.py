#!/usr/bin/env python3
"""Only JSON/source identities and AST compilation; no images/arrays/math calls."""
import ast,copy,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
ENDS=['initial_0step','corrected_getter_400','global_rescaled_400','common_pair_scale_400']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def main():
    start=datetime.now(timezone.utc).isoformat();out=HERE/'manifest_candidate.json';assert not out.exists(),'Do not overwrite candidate'
    base=ROOT/'results/S32_consumer_scoring';rp=base/'receipt.json';assert sha(rp)=='834627965eaa4198e42a8a00c43951949bf45a15bbdd0e28f871e63d98017b37'
    r=read(rp);assert r['status']=='PASS';mp=ROOT/'work/S32_scoring_preparation/manifest.json';assert sha(mp)==r['scoring_manifest_sha256'];m=read(mp)
    rev=ROOT/'work/S32_independent_numeric_review_v2/receipt.json';assert sha(rev)=='2933625352cc2edb2d5581d78418eaffdc0ae108b8bbae41333a5fac8fbb2a97'
    assert read(rev)['status']=='PASS_INDEPENDENT_SAVED_NUMERIC_REVIEW'
    old={str(rp):sha(rp),str(mp):sha(mp),str(rev):sha(rev)}
    for name in ['metrics.json','per_frame.csv']:
        p=base/name;assert sha(p)==r['output_sha256'][name];old[str(p)]=sha(p)
    windows=[]
    for w in m['windows']:
        missing=w['id']=='fr2_desk_j1';directory=ROOT/'results/S33_pair_scale_control'/w['id']
        windows.append(dict(id=w['id'],availability='UNAVAILABLE_MISSING_POSE' if missing else 'PENDING_PRODUCER_TERMINAL',
            reason='MISSING_GIVEN_CAMERA_ASSOCIATION' if missing else 'Pending actual new PASS or FAILED; old48 remain unchanged',
            producer_receipt=dict(path=str(directory/'receipt.json'),sha256=None),frames=copy.deepcopy(w['frames']),
            endpoint=dict(name=ENDS[-1],status='UNAVAILABLE' if missing else 'PENDING',path=None if missing else str(directory/(ENDS[-1]+'.npz')),sha256=None,depth_key='depth',dtype='float32')))
    helper=ROOT/'work/S32_scoring_preparation/score_s32.py';original=ROOT/'scripts/score_s26b_consumer.py';policy=ROOT/'work/S32_preparation/B_contract.json'
    assert sha(helper)=='adb646284110b38741c311e893064558ca4d409ecc3b5e7e75c4540f1203c319'
    assert sha(original)=='02317889281583ae0fd8a12a1148811c9e9a0afb7bcf75275aea9fd1a34f5cc7'
    assert sha(policy)=='340c1b7b9e246fb088db8a50194d3003e1e384ecb05a24dc901bda2ff7bdca60'
    controls={str(p):sha(p) for p in [HERE/'score_s33.py',HERE/'protocol.md',Path(__file__).resolve(),helper,original,policy]}
    for p in [HERE/'score_s33.py',Path(__file__).resolve()]:ast.parse(p.read_text());compile(p.read_text(),str(p),'exec')
    d=dict(schema='s33-import48-score16-v1',status='CANDIDATE_NOT_FROZEN',prepared_utc=datetime.now(timezone.utc).isoformat(),
        output_root=str(ROOT/'results/S33_pair_scale_scoring'),endpoints=ENDS,resource=dict(cpu_threads=1,wall_seconds=120,rss_bytes=2*1024**3),
        selection_path=m['selection_path'],selection_sha256=m['selection_sha256'],old_scoring_sha256=old,control_sha256=controls,
        producer_contract=dict(path=str(ROOT/'work/S33_preparation/contract.json'),sha256='44a817a74afe10a16b758cc8fa6f7a17781d34d41ac575dd24e73b1ac1101400'),
        terminal_barrier=dict(path=str(ROOT/'work/S33_execution/dispatch_receipt.json'),sha256=None),windows=windows,
        fixed_denominators=dict(windows=4,metadata_pose_eligible=3,old_rows=48,new_rows=16,total_rows=64,total_endpoint_groups=16),
        no_old_rescoring=True,no_new_k=True,no_GT_fit=True,no_confidence_mask=True,no_far_cut=True,
        freeze_requirements=['Final new producer contract and source pre-review complete','All4 terminal receipts/dispatcher and all new PASS outputs SHA available',
            'Scorer/source/old-table identities reviewed; root writes separate FROZEN manifest and explicit caller SHA','No reading new endpoint or sensor bytes during this preparation'])
    assert sha(Path(d['producer_contract']['path']))==d['producer_contract']['sha256']
    write(out,d)
    receipt=dict(status='PASS_METADATA_AND_STATIC_PREPARATION_ONLY',started_utc=start,completed_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=sha(HERE/'score_s33.py'),protocol_sha256=sha(HERE/'protocol.md'),candidate_sha256=sha(out),prepare_sha256=sha(__file__),
        old_scoring_source_sha256=old,producer_contract=d['producer_contract'],controls=controls,checks=['Source AST parse and compile only','Existing sealed JSON/CSV identity verification','All4windows and originalGTmetadata copied without reading sensor images','Candidate remains unbound and non-executable'],
        actual_access=dict(RGB_image_bytes=0,prediction_NPZ_bytes=0,sensor_PNG_bytes=0,pose_file_bytes=0,scientific_function_calls=0,model_GA=0),
        scope='Implementation preparation, not runtime or metric validation; no fakePASS for unrun science')
    write(HERE/'preparation_receipt.json',receipt);print(json.dumps({k:receipt[k] for k in ['status','source_sha256','protocol_sha256','candidate_sha256','prepare_sha256']},indent=2))
if __name__=='__main__':main()
