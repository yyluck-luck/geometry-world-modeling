#!/usr/bin/env python3
"""Independent small synthetic renderer edge checks; no real data or timing.

Candidate API: module.renderer_function() returns a bindable renderer function.
Baseline source remains untouched. Output directories must be new.
"""
import argparse
import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib
import inspect
import json
import math
from pathlib import Path
import platform
import sys
from types import SimpleNamespace
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import torch
from src.vmem_retrieval_kernel import RetrievalKernel

FIELDS = ('depth', 'surfel_index_map', 'cos_value_map')
SOURCE = ROOT / 'src/vmem_retrieval_kernel.py'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def surfel(position, normal=(0, 0, 1), radius=.65, dtype='float64'):
    return {'position': list(position), 'normal': list(normal), 'radius': radius,
            'dtype': dtype}


def fixture(name, surfels, **kwargs):
    return {'name': name, 'surfels': surfels, 'width': 9, 'height': 9,
            'focal': [4., 4.], 'principal': [4., 4.], 'pose': np.eye(4).tolist(),
            'disk_resolution': 16, 'tensor_camera': False, **kwargs}


def fixtures():
    """Inputs declared without inspecting candidate implementation or real maps."""
    z0 = 1. + 3. * 2.**-25  # rounds upward to the next float32 above one
    same_bin = 1. + 7. * 2.**-26
    below_bin = 1. + 1. * 2.**-25
    f = [
        fixture('single_front', [surfel((0, 0, 2))], expected_center_id=0),
        fixture('equal_depth_first_wins', [surfel((0, 0, 2)), surfel((0, 0, 2))], expected_center_id=0),
        fixture('round_up_identical_no_reoverwrite_np2', [surfel((0, 0, z0)), surfel((0, 0, z0))], expected_center_id=0),
        fixture('nearer_same_float32_bin_not_replace_np2', [surfel((0, 0, same_bin)), surfel((0, 0, z0))], expected_center_id=0),
        fixture('nearer_cross_float32_bin_replace', [surfel((0, 0, z0)), surfel((0, 0, below_bin))], expected_center_id=1),
        fixture('three_overlapping_depth_bins', [surfel((0, 0, z0)), surfel((0, 0, z0)), surfel((0, 0, below_bin))], expected_center_id=2),
        fixture('equal_depth_different_normal', [surfel((0, 0, 2)), surfel((0, 0, 2), (.2, 0, 1))]),
        fixture('front_far_then_near', [surfel((0, 0, 3)), surfel((0, 0, 2))], expected_center_id=1),
        fixture('front_near_then_far', [surfel((0, 0, 2)), surfel((0, 0, 3))], expected_center_id=0),
        fixture('diamond_integer_boundary', [surfel((0, 0, 2), radius=1)], disk_resolution=4),
        fixture('diamond_halfpixel_shift', [surfel((.25, .25, 2), radius=1)], disk_resolution=4),
        fixture('triangle_integer_boundary', [surfel((0, 0, 2), radius=1)], disk_resolution=3),
        fixture('clipped_viewport_disk', [surfel((-1.5, 0, 2), radius=1.8)]),
        fixture('zero_radius', [surfel((0, 0, 2), radius=0)], expected_empty=True),
        fixture('tiny_radius_between_pixels', [surfel((.25, .25, 2), radius=1e-15)], expected_empty=True),
        fixture('zero_normal', [surfel((0, 0, 2), (0, 0, 0))], expected_empty=True),
        fixture('normal_below_cutoff', [surfel((0, 0, 2), (0, 0, .5e-12))], expected_empty=True),
        fixture('normal_at_cutoff', [surfel((0, 0, 2), (0, 0, 1e-12))], expected_center_id=0),
        fixture('backface', [surfel((0, 0, 2), (0, 0, -1))], expected_empty=True),
        fixture('edge_on_zero_cosine', [surfel((0, 0, 2), (1, 0, 0))]),
        fixture('center_on_near_plane', [surfel((0, 0, .1), radius=.05)], expected_empty=True),
        fixture('center_above_near_plane', [surfel((0, 0, float(np.nextafter(.1, 1.))), radius=.05)], expected_center_id=0),
        fixture('center_below_near_plane', [surfel((0, 0, float(np.nextafter(.1, 0.))), radius=.05)], expected_empty=True),
        fixture('center_on_far_plane', [surfel((0, 0, 1000), radius=500)], expected_empty=True),
        fixture('center_below_far_plane', [surfel((0, 0, float(np.nextafter(1000., 0.))), radius=500)], expected_center_id=0),
        fixture('center_behind_camera', [surfel((0, 0, -2))], expected_empty=True),
        fixture('left_frustum_margin_inclusive', [surfel((-27, 0, 2), radius=30)]),
        fixture('left_frustum_margin_outside', [surfel((-27-1e-9, 0, 2), radius=30)], expected_empty=True),
        fixture('right_frustum_margin_exclusive', [surfel((27.5, 0, 2), radius=30)], expected_empty=True),
        fixture('right_frustum_margin_inside', [surfel((27.5-1e-9, 0, 2), radius=30)]),
        fixture('mixed_positive_negative_vertices', [surfel((0, 0, .2), (math.sqrt(.75), 0, .5), radius=.6)]),
        fixture('vertex_at_zero_depth', [surfel((0, 0, .25), (1, 0, 1), radius=.25*math.sqrt(2))], disk_resolution=4),
        fixture('fewer_than_three_disk_vertices', [surfel((0, 0, 2))], disk_resolution=2, expected_empty=True),
        fixture('float32_geometry', [surfel((0, 0, z0), dtype='float32'), surfel((.1, .1, 1.2), (.2, .1, 1), dtype='float32')]),
        fixture('tensor_camera_arguments', [surfel((0, 0, 2))], tensor_camera=True),
        fixture('non_square_anisotropic', [surfel((.2, -.3, 2), (.2, .3, 1), radius=1.7)], width=13, height=7, focal=[3.25, 7.5], principal=[5.5, 2.25]),
    ]
    # Fixed small mixed fixtures, separate from hand-selected exact boundary cases.
    rng = np.random.default_rng(20260906)
    for j in range(24):
        ss=[]
        for _ in range(5):
            ss.append(surfel(rng.uniform([-2,-2,.08],[2,2,4]), rng.normal(size=3), float(rng.uniform(.01,1.4))))
        f.append(fixture(f'seeded_small_mix_{j:02}', ss, width=11, height=7,
                         principal=[5.25,3.], focal=[4.,5.], disk_resolution=[3,4,16][j%3]))
    return f


