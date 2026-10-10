#!/usr/bin/env python3
"""S139 step A: cross-sequence revisit banks (7-Scenes chess), repaired memory (gl + KPS + coverage priming).

Header (model load, KPS/probe patches) identical to run_retrieval_s136.py; the window loop reads WINDOW_MANIFEST
(JSON: windows with bank refs "seq-XX/NNNNNN", target refs, priming chunks). Original S136 docstring follows.

S136 step A: repaired VMem memory = scale init (INIT) + priming schedule (PRIMING), maps + retrieval contexts.

Derived from work/S134_tacc_fixed_map/run_retrieval_s134.py. New env switches:
  INIT    = orig | fix (S133 adaptive PnP threshold) | kps (S135 known-pose dense scale) | kpsK (kps with known K)
  PRIMING = s111 (5 frames, then 7 at once: VMem only adds surfels for the last target_num_frames=4 frames, so bank
            offsets 25/30/35 never enter memory) | chunk4 (5 frames, then chunks of 4 and 3, VMem's intended cadence)
kps.py must sit next to this file (bound at /opt/kps.py in the container). Original S134 docstring follows.

S134 step A: surfel map + retrieval contexts with/without the S133 PnP fix (TACC gpu13).

Derived from work/S132_C9_convention/run_support_retrieval_c9.py (C8/C9 producer; nms_s111 priming,
two-stage surfel construction, render_surfels_to_image). Changes: WEIGHTS from env; PNP_FIX=1 applies
the S133 candidate fix (MST PnP mask threshold = min(3, min view median CUT3R confidence)); per-construct
probes (similarity scale s, PnP successes, confidence medians, CUT3R depth medians). Never runs diffusion;
DATA_ROOT must hold only bank color+pose and target pose.
"""
import datetime as dt, io, json, os, socket, sys, time
from pathlib import Path
import numpy as np
RUN=Path(os.environ.get('RUN_ROOT','/home/yliutz/gwm_source_transport_20260915')); DATA=Path(os.environ['DATA_ROOT']); OUT=Path(os.environ['ARM_OUT']); SOURCE=RUN/'vmem'; WEIGHTS=Path(os.environ.get('WEIGHTS','/home/yliutz/gwm_weights_20260915'))
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
from cloud_opt.dust3r_opt import init_im_poses as IIP
INIT=os.environ.get('INIT','orig'); PRIMING=os.environ.get('PRIMING','s111')
PNP_FIX=INIT=='fix'; PROBES=[]; KPS_LOG=[]
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
_om=IIP.minimum_spanning_tree; _oa=IIP.align_multiple_poses; _op=IIP.fast_pnp
def _mst(imshapes,edges,pred_i,pred_j,conf_i,conf_j,im_conf,thr,*a,**k):
 PROBES.append({'conf_median':[float(c.median()) for c in im_conf],'thr_orig':float(thr),'pnp_ok':0,'pnp_calls':0})
 if PNP_FIX: thr=min(float(thr),min(float(c.median()) for c in im_conf))
 PROBES[-1]['thr_used']=float(thr)
 return _om(imshapes,edges,pred_i,pred_j,conf_i,conf_j,im_conf,thr,*a,**k)
def _pnp(*a,**k):
 r=_op(*a,**k)
 if PROBES: PROBES[-1]['pnp_calls']+=1; PROBES[-1]['pnp_ok']+=int(bool(r))
 return r
def _align(src,tgt):
 s,R,T=_oa(src,tgt)
 if PROBES: PROBES[-1]['s']=float(s)
 return s,R,T
_ORIG_INIT=IIP.init_minimum_spanning_tree
IIP.minimum_spanning_tree=_mst; IIP.fast_pnp=_pnp; IIP.align_multiple_poses=_align
def cut3r_K(K):  # dataset 640x480 K -> VMem rgb() 576 crop -> CUT3R 512 resize + 512x384 crop
 a=1.2*512/576; return np.array([[K[0,0]*a,0,(K[0,2]*1.2-96)*512/576],[0,K[1,1]*a,K[1,2]*a-64],[0,0,1]])
cfg=OmegaConf.load(str(SOURCE/'configs/inference/inference.yaml')); device='cuda'; dtype=torch.float32; torch.set_num_threads(8); torch.set_num_interop_threads(1)
pipe=VMemPipeline(cfg,torch.device(device)); OUT.mkdir(parents=True,exist_ok=True)

MANIFEST=json.loads(Path(os.environ['WINDOW_MANIFEST']).read_text())
SCENE_ROOT=DATA/MANIFEST['scene_dir']
K0=np.loadtxt(io.StringIO((SCENE_ROOT/'camera-intrinsics.txt').read_text()),dtype=np.float32).reshape(3,3)
CONVENTION=os.environ.get('POSE_CONVENTION','gl')
def split(ref): s,f=ref.split('/'); return SCENE_ROOT/s, int(f)
def rgb(ref):
 from PIL import Image
 d,fid=split(ref); a=np.asarray(Image.open(d/f'frame-{fid:06d}.color.png').convert('RGB')); t=torch.from_numpy(a.transpose(2,0,1).copy()).float()/255.; t=torch.nn.functional.interpolate(t.unsqueeze(0),(576,768),mode='area')[:,:,:,96:672]; return (t*2-1)[0]
def pose(ref):
 d,fid=split(ref); p=np.loadtxt(io.StringIO((d/f'frame-{fid:06d}.pose.txt').read_text()),dtype=np.float32).reshape(4,4)
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
 f=root/'retrieval_maps.npz'; np.savez_compressed(f,**arrays); rec['retrieval_maps']=str(f)
