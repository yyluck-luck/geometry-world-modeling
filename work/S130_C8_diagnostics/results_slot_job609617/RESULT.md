# C8 Experiment 1 result — slot-0 factor separation (job 609617)

Scope: development panel, scene_13 window 0, targets 60/75/90/105, one frozen consumer, RGB PSNR.
Not a method validation. `new_method_validated=false`, `novelty_authorization=NONE`.

## Harness gate: PASS
Convention N at seed 42 reproduced S107 orderings o0/o3 byte-for-byte (SHA-256 of all four
`*_target_rgb_fp32.npy` identical to job 594733) and the scorer returned identical PSNR.

## Primary result (seed 42, preregistered threshold 0.15 dB)

| convention | M1 {55,55,40,40} delta B-A | M2 {50,50,45,45} delta B-A | both below 0.15 |
|---|---|---|---|
| N native | +0.5519 | -0.7837 | no |
| R reference fixed | +0.0504 | -0.5397 | no |
| S scale fixed | +0.3028 | -0.7823 | no |
| RS both fixed | -0.0093 | -0.0161 | **yes** |

Preregistered verdict: **REFERENCE_SCALE_INTERACTION** — neither fixing the ray reference nor
fixing the translation scale alone removes the slot-0 effect; fixing both removes it.
Preregistered action: use RS as the canonical control in every later context/order comparison.

## Secondary (seed 7, report-only)

| convention | M1 delta | M2 delta |
|---|---|---|
| N | -0.3467 | +0.0393 |
| R | -0.3797 | +0.0480 |
| S | -0.5300 | +0.1245 |
| RS | -0.0233 | -0.0142 |

## Reading (bounded to this panel)

1. With reference and scale fixed, swapping which frame occupies slot 0 changes PSNR by at most
   0.023 dB in all four multiset x seed cells. Together with the earlier zero-GPU finding that
   reordering slots 1-3 changes PSNR by about zero, the consumer is effectively order-insensitive
   once the coordinate convention is fixed.
2. The native slot-0 effect is **not a stable directional effect**: it flips sign between seeds
   (M1: +0.55 at seed 42, -0.35 at seed 7; M2: -0.78 at seed 42, +0.04 at seed 7). The previously
   reported "0.55 / 0.87 dB slot-0 effect" was a single-seed measurement of a coordinate-frame
   perturbation, not a property of how the generator weights the first image.
3. Seed variation is large relative to many reported contrasts: the same arm (M1, order A, N)
   scores 16.42 dB at seed 42 and 17.94 dB at seed 7. Earlier single-seed comparisons on this
   harness (including the S106 position arms behind the "5.6 dB" figure) must be read with this in
   mind. Byte-identical replay controls replay noise only, not seed-to-seed variation.
