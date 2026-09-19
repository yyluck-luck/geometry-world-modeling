#!/usr/bin/env python3
"""S103-VMemBase: fixed four-history/four-command-camera development forward.
Only staged history RGB/pose, K and command_camera are read by this process.
Future RGB-D/pose files are scorer inputs and are never opened here.
"""
from __future__ import annotations
import hashlib, io, json, os, random, sys, time
from pathlib import Path
import numpy as np

def sha_bytes(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def sha_file(p: Path) -> str: return sha_bytes(p.read_bytes())
def require(x, msg):
    if not x: raise RuntimeError(msg)

RUN=Path(os.environ.get('RUN_ROOT','/home/yliutz/gwm_source_transport_20260915'))
STAGE=Path(os.environ.get('PREDICTOR_ROOT',''))
OUT=Path(os.environ.get('PREDICTOR_OUT',''))
WEIGHTS=Path('/home/yliutz/gwm_weights_20260915')
require(STAGE.is_dir() and OUT.is_dir(), 'PREDICTOR_ROOT/PREDICTOR_OUT required')
# The isolation launcher provides this allowlist; reject environment drift.
require(os.environ.get('EXECUTION_BOUNDARY_ID','').strip(), 'missing execution boundary id')
SOURCE=RUN/'vmem'; sys.path[:0]=[str(SOURCE),str(SOURCE/'extern/CUT3R'),str(SOURCE/'extern/CUT3R/src')]
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_IMPLICIT_TOKEN='1',PYTHONDONTWRITEBYTECODE='1')
import torch
from omegaconf import OmegaConf
import huggingface_hub
from diffusers.models import AutoencoderKL
import open_clip

def local_hf(repo_id, filename, *args, **kwargs):
    table={('liguang0115/vmem','vmem_weights.pth'):WEIGHTS/'vmem_weights.pth',('liguang0115/cut3r','cut3r_512_dpt_4_64.pth'):WEIGHTS/'cut3r_512_dpt_4_64.pth'}
    p=table.get((repo_id,filename)); require(p is not None and p.exists(),f'unbound HF request {repo_id}/{filename}'); return str(p)
huggingface_hub.hf_hub_download=local_hf
orig_vae=AutoencoderKL.from_pretrained
def local_vae(repo,*args,**kwargs):
    # The formal source and checkpoint mounts are read-only.  Both required VAE
    # files already live in WEIGHTS, so no runtime directory/symlink creation is
    # permitted or needed.
    return orig_vae(str(WEIGHTS),local_files_only=True,force_download=False,low_cpu_mem_usage=False,use_safetensors=True)
AutoencoderKL.from_pretrained=local_vae
orig_clip=open_clip.create_model_and_transforms
def local_clip(name,*args,**kwargs): return orig_clip(name,pretrained=str(WEIGHTS/'open_clip_model.safetensors'))
open_clip.create_model_and_transforms=local_clip
orig_load=torch.load
def verified_load(path,*args,**kwargs):
    if str(path) in {str(WEIGHTS/'vmem_weights.pth'),str(WEIGHTS/'cut3r_512_dpt_4_64.pth')}: kwargs['weights_only']=False
    return orig_load(path,*args,**kwargs)
torch.load=verified_load
from modeling.network import VMemModel, VMemModelParams, VMemWrapper
from modeling.modules.autoencoder import AutoEncoder
from modeling.modules.conditioner import CLIPConditioner
from modeling.sampling import DDPMDiscretization, DiscreteDenoiser, create_samplers
from modeling.pipeline import VMemPipeline
from utils import load_img_and_K, encode_vae_image, encode_image, do_sample, tensor_to_pil

