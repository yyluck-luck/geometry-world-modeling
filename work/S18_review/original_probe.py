#!/usr/bin/env python3
"""Tiny artificial checks of pinned original code; no archived data/model input."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import traceback
from types import SimpleNamespace
from typing import Union
import numpy as np
import torch
import torch.nn.functional as F

OUT = Path(__file__).resolve().parent
ORIG = Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def utc(): return datetime.now(timezone.utc).isoformat()
report = dict(schema='s18-third-author-artificial-original-v1', status='RUNNING', started_utc=utc(),
              source_sha256=sha(Path(__file__)), original_rgb_reads=0, archived_npz_reads=0,
              gt_reads=0, model_calls=0, checks=[], observations={})
def check(name, value, **details):
    report['checks'].append(dict(name=name, passed=bool(value), **details))
    if not value: raise AssertionError(name)

try:
    torch.set_num_threads(8)
    torch.manual_seed(0)
    np.random.seed(0)
    report['versions'] = dict(numpy=np.__version__, torch=torch.__version__, torch_threads=torch.get_num_threads())
    check('fixed numpy 1.26.4 and torch 2.7.0', np.__version__=='1.26.4' and torch.__version__=='2.7.0')
    sources = {'modeling/pipeline.py':'90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e',
               'utils/util.py':'0b71dcf6d4a43109d785f49d9c6def37b1256c4d189ab9438bfb185f3099f013'}
    for path, expected in sources.items(): check('pinned source '+path, sha(ORIG/path)==expected)
    p_tree = ast.parse((ORIG/'modeling/pipeline.py').read_text())
    u_tree = ast.parse((ORIG/'utils/util.py').read_text())
    source_class = next(n for n in p_tree.body if isinstance(n,ast.ClassDef) and n.name=='VMemPipeline')
    names = ['estimate_normal_from_pointmap','pointmap_to_surfels','merge_surfels',
             'render_surfels_to_image','get_frame_distribution','process_retrieved_spatial_information']
    body = [deepcopy(n) for n in source_class.body if isinstance(n,ast.FunctionDef) and n.name in names]
    check('six entire original method ASTs selected',len(body)==6)
    cls = ast.ClassDef(name='OriginalMethods',bases=[],keywords=[],body=body,decorator_list=[])
    original_classes = [deepcopy(n) for n in u_tree.body if isinstance(n,ast.ClassDef) and n.name in ('Surfel','Octree')]
    module = ast.fix_missing_locations(ast.Module(body=original_classes+[cls], type_ignores=[]))
    ns = dict(np=np,torch=torch,F=F,math=math,Union=Union)
    exec(compile(module, str(ORIG/'modeling/pipeline.py')+':isolated_AST', 'exec'),ns)
    obj = ns['OriginalMethods']()
    obj.device='cpu'; obj.config=SimpleNamespace(surfel=SimpleNamespace(conf_thresh=1),model=SimpleNamespace(context_num_frames=4))

    # Odd input size distinguishes scale_factor=0.05 from recomputed output/input ratio.
    yy,xx=torch.meshgrid(torch.arange(41),torch.arange(61),indexing='ij')
    plane=(xx+2*yy).to(torch.float32)[None,None]
    downsized=F.interpolate(plane,scale_factor=0.05,mode='bilinear')
    expected=np.array([[28.5,48.5,68.5],[68.5,88.5,108.5]],dtype=np.float32)
    check('odd-size bilinear keeps 20x inverse scale',np.array_equal(downsized.numpy()[0,0],expected))
    check('bilinear resized shape 41x61 to 2x3',tuple(downsized.shape)==(1,1,2,3))

    pointmap=torch.tensor([[[0,0,2],[1,0,2],[2,0,2]],[[0,1,2],[1,1,2],[2,1,2]]],dtype=torch.float32)
    normals=obj.estimate_normal_from_pointmap(pointmap)
    check('right-cross-down gives positive z on interior',torch.equal(normals[0,:2],torch.tensor([[0,0,1],[0,0,1]],dtype=torch.float32)))
    check('last row and last col keep zero normals',bool((normals[1]==0).all() and (normals[:,-1]==0).all()))
    depths=torch.tensor([[1,2,3],[4,5,6]],dtype=torch.float32)
    conf=torch.tensor([[.99,1,2],[2,2,2]],dtype=torch.float32)
    focal=torch.tensor([10.],dtype=torch.float32)
    surfels=obj.pointmap_to_surfels(pointmap,focal,depths,conf,torch.eye(4),radius_scale=.5)
    # Quantile removes max depth and confidence rejects first cell; row-major kept IDs 1,2,3,4.
    check('quantile .999 and inclusive conf 1 exact candidates',len(surfels)==4 and np.array_equal(np.array([s.position for s in surfels]),pointmap.reshape(-1,3)[[1,2,3,4]].numpy()))
    check('original does not insert colors',all(s.color is None for s in surfels))
    check('zero normal retained with denominator .2',abs(float(surfels[1].radius)-.75)<1e-7)
    check('scalar focal shape one is preserved',tuple(focal.shape)==(1,))
    q=float(torch.quantile(depths,.999)); report['observations']['quantile_float32']=q
    check('float32 .999 quantile value near 5.995',abs(q-5.995)<1e-6)

    # Two anchors are below the default leaf cap; original match chooses first leaf ID, not nearest.
    Surfel=ns['Surfel']
    old=[Surfel(np.array([0.,0.,2.]),np.array([0.,0.,1.]),.1),Surfel(np.array([.002,0.,2.]),np.array([0.,0.,1.]),.1)]
    new=[Surfel(np.array([.0018,0.,2.]),np.array([0.,0.,1.]),.1)]
    before=np.stack([s.position.copy() for s in old]); mapping={0:[0],1:[0]}
    kept,mapping=obj.merge_surfels(new,1,old,mapping,normal_threshold=.6)
    check('original first matching ID not nearest ID',len(kept)==0 and mapping=={0:[0,1],1:[0]})
    check('original merge preserves all old geometry',np.array_equal(before,np.stack([s.position for s in old])))

    # NumPy1.26 scalar promotion differs from the prior NumPy2.3 reference environment.
    x=1.0000000894069672
    report['observations']['strict_z_scalar'] = dict(x=x,buffer=float(np.float32(x)),
        pythonfloat_lt_numpyfloat32=bool(x<np.float32(x)),
        pythonfloat_lt_numpyarray=bool((x<np.array([x],dtype=np.float32))[0]))
    check('numpy1.26 Python float vs np.float32 scalar comparison true',x<np.float32(x))
    dup=[Surfel(np.array([0.,0.,x]),np.array([0.,0.,1.]),.2) for _ in range(2)]
    rendered=obj.render_surfels_to_image(dup,np.eye(4),[10.,10.],[3.,3.],7,7)
    report['observations']['duplicate_disc_center_id']=int(rendered['surfel_index_map'][3,3])
    check('original1.26 repeated equal raw depth overwrites rounded-up float32 center',int(rendered['surfel_index_map'][3,3])==1)

    obj.surfel_to_timestep={0:[0],1:[1]}
    inp=dict(surfel_index_map=np.array([[0,0,1]],dtype=np.int32),cos_value_map=np.ones((1,3),dtype=np.float32),depth=np.ones((1,3),dtype=np.float32))
    weights,counts=obj.process_retrieved_spatial_information(inp)
    report['observations']['weights']=weights; report['observations']['candidate_counts']=counts
    check('first contribution double counted 3/5 and 2/5',np.allclose([w for _,w in weights],[.6,.4],atol=0,rtol=0))
    check('two sources each one candidate regardless unequal weights',counts==[(0,1),(1,1)])
    for path,expected in sources.items(): check('original unchanged '+path,sha(ORIG/path)==expected)
    report['status']='PASS_ARTIFICIAL_ORIGINAL_ONLY'
except Exception as exc:
    report['status']='FAIL';report['error']=repr(exc);report['traceback']=traceback.format_exc()
finally:
    report['completed_utc']=utc()
    (OUT/'original_probe_receipt.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(dict(status=report['status'],checks=len(report['checks']),observations=report['observations'])))
if report['status']=='FAIL': raise SystemExit(1)
