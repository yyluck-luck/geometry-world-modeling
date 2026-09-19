# Gemini visible answer (accessibility text transcription)

The AX representation omits several inline mathematical tokens. Gguide/G0 names are preserved as visible; blank formula locations below are not reconstructed as quoted math. This is a model answer, not verified research evidence.

## 1. Falsifiable Mechanism Hypothesis

Hypothesis: The latent blending in Gguide does not merely copy the warped history into the support mask. Instead, injecting its latents actively propagates through the VAE’s global receptive fields (GroupNorm and spatial attention), causing structural alterations in the unmasked generation region compared to G0. This implies Gguide uses the constrained geometry inside the mask as a semantic anchor to globally harmonize the surrounding scene, producing correlated pixel changes outside the mask that pixel-space compositing (Gpaste) cannot achieve.

## 2. Necessary Control and Predeclared Failure Condition

The Control: Execute Gguide using a spatially scrambled version of the warp (shuffling the pixels inside the mask to destroy geometric structure while preserving the exact color/frequency distribution and masking operations), using the identical seed, cameras, and number of sampling/blending steps. Compare the unmasked regions of Gguide(W), Gguide(W_scramble), and G0.

Predeclared Failure Condition: The hypothesis is falsified if the unmasked region of Gguide(W_scramble) diverges from G0 to the same degree and with the same boundary-smoothing artifacts as Gguide(W). If this occurs, the alterations outside the mask are merely a mechanical reaction to latent discontinuities or the extra compute steps of the blending operation, rather than a geometrically aware harmonization of your specific warped history.

## 3. Why this does not establish novelty

Even if Gguide successfully harmonizes the warped geometry with the unmasked region, this demonstrates a known operational effect of latent generative models, not a novel mechanism for true 3D geometry.

The strongest reason this lacks novelty is that forcing spatial conditions into a latent sampling process and relying on the network to smooth the boundaries is fundamentally 2D inpainting/outpainting. You are observing correlated pixel harmonization—a documented feature of how self-attention resolves latent discontinuities—not the generation of independent scenes rooted in true multi-view geometry. The network is synthesizing plausible 2D textures to bridge a gap, oblivious to causal 3D depth.

This operational effect is extensively established. For example, RePaint: Inpainting using Denoising Diffusion Probabilistic Models (Lugmayr et al., 2022) demonstrates latent substitution during sampling to harmonize masked regions, while ControlNet (Zhang et al., 2023) proves that localized spatial conditioning permanently alters global image layout. Demonstrating these exact 2D harmonization mechanics using a warped prior validates the VAE's ability to smooth synthetic artifacts; it is a limitation of the decoder's spatial bleeding, not a breakthrough in geometry-guided video generation.
