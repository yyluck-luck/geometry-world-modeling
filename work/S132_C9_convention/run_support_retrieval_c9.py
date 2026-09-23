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
SCENES={'scene_13':('scene_13',462),'scene_14':('scene_14',659)}   # staged: bank color+pose, target pose only
WINDOWS=[50,100,150,200,250,300,350]; TARGET_OFF=[60,75,90,105]; BANK_OFF=list(range(0,60,5))
def rgb(seq,fid):
 from PIL import Image
 a=np.asarray(Image.open(seq/f'frame-{fid:06d}.color.png').convert('RGB')); t=torch.from_numpy(a.transpose(2,0,1).copy()).float()/255.; t=torch.nn.functional.interpolate(t.unsqueeze(0),(576,768),mode='area')[:,:,:,96:672]; return (t*2-1)[0]
CONVENTION=os.environ.get('POSE_CONVENTION','native')   # C9: 'gl' negates y and z columns (OpenCV -> OpenGL)
def pose(seq,fid):
 p=np.loadtxt(io.StringIO((seq/f'frame-{fid:06d}.pose.txt').read_text()),dtype=np.float32).reshape(4,4)
 if CONVENTION=='gl': p=p.copy(); p[:,[1,2]]*=-1
 return p
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
   # Provenance needed by the CPU evaluator for J (maps are identical across arms).
   wroot=OUT/f'{scene}_w{start:04d}'; wroot.mkdir(parents=True,exist_ok=True)
   s2t=pipe.surfel_to_timestep
   s2t_keys=np.array(sorted(int(k) for k in s2t.keys()),dtype=np.int64)
   s2t_vals=[list(s2t[k] if k in s2t else s2t[str(k)]) for k in s2t_keys.tolist()]
   s2t_len=np.array([len(v) for v in s2t_vals],dtype=np.int64); s2t_flat=np.array([int(x) for v in s2t_vals for x in v],dtype=np.int64)
   np.savez_compressed(wroot/'surfel_to_timestep.npz',keys=s2t_keys,lengths=s2t_len,flat=s2t_flat)
   target_K=float(np.mean(pipe.surfel_Ks)) if np.ndim(pipe.surfel_Ks[0])==0 else np.mean(pipe.surfel_Ks,axis=0)
   avg_idx=len(targets)-max(1,len(targets)//4)   # VMem averages target_c2ws[-k//4:], k=4 -> last target
   renders=[]
   for ti,tgt in enumerate(targets):
    tc=np.asarray(q[ti:ti+1].detach().cpu())[0]; transformed=pipe.get_transformed_c2ws(tc)
    info=pipe.render_surfels_to_image(pipe.surfels,transformed,[target_K*0.65]*2,principal_points=(int(cfg.surfel.width/2),int(cfg.surfel.height/2)),image_width=int(cfg.surfel.width),image_height=int(cfg.surfel.height))
    out=wroot/f't{tgt:06d}'; out.mkdir(parents=True,exist_ok=True)
    rec={'target_frame':tgt,'is_vmem_averaged_render':ti==avg_idx,'render_c2w_dataset':tc.tolist(),'render_c2w_transformed':np.asarray(transformed).tolist()}
    save_map(rec,info,out); rec['frame_count']=pipe.process_retrieved_spatial_information(info)[1]; renders.append(rec)
   wrec=dict(recbase,status='OK',raw_contexts=raw_contexts,consumer_contexts=contexts,
             vmem_bank_timestep_to_frame=bank,surfel_Ks=np.asarray(pipe.surfel_Ks).tolist(),
             retrieval_focal=(np.asarray(target_K)*0.65).tolist(),retrieval_size=[int(cfg.surfel.width),int(cfg.surfel.height)],
             averaged_render_target=targets[avg_idx],n_surfels=int(len(pipe.surfels)),renders=renders)
   (wroot/'WINDOW_RECEIPT.json').write_text(json.dumps(wrec,indent=2,default=str)+'\n'); records.append(wrec)
  except Exception as exc:
   records.append(dict(recbase,status='BLOCKED',error=f'{type(exc).__name__}: {exc}'))
blocked=sum(1 for r in records if r.get('status') == 'BLOCKED')
status='MAPS_COMPLETE_NO_DIFFUSION' if records and not blocked else ('PARTIAL_NO_DIFFUSION' if records else 'BLOCKED')
(Path(OUT/'C8_SUPPORT_RETRIEVAL_RECEIPT.json')).write_text(json.dumps({'schema':'c9-support-retrieval-'+CONVENTION,'status':status,'recorded_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'hostname':socket.gethostname(),'slurm_job_id':os.environ.get('SLURM_JOB_ID'),'records':records,'blocked_records':blocked,'new_method_validated':False,'novelty_authorization':'NONE'},indent=2,default=str)+'\n')
print(json.dumps({'records':len(records),'blocked_records':blocked,'status':status,'new_method_validated':False,'novelty_authorization':'NONE'},indent=2))
