# S46 C1 最薄真实 I/O wrapper 协议草案：V3仅适配V12相机结果

状态：`SOURCE_ONLY_UNBOUND_NOT_EXECUTABLE`  
接续作者角色：`/root/execution_resumption_audit`

原wrapper作者为`/root/c2_v5_lifecycle_review`，冻结数学scorer作者为`/root/c1_blind_score_builder`。历史V2由同一接续作者将V9状态名适配为V11。本次V3只另立目录、将未来独立相机复核的V11状态名适配为V12；当前作者身份、原目录、V2和数学源保持原样。两名wrapper作者与scorer作者均不能计作本包独立源码审查者。接续身份与原件SHA见`SOURCE_ONLY_PREPARATION_RECEIPT.json`。

V11真实运行没有取得监督终态PASS，旧失败保留。V12独立结果PASS在本包准备时尚未交付，本协议只是等待该结果的接口约定；它不宣称V12正式相机已通过，也不允许正式评分。

## 目的与边界

本目录只补齐 S46 第 4/6 节缺少的身份与 I/O 接口。wrapper 不重新实现评分数学；它只能加载 SHA-256 为 `ada2ba80...c3f1a` 的原封存 `score_c1_blind_candidate.py`，并调用其中的 `score_frames`。ROI、ID0/ID8 主比较、float64 除以 255、逐块累加、严格 `MSE > 0.01`、诊断配对和复制守卫全部保持在封存 kernel 中。

当前没有 `WRAPPER_EXECUTION_BINDING.json`，模板中的身份均为 `null`，因此本目录不能正式运行。源码准备和自检不得读取真实 C1 `.bin`，不得解码或查看图片，不得调用模型、readback 或正式评分。

## 正式入口必须同时满足的门

1. exact bound contract 必须由原 S46 identity-only binder 产生，保持 frozen-math canonical SHA `9bee0abe...2812`，绑定固定 attempt 01、八类上游 JSON、九个权威像素身份及固定 tensor 目录。
2. 七份已有 S44/S45 JSON 必须保持本 wrapper 内固定路径与 SHA；九个身份必须逐项等于 S45 independent result review，并验证每个只读 sidecar 的 `uint8[576,576,3]`、C order、995328 bytes 与 body SHA 元数据。
3. 未来 V12 数值相机门必须先有独立结果复核：schema `s45b-c1-numeric-camera-guard-independent-result-review-v1`、status `PASS_S45B_C1_NUMERIC_CAMERA_GUARD_INDEPENDENT_RESULT_REVIEW_V12`。它必须绑定真实 supervisor exit-0 terminal seal，声明 `requested_pose_K_guard_pass=true`、六个 row-validity assertion 全 true、零像素解码/零看图、空 blockers，并原样携带 S45 的九个像素身份。bound contract 的 `row_validity_review` 必须就是此文件。
4. 两位不同 reviewer 分别给 exact scorer、wrapper、bound contract 和 S42 protocol 出具既定 primary/adversarial PASS。scorer 作者、wrapper 作者和两位 reviewer 四个角色须互异；review 必须声明未执行、未读 C1 payload、未看图且 blockers 为空。
5. 两份 review 之后、正式 body 打开之前，root create-only 形成 `s46-c1-blindness-attestation-v1` / `PASS_S46_C1_BLINDNESS_PRE_SCORE`；四个盲态字段必须为 false，并精确绑定 scorer、contract、两份 review 和 attempt 01。
6. 最后创建 `WRAPPER_EXECUTION_BINDING.json`，精确绑定上述全部文件与 wrapper 自身 SHA。缺一项、SHA 不同、时间顺序错误或输出路径已存在，均在真实 body 打开前失败。

## 唯一 I/O 行为

所有元数据和 tensor body 都通过同一只读 FD 完成读取、SHA 与前后 `fstat` 身份核验。只有前述门全部通过，才会打开九个 exact `.bin`，由不可变 bytes 建立 C-contiguous NumPy 1.26.4 `uint8` 视图并一次调用封存 kernel。wrapper 不打开 PNG/PIL/montage。

正式 attempt 使用固定隐藏 staging 目录；成功写 create-only `report.json` 与 `receipt.json` 后才原子发布为既定 `C1_score_attempt_01`。数学或 body 失败只能留下 `technically_valid=false` 的终态 receipt，没有 report。任何终态 C1 仍只是一个 baseline 行，C2 继续强制，不能据此声称视觉质量、相机服从、方法增益或创新。

## 当前验证

`integration_selftest.py` 有两个入口：系统 Python 仅检查源码、真实 JSON 与九个真实 sidecar 元数据；项目 Python 另用临时合成 `.bin` 验证同 FD loader 与封存 kernel 的实际衔接。两者都检查正式 binding/output 不存在；真实 body 读取计数必须为 0。
