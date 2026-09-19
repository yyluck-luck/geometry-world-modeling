# S15 history-only runner interface

This is a new-source engineering preparation, not a completed real-data experiment. The implementation uses the existing pinned CUT3R linear 224 checkpoint and signed RoPE adapter. It does not choose calibration, decode target labels, query target cameras, train a model, or assess quality. For S15A the parent supplies twenty frozen native RGB images, with no guessed or repeated undistortion because Bonn image rectification status and optical GT c2w remain unresolved. Sampling/provenance belong to the parent preparation protocol; `load_images(..., size=224)` performs the official normalization, resize, and crop once.

## Invocation and required contract

```
.venv-cut3r/bin/python scripts/run_s15_history.py --manifest /absolute/manifest.json --output /absolute/new-output-directory
```

Invoke through a reviewed external caller that enforces 600 seconds and 32 GiB monitored RSS. The runner has completion gates and records its process peak RSS; these do not substitute for the caller's live termination limit. Output directory must not exist; failures and their partial outputs are retained.

Manifest top-level fields:

- `schema`: `s15-history-manifest-v1`
- `repo`: canonical absolute CUT3R checkout path.
- `commit`: `8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf`.
- `python`: absolute venv Python executable path (symlink allowed, compared using realpath).
- `runner`, `checkpoint`, `rope_check`: canonical absolute frozen files.
- `history_images`: exactly twenty ordered entries `{ "index": 0, "path": "/absolute/rgb.png", "sha256": "64 lower-case hex" }`, indices 0 through 19, no duplicate paths.
- `control_files`: optional distinct absolute frozen MD/JSON/Python control files. They may name dataset provenance in text, but must not contain target image or depth arrays. The runner hashes these controls and never decodes them.
- `identities`: exact canonical-path-to-SHA256 mapping for the twenty RGB inputs, checkpoint, signed RoPE check, `scripts/cut3r_rope_compat.py`, runner, 99 upstream Python source files under `repo`, and optional `control_files`. No other files are accepted. In particular no target RGB, depth, NPZ, NPY, `groundtruth.txt`, `rgb.txt`, or `depth.txt` belong here.
- `contract` exactly matches the following values (additional descriptive contract fields are permitted):

```json
{
  "history_count": 20,
  "query_count": 0,
  "history_flags": {"img_mask": true, "ray_mask": false, "update": true, "reset": false},
  "device": "cpu", "cpu_threads": 8, "seed": 0,
  "size": [224, 224], "dtype": "float32",
  "wall_seconds": 600, "monitored_rss_bytes": 34359738368,
  "external_monitor_required": true,
  "history_rgb_allowed": true,
  "target_rgb_allowed": false,
  "target_depth_allowed": false
}
```

The only accepted checkpoint SHA256 is `7a7d83e47f822e040980c8f5aff4c15aa94366d469d3ceae51fa30cc2f62327d`. Model construction follows the established weights-only loader and scoped OmegaConf safe globals. It checks every checkpoint key, pinned architecture, clean tracked upstream source, and signed adapter identity. All frozen inputs and sources are hashed both before and after execution. Imported upstream modules must occur in the 99-file freeze; their actual file paths and hashes are recorded. No actual new-source model or weight arrays were read during runner preparation.

## Actual history behavior

The exact twenty allowed paths are decoded in manifest order through a guarded `PIL.Image.open`. Any extra image read fails, including an attempted second decode of a history. The original input dimensions/mode and normalized tensors' fixed 224 dimensions are checked/recorded. History views have dummy identity camera poses, NaN channel-last ray maps `[1,224,224,6]`, and fixed masks above. Those ray maps carry no camera information and are unselected.

One official `inference(views, model, 'cpu')` call processes all twenty histories and returns twenty predictions plus twenty-one latent snapshots (initial + twenty updates). The model's official `_encode_views` has an internal fallback: when all ray masks are false, it evaluates **one zero dummy ray map and multiplies its encoded contribution by zero** (`src/dust3r/model.py`, fallback after `selected_ray_maps`). Thus the fixed hook gates are one image-encoder call containing twenty frames and one internal dummy ray-encoder call. Neither is a target query. Reporting zero ray-encoder calls here would be incorrect.

## Outputs and downstream binding

`run_metadata.json` has schema `s15-history-run-v1`, `status` `SUCCESS` or `FAILED`, UTC start/update/completion times, phase, error/traceback on failure, exact input order/read counters, versions, loaded source identities, wall/peak RSS, encoder/call counts, and output file SHA256. `video_generated`, `new_model_trained`, and `accuracy_evaluated` are false. Its `state_final` is the five-field identity mapping consumed by the next stage, and `history_output_ids`/`history_pose_ids` record shape/dtype/contiguous-byte SHA256.

`predictions.npz` contains 120 arrays: prefix `frame0_` through `frame19_` plus each of these six official keys:

| Key suffix | Shape | Dtype |
|---|---|---|
| `pts3d_in_self_view` | 1×224×224×3 | float32 |
| `pts3d_in_other_view` | 1×224×224×3 | float32 |
| `conf_self` | 1×224×224 | float32 |
| `conf` | 1×224×224 | float32 |
| `camera_pose` | 1×7 | float32 |
| `rgb` | 1×224×224×3 | float32 |

These are untouched official outputs. The `rgb` tensor is model output, not a newly opened target photo. Both complete xyz point maps are retained; no depth-only truncation, confidence filtering, world alignment, point cleaning, or unit conversion occurs.

`history_poses.npz` has exactly `history_pose_encodings` (20×7 float32) and `history_poses` (20×4×4 float32). The latter comes from official `pose_encoding_to_camera`. All outputs must be finite; c2w bottom rows are exact and proper rotations use fixed absolute tolerance 1e-4, relative tolerance zero.

`state.npz` contains exactly:

| Field | Shape | Dtype |
|---|---|---|
| `state_feat` | 1×768×768 | float32 |
| `state_pos` | 1×768×2 | int64 |
| `init_state_feat` | 1×768×768 | float32 |
| `mem` | 1×256×1536 | float32 |
| `init_mem` | 1×256×1536 | float32 |

Raw prediction and final-state arrays are persisted before finite/semantic gates, so a returned but invalid model result remains reviewable. Other payloads are `frozen_manifest.json`, `source_snapshot.py`, `checkpoint_load.txt`. File hashes exclude the mutable metadata itself; the parent must seal that file and all successful payloads before downstream conditioning/query work.

The new query stage must bind to **this** successful history metadata and `state_final`/file hashes, rather than requiring an S14D schema. It must use a newly specified same-segment parity control (e.g. two identical frozen first queries from the same restored state) and require byte-exact six-output parity plus five-state immutability before relying on new queries. This runner deliberately makes zero queries and therefore supplies no old-query parity reference. It must never reuse a previous scene's state or require numerical equality to S14D.

## Skill application and preparation evidence

Applied Supervisor `vibe-research-workflow` coding procedure: freeze explicit scope and schema, use official code, implement a bounded stage, preserve failures, and request another author's review before real execution. Applied local Claude `sci-scientific-critical-thinking` to distinguish artificial code checks from actual inference and prevent leaking target answers into inputs. No Claude model or CLI was called. User private understanding, code review, course/venue obligations, and actual experimental effectiveness are not inferred from these checks.

Artificial checks and actual preparation timestamps are in `work/S15_history_preparation/receipt.json`; they do not count as real photos or model evaluations. For S15A the parent must finish native-RGB sample identity, history-only protocol freeze, and independent source review before running this program. Known-camera geometry and depth scoring require a later separately validated calibration protocol; they are not prerequisites for this bounded RGB history run.
