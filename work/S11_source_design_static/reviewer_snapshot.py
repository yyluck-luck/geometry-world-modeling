"""Static S11 source-only design inventory; does not import or execute kernels."""
import ast, hashlib, json, symtable
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

P=Path(__file__).resolve().parents[1]
OUT=P/'work/S11_source_design_static'
OUT.mkdir(exist_ok=False)
start=datetime.now(timezone.utc).isoformat()
checks=0
def req(ok, msg):
    global checks
    if not ok: raise AssertionError(msg)
    checks+=1
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def j(path): return json.loads(path.read_text())
sources=['src/vmem_retrieval_kernel.py','src/vmem_memory_kernel.py',
         'src/s10_vectorized_renderer.py','src/s6_memory_bridge.py',
         'src/retrieval_diagnostic.py','src/rgbd_retrieval.py',
         'src/s7_event_replay.py','scripts/profile_s9_components.py']
tree=ast.parse((P/sources[0]).read_text())
cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='RetrievalKernel')
renderer=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='render_surfels_to_image')
process=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='process_retrieved_spatial_information')
attrs=sorted({ast.unparse(x) for x in ast.walk(renderer) if isinstance(x,ast.Attribute)})
self_names=[x.lineno for x in ast.walk(renderer) if isinstance(x,ast.Name) and x.id=='self' and isinstance(x.ctx,ast.Load)]
source_sites=[dict(line=x.lineno,expression=ast.unparse(x)) for x in ast.walk(cls) if isinstance(x,ast.Attribute) and x.attr=='surfel_to_timestep']
req(not self_names,'renderer may not read self')
req(source_sites==[dict(line=229,expression='self.surfel_to_timestep')],'source lookup location changed')
surfel_attrs=[x for x in attrs if x.startswith(('s.','surfel.'))]
req(surfel_attrs==['s.position','surfel.normal','surfel.position','surfel.radius'],'surfel read set changed')
symbols=symtable.symtable(ast.unparse(renderer),'static-renderer','exec').get_children()[0]
parameter_reads=sorted(x.get_name() for x in symbols.get_symbols() if x.is_parameter() and x.is_referenced())
req(parameter_reads==['disk_resolution','focal_lengths','image_height','image_width','poses','principal_points','surfels'],'formal parameter read set')
global_names=sorted(x.get_name() for x in symbols.get_symbols() if x.is_global())
all_inputs={}
inventory=[]
for stage,run in [('S7','results/S7_event_replay'),('S8','results/S8_event_replay_v2')]:
    meta_path=P/run/'run_metadata.json';meta=j(meta_path)
    all_inputs[str(meta_path.relative_to(P))]=sha(meta_path)
    req(meta['status']=='completed','old stage complete')
    for block in range(3):
        folder=P/run/f'block{block}_stride8'
        entries=[c for c in meta['cases'] if c['block']==block and c['stride']==8]
        req(len(entries)==1,'case identity')
        entry=entries[0]
        for name in ('A0P0_sources.json','A0P0.npz','predicted_poses.npz','query20_A0P0_render.npz','prediction_only_selection.json'):
            path=folder/name;digest=sha(path)
            req(digest==entry['sealed_files'][name],'old sealed file '+str(path))
            all_inputs[str(path.relative_to(P))]=digest
        raw=j(folder/'A0P0_sources.json')
        mapping={int(k):v for k,v in raw.items()}
        req(set(mapping)==set(range(len(mapping))),'contiguous surfel key domain')
        for ids in mapping.values():
            req(bool(ids) and all(type(t)is int and 0<=t<20 for t in ids) and len(ids)==len(set(ids)), 'nonempty unique valid source IDs')
        lens=Counter(map(len,mapping.values()))
        append=sum(n for length,n in lens.items() if length<20)
        remove=sum(n for length,n in lens.items() if length>1)
        req(append>0 and remove>0,'all three predetermined variants nonvacuous by metadata')
        inventory.append(dict(stage=stage,block=block,query=20,stride=8,map='A0P0',source_rows=len(mapping),source_length_histogram=dict(sorted(lens.items())),append_changed_rows=append,remove_changed_rows=remove,reverse_changed_rows=remove,buffer_visibility_examined=False,edited_mapping_constructed=False))
receipt=dict(status='PASS_STATIC_ONLY',started_utc=start,completed_utc=datetime.now(timezone.utc).isoformat(),checks_passed=checks,renderer_method_lines=[renderer.lineno,renderer.end_lineno],renderer_ast_sha256=hashlib.sha256(ast.dump(renderer,include_attributes=False).encode()).hexdigest(),renderer_parameter_reads=parameter_reads,renderer_self_load_lines=self_names,renderer_surfel_attribute_reads=surfel_attrs,renderer_all_attribute_expressions=attrs,renderer_python_global_names=global_names,source_mapping_read_sites_in_RetrievalKernel=source_sites,source_sha256={f:sha(P/f) for f in sources},sealed_input_sha256=all_inputs,source_inventory=inventory,scope='AST and already-sealed source JSON metadata plus file hashes only. NPZ bytes hashed without decoding arrays. No renderer, reference selector, candidate, vote, NMS, model, timing or S11 result read.',fixture_count_adopted=18,extra_low_source_branches_adopted=False)
(OUT/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
(OUT/'reviewer_snapshot.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({k:receipt[k] for k in ['status','started_utc','completed_utc','checks_passed','fixture_count_adopted']},indent=2))
