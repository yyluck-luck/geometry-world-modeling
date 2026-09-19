# A camera-only response control before another reconstruction comparison

Status: NO_METHOD_SELECTED. This is a prospective classical-geometry diagnostic, not an adopted experiment or a novelty claim. Source-only scope; no S74 result, tensor, image, weight, or model was read or run.

## Closest new primary evidence

**CamVerse, “Taming Camera-Controlled Video Generation with Verifiable Geometry Reward”**, Zhaoqing Wang et al., arXiv:2512.02870v1 (2 December 2025). Figure 1 explicitly compares the same first frame and prompt under different camera paths. Section 3.2 instead evaluates reconstructed trajectories: it similarity-aligns poses, scores relative segment motion, and masks low-confidence segments. This avoids equating RGB reconstruction error with camera error, but retains estimator/appearance dependence and a changing retained population. Its illustrated pairing does not establish common actual noise. Formal conference acceptance was not verified. [Primary text](https://arxiv.org/html/2512.02870v1).

**Time-to-Move: Training-Free Motion Controlled Video Generation via Dual-Clock Denoising**, Assaf Singer, Noam Rotstein, Amir Mann, Ron Kimmel, Or Litany, arXiv:2511.08633v1 (9 November 2025); the author project states ICLR 2026 acceptance. Section 4.2 compares a raw warped-video baseline and generation approaches with the same warp construction; it reports optical-flow error separately from image alignment and appearance metrics. Section 4.1 additionally measures background–object relative motion to expose a wrong source of apparent motion. Flow still depends on correspondence and does not uniquely establish physical camera motion. [Primary text](https://arxiv.org/html/2511.08633v1), [author project](https://time-to-move.github.io/).

The local control below is my proposed inference from these separation principles, not a control claimed in either paper. Neither source licenses calling an ordinary homography check a new mechanism.

## Most discriminating local next control

Freeze one paired **A / rotated-A** comparison before any new generation. Keep the ordered histories [19,18,13,12], all cached appearance tensors, context cameras, target centers, intrinsics, target order 20–23 and all sampling settings fixed. Change only each target's optical-camera orientation by the same predeclared local yaw, e.g. +5 degrees; no angle sweep or scene selection. Rebuild the two complete conditions through the original S69 helpers, including the original scale and ray path. Check the naturally computed scale and non-camera fields rather than overriding them. MultiviewCFG also consumes cameras: its original behavior must remain declared, so this measures the full camera-conditioned system, not the ray module in isolation.

Use the successful S70 CPU8 FP32, ft-mse VAE, full eight-slot decode, 50-step sampler-0 protocol. Restore the same actual initial noise and Python/NumPy/Torch RNG states, and verify the per-step stream. A fresh baseline replay plus one rotated arm is a bounded two-arm test, approximately 50 minutes from the earlier per-arm duration; it is not authorized by this source note. Preserve every failure/output. If using old A0 instead, its exact executable/input/RNG binding must support an actual replay check; seed44 alone does not suffice.

For optical c2w rotations R and R' with unchanged center, the predicted image map is H = K R'^T R K^-1. This relation is independent of scene depth for a static perspective scene. Compare generated A to generated rotated-A using the same accepted correspondences for fixed H and identity; do not fit a replacement homography. Report availability, spatial support and residual distributions for all four targets, including empty/low-support cases. Record the known H displacement over a fixed image grid so an almost-identity intervention is visible before matching. Camera conventions and this image-map direction must be source-checked before adoption.

## Competing explanations and falsifiers

| Observation | Supported or rejected interpretation | Remaining limit |
|---|---|---|
| Byte-identical outputs despite nonidentity H, with valid replay/RNG | Rejects a response to this camera intervention | Does not locate the ignored or saturated component |
| H has smaller median residual than identity on all four fixed match sets | Supports directional response; rejects the simplest camera-ignored explanation | Not exact angular accuracy, absolute calibration, scene identity or image quality |
| Any target has nonpositive median(identity residual minus H residual) | Rejects the predefined all-four directional-response event | Wrong correspondences or regenerated content can explain failure |
| Missing/unusable support on any target | All-four event UNKNOWN; retain that target | Survivor-only medians cannot settle the camera question |

Zero is the proposed sign boundary, not a calibrated accuracy threshold. Publish residual magnitudes as well as signs; being closer to H than identity does not certify the requested angle. A model can respond correctly to relative rotation while retaining an absolute framing bias. Conversely, appearance/scene reconstruction drift can break the relation even with a responsive camera pathway. This deliberately narrower intervention complements the current wrong-label observer control: it changes the actual conditioning and avoids requiring a new fitted 3D reconstruction. It does not solve the S70 cause by itself, certify a new method, or replace real-reference evaluation.
