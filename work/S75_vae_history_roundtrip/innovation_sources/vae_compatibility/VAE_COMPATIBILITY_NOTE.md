# ft-mse provenance and the limit of a VAE round trip

**Finding:** Official provenance supports preservation of the encoder's latent representation relative to the original kl-f8 family. It does not identify the exact SD2.1 VAE bytes or certify the actual VMem network's compatibility. No evidence here establishes that S70's framing failure is a VAE problem. S75 results were not read.

The [official model card at revision 31f26fdeee1355a5c34592e401dd41e45d25a493](https://huggingface.co/stabilityai/sd-vae-ft-mse/blob/31f26fdeee1355a5c34592e401dd41e45d25a493/README.md), lines 24–29, describes original kl-f8 → ft-EMA → ft-MSE, with only decoder fine-tuning to preserve compatibility. It describes OpenImages pretraining followed by LAION-Aesthetics/Humans, and an MSE-emphasized final reconstruction loss. The worked replacement example uses SD v1-4 (lines 13–21). This is a substantive intended-compatibility statement, not merely a matching tensor shape. It is a model-card declaration rather than an encoder-weight byte comparison.

| Claim | What the current evidence supports |
|---|---|
| Same latent convention | Original VMem source uses factor-8 compression, posterior mean × 0.18215, and division by 0.18215 before decoding. S70 retains that wrapper. Dimensions/scaling alone do not identify a latent basis. |
| Encoder retained; decoder adjusted | Official ft-mse training provenance supports this relative to its original kl-f8 ancestor. It weakens an arbitrary new-encoder-coordinate explanation. |
| Exact SD2.1 VAE identity | Unresolved. S70 explicitly records UNKNOWN. The official SD2.1 card returned 401; the old official repository README returned 404. No access request, credential use or community-mirror substitution followed. |
| Actual VMem denoiser compatibility | Plausible intended family compatibility is weaker than a verified SD2.1/VMem training-latent identity and successful consumer behavior. Loading with matching shapes does not prove this stronger claim. |

For byte identity, the relevant check would concern encoder-side parameter values and preprocessing/scaling against the exact autoencoder used by the consumer, not equality of whole checkpoint files: decoder changes are deliberate. File serialization can also differ without changing parameter values. This note neither requests a download nor requires repeating any successful component test.

A five-line symbolic counterexample to *round-trip alone*, not a claim about these weights:

1. Let E(x)=x and D(z)=z in two dimensions, with x=(1,0).
2. Let T swap coordinates; define E'=T E and D'=D T⁻¹.
3. Then D'(E'(x))=x exactly, retaining dimension and norm.
4. A fixed old generator G returning z=(1,0) instead produces D'(G)=(0,1).
5. If E'=E is established on the relevant latent image, this particular coordinate-remapping counterexample is excluded there.

Thus documented encoder preservation meaningfully narrows the generic counterexample; it must not be ignored to manufacture a compatibility worry. What remains unverified is the link to the exact SD2.1/VMem encoder and behavior on *generated* latents. Even a decoder that reconstructs historical encoded images well is not thereby verified on all denoiser outputs. Conversely, a poor loop could reflect input/scaling/implementation issues and would not uniquely implicate the decoder weights. A good S75 result would narrow gross reconstruction explanations for its five history latents; it would neither prove full network compatibility nor establish correct requested-camera response. No round-trip outcome is assumed here.

Actual source scope: pinned official text only, original local AutoEncoder source, and S70 input metadata. The card's image URLs were read as text but no linked image was fetched or viewed. The 6,844-byte README is preserved; no weights, RGB, latent arrays, model execution or S75 results were consumed. This is a bounded provenance/interpretation result, not a method proposal.
