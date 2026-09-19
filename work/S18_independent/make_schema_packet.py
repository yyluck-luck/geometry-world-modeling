"""Exercise new producer observer/output schema on previously invented input.
This is not a model run or a rerun of S0-S11 / S17C.
"""
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
import hashlib,importlib.util,json,sys
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=HERE/'schema_packet';OUT.mkdir(exist_ok=False)
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('s18_producer',ROOT/'scripts/run_s18_memory_bridge.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
from src import vmem_memory_kernel as memory
from src.s18_original_kernels import OriginalGeometryKernel
started=datetime.now(timezone.utc).isoformat();torch.set_num_threads(8)
with np.load(HERE/'artificial_packet/inputs.npz',allow_pickle=False) as z:data={k:z[k] for k in z.files}
c2w=data['c2ws'];focal=(data['scaled_focal']/np.float32(.05)).astype(np.float32)
raw=dict(point_clouds=data['pointcloud'],depths=data['depths'],confidences=data['confs'],focal=focal,R=c2w[:,:3,:3],t=c2w[:,:3,3],colors=np.zeros_like(data['pointcloud']),pp=np.full((2,2),192,dtype=np.float32))
np.savez_compressed(OUT/'invented_final.npz',**raw)
p.write(OUT/'invented_prior_metadata.json',dict(array_files={'final_result.npz':{k:p.tensor_id(v) for k,v in raw.items()}}))
report=dict(array_files={},counters=dict(final_array_decodes=6,resize_calls=1,store_calls=1,pointmap_calls=0,normal_calls=0,merge_calls=0,octree_root_queries=0,render_calls=0,process_calls=0),frames=[])
k=OriginalGeometryKernel();k.device='cpu';k.surfels=[];k.surfel_to_timestep={}
k.config=SimpleNamespace(surfel=SimpleNamespace(shrink_factor=.05,radius_scale=.5,conf_thresh=1,merge_normal_threshold=.6),model=SimpleNamespace(context_num_frames=4,target_num_frames=4),inference=SimpleNamespace(visualize_surfel=False))
points,depth,conf=k.resize_scene_inputs(torch.from_numpy(raw['point_clouds']),torch.from_numpy(raw['depths']),torch.from_numpy(raw['confidences']))
rf=np.tile(np.mean(focal,axis=0)*.65,(2,1))
p.save_arrays(OUT,'reduced_inputs.npz',dict(pointcloud=points,depths=depth,confs=conf,c2ws=c2w,focal=focal,scaled_focal=focal*.05,render_focal=rf,render_pp=np.array([256,144],dtype=np.int64)),report)
p.save_arrays(OUT,'bilinear_provenance.npz',p.bilinear_provenance(np),report)
obs=p.BridgeObserver(k,memory,torch,np,OUT,report,lambda x:None);obs.install()
try:
 k.store_reduced_scene(points,depth,conf,focal,c2w)
 final,sources=obs.map_snapshot('map_after_frame1');report.update(map_surfel_count=len(k.surfels),map_source_lists=sources)
 obj_to_final={id(s):i for i,s in enumerate(k.surfels)};records={x['candidate_index']:x for x in obs.merge_records};mapping=[]
 for (frame,j),s in obs.candidate_objects.items():
  fid=obj_to_final.get(id(s));fid=records[j]['final_surfel_id'] if fid is None else fid
  flat=obs.owners[id(s)][1]
  mapping.append(dict(frame=frame,candidate_index=j,reduced_flat_id=flat,reduced_row=flat//25,reduced_col=flat%25,final_surfel_id=fid,geometry_retained=id(s) in obj_to_final))
 p.write(OUT/'candidate_provenance.json',dict(candidates=mapping))
finally:obs.restore()
statuses=[p.consume_query(k,np,OUT,i,c2w[i],rf,report) for i in range(2)]
report['status']='NO_VISIBLE_SOURCE' if 'NO_VISIBLE_SOURCE' in statuses else 'SUCCESS'
p.write(OUT/'invented_metadata.json',report)
p.write(OUT/'packet_receipt.json',dict(status='ARTIFICIAL_SCHEMA_PACKET_COMPLETE',started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat(),producer_sha256=p.sha(ROOT/'scripts/run_s18_memory_bridge.py'),driver_sha256=p.sha(Path(__file__)),input='Previously invented artificial_packet/inputs.npz',real_archive_reads=0,model_calls=0,GT_reads=0,real_cli_identity_gate_tested=False))
print(json.dumps({'status':'ARTIFICIAL_SCHEMA_PACKET_COMPLETE','surfels':len(k.surfels),'queries':statuses}))