if INIT in ('kps','kpsK'):
 import kps; IIP.init_minimum_spanning_tree=_ORIG_INIT; kps.install(IIP,log=KPS_LOG,known_K=cut3r_K(K0.astype(np.float64)) if INIT=='kpsK' else None)
records=[]; T4=int(cfg.model.target_num_frames)
for w in MANIFEST['windows']:
 reset(); PROBES.clear(); KPS_LOG.clear(); bank=w['bank']; targets=w['targets']; recbase={'window_id':w['window_id'],'pair':w['pair'],'start':w['start'],'bank':bank,'targets':targets}
 try:
  t0=time.time()
  pipe.initialize(rgb(bank[0]).unsqueeze(0).to(device,pipe.dtype),pose(bank[0]),K0)
  def append(ref):
   im=rgb(ref).unsqueeze(0).to(device,pipe.dtype)
   with torch.inference_mode():
    pipe.latents.append(encode_vae_image(im,pipe.vae,pipe.device,pipe.dtype).detach().cpu().numpy()[0]); pipe.encoder_embeddings.append(encode_image(im,pipe.image_encoder,pipe.device,pipe.dtype).detach().cpu().numpy()[0])
   pipe.c2ws.append(pose(ref)); pipe.Ks.append(K0); pipe.pil_frames.append(tensor_to_pil(im))
  for ref in bank[1:5]: append(ref)
  pipe.construct_and_store_scene(pipe.pil_frames,list(range(len(pipe.pil_frames))),niter=cfg.surfel.niter,lr=cfg.surfel.lr,device=device)
  pipe.get_context_info(torch.tensor(np.stack([pose(bank[4])]),device=device,dtype=torch.float32))   # NMS threshold at the 5-frame state (VMem)
  pos=5
  for n in w['priming_chunks']:      # coverage priming: target_num_frames = chunk length so every new frame gets surfels
   for ref in bank[pos:pos+n]: append(ref)
   pos+=n; cfg.model.target_num_frames=n
   try: pipe.construct_and_store_scene(pipe.pil_frames,list(range(len(pipe.pil_frames))),niter=cfg.surfel.niter,lr=cfg.surfel.lr,device=device)
   finally: cfg.model.target_num_frames=T4
  assert pos==len(bank), (pos,len(bank))
  q=torch.tensor(np.stack([pose(t) for t in targets]),device=device,dtype=torch.float32)
  clean_ctx=pipe.get_context_info(q,use_non_maximum_suppression=True)
  ids=[int(x) for x in clean_ctx['context_time_indices'].detach().cpu().numpy().ravel()]
  raw=[bank[i] for i in ids]; consumer=(raw*4)[:4]
  wroot=OUT/w['window_id']; wroot.mkdir(parents=True,exist_ok=True)
  s2t=pipe.surfel_to_timestep
  s2t_keys=np.array(sorted(int(k) for k in s2t.keys()),dtype=np.int64)
  s2t_vals=[list(s2t[k]) for k in s2t_keys.tolist()]
  np.savez_compressed(wroot/'surfel_to_timestep.npz',keys=s2t_keys,lengths=np.array([len(v) for v in s2t_vals],dtype=np.int64),flat=np.array([int(x) for v in s2t_vals for x in v],dtype=np.int64))
  target_K=float(np.mean(pipe.surfel_Ks)) if np.ndim(pipe.surfel_Ks[0])==0 else np.mean(pipe.surfel_Ks,axis=0)
  tc=np.asarray(q[-1:].detach().cpu())[0]
  info=pipe.render_surfels_to_image(pipe.surfels,pipe.get_transformed_c2ws(tc),[target_K*0.65]*2,principal_points=(int(cfg.surfel.width/2),int(cfg.surfel.height/2)),image_width=int(cfg.surfel.width),image_height=int(cfg.surfel.height))
  rr={'target':targets[-1]}; save_map(rr,info,wroot); rr['frame_count']=pipe.process_retrieved_spatial_information(info)[1]
  wrec=dict(recbase,status='OK',raw_contexts={'memory_nms_on_clean':raw},consumer_contexts={'memory_nms_on_clean':consumer},
            n_surfels=int(len(pipe.surfels)),memory_frames=sorted({bank[int(t)] for v in s2t.values() for t in v}),
            frac_history_in_context=sum(r.startswith(w['history_seq']) for r in consumer)/4.0,
            init=INIT,convention=CONVENTION,kps_log=list(KPS_LOG),construct_probes=list(PROBES),render_last_target=rr,
            seconds=round(time.time()-t0,1))
  (wroot/'WINDOW_RECEIPT.json').write_text(json.dumps(wrec,indent=2,default=str)+'\n'); records.append(wrec)
  print(f"[s139A] {w['window_id']} ctx={consumer} hist_frac={wrec['frac_history_in_context']} surfels={wrec['n_surfels']} {wrec['seconds']}s",flush=True)
 except Exception as exc:
  import traceback
  records.append(dict(recbase,status='BLOCKED',error=f'{type(exc).__name__}: {exc}',traceback=traceback.format_exc()[-2000:]))
  print(f"[s139A] {w['window_id']} BLOCKED {exc}",flush=True)
blocked=sum(1 for r in records if r.get('status')=='BLOCKED')
(Path(OUT/'RETRIEVAL_RECEIPT.json')).write_text(json.dumps({'schema':'s139-retrieval-v1','convention':CONVENTION,'init':INIT,'status':'MAPS_COMPLETE_NO_DIFFUSION' if not blocked else 'PARTIAL','recorded_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'hostname':socket.gethostname(),'slurm_job_id':os.environ.get('SLURM_JOB_ID'),'records':records,'blocked_records':blocked,'new_method_validated':False,'novelty_authorization':'NONE'},indent=2,default=str)+'\n')
print(json.dumps({'records':len(records),'blocked':blocked}))
