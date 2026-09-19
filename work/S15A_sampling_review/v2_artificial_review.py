from pathlib import Path
from decimal import Decimal as D
from datetime import datetime,timezone
import ast,copy,hashlib,importlib.util,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
v1=ROOT/'scripts/select_s15_samples.py';v2=ROOT/'scripts/select_s15_samples_v2.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
started=datetime.now(timezone.utc).isoformat();before={str(p.relative_to(ROOT)):sha(p) for p in [v1,v2,ROOT/'scripts/run_s15_history.py']};checks=[]
def must(ok,label):
 if not ok:raise AssertionError(label)
def note(name):checks.append(dict(name=name,status='PASS'))
def function_ast(path,name):return ast.dump(next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name))
for fn in ['nearest','select']:
 must(function_ast(v1,fn)==function_ast(v2,fn),fn+' changed');note(fn+'_AST_identical_to_reviewed_v1')
must(before['scripts/select_s15_samples.py']=='d225970650f611eb0f3e9ee944f4e9b2d39db0ce9c5e6675d5019edde1a1dcc7','v1 preserved');note('v1_frozen_source_preserved')
spec=importlib.util.spec_from_file_location('s15v2',v2);s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
prefix='rgbd_bonn_static_close_far/'
rgb=[(D(0),prefix+'rgb/000.png')]+[(D(1)+D('.4')*i,prefix+f'rgb/{i+1:03d}.png') for i in range(24)]
dep=[(t,p.replace('/rgb/','/depth/')) for t,p in rgb]
def text(rows):return '\n'.join(f'{t} {p[len(prefix):]}' for t,p in rows)+'\n'
expected=s.select(rgb,dep)
def cli_case(name,rgb_rows,dep_rows,absent=(),duplicate_receipt=False,duplicate_inventory=False):
 folder=HERE/('v2_artificial_'+name);folder.mkdir(exist_ok=False)
 for kind,rows in [('rgb',rgb_rows),('depth',dep_rows)]: (folder/(kind+'.txt')).write_text(text(rows))
 invrows=[dict(name=p) for t,p in rgb_rows+dep_rows if p not in absent]
 if duplicate_inventory:invrows.append(copy.deepcopy(invrows[0]))
 inv=folder/'inventory.json';inv.write_text(json.dumps(dict(entries=invrows)))
 members=[dict(name=prefix+kind+'.txt',path=str(folder/(kind+'.txt')),sha256=sha(folder/(kind+'.txt'))) for kind in ['rgb','depth']]
 if duplicate_receipt:members.append(copy.deepcopy(members[0]))
 metadata=folder/'metadata_receipt.json';metadata.write_text(json.dumps(dict(status='PASS',members=members)))
 protocol=folder/'synthetic_protocol.md';protocol.write_text('Artificial frozen protocol, no actual data bytes\n')
 command=[sys.executable,str(v2),'--metadata-receipt',str(metadata),'--metadata-receipt-sha256',sha(metadata),'--inventory',str(inv),'--inventory-sha256',sha(inv),'--protocol',str(protocol),'--protocol-sha256',sha(protocol),'--output',str(folder/'output')]
 p=subprocess.run(command,capture_output=True,text=True);(folder/'stdout.txt').write_text(p.stdout);(folder/'stderr.txt').write_text(p.stderr)
 receipt=json.loads((folder/'output/receipt.json').read_text())
 must(receipt['image_decodes']==receipt['trajectory_rows_read']==receipt['model_calls']==0,'forbidden reads')
 return folder/'output',p.returncode,receipt
