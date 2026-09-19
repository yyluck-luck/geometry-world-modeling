# S76 sealed scorer invocation

Source-only verification at 2026-09-09T09:43:23.410398+00:00. Source SHA `5236e28c3c2ed15dceb538ee34b481d8cbe1a4eb751e5b121c9f00b68405c469` and contract SHA `7b0216596bd3c8859d5a0c3a864c47efa28c1c37b9fbf2beef3a50ee2de23d54` were freshly read. Worker/external SHA values below were supplied by root; this review did not inspect their scientific fields, images or score values. No program invocation, model load, rematching, or new-array read occurred.

Actual CLI is exactly three positional SHA arguments after the script: contract, generation receipt, external generation receipt. No output-path or timeout CLI flag exists. Keep the lexical venv interpreter path; cwd is the project root. Output is create-only `scoring_01`, so preserve any existing output and do not duplicate a run.

Exact argv for root's single externally bounded invocation:

```json
[
  "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/.venv-cut3r/bin/python",
  "-B",
  "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S76_relative_camera_response/score_single_yaw.py",
  "7b0216596bd3c8859d5a0c3a864c47efa28c1c37b9fbf2beef3a50ee2de23d54",
  "a9f2b46405a388dd5d589f4012e454a029b324e717a1006ccdddfae00de08ce2",
  "c165a7512c056652fd0e9e34b57afd1319ed45019fb4a51a4d98130819b1ea9e"
]
```

Root's outer subprocess must impose `timeout=60` seconds and record start/end, returncode or timeout, stdout/stderr and actual SHA. The internal55-second budget only runs at boundaries and does not interrupt native calls. Use the existing root wrapper; no extra model or repeated baseline process is needed. The generation verifier is currently handled by root: only after its actual acceptance should root execute this one scoring call.

Required input success: external `returncode=0`, `stop_reason=null`; worker `COMPLETE_SINGLE_YAW_FIXED_STREAM`, correct contract and `stream_identity_pass`, `model_unchanged`, `all4_targets_preserved`; old replay/shared stream also checked. Successful scorer status is `COMPLETE_SAVED_YAW_DIRECTION_DIAGNOSTIC`, returned0. Failure preserves `FAILED`, error and `unrun_target_ids`; an outer kill may leave partial outputs without a final receipt and must not be called complete.

Output contains four target rows20–23, fixed SIFT mutual matches, same-point identity-versus-H residuals, match availability, invalid/outside counts and all-four events with None precedence. Source and array identity gates execute before score computation. Runtime versions NumPy1.26.4/OpenCV4.11.0.86/Pillow10.3.0 are enforced by the scorer; this source review did not import them.

User-facing wording boundaries:

- New yaw images belong to the actual preceding model run. Scoring is saved-image matching/arithmetic, not another neural generation; these images are model-generated, not real photographs.
- A completed process or score does not establish camera compliance. Independent numerical verification and all-four visual inspection are still separate stages.
- All-valid and common-FOV are distinct reports. Missing support and None remain visible; same matched points define identity-H. Do not call the common-FOV subset whole-image truth or hide the hardest target.
- Any positive directional response concerns one already seen scene, one fixed image-grid random realization and four coupled targets under a full-system camera intervention. It is not absolute calibration, isolated-ray causality, exact homography/noise equivariance, significance, a new method or PhD/CCF-A validation.
- Preserve S73 UNKNOWN and NO_METHOD_SELECTED unless a separate justified research decision changes the applicable claim; this scorer does not do that.
