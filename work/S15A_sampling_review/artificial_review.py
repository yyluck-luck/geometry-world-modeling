from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal as D
import copy,hashlib,importlib.util,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
source=ROOT/'scripts/select_s15_samples.py'
started=datetime.now(timezone.utc).isoformat()
spec=importlib.util.spec_from_file_location('author_selector',source);s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
checks=[]
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
before=digest(source)
def check(name,fn,fail=False):
 try:result=fn()
 except Exception as e:
  if not fail:raise
  checks.append(dict(name=name,status='PASS',expected_error=repr(e)))
 else:
  if fail:raise AssertionError(name+' not rejected')
  checks.append(dict(name=name,status='PASS'))
def must(ok):
 if not ok:raise AssertionError('independent expected result mismatch')
def stream(kind,offset=D(0),shift=D(0)):
 times=[offset]+[offset+D(1)+D('.4')*i+shift for i in range(24)]
 return [(t,f'rgbd_bonn_static_close_far/{kind}/{i:03d}.png') for i,t in enumerate(times)]
def as_text(rows):return '# artificial only\n\n'+'\n'.join(f'{t} {p.split("/",1)[1]}' for t,p in rows)+'\n'
rgb=stream('rgb');dep=stream('depth')
inventory={p:dict(name=p) for _,p in rgb+dep}
check('valid_parse_comments',lambda:must(s.parse_index(as_text(rgb),'rgb',inventory)==rgb))
selected=s.select(rgb,dep)
check('normal_24_exact_order_role_split',lambda:must(len(selected)==24 and [a['role'] for a in selected]==['history']*20+['future_target']*4 and [D(a['rgb_timestamp']) for a in selected]==[D(1)+D('.4')*i for i in range(24)]))
# Independent nearest reference is a complete linear search, not bisect.
def reference(rows,q):return min(rows,key=lambda row:(abs(row[0]-q),row[0]))
for q in [D('-.1'),D('0'),D('.01'),D('.5'),D('1.005'),D('1.2'),D('1.399'),D('10.2'),D('10.3')]:
 check('nearest_linear_reference_'+str(q),lambda q=q:must(s.nearest(rgb,q)==reference(rgb,q)))
check('rgb_exact_tie_earlier',lambda:must(s.nearest([(D('.99'),'early'),(D('1.01'),'late')],D(1))[1]=='early'))
check('depth_exact_tie_earlier',lambda:must(s.nearest([(D('1.015'),'early'),(D('1.035'),'late')],D('1.025'))[1]=='early'))
check('rgb_inclusive_025_boundary',lambda:must(all(D(x['rgb_sampling_gap_seconds'])==D('.025') for x in s.select(stream('rgb',shift=D('.025')),stream('depth',shift=D('.025'))))))
check('rgb_just_over_025_boundary',lambda:s.select(stream('rgb',shift=D('.025000000001')),stream('depth',shift=D('.025000000001'))),True)
check('depth_inclusive_025_boundary',lambda:must(all(D(x['rgb_depth_gap_seconds'])==D('.025') for x in s.select(rgb,stream('depth',shift=D('.025'))))))
check('depth_just_over_025_boundary',lambda:s.select(rgb,stream('depth',shift=D('.025000000001'))),True)
offset=D('1500000000.123456789')
check('unix_scale_boundary_retains_decimal',lambda:must(all(D(x['rgb_sampling_gap_seconds'])==D('.025') for x in s.select(stream('rgb',offset,D('.025')),stream('depth',offset,D('.025'))))))
check('unix_scale_just_over_boundary',lambda:s.select(stream('rgb',offset,D('.025000000001')),stream('depth',offset,D('.025000000001'))),True)
check('depth_target_is_actual_rgb_not_nominal',lambda:must(all(D(x['rgb_depth_gap_seconds'])==D('.010') for x in s.select(stream('rgb',shift=D('.020')),stream('depth',shift=D('.030'))))))
check('missing_last_rgb_no_clipping',lambda:s.select(rgb[:-1],dep),True)
check('missing_last_depth_no_clipping',lambda:s.select(rgb,dep[:-1]),True)
check('empty_nearest_fails',lambda:s.nearest([],D(0)),True)
check('empty_parse_fails',lambda:s.parse_index('# nothing\n','rgb',inventory),True)
check('short_index_fails',lambda:s.parse_index(as_text(rgb[:23]),'rgb',inventory),True)
check('duplicate_timestamp',lambda:s.parse_index(as_text([rgb[0],(rgb[0][0],rgb[1][1])]+rgb[2:]),'rgb',inventory),True)
check('descending_timestamp',lambda:s.parse_index(as_text([rgb[1],rgb[0]]+rgb[2:]),'rgb',inventory),True)
check('duplicate_index_path',lambda:s.parse_index(as_text(rgb[:-1]+[(rgb[-1][0],rgb[-2][1])]),'rgb',inventory),True)
for literal in ['NaN','Infinity','-Infinity']:
 check('nonfinite_'+literal,lambda literal=literal:s.parse_index(literal+' rgb/000.png\n'+as_text(rgb[1:]),'rgb',inventory),True)
