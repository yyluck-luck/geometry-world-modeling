"""Ordinary masked clean-prediction fusion, not a new research method.

Pure tensor prototype only. No camera, image, model, sampler or file I/O.
Use AFTER CFG and BEFORE the original Euler derivative, if a later frozen
experiment authorizes integration. The current VMem sampler is unchanged.
"""
import math
import torch


def fuse_clean_prediction(denoised, warp_latents, support_mask, history_slots, strength):
    """Blend target slots; preserve every unsupported/history value exactly.

    denoised/warp_latents: same floating [T,C,H,W], dtype and device.
    support_mask: floating [T,1,H,W] in[0,1], same dtype/device.
    history_slots: bool[T], same device; True slots are never modified.
    strength: scalar[0,1], fixed by the later experiment contract.

    Source geometry, VAE encoding and mask construction are caller inputs;
    this helper does not verify those scientific provenance requirements.
    Zero strength or no target support returns the ORIGINAL tensor object,
    without arithmetic or RNG draws. Nonzero calls allocate a new tensor.
    """
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise TypeError('strength must be a finite scalar number')
    if not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be in [0,1]')
    if denoised.ndim != 4 or not denoised.is_floating_point():
        raise ValueError('denoised must be floating [T,C,H,W]')
    if warp_latents.shape != denoised.shape:
        raise ValueError('warp shape mismatch')
    if support_mask.shape != (denoised.shape[0], 1, *denoised.shape[2:]):
        raise ValueError('support_mask must be [T,1,H,W]')
    if history_slots.shape != (denoised.shape[0],) or history_slots.dtype != torch.bool:
        raise ValueError('history_slots must be bool[T]')
    for other in (warp_latents, support_mask):
        if other.dtype != denoised.dtype or other.device != denoised.device:
            raise ValueError('no implicit dtype/device conversion is permitted')
    if history_slots.device != denoised.device:
        raise ValueError('history_slots device mismatch')
    if any(not bool(torch.isfinite(t).all()) for t in (denoised, warp_latents, support_mask)):
        raise ValueError('nonfinite tensor input')
    if bool(((support_mask < 0) | (support_mask > 1)).any()):
        raise ValueError('support_mask must be in [0,1]')
    if strength == 0:
        return denoised
    weight = support_mask * (~history_slots).reshape(-1, 1, 1, 1) * strength
    if not bool((weight > 0).any()):
        return denoised
    mixed = (1 - weight) * denoised + weight * warp_latents
    # Explicit selection preserves untouched values including signed zero.
    return torch.where(weight > 0, mixed, denoised)