def run_renderer(func, spec):
    objects=[SimpleNamespace(position=np.array(s['position'], dtype=s['dtype']),
             normal=np.array(s['normal'], dtype=s['dtype']), radius=s['radius']) for s in spec['surfels']]
    pose=np.array(spec['pose'],dtype=np.float64)
    focal=np.array(spec['focal'],dtype=np.float64)
    principal=np.array(spec['principal'],dtype=np.float64)
    if spec['tensor_camera']:
        pose=torch.from_numpy(pose); focal=torch.from_numpy(focal); principal=torch.from_numpy(principal)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        result=func(None, objects, pose, focal, principal, spec['width'], spec['height'], spec['disk_resolution'])
    return result,[{'category':w.category.__name__,'message':str(w.message)} for w in caught]


def arrays_identical(a,b):
    return all(a[k].dtype==b[k].dtype and a[k].shape==b[k].shape and
               a[k].tobytes()==b[k].tobytes() for k in FIELDS)


def promotion_probe():
    x=1.+3.*2.**-25; b=np.float32(x); a=np.array([b],dtype=np.float32)
    return {'numpy':np.__version__,'python_float':x,'float32_stored_as_python':float(b),
      'stored_rounds_up':bool(float(b)>x),
      'python_float_lt_numpy_float32_scalar':bool(x<b),
      'python_float_lt_float32_array':bool((x<a)[0]),
      'numpy_float64_lt_numpy_float32_scalar':bool(np.float64(x)<b),
      'numpy_float64_lt_float32_array':bool((np.float64(x)<a)[0]),
      'python_float_lt_float64_array':bool((x<a.astype(np.float64))[0]),
      'python_float_plus_numpy_float32_dtype':str(np.asarray(x+b).dtype),
      'numpy_float64_plus_numpy_float32_dtype':str(np.asarray(np.float64(x)+b).dtype)}