check('invalid_timestamp_token',lambda:s.parse_index('oops rgb/000.png\n'+as_text(rgb[1:]),'rgb',inventory),True)
check('three_columns',lambda:s.parse_index(as_text(rgb)+'100 rgb/999.png extra','rgb',inventory),True)
check('one_column',lambda:s.parse_index(as_text(rgb)+'100','rgb',inventory),True)
for name,path in [('absolute','/rgb/000.png'),('traversal','rgb/../000.png'),('wrong_stream','depth/000.png'),('wrong_extension','rgb/000.jpg'),('backslash','rgb\\000.png'),('missing_frozen_member','rgb/missing.png'),('nested_path','rgb/nested/000.png')]:
 check(name,lambda path=path:s.parse_index('0 '+path+'\n'+as_text(rgb[1:]),'rgb',inventory),True)
dup_rgb=rgb[:-1]+[(rgb[-1][0],rgb[-2][1])]
dup_dep=dep[:-1]+[(dep[-1][0],dep[-2][1])]
check('selected_rgb_paths_24_unique',lambda:s.select(dup_rgb,dep),True)
check('selected_depth_paths_24_unique',lambda:s.select(rgb,dup_dep),True)
# CLI uses only freshly manufactured local metadata and freezes. No real indices read.
fixture=HERE/'artificial_cli_inputs';fixture.mkdir(exist_ok=False)
for kind,rows in [('rgb',rgb),('depth',dep)]: (fixture/(kind+'.txt')).write_text(as_text(rows))
inv=fixture/'inventory.json';inv.write_text(json.dumps(dict(entries=list(inventory.values()))))
proto=fixture/'protocol.md';proto.write_text('Artificial protocol bytes only\n')
meta=fixture/'metadata.json';meta.write_text(json.dumps(dict(status='PASS',members=[dict(name='rgbd_bonn_static_close_far/'+kind+'.txt',path=str(fixture/(kind+'.txt')),sha256=digest(fixture/(kind+'.txt'))) for kind in ('rgb','depth')])))
args=[sys.executable,str(source),'--metadata-receipt',str(meta),'--metadata-receipt-sha256',digest(meta),'--inventory',str(inv),'--inventory-sha256',digest(inv),'--protocol',str(proto),'--protocol-sha256',digest(proto)]
for mode in ('success','bad_sha'):
 command=args+['--output',str(HERE/('artificial_cli_'+mode))]
 if mode=='bad_sha':command[command.index('--metadata-receipt-sha256')+1]='0'*64
 p=subprocess.run(command,capture_output=True,text=True)
 (HERE/f'cli_{mode}_stdout.txt').write_text(p.stdout);(HERE/f'cli_{mode}_stderr.txt').write_text(p.stderr)
 rec=json.loads((HERE/('artificial_cli_'+mode)/'receipt.json').read_text())
 must(p.returncode==(0 if mode=='success' else 1) and rec['status']==('PASS' if mode=='success' else 'FAIL') and rec['image_decodes']==rec['model_calls']==rec['trajectory_rows_read']==0)
 checks.append(dict(name='cli_'+mode+'_receipt_and_exit',status='PASS'))
 if mode=='success':
  saved=json.loads((HERE/'artificial_cli_success/samples.json').read_text());must(saved['samples']==selected)
  checks.append(dict(name='cli_samples_equal_independent_expected',status='PASS'))
# A semantic caution: duplicate receipt rows are collapsed by dict construction.
dup_members=json.loads(meta.read_text());dup_members['members'].append(copy.deepcopy(dup_members['members'][0]));(fixture/'metadata_duplicate.json').write_text(json.dumps(dup_members))
# No CLI adversarial run here; report source observation without changing production.
must(digest(source)==before)
receipt=dict(schema='s15a-sampling-different-author-review-v1',status='PASS_WITH_MINOR_NOTE',started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat(),selector_sha256=before,protocol_sha256=digest(ROOT/'docs/S15A_NATIVE_HISTORY_PROTOCOL.md'),checks=checks,check_count=len(checks),real_metadata_reads=0,real_image_decodes=0,real_model_calls=0,artificial_cli_runs=2,independent_reference='Decimal linear global minimization vs author bisect',minor_note='main converts receipt members/inventory entries to dictionaries without rejecting duplicate names. Fixed independently validated inventory and exact metadata-fetch contract reduce current risk; adding explicit uniqueness checks would make the selector self-contained. No production files modified.')
(HERE/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(dict(status=receipt['status'],checks=len(checks),selector_sha256=before)))
