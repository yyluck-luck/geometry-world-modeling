from pathlib import Path
from datetime import datetime,timezone
from types import SimpleNamespace
import ast,copy,hashlib,inspect,json,textwrap
root=Path(__file__).resolve().parents[2];path=root/'scripts/run_s11_source_regression.py';original_path=root/'src/s7_event_replay.py'
def require(ok,message):
    if not ok:raise ValueError(message)
ns={'__name__':'s11_pure_review','ast':ast,'copy':copy,'inspect':inspect,'textwrap':textwrap,'require':require}
tree=ast.parse(path.read_text());nodes=[]
for n in tree.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('VARIANTS','CONTRACT') for t in n.targets):nodes.append(n)
    if isinstance(n,ast.FunctionDef) and n.name in ('edit_mapping','source_decision_recorder'):nodes.append(n)
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
base={0:[2],1:[4,1],2:list(range(20))};before=copy.deepcopy(base);edit=ns['edit_mapping'];v=ns['VARIANTS'];outs={x:edit(base,x) for x in v}
checks={'five_variants_in_prespecified_order':v==('append_min_missing','drop_last','reverse','only_0','only_0_1_2'),'append_min_missing_all_rows':outs[v[0]]=={0:[2,0],1:[4,1,0],2:list(range(20))},'drop_last_preserve_nonempty':outs[v[1]]=={0:[2],1:[4],2:list(range(19))},'reverse_not_sorted':outs[v[2]]=={k:list(reversed(vals)) for k,vals in base.items()},'only_0':all(vals==[0] for vals in outs[v[3]].values()),'only_012':all(vals==[0,1,2] for vals in outs[v[4]].values()),'original_not_mutated':base==before,'all_outputs_keep_keys':all(set(m)==set(base) for m in outs.values())}
for label,values in [('empty',[]),('duplicate',[0,0]),('negative',[-1]),('future',[20]),('bool',[True]),('str',['0'])]:
    caught=False
    try:edit({0:values},v[0])
    except ValueError:caught=True
    checks['reject_'+label]=caught
original=next(n for n in ast.parse(original_path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='decision_trace')
oldns={'__name__':'s11_original_trace_ast_only'};exec(compile(ast.Module(body=[original],type_ignores=[]),str(original_path),'exec'),oldns)
adapted,receipt=ns['source_decision_recorder'](SimpleNamespace(decision_trace=oldns['decision_trace']))
a=ast.parse(receipt['adapted_source']);b=ast.parse(receipt['original_source']);terminal=a.body[0].body[-2]
checks['two_terminal_guards_use_maximum']=all(isinstance(c.comparators[0],ast.Name) and c.comparators[0].id=='maximum' for c in terminal.test.values[:2])
terminal.test=copy.deepcopy(b.body[0].body[-2].test)
checks['all_other_trace_AST_equal']=ast.dump(a)==ast.dump(b)
checks['recorder_callable_not_called']=callable(adapted)
signature=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='signature')
expr=copy.deepcopy(signature.body[1]);assert isinstance(expr,ast.Expr) and isinstance(expr.value,ast.Call) and expr.value.func.id=='require'
code=compile(ast.fix_missing_locations(ast.Module(body=[expr],type_ignores=[])),'<actual integer-type guard only>','exec')
for label,values,expected in [('valid_ints',(160,160,16),True),('fractional_width',(160.9,160,16),False),('integral_float_width',(160.,160,16),False),('bool_width',(True,160,16),False),('str_width',('160',160,16),False),('fractional_height',(160,160.9,16),False),('fractional_disk',(160,160,16.9),False),('bool_disk',(160,160,True),False)]:
    got=True
    try:exec(code,{'require':require,**dict(zip(('image_width','image_height','disk_resolution'),values))})
    except ValueError:got=False
    checks['type_guard_'+label]=got==expected
main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
exprs=[n for n in ast.walk(main) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='require' and any(isinstance(a,ast.Constant) and a.value=='Nonempty pre-run review evidence required' for a in n.value.args)]
assert len(exprs)==1;code=compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(exprs[0])],type_ignores=[])),'<actual nonempty review guard only>','exec')
for label,value,expected in [('valid',{'review_evidence_sha256':{'x':'y'}},True),('empty',{'review_evidence_sha256':{}},False),('missing',{},False),('wrong_type',{'review_evidence_sha256':['x']},False)]:
    got=True
    try:exec(code,{'require':require,'frozen':value})
    except ValueError:got=False
    checks['review_guard_'+label]=got==expected
assert all(checks.values())
result={'status':'PASS_PURE_PREPARATION','checked_utc':datetime.now(timezone.utc).isoformat(),'scope':'Only isolated source-edit Python-list fixtures, recording-only AST adaptation factory and exact type/nonempty-review guard expressions. No candidate factory, numerical-library import, real-array decode, reference/candidate selector or compiled NMS trace body execution.','source_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (path,original_path)},'checks':checks,'count':len(checks)}
assert result['source_sha256'][str(path.relative_to(root))]=='b2aa29f3c3486a062bbb2f1a388318e0be8ae72d5d9ce84d0f0926b5b69ed176'
(root/'work/S11_pre_run_review/source_pure_precheck_final.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
