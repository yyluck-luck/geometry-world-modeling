#!/usr/bin/env python3
"""Bind S33 reviewer source/JSON metadata only; never open predictions or GT."""
from __future__ import annotations
import ast,hashlib,json,time
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
P=ROOT/'work/S33_preparation/contract.json'
PSHA='44a817a74afe10a16b758cc8fa6f7a17781d34d41ac575dd24e73b1ac1101400'
S=ROOT/'work/S33_scoring_preparation/manifest.json'
SSHA='83be08e12d3102487cf31f902c396db49567cfdbc63cbfeba12b02d3ab1665ab'
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
def require(ok,msg):
    if not ok:raise ValueError(msg)
def write(name,data):(HERE/name).write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def main():
    started=datetime.now(timezone.utc).isoformat();timer=time.perf_counter()
    require(not (HERE/'candidate.json').exists(),'Never overwrite candidate')
    ids={}
    def add(p,expected=None):
        p=Path(p).resolve();require(p.suffix in ('.py','.md','.json','.csv'),'Source/JSON/old table metadata only')
        h=sha(p);require(expected is None or h==expected,'Metadata identity changed: '+str(p))
        require(str(p) not in ids or ids[str(p)]==h,'Consistent duplicate identity');ids[str(p)]=h
    add(P,PSHA);add(S,SSHA);pc=read(P);sm=read(S)
    require(pc['status']==sm['status']=='FROZEN','Actual formal producer and scorer')
    require(sm['producer_contract']==dict(path=str(P),sha256=PSHA),'Same S33 producer')
    for name in ('recompute.py','protocol.md','prepare_candidate.py'):add(HERE/name)
    add(ROOT/'work/S28_independent_numeric_review/recompute.py','2bef151226649a87b5c8cc29e6bd5173b2ece63900837f100dbf4338006d40f2')
    add(ROOT/'work/S32_independent_numeric_review_v2/recompute.py','5222035721dafe55bff1d0aaaf62de110df9b97db3e285af5c2412a26b4f45bf')
    add(ROOT/'work/S33_preparation/run_s33.py','bd2711d50da6200453a40f73074e4b11d60a67d1e25d0a8ae22ad66f0fb9f392')
    for mapping in (sm['control_sha256'],sm['old_scoring_sha256']):
        for p,h in mapping.items():add(p,h)
    add(sm['terminal_barrier']['path'],sm['terminal_barrier']['sha256'])
    for w in sm['windows']:
        ref=w['producer_receipt'];add(ref['path'],ref['sha256'])
        old=pc['references'][w['id']];add(old['receipt'],old['receipt_sha256'])
        if old['status']=='PASS':
            d=Path(old['receipt']).parent;r=read(old['receipt'])
            add(d/'GA/C2a/initial_raw_metadata.json',old['files']['GA/C2a/initial_raw_metadata.json'])
            add(d/'decomposition.json',r['outputs']['decomposition.json'])
    sr=ROOT/'results/S33_pair_scale_scoring/receipt.json';add(sr)
    require(read(sr)['status']=='PASS' and read(sr)['scoring_manifest_sha256']==SSHA,'Completed scorer only')
    for name in ('recompute.py','prepare_candidate.py'):compile((HERE/name).read_text(),str(HERE/name),'exec',ast.PyCF_ONLY_AST)
    candidate=dict(schema='s33-independent-saved-review-candidate-v1',status='CANDIDATE_UNBOUND_DO_NOT_EXECUTE',created_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=ids,resource=dict(cpu_threads=1,wall_seconds=120,rss_bytes=2*1024**3),
        expected_scoring_manifest=dict(path=str(S),sha256=SSHA),expected_scoring_receipt=dict(path=str(sr),sha256=sha(sr)),
        fixed_scope=dict(old_rows_import_only=48,new_rows=16,total_rows=64,total_groups=16,new_actual_scored_rows=read(sr)['new_scored_rows'],new_NA_rows=read(sr)['new_NA_rows'],scale_gradient_saved_rows_per_PASS_window=400,matched_old_initial_raw_per_PASS_window=33,validated_new_initial_final_raw_per_PASS_window=66,full_pixel_mu_per_PASS_window=786432,new_k=0,new_SS_RMS=0),
        binding_schema='s33-independent-saved-review-binding-v1',new_model=0,new_GA=0,new_MST=0,new_backward=0,
        preparation_prediction_array_reads=0,preparation_GT_byte_reads=0,preparation_RGB_pixel_reads=0,preparation_weight_reads=0)
    write('candidate.json',candidate)
    write('preparation_receipt.json',dict(status='PASS_SOURCE_JSON_PREPARATION_ONLY',started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat(),wall_seconds=time.perf_counter()-timer,candidate_sha256=sha(HERE/'candidate.json'),source_identities=len(ids),source_sha256=ids,prediction_array_reads=0,GT_byte_reads=0,scientific_runs=0,scientific_imports=0,reviewer_not_executed=True))
    print(json.dumps(dict(candidate_sha256=sha(HERE/'candidate.json'),source_identities=len(ids))))
if __name__=='__main__':main()
