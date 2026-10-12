"""UC-input-only intervention; the original sampler state is never edited."""
import hashlib
import json
import types
from pathlib import Path
import torch


def digest(x):
    return hashlib.sha256(x.detach().contiguous().cpu().numpy().tobytes()).hexdigest()


class P2Denoiser:
    def __init__(self, original, context, arm, trace_file):
        assert arm in {'native', 'real', 'zero', 'permuted', 'low_cfg'}
        self.original = original
        self.context = context.detach().clone()
        self.arm = arm
        self.trace_file = Path(trace_file)
        self.eps = None
        self.rows = []

    def __getattr__(self, name):
        return getattr(self.original, name)

    def capture(self, initial):
        assert initial.shape[0] == 8 and self.eps is None
        self.eps = initial[:4].detach().clone()

    def __call__(self, network, x, sigma, cond, **kwargs):
        assert x.shape[0] == 16 and self.eps is not None
        assert self.context.shape == self.eps.shape == x[:4].shape
        assert not bool(cond['replace'][:8, -1].any())
        assert bool((cond['replace'][8:12, -1] == 1).all())
        q = self.original.idx_to_sigma(self.original.sigma_to_idx(sigma))
        qh = q[:4].reshape(4, 1, 1, 1)
        real = self.context + qh * self.eps
        rms = lambda t: float(t.float().square().mean().sqrt())
        row = {'step': len(self.rows), 'sigma_raw': float(sigma[0]),
               'sigma_quantized': float(q[0]),
               'native_context_to_real_rms': rms(x[:4] - real),
               'native_context_rms': rms(x[:4]),
               'source_rms': rms(self.context), 'noise_rms': rms(self.eps),
               'cpu_rng': digest(torch.get_rng_state()),
               'cuda_rng': digest(torch.cuda.get_rng_state()) if x.is_cuda else None}
        inp = x
        if self.arm not in {'native', 'low_cfg'}:
            inp = x.clone()
            source = (torch.zeros_like(self.context) if self.arm == 'zero' else
                      self.context.roll(1, 0) if self.arm == 'permuted' else self.context)
            inp[:4] = source + qh * self.eps
            assert torch.equal(inp[4:], x[4:])
        row['intervention_rms'] = rms(inp[:4] - x[:4])
        result = self.original(network, inp, sigma, cond, **kwargs)
        row['target_guidance_residual_rms'] = rms(result[12:16] - result[4:8])
        self.rows.append(row)
        return result

    def save(self):
        assert len(self.rows) == 50, len(self.rows)
        assert not self.trace_file.exists()
        self.trace_file.write_text(json.dumps({'arm': self.arm,
            'initial_context_noise_sha256': digest(self.eps), 'steps': self.rows}, indent=2)+'\n')


def capture_initial_noise(sampler, denoiser):
    original = sampler.prepare_sampling_loop
    def prepare(_self, x, *args, **kwargs):
        denoiser.capture(x)
        return original(x, *args, **kwargs)
    sampler.prepare_sampling_loop = types.MethodType(prepare, sampler)
    return sampler
