#!/usr/bin/env python3
"""GPU-minimal C8 support audit producer.

This follows nms_s111.py's exact five-frame priming and two-stage surfel construction,
then calls only render_surfels_to_image/process_retrieved_spatial_information. It never
runs diffusion and never binds target RGB/depth into the model process.
"""
import datetime as dt, io, json, os, socket, sys, time
from pathlib import Path
import numpy as np
RUN=Path(os.environ.get('RUN_ROOT','/home/yliutz/gwm_source_transport_20260915')); DATA=Path(os.environ['DATA_ROOT']); OUT=Path(os.environ['ARM_OUT']); SOURCE=RUN/'vmem'; WEIGHTS=Path('/home/yliutz/gwm_weights_20260915')
sys.path[:0]=[str(SOURCE),str(SOURCE/'extern/CUT3R'),str(SOURCE/'extern/CUT3R/src')]; os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1')
import torch
# Keep checkpoint loading identical to the verified S111 runner under
# PyTorch 2.6+, whose safe default can reject the pinned checkpoints.
_torch_load = torch.load
def _verified_torch_load(path, *args, **kwargs):
 if str(path) in {str(WEIGHTS/'vmem_weights.pth'), str(WEIGHTS/'cut3r_512_dpt_4_64.pth')}: kwargs['weights_only'] = False
 return _torch_load(path, *args, **kwargs)
torch.load = _verified_torch_load
from omegaconf import OmegaConf
import huggingface_hub
from diffusers.models import AutoencoderKL
import open_clip
huggingface_hub.hf_hub_download=lambda repo_id,filename,*a,**k:str(WEIGHTS/filename)
import modeling.pipeline as PM
PM.hf_hub_download=huggingface_hub.hf_hub_download
_ov=AutoencoderKL.from_pretrained; AutoencoderKL.from_pretrained=lambda repo,*a,**k:_ov(str(WEIGHTS),local_files_only=True,force_download=False,low_cpu_mem_usage=False,use_safetensors=True)
_oc=open_clip.create_model_and_transforms; open_clip.create_model_and_transforms=lambda name,*a,**k:_oc(name,pretrained=str(WEIGHTS/'open_clip_model.safetensors'))
from modeling.pipeline import VMemPipeline,encode_vae_image,encode_image,tensor_to_pil
cfg=OmegaConf.load(str(SOURCE/'configs/inference/inference.yaml')); device='cuda'; dtype=torch.float32; torch.set_num_threads(8); torch.set_num_interop_threads(1)
pipe=VMemPipeline(cfg,torch.device(device)); OUT.mkdir(parents=True,exist_ok=True)
SCENES={'scene_13':('heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13',462),'scene_14':('heldout_3dmatch_scene14/extracted/rgbd-scenes-v2-scene_14',659)}
WINDOWS=[50,100,150,200,250,300,350]; TARGET_OFF=[60,75,90,105]; BANK_OFF=list(range(0,60,5))
def rgb(seq,fid):
 from PIL import Image
 a=np.asarray(Image.open(seq/f'frame-{fid:06d}.color.png').convert('RGB')); t=torch.from_numpy(a.transpose(2,0,1).copy()).float()/255.; t=torch.nn.functional.interpolate(t.unsqueeze(0),(576,768),mode='area')[:,:,:,96:672]; return (t*2-1)[0]
def pose(seq,fid): return np.loadtxt(io.StringIO((seq/f'frame-{fid:06d}.pose.txt').read_text()),dtype=np.float32).reshape(4,4)
def reset():
 pipe.reset()
 for n in ('latents','encoder_embeddings','c2ws','Ks','pil_frames','surfels','surfel_Ks','surfel_depths','rgb_vae_latents','rgb_encoder_embeddings','poses','focal_lengths','all_pil_frames'):
  if hasattr(pipe,n): setattr(pipe,n,[])
 if hasattr(pipe,'surfel_to_timestep'): pipe.surfel_to_timestep={}
 if hasattr(pipe,'initial_threshold'): delattr(pipe,'initial_threshold')
def save_map(rec,info,root):
 arrays={k:np.asarray(v) for k,v in info.items() if k in ('surfel_index_map','cos_value_map','depth','frame_id_map')}
 rec['rgb_map_rejected']=('rgb' in info)
 f=root/'retrieval_maps.npz'; np.savez_compressed(f,**arrays); rec['retrieval_maps']=str(f); rec['map_keys']=sorted(arrays); rec['map_shapes']={k:list(v.shape) for k,v in arrays.items()}