def original_ast():
    tree=ast.parse(SOURCE.read_text())
    return next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='render_surfels_to_image')


def polygon_probe():
    fn=next(n for n in ast.walk(original_ast()) if isinstance(n,ast.FunctionDef) and n.name=='point_in_polygon_2d')
    ns={};exec(compile(ast.Module(body=[deepcopy(fn)],type_ignores=[]),str(SOURCE),'exec'),ns)
    poly=ns['point_in_polygon_2d']
    # Integer tests include exact boundaries; epsilon-specific query is continuous.
    cases=[('square',[[1,1],[5,1],[5,5],[1,5]],[(1,1),(5,1),(1,5),(3,3)]),
      ('square_reversed',[[1,5],[5,5],[5,1],[1,1]],[(1,1),(5,1),(1,5),(3,3)]),
      ('collinear',[[1,1],[3,3],[5,5]],[(1,1),(2,2),(2,3)]),
      ('duplicate_vertex',[[1,1],[5,1],[5,1],[5,5],[1,5]],[(1,1),(5,1),(3,3)]),
      ('epsilon_scale',[[0,0],[1,1e-15],[2,0]],[(1.,5e-16),(.5,5e-16),(1.5,5e-16)]),
      ('epsilon_zero_denominator',[[0,0],[1,-1e-15],[2,0]],[(1.,-5e-16)])]
    out=[]
    for name,coords,points in cases:
        with np.errstate(all='ignore'):
            outcomes=[bool(poly(x,y,np.asarray(coords,dtype=np.float64))) for x,y in points]
        out.append({'name':name,'polygon':coords,'points':points,'inside':outcomes})
    return out


