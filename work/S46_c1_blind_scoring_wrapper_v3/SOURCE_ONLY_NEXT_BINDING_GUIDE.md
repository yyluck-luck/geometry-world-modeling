# S46 V3 下一绑定接口说明（source-only）

记录UTC：2026-09-08T15:08:28.176659+00:00。作者：`/root/execution_resumption_audit`（wrapper作者，不能独立审本包）；历史wrapper作者`/root/c2_v5_lifecycle_review`、scorer作者`/root/c1_blind_score_builder`均须排除于wrapper独立源审。

**当前只交付说明，没有执行以下命令。V12的actual result review PASS交付前，不创建upstream identity binding或bound contract。** V12源码/绑定审查PASS、worker exit0、磁盘pending候选均不满足这个前置。该指南是冻结包旁追加的文档，不改四源、冻结清单或作者回执，也不提供新授权。

项目根目录：`/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling`。下面第一列为原binder标签；路径和SHA来自冻结wrapper的`FIXED_UPSTREAM`（行40–78）。

| 标签 | 实际JSON路径 | 固定SHA-256 |
|---|---|---|
| `generation_manifest` | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S44_c1_confirmation_generation/review_attachment_01/manifest.json` | `1e86e8279c608995a03d6675a8636c354d6d4d046b7c8faea9611d6e6a9fd93b` |
| `generation_terminal_receipt` | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S44_c1_confirmation_generation/execution_01/receipt.json` | `44753718ca666d134ac9500ffcd6ada6b0e7e4e6ce6cbfc3bfa9f50de85dcb18` |
| `generation_worker_receipt` | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S44_c1_confirmation_generation/execution_01/worker_receipt.json` | `5deea6956876f03d7b36ed6ab57f608f9613da79e133921d3ead0865196b18f0` |
| `readback_supervisor_receipt` | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S45_c1_result_readback/supervision_01/receipt.json` | `801798bd89f9ffc06025652e1af4abeb533a9bcda503cdfb80857824a353d611` |
| `readback_worker_receipt` | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S45_c1_result_readback/executed_01/receipt.json` | `54b457212fc0128c3fe8c59d9549d7b2f25e26bc8e5778ca38edae868c8201a1` |
| `readback_report` | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S45_c1_result_readback/executed_01/report.json` | `423e5fb85ea092ba613ff71d28671f89f7df365eb29be8ca1c8f9a950662df47` |
| `readback_result_review` | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S45_c1_result_readback/supervision_01/independent_result_review.json` | `2b5e4bc3dcf28f60b320ae4d3af2b4949b60a526cacc62b2deacd87ac6ddad4c` |
| `row_validity_review` | V12实际完成后，独立审查者最终交付的结果review路径；当前不指定虚构文件 | 该最终review的实际整文件SHA |

**九身份来源。** 从上表`readback_result_review`的`/authoritative_pixel_identities`原样拷贝，不从图像或相机数组重建。它是按ID0–8排序的9项，每项恰好四键：`id`、`tensor_descriptor_sha256`、`tensor_body_sha256`、`blob`。当前已读取该review的身份元数据并核固定SHA，列表canonical JSON SHA为`cc976f12e937828a7af1d39ce1b69a722efe6a18be68dc6d05a607d7334ad8e0`。所有`blob`都在`results/S44_C1_confirmation_generation/archive/tensors`，文件名为`<tensor_descriptor_sha256>.bin`；本说明没有打开这些body。V12独立review与bound contract必须携带同一个列表。

**V12独立结果review：wrapper直接读取的字段。** 以下是现有接口，不是可直接填true的结论模板。独立审查者须依据真实外部退出、完整终态与既有证据链逐项得出，并记录对应实际证据的路径/SHA；缺证据时不能给PASS。

| JSON字段/指针 | 必需值 |
|---|---|
| `/schema` | `s45b-c1-numeric-camera-guard-independent-result-review-v1` |
| `/status` | `PASS_S45B_C1_NUMERIC_CAMERA_GUARD_INDEPENDENT_RESULT_REVIEW_V12` |
| `/row`, `/passed`, `/requested_pose_K_guard_pass` | `C1`, `true`, `true` |
| `/numeric_guard_terminal_schema` | `s45b-c1-numeric-camera-guard-terminal-pass-seal-v4` |
| `/numeric_guard_terminal_status` | `PASS_C1_REQUESTED_CAMERA_INPUT_CONDITION_GUARD_ONLY` |
| `/numeric_guard_terminal_authority`, `/observed_supervisor_returncode` | `true`, `0`，须来自实际外部终态 |
| `/pixels_decoded`, `/images_viewed`, `/blocking_findings` | `0`, `0`, `[]` |
| `/completed_utc` | 实际完成UTC，带时区且偏移为0，早于评分 |
| `/authoritative_pixel_identities` | 上述S45原样九项列表 |
| `/row_validity_assertions` | 下列六项全部有证据为`true` |

```text
generation_first_technically_valid_attempt
readback_independently_reviewed
cache_readback_guard_pass
requested_pose_K_guard_pass
all_nine_authoritative_pixels_identified
no_visual_QA_before_machine_score
```

**结果PASS后生成binder输入。** 可选用尚不存在的`work/S46_c1_blind_scoring_preparation/C1_UPSTREAM_IDENTITY_BINDING.json`，create-only；无需发明新版本。顶层按现有`bind_score`读取以下字段：

- `schema=s46-c1-upstream-identity-binding-v1`，`status=READY_TO_BIND_C1_IDENTITIES_AFTER_INDEPENDENT_READBACK`，`row=C1`，`completed_utc=实际UTC`。
- `upstream_records`恰好上述8项；每项仅`label,path,sha256,expected_json_fields`四键。前7项`expected_json_fields`须逐字取wrapper `FIXED_UPSTREAM[label]["fields"]`，不要把旧pending字段擅改为新PASS。第8项绑定真正V12结果review，以`/schema`、`/status`、`/row`及上述布尔/整数标量指针声明预期；六assertions可用`/row_validity_assertions/<名称>`。不得把整列表放进`expected_json_fields`，那里只允许标量。
- `authorized_attempt=1`，`authorized_output_path=/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S46_c1_blind_scoring_preparation/C1_score_attempt_01`。
- `authoritative_pixel_identities=原样九项`，`archive_tensor_directory=/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S44_C1_confirmation_generation/archive/tensors`。
- `pixel_identity_source_record_label=row_validity_review`，`pixel_identities_json_pointer=/authoritative_pixel_identities`，`row_validity_assertions_json_pointer=/row_validity_assertions`。

binder只读取输入JSON和已封存模板，**不会读取/核实其引用的结果JSON**；PASS前置必须先由实际独立结果审查满足。不要向输入加入MSE/PSNR/图像内容或浮点量。输出只能是`work/S46_c1_blind_scoring_preparation`下尚不存在的直接子文件。以下命令是现有CLI，当前不执行：

```sh
cd "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling"
/opt/homebrew/opt/python@3.13/bin/python3.13 -I -B -S \
  work/S46_c1_blind_scoring_preparation/bind_identity_only.py \
  --kind score \
  --binding "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S46_c1_blind_scoring_preparation/C1_UPSTREAM_IDENTITY_BINDING.json" \
  --out "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S46_c1_blind_scoring_preparation/C1_SCORING_BOUND_CONTRACT.json"
