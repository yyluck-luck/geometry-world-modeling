"""Instance-local S86 hooks. No file I/O, model loading, or random draws."""
import math


def _strength(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("strength must be an int/float scalar")
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("strength must be finite in [0,1]")
    return value


def _copy(tensor):
    return tensor.detach().clone()


class _GuiderProxy:
    def __init__(self, controller, base):
        self.controller = controller
        self.base = base

    def prepare_inputs(self, x, s, c, uc):
        owner = self.controller
        row = owner._active()
        row["prepare_calls"] += 1
        if row["prepare_calls"] != 1:
            raise RuntimeError("multiple prepare_inputs calls in one original step")
        if row["step"] == owner.expected_steps:
            owner.last.update(x_tilde=_copy(x), sigma_hat=_copy(s))
        return self.base.prepare_inputs(x, s, c, uc)

    def __call__(self, x, sigma, scale, c2w, K, input_frame_mask):
        owner = self.controller
        row = owner._active()
        row["cfg_calls"] += 1
        if row["prepare_calls"] != 1 or row["cfg_calls"] != 1:
            raise RuntimeError("CFG call order/count differs from original")
        raw = self.base(x, sigma, scale, c2w, K, input_frame_mask)
        if row["step"] == owner.expected_steps:
            owner.last["raw_clean"] = _copy(raw)
        used = raw
        if owner.mode == "Gguide":
            if (owner.history_slots.shape != input_frame_mask.shape
                    or not bool((owner.history_slots == input_frame_mask).all())):
                raise ValueError("fusion history slots differ from original CFG input mask")
            row["fusion_calls"] += 1
            used = owner.fusion_fn(raw, owner.warp_latents, owner.support_mask,
                                   owner.history_slots, row["strength"])
            if used.shape != raw.shape or used.dtype != raw.dtype or used.device != raw.device:
                raise RuntimeError("fusion changed clean prediction shape/dtype/device")
        row["clean_returned_same_object"] = used is raw
        if row["step"] == owner.expected_steps:
            owner.last["used_clean"] = _copy(used)
        if owner.on_clean is not None:
            row["callback_calls"] += 1
            owner.on_clean(row["step"], raw, used)
        return used


class HookController:
    """Public state: steps JSON records and last detached same-device tensors."""
    def __init__(self, sampler, *, mode, expected_steps, fusion_fn=None,
                 warp_latents=None, support_mask=None, history_slots=None,
                 strengths=None, on_clean=None):
        if mode not in ("G0", "Gguide"):
            raise ValueError("mode must be G0 or Gguide")
        if isinstance(expected_steps, bool) or not isinstance(expected_steps, int) or expected_steps < 1:
            raise ValueError("expected_steps must be a positive integer")
        if hasattr(sampler, "_s86_hook_controller"):
            raise RuntimeError("hooks already installed on this sampler")
        if type(sampler.guider).__name__ != "MultiviewCFG":
            raise TypeError("this adapter requires the original MultiviewCFG")
        if on_clean is not None and not callable(on_clean):
            raise TypeError("on_clean must be callable or None")
        if mode == "Gguide":
            if not callable(fusion_fn) or any(v is None for v in (warp_latents, support_mask, history_slots)):
                raise ValueError("Gguide requires fusion function and all fusion tensors")
            if strengths is None or len(strengths) != expected_steps:
                raise ValueError("Gguide requires one frozen strength per step")
            strengths = tuple(_strength(v) for v in strengths)
        else:
            if strengths is not None:
                raise ValueError("G0 takes no strength schedule")
            strengths = (0.0,) * expected_steps
        self.mode = mode
        self.expected_steps = expected_steps
        self.fusion_fn = fusion_fn
        self.warp_latents = warp_latents
        self.support_mask = support_mask
        self.history_slots = history_slots
        self.strengths = strengths
        self.on_clean = on_clean
        self.steps = []
        self.last = {}
        self.current = None
        self.original_step = sampler.sampler_step
        self.base_guider = sampler.guider
        sampler.guider = _GuiderProxy(self, self.base_guider)
        sampler.sampler_step = self.observed_step
        sampler._s86_hook_controller = self

    def _active(self):
        if self.current is None:
            raise RuntimeError("guider called outside the observed original step")
        return self.current

    def observed_step(self, sigma, next_sigma, denoiser, x, scale, cond, uc,
                      gamma=0.0, **guider_kwargs):
        if self.current is not None:
            raise RuntimeError("nested sampler_step call")
        if any(row["status"] != "COMPLETED" for row in self.steps):
            raise RuntimeError("cannot resume a failed hooked sampler")
        step = len(self.steps) + 1
        if step > self.expected_steps:
            raise RuntimeError("more sampler steps than frozen expected_steps")
        row = dict(step=step, status="ENTERED", prepare_calls=0, cfg_calls=0,
                   fusion_calls=0, callback_calls=0, strength=self.strengths[step - 1])
        self.steps.append(row)
        self.current = row
        try:
            if step == self.expected_steps:
                self.last = dict(mode=self.mode, step=step, gamma=gamma, complete=False,
                                 sigma=_copy(sigma), next_sigma=_copy(next_sigma))
                if not bool((next_sigma == 0).all()):
                    raise ValueError("frozen last step must have next_sigma exactly zero")
            output = self.original_step(sigma, next_sigma, denoiser, x, scale,
                                        cond, uc, gamma, **guider_kwargs)
            if row["prepare_calls"] != 1 or row["cfg_calls"] != 1:
                raise RuntimeError("original step did not delegate once to each hook")
            if row["fusion_calls"] != (1 if self.mode == "Gguide" else 0):
                raise RuntimeError("fusion call count mismatch")
            if row["callback_calls"] != (1 if self.on_clean is not None else 0):
                raise RuntimeError("callback call count mismatch")
            if step == self.expected_steps:
                self.last.update(output=_copy(output), complete=True)
            row["status"] = "COMPLETED"
            return output
        except Exception as error:
            row.update(status="FAILED", error_type=type(error).__name__, error=str(error))
            raise
        finally:
            self.current = None

    def assert_complete(self):
        if self.current is not None or len(self.steps) != self.expected_steps:
            raise RuntimeError("incomplete sampler step count")
        for row in self.steps:
            if (row["status"] != "COMPLETED" or row["prepare_calls"] != 1
                    or row["cfg_calls"] != 1
                    or row["fusion_calls"] != (1 if self.mode == "Gguide" else 0)
                    or row["callback_calls"] != (1 if self.on_clean is not None else 0)):
                raise RuntimeError("incomplete hook record")
        if not self.last.get("complete", False):
            raise RuntimeError("last step capture is incomplete")
        return self.last


def install_hooks(sampler, *, mode, expected_steps, fusion_fn=None,
                  warp_latents=None, support_mask=None, history_slots=None,
                  strengths=None, on_clean=None):
    """Install once. on_clean(step, raw, used) must not mutate tensors or RNG."""
    return HookController(sampler, mode=mode, expected_steps=expected_steps,
                          fusion_fn=fusion_fn, warp_latents=warp_latents,
                          support_mask=support_mask, history_slots=history_slots,
                          strengths=strengths, on_clean=on_clean)


def replay_last(sampling, last, *, fusion_fn=None, warp_latents=None,
                support_mask=None, history_slots=None, strength=0.0):
    """Recompute G0's last Euler step, with optional clean fusion; no denoiser."""
    strength = _strength(strength)
    if last.get("mode") != "G0" or not last.get("complete", False):
        raise ValueError("replay requires a complete G0 last-step capture")
    x = last["x_tilde"]
    sigma_hat = last["sigma_hat"]
    next_sigma = last["next_sigma"]
    raw = last["raw_clean"]
    if not bool((next_sigma == 0).all()) or not bool((sigma_hat > 0).all()):
        raise ValueError("invalid final Euler sigmas")
    clean = raw
    if strength != 0:
        if not callable(fusion_fn) or any(v is None for v in (warp_latents, support_mask, history_slots)):
            raise ValueError("nonzero replay requires the fusion function and tensors")
        clean = fusion_fn(raw, warp_latents, support_mask, history_slots, strength)
        if clean.shape != raw.shape or clean.dtype != raw.dtype or clean.device != raw.device:
            raise RuntimeError("fusion changed clean prediction shape/dtype/device")
    derivative = sampling.to_d(x, sigma_hat, clean)
    dt = sampling.append_dims(next_sigma - sigma_hat, x.ndim)
    return dict(clean_used=clean, latents=x + dt * derivative)
