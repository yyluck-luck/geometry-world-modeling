# S66：S64 相机与固定评分的薄接线

本包只处理已完成的 `C2_UNIT_REPAIRED_S64` 保存结果。它是失败后另立的工程变体，保留 ft-mse VAE 与原 retrieval_variant；不补原 S42 cohort，不重跑模型，不看图，不新设指标。`measure.py` 固定实际 S64 manifest、outer、commit、postrun、不同作者结果复核、archive/event SHA；无未来结果 SHA 占位。

原来源均从核 SHA 的同一字节加载。相机仅 AST 抽取 V12 的选择、CameraTensorStore、解码和数学及必要纯 helper；主/独立评分加载原 `score_frames` / `recompute_frames`，不运行任何原 main 或大型 C1 wrapper。原数学未改。原 C1 row/status/cohort 字段不作为本报告结论；旧 `compare_math` 的 row_status 仅在内部按封存 event 恢复确定的兼容字符串，原精确比较保留。

## 三个独立 mode

| mode | 前提与正文范围 | 固定新输出 |
|---|---|---|
| `camera` | 已独立完成的 S64 工程链；两次 batch_input 和 cache_commit 的小 c2w/K 数组。原解码、finite/shape/SHA、`max_abs≤1e−6`、最终 cache ID0 锚、yaw、K、连续性与闭环全部保留。仅从最终 cache occurrence1 导出九帧元数据，0 RGB 正文。 | `camera_01` |
| `score` | root 已收到不同作者相机结果核验，再传该 review 路径/SHA；核 camera report/receipt 和相同九项身份。只读 ID0–8 的权威 uint8[576,576,3] 快照，九份共8,957,952 B。原 M_outer4/ID0–8、float64、严格 MSE>0.01、复制退化、区域/全图/三对诊断不变。 | `score_01` |
| `recompute` | 主评分已封存，传实际 score receipt/report SHA。只读其同九项权威像素；仅调用不同原数学实现和既有全 metric/floathex/分母/event 精确比较。差异保存并非零返回。 | `recompute_01` |

相机只能证明请求输入闭环，不能证明画面服从。主评分是该工程变体的探索性描述，不提供记忆原因、方法增益或创新结论。S64 postrun 之前已经读取 RGB 正文；本包不会伪造“像素未读”或恢复旧 cohort 盲态。原 ROI/配对/阈值均沿用，评分/复算结束及结果核验前不显示新图；全九帧导出由 root 另做。

## 实际调用与有限结果接口

现有 `.venv-cut3r/bin/python -B measure.py --mode <camera|score|recompute> --source-sha256 <本最终源码实际SHA>`。没有自动串联。每次固定 create-only 目录，任何既有目录使调用停止；失败保留目录/receipt/异常。内层110秒，root 外控不超过120秒并保存真实退出码。NumPy只在 score/recompute 按原1.26.4加载；camera不需要科学库。PASS receipt 必须与外部return0一起解释，不能将文件存在当执行成功。

score 另需 `--camera-review`、`--camera-review-sha256`。review使用有限实际字段：`schema=s66-camera-independent-result-review-v1`、`status=PASS_S66_CAMERA_INDEPENDENT_RESULT_REVIEW`、`row=C2_UNIT_REPAIRED_S64`、非本作者的 `reviewer_role`、`observed_returncode=0`、本最终 `source_sha256`、`camera_receipt`/`camera_report`各 `{path,sha256}`、`authoritative_pixel_identities`、空`blockers`。这些是实际结果核验接口，不是可预填 PASS 的模板。

recompute 另需 `--score-receipt-sha256`、`--score-report-sha256`。三个 mode 均输出 report/receipt 与真实文件/正文尝试记录。九帧表每项恰为 `id/blob(绝对路径)/tensor_descriptor_sha256/tensor_body_sha256`。相机分列初次实际读取字节与关闭时成功复核字节；失败的关闭复读量可未知，不填0。RGB snapshots逐份计数；失败时 attempted payload 可能只有部分字节，不能把未完成快照说成未读。

## 作者检查与未验证范围

`--compile-only` 只核冻结来源、纯定义和编译，不进入 mode。作者另核已允许的实际 JSON 元数据，并用一组人工矩阵调用原解码/数学接口；没有读实际相机或 RGB 正文，没有执行评分、复算、模型或正式 mode。第一次人工 DummyStore 将 shape 传为 tuple，原接口要求 list，检查失败已保留；只改人工 fixture 后同一小检查通过，生产源码/数学未因此放宽。`AUTHOR_CHECK.json` 绑定最终源码，`AUTHOR_CHECK_INITIAL_FAILURE.json` 保留失败。此自检是接线检查，不代替不同作者源审或之后实际结果核验；不重跑旧测试矩阵。