```

**随后沿用现有评分前流程。** 新bound contract仅是候选，仍须两名不同非作者对exact scorer、V3 wrapper、contract、S42 protocol给出既有primary/adversarial PASS；四角色检查不变。之后创建既有真实盲态attestation，四项字段保持实际false且时间晚于两review。最后由V3模板create-only生成`WRAPPER_EXECUTION_BINDING.json`：顶层schema改为`s46-c1-blind-scoring-wrapper-execution-binding-v1`，status改为`BOUND_C1_BLIND_SCORING_WRAPPER_EXECUTION_AWAITING_EXACT_GATE_VALIDATION`；填实际UTC及所有`path/sha256`，`numeric_guard_independent_review`必须与contract的`row_validity_review`同文件同SHA；其余键不增删。

正式执行使用V3 wrapper，scorer CLI本身仅提供合成自检，不能直接正式评分。**以下命令仅在上述既有门全部满足、唯一attempt和staging均不存在时执行一次；本任务未执行。** `s46_binding_sha`必须由root设置为已封存binding的实际64位SHA。

```sh
cd "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling"
: "${s46_binding_sha:?Set the actual frozen wrapper binding SHA first}"
.venv-cut3r/bin/python -I -B \
  work/S46_c1_blind_scoring_wrapper_v3/score_c1_blind_wrapper.py \
  --binding-sha256 "$s46_binding_sha" \
  --wrapper-sha256 3c8f931da47403cd5b249a6680790107136ffea0267f871679e77e7b27150463
```

正式环境使用NumPy1.26.4，不能加`-S`隐藏项目site-packages。输出仍唯一为`C1_score_attempt_01/report.json`和`receipt.json`；wrapper通过同FD读取9个body并一次调用原封存kernel，source SHA`ada2ba80eceebe83a514fd929c6cc82b69669e6525e261ff4729064f2bac3f1a`，数学SHA`9bee0abe9392e04e061adb7cf8b39297d7730e7045ed856486f1e03ee8d82812`。C1即使技术有效仍只是一行基线，C2继续必需，不构成新方法收益。