def mutant(kind):
    """Known-wrong negative controls exist only in memory, never in source files."""
    node=deepcopy(original_ast())
    class Change(ast.NodeTransformer):
        def visit_Constant(self,n):
            if kind=='zero_polygon_epsilon' and isinstance(n.value,float) and n.value==1e-15:
                n.value=0.
            return n
        def visit_Compare(self,n):
            self.generic_visit(n)
            if isinstance(n.left,ast.Name) and n.left.id=='avg_depth':
                if kind=='force_float64_depth':
                    n.left=ast.Call(func=ast.Attribute(value=ast.Name(id='np',ctx=ast.Load()),attr='float64',ctx=ast.Load()),args=[n.left],keywords=[])
                elif kind=='non_strict_depth':n.ops=[ast.LtE()]
            if kind=='include_near_plane' and isinstance(n.comparators[0],ast.Name) and n.comparators[0].id=='near_z':n.ops=[ast.GtE()]
            return n
        def visit_Call(self,n):
            self.generic_visit(n)
            if kind=='half_pixel_polygon' and isinstance(n.func,ast.Name) and n.func.id=='point_in_polygon_2d':
                n.args[:2]=[ast.BinOp(left=a,op=ast.Add(),right=ast.Constant(.5)) for a in n.args[:2]]
            return n
    changed=ast.fix_missing_locations(Change().visit(node))
    ns={'np':np,'torch':torch,'math':math}
    exec(compile(ast.Module(body=[changed],type_ignores=[]),'<S10-known-wrong-negative-control>','exec'),ns)
    return ns['render_surfels_to_image']


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--candidate-module',help='e.g. src.s10_vectorized_renderer; omit to audit baseline fixtures only')
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    started=datetime.now(timezone.utc).isoformat()
    specs=fixtures()
    source_hash=sha(SOURCE); script_hash=sha(Path(__file__))
    candidate=None; candidate_source=None
    if a.candidate_module:
        module=importlib.import_module(a.candidate_module)
        candidate=module.renderer_function()
        candidate_source={'path':str(Path(module.__file__).resolve()),'sha256':sha(Path(module.__file__))}
    pre={'started_utc':started,'scope':'Synthetic small fixtures only; no real maps, PNG, GT, model or timing benchmark.',
      'source_sha256':source_hash,'script_sha256':script_hash,'candidate':candidate_source,
      'environment':{'python':sys.version,'executable':sys.executable,'numpy':np.__version__,'torch':torch.__version__,'platform':platform.platform()},
      'fixture_count':len(specs),'fixtures':specs,'equality':'shape, dtype and exact bytes for all three renderer arrays; zero tolerance',
      'limitations':['Finite edge tests do not prove all-input equivalence.','Warning text/count is recorded, not required equal; value/ID/dtype contract is tested.','No speed or research novelty is inferred.','Only pinned NumPy2.3.5 environment is supported for the expected promotion guards.']}
    (a.out/'pre_run.json').write_text(json.dumps(pre,indent=2)+'\n')
    result={**pre,'status':'running','promotion':promotion_probe(),'polygon_scalar_probes':polygon_probe(),'cases':[],'negative_controls':[]}
    try:
        assert np.__version__=='2.3.5','Use the fixed project environment; do not silently change promotion assumptions.'
        probe=result['promotion']
        assert not probe['python_float_lt_numpy_float32_scalar']
        assert not probe['python_float_lt_float32_array']
        assert probe['numpy_float64_lt_numpy_float32_scalar'] and probe['numpy_float64_lt_float32_array']
        assert probe['python_float_plus_numpy_float32_dtype']=='float32'
        originals={}
        for spec in specs:
            ref,rw=run_renderer(RetrievalKernel.render_surfels_to_image,spec)
            originals[spec['name']]=ref
            assert tuple(ref)==FIELDS
            assert ref['depth'].dtype==np.float32 and ref['cos_value_map'].dtype==np.float32
            assert ref['surfel_index_map'].dtype==np.int32
            if 'expected_center_id' in spec:assert int(ref['surfel_index_map'][4,4])==spec['expected_center_id'],spec['name']
            if spec.get('expected_empty'):assert (ref['surfel_index_map']==-1).all(),spec['name']
            np.savez_compressed(a.out/(spec['name']+'_reference.npz'),**ref)
            item={'name':spec['name'],'visible_pixels':int((ref['surfel_index_map']>=0).sum()),'reference_warnings':rw,
                  'reference_arrays':{k:{'dtype':str(ref[k].dtype),'shape':list(ref[k].shape),'sha256':hashlib.sha256(ref[k].tobytes()).hexdigest()} for k in FIELDS}}
            if candidate:
                got,cw=run_renderer(candidate,spec)
                np.savez_compressed(a.out/(spec['name']+'_candidate.npz'),**got)
                item['candidate_warnings']=cw
                item['exact_arrays_equal']=arrays_identical(ref,got)
                item['differing_elements']={k:int(np.count_nonzero(ref[k]!=got[k])) for k in FIELDS}
                result['cases'].append(item)
                assert item['exact_arrays_equal'],spec['name']+' candidate differs'
            else:result['cases'].append(item)
        controls={'force_float64_depth':'round_up_identical_no_reoverwrite_np2',
                  'non_strict_depth':'equal_depth_first_wins',
                  'half_pixel_polygon':'diamond_integer_boundary',
                  'zero_polygon_epsilon':'diamond_integer_boundary',
                  'include_near_plane':'center_on_near_plane'}
        for kind,name in controls.items():
            spec=next(s for s in specs if s['name']==name)
            bad,_=run_renderer(mutant(kind),spec)
            rejected=not arrays_identical(originals[name],bad)
            result['negative_controls'].append({'mutation':kind,'fixture':name,'detected':rejected})
            assert rejected,'fixture failed to detect known-wrong '+kind
        assert sha(SOURCE)==source_hash and sha(Path(__file__))==script_hash
        if candidate_source:assert sha(Path(candidate_source['path']))==candidate_source['sha256']
        result['status']='passed_candidate_exact_edges' if candidate else 'passed_baseline_fixture_guards'
    except Exception as e:
        result['status']='failed';result['error']=repr(e)
        raise
    finally:
        result['completed_utc']=datetime.now(timezone.utc).isoformat()
        result['source_unchanged']=sha(SOURCE)==source_hash
        (a.out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'status':result['status'],'cases_completed':len(result['cases']),'out':str(a.out),'error':result.get('error')}))


if __name__=='__main__':main()
