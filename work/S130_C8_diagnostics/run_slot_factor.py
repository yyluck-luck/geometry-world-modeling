#!/usr/bin/env python3
"""Remote C8 Experiment 1 runner. Reuses the S107 model and launch recipe; no source edits."""
import datetime as dt, hashlib, io, json, os, random, socket, sys, time
from pathlib import Path
import numpy as np

RUN = Path(os.environ.get('RUN_ROOT', '/home/yliutz/gwm_source_transport_20260915'))
WEIGHTS = Path('/home/yliutz/gwm_weights_20260915')
BANK = Path(os.environ['BANK_STAGE'])
OUT = Path(os.environ['ARM_OUT'])
POSE = Path(os.environ['C8_S107_POSES'])
SEED = 42
SOURCE = RUN / 'vmem'
sys.path[:0] = [str(SOURCE), str(SOURCE / 'extern/CUT3R'), str(SOURCE / 'extern/CUT3R/src')]
os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1')
import torch
from omegaconf import OmegaConf
import huggingface_hub
from diffusers.models import AutoencoderKL
import open_clip
huggingface_hub.hf_hub_download = lambda repo_id, filename, *a, **k: str(WEIGHTS / filename)
import modeling.pipeline as PM
PM.hf_hub_download = huggingface_hub.hf_hub_download
_ov = AutoencoderKL.from_pretrained
AutoEncoderKL = AutoencoderKL
AutoencoderKL.from_pretrained = lambda repo, *a, **k: _ov(str(WEIGHTS), local_files_only=True, force_download=False, low_cpu_mem_usage=False, use_safetensors=True)
_oc = open_clip.create_model_and_transforms
open_clip.create_model_and_transforms = lambda name, *a, **k: _oc(name, pretrained=str(WEIGHTS / 'open_clip_model.safetensors'))
_ol = torch.load
def _vl(path, *a, **k):
    if str(path) in {str(WEIGHTS / 'vmem_weights.pth'), str(WEIGHTS / 'cut3r_512_dpt_4_64.pth')}: k['weights_only'] = False
    return _ol(path, *a, **k)
torch.load = _vl
from modeling.pipeline import VMemPipeline, encode_vae_image, encode_image
from modeling.sampling import DDPMDiscretization, DiscreteDenoiser, create_samplers
from utils import do_sample
from factorized_conditioning import build_conditioning

cfg = OmegaConf.load(str(SOURCE / 'configs/inference/inference.yaml'))
device, dtype = 'cuda', torch.float32
torch.set_num_threads(8); torch.set_num_interop_threads(1)
pipe = VMemPipeline(cfg, torch.device(device)); model, ae, clip = pipe.model_wrapper, pipe.vae, pipe.image_encoder

def sha(p):
    h=hashlib.sha256();
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20), b''): h.update(b)
    return h.hexdigest()
def gridK(K):
    k=torch.tensor(K,dtype=torch.float32,device=device).clone(); k[0]*=768/640; k[1]*=576/480; k[0,2]-=96; return k
def load_rgb(fid):
    from PIL import Image
    a=np.asarray(Image.open(BANK/'bank'/f'frame-{fid:06d}.color.png').convert('RGB'))
    t=torch.from_numpy(a.transpose(2,0,1).copy()).float()/255
    t=torch.nn.functional.interpolate(t.unsqueeze(0),(576,768),mode='area')[:,:,:,96:672]
    return (t*2-1)[0]
def pose(fid, sub='bank'):
    return np.loadtxt(io.StringIO((BANK/sub/f'frame-{fid:06d}.pose.txt').read_text()),dtype=np.float32).reshape(4,4)

def sample(ctx_ids, target_ids, convention, reference_id):
    random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)
    imgs=torch.stack([load_rgb(f) for f in ctx_ids]).to(device,dtype); lat=encode_vae_image(imgs,ae,device,dtype); emb=encode_image(imgs,clip,device,dtype)
    c2ws=torch.tensor(np.stack([pose(f) for f in ctx_ids]),device=device,dtype=torch.float32)
    qc2w=torch.tensor(np.stack([pose(f,'query') for f in target_ids]),device=device,dtype=torch.float32)
    Ks=torch.stack([gridK(np.loadtxt(io.StringIO((BANK/'camera-intrinsics.txt').read_text()),dtype=np.float32).reshape(3,3)) for _ in ctx_ids])
    qK=Ks[0]; allK=torch.cat([Ks,qK.unsqueeze(0).repeat(len(target_ids),1,1)])
    raw=torch.cat([c2ws,qc2w]); mask=torch.tensor([True]*4+[False]*4,device=device)
    carrier=object.__new__(VMemPipeline); carrier.camera_scale=2.0; carrier.device=torch.device(device); carrier.dtype=dtype; carrier.config=cfg
    ref=torch.tensor(pose(reference_id),device=device,dtype=torch.float32)
    cond=build_conditioning(carrier,lat,raw,allK,emb,mask,convention,ref)
    den=DiscreteDenoiser(DDPMDiscretization(),num_idx=1000,device=device)
    sampler=create_samplers(guider_types=int(cfg.model.guider_types),discretization=DDPMDiscretization(),num_frames=8,num_steps=int(cfg.model.inference_num_steps),cfg_min=float(cfg.model.cfg_min),device=device)[0]
    out,_=do_sample(model,ae,den,sampler,cond['c'],cond['uc'],cond['all_c2ws'],cond['all_Ks'],cond['input_masks'],H=576,W=576,C=4,F=8,T=8,cfg=float(cfg.model.cfg),decoding_t=1,verbose=False,global_pbar=None,return_latents=True,device=device)
    return out[0][4:].detach().float().cpu().numpy(), cond

payload=json.loads(POSE.read_text()); out_records=[]; OUT.mkdir(parents=True,exist_ok=True)
orders={'M1':([55,55,40,40],[40,55,55,40]),'M2':([50,50,45,45],[45,50,50,45])}
targets=[60,75,90,105]
for m,(a,b) in orders.items():
    for order_name,ctx in [('A',a),('B',b)]:
        for q in ('N','R','S','RS'):
            arr,cond=sample(ctx,targets,q,a[0]); tag=f'{m}_{order_name}_{q}_seed{SEED}'
            f=OUT/f'{tag}.npy'; np.save(f,arr,allow_pickle=False)
            out_records.append({'tag':tag,'multiset':m,'order':order_name,'convention':q,'seed':SEED,'context_frame_ids':ctx,'target_frame_ids':targets,'reference_frame_id':a[0],'output':{'path':str(f),'sha256':sha(f),'bytes':f.stat().st_size},'reference_override_calls':cond['c8_reference_override_calls']})
(Path(OUT/'C8_SLOT_FACTOR_RECEIPT.json')).write_text(json.dumps({'schema':'c8-slot-factor-v1','status':'OUTPUTS_COMPLETE_UNSCORED','recorded_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'hostname':socket.gethostname(),'slurm_job_id':os.environ.get('SLURM_JOB_ID'),'pose_receipt':str(POSE),'runs':out_records,'new_method_validated':False,'novelty_authorization':'NONE'},indent=2,sort_keys=True)+'\n')
print(json.dumps({'runs':len(out_records),'status':'OUTPUTS_COMPLETE_UNSCORED','new_method_validated':False,'novelty_authorization':'NONE'},indent=2))
