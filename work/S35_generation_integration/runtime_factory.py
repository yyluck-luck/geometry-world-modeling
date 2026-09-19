"""Prepared original CPU runtime factory; execute only in a fresh supervised worker.

No model or scientific library is imported at module import time. No real model
has been loaded by this preparation. Network stays disabled for this worker.
"""
from __future__ import annotations
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import socket
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SOURCE=ROOT/'work/S20_environment/isolated_vmem_source'


def create_runtime(gate):
    from resource_gate import validate_gate, require
    gate=validate_gate(gate)  # Before imports, input image reads, or constructors.
    m=json.loads(Path(gate['manifest_path']).read_text())
    out=Path(m['output_root'])
    require(out.is_absolute(), 'Absolute dedicated output root required')
    cwd=out/'runtime_cwd'
    cwd.mkdir(parents=True,exist_ok=False)
    receipt=out/'runtime_loading.json'
    require(not receipt.exists(), 'Do not overwrite a prior loading receipt')
    record=dict(status='LOADING_REAL_COMPONENTS',started_utc=datetime.now(timezone.utc).isoformat(),
                evidence_kind='recorded_execution',manifest_sha256=gate['manifest_sha256'],
                component_paths={k:v['path'] for k,v in gate['components'].items()},
                original_calls=[], state_dict_loads=[], network_attempts=0)
    def save():
        temporary=receipt.with_suffix('.tmp')
        temporary.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
        temporary.replace(receipt)
    save()
    def denied_network(*args,**kwargs):
        record['network_attempts']+=1
        raise RuntimeError('Offline original runtime forbids network access')
    socket.socket.connect=denied_network
    socket.socket.connect_ex=denied_network
    socket.create_connection=denied_network
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_IMPLICIT_TOKEN='1',
                      HF_HOME=str(cwd/'empty_hf_cache'),MPLBACKEND='Agg',MPLCONFIGDIR=str(cwd/'mpl'),
                      KORNIA_CHECK_VERSION='0',PYTHONDONTWRITEBYTECODE='1')
    sys.dont_write_bytecode=True
    require('modeling.pipeline' not in sys.modules and 'navigation' not in sys.modules,
            'Use a fresh worker, without pre-imported original pipeline aliases')
    sys.path[:0]=[str(ROOT/'work/S20_environment/site-packages'),str(ROOT/'work/S17C_environment/site-packages'),
                  str(SOURCE),str(SOURCE/'extern/CUT3R'),str(SOURCE/'extern/CUT3R/src')]
    os.chdir(cwd)  # Navigator's original visualization deletion is confined here.
    try:
        import numpy as np
        import torch
        from omegaconf import OmegaConf, DictConfig
        from omegaconf.base import ContainerMetadata, Metadata
        from omegaconf.nodes import AnyNode
        from collections import defaultdict
        from typing import Any
        import huggingface_hub
        import open_clip
        from diffusers.models import AutoencoderKL
        import modeling.pipeline as pipeline_module
        from navigation import Navigator
        from utils import load_img_and_K, transform_img_and_K, get_default_intrinsics
        require(torch.__version__.split('+')[0]=='2.7.0' and np.__version__=='1.26.4', 'Frozen scientific base versions required')
        require(Path(pipeline_module.__file__).resolve()==SOURCE/'modeling/pipeline.py', 'Wrong original pipeline source')
        torch.set_num_threads(8)
        random.seed(42);np.random.seed(42);torch.manual_seed(42)
        config=OmegaConf.load(m['config']['path'])
        for key in ['height','width','num_frames','context_num_frames','target_num_frames','inference_num_steps','use_non_maximum_suppression']:
            require(config.model[key]==gate['controls'][key], 'Original YAML differs: '+key)
        require(config.seed==42 and config.surfel.niter==400 and config.surfel.lr==.01, 'Original seed/geometry settings differ')
        require(config.model.model_path=='liguang0115/vmem' and config.surfel.model_path=='liguang0115/cut3r', 'Original model names required')
        config.model.samples_dir=str(cwd/'samples')
        config.visualization_dir=str(cwd/'visualization')
        config.inference.visualize=False
        config.inference.visualize_pointcloud=False
        config.inference.visualize_surfel=False
        allowed=[DictConfig,ContainerMetadata,Any,dict,defaultdict,AnyNode,Metadata]
        old_torch_load=torch.load
        old_vae_load=AutoencoderKL.from_pretrained
        old_clip_load=open_clip.create_model_and_transforms
        old_state_load=torch.nn.Module.load_state_dict
        component_paths={str(Path(x['path']).resolve()) for x in gate['components'].values()}
        def local_hub(*args,**kwargs):
            require(not args and set(kwargs)=={'repo_id','filename'}, 'Unexpected original Hub call')
            key=(kwargs['repo_id'],kwargs['filename'])
            routes={('liguang0115/vmem','vmem_weights.pth'):'vmem',
                    ('liguang0115/cut3r','cut3r_512_dpt_4_64.pth'):'cut3r'}
            require(key in routes, 'Unfrozen Hub asset')
            record['original_calls'].append({'loader':'hf_hub_download_local_resolution','repo':key[0],'filename':key[1]})
            return gate['components'][routes[key]]['path']
        def safe_torch_load(f,*args,**kwargs):
            require(isinstance(f,(str,os.PathLike)) and str(Path(f).resolve()) in component_paths, 'Unfrozen Torch weight input')
            require(kwargs.get('weights_only',True) is True, 'Unsafe weight loading is not permitted')
            kwargs['weights_only']=True
            return old_torch_load(f,*args,**kwargs)
        def checked_state_load(module,*args,**kwargs):
            result=old_state_load(module,*args,**kwargs)
            item={'class':type(module).__name__,'strict_requested':kwargs.get('strict',True),
                  'missing_keys':list(result.missing_keys),'unexpected_keys':list(result.unexpected_keys)}
            record['state_dict_loads'].append(item)
            require(not item['missing_keys'] and not item['unexpected_keys'], 'Incomplete original state_dict load')
            return result
        def local_vae(repo,*args,**kwargs):
            require(repo=='stabilityai/stable-diffusion-2-1-base' and not args and
                    kwargs==dict(subfolder='vae',force_download=False,low_cpu_mem_usage=False), 'Unexpected original VAE invocation')
            weight=Path(gate['components']['vae_weight']['path'])
            loaded,info=old_vae_load(str(weight.parent),local_files_only=True,force_download=False,
                                     low_cpu_mem_usage=False,use_safetensors=weight.suffix=='.safetensors',
                                     output_loading_info=True)
            record['vae_loading_info']=info
            require(not any(info.get(k) for k in ['missing_keys','unexpected_keys','mismatched_keys','error_msgs']), 'Incomplete original VAE load')
            record['original_calls'].append({'loader':'original_vae_local_directory','calls':1})
            return loaded
        def local_clip(name,*args,**kwargs):
            require(name=='ViT-H-14' and not args and kwargs=={'pretrained':'laion2b_s32b_b79k'}, 'Unexpected original CLIP invocation')
            record['original_calls'].append({'loader':'original_clip_local_safetensors','calls':1})
            return old_clip_load(name,pretrained=gate['components']['clip']['path'])
        with ExitStack() as stack:
            stack.enter_context(patch.object(huggingface_hub,'hf_hub_download',local_hub))
            stack.enter_context(patch.object(torch,'load',safe_torch_load))
            stack.enter_context(patch.object(torch.nn.Module,'load_state_dict',checked_state_load))
            stack.enter_context(patch.object(AutoencoderKL,'from_pretrained',local_vae))
            stack.enter_context(patch.object(open_clip,'create_model_and_transforms',local_clip))
            stack.enter_context(torch.serialization.safe_globals(allowed))
            pipeline=pipeline_module.VMemPipeline(config,device='cpu',dtype=torch.float32)
        for name in ['model','vae','image_encoder','surfel_model']:
            component=getattr(pipeline,name)
            require(not any(x.training for x in component.modules()), 'Original component must be in eval mode: '+name)
            require(all(p.device.type=='cpu' and p.dtype==torch.float32 for p in component.parameters()), 'CPU FP32 parameters required: '+name)
        image,_=load_img_and_K(m['input_image']['path'],None,K=None,device='cpu')
        image,_=transform_img_and_K(image,(576,576),mode='crop',K=None)
        navigator=Navigator(pipeline,step_size=.1,num_interpolation_frames=4)
        record.update(status='PASS_ORIGINAL_COMPONENT_LOADING_ONLY',completed_utc=datetime.now(timezone.utc).isoformat(),
                      torch_version=torch.__version__,numpy_version=np.__version__,generation_calls=0)
        save()
        return dict(pipeline=pipeline,navigator=navigator,pipeline_module=pipeline_module,image=image,
                    initial_pose=np.eye(4),initial_K=np.array(get_default_intrinsics()[0]))
    except BaseException as exc:
        record.update(status='FAILED_RUNTIME_PREPARATION',error_type=type(exc).__name__,error=str(exc),
                      completed_utc=datetime.now(timezone.utc).isoformat())
        save()
        raise