records=[]
for scene,(rel,nframes) in SCENES.items():
 root=DATA/rel; seq=root/'seq-01'; K0=np.loadtxt(io.StringIO((root/'camera-intrinsics.txt').read_text()),dtype=np.float32).reshape(3,3)
 for start in WINDOWS:
  if start+max(TARGET_OFF)>=nframes: continue
  reset(); bank=[start+x for x in BANK_OFF]; targets=[start+x for x in TARGET_OFF]; recbase={'scene':scene,'window_start':start,'bank_frame_ids':bank,'target_frame_ids':targets}
  try:
   pipe.initialize(rgb(seq,bank[0]).unsqueeze(0).to(device,pipe.dtype),pose(seq,bank[0]),K0)
   def append(fid):
    im=rgb(seq,fid).unsqueeze(0).to(device,pipe.dtype)
    with torch.inference_mode():
     pipe.latents.append(encode_vae_image(im,pipe.vae,pipe.device,pipe.dtype).detach().cpu().numpy()[0]); pipe.encoder_embeddings.append(encode_image(im,pipe.image_encoder,pipe.device,pipe.dtype).detach().cpu().numpy()[0])
    pipe.c2ws.append(pose(seq,fid)); pipe.Ks.append(K0); pipe.pil_frames.append(tensor_to_pil(im))
   for fid in bank[1:5]: append(fid)
   pipe.construct_and_store_scene(pipe.pil_frames,list(range(len(pipe.pil_frames))),niter=cfg.surfel.niter,lr=cfg.surfel.lr,device=device)
   pipe.get_context_info(torch.tensor(np.stack([pose(seq,bank[4])]),device=device,dtype=torch.float32))
   for fid in bank[5:]: append(fid)
   pipe.construct_and_store_scene(pipe.pil_frames,list(range(len(pipe.pil_frames))),niter=cfg.surfel.niter,lr=cfg.surfel.lr,device=device)
   q=torch.tensor(np.stack([pose(seq,f) for f in targets]),device=device,dtype=torch.float32)
   # Clean NMS reads the naturally primed threshold. NMS-off then overwrites
   # initial_threshold=1e8; the following NMS-on call reproduces the sealed
   # leaked arm. The maps are the same surfel render, while C differs by arm.
   clean_ctx=pipe.get_context_info(q,use_non_maximum_suppression=True)
   off_ctx=pipe.get_context_info(q,use_non_maximum_suppression=False)
   leaked_ctx=pipe.get_context_info(q,use_non_maximum_suppression=True)
   raw_contexts={
    'memory_nms_on_clean':[bank[int(x)] for x in clean_ctx['context_time_indices'].detach().cpu().numpy().ravel()],
    'memory_nms_off':[bank[int(x)] for x in off_ctx['context_time_indices'].detach().cpu().numpy().ravel()],
    'memory_nms_on_leaked':[bank[int(x)] for x in leaked_ctx['context_time_indices'].detach().cpu().numpy().ravel()],
    'static':[start+x for x in [0,15,30,45]],
   }
   # Reproduce sealed S111's consumer contract exactly: if retrieval returns
   # fewer than four ids, the downstream input repeats them before truncating.
   contexts={arm: ((ids*4)[:4] if arm.startswith('memory_') else ids)
             for arm,ids in raw_contexts.items()}
   for arm,ctx_ids in contexts.items():
    for ti,tgt in enumerate(targets):
     avg=np.asarray(q[ti:ti+1].detach().cpu()); transformed=pipe.get_transformed_c2ws(avg[0]); target_K=np.mean(pipe.surfel_Ks,axis=0)
     info=pipe.render_surfels_to_image(pipe.surfels,transformed,[target_K*0.65]*2,principal_points=(int(cfg.surfel.width/2),int(cfg.surfel.height/2)),image_width=int(cfg.surfel.width),image_height=int(cfg.surfel.height))
     out=OUT/f'{scene}_w{start:04d}_{arm}_t{tgt:06d}'; out.mkdir(parents=True,exist_ok=True)
     rec=dict(recbase,arm=arm,target_frame=tgt,
              raw_context_frame_ids=raw_contexts[arm],
              consumer_context_frame_ids=ctx_ids,
              context_frame_ids=ctx_ids,
              map_source_arm='memory_nms_on_clean',
              retrieval_pose_source='per_target_query_pose',
              retrieval_target_K_scale=0.65)
     save_map(rec,info,out); rec['frame_count']=pipe.process_retrieved_spatial_information(info)[1]; (out/'RECEIPT.json').write_text(json.dumps(rec,indent=2,default=str)+'\n'); records.append(rec)
  except Exception as exc:
   records.append(dict(recbase,status='BLOCKED',error=f'{type(exc).__name__}: {exc}'))
blocked=sum(1 for r in records if r.get('status') == 'BLOCKED')
status='MAPS_COMPLETE_NO_DIFFUSION' if records and not blocked else ('PARTIAL_NO_DIFFUSION' if records else 'BLOCKED')
(Path(OUT/'C8_SUPPORT_RETRIEVAL_RECEIPT.json')).write_text(json.dumps({'schema':'c8-support-retrieval-v1','status':status,'recorded_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'hostname':socket.gethostname(),'slurm_job_id':os.environ.get('SLURM_JOB_ID'),'records':records,'blocked_records':blocked,'new_method_validated':False,'novelty_authorization':'NONE'},indent=2,default=str)+'\n')
print(json.dumps({'records':len(records),'blocked_records':blocked,'status':status,'new_method_validated':False,'novelty_authorization':'NONE'},indent=2))
