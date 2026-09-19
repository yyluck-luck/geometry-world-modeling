#!/usr/bin/env python3
"""Independent non-identity ray test for the reference override.  No diffusion.

An identity control cannot distinguish "the override is transparent" from "the
override never fires".  This test supplies a deliberately different, non-
degenerate reference (both rotation and translation) and checks the resulting
Plucker maps against an oracle computed independently, in FP64, from the raw
physical poses -- not from the matrix the override emitted.

Oracle, following the pinned conventions:
    D      = diag(1, -1, -1)
    Q_i    = R_i D                     (get_cond flips c2w columns 1 and 2)
    A_g,i  = [[Q_g^T Q_i, s Q_g^T (t_i - t_g)], [0, 1]]
The centring offset cancels in A, which is why the oracle does not reuse the
override's recovered-offset logic.

    o_g,i     = s Q_g^T (t_i - t_g)
    d_g,i,p   = normalize(Q_g^T Q_i K_eff^-1 p),  p = (u+0.5, v+0.5, 1)
    m_g,i,p   = o_g,i x d_g,i,p
    plucker   = [d, m]                 (direction first, then moment)

Reference-to-reference relation, the decisive check:
    H = E_b E_a^-1 = [[Q, t], [0, 1]]
    d_b = Q d_a
    m_b = Q m_a + t x (Q d_a)

Both conditioning branches are verified at both ray injection sites.
"""
import io, json, os, sys
from pathlib import Path
import numpy as np

RUN = Path(os.environ.get('RUN_ROOT', '/home/yliutz/gwm_source_transport_20260915'))
WEIGHTS = Path('/home/yliutz/gwm_weights_20260915')
DATA = Path(os.environ['DATA_ROOT'])
OUT = Path(os.environ['ARM_OUT'])
TOL_DIR = 1e-5
TOL_MOM_REL = 1e-5

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
AutoencoderKL.from_pretrained = lambda repo, *a, **k: _ov(
    str(WEIGHTS), local_files_only=True, force_download=False,
    low_cpu_mem_usage=False, use_safetensors=True)
_oc = open_clip.create_model_and_transforms
open_clip.create_model_and_transforms = lambda name, *a, **k: _oc(
    name, pretrained=str(WEIGHTS / 'open_clip_model.safetensors'))
_ol = torch.load
def _vl(path, *a, **k):
    if str(path) in {str(WEIGHTS / 'vmem_weights.pth'), str(WEIGHTS / 'cut3r_512_dpt_4_64.pth')}:
        k['weights_only'] = False
    return _ol(path, *a, **k)
torch.load = _vl
from modeling.pipeline import VMemPipeline

_REF = {"w2c": None, "used": 0}
_orig = PM.get_plucker_coordinates
def _patched(extrinsics_src, extrinsics, intrinsics, target_size, **kw):
    if _REF["w2c"] is not None:
        extrinsics_src = _REF["w2c"]; _REF["used"] += 1
    return _orig(extrinsics_src=extrinsics_src, extrinsics=extrinsics,
                 intrinsics=intrinsics, target_size=target_size, **kw)
PM.get_plucker_coordinates = _patched

device = 'cuda' if torch.cuda.is_available() else 'cpu'
cfg = OmegaConf.load(str(SOURCE / 'configs/inference/inference.yaml'))
D64 = np.diag([1.0, -1.0, -1.0])

def gridK(K):
    k = torch.tensor(K, dtype=torch.float32).clone()
    k[0] *= 768.0 / 640.0; k[1] *= 576.0 / 480.0; k[0, 2] -= 96.0
    return k

def build_cond(all_c2w_raw, all_K, lat, emb, mask, ref_c2w_raw_or_none, scale_probe=None):
    carrier = object.__new__(VMemPipeline)
    carrier.camera_scale = 2.0; carrier.device = torch.device(device)
    carrier.dtype = torch.float32; carrier.config = cfg
    raw_before = all_c2w_raw.clone()
    scale, all_c2w = VMemPipeline.get_translation_scaling_factor(carrier, all_c2w_raw.clone())
    if ref_c2w_raw_or_none is None:
        _REF["w2c"] = None
    else:
        offset = (raw_before[:, :3, 3] - all_c2w[:, :3, 3]).mean(0)
        ref = torch.tensor(ref_c2w_raw_or_none, device=device, dtype=torch.float32).clone()
        ref[:3, 3] -= offset
        ref[:, [1, 2]] *= -1
        rw = torch.linalg.inv(ref); rw[:3, 3] *= scale
        _REF["w2c"] = rw.unsqueeze(0)
    _REF["used"] = 0
    cond = VMemPipeline.get_cond(carrier, lat, all_c2w, all_K.clone(), scale, emb, mask)
    used = _REF["used"]; _REF["w2c"] = None
    return cond, float(scale), used