# Manifest is generated before launch and is the only identity source.
manifest=json.loads((STAGE/'predictor_inputs.json').read_text())
require(manifest.get('roles')==['history_rgb','history_pose','command_camera','camera_intrinsics'],'unexpected predictor roles')
records=manifest['records']; require(len(records)==13,'expected 4 history RGB + 4 history pose + 4 camera commands + K')
reads=[]
def read(ref, role):
    p=Path(ref['path']); require(p.is_relative_to(STAGE),f'{role} escapes stage'); b=p.read_bytes(); actual=sha_bytes(b)
    require(actual==ref['sha256'] and len(b)==ref['bytes'],f'{role} identity mismatch {p}')
    reads.append({'role':role,'path':str(p),'bytes':len(b),'sha256':actual}); return b
# Load only declared staged files. No dataset archive or outcome root is reachable here.
by_role={}
for row in records: by_role.setdefault(row['role'],[]).append(row)
require(len(by_role.get('history_rgb',[]))==4 and len(by_role.get('history_pose',[]))==4
        and len(by_role.get('command_camera',[]))==4 and len(by_role.get('camera_intrinsics',[]))==1,
        'predictor role counts differ')
ordered=[]
for rgb,pose in zip(sorted(by_role['history_rgb'],key=lambda x:int(x['frame_id'])),
                    sorted(by_role['history_pose'],key=lambda x:int(x['frame_id']))):
    require(rgb['frame_id']==pose['frame_id'],'history RGB/pose IDs differ')
    ordered.append((rgb,pose))
config=OmegaConf.load(SOURCE/'configs/inference/inference.yaml')
device='cuda'; dtype=torch.float16
# Runtime and model binding are fixed by the contract/launcher, not command-line overrides.
torch.set_num_threads(8); torch.set_num_interop_threads(1)
random.seed(42); np.random.seed(42); torch.manual_seed(42); torch.cuda.manual_seed_all(42)
model=VMemModel(VMemModelParams()).to(device,dtype); state=torch.load(WEIGHTS/'vmem_weights.pth',map_location='cpu',weights_only=False); state={k.replace('module.','') if 'module.' in k else k:v for k,v in state.items()}; info=model.load_state_dict(state,strict=True); require(not info.missing_keys and not info.unexpected_keys,'VMem state mismatch'); del state
model=VMemWrapper(model).eval()
ae=AutoEncoder(chunk_size=1).to(device,dtype).eval()
clip=CLIPConditioner().to(device,dtype).eval()
# Use original preprocessing and K transformation; source K is unnormalised 640x480.
K0=np.asarray(json.loads(read(by_role['camera_intrinsics'][0]['file'],'camera_intrinsics').decode())['K'],dtype=np.float32)
def model_grid_K(source_K):
    """Apply 640x480 -> 768x576 resize and x=[96,672) crop exactly once."""
    k=torch.tensor(source_K,dtype=torch.float32).clone()
    k[0]*=1.2; k[1]*=1.2; k[0,2]-=96.
    require(torch.allclose(k[2],torch.tensor([0.,0.,1.])), 'transformed K homogeneous row changed')
    return k
images=[]; Ks=[]; c2ws=[]; ids=[]
for rgb,pose in ordered:
    rgb_bytes=read(rgb['file'],'history_rgb'); pose_bytes=read(pose['file'],'history_pose')
    rgb_path=STAGE/'history'/f"{int(rgb['frame_id']):06d}.color.png"; pose_path=STAGE/'history'/f"{int(pose['frame_id']):06d}.pose.txt"
    # Manifest file path is authoritative; use temporary in-memory decode to avoid alternate paths.
    from PIL import Image
    img=Image.open(io.BytesIO(rgb_bytes)).convert('RGB'); arr=np.asarray(img)
    t=torch.from_numpy(arr.transpose(2,0,1).copy()).float()/255.; t=t.unsqueeze(0)
    # Explicit equivalent to source transform: resize 640x480 -> 768x576, crop x=96.
    t=torch.nn.functional.interpolate(t,(576,768),mode='area')[:,:, :,96:672]*2.-1.
    k=model_grid_K(K0)
    images.append(t[0]); Ks.append(k)
    c2ws.append(np.loadtxt(io.StringIO(pose_bytes.decode()),dtype=np.float32).reshape(4,4))
    ids.append(int(rgb['frame_id']))
