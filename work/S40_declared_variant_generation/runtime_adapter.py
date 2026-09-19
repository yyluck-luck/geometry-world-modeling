"""Same reviewed S35 constructor and S39 v2 final checks, routed to the S40 gate."""
from __future__ import annotations
import ast
import copy
import json
from pathlib import Path
import generation_gate as gate_api

require,sha = gate_api.require,gate_api.sha
FACTORY = gate_api.ROOT/'work/S35_generation_integration/runtime_factory.py'
FACTORY_SHA = 'a7f812717c053b401433bac423ba0a63028a9dc1874b1cba3c4fbca6c276e3d0'
LABELS = {'LOADING_REAL_COMPONENTS':'LOADING_DECLARED_COMPONENT_VARIANT',
          'PASS_ORIGINAL_COMPONENT_LOADING_ONLY':'LOADED_PENDING_VARIANT_INVARIANT_CHECKS',
          'original_vae_local_directory':'declared_official_ft_mse_local_directory',
          'recorded_execution':'recorded_component_variant_loading'}


def derive_factory():
    require(sha(FACTORY)==FACTORY_SHA,'Original factory changed')
    original = ast.parse(FACTORY.read_text(),filename=str(FACTORY))
    derived = copy.deepcopy(original); count = {s:0 for s in LABELS}; imports = 0
    for node in ast.walk(derived):
        if isinstance(node,ast.ImportFrom) and node.module=='resource_gate':
            require([(x.name,x.asname) for x in node.names]==[('validate_gate',None),('require',None)],'Unexpected gate import')
            node.module='generation_gate'; imports+=1
        if isinstance(node,ast.Constant) and isinstance(node.value,str) and node.value in LABELS:
            count[node.value]+=1; node.value=LABELS[node.value]
    require(imports==1 and all(v==1 for v in count.values()),'Unexpected factory routing change count')
    inverse={v:k for k,v in LABELS.items()}; restored=copy.deepcopy(derived)
    for node in ast.walk(restored):
        if isinstance(node,ast.ImportFrom) and node.module=='generation_gate': node.module='resource_gate'
        if isinstance(node,ast.Constant) and isinstance(node.value,str) and node.value in inverse:
            node.value=inverse[node.value]
    require(ast.dump(restored,include_attributes=False)==ast.dump(original,include_attributes=False),
            'Changes outside gate routing and four identity labels')
    ns=dict(__file__=str(FACTORY),__name__='_s40_declared_factory')
    exec(compile(derived,str(FACTORY)+'[S40 gate/labels]','exec'),ns)
    return ns['create_runtime']


def create_runtime(gate):
    gate_api.validate_gate(gate)
    runtime=derive_factory()(gate)
    m=json.loads(Path(gate['manifest_path']).read_text())
    path=Path(m['output_root'])/'runtime_loading.json'
    loading=json.loads(path.read_text())
    try:
        # Exactly the S39 v2 attribute/list criteria, before initialize or any forward.
        import diffusers
        vae=runtime['pipeline'].vae; module=vae.module
        checks=dict(diffusers_version=diffusers.__version__,use_tiling=module.use_tiling,
            use_slicing=module.use_slicing,sample_size=module.config.sample_size,
            latent_channels=module.config.latent_channels,wrapper_chunk_size=vae.chunk_size,
            wrapper_scale_factor=vae.scale_factor,wrapper_downsample=vae.downsample)
        require(checks==dict(diffusers_version='0.32.2',use_tiling=False,use_slicing=False,
            sample_size=256,latent_channels=4,wrapper_chunk_size=1,wrapper_scale_factor=0.18215,
            wrapper_downsample=8),'Declared VAE path differs from reviewed S39')
        require(loading['status']=='LOADED_PENDING_VARIANT_INVARIANT_CHECKS','Factory did not finish loading')
        loads=loading.get('state_dict_loads')
        require(isinstance(loads,list) and loads and all(isinstance(x,dict) and
            x.get('missing_keys')==[] and x.get('unexpected_keys')==[] and 'strict_requested' in x
            for x in loads),'One or more recorded state-dict attempts was incomplete')
        gate_api.validate_gate(gate)
        loading.update(status='PASS_S40_DECLARED_VARIANT_COMPONENT_LOADING_ONLY',variant=gate_api.VARIANT,
            variant_invariants=checks,original_sd21_equivalence_verified=False,codec_numerics_verified=False,
            generation_completed=False)
    except BaseException as exc:
        loading.update(status='FAILED_S40_DECLARED_VARIANT_INVARIANTS',error_type=type(exc).__name__,error=str(exc))
        raise
    finally:
        temp=path.with_suffix('.s40.tmp')
        temp.write_text(json.dumps(loading,ensure_ascii=False,indent=2)+'\n');temp.replace(path)
    return runtime
