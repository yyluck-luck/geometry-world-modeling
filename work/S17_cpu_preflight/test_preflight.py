"""Small artificial component checks, never full VMem/CUT3R or trained weights.

Frozen test contract: CPU 8 threads/seed 0/FP32 network operations; official
RoPE call-site FP16 is tested explicitly. Attention uses no mask, noncausal,
dropout zero, default scale. FP32 attention tolerance (2e-6,2e-5); signed
RoPE positions up to 31: (2e-5,2e-5), FP16 (2e-3,2e-3); 767 stress only:
(3e-4,1e-4). No scalar threshold is selected after observing errors.
"""
import ast
import contextlib
import datetime
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback
import types
import warnings

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
START = time.perf_counter()
RESULT = {'status': 'RUNNING', 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'evidence': 'tiny artificial component tests, no trained model or real data',
          'checks': [], 'expected_original_failures': [], 'observations': {}}

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def check(name, ok, **detail):
    RESULT['checks'].append({'name': name, 'pass': bool(ok), **detail})
    if not ok:
        raise AssertionError(name + ': ' + str(detail))

def module(name, p):
    spec = importlib.util.spec_from_file_location(name, p)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj

def close(name, actual, reference, atol=2e-6, rtol=2e-5):
    delta = (actual.double() - reference.double()).abs()
    check(name, actual.shape == reference.shape and torch.isfinite(actual).all().item()
          and torch.allclose(actual.double(), reference.double(), atol=atol, rtol=rtol),
          shape=list(actual.shape), max_abs_error=delta.max().item(), atol=atol, rtol=rtol)

def scalar_rope(tokens, positions, base=100.0, factor=1.0):
    # Independent scalar Python float64 loop follows curope.cpp's axis/pair order.
    original = tokens.double().numpy()
    answer = original.copy()
    batch, heads, length, dim = original.shape
    quarter = dim // 4
    for b in range(batch):
        for h in range(heads):
            for n in range(length):
                for axis in range(2):
                    for j in range(quarter):
                        theta = factor * int(positions[b, n, axis]) / math.pow(base, j / quarter)
                        cost, sint = math.cos(theta), math.sin(theta)
                        a, z = axis * 2 * quarter + j, axis * 2 * quarter + j + quarter
                        u, v = float(original[b, h, n, a]), float(original[b, h, n, z])
                        answer[b, h, n, a] = u * cost - v * sint
                        answer[b, h, n, z] = v * cost + u * sint
    return torch.from_numpy(answer).to(tokens.dtype)

def extract_sample(where):
    p = HERE / where / 'utils/util.py'
    tree = ast.parse(p.read_text())
    fn = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'do_sample')
    namespace = {'torch': torch, 'math': math}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(p), 'exec'), namespace)
    return namespace['do_sample']

def sample_checks():
    original, patched = extract_sample('original'), extract_sample('patched')
    history = []
    def denoiser(model, noise, sigma, cond, num_frames):
        check('stub denoiser CPU inputs', noise.device.type == 'cpu' and num_frames == 2)
        return noise + cond['value']
    def sampler(fn, noise, scale, cond, uc, verbose, **kwargs):
        history.append(noise.clone())
        check('stub sampler device plumbing', all(kwargs[x].device.type == 'cpu' for x in ['c2w', 'K', 'input_frame_mask']))
        check('stub noise shape and dtype', noise.shape == (2, 4, 2, 2) and noise.dtype == torch.float32)
        return fn(noise, torch.ones(2), cond)
    class AE:
        def decode(self, latent, decoding_t):
            check('stub decode chunk', decoding_t == 1)
            return latent * 2
    args = dict(model=object(), ae=AE(), denoiser=denoiser, sampler=sampler,
                c={'value': torch.tensor(.5)}, uc={'value': torch.tensor(0.)},
                c2w=torch.eye(4)[None].repeat(2, 1, 1), K=torch.eye(3),
                cond_frames_mask=torch.tensor([True, False]), H=16, W=16, C=4,
                F=8, T=2, device='cpu', verbose=False)
    with warnings.catch_warnings(record=True) as caught:
        try:
            original(**args)
        except Exception as exc:
            RESULT['expected_original_failures'].append({'component': 'do_sample CPU stub', 'type': type(exc).__name__, 'message': str(exc)})
        else:
            check('original do_sample must expose fixed cuda transfer', False)
        RESULT['observations']['original_sample_warnings'] = [str(x.message) for x in caught]
    torch.manual_seed(17)
    expected = torch.randn(2, 4, 2, 2)
    torch.manual_seed(17)
    with warnings.catch_warnings(record=True) as caught:
        out, latent = patched(**args, return_latents=True)
    close('do_sample same CPU RNG source', history[-1], expected, 0., 0.)
    close('do_sample stub return latents', latent, expected + .5, 0., 0.)
    close('do_sample stub decoded result', out, (expected + .5) * 2, 0., 0.)
    check('patched CPU sample no autocast warning', len(caught) == 0)
    torch.manual_seed(17)
    close('do_sample return sample only', patched(**args), out, 0., 0.)
    args['sampler'] = lambda *a, **k: None
    check('do_sample interrupted sampler returns None', patched(**args) is None)

