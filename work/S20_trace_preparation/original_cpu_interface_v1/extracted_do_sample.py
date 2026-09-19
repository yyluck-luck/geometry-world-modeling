def do_sample(
    model,
    ae,
    denoiser,
    sampler,
    c,
    uc,
    c2w,
    K,
    cond_frames_mask,
    H=576,
    W=768,
    C=4,
    F=8,
    T=8,
    cfg=2.0,
    decoding_t=1,
    verbose=True,
    global_pbar=None,
    return_latents=False,
    device: str = "cuda",
    **_,
):

    device = torch.device(device)
    if device.type not in ("cpu", "cuda"):
        raise ValueError("This candidate supports CPU or CUDA; other devices are unvalidated")
    num_samples = [1, T]
    with torch.inference_mode(), torch.autocast(device_type=device.type, enabled=device.type == "cuda"):

        additional_model_inputs = {"num_frames": T}
        additional_sampler_inputs = {
            "c2w": c2w.to(device),
            "K": K.to(device),
            "input_frame_mask": cond_frames_mask.to(device),
        }
        if global_pbar is not None:
            additional_sampler_inputs["global_pbar"] = global_pbar

        shape = (math.prod(num_samples), C, H // F, W // F)
        randn = torch.randn(shape).to(device)

        samples_z = sampler(
            lambda input, sigma, c: denoiser(
                model,
                input,
                sigma,
                c,
                **additional_model_inputs,
            ),
            randn,
            scale=cfg,
            cond=c,
            uc=uc,
            verbose=verbose,
            **additional_sampler_inputs,
        )
        if samples_z is None:
            return

        samples = ae.decode(samples_z, decoding_t)
    if return_latents:
        return samples, samples_z
    
    return samples
