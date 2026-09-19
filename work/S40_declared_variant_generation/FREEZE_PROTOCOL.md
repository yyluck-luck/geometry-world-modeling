# S40 实际生成 manifest 冻结与双审协议

此协议只把已经通过独立审查的 S39 实际加载链写入一个新的 S40 core，再附着两份针对该实际 core 的独立审查。它不加载模型、不读取 GB 权重正文、不解码图片，也不执行生成。

## 固定顺序

1. `prepare` 读取保持不变的 `manifest_candidate.json`，只从 S39 最终 manifest 复制五组件、配置和原始输入身份；把 S39 launch、worker、runtime loading、full resource gate 以及不同作者 loading evidence review 的实际路径和 SHA 写入新 core。
2. `prepare` 调用当前 `generation_gate.loading_chain` 验证整个 S39 链。创建任何 freeze 输出前，工具必须确认该输出与 S40 结果根和未来 `execution_01` 既不相等、也不存在上下级目录关系，并确认两个保留运行根都不存在；发布 core 和成功回执前再次检查。成功状态只能是 `S40_CORE_FROZEN_AWAITING_REAL_REVIEWS`。
3. 两名不同作者读取同一个实际 core。一份状态必须为 `PASS_S40_GENERATION_SOURCE_REVIEW`，另一份必须为 `READY_TO_ATTEMPT_S40_DECLARED_GENERATION`；两份均完整绑定 variant 与排除 `review_receipts` 后的规范 `core_sha256`。
4. `attach-reviews` 只接受 core 文件 SHA 和两份 review 文件 SHA。创建 attach 输出目录前，它先按 core 文件 SHA 读取外部 core，并要求其中 `output_root` 精确等于预注册 candidate 的唯一结果根；attach 函数内再次检查。它必须把 `freeze_preparation` 的完整固定键和值重新构造，并要求其中 candidate 身份、工具身份、零执行计数以及 S39 manifest、四份 loading evidence、loading review 与 core 顶层实际绑定逐项完全一致。它也要重新执行保留运行根隔离/新鲜检查，附着审查后调用 `generation_gate.check_manifest(..., metadata_only=True)`，并在写入最终 manifest 和成功回执前继续确认两个运行根未被占用；成功状态只能是 `S40_REVIEWS_ATTACHED_METADATA_GATE_PASSED`。
5. 生成入口必须使用 attach receipt 的实际 `manifest_path` 和 `manifest_sha256`。任何失败目录均保留，不能删除后伪装首次运行。

## SHA 含义

- `core_file_sha256` 是 `manifest_core.json` 的文件字节 SHA，传给 `attach-reviews --core-sha256`。
- `core_sha256` 是排除 `review_receipts` 后的规范 JSON SHA，写入两份 actual-core review。
- `manifest_sha256` 是附着两份 review 后最终 manifest 的文件 SHA，传给 metadata gate 和真实生成入口。

S40 仍是 `VMem + stabilityai/sd-vae-ft-mse` 声明组件变体；原 SD2.1 VAE 身份保持 `UNKNOWN`。即使 metadata gate 通过，也只允许一次受控两批 baseline 执行，不代表生成成功、视频质量、长期一致性或创新。
