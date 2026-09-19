# S39 冻结与加载接续：独立准备审计

审计时点：2026-09-07T05:51:24.092985+00:00（Asia/Shanghai：2026-09-07T13:51:24.093954+08:00）  
审查者：`/root/vmem_recovery_diagnosis`

## 结论

**READY_SERIAL_PLAYBOOK_BLOCKED_ON_ATTEMPT4_TERMINAL_SUCCESS**。

源码接续链当前没有旧 SHA 冲突；冻结脚本、gate、loader、draft 和两份既有源码前审都仍绑定当前文件。但是 attempt4 的实际回执仍是 `RUNNING`，正式目标文件在本审计时点尚不存在，所以现在不能执行 freeze、attach 或 loading。

如果 attempt4 最终通过完整大小、完整 SHA、文件稳定性和进程组清理门，**应直接把它的 verified target 绝对路径作为 `freeze_manifest.py prepare --vmem` 的值**：

`/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/data/vmem_recovery/xet_attempt4_01/vmem_weights.pth`

S39 gate 只要求绝对路径、固定大小、固定完整 SHA 和冻结前后未改变，不要求文件位于 `data/vmem_original/`。不需要、也不建议为了 S39 复制到 canonical：复制会新增一个约 5.06 GB 的同内容副本和第二个可混淆身份，却不增加任何验收强度。attempt4 协议本来也明确隔离 canonical。后续全部步骤都使用实际 receipt 给出的 recovery 路径。

本审计只读了源码、协议、JSON 回执和文件元数据；没有运行下载、freeze、attach、gate、模型加载或生成，没有读取任何权重正文，也没有修改研究主账。

## 当前绑定与状态

| 文件 | 当前 SHA-256 | 判断 |
|---|---|---|
| `work/S39_component_variant/freeze_manifest.py` | `e7c03af60ed4d50bd5a9a1fb40f12df360f390a7a7fce1fe6f907f74bd8fb6b1` | 与 freeze 独立源码审查一致 |
| `work/S39_component_variant/FREEZE_PROTOCOL_DRAFT.md` | `ca421b4bfe5cca5c89d0bf518a3ebf21cbff8e5303cccf3150f12c2fd874a9bf` | 与 freeze 独立源码审查一致 |
| `work/S39_component_variant/s39_variant_gate.py` | `cf667bdc0bc43f902d0dca3041c4dbf33a53d908ee4e5d13ebfba2f853a78f4e` | 与脚本 pin、S39/S40 review 一致 |
| `work/S39_component_variant/load_components.py` | `7b554276d5f00e6f14283a0c3a3d06bccda73b3c9dd2b6a9ef2514287732738e` | 与 S39 source review 和 S40 pin 一致 |
| `work/S39_component_variant/PROTOCOL_DRAFT.md` | `263f1f58b50291f567fb3dce706c1b58bd931fcb26c444aece16c3645f245cea` | 与 S39 source review 一致 |
| `work/S39_component_variant/manifest_draft.json` | `21443f4b2fdd7c91e166c55a6ed2855d397ae5ba71b49da4d7d417d443ff6ee2` | 与 freeze 脚本 pin 一致；仍是 DRAFT |
| `work/S41_vmem_xet_attempt4/download_attempt4.py` | `a708d23cc0b64c8b3f5a23d427a6414a12fe1e1fb935beb8726b3e698102aa15` | 与 attempt4 独立审查一致 |
| `work/S41_vmem_xet_attempt4/PROTOCOL.md` | `ba6b7befbbb4c0c4f94d958cd832c4b73d39cdc18de1a87badf10f431d2ddbea` | 与 attempt4 独立审查一致 |

已齐的伴随组件：

- CLIP：`data/clip_original/open_clip_model.safetensors`，3,944,517,836 bytes，完整 SHA `0084e75319a50ad85ef45377bad5bc38f2f58824459eb690048d51c9f8863be5`；
- VAE 目录：`data/vae_official_ft_mse/`，只有固定的 `config.json` 与 `diffusion_pytorch_model.safetensors`；
- CUT3R：`data/cut3r/cut3r_512_dpt_4_64.pth`，3,173,761,006 bytes；
- `companion_download_receipt.json` 状态为 `ALL_COMPANIONS_VERIFIED`。

以下新路径在审计时均不存在，满足“一次新鲜执行”的前提：`freeze_attempt_01`、`review_attachment_01`、`metadata_check_01.json`、`loading_attempt_01` 和 `results/S39_declared_ft_mse_component_loading`。canonical VMem 也不存在。

## 精确串行步骤

### 0. 先等 attempt4 真正终态，不从 `RUNNING` 推断成功

