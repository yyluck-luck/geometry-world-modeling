#!/usr/bin/env python3
"""Static original-code equality for only the new S18 dependency path."""
import ast, hashlib, json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
ORIG=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tree(p):return ast.parse(p.read_text())
def cls(t,name):return next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name==name)
def func(c,name):return next(n for n in c.body if isinstance(n,ast.FunctionDef) and n.name==name)
def dump(n):return ast.dump(n,include_attributes=False)
start=datetime.now(timezone.utc).isoformat()
p=cls(tree(ORIG/'modeling/pipeline.py'),'VMemPipeline');u=tree(ORIG/'utils/util.py')
s=cls(tree(ROOT/'src/s18_original_kernels.py'),'OriginalGeometryKernel')
m=cls(tree(ROOT/'src/vmem_memory_kernel.py'),'MemoryKernel')
r=cls(tree(ROOT/'src/vmem_retrieval_kernel.py'),'RetrievalKernel')
checks=[]
def check(name,v):
 checks.append(dict(name=name,passed=bool(v)))
 if not v:raise AssertionError(name)
for name,copy in [('pointmap_to_surfels',s),('estimate_normal_from_pointmap',s),('merge_surfels',m),
 ('render_surfels_to_image',m),('process_retrieved_spatial_information',r),('get_frame_distribution',r)]:
 check('full original function AST '+name,dump(func(p,name))==dump(func(copy,name)))
source_construct=func(p,'construct_and_store_scene')
resize=[n for n in source_construct.body if n.lineno>=998 and n.end_lineno<=1022]
check('nine resize statement ASTs exact',len(resize)==9 and [dump(n) for n in resize]==[dump(n) for n in func(s,'resize_scene_inputs').body[:-1]])
store=[n for n in source_construct.body if n.lineno>=1026 and n.end_lineno<=1082]
check('complete original store statement block exact',len(store)==3 and [dump(n) for n in store]==[dump(n) for n in func(s,'store_reduced_scene').body])
memorytree=tree(ROOT/'src/vmem_memory_kernel.py')
check('full original Octree class AST',dump(cls(u,'Octree'))==dump(cls(memorytree,'Octree')))
check('original Surfel initializer AST',dump(func(cls(u,'Surfel'),'__init__'))==dump(func(cls(memorytree,'Surfel'),'__init__')))
paths=[ORIG/'modeling/pipeline.py',ORIG/'utils/util.py',ROOT/'src/s18_original_kernels.py',ROOT/'src/vmem_memory_kernel.py',ROOT/'src/vmem_retrieval_kernel.py',Path(__file__)]
report=dict(schema='s18-third-author-ast-static-v1',status='PASS_STATIC_ONLY',started_utc=start,completed_utc=datetime.now(timezone.utc).isoformat(),checks=checks,
 bindings={str(f):sha(f) for f in paths},data_reads=0,model_calls=0)
(Path(__file__).parent/'original_ast_receipt.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status=report['status'],checks=len(checks))))
