"""S20 metadata/source-only check; no model imports, weights, images or arrays."""
from pathlib import Path
import ast, datetime, hashlib, json

W = Path(__file__).resolve().parent
ROOT = W.parents[1]
VMEM = Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem')
checks = []
def check(name, condition):
    checks.append({'name': name, 'pass': bool(condition)})
    if not condition:
        raise AssertionError(name)
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

api = json.loads((W / 'laion_api.body').read_text())
files = {x['rfilename']: x for x in api['siblings']}
safe = files['open_clip_model.safetensors']
check('publisher', api['id'] == 'laion/CLIP-ViT-H-14-laion2B-s32B-b79K')
check('public metadata', api['private'] is False and api['gated'] is False)
check('revision', api['sha'] == '1c2b8495b28150b8a4922ee1c8edee224c284c0c')
check('safe length', safe['size'] == 3944517836)
check('LFS identity', safe['lfs']['sha256'] == '0084e75319a50ad85ef45377bad5bc38f2f58824459eb690048d51c9f8863be5')
cfg = json.loads((W / 'clip_hub_config.body').read_text())
arch = json.loads((W / 'clip_architecture.json').read_text())
check('Hub and version 2.30.0 architecture exact', cfg['model_cfg'] == arch)
check('preprocess mean', cfg['preprocess_cfg']['mean'] == [0.48145466, 0.4578275, 0.40821073])
check('preprocess std', cfg['preprocess_cfg']['std'] == [0.26862954, 0.26130258, 0.27577711])
pre = (W / 'clip_pretrained.py').read_text()
factory = (W / 'clip_factory.py').read_text()
constants = (W / 'clip_constants.py').read_text()
for name, source in [('pretrained', pre), ('factory', factory), ('constants', constants)]:
    ast.parse(source)
    check(name + ' parse', True)
check('tag maps exact LAION repository', "laion2b_s32b_b79k=_pcfg(hf_hub='laion/CLIP-ViT-H-14-laion2B-s32B-b79K/')" in pre)
check('OpenCLIP safe filename', 'open_clip_model.safetensors' in constants)
check('safe load source', 'from safetensors.torch import load_file' in factory and 'checkpoint = load_file(checkpoint_path, device=device)' in factory)
check('local pretrained path accepted', 'elif os.path.exists(pretrained):' in factory)
head = json.loads((W / 'clip_weight_head.json').read_text())
check('anonymous HEAD success', head['curl_returncode'] == 0 and any(x.startswith('HTTP/2 200') for x in head['headers']))
check('HEAD agrees size', 'content-length: 3944517836' in head['headers'])
check('HEAD agrees LFS', any('0084e75319a50ad85ef45377bad5bc38f2f58824459eb690048d51c9f8863be5' in x for x in head['headers']))
check('HEAD supports range', 'accept-ranges: bytes' in head['headers'])
vae = (VMEM / 'modeling/modules/autoencoder.py').read_text()
clip = (VMEM / 'modeling/modules/conditioner.py').read_text()
check('original VAE repository and subfolder', '"stabilityai/stable-diffusion-2-1-base"' in vae and 'subfolder="vae"' in vae)
check('original scale and mean', '0.18215' in vae and '.latent_dist.mean' in vae)
check('original CLIP architecture and tag', '"ViT-H-14", pretrained="laion2b_s32b_b79k"' in clip)
check('original Kornia preprocess', 'align_corners=True' in clip and 'antialias=True' in clip and 'interpolation="bicubic"' in clip)
sources = [VMEM / 'modeling/modules/autoencoder.py', VMEM / 'modeling/modules/conditioner.py']
inputs = [p for p in W.iterdir() if p.suffix in {'.body', '.py', '.json', '.txt'} and p.name != 'static_compatibility.json']
receipt = {'schema': 's20-static-source-metadata-check-v1', 'status': 'PASS_SOURCE_AND_METADATA_ONLY',
           'completed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'checks': checks,
           'check_count': len(checks), 'model_weight_payload_downloads': 0, 'weight_loads': 0,
           'model_instantiations': 0, 'image_decodes': 0, 'array_reads': 0, 'package_installs': 0,
           'runtime_compatibility_verified': False,
           'input_files': {str(p): {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sources + inputs}}
(W / 'static_compatibility.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'status': receipt['status'], 'checks': len(checks)}))
