"""One create-only, synthetic-only author check; never calls runner.run or a VAE."""
import ast
import importlib.util
import json
import sys
import time
import traceback
from pathlib import Path
from datetime import datetime, timezone

H = Path(__file__).resolve().parent
OUT = H / 'author_synthetic_01'


def main():
    OUT.mkdir()
    started = time.monotonic()
    report = dict(status='RUNNING', started_utc=datetime.now(timezone.utc).isoformat(),
                  checks=[], actual_scientific_array_reads=0, actual_weight_reads=0,
                  actual_VAE_instances=0, actual_decoder_calls=0, auto_retries=0)
    try:
        cfg = json.loads((H / 'GENERATION_CONTRACT.json').read_text())
        sys.path[:0] = cfg['pythonpath']
        import numpy as np
        import torch
        from PIL import Image
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        spec = importlib.util.spec_from_file_location('s87_author', H / 'generate_terminal_controls.py')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        report['runner_sha256'] = mod.sha((H / 'generate_terminal_controls.py').read_bytes())
        report['contract_sha256'] = mod.sha((H / 'GENERATION_CONTRACT.json').read_bytes())
        report['check_source_sha256'] = mod.sha(Path(__file__).read_bytes())
        sources = {k: Path(v['path']).read_text() for k, v in cfg['sources'].items()}
        for k, source in sources.items():
            assert mod.sha(source.encode()) == cfg['sources'][k]['sha256']
        def check(name, good):
            assert bool(good), name
            report['checks'].append(name)
            assert time.monotonic() - started < 60, 'synthetic60s'
        same = lambda a, b: a.contiguous().numpy().tobytes() == b.contiguous().numpy().tobytes()
        functions = mod.load_functions(sources['sampling'], ['append_dims', 'to_d'],
                                       {'torch': torch}, cfg['sources']['sampling']['path'])
        namespaces = []
        for key in ('hooks', 'fusion'):
            ns = {}
            exec(compile(sources[key], cfg['sources'][key]['path'], 'exec'), ns)
            namespaces.append(ns)
        replay = namespaces[0]['replay_last']
        fuse = namespaces[1]['fuse_clean_prediction']
        raw = torch.full((8, 4, 2, 2), 2.0)
        raw[:4] = -0.0
        warp = torch.full_like(raw, 10.0)
        warp[:4] = 0.0
        mask = torch.tensor([0., .25, .5, 1.]).reshape(1, 1, 2, 2).repeat(8, 1, 1, 1)
        mask[:4] = 0.0
        history = torch.tensor([True]*4 + [False]*4)
        sigma_hat = torch.full((8,), 1.000001)
        x = torch.full_like(raw, 3.0)
        original = x + (-sigma_hat[:, None, None, None]) * ((x - raw) / sigma_hat[:, None, None, None])
        last = dict(mode='G0', complete=True, x_tilde=x, sigma_hat=sigma_hat,
                    next_sigma=torch.zeros(8), raw_clean=raw)
        protected = ((mask == 0) | history[:, None, None, None]).expand_as(raw)
        rng_start = torch.get_rng_state().clone()
        for strength in (.5, .75, 1.):
            d = replay(functions, last, fusion_fn=fuse, warp_latents=warp,
                       support_mask=mask, history_slots=history, strength=strength)
            check(f'{strength}:hand clean values', d['clean_used'][4, 0].flatten().tolist() ==
                  [2., 2.+2.*strength, 2.+4.*strength, 2.+8.*strength])
            check(f'{strength}:history/zero clean bytes', same(d['clean_used'][protected], raw[protected]))
            check(f'{strength}:history/zero latent bytes', same(d['latents'][protected], original[protected]))
            expected = x + (-sigma_hat[:,None,None,None]) * ((x - d['clean_used']) / sigma_hat[:,None,None,None])
            check(f'{strength}:original Euler operation sequence', same(d['latents'], expected))
        check('lambda1 fractional support not full warp', float(d['clean_used'][4,0,0,1]) == 4.)
        check('zero strength original object', fuse(raw, warp, mask, history, 0) is raw)
        check('all-zero support original object', fuse(raw, warp, torch.zeros_like(mask), history, 1) is raw)
        invalid = dict(last, next_sigma=torch.ones(8))
        try:
            replay(functions, invalid)
            raise AssertionError('invalid sigma accepted')
        except ValueError:
            check('invalid sigma fails', True)
        try:
            fuse(raw, warp.double(), mask, history, .5)
            raise AssertionError('different dtype accepted')
        except ValueError:
            check('different dtype fails', True)
        r = torch.tensor([[[[-0.0, .2], [1.2, .5]]]]).repeat(4,3,1,1)
        rgb_warp = torch.full_like(r, .8)
        rgb_mask = torch.tensor([False, True, True, False]).reshape(1,1,2,2).repeat(4,1,1,1)
        for strength in (.5,.75,1.):
            p = mod.paste(r, rgb_warp, rgb_mask, strength, torch)
            check(f'{strength}:RGB hole signed zero', same(p[...,0,0], r[...,0,0]))
            check(f'{strength}:RGB masked hand result',
                  bool((p[...,0,1] == (1-strength)*torch.tensor(.2) + strength*torch.tensor(.8)).all()))
            check(f'{strength}:RGB clamp before blend',
                  bool((p[...,1,0] == (1-strength)*torch.tensor(1.) + strength*torch.tensor(.8)).all()))
        negative = torch.full((4,3,2,2), -.5)
        check('RGB negative branch maps before clamp', bool((mod.paste(negative,rgb_warp,torch.zeros_like(rgb_mask),.5,torch)==.25).all()))
        util = mod.load_functions(sources['util'], ['tensor_to_pil'],
                                 {'torch':torch,'np':np,'Image':Image}, cfg['sources']['util']['path'])
        qraw = torch.tensor([-.1, 0., .5, 1.2], dtype=torch.float32).reshape(1,1,2,2).repeat(4,3,1,1)
        qraw[1] = torch.tensor([-.1001,-1.,0.,1.]).reshape(1,2,2)
        qraw[2] = torch.tensor([0.,1/255, .5,1.1]).reshape(1,2,2)
        qraw[3] = torch.tensor([-0.,0.,.001,1.]).reshape(1,2,2)
        q, branches = mod.quantize(qraw.numpy(), np)
        original_q = np.stack([np.array(util.tensor_to_pil(t)) for t in qraw])
        check('four artificial frames original quantizer bytes', q.tobytes() == original_q.tobytes())
        check('uint8 truncation .5 ->127', bool((q[2,1,0] == 127).all()))
        qbad = qraw.numpy().copy(); qbad[0,0,0,0] = np.nan
        try:
            mod.quantize(qbad,np)
            raise AssertionError('nonfinite accepted')
        except RuntimeError:
            check('nonfinite output fails',True)
        # Original class and decode methods, with an explicit tiny stand-in KL module.
        calls = []
        class StubKL(torch.nn.Module):
            def decode(self,z):
                calls.append(list(z.shape))
                return type('Result', (), {'sample':z[:,:3]})()
        class Factory:
            @staticmethod
            def from_pretrained(repo, **kwargs):
                assert repo == 'stabilityai/stable-diffusion-2-1-base'
                assert kwargs == dict(subfolder='vae',force_download=False,low_cpu_mem_usage=False)
                return StubKL()
        tree = ast.parse(sources['autoencoder'])
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'AutoEncoder')
        ns = dict(torch=torch, nn=torch.nn, AutoencoderKL=Factory)
        exec(compile(ast.Module(body=[cls],type_ignores=[]),'original-wrapper-class','exec'),ns)
        ae = ns['AutoEncoder'](chunk_size=1)
        for strength in (.5,.75,1.):
            out = ae.decode(torch.full((8,4,2,2),strength),1)
            check(f'{strength}:original wrapper full8 stub decode', list(out.shape)==[8,3,2,2])
            check(f'{strength}:original .18215 decode scaling', same(out,torch.full((8,3,2,2),strength)/.18215))
        check('three full8 decode calls ->24 chunks1', calls == [[1,4,2,2]]*24)
        check('synthetic helper/stub RNG unchanged', same(rng_start,torch.get_rng_state()))
        report['stub_decoder_chunks'] = len(calls)
        report['status'] = 'PASS_SYNTHETIC_ONLY'
        result = 0
    except BaseException as error:
        report.update(status='FAILED_PRESERVED_NO_AUTO_RETRY', error=str(error), traceback=traceback.format_exc())
        result = 1
    report.update(completed_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-started)
    (OUT/'RECEIPT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
    return result


if __name__ == '__main__':
    sys.exit(main())