# Missing unselected rows are retained and cannot affect previously fixed selection.
extra=(D('.5'),prefix+'depth/unselected.png');dep_extra=sorted(dep+[extra]);out,code,r=cli_case('unselected_depth_missing',rgb,dep_extra,[extra[1]])
payload=json.loads((out/'samples.json').read_text());missing=json.loads((out/'metadata_missing_members.json').read_text())
must(code==0 and r['status']=='PASS' and payload['samples']==expected,'unselected missing changed samples');note('unselected_depth_missing_passes_with_identical_24_samples')
must(payload['index_rows']['depth']==26 and missing['depth']==[dict(timestamp='.5',member=extra[1])].copy() if False else payload['index_rows']['depth']==26 and missing['depth']==[dict(timestamp='0.5',member=extra[1])],'all rows retained');note('missing_unselected_row_remains_in_full_index_and_missing_list')
# The initial RGB index t0 is retained even if its own image is absent/unselected.
out,code,r=cli_case('unselected_anchor_rgb_missing',rgb,dep,[rgb[0][1]])
payload=json.loads((out/'samples.json').read_text())
must(code==0 and payload['first_rgb_timestamp']=='0' and payload['samples']==expected,'missing initial index changed t0');note('unselected_missing_initial_rgb_does_not_shift_t0_or_samples')
# Selected missing nearest has an available close alternative: it must fail, not retime.
alt=(D('1.01'),prefix+'depth/alternative.png');dep_alt=sorted(dep+[alt]);out,code,r=cli_case('selected_depth_missing',rgb,dep_alt,[dep[1][1]])
candidates=json.loads((out/'selected_candidates_before_presence_gate.json').read_text())
must(code==1 and r['status']=='FAIL' and 'selected member missing' in r['error'] and not (out/'samples.json').exists(),'selected missing must fail');note('selected_missing_depth_fails_and_never_emits_success_samples')
must(candidates==expected and candidates[0]['depth_member']==dep[1][1] and candidates[0]['depth_member']!=alt[1],'missing nearest substituted');note('saved_candidate_keeps_missing_nearest_despite_available_alternative')
must(json.loads((out/'metadata_missing_members.json').read_text())['depth']==[dict(timestamp=str(dep[1][0]),member=dep[1][1])],'failure missing list');note('failure_preserves_missing_member_list')
# Same rule independently guards selected RGB, including original candidate time.
altr=(D('1.01'),prefix+'rgb/alternative.png');rgb_alt=sorted(rgb+[altr]);out,code,r=cli_case('selected_rgb_missing',rgb_alt,dep,[rgb[1][1]])
candidates=json.loads((out/'selected_candidates_before_presence_gate.json').read_text())
must(code==1 and r['status']=='FAIL' and candidates==expected and not (out/'samples.json').exists(),'selected RGB substitute');note('selected_missing_rgb_fails_without_nearest_replacement')
for name,kw,error in [('duplicate_receipt',dict(duplicate_receipt=True),'duplicate fetched member names'),('duplicate_inventory',dict(duplicate_inventory=True),'duplicate inventory names')]:
 out,code,r=cli_case(name,rgb,dep,**kw)
 must(code==1 and error in r['error'] and not (out/'samples.json').exists(),'duplicate names not rejected');note(name+'_explicitly_rejected')
must({str(p.relative_to(ROOT)):sha(p) for p in [v1,v2,ROOT/'scripts/run_s15_history.py']}==before,'production sources changed during review');note('v1_v2_and_runner_unchanged_during_review')
receipt=dict(schema='s15a-sampling-v2-difference-review-v1',status='PASS',started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat(),source_sha256=before,protocol_v2_sha256=sha(ROOT/'docs/S15A_NATIVE_HISTORY_PROTOCOL_V2.md'),checks=checks,check_count=len(checks),artificial_cli_runs=6,real_metadata_reads=0,real_image_reads=0,trajectory_reads=0,model_runs=0,scope='Only changed missing-member semantics and duplicate-name gates; v1 nearest/select AST byte structure identical, original46 checks not rerun.',context='Real missing counts are parent-reported and protocol-described; this reviewer did not reopen real indices or diagnose those counts.')
(HERE/'v2_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(status='PASS',checks=len(checks),v2_sha256=sha(v2))))