def oracle_plucker(raw_c2ws, ref_c2w_raw, scale, K_eff, H, W):
    """FP64, independent of the override's construction."""
    Qg = ref_c2w_raw[:3, :3] @ D64
    tg = ref_c2w_raw[:3, 3]
    v, u = np.meshgrid(np.arange(H, dtype=np.float64), np.arange(W, dtype=np.float64), indexing='ij')
    pix = np.stack([u + 0.5, v + 0.5, np.ones_like(u)], -1).reshape(-1, 3)
    Kinv = np.linalg.inv(K_eff.astype(np.float64))
    out = []
    for i in range(raw_c2ws.shape[0]):
        Qi = raw_c2ws[i, :3, :3] @ D64
        ti = raw_c2ws[i, :3, 3]
        M = Qg.T @ Qi
        o = scale * (Qg.T @ (ti - tg))
        d = (M @ (Kinv @ pix.T)).T
        d = d / np.linalg.norm(d, axis=1, keepdims=True)
        m = np.cross(np.broadcast_to(o, d.shape), d)
        out.append(np.concatenate([d, m], -1).reshape(H, W, 6).transpose(2, 0, 1))
    return np.stack(out), o

def main():
    root = DATA / 'heldout_3dmatch_scene13/extracted/rgbd-scenes-v2-scene_13'
    seq = root / 'seq-01'
    K0 = np.loadtxt(io.StringIO((root / 'camera-intrinsics.txt').read_text()), dtype=np.float32).reshape(3, 3)
    ctx_ids, tgt_ids = [0, 15, 30, 45], [60, 75, 90, 105]
    def pose(f):
        return np.loadtxt(io.StringIO((seq / f'frame-{f:06d}.pose.txt').read_text()),
                          dtype=np.float64).reshape(4, 4)
    raw = np.stack([pose(f) for f in ctx_ids + tgt_ids])
    all_c2w_raw = torch.tensor(raw, device=device, dtype=torch.float32)
    all_K = torch.stack([gridK(K0) for _ in range(8)]).to(device)
    lat = torch.zeros(4, 4, 72, 72, device=device)
    emb = torch.zeros(4, 1024, device=device)
    mask = torch.tensor([True] * 4 + [False] * 4, device=device)

    checks, detail = [], {}

    # Reference A: the native slot-0 camera.  Reference B: a deliberately
    # different, non-degenerate pose with BOTH rotation and translation.
    refA = raw[0].copy()
    ang = np.deg2rad(37.0)
    Rz = np.array([[np.cos(ang), -np.sin(ang), 0], [np.sin(ang), np.cos(ang), 0], [0, 0, 1]])
    refB = raw[0].copy()
    refB[:3, :3] = Rz @ refB[:3, :3]
    refB[:3, 3] = refB[:3, 3] + np.array([0.20, -0.10, 0.30])

    condN, sN, usedN = build_cond(all_c2w_raw, all_K, lat, emb, mask, None)
    condA, sA, usedA = build_cond(all_c2w_raw, all_K, lat, emb, mask, refA)
    condB, sB, usedB = build_cond(all_c2w_raw, all_K, lat, emb, mask, refB)
    checks.append(("override fires exactly once when installed and not at all when disabled",
                   usedN == 0 and usedA == 1 and usedB == 1))
    checks.append(("scale is unchanged by the reference choice", sN == sA == sB))

    # get_cond returns sibling keys 'c' and 'uc'; rays live inside each.
    pA = condA['c']['concat'][:, 1:7].detach().double().cpu().numpy()
    pB = condB['c']['concat'][:, 1:7].detach().double().cpu().numpy()
    Keff = gridK(K0).numpy()
    Hh, Ww = pA.shape[-2], pA.shape[-1]
    oraA, oA = oracle_plucker(raw, refA, sA, Keff, Hh, Ww)
    oraB, oB = oracle_plucker(raw, refB, sB, Keff, Hh, Ww)

    def err(actual, ora):
        ed = np.abs(actual[:, :3] - ora[:, :3]).max()
        denom = max(1.0, np.abs(ora[:, 3:]).max())
        em = np.abs(actual[:, 3:] - ora[:, 3:]).max() / denom
        return float(ed), float(em)

    eAd, eAm = err(pA, oraA); eBd, eBm = err(pB, oraB)
    detail['oracle_errors'] = {'refA_dir': eAd, 'refA_moment_rel': eAm,
                               'refB_dir': eBd, 'refB_moment_rel': eBm}
    checks.append(("native reference matches the FP64 oracle",
                   eAd <= TOL_DIR and eAm <= TOL_MOM_REL))
    checks.append(("non-identity reference matches the FP64 oracle",
                   eBd <= TOL_DIR and eBm <= TOL_MOM_REL))
    checks.append(("the non-identity reference actually changed the rays",
                   np.abs(pA - pB).max() > 1e-3))

    # Decisive reference-to-reference relation, computed from the oracle poses.
    QgA = refA[:3, :3] @ D64; QgB = refB[:3, :3] @ D64
    Q = QgB.T @ QgA
    t = sA * (QgB.T @ (refA[:3, 3] - refB[:3, 3]))
    # Q and t come from the raw physical reference poses, independently of the
    # override.  The relation is then applied to the PRODUCTION rays, not to the
    # oracle's own output: checking oracle against oracle would only confirm the
    # oracle's internal consistency and would say nothing about the override.
    dA, mA = pA[:, :3], pA[:, 3:]
    dB_pred = np.einsum('ij,njhw->nihw', Q, dA)
    mB_pred = np.einsum('ij,njhw->nihw', Q, mA) + np.cross(
        np.broadcast_to(t.reshape(1, 3, 1, 1), dB_pred.shape), dB_pred, axis=1)
    rel_d = float(np.abs(pB[:, :3] - dB_pred).max())
    rel_m = float(np.abs(pB[:, 3:] - mB_pred).max() / max(1.0, np.abs(oraB[:, 3:]).max()))
    detail['reference_relation_errors'] = {'direction': rel_d, 'moment_rel': rel_m}
    checks.append(("production rays satisfy d_b = Q d_a and m_b = Q m_a + t x (Q d_a)",
                   rel_d <= TOL_DIR and rel_m <= TOL_MOM_REL))

    # Both branches, both ray injection sites.  The conditional and unconditional
    # rays are intentionally identical, so a ray-only check cannot detect a branch
    # swap; the branch-distinguishing fields are asserted separately below.
    for name, cond, expect in (('A', condA, pA), ('B', condB, pB)):
        for branch in ('c', 'uc'):
            cc = cond[branch]['concat'][:, 1:7].detach().double().cpu().numpy()
            checks.append((f"ref {name}: {branch} concat[:,1:7] carries the rays",
                           np.abs(cc - expect).max() < 1e-6))
            if 'dense_vector' in cond[branch]:
                dv = cond[branch]['dense_vector'].detach().double().cpu().numpy()
                checks.append((f"ref {name}: {branch} dense_vector carries the same rays",
                               np.abs(dv - expect).max() < 1e-6))
    # Non-ray conditioning must be unchanged across the reference choice.
    for branch in ('c', 'uc'):
        for key in ('crossattn', 'replace'):
            if key in condA[branch] and key in condB[branch]:
                checks.append((f"{branch}[{key}] unchanged across references",
                               torch.equal(condA[branch][key], condB[branch][key])))
        checks.append((f"{branch} mask channel unchanged across references",
                       torch.equal(condA[branch]['concat'][:, 0], condB[branch]['concat'][:, 0])))
    # The two branches must remain distinguishable.
    distinct = any(k in condA['c'] and k in condA['uc']
                   and not torch.equal(condA['c'][k], condA['uc'][k])
                   for k in ('crossattn', 'replace', 'concat'))
    checks.append(("conditional and unconditional packets are not identical", distinct))

    detail['cond_keys'] = sorted(condA.keys())

    bad = 0
    for n, ok in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {n}")
        bad += 0 if ok else 1
    print()
    print(json.dumps(detail, indent=2, default=str))
    receipt = {'schema': 'non-identity-ray-test-v1',
               'status': 'PASS' if bad == 0 else 'FAIL',
               'checks': [{'name': n, 'passed': bool(o)} for n, o in checks],
               'detail': detail, 'tolerances': {'direction': TOL_DIR, 'moment_relative': TOL_MOM_REL},
               'note': 'zero diffusion; oracle computed in FP64 from raw physical poses',
               'new_method_validated': False, 'novelty_authorization': 'NONE'}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'RAY_TEST.json').write_text(json.dumps(receipt, indent=2, sort_keys=True, default=str) + '\n')
    return 0 if bad == 0 else 1

if __name__ == '__main__':
    raise SystemExit(main())