def run():
    global torch
    import torch
    from torch.nn.attention import SDPBackend, sdpa_kernel
    import torch.nn.functional as F
    torch.set_num_threads(8)
    torch.manual_seed(0)
    RESULT['environment'] = {'python': sys.version, 'executable': sys.executable,
                             'platform': platform.platform(), 'torch': torch.__version__,
                             'cpu_threads': torch.get_num_threads(), 'seed': 0,
                             'cuda_available': torch.cuda.is_available(),
                             'mps_available': torch.backends.mps.is_available(),
                             'dependencies': {}}
    for name in ['numpy', 'einops', 'omegaconf', 'diffusers', 'pytorch_lightning', 'open_clip',
                 'gradio', 'spaces', 'open3d', 'curope', 'kornia', 'transformers', 'safetensors', 'torchvision', 'cv2', 'roma']:
        spec = importlib.util.find_spec(name)
        RESULT['environment']['dependencies'][name] = {'present': spec is not None, 'origin': spec.origin if spec else None}
    provenance = json.loads((HERE / 'source_provenance.json').read_text())
    source = Path(provenance['source'])
    check('fixed author commit', subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() == provenance['commit'])
    for name, sha in provenance['files'].items():
        check('source unchanged ' + name, digest(source / name) == sha)
    for name in ['original', 'patched']:
        for p in (HERE / name).rglob('*.py'):
            ast.parse(p.read_text())
    check('all source copies parse', True)
    original = module('s17_original_transformer', HERE / 'original/modeling/modules/transformer.py')
    patched = module('s17_patched_transformer', HERE / 'patched/modeling/modules/transformer.py')

    for index, (b, h, lq, lk, d) in enumerate([(2, 5, 17, 17, 64), (2, 5, 17, 19, 64), (3, 2, 8, 8, 64), (1, 2, 129, 137, 64)]):
        q, k, v = torch.randn(b, h, lq, d), torch.randn(b, h, lk, d), torch.randn(b, h, lk, d)
        reference = (torch.softmax(q.double() @ k.double().transpose(-2, -1) / math.sqrt(d), -1) @ v.double()).float()
        with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU]) as profiler:
            with sdpa_kernel(SDPBackend.FLASH_ATTENTION):
                flash = F.scaled_dot_product_attention(q, k, v)
        ops = [x.key for x in profiler.key_averages() if 'attention' in x.key]
        RESULT['observations'].setdefault('native_flash_ops', []).append({'shape': [b,h,lq,lk,d], 'ops': ops})
        check(f'CPU native flash kernel {index}', 'aten::_scaled_dot_product_flash_attention_for_cpu' in ops)
        close(f'native FLASH vs FP64 dense {index}', flash, reference)
        with sdpa_kernel(SDPBackend.MATH):
            full = F.scaled_dot_product_attention(q, k, v)
            for chunk in [7, 64, 128]:
                chunked = torch.cat([F.scaled_dot_product_attention(q[:, :, start:start+chunk], k, v)
                                     for start in range(0, lq, chunk)], dim=-2)
                close(f'query chunk {chunk} vs FP64 dense {index}', chunked, reference)
        close(f'MATH vs FP64 dense {index}', full, reference)

    with torch.inference_mode():
        for context_dim in [None, 48]:
            old = original.Attention(64, context_dim=context_dim, heads=2, dim_head=64).eval()
            x = torch.randn(2, 17, 64)
            context = None if context_dim is None else torch.randn(2, 19, context_dim)
            expected = old(x, context)
            for chunk in [0, 7, 64, 128]:
                new = patched.Attention(64, context_dim=context_dim, heads=2, dim_head=64, cpu_math_query_chunk_size=chunk).eval()
                new.load_state_dict(old.state_dict())
                close(f'actual VMem Attention module context={context_dim} chunk={chunk}', new(x, context), expected)

    # Import original position module without installing the absent compiled package.
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        pos_old = module('s17_original_pos_embed', HERE / 'original/extern/CUT3R/src/croco/models/pos_embed.py')
    check('author fallback leaves RoPE2D undefined', not hasattr(pos_old, 'RoPE2D'))
    RESULT['expected_original_failures'].append({'component': 'pos_embed missing curope', 'type': 'undefined RoPE2D', 'message': stdout.getvalue().strip()})
    models = types.ModuleType('models')
    models.__path__ = [str(HERE / 'patched/extern/CUT3R/src/croco/models')]
    sys.modules['models'] = models
    rope = module('models.rope_cpu', HERE / 'patched/extern/CUT3R/src/croco/models/rope_cpu.py')
    pos_new = module('s17_patched_pos_embed', HERE / 'patched/extern/CUT3R/src/croco/models/pos_embed.py')
    for d in [48, 64]:
        positions = torch.tensor([[[-1, -1], [0, 0], [1, 2], [17, 31], [-31, -7], [31, -31]]], dtype=torch.int64)
        for dtype in [torch.float32, torch.float16]:
            tokens = torch.randn(1, 2, len(positions[0]), d).to(dtype)
            frozen = tokens.clone()
            for f0 in [1., -.5]:
                implementation = rope.RoPE2DPyTorch(100., f0)
                got = implementation(tokens, positions)
                tol = (2e-5, 2e-5) if dtype == torch.float32 else (2e-3, 2e-3)
                close(f'signed scalar RoPE D={d} {dtype} F0={f0}', got, scalar_rope(tokens, positions, factor=f0), *tol)
                check(f'RoPE output dtype D={d} {dtype} F0={f0}', got.dtype == dtype)
                check(f'RoPE nonmutation D={d} {dtype} F0={f0}', torch.equal(tokens, frozen))
            close(f'CPU dispatcher D={d} {dtype}', pos_new.RoPE2D()(tokens, positions), rope.RoPE2DPyTorch()(tokens, positions), 0, 0)
            close(f'zero position identity D={d} {dtype}', implementation(tokens, torch.zeros_like(positions)), tokens, 0, 0)
        stress_pos = torch.tensor([[[-767, 767], [324, -324], [31, -31]]], dtype=torch.int64)
        stress = torch.randn(1, 2, 3, d)
        close(f'signed RoPE stress D={d}', rope.RoPE2DPyTorch()(stress, stress_pos), scalar_rope(stress, stress_pos), 3e-4, 1e-4)
    for label, tok, pos in [('wrong_dtype', torch.zeros(1, 2, 3, 64).double(), torch.zeros(1, 3, 2, dtype=torch.int64)),
                            ('wrong_D', torch.zeros(1, 2, 3, 62), torch.zeros(1, 3, 2, dtype=torch.int64)),
                            ('float_positions', torch.zeros(1, 2, 3, 64), torch.zeros(1, 3, 2))]:
        try:
            rope.RoPE2DPyTorch()(tok, pos)
        except ValueError:
            check('reject ' + label, True)
        else:
            check('reject ' + label, False)

    blocks = module('s17_original_cut3r_blocks', HERE / 'original/extern/CUT3R/src/croco/models/blocks.py')
    class ScalarRoPE(torch.nn.Module):
        def forward(self, tokens, positions):
            check('actual CUT3R block sends FP16 to RoPE', tokens.dtype == torch.float16)
            return scalar_rope(tokens, positions)
    with torch.inference_mode():
        for dim in [96, 128]:
            p = torch.tensor([[[-1, -1], [0, 0], [31, 17], [8, -7]]], dtype=torch.int64)
            q, k, v = torch.randn(1, 4, dim), torch.randn(1, 3, dim), torch.randn(1, 3, dim)
            for cls, args in [(blocks.Attention, (q, p)), (blocks.CrossAttention, (q, k, v, p, p[:, :3]))]:
                actual = cls(dim=dim, num_heads=2, rope=rope.RoPE2DPyTorch()).eval()
                reference = cls(dim=dim, num_heads=2, rope=ScalarRoPE()).eval()
                reference.load_state_dict(actual.state_dict())
                close(f'CUT3R {cls.__name__} FP32 block through FP16 RoPE D={dim//2}', actual(*args), reference(*args), 2e-4, 2e-3)
    sample_checks()
    check('original tracked status still clean', not subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain', '--untracked-files=no'], text=True))
    for name, sha in provenance['files'].items():
        check('source posthash ' + name, digest(source / name) == sha)
    RESULT['scope'] = {'real_rgb_reads': 0, 'depth_image_reads': 0, 'trained_weight_reads': 0,
                       'full_model_instantiations': 0, 'tiny_random_attention_modules': True,
                       'full_pipeline_import': False, 'full_video_generation': False,
                       'network_downloads': 0, 'package_installs': 0, 'venv_changes': 0,
                       'CUDA_MPS_math_validation': False, 'backward_training_validation': False,
                       'original_frozen_checkout_unchanged': True}
    RESULT['status'] = 'PASS_COMPONENTS_ONLY'

if __name__ == '__main__':
    try:
        run()
    except BaseException as exc:
        RESULT['status'] = 'FAIL'
        RESULT['failure'] = {'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()}
    finally:
        RESULT['ended_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        RESULT['elapsed_seconds'] = time.perf_counter() - START
        RESULT['script_sha256'] = digest(__file__)
        RESULT['source_provenance_sha256'] = digest(HERE / 'source_provenance.json')
        RESULT['pass_checks'] = sum(x['pass'] for x in RESULT['checks'])
        out = HERE / 'numeric_receipt.json'
        if out.exists():
            raise FileExistsError('preserve earlier receipt; do not rerun successful preflight')
        out.write_text(json.dumps(RESULT, indent=2) + '\n')
        print(json.dumps({'status': RESULT['status'], 'pass_checks': RESULT['pass_checks'], 'elapsed_seconds': RESULT['elapsed_seconds'], 'failure': RESULT.get('failure')}))
    sys.exit(0 if RESULT['status'] == 'PASS_COMPONENTS_ONLY' else 1)
