"""Create reviewable source-only candidates; never mutate the author checkout."""
from pathlib import Path
import datetime, difflib, hashlib, json, subprocess

HERE = Path(__file__).resolve().parent
SOURCE = Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem')
EXPECTED = '39291e4f272f6b4f270691d930926ab5930f942e'
FILES = ['modeling/modules/transformer.py', 'utils/util.py', 'modeling/pipeline.py',
         'app.py', 'modeling/network.py', 'requirements.txt',
         'extern/CUT3R/src/croco/models/pos_embed.py',
         'extern/CUT3R/src/croco/models/blocks.py',
         'extern/CUT3R/src/croco/models/crope.py',
         'extern/CUT3R/src/croco/models/curope/curope.cpp',
         'extern/CUT3R/src/croco/models/curope/kernels.cu',
         'extern/CUT3R/src/croco/models/curope/curope2d.py',
         'extern/CUT3R/src/croco/models/curope/setup.py']
FILES.remove('extern/CUT3R/src/croco/models/crope.py')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def replace_once(text, old, new):
    assert text.count(old) == 1, repr(old)
    return text.replace(old, new, 1)

def main():
    commit = subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip()
    status = subprocess.check_output(['git', '-C', str(SOURCE), 'status', '--porcelain', '--untracked-files=no'], text=True)
    assert commit == EXPECTED and not status
    provenance = {'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'source': str(SOURCE), 'commit': commit, 'tracked_status': status, 'files': {}}
    for name in FILES:
        data = (SOURCE / name).read_bytes()
        provenance['files'][name] = sha(data)
        for where in ['original', 'patched']:
            out = HERE / where / name
            out.parent.mkdir(parents=True, exist_ok=True)
            assert not out.exists(), str(out)
            out.write_bytes(data)
    p = HERE / 'patched/modeling/modules/transformer.py'
    t = p.read_text()
    begin = t.index('class Attention(nn.Module):')
    end = t.index('\n\nclass TransformerBlock', begin)
    a = t[begin:end]
    a = replace_once(a, '        dropout: float = 0.0,\n', '        dropout: float = 0.0,\n        cpu_math_query_chunk_size: int = 0,\n')
    a = replace_once(a, '        self.heads = heads\n', '        self.heads = heads\n        if not isinstance(cpu_math_query_chunk_size, int) or cpu_math_query_chunk_size < 0:\n            raise ValueError("cpu_math_query_chunk_size must be a nonnegative integer")\n        self.cpu_math_query_chunk_size = cpu_math_query_chunk_size\n')
    a = replace_once(a, '        with sdpa_kernel(SDPBackend.FLASH_ATTENTION):\n            out = F.scaled_dot_product_attention(q, k, v)', '''        # Native PyTorch 2.7 flash attention also works on CPU; retain it by default.
        # Optional bounded-memory math control: split Q only, retaining every K/V.
        # This module's actual contract is no mask, noncausal, attention dropout=0.
        if q.device.type == "cpu" and self.cpu_math_query_chunk_size:
            with sdpa_kernel(SDPBackend.MATH):
                out = torch.cat([
                    F.scaled_dot_product_attention(
                        q[:, :, start:start + self.cpu_math_query_chunk_size], k, v,
                        dropout_p=0.0, is_causal=False,
                    )
                    for start in range(0, q.shape[-2], self.cpu_math_query_chunk_size)
                ], dim=-2)
        else:
            with sdpa_kernel(SDPBackend.FLASH_ATTENTION):
                out = F.scaled_dot_product_attention(q, k, v)''')
    p.write_text(t[:begin] + a + t[end:])
    p = HERE / 'patched/utils/util.py'
    t = p.read_text()
    t = replace_once(t, '    num_samples = [1, T]\n    with torch.inference_mode(), torch.autocast("cuda"):', '''    device = torch.device(device)
    if device.type not in ("cpu", "cuda"):
        raise ValueError("This candidate supports CPU or CUDA; other devices are unvalidated")
    num_samples = [1, T]
    with torch.inference_mode(), torch.autocast(device_type=device.type, enabled=device.type == "cuda"):''')
    for key in ['c2w', 'K']:
        t = replace_once(t, f'"{key}": {key}.to("cuda")', f'"{key}": {key}.to(device)')
    t = replace_once(t, '"input_frame_mask": cond_frames_mask.to("cuda")', '"input_frame_mask": cond_frames_mask.to(device)')
    p.write_text(t)
    p = HERE / 'patched/modeling/pipeline.py'
    t = p.read_text()
    t = replace_once(t, "            device = 'cuda',\n", '            device = None,\n')
    t = replace_once(t, '        # Flip Y and Z components of camera poses to match dataset convention\n', '        device = self.device if device is None else device\n        # Flip Y and Z components of camera poses to match dataset convention\n')
    p.write_text(t)
    p = HERE / 'patched/app.py'
    t = replace_once(p.read_text(), '@torch.autocast("cuda")', '@torch.autocast(device_type=DEVICE.type, enabled=DEVICE.type == "cuda")')
    p.write_text(t)
    p = HERE / 'patched/extern/CUT3R/src/croco/models/pos_embed.py'
    t = p.read_text()
    first = t.index('# Directly use PyTorch implementation due to CUDA compatibility issues')
    last = t.index('\n\n# class RoPE2D', first)
    t = t[:first] + '''# Isolated S17 CPU candidate: preserve the compiled path on CUDA.
from models.rope_cpu import RoPE2DPyTorch
try:
    from models.curope import cuRoPE2D as _CompiledRoPE2D
except ImportError:
    _CompiledRoPE2D = None


class RoPE2D(torch.nn.Module):
    def __init__(self, freq=100.0, F0=1.0):
        super().__init__()
        self.base, self.F0 = freq, F0
        self.cpu_impl = RoPE2DPyTorch(freq, F0)
        self.compiled_impl = None if _CompiledRoPE2D is None else _CompiledRoPE2D(freq, F0)

    def forward(self, tokens, positions):
        if tokens.device.type == "cpu":
            return self.cpu_impl(tokens, positions)
        if tokens.device.type == "cuda" and self.compiled_impl is not None:
            return self.compiled_impl(tokens, positions)
        raise RuntimeError("No validated RoPE implementation for this device")
''' + t[last:]
    p.write_text(t)
    new = HERE / 'patched/extern/CUT3R/src/croco/models/rope_cpu.py'
    new.write_text('''# S17 CPU candidate derived from NAVER curope.cpp mathematical layout.
# Original cuRoPE code: Copyright (C) 2022-present NAVER Corporation.
# Licensed under CC BY-NC-SA 4.0. See author checkout LICENSE.
import math
import torch


class RoPE2DPyTorch(torch.nn.Module):
    """Signed positions; B,H,N,D tokens and B,N,2 int64 (y,x) positions.

    The official blocks cast q/k to float16 before RoPE even under FP32 inference.
    This CPU candidate computes rotations in float32 and restores the input dtype.
    It returns a new tensor; mutation/alias behavior and training are not validated.
    """
    def __init__(self, freq=100.0, F0=1.0):
        super().__init__()
        if not math.isfinite(freq) or freq <= 0 or not math.isfinite(F0):
            raise ValueError("finite positive base and finite F0 required")
        self.base, self.F0 = float(freq), float(F0)

    def forward(self, tokens, positions):
        if tokens.device.type != "cpu" or positions.device != tokens.device:
            raise ValueError("CPU tokens and positions on the same device required")
        if tokens.dtype not in (torch.float32, torch.float16):
            raise ValueError("Only FP32 and the official FP16 RoPE input are validated")
        if tokens.ndim != 4 or tokens.shape[-1] % 4:
            raise ValueError("Expected B,H,N,D with D divisible by four")
        if positions.shape != (tokens.shape[0], tokens.shape[2], 2) or positions.dtype != torch.int64:
            raise ValueError("Expected B,N,2 int64 signed positions")
        quarter = tokens.shape[-1] // 4
        denominator = self.base ** (torch.arange(quarter, dtype=torch.float32) / quarter)
        theta = self.F0 * positions.to(torch.float32)[..., None] / denominator
        cost, sint = theta.cos()[:, None], theta.sin()[:, None]
        pieces = tokens.float().reshape(*tokens.shape[:-1], 2, 2, quarter)
        u, v = pieces[..., 0, :], pieces[..., 1, :]
        result = torch.stack((u * cost - v * sint, v * cost + u * sint), dim=-2)
        return result.flatten(-3).to(tokens.dtype)
''')
    changed = []
    diff = []
    for p in sorted((HERE / 'patched').rglob('*.py')):
        name = str(p.relative_to(HERE / 'patched'))
        old = HERE / 'original' / name
        a = old.read_text() if old.exists() else ''
        b = p.read_text()
        if a != b:
            changed.append({'path': name, 'sha256': sha(p.read_bytes())})
            diff.extend(difflib.unified_diff(a.splitlines(True), b.splitlines(True), fromfile='a/' + name if old.exists() else '/dev/null', tofile='b/' + name))
    (HERE / 'cpu_candidate.patch').write_text(''.join(diff))
    provenance['changed_candidates'] = changed
    provenance['patch_sha256'] = sha((HERE / 'cpu_candidate.patch').read_bytes())
    (HERE / 'source_provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(json.dumps({'status': 'PREPARED', 'changed': len(changed), 'patch_sha256': provenance['patch_sha256']}))

if __name__ == '__main__':
    main()