只接续同一次 attempt4；不重启、不另开下载。终态 receipt 必须同时满足：

- `status == VERIFIED_COMPLETE_ORIGINAL_WEIGHT`；
- `download_exit_code == 0`；
- `target` 等于上述 recovery 绝对路径；
- `actual_bytes == expected_bytes == 5056346672`；
- `actual_sha256 == expected_sha256 == 675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4`；
- `file_stable_during_hash == true`；
- `child_still_alive == false` 且 `group_still_alive == false`；
- receipt 中的 source/protocol 身份仍对应本报告表内的双 SHA。

终态后先记录两个不同概念的 SHA：

1. 权重内容 SHA：固定为 `675dc486...fcb7fe4`；
2. **终态 receipt 文件 SHA**：在终态原子写入后动态计算。当前 `RUNNING` receipt SHA `7b9128d7...2468` 只是本次审计快照，终态必然会变化，禁止把它写入后续冻结批准。

任何非上述成功状态都停止本链；保留失败，不执行 prepare。

### 1. 使用 verified recovery 文件直接 prepare

只有步骤 0 全通过后执行一次：

```sh
S39_ROOT='/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling'
S39_TOOL="$S39_ROOT/work/S39_component_variant/freeze_manifest.py"
S39_VMEM="$S39_ROOT/data/vmem_recovery/xet_attempt4_01/vmem_weights.pth"
S39_CLIP="$S39_ROOT/data/clip_original/open_clip_model.safetensors"
S39_VAE_DIR="$S39_ROOT/data/vae_official_ft_mse"

python3 -B "$S39_TOOL" prepare \
  --vmem "$S39_VMEM" \
  --clip "$S39_CLIP" \
  --vae-directory "$S39_VAE_DIR" \
  --out "$S39_ROOT/work/S39_component_variant/freeze_attempt_01"
```

执行前再次要求：五个组件和所有小来源存在；固定 `results/S39_declared_ft_mse_component_loading` 仍不存在；`freeze_attempt_01` 不存在；表内源码 SHA 未变。prepare 会完整读取并重新 SHA 五个组件，这是冻结验收，不是模型加载。

成功 receipt 必须为 `CORE_FROZEN_AWAITING_REAL_REVIEWS`。从该 receipt 取得并分清：

- `core_path`：实际 `manifest_core.json`；
- `core_file_sha256`：**manifest_core.json 文件字节 SHA**；
- `core_sha256`：排除 `review_receipts` 后的规范 JSON SHA；
- `content_hashes_sha256`：逐文件完整读取审计账的文件 SHA。

prepare 失败会先留下独占目录和前缀证据；不能复用或删除该目录重跑，应改用 `freeze_attempt_02` 并重新审查实际失败原因。

### 2. 两名不同作者审查同一个实际 core

prepare 作者或执行者不能自己代签。安排两名相互不同的审查者，二者都必须读取同一个 `core_path`、prepare receipt、`content_hashes.jsonl`、freeze tool/protocol 和实际终态 attempt4 receipt：

1. **源码/core 审查**：新建 JSON，`status=PASS_S39_SOURCE_REVIEW`；
2. **运行冻结审查**：另一作者新建 JSON，`status=READY_TO_ATTEMPT_DECLARED_VARIANT_LOADING`。

两份 JSON 都必须含：完整 `variant` 对象、步骤 1 的动态 `core_sha256`、审查者身份、实际 core 文件 SHA、审查范围和未运行模型边界。现有 `independent_review.json` 与 `freeze_independent_source_review.json` 可作源码历史依据，但不能原样使用，原因见“阻断与旧状态”一节。

两份 review 写完后分别计算其**文件 SHA**；这是 attach 命令的第二组动态 SHA。

### 3. attach 两份真实 review，生成最终 manifest

变量含义必须按下面对应，不可把两个 core SHA 交换：

```sh
S39_CORE="$S39_ROOT/work/S39_component_variant/freeze_attempt_01/manifest_core.json"
S39_CORE_FILE_SHA='<prepare receipt.core_file_sha256>'
S39_CORE_CANONICAL_SHA='<prepare receipt.core_sha256；写进两份review JSON，不传给--core-sha256>'
S39_SOURCE_REVIEW='<实际源码/core审查JSON绝对路径>'
S39_SOURCE_REVIEW_FILE_SHA='<该JSON文件实际SHA>'
S39_RUNTIME_REVIEW='<实际运行冻结审查JSON绝对路径>'
S39_RUNTIME_REVIEW_FILE_SHA='<该JSON文件实际SHA>'

python3 -B "$S39_TOOL" attach-reviews \
  --core "$S39_CORE" \
  --core-sha256 "$S39_CORE_FILE_SHA" \
  --source-review "$S39_SOURCE_REVIEW" \
  --source-review-sha256 "$S39_SOURCE_REVIEW_FILE_SHA" \
  --runtime-freeze "$S39_RUNTIME_REVIEW" \
  --runtime-freeze-sha256 "$S39_RUNTIME_REVIEW_FILE_SHA" \
  --out "$S39_ROOT/work/S39_component_variant/review_attachment_01"
```