images=torch.stack(images).to(device,dtype); Ks=torch.stack(Ks).to(device); c2ws=torch.tensor(np.stack(c2ws),device=device,dtype=torch.float32)
# Existing VMem helper methods are called with a geometry carrier; camera arithmetic stays FP32.
carrier=object.__new__(VMemPipeline); carrier.camera_scale=2.0; carrier.device=torch.device(device); carrier.dtype=torch.float32; carrier.config=config
with torch.inference_mode():
    lat=encode_vae_image(images,ae,device,dtype)
    emb=encode_image(images,clip,device,dtype)
    scale, centered=VMemPipeline.get_translation_scaling_factor(carrier,c2ws.clone())
# Query camera commands are predeclared; they are not target RGB/depth outcomes.
query=[]
for cam in sorted(by_role['command_camera'],key=lambda x:int(x['frame_id'])):
    payload=json.loads(read(cam['file'],'command_camera').decode()); query.append(np.asarray(payload['c2w'],dtype=np.float32));
all_c2w=torch.tensor(np.concatenate([centered.detach().cpu().numpy(),np.stack(query)]),device=device,dtype=torch.float32)
query_K=model_grid_K(K0).to(device)
all_K=torch.cat([Ks,query_K.unsqueeze(0).repeat(len(query),1,1)],0)
require(torch.allclose(all_K[:,2],torch.tensor([0.,0.,1.],device=device).expand(8,-1)),
        'history/query K homogeneous rows differ')
require(torch.allclose(all_K[:,0,2],torch.full((8,),288.,device=device)),
        'history/query K principal points differ')
require(torch.allclose(all_K,query_K.unsqueeze(0).expand(8,-1,-1)),
        'history/query transformed intrinsics differ')
mask=torch.tensor([True]*4+[False]*4,device=device)
with torch.inference_mode():
    cond=VMemPipeline.get_cond(carrier,lat,all_c2w,all_K,scale,emb,mask)
    den=DiscreteDenoiser(DDPMDiscretization(),num_idx=1000,device=device)
    sampler=create_samplers(guider_types=1,discretization=DDPMDiscretization(),num_frames=8,num_steps=50,cfg_min=1.2,device=device)[0]
    outputs=do_sample(model,ae,den,sampler,cond['c'],cond['uc'],cond['all_c2ws'],cond['all_Ks'],cond['input_masks'],H=576,W=576,C=4,F=8,T=8,cfg=2.0,decoding_t=1,verbose=False,global_pbar=None,return_latents=True,device=device)
samples,latents=outputs; target=samples[4:].detach().float().cpu().numpy(); latent_out=latents.detach().float().cpu().numpy()
np.save(OUT/'predicted_target_rgb_fp32.npy',target,allow_pickle=False); np.save(OUT/'all8_latents_fp32.npy',latent_out,allow_pickle=False)
receipt={'schema':'s103-vmem-development-prediction-v1','status':'PREDICTION_COMPLETE','scope':'selector_free_development_baseline','run_id':os.environ.get('RUN_ID',''),'execution_boundary_id':os.environ['EXECUTION_BOUNDARY_ID'],'history_frame_ids':ids,'target_command_count':4,'resolution':[576,576],'context_num_frames':4,'target_num_frames':4,'sampling_steps':50,'seed':42,'dtype':'fp16_cuda_model_fp32_saved_outputs','reads':reads,'output_files':[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha_file(p)} for p in sorted(OUT.glob('*.npy'))],'future_outcome_files_opened':False,'future_gt_opened':False,'unauthorized_input_reads':0,'completed_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}
(OUT/'PREDICTION_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
