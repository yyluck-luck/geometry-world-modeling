from pathlib import Path
import ast, datetime,hashlib,importlib.metadata as md,json,subprocess,sys
from packaging.requirements import Requirement
from packaging.tags import sys_tags
from packaging.utils import parse_wheel_filename,canonicalize_name
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent.parent;sys.path.insert(0,str(ROOT/'work/S17C_environment/site-packages'))
RANK={t:i for i,t in enumerate(sys_tags())};utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
tree=ast.parse((HERE/'prepare_wheels.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='metadata'],type_ignores=[]),'<unchanged metadata acquisition function>','exec'))
j=json.loads((HERE/'wheel_plan.json').read_text());j['previous_plan_sha256']=hashlib.sha256((HERE/'wheel_plan.json').read_bytes()).hexdigest();j['started_utc']=utc();j['wheels'].append(metadata(('wcwidth','0.2.13')))
versions={canonicalize_name(d.metadata['Name']):d.version for d in md.distributions()};versions.update({canonicalize_name(w['name']):w['version'] for w in j['wheels']})
checks=[]
for w in j['wheels']:
 for raw in w['requires']:
  r=Requirement(raw)
  if r.marker and not r.marker.evaluate({'extra':''}):continue
  actual=versions.get(canonicalize_name(r.name));checks.append({'package':w['name'],'requirement':raw,'actual':actual,'pass':actual is not None and r.specifier.contains(actual)})
j['requirements_checks']=checks;j['total_wheel_bytes']=sum(w['bytes'] for w in j['wheels']);j['ended_utc']=utc();j['status']='PASS_CANDIDATE_WHEEL_PLAN' if all(c['pass'] for c in checks) else 'FAILED';j.pop('elapsed_seconds',None)
(HERE/'wheel_plan_v2.json').write_text(json.dumps(j,indent=2));(HERE/'locked_wheels.txt').write_text('\n'.join(f'{w["name"]}=={w["version"]} --hash=sha256:{w["sha256"]}' for w in j['wheels'])+'\n');print(j['status'],len(j['wheels']),j['total_wheel_bytes'],len(checks))