成功 receipt 必须为 `REVIEWS_ATTACHED_METADATA_GATE_PASSED`。从它动态取得：

- `manifest_path`：实际最终 manifest 路径；
- `manifest_sha256`：最终 manifest 文件 SHA，供 gate/loader 使用；
- `core_sha256`：应仍等于步骤 1 的规范 core SHA。

attach 失败也不能复用原输出目录；用新目录并保留失败证据。

### 4. 用实际 manifest 路径做便宜的 metadata 门

`attach-reviews` 已内置一次 metadata gate，loader 父进程还会再做一次。为严格沿用现有 `PROTOCOL_DRAFT.md`，可在真正加载前留下独立、便宜的即时回执；它不读取 GB 权重正文：

```sh
S39_MANIFEST='<attach receipt.manifest_path>'
S39_MANIFEST_FILE_SHA='<attach receipt.manifest_sha256>'

"$S39_ROOT/.venv-cut3r/bin/python" -B \
  "$S39_ROOT/work/S39_component_variant/s39_variant_gate.py" \
  --manifest "$S39_MANIFEST" \
  --manifest-sha256 "$S39_MANIFEST_FILE_SHA" \
  --metadata-only \
  --receipt "$S39_ROOT/work/S39_component_variant/metadata_check_01.json"
```

要求 `PASS_METADATA_ONLY`。失败则不加载。这个单独命令是即时证据，不是跨进程授权令牌；loader 仍会自己复核。

### 5. 一次有界 S39 实际加载

再次确认以下路径都不存在：

- `work/S39_component_variant/loading_attempt_01`；
- `results/S39_declared_ft_mse_component_loading`。

然后执行一次：

```sh
"$S39_ROOT/.venv-cut3r/bin/python" -B \
  "$S39_ROOT/work/S39_component_variant/load_components.py" \
  --manifest "$S39_MANIFEST" \
  --manifest-sha256 "$S39_MANIFEST_FILE_SHA" \
  --execution-directory "$S39_ROOT/work/S39_component_variant/loading_attempt_01"
```

父进程门为 CPU 8、1800 秒、45 GiB 进程树 RSS、持续至少 10 GiB 空闲磁盘。worker 会在构造模型前再次完整 SHA 五组件；这和 prepare 的冻结 SHA 是两个时点的独立全读。

成功仍只是“加载返回、等待独立验收”，必须同时看到：

- `loading_attempt_01/receipt.json`：`VARIANT_LOADING_RETURNED_PENDING_INDEPENDENT_REVIEW`、returncode 0、无 limit/survivor；
- `loading_attempt_01/worker_receipt.json`：同一 pending 状态、一次 factory、零 generation、零额外 codec 请求；
- `loading_attempt_01/full_resource_gate.json`：`PASS_DECLARED_VARIANT_RESOURCE_GATE`；
- `results/S39_declared_ft_mse_component_loading/runtime_loading.json`：`PASS_DECLARED_VARIANT_COMPONENT_LOADING_ONLY`，所有 `state_dict_loads` 的 missing/unexpected 均为空，VAE loading info 无错误。

如果 loading 在创建固定 output root 后失败，原 frozen manifest 不能再用于第二次 fresh load，因为它绑定的 output root 已存在。保留失败，另立新的 output root/manifest 版本并重新走 core 双审，不能删除目录后伪装第一次执行。

### 6. 不同作者审查实际四份 loading 证据

由不同于加载执行者的审查者读取上一步四份文件并计算各自文件 SHA，写新回执：

- `status=PASS_S39_LOADING_EVIDENCE_REVIEW`；
- `variant` 等于 S39 固定完整对象；
- `loading_manifest_sha256` 等于步骤 3 的 `manifest_sha256`；
- `resource_core_sha256` 等于步骤 1 的规范 `core_sha256`；
- `evidence_sha256` 恰有 `launch`、`worker`、`runtime_loading`、`full_resource_gate` 四键并绑定实际 SHA。

该审查不是 S39 loader 返回 0 的一部分，但它是 S40 generation gate 的强制前置条件。建议使用第三名审查者；最低要求是他/她没有执行本次 loading，并实际审阅四份证据，不能由脚本或执行者自动生成 PASS。

### 7. 交给 S40，而不是直接生成

只有步骤 6 通过，才可把以下动态值填入 S40 的新 frozen manifest：S39 最终 manifest 路径/SHA、S39 规范 core SHA、四份 loading 证据路径/SHA、loading evidence review 路径/SHA。S40 当前 `manifest_candidate.json` 对这些字段仍是 `null`，仍须另行冻结并由两名不同作者给 `PASS_S40_GENERATION_SOURCE_REVIEW` 与 `READY_TO_ATTEMPT_S40_DECLARED_GENERATION`，然后才允许启动两批生成。

## 双 SHA 速查

| 对象 | SHA A | SHA B | 使用位置 |
|---|---|---|---|
| attempt4 | 权重完整 SHA（固定） | 终态 receipt 文件 SHA（动态） | 判断下载身份；后者绑定交接证据 |
| frozen core | `core_file_sha256`（动态文件 SHA） | `core_sha256`（动态规范 JSON SHA） | A 传 `attach --core-sha256`；B 写入两份 core review |
| 两份 core review | source review 文件 SHA | runtime-freeze review 文件 SHA | 分别传 attach 的两个 `--*-sha256` |
| final manifest | `manifest_sha256`（动态文件 SHA） | 继承不变的 `core_sha256` | 前者传 gate/loader；后者贯穿 S40 资源 core |
| loading evidence | 四份实际文件各自 SHA | loading evidence review 文件 SHA | 填入 S40 的 evidence map 和 review binding |

## 当前阻断与旧状态陷阱

1. **唯一当前硬阻断**：attempt4 还是 `RUNNING`，目标文件在本审计时点不存在。不得以下载进程存活、临时 cache 或预期大小代替终态成功。
2. `work/S39_component_variant/independent_review.json` 虽然 status 是 `PASS_S39_SOURCE_REVIEW`，但 `core_sha256` 为 `null`；它是源码前审，不能 attach 到未来实际 core。
3. `freeze_independent_source_review.json` 的 status 是 `PASS_S39_FREEZE_SOURCE_REVIEW`，不是 gate 接受的 `PASS_S39_SOURCE_REVIEW`，且 `core_sha256` 同样为 `null`；它只证明 freeze 工具源码已审。
4. `manifest_draft.json` 仍为 `DRAFT_NOT_READY_FOR_COMPONENT_LOADING`，不能直接改名或复制成 manifest。
5. `FREEZE_PROTOCOL_DRAFT.md` 中“core SHA”的文字容易混淆。源码实际要求：`attach --core-sha256` 接收 **core 文件 SHA**，review JSON 接收 **规范 core SHA**。
6. `PROTOCOL_DRAFT.md` 示例把 manifest 写成 `work/S39_component_variant/manifest.json`；新 freeze 工具实际写到 `attach receipt.manifest_path`（预计为 `review_attachment_01/manifest.json`）。必须用 receipt 动态路径，不要复制到示例路径，也不要传旧草案路径。
7. `work/S40_declared_variant_generation/progress_handoff.json` 仍描述 attempt3/session71130 为 live，这是历史快照；当前资源状态应以 attempt4 终态 receipt 为准。它不直接进入 S39 gate，但不能据此选择旧下载句柄。
8. 当前 freeze/gate/loader/S40 pin 的源码 SHA 全部一致，没有发现需先改代码的旧 SHA 阻断。任一源码后续变化都会使上述 review 失效，必须重新审查。

## 作者隔离要求

| 产物 | 谁可产生 | 是否必须另作者审查 |
|---|---|---|
| attempt4 terminal receipt | 已审 wrapper 的唯一执行 | 已有执行前源码审查；终态仍由后续 reviewer 核 |
| freeze prepare/core | root 或指定执行者 | 是：两名不同作者分别作 source/core 与 runtime-freeze 审查 |
| attach 与 metadata receipt | root 或指定执行者 | 依赖前述两份真实 review；脚本不认证作者身份，工作流必须保证 |
| S39 loading 四份实际证据 | root 或指定执行者 | 是：不同于执行者的 loading evidence reviewer |
| S40 frozen core | 后续 S40 执行者 | 是：另两份绑定 S40 core 的实际批准；现有 source-only review 不能代替 |

这些步骤建立的是具名 `VMem + stabilityai/sd-vae-ft-mse` 组件变体的加载证据，不是 exact-original SD2.1 VAE 复现、codec 数值验证、视频生成、质量提升或创新结论。
