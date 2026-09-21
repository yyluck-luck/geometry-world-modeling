## 2026-09-16T12:49:05+08:00 — GPU隔离镜像卡点解除（合成探针通过）；下一步仍是合同而不是跑模型

**用户问题：** "GPU 侧需要你或 ITSC 确认能否拿到可固定的镜像/registry 权限——你不能确认吗？" 本轮实际去确认了，结论：**技术上可以自己确认，不需要 ITSC 开权限**；只有一个"要不要花 1.5GB 下载"的决定需要用户点头（用户选择了"现在就做"）。

**自己确认到的事实（登录节点 slogin-02，只读探测 + 官方文档）：**
1. `module load apptainer` 后可用 `apptainer 1.1.9`（`/cm/local/apps/apptainer/current/bin/apptainer`，同时提供 `singularity`）。
2. 登录节点**有**到容器 registry 的出网：`ghcr.io`→405、`registry-1.docker.io`→401、`quay.io`→401、`nvcr.io`→401、`pypi.org`→200（401/405 是标准的"可达但需令牌"响应）。
3. **匿名令牌可以解析并固定 digest**（不下载任何层）：`nvidia/cuda:12.6.3-runtime-ubuntu22.04` → index `sha256:63a18dd805367dacfb077aeced8384ab2fb569598ec5f5f5220c3f90a5c23650`，amd64 `sha256:4cf7f8137bdeeb099b1f2de126e505aa1f01b6e4471d13faf93727a9bf83d539`，压缩层共 1529.9 MB。
4. `$HOME` 200G/剩 148G，足够放 SIF；`/cm/shared` 12P。
5. 登录节点 `enroot` 不可用（配置指向 `/raid/local`，权限拒绝）——与旧回执一致；Pyxis 属于作业时路径。
6. 官方文档（HKUST ITSO Apptainer 页 + HPC Handbook Enroot/Pyxis 页）确认：注册表镜像可由用户自行取得，`.sif` 放 home，用 `apptainer exec --nv` 在 SLURM 作业里运行；Pyxis `--container-image` 也支持作业时拉取（NGC 需用 `nvcr.io#org/image` 语法）。**没有任何"需要 ITSC 预先批准镜像"的说法。**

**本轮实际执行（用户批准后）：**
- 在持久 tmux `gwm-pull` 中按 digest 拉取：`apptainer pull --force` → `pull_exit=0`，`real 2m33s`，SIF 1,526,910,976 bytes，`sha256=5a79221373914393c844cc92c32c89e722003591431f3545fc674c0739c59dd0`，存于 `/home/yliutz/gwm-images/`（**项目树之外**，避免 rsync 回传 1.5GB）。
- 合成探针作业 **589607**（`gwm-img-isolation`，partition normal、account mscitspod2026、1 GPU）在 **dgx-21 COMPLETED，28 秒，exit 0:0**，由持久 tmux `gwm-img-probe` 提交。
- 通过项：绑定解释器 `~/.conda/envs/gwm-cut3r-py311-20260915/bin/python3.11` 在镜像内可执行；staged 输入只读可读；**未绑定的 sentinel 与项目根目录在容器内不可见**；`/` 与 stage 绑定只读；`torch 2.7.0+cu126` 在 **NVIDIA H800**（driver 580.159.03）上完成 1024×1024 CUDA matmul，峰值 53.5 MB。`model_access=false`、`dataset_access=false`、`ground_truth_access=false`、`forward_completed=false`。

**边界与未做：** 这是基础设施证据，不是 Gate0 通过、不是安全边界（挂载策略只限制冻结预测器"能读什么"，不防恶意代码）、不是科学结果。计算节点缺 `squashfuse`/`fuse2fs`，每次 `exec` 都会把 SIF 转成临时 sandbox，正式作业前需实测启动开销。`/tmp` 容器内可写（已如实记录）。未跑任何 VMem forward、未读数据/GT、未评分。

**Gate0 仍未通过，剩余缺件不变：** 有效 v4 合同、scorer、独立 verifier、完整窗口 manifest 与命令相机来源，然后才是 validator `PRE_RUN_READY` + formal launch guard receipt。`new_method_validated=false`；`novelty_authorization=NONE`。

**证据：** `work/S103_selector_free_baseline/gpu_image_isolation_20260916/COMPUTE_ISOLATION_RECEIPT_20260916.json`（协议 `README.md`、原始输出 `remote_receipts_589607/`）；状态文档已更新 `docs/GATE0_AND_GPU_START_STATUS_20260916.md`、`docs/RESEARCH_HANDOFF_CURRENT.md`。

## 2026-09-16T12:00:00+08:00 — 本机↔SuperPOD 进度对齐（双向合并）；逐项记录实际改动

**任务：** 用户要求确保本机研究进度与服务器（`yliutz@superpod.ust.hk:~/geometry-world-modeling`）一致，并记录改了什么。SSH 此前被本机 Clash(fake-IP, 198.18.0.165) 干扰而时断时续；连接恢复后执行下列**双向**同步。备份目录：`tmp/sync_backup_20260916/`。

**对齐前的真实差异（实测，非估计）：**

| 项 | 本机 | 服务器 |
|---|---|---|
| 总体积 | 69 GB | 670 MB |
| `data/`、`results/` | 33G + 28G | 不存在 |
| `work/` | 6.2 GB、429 目录 | 202 MB、435 目录 |
| 主账事件 | 1993 条（末条 09-16 11:20） | 1844 条（末条 09-15 21:46） |

**已执行的三步（实际改动）：**

1. **主账合并（服务器→本机）。** 逐条比对 (occurred_at, action, outcome) 后发现**服务器独有 14 条本机缺失的事件**，逐条补入并按时间排序。主账 1993 → **2007 条**；`RESEARCH_LOG.md` 用项目自带 `research_log.py:render()` 重建。备份：`tmp/sync_backup_20260916/research_events.jsonl.{local,remote}_backup`。合并脚本 `tmp/merge_remote_ledger.py`（合并前全量备份、拒绝写入更小账本、拒绝重复 id、写完回读校验）。
   - 补入的关键事实：① 项目根目录 `2606.09803v1.pdf` 即 **Echo-Memory**（受控记忆研究；三评测支路经常互相矛盾，replay 不是"记住世界"的充分代理）；② **GRC 选择机制已被 GIM-World（arXiv:2606.02436，南大+快手Kling）第3.4节 Information-Guided Pruning 发表**，原 GRC 轴需更换；③ ICL-NUIM `depth_semantics` 由待换算变为**实测确认**（K: fx=481.20/fy=−480.00/cx=319.50/cy=239.50，深度 z=raw/5000，位姿 c2w 直接使用）；④ TUM fr3_long_office_household 逐项独立复算通过；⑤ S104 封存预测只读结构检查与评分协议草案（均未评分、未读预测-真值数字）。

2. **拉取服务器独有目录到本机。** `work/S104_cut3r_icl_rgb_calibration/`（服务器独有，89 文件、97 MB，含 ICL-NUIM 校准、创新扫描、作业回执）已完整拉回本机。

3. **本机→服务器整体推送。** 同步前 dry-run：要传 20814 文件、6.37 GB，**0 个删除**。分两阶段：非 `work/` 部分（1275 文件、210 传输、约 8 秒）完成；`work/`（约 6 GB）后台 `rsync` 执行。
   - 排除项：`data/`、`results/`、`tmp/`、`.venv*`、`tools/deepseek-harness/{runtime,state}`、`__pycache__`、`.DS_Store`。
   - 服务器仍不保留 `data/`、`results/`（33G+28G，非本次同步目标）。

**环境事实（本次核实）：**
- 服务器登录节点本次为 **slogin-02**（旧文档写 slogin-01；同类登录节点，仅编号不同）。
- 工作方式：**本机 Mac 为主要工作台**，SuperPOD H800 为已授权远程算力；远程作业须走已记录的 SSH/Slurm 契约与证据门。服务器旧 `AGENTS.md`/`RESEARCH_PRINCIPLES.md` 写"工作机=slogin-01、本树是残缺副本"，属登录节点时期旧表述；本机 `RESEARCH_PRINCIPLES` 为 **v2.12（2026-09-16T00:55）**，是更新版本，已随本次推送覆盖服务器副本；服务器旧版本存于本机备份。
- 本机 `~/bin/dsh-web` 已建立（SSH 隧道映射远程 dsh Web，端口 3099）；`~/bin` 已加入 `~/.zshrc` PATH（备份 `~/.zshrc.bak-before-binpath`）。远程 dsh 版本 0.1.5-rc.1，位于 `~/.local/node-v26.8.2-linux-x64/bin/dsh`。

**最终核对结果（已完成）：** 全部推送完成后，用 `rsync --checksum --delete --dry-run` 做内容级校验：**仍有差异的文件 0、远程多余条目 0**（total size 6374939265 B）。7 个顶层关键文件本机/服务器字节数逐一相同（research_events.jsonl 2146168、RESEARCH_LOG.md 1198817、RESEARCH_MEMORY.md 162980、AGENTS.md 2401、RESEARCH_PRINCIPLES.md 36628、workflow_checks.jsonl 2248252、PROGRESS_REPORT_20260916.txt 13042）。服务器 `work/` 由 202M 增至约 6.6G、448 个目录，与本机一致。校验记录：`tmp/final_diff.txt`。

**传输中断与续传（如实记录）：** 首次 `work/` 后台推送在约 2.6G 处被 `Connection reset by peer` 中断（Clash/网络导致），已保留为失败记录；改为 `--partial` 加 `ServerAliveInterval=20/CountMax=10/TCPKeepAlive` 后断点续传成功（18347 文件、4419397674 B）。

**未做 / 边界：** 未同步 `data/`、`results/`；未删除本机任何大文件；未改动任何既有实验结果、协议或报告。本次是文件与记录对齐，**不是**新实验、不是方法验证。创新状态仍为 `new_method_validated=false`、`novelty_authorization=NONE`。

**已知隐患（本次发现，未修）：** 本机项目目录内**没有** `.git`；但 `/Users/rocket`（整个用户主目录）是一个 git 仓库，暂存区已有 776 个主目录之外的条目且 0 提交。直接在该仓库 commit 会误提交无关文件。建议在项目内单独 `git init` 并配 `.gitignore`（排除 `data/`、`results/`、`work/` 及大二进制）。

## 2026-09-16T01:57:28.641097+08:00 — Gemini/Computer 实际接口订正

本轮已找到并实际调用本机 Computer 插件（node_repl + @oai/sky）；操作 Codex 应用时返回明确限制：“Computer Use is not allowed to use the app 'com.openai.codex' for safety reasons.” 没有绕过限制，也未从本任务向 Gemini 发送问题。此前仅凭工具名缺失推断无法使用的判断不完整。另一研究任务已通过其 Browser 接口保存 Gemini 审查摘要，报告可见模式为 Pro Extended，数字版本3.1未确认；新咨询已转交该可用任务。数据适配、实际输入隔离和创新实验设计三个代理已接续。证据：`work/gemini_capability_20260916/CURRENT_CHECK_20260916T015728+0800.json`。

## 2026-09-16T01:43:12.338590+08:00 — Gate0 attack: corrected 7-Scenes rejection and acquired 3DMatch scene archives

Independent audit rejected candidate-v2 PASS labels: 7-Scenes RGB/depth are explicitly uncalibrated, the effective VMem config is 576x576 with 4+4 frames and seed 42, the substring future-path guard is bypassable, and the validator mixes pre-run readiness with post-run acceptance. Candidate-v2 is preserved and formally retracted in `work/S102_gate0_tum/GATE0_CANDIDATE_V2_RETRACTION_20260916.json`; candidate-v3 and current decision remain BLOCKED. The new `validate_gate0_v2.py` separates PRE_RUN_READY from PREDICTION_SEALED/POST_RUN_ACCEPTED and passes 7 synthetic software checks only.

The 7-Scenes Chess archive is real and hashed (`d00b5b8f...`), but remains an unqualified raw RGB-D candidate. After a source-only freeze, 3DMatch RGB-D Scenes v2 scene_13 was downloaded and hashed (`9fa3b934...`, 180MB) and scene_14 was downloaded and hashed (`d3011fe0...`, 239153034 bytes) through remote tmux; no model/score was run. Scene_13 has one sequence, so it is calibration/development only; scene_14 is the independent scene candidate. Both use estimated mapping poses and still require source-specific adapter/lineage checks.

Remote H800/tmux/Slurm preflight is complete with corrected checkpoint names and launcher hash checks; no formal job was submitted. Current next gate work: extract/audit scene_13/14 source contracts, build staged allowlist isolation and effective VMem manifest, then qualify PRE_RUN_READY. Formal baseline and GRC/SOCF scoring remain unauthorized until the corrected contract and calibrated heldout evidence pass.

Gemini 3.1 Pro Extended was not called this turn because no Computer Use/browser-control tool was exposed and macOS AX trust was false; capability receipt is `work/gemini_capability_20260916/RECEIPT.json`. This is an interface limitation, not evidence about Gemini service availability.

## 2026-09-16T01:36:11.321831+08:00 — Gate0 candidate correction and Gemini interface check

7-Scenes Chess archive has been downloaded and hashed on SuperPOD, but official uncalibrated RGB/depth prevents treating it as a qualified metric-reprojection heldout source. Candidate v2 PASS fields were unreviewed and are retracted by `work/S102_gate0_tum/GATE0_CANDIDATE_V2_RETRACTION_20260916.json`; candidate v3 and current decision remain BLOCKED. Incorrect hand-entered document timestamps are corrected using birth times and the event ledger. Pre-run/post-run Gate0 circularity, actual model config and checkpoint paths are being audited. Computer plugin was explicitly requested; current tool/skill discovery and local AX probe did not yield a usable interface, so no Gemini prompt has been sent this turn.

## 2026-09-16T00:25:59+08:00 — Parallel pre-Gate innovation pilots started

已启动三个并行代理：SOCF-A 源级冲突诊断、重影机制诊断、CVaR/DLV pilot 准备。它们只能使用既有开发/合成材料，不得读取 held-out future outcomes；正式创新实验仍需 Gate 0、数据合同和预测封存。20 分钟自动计划已同步为“先收集这些回执，再冻结 Gate 0 与 S103”。

## 2026-09-16T00:23:00+08:00 — Full no-data VMem model-load smoke passed

H800 Slurm job 588459 成功完成完整 VMem 无数据加载：VMemModel、AutoEncoder、CLIPConditioner、ARCroco3DStereo 均从已校验权重加载，24.60 秒、峰值显存 7.884 GB；没有读取数据、未来 GT 或执行 forward。自动化计划已同步更新，下一步是冻结 S103 实现与数据合同、正式运行 Gate 0；创新候选仍按 SOCF-A/FGB-Future 路线保持未验证。

## 2026-09-16T00:16:16+08:00 — All promising innovation directions ranked

并行创新、理论和审稿代理完成了全量重排。当前最强条件方法候选是 SOCF-A（联合源级几何冲突 + abstention），最稳妥的论文问题是 FGB-Future（固定预算下检验历史是否改善独立未来 RGB-D/pose 状态）。反事实来源干预和重影机制分解优先作为测量/诊断；CVaR、DLV、分歧加权/写入准入作为条件候选；异构代价选择只作系统分析。原始 GRC-Memory 因 GIM-World、Mem-World、Future Forcing 等近邻覆盖，暂判 Reject and Pivot。完整排名见 `work/agents/INNOVATION_SYNTHESIS_20260916.md`。所有候选仍未验证。

## 2026-09-15T23:48:38+08:00 — No-data model-load smoke dependency repair

S103 no-data smoke job 588242 已完成 VMem、VAE、CLIP 与 CUT3R 权重加载，但在导入 CUT3R 可视化依赖 `viser` 时失败；未读取任何数据或 GT。已在隔离远程环境安装 `viser` 与 `trimesh`，同一脚本重新提交为 job 588321，目前运行中。该步骤仍是基础设施验证，不能替代 VMem forward 或正式实验。

## 2026-09-15T23:34:13+08:00 — VMem checkpoint transfer completed; no-data smoke resubmitted

远程 VMem 权重已完整传输并通过 SHA-256 校验（5,056,346,672 bytes，SHA 与本地声明一致）。随后提交 S103 no-data H800 model-load smoke：job 588215 在 CUT3R 权重的 PyTorch weights_only 安全限制处失败，未访问数据；已对两个 SHA 已核验 checkpoint 做窄范围兼容补丁并提交 job 588242。尚未运行 VMem forward、视频或 GRC。

## 2026-09-15T22:43:47+08:00 — 20-minute research heartbeat activated

根据上一轮真实结果（S104 CUT3R H800 前向成功、VMem 权重仍在传输），已将现有科研自动化从每30分钟改为每20分钟。后续每次检查都必须先读取最新账本和计划，再按最新状态决定：监控/续传权重、核验远端 SHA、Gate 0、无数据模型加载、冻结 S103，随后才允许正式基线和 GRC 对照。自动化同时保留创新检索、红队审查、代理容量如实记录和“完成全部 GPU 实验后再统一分析”的约束。

## 2026-09-15T22:12:02+08:00 — S104 CUT3R H800 component inference completed; remote innovation reports synchronized

已通过 SSH 连接 HKUST SuperPod 并完成真正的 H800 组件实验：Slurm job 586699 成功编译并导入 CUT3R cuRoPE，job 586719 使用固定四张历史 RGB（id 1/31/61/91）完成 CUT3R 前向。回执显示模型 SHA 与声明权重一致，forward 10.663 秒、峰值显存 3.642 GB、设备 NVIDIA H800；depth、pose、GT 均未读取。这是组件可运行性证据，不是 VMem 长时程基线，也不支持 GRC 方法效果。

远程工作区最近新增 `S104_cut3r_icl_rgb_calibration/INNOVATION_SCAN_20260915.md` 与 `INNOVATION_IDEAS_20260915.md`，已复制到本地 `work/remote_innovation_20260915/`。其排重结论显示 GIM-World、Mem-World、Future Forcing、R2M-Bench 等已占据原始 GRC 组合；较有区分度的待证伪方向转向误差相关结构、CVaR 尾部风险、记忆失效/准入和重影机制分解。所有候选仍保持 `novelty_authorization=NONE`、`new_method_validated=false`。

VMem 权重仍只有 2,666,266,624 / 5,056,346,672 bytes，SHA 未完成；本地已启动可恢复 rsync。Gate 0 和实现审查仍是正式 VMem 运行前置条件。

## 2026-09-15T12:56:31+08:00 — Continuous innovation and full agent staffing enabled

The 30-minute heartbeat prompt now requires a bounded innovation-search or red-team agent whenever capacity permits, with separate roles for primary-source novelty scanning, skeptical review, and H800 execution. Current live child agents: `innovation_continuous`, `innovation_redteam_continuous`, and `gpu_execution_preflight`; all are running with distinct scopes. The previous translation agent completed the four English protocol copies and was released.

The scheduler remains active and was updated through the app automation tool. The remote VMem transfer is still partial; no VMem baseline or formal GRC experiment has run.

## 2026-09-15T12:51:39+08:00 — Parallel innovation and GPU plan artifacts

Three bounded agents were dispatched. The innovation review checked ViewRope, Spatia, GIM-World, and WorldTrace source claims and narrowed the primary candidate to SOCF-A (replacement-direction conflict plus abstention); FVR remains a secondary candidate. Both remain unvalidated, with explicit pilot and kill criteria. The H800 agent created and syntax-checked a plan-only CUT3R RGB-only component runner under `work/S104_h800_cut3r_calibration/`; it has not been submitted and does not access depth, pose, or GT. The translation agent is working on faithful English copies of four critical protocols.

The English plan registry was corrected to avoid speculative S92-S100 meanings; verified archived entrypoints are named by full paths and prospective work uses P01-P18. The remote VMem checkpoint transfer remains partial, so no model or formal GRC run is accepted.

## 2026-09-15T12:36:03+08:00 — English research-plan registry and scheduler rewrite

Per user request, all active plan instructions are now restated in English in `docs/RESEARCH_PLANS_EN.md`; scheduler-specific instructions are in `docs/RESEARCH_AUTOMATION_CONFIG_EN.md`. The registry preserves S0–S103 identifiers, proposal alignment, evidence gates, innovation falsification requirements, and the current H800 queue. Historical Chinese plans and Chinese beginner summaries remain unchanged as evidence. No scientific result or novelty status changed. The remote weight transfer is still incomplete; no VMem/GRC model run has started.

Next: finish/resume transfer, verify every remote checkpoint hash, run a no-data model-load smoke, then proceed to the frozen calibration/development VMem baseline only after the implementation audit.

## 当前接续入口（记录UTC 2026-09-15T01:54:30Z）

2026-09-15 09:54本地推进：完成 ICL-NUIM 官方相机/深度合同审查。TUM 官方文件格式明确 640×480 RGB-D、16-bit 深度因子5000、0为缺失、RGB-depth 预配准、轨迹字段；ICL 官方 MATLAB 源码明确 native `.depth` 是 radial distance，需 radial→z，且 MATLAB 1-index 中心320.5/240.5对应0-index 319.5/239.5。新增合同说明、三项纯算术单测及SHA回执；单测仅证明实现公式自洽，0数据/0GT/0模型，Gate0仍阻断。详见 `work/S102_gate0/ICL_CAMERA_DEPTH_CONTRACT_REVIEW_20260915.md`、`ICL_CONTRACT_ALGEBRA_CHECK.json` 和 `official_camera_sources_20260915/`。

2026-09-15 10:02本地推进：SSH恢复并核验Slurm job584548为COMPLETED exit0；imageio2.31.1已安装，PyTorch2.7.0+cu126、torchvision0.22.0、numpy1.26.4、scipy1.16.2、transformers4.48.3、accelerate1.4.0、cv2 4.11.0、imageio2.31.1、diffusers0.32.2九项基础import通过。回执已复制到 `work/S101_env_bootstrap/remote_receipts_584548/` 并更新 `SUBMISSION.json`。这只证明环境包可用，尚未导入VMem项目、加载权重、运行模型或读取数据/GT。

2026-09-15 10:35本地推进：完整源码包上传SuperPOD后SHA与196个tar条目核对通过。首次项目探针误用系统Python3.10，纠正为个人Python3.11绝对路径后确认缺kornia；585714完成直接依赖安装，kornia/open_clip/matplotlib/torcheval导入通过。重跑无GT项目探针后 `modeling`、`modeling.pipeline`、`conditioner`、`autoencoder`、`utils` 全部IMPORT_OK。仍未构造模型、加载权重、读取数据/GT或运行科学实验；下一步是最小GPU smoke和Gate0样本资格审计。

2026-09-15 10:52本地推进：H800 GPU smoke 修正后 job585971 在 dgx-09 完成 exit0；H800 81559 MiB、CUDA可用、torch2.7.0+cu126、1024矩阵乘通过；加入 `vmem` 与 `extern/CUT3R` 双 PYTHONPATH 后五个 VMem 项目模块全部 IMPORT_OK。585900/585928 的路径错误均保留。该结果只证明GPU环境和代码导入，不是模型/科学实验；0数据、0GT、0权重。下一步进入 ICL Gate0 小样本解码和合同审计，资格门通过前不运行正式GRC。

2026-09-15 10:59本地推进：ICL Gate0 小样本解码 job586074 完成。服务器归档中 id 1、2、3、750、1508 的5对 RGB/depth 全部存在；RGB均640×480 RGB PNG，depth均640×480 I;16 PNG，uint16样本无零值。该步骤仅用于合同资格，未用未来GT选择、未运行模型；完整归档、split、相机坐标和GT隔离仍需审计，Gate0继续阻断。

SSH 至 SuperPOD 仍在服务端版本交换前关闭，584548 imageio 修复作业状态未知；没有重复提交或修改代理/VPN/私钥。恢复后先取回作业回执，再上传196文件完整源码包并做远端无GT项目import；取得归档后先做小样本 dtype/尺寸/单位/时间抽样，未通过 Gate0 前禁止正式 GRC。

## 当前接续入口（记录UTC 2026-09-14T23:10:04Z）

2026-09-15 09:18本地补充：SSH verbose将失败定位在服务端版本交换之前，未到账号/密钥认证。系统DNS与UDP公共DNS都返回198.18.0.84，经utun9/198.18.0.1；HTTPS DNS返回143.89.184.2，向该IP只读TCP探针同样约5秒后空banner。可确认连接链含本地隧道/代理，不能确认哪端关闭；未改VPN/代理/密钥。详见`work/S101_env_bootstrap/TRANSPORT_DIAGNOSIS_20260915.json`。继续取584548回执，不反复改依赖排查连接错误。

已创建并安装个人Python3.11环境；584449 resolver成功、584494安装成功但imageio缺失，584548修复已提交。两轮SSH均连接关闭，584548状态未知，禁止重复安装。此次连接输出只证明SSH传输失败，不能归因学校服务器或模型。旧各环境与共享base记录仅为历史。

已准备完整无数据/权重源码包：`work/S101_env_bootstrap/source_transport_v1/`，196文件、357741B、196个哈希与S40保存清单一致。`vendor/vmem_snapshot`只有7个审计文件，不可作为完整源码上传。实际代码还需kornia/open_clip等，九包probe不能支持“VMem只缺imageio/diffusers”的结论。SSH恢复后先取584548回执，再上传完整源码包并运行不构造模型的离线import检查。正式GRC仍未运行，创新候选未验证。本轮子agent接续因thread limit失败，root本地完成源码包，不宣称agents在运行。

## S91R-C修正：保存数据控制审查停止GRC方法主张

更新UTC：2026-09-12T07:47:23+00:00（北京时间15:47:23）。S91R-C对上一段S91R saved-data先导复算做了固定控制审查。原先“32个组合/每方法32”表述不准确：实际是2方法×4目标×4来源=32个分层，每方法16个；原脚本的风险分位边界还使用了future-valid掩码，已在C审查中改为先用过去候选的全部finite/positive像素定边界，再应用未来有效性。

控制审查结果：4个目标的有符号未来AbsRel改善（never−all_new）均值分别为−0.014472、−0.007696、−0.005395、−0.006582；all_new虽然在像素层面改善比例为0.5948、0.6317、0.6467、0.6459，但总体平均误差变差。加入disagreement的留一目标预测相对基础控制的ΔR²平均约+0.01463且4/4为正，但两个方法在同一目标上的source identity相同比例只有约4.35%–5.49%，因此不能解释成同一记忆条目的因果收益或GRC方法效果。按预先停止规则，当前 saved-data 不支持GRC-Memory方法主张；S91仍为Gate0阻断，必须等合格未见RGB-D/相机配对后再做同身份、固定预算比较。

证据：work/S91R_saved_future_error_reanalysis/CONTROL_AUDIT_PROTOCOL.md、CONTROL_AUDIT_REPORT.md、control_audit_results.json、control_audit_recheck.json、verify_s91r_control_audit.py。\n\n## S91R（已保存历史候选与未来深度误差回顾性复算）：先导信号，不是新方法验证

更新UTC：2026-09-12T07:25:40.995135+00:00；北京时间：2026-09-12T15:25:40.995135+08:00。在不联网、不调用新模型的条件下，对已保存的 S15B proposal、目标预测和传感器深度进行固定公式复算。结果显示：old/new 几何相对不一致度与未来目标深度 AbsRel 在 `never` 和 `all_new` 两条保存消费者输出上均呈正向描述性相关；`never` 组合范围约0.088–0.633，`all_new`约0.154–0.497。独立脚本对32个 method×target×source 组合复算通过。

证据：`work/S91R_saved_future_error_reanalysis/PROTOCOL.md`、`RESULTS.md`、`results.json`、`verify_s91r.py`、`risk_future_correlation.png`。

边界：这是一个已经暴露的单段 TUM 数据上的 saved-data reanalysis，不是未见测试、跨场景实验、GRC-Memory验证或新模型运行。正相关可能来自来源、覆盖率、confidence、位姿和场景结构混杂；必须在 Gate 0 合格数据上与 recent/random/pose/coverage/utility/confidence 等同预算基线比较。

下一步：把它作为 GRC-Pilot 的先导信号；Gate 0 通过前不把它写成创新成立，也不启动新的未来答案评分。

<!-- S90_INNOVATION_UPDATE_BEGIN -->
## S90继续：昨天猜测已改成可证伪矩阵，第二轮创新检索完成（记录UTC 2026-09-12T07:01:24.542432+00:00）

用户要求继续使用全部Agent并完成昨天猜测与创新点。本轮实际并行交付：`agents/yesterday_hypotheses_matrix_20260912.md`、`agents/innovation_retrieval_round2_20260912.md`、`agents/yesterday_progress_audit_20260912.md`和`agents/advisor_oral_brief_20260912.md`。新增原文核验R2M-Bench、WorldPack、GIM-World和CAP；未找到完整“逐历史未来几何风险+固定预算保证”方案，但结论仍UNKNOWN，不授权新颖性。

四个候选已分层：GRC待独立未来真值；反事实是有符号未来损失测量协议；2×2是重影诊断而非GRC验证；变点方向因动态数据缺口暂缓。S86/S87实际结果和NO_METHOD_SELECTED状态不变。报告更新入口：`work/S90_proxy_resumable_index/YESTERDAY_HYPOTHESES_AND_INNOVATION_UPDATE_20260912.md`及用户快照`outputs/创新候选逐条核验_S90_2026-09-12/`。

下一项研究门保持：先完成并复审S90索引工程，Gate0数据资格，再做2×2和小型同预算GRC pilot。没有新模型/网络数据/未来几何评分。
<!-- S90_INNOVATION_UPDATE_END -->

<!-- S90_CURRENT_BEGIN -->
## S90当前：对话与附件30项核验完成，GRC仍未验证（更新UTC 2026-09-11T16:07:34.254982+00:00）

本段优先于下方历史S89状态。最新完整核验：`work/S90_proxy_resumable_index/DIALOGUE_CLAIM_AUDIT.md`。三个Agent实际并行核数学/近邻/附件，root完成独立有理数复算，见`ROOT_DIALOGUE_AUDIT_RECEIPT.json`。没有新真实模型/图像/几何评分。

- S86/S87真实局部基线仍成立；S87普通末端.75的MSE0.05116758低于多步0.05242222，只否定该例多步必要性，非GRC/几何优势；target22失败保留。
- 原GRC高分与已成立新颖性撤回。GIM已有geometry+MI+固定预算，差异须落到可验证的未来几何帮助。CRC缺单调策略损失等前提，不能给每条记忆上界。互信息目标不天然泄漏；测试读真实未来才泄漏。Σq对一般集合损失无自动保证，但union bound仍合法。
- 两个新增人工例已执行，root Fraction复算：2×2交互非记忆收益必要/充分条件；风险阈值收紧可令下游损失增加。全部是合成逻辑，非方法效果。2×2用于重影诊断，与GRC直接风险→future benefit试验分开。
- COVRAG/WorldTrace/GIM已有历史记录，非本轮首次发现；SWIM变点说法无对应证据。旧主综述WorldTrace链接正确，本轮Agent曾误读，已更正。旧root七项测试被加固版本覆盖/2×2初版未备份的来源缺口均记录，不假装完美复现。
- S90一条512B传输已恢复：代理7897、HTTP206/TLS0，00000/00134.depth.exr头，3.592271秒。0新RGB/EXR正文。索引脚本仅静态审查REVISE，尚未执行；下一偏移12605440。

下一项实质任务：修`index_rtmv_resumable.py`的归档绑定、512B失败正文边界、HTTPS与断点链/崩溃语义；不同作者复审后冻结有限索引预算，取得开发配对核EXR/相机/单位。新数据不沿用旧场景底图，静态视角ID不当动态时间。随后冻结直接风险—未来帮助小实验；2×2并行作为独立诊断支线。当前`NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false`。

旧176页LaTeX/PDF是S89截点，未被本轮改写；本轮交付为详细Markdown核验、原始JSON和源码快照。检查超时如实OVERDUE，不把中断间隔当工作小时。
<!-- S90_CURRENT_END -->

<!-- S89_CURRENT_BEGIN -->
## S89当前：两次数据接续受TLS阻断；8页教学增补及176页连续版已核验（UTC 2026-09-11T01:41:37.711993+00:00）

S88已经取得的7头+相机JSON与S87真实生成结果均保留。S89从11460608续索引的两次不同TLS栈尝试分别1.460404秒/0.533428秒，均1请求/0新正文/0新头；第二次没有HTTP响应，不声称到达CDN。旧6个不完整视角组保留，完整三件套0/selected=null仅表示尚未取得，不证明数据缺失。两批失败分别44/25项不同作者记录核验接受，见work/S89_matched_view_index/ROOT_INDEX_ACCEPTANCE.json。0新模型/几何评分。

创新源审新增GeoNeRF(CVPR2022)/GeCoNeRF(ICML2023)，分离独立落点、可见性与颜色；数学反例说明cycle=0可同时落点错20px。生成RGB的重复/缺失需全部记录，warp身份/深度不能当生成物体真值；旧观察器控制无新风险不重跑。RTMV仅作静态投影/混合反证，不能替代长期动态与实拍泛化；8数字ID不是连续轨迹。NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false。

新8页以零基础手算、真实target22完整失败图、S86/S87十策略均值、S88数据/相机含义、S89失败与proposal/5问答解释；本机LaTeX、不同作者内容和root全8页视觉通过。与原168页合为176页，全部页文字/尺寸/绘制内容一致，4处衔接渲染像素一致，旧稿不改。用户目录：/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/导师汇报_科研同步增补_S89_2026-09-11。最终文件及复制回读以FINAL_DELIVERY_INDEX.json为准。

下一步先恢复可达HTTPS路径，再按原身份从11460608续索引，勿盲重复两批、勿禁用证书校验；随后固定一个开发视角/有重叠的源—目标配对核真实EXR语义，再决定8视角实验。具体NEXT_PAYLOAD_DEVELOPMENT_PLAN.md与innovation/RTMV_SCOPE_AND_NEXT_DECISION.md。三子岗本批均实际完成，未声称后台无限检索。
<!-- S89_CURRENT_END -->

<!-- S88_CURRENT_BEGIN -->
## S88当前：RTMV原相机JSON实际取回并独立核验；尚无新图像/深度实验（UTC 2026-09-11T01:10:40.076049+00:00）

S87数值/24新图/12页新报告及168页连续版已经交付且保持不变。本轮从独立数据与竞争解释推进，0新模型/生成/图像评分，NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false。

RTMV作者重发布abc.tar固定commit855627f73a6fdd4db7fa150097a576f6e890c569，整包发布大小12,064,450,560B。第一次探针因302说明正文1032B超过本机512B传输cap而rc56、0正文；不是TLS/Range失败。v2经不同作者源审后真实16.344068秒，8逻辑Range（7头+JSON）均精确206，共193483B，取得00000/00108.json。没有下载全档/全档SHA验算，也没读RGB/EXR正文。JSON完整字节含objects已解析，但只分析camera_data，不能说从未接触GT字节。

JSON1600²、focal1931.371337890625、principal800；cam2world/view按转置使用。root与不同作者106项字节/偏移/标量相机复核通过；V×C残差7.64e-8仅内部算术，不是物理精度。ROOT_METADATA_ACCEPTANCE.json记录边界。作者生成源码支持depth bounce0、中心采样、矩阵逐列导出；归档实际构建/EXR通道行序/无效值/同场景多视角静态性仍未核。不用巨大scene_bbox猜尺度，不把Wisp筛选当GT定义。

创新岗新增FWD(CVPR2022)/PMRF(ICLR2025)原文和固定代码：错误几何与软混合可能共同产重影，固定blend不是已知posterior mean。只保留未来几何来源×RGB .75/1的2x2诊断，外部源几何为oracle额外信息；普通可信几何复制若解决则停止新融合主张。尚未执行这个新实验。

具体接续：work/S88_independent_geometry_data/NEXT_MATCHED_VIEW_INDEX_PLAN.md。先从已核JSON末尾的下一tar头有界索引，不请求旧7头；定位同basenameJSON/RGB/depth，再另冻实际读取/单位检查预算。不重跑S86/S87，也不盲下载PointOdyssey/RTMV整包或TinyNeRF。PointOdyssey作者资产许可评论已恢复但同步小片段仍未知。三子岗本批完成后收束，不假称后台持续研究。

七项检查UTC2026-09-11T01:10:40.076049+00:00，实际间隔26.339105分钟，ON_TIME；本轮起始34.456495分钟OVERDUE保留。科研正文S88_RESULTS.md及全部来源/失败/核验随新S88用户快照交付；168页不追溯改写。
<!-- S88_CURRENT_END -->

<!-- S87_CURRENT_BEGIN -->
## S87当前：普通末端反例经实算与独立复算确认，仍有重影；12页新报告及168页连续版已核验交付（交付记录UTC 2026-09-11T00:09:52.340028+00:00）

本段优先于下面历史当前状态。唯一执行UTC23:37:54–23:38:48，科学进程53.741317292秒，3次VAE全8槽解码/24chunk+3组RGB派生，0新完整链/0新几何/编码。固定强度.5/.75/1×两族，全部24新行+旧S86原16引用。独立派生50字段精确通过/0.53309秒，直方图与Fraction1969精确比较/309展示浮点通过/0.19463秒，max展示差1.38778e-17；不重跑VAE复核。root接受work/S87_terminal_strength_audit/ROOT_RESULT_ACCEPTANCE.json。

六新策略全图四帧MSE：Gpaste .5=.0650333576694、.75=.0533606667251、1=.0560597908739；Gterminal .5=.0675577687885、.75=.0511675816620、1=.0525320458852。Gterminal.75 SSE13246509800低于旧Gguide13571317266，精确差−324807466。**STOP_NECESSITY_CLAIM：取得本例RGB分数不需要多步引导。** 这不是纯时机/等累计剂量因果识别，也不是跨场景验证、速度纪录或新方法。只有20/21/23的全图误差较低，22较高(.07483243对.06826439)，全部保留。

root实际看了全部24张576原尺寸新图和4张总览（工具总览显示2048×971，文件2952×1400）。.5/.75明显叠加，.75四目标仍有重影；1更接近投影主轮廓但点状破碎、孔洞接缝/底部原生成残留等保留。不把清晰或低MSE当几何真值。ROOT_VISUAL_ACCEPTANCE.json记录非盲观察范围与每目标现象。

创新原文/数学：SHAPE_FAILURE_MECHANISM_REVIEW.md、BEGINNER_MECHANISM_EXPLANATION.md解释条件均值/误差与形状、两像素反例及soft非一概错误。HARD_SELECTION_FOLLOWUP_FEASIBILITY.md仅source-only普通RGB选择草案，0新执行；不继续S87强度细扫，下一先核独立相机/物体位置的评价与可用数据，再判断普通hard诊断是否有必要。保持NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false。

报告同步（实际交付更新UTC 2026-09-11T00:05:24.632791+00:00）：新增12页LaTeX已本机双遍编译；root实看全部12页，不同作者核24行/公式/成本和边界通过，无溢出/缺字警告。与原156页合成168页，逐页文字/尺寸/绘制内容等源、4关键页源/合并渲染像素一致，root接受，已复制回读SHA一致。连续入口：/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/导师汇报_深入讲解第二版_2026-09-10/最新连续阅读版/完整汇报_含S87实际结果_168页.pdf；全部数据/PNG/源LaTeX/证据：/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/导师汇报_深入讲解第二版_2026-09-10/S87_09月11日末端反证与详细讲解。旧156页及各历史截点不改。完整交付以FINAL_DELIVERY_INDEX及其清单为准。

下一科研任务：NEXT_SCIENTIFIC_DECISION.md已核旧S73/S74/S77/S80/S81正负控制实际存在，不重复验证。PointOdyssey官方3个元数据请求暂未定位可单独获取的同刻多视角片段；最小HF数据包3,324,284,510字节，未下载，具体同步索引、场景独立性和数据许可冲突未核清。下一批只有限访问已观察到的官方入口，不启动新生成。真实传感器参照与模拟器真值分开。

第二批实际3请求已核Drive目的页只见整包和官方repo问题元数据，另1请求TLS失败；共6请求/2批，仍未定位具体同步序列。未取得新图像/NPZ/数据包，许可冲突与划分独立性保留。见NEXT_DATA_ACCESS_CHECK_02.md；用户问题不是作者数据声明。

最新七项检查UTC 2026-09-11T00:09:52.340028+00:00，实际间隔22.630301分钟，ON_TIME；前两次OVERDUE记录不改。报告与科研本批已闭合，下一按独立数据入口推进；不重跑已成功的S86/S87。
<!-- S87_CURRENT_END -->

<!-- S85_CURRENT_BEGIN -->

<!-- S86_CURRENT_BEGIN -->
## 当前：S86四臂真实结果接受；MSE下降但明显重影，156页报告和全部实际数据已交付（UTC 2026-09-10T22:29:31.388829+00:00）

本段优先于下方历史当前状态。S86已于UTC2026-09-10 22:14完成，原监督/科学进程已正常退出，不再等待或重跑。两条完整50步链G0/Gguide及同G0派生Gpaste/Gterminal全部封存；科学总2636.981462042秒，监督2640.523644708秒，树峰值17.17GiB。原VMem流程/权重+声明ft-mse VAE，原SD2.1VAE身份UNKNOWN；CPU FP32/8线程/576，固定history19/18/13/12、target20–23、同真实随机流、avg8支持mask、λ=.25。所有50步Gguide raw/used保存，不冻结干预后代。G0与事前绑定S70 A0完整noise/latent/raw/uint8/RNG精确兼容。

只运行一次正式评分。完整4帧发图uint8全图归一化MSE：G0=0.13116666776908745，Gpaste=0.09096801252375357，Gterminal=0.09819160239669339，Gguide=0.05242222252907684。事前主差guide−terminal=−0.045769379867616554；对G0/paste亦均负。四目标全图/支持/洞区的三对比全部同方向，完整16行及分母位于scoring_01。不同作者保存量复核123字段PASS/maxdiff0；统计直方图/Fraction复核821精确比较、174浮点展示PASS/maxdiff1.38778e−17。ROOT_RESULT_ACCEPTANCE.json仅接受描述性RGB分数和保存量，不是外部复现或新方法确认。

已导出33PNG并root实际看全总览及全部32张576原尺寸图，字节/像素读回通过。**Gguide在20有双影，21–23明显重影、涂抹和形状模糊。MSE下降与可见缺陷同时成立，不能说全面画质更好。** 人工观察非盲、无量化感知评分。ROOT_VISUAL_ACCEPTANCE.json只验图内容/版面。单已见静态场景、四相关帧、一次噪声不能证明动态/长期/跨场景；50次vs1次累计干预/传播混杂、VAE全局耦合和近邻前例都保留。

科研接续：S86_RESULT_TO_INNOVATION_DECISION.md接受已有基线作用、拒绝软融合算子新颖性；下一项设计为有限普通末端强度反证(.5/.75/1)，复用已存G0末态，先独立审冻结，未运行。它只否证‘达到本次MSE需要多步’，不把事后选最小值当验证成绩，不继续细扫。NVS源码/理论边界、时机剂量数学、长期候选及DynaBench缺项已保存；动态数据可行性UNKNOWN且不阻碍本批完成。保持NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false。

报告同步：10页《S85_S86_从投影到生成强对照_教学增补.pdf》、tex、全16对/4目标CSV和8问答34文件已交付0回读差，目录outputs/导师汇报_深入讲解第二版_2026-09-10/S85_S86_09月11日原理与生成对照/。其05:34截点不变。新4页实际结果报告已全页/内容验收，连同全部保存数组/33图和证据实际复制279文件，316228194字节，回读0差。156页连续版已合并并核全部页文本/尺寸、9页源/合并渲染，见RESULT_REPORT_DELIVERY_COMPLETION.json。最新用户入口：/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/导师汇报_深入讲解第二版_2026-09-10/最新连续阅读版/完整汇报_含S86实际结果_156页.pdf；新包：/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/导师汇报_深入讲解第二版_2026-09-10/S86_09月11日四臂实际结果。旧142/10页不改。

当前三子岗分别实际结果PDF、结果解释审查、创新反证协议；状态按真实消息核。Gemini Pro Extended本轮通过CUA真实英文审查，错误被独立数学/原文否决；本机Python/原模型/LaTeX/Poppler已实际使用。最近七项检查UTC22:30:41（实际间隔25.706688分钟），下一须不晚于23:00:41；主账按真实时间追加，时间不是学生工时。

报告交付闭合记录UTC 2026-09-10T22:41:42.632813+00:00；S87设计已通过不同作者草案审查，N1候选集合/平局定义修订由root确认；正式执行器、合同和源码前审待完成，0新执行。
<!-- S86_CURRENT_END -->

## 当前：S85实际历史投影及独立复算完成（UTC 2026-09-10T20:35:08.829437+00:00）

最新科学接受`work/S85_fixed_geometry_warp/ROOT_RESULT_ACCEPTANCE.json`，SHA835e9e6879b9dacc1a1583d116204bc36b74c17792fa6e4ea8fa11cdfc597857。四历史12/13/18/19×四目标20–23，全部16对、3145728源点记录和5个数值档案已保存；唯一投影运行2.293416秒，监督2.378199秒，峰值自进程RSS538640384B。不同作者从2原档案+5输出实际复算1.823490秒，120字段比较通过，其中28浮点项最大差0；另核31×4schema、完整候选排列及严格顺序。没有新模型、优化、目标RGB或传感器读取。此处只接受固定规则的数值/保存一致，不能称物理准确或生成改进。

目标20–23各331776像素，预测支持312396/292217/267572/263594，孔洞19380/39559/64204/68182，覆盖94.1587/88.0766/80.6484/79.4494%。正双线性足迹仅定候选，硬Z赢家直接复制源RGB；多候选不等于真实遮挡，历史12赢家多不证明它更可靠，四目标不是四独立场景。13张PNG及总览已导出，root像素核验与四目标原尺寸视觉检查通过；灰格表示无投影支持，不是新生成或目标实拍。完整说明`S85_RESULTS.md`、4/16行CSV和`visuals_01/`。

用户快照入口：`/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/导师汇报_深入讲解第二版_2026-09-10/S85_09月11日历史投影与对照`；完成以该目录`COPY_READBACK.json`和项目`DELIVERY_COMPLETION.json`为准。旧142页完整汇报保留原S84科学截点，未假称已包含S85。S82真实4历史预测、S83固定相机100步及S84单张传感器MAE约0.35617→0.35497米的旧结果与限制均保留。

**下一项实质科研：S86固定warp生成消费者。** 原S70同设置每链约24.6分钟已核，不按S85两秒估计生成成本。新增Gterminal：从G0真实保存最后x_tilde/CFG clean d/sigmas，按原Euler末步算术融合再解码；与G0、末端RGB合成Gpaste、多步Gguide比较。原数学推导、S70/原Euler/CFG/VAE源码核验和DeepSeek不同作者反驳已保存；正式adapter/生成合同、λ/日程/latent mask及独立评分尚待冻结，未新生成。不同作者已交付`work/S86_fixed_warp_consumer/ADAPTER_SOURCE_PLAN.md`，root核原CFG/Euler并接受最小设计；两个局部包装仍待实现，不能把设计当已接入。

创新原文岗位完成GenWarp/WAVE、DDNM/guidance-interval两有界批次并核单步对照先例；普通warp/clean融合/引导区间/末步消融不是新颖性证据。条件winner-gap界与边界/隐藏遮挡反例、终端恒等式均是数学说明。Gguide只胜Gpaste排除不了末步融合/VAE解释，胜Gterminal仍保留累计干预强度；劣于G0不报总体改善。NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false。

本轮DSH低价Flash0731一次真实返回，实际session核10903输入1099输出token；原答部分错误经源码/数学独立否决，不能当原文。UI归组HTTPError、CUA本地客户端阻断保留，未绕过。三子岗位按实质批次交付，完成不冒称继续检索。最新七项检查UTC20:31:46.439514，实际间隔30.063845分钟，超约3.831秒已如实标记并纠正误写标题。全部时间是实际动作时间，不是学生工时。以下为按各日期理解的历史记录，不覆盖本段。
<!-- S85_CURRENT_END -->

<!-- S84_CURRENT_BEGIN -->
## 当前：S84真实评分及142页完整汇报已交付（UTC 2026-09-10T19:28:11.421577+00:00）

科学结果截止UTC 2026-09-10T19:11:28.885950：S82四张历史照片真实模型预测、S83固定相机100步实际拟合、S84一次真实传感器参考评分均完成并经不同作者核验。S84固定196608网格，125708有效参考、70900缺测保留；未缩放深度MAE0.356166738→0.354967852米，平均仅降约1.199毫米。不同作者核全部196608×24及CSV，逐像素差0，均值差5.55e−17。接受单张已见参考的有限比较；最终误差仍约0.355米。17.126ms不同步、近似K、无去畸变和历史选图已见目标限制保留；不能据此认定稳健物理收益、生成改善或创新。

**已完成报告交付：** [142页连续阅读版](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/导师汇报_深入讲解第二版_2026-09-10/最新连续阅读版/完整汇报_含S84最新科研.pdf>)；SHA aca5151607878639c66237e273c168495a2ab34922c1fa3d8408b117b8658e8f。新增导航1页＋125/4/5/5/2页五原稿；141个包含页原文/数字逐页一致、尺寸相同，root核新封面和6个衔接/末页；不假称重新视觉核全部142页。S82/S83五页52文件、S84两页38文件（含全196608行数据）已复制回读；原报告、224页主账、47份CSV及旧结果均保留。核验见新目录ROOT_DELIVERY_ACCEPTANCE.json及MERGE_CONTENT_REVIEW.md。报告编制不算新实验。

**下一项实质科研：S85固定历史投影。** 从S83清理前终态，四历史12/13/18/19投到四目标20–23，保留16对及全部缺测/碰撞；双线性正足迹只定候选，硬z-buffer赢家直接取源RGB，不能叫加权颜色融合。三手算夹具和Softmax Splatting原文语义审查已完成。`work/S85_fixed_geometry_warp/ROOT_DESIGN_REVIEW.json`接受设计依据，projector源码、执行合同和独立前审仍待实施；没有真实投影/新视频。之后同warp比较G0原生成、Gpaste末端贴图、Gguide采样中引导，不以内部loss下降或与自身warp吻合代替独立收益。

Gemini Pro Extended本轮真实返回；原答/原文/数学核验已留档，拒绝机制混用、打乱保频谱和同偏移量作因果判断。三个子岗位完成实作、报告/独立核验、创新近邻与反例；完成/待命不冒称始终运行。当前NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false。下面历史段按其日期理解，不覆盖本段。
<!-- S84_CURRENT_END -->

<!-- S83_CURRENT_BEGIN -->
## S83 固定相机100步真实计算已接受（UTC 2026-09-10T18:54:40.300194+00:00）

本段优先于下方历史状态。S83于北京时间09-11 02:43:36–47真实运行，4历史缓存、原star/MST、固定共享光学P/近似K、100次Adam，一次清理；0新模型/原RGB/传感器/渲染/生成。局部FP32梯度修复后四张注册深度实际更新；边对齐参数亦训练，不能说是只调深度。初始化目标1.7617251873，最终0.0282186847，这是预测拟合目标，未证明真实几何改善。

不同作者6档案/100步记录/全部2359296个三维点位置的独立D/P/K反投影通过，max1.18054e-6；终初log-depth变化独立核字节，清理只改置信度。中间梯度仅记录摘要，loss未独立重算；不偷换为真实精度。主接受`work/S83_fixed_camera_geometry/ROOT_RESULT_ACCEPTANCE.json`，解释`S83_RESULTS.md`。

S82真实四历史raw预测与两次加载后技术失败仍完整保留，83文件快照已交付。S82/S83联合五页LaTeX增补正在编译准备，旧125页及S80/S81不变。S84已派发只读单锚点传感器参考深度前后诊断代码/合同准备，尚未新读取传感器或评分；不拟合尺度、不筛好点、保留17.126ms不同步/近似K。然后比较G0/Gpaste/Gguide，仍无新生成或已验证新方法。

创新原文岗位完成AFNet/CRC/DPS、latent非局部性和置信度/尺度反例；当前NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false。三岗位实作/独立核验/创新诊断，实际日志与流程检查同步。

S82/S83报告交付（UTC 2026-09-10T19:05:18.650652+00:00）：5页PDF已内容/全页视觉验收及复制读回，文件SHA62f7d5c99869af6062fd4e6d55f4606ef05335e217a4c5a8e66d621f370af407；用户目录`/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/导师汇报_深入讲解第二版_2026-09-10/S82_S83_09月11日历史几何增补`，附52份来源/实际数组档案，回读0错。当前S84真实评分已执行完成，另等不同作者复算，尚不在本PDF截点内。
<!-- S83_CURRENT_END -->

<!-- S82_CURRENT_BEGIN -->
## S82 四历史真实预测已接受；S83准备中（UTC 2026-09-10T18:29:35.586715+00:00）

当前真实完成入口：`work/S82_history_geometry_guidance/S82_RESULTS.md`与`ROOT_GEOMETRY_RESULT_ACCEPTANCE.json`。V3于北京时间09-11 02:25:31–43读取四张实际历史照片12/13/18/19，已有512 DPT模型eval/fresh state，一次recurrent前向保存4heads与预处理/预测相机六档案；前向加归档5.833599秒，成功尝试总11.618882秒。不同作者核全部身份/形状/字节/有限性及独立wxyz矩阵，最大差3.77e−08。只接受原始预测组件，没有公制准确性/几何对齐/新生成/创新通过。

三次实际尝试、3次模型加载、12次RGB解码、总1次前向；前两次均加载后记录程序错误，0forward，原输出完整保留。第二次回执load0/FAILED_TERMINATED为记录瑕疵，真实1加载/普通退出1已单独补记。累计监督耗时23.560855秒，不能只报最后成功成本。

成功缓存路径是`work/S82_history_geometry_guidance/execution_geometry_03/`，不是旧计划01或中间02。下一步`work/S83_fixed_camera_geometry/`按原star/MST、固定共享历史光学P/K和100步诊断准备，尚未执行真实optimizer。原fork深度梯度断连由人工张量确认；局部适配器仅人工FP32/同尺寸检查通过。近邻核AFNet/CRC/DPS等，共同一致不等于正确，贴合预测warp不等于真实收益。创新仍NO_METHOD_SELECTED/novelty_authorization=NONE/new_method_validated=false。

报告保持旧125页主文及S80/S81已交付增补；S82当前新增真实数据与本段记录，没有假称已新增PDF或视频。三岗位继续实现/不同作者审查/创新反证；任务完成或等待如实记，不以满载代替实际研究。
<!-- S82_CURRENT_END -->

<!-- S81_CURRENT_BEGIN -->
## S81 新增传感器深度评分已接受（记录UTC 2026-09-10T17:16:23.726164+00:00）

本段优先于下面的历史当前/下一步。S81实际计算于北京时间09-11 01:11:10完成：复用旧S80对应，一张真实注册源深度，0新RGB/匹配/生成/模型调用；全部24行7757记录保留，1313源点有968个有效深度。实拍2405/2647、生成3828/5110可评分；实拍各行中位1.875–8.346px，生成40.674–314.255px，生成可评分记录≤10px为0。出画有限投影也计入；未评分1524条均源深度0，不当作已知错误。target23的A0/BF仅15/42可评分，限制保留。

不同作者已从原深度和相机独立标量核全部源点/5252投影/7757记录/28配对及CSV，最大像素差3.41e-13，root全文核读独立器并接受。仅是原对应＋17.126ms不同步深度＋近似K条件下的不一致；不能唯一归因相机、确认物理对应或全图三维，也不是新方法验证。接受入口`work/S81_anchor_depth_reprojection/ROOT_RESULT_ACCEPTANCE.json`，完整表/限制`S81_RESULTS.md`，全部数据`execution_01/`。原S70–S80及125页主报告不改。

创新最近邻与实际接入：`work/S81_anchor_depth_reprojection/GENERATION_MECHANISM_NEXT_STEP.md`复核WorldForge/Latent-Reframe/Gen3C和现有VMem检索渲染与latent条件区别。下一步实施普通历史预测几何引导基线，比较原生成、末端像素合成、采样中引导；先核恰合法四历史的CUT3R几何、相机/尺度，S68仅VAE/CLIP不含预测深度，不偷用S81传感器评分深度。该生成方案尚未执行。动态杯球草案仍未满足可执行设计，创新`NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false`。

三子岗位当前分别：S81中文增补PDF；原文创新反证；下一代四历史几何输入/架构。S81增补PDF已交付（见本段下方闭合记录），旧125页已验收文件SHA29256638939c377954071b3ece6cecfbf9e4b668bdc428e9a04dab3ac916d530本轮重新核相同。实际流水与七项检查见主账，不能把自动30分钟计划当历史准点或学生工时。

S81交付闭合（UTC 2026-09-10T17:28:50.278154+00:00）：5页`S81_真实深度评分增补.pdf`已完成内容/全部页面核验，连同可编辑LaTeX、24行表、7757条原数据及协议/复核共100份文件已复制到用户报告文件夹的`S81_09月11日真实深度评分增补/`，PDF SHA6c513e8aaa8cbde1a3a448e0aa22f1feacea34c3924cccbf7dbf410fbcf5f89b。`work/S81_anchor_depth_reprojection/REPORT_DELIVERY.json`为当前交付状态，旧科学接受文件中“PDF制作中”是当时状态。

S82当前：`work/S82_history_geometry_guidance/README.md`是下一任务入口。已有恰四历史源码/输入审查、普通纯融合原型、17项人工张量检查和不同作者静态论文/实现核对；未生成新几何/warp或视频。限定缓存检索未找到本四历史，默认principal-point preset可能未赋值须实际读回，self/cross头不能混用；下一步按新合同进行一次仅四历史的512 DPT推理与已知相机/内参对齐，再比较G0/Gpaste/Gguide。三子岗位本轮任务均有落盘交付，未把等待/结束状态说成持续检索。
<!-- S81_CURRENT_END -->

<!-- S80_CURRENT_BEGIN -->
## S80真实计算与全流程审查（2026-09-11T00:09:06.159310+08:00）

本段优先于下方历史“当前/下一步”。全流程复核入口：`work/S79_workflow_accuracy_audit/ROOT_FULL_WORKFLOW_AUDIT.md`；原则v2.11仍适用，最近七项检查见`WORKFLOW_CHECK_S80.json`（北京时间09-11 00:05，距上次29.805分钟）。

S80已从“组件加载0forward”推进为真实新观察器实验：09-10 23:51实际9.513933秒，13张原评分图/13次RootSIFT/12BF/12LG神经前向/24行，无缺失。新源N1313，生成BF1171与LG3939匹配均大于10px固定请求相机残差。root不同实现独立复算7757坐标对/3655断言PASS，最大差2.274e-13；首次FP32覆盖口径错误保留并修正检查器，未改实验。它仅表明接受数增多未伴随≤10px的接受计数增加；没有单独操纵数量，仍不能排除匹配错误、覆盖偏差或固定F近似，也不能确定物理对应真值或唯一根因。`work/S80_lightglue_observer/ROOT_RESULT_ACCEPTANCE.json`及`S80_RESULTS.md`为当前接受证据。

S79六源点×三臂全18卡已实际检查，8同10异，非盲/非独立，不以16/18作准确率；旧S73/S77未修改。Perception样例metadata在23:37的一次请求curl35/HTTP000/0字节，未取得新ZIP/投影/合格样例，不能再记待获取或获取成功。失败在`work/S79_conservative_prefix/metadata_attempt01/`。

创新专职检索与数学否决：`work/S79_innovation_state_witness/`保存原文范围、两个玩具环境、iSAM2/3D-Mem最近邻。普通持久状态/后验在给定小环境已达到旧见证的风险；root额外独立核T2风险与全部16/256编码最优。仅纯数学诊断，不是真实视频收益；新机制维持NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false。

Gemini Pro Extended已通过computer use实际返回，官方RootSIFT等错误建议已核源码拒绝；本机Harness请求低价Flash0731也已真实返回，但数字抄错与因果建议已纠正，3080专栏归组HTTP失败未掩盖。外部模型不是原文、实验或验收，凭据不进入交付。

报告：原73页主文/224页主账/47CSV与331来源原样保留。第二版最终125页PDF已交付验收（52页新增深入讲解＋73页原报告，SHA29256638939c377954071b3ece6cecfbf9e4b668bdc428e9a04dab3ac916d530）；01–10章不同作者科学审查、root全新增页缩略/关键页全尺寸、全部73历史页文本对照完成，缺字/溢出/未定义引用0；目录`/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/导师汇报_深入讲解第二版_2026-09-10`。其主文科研截点23:37；同目录`S80_23点54分真实实验增补/`的4页PDF、LaTeX、全部24行CSV已独立复算及root全页可视核验。

下一步：科研回到具体对应判读与公平动态强基线失败。当前杯球设计的前端/reader尚未可执行，杯身份与当前位置语义、联合后验支持、预算和评分封存仍须修正，见`work/S79_innovation_state_witness/NEXT_DECISION_INDEPENDENT_REVIEW.md`及`NEXT_DECISION_MINIMAL_REVISION_LIST.md`；尚未启动该真实动态实验。报告已接受，阅读入口为同目录`00_从这里开始.md`和`ROOT_DELIVERY_ACCEPTANCE.json`。没有发送导师消息，没有将评分权重/算力耗时换成项目完成比例、学生工时或PhD/CCF A认证。
<!-- S80_CURRENT_END -->

## S79/S80 当前进度增补（2026-09-10T23:30:20.089650+08:00）

本段优先于下方所有历史“当前/下一步”。用户要求全流程复核，正在由root与不同作者沿proposal→数据→基线→诊断→审查→创新→报告核实；入口见`work/S79_workflow_accuracy_audit/`。原则已更新v2.11，旧版本备份保留。

S79全18项保存匹配视觉检查实际完成：显示64px局部/2倍最近邻，root和不同作者各看全部卡片后分别封存。8项同判、10项分歧；两者都没有标明显错配，但局部结构相似不证明精确中心或三维点正确。分歧原样保留，不用16/18等作准确率。原S73/S77指标未变，S77 root验收已完成（09-10记录；原09-09执行不变）。证据`work/S78_match_visual_preflight/ROOT_VISUAL_OBSERVATIONS.json`及`INDEPENDENT_RATING_DISAGREEMENT_REVIEW.md`。

S80仅完成官方固定LightGlue源与SIFT权重获取、隔离依赖及真实组件加载（UTC15:23:02–15:23:05，3.005869秒）；权重47,632,573B，全部学习参数可加载，仅无非学习confidence_thresholds缓存。**model forward=0、image read=0、SIFT detect=0**。还没有新的12对匹配实验，合同/源码/前审完成前不推理。计划让新BF与新LG共享同一份RootSIFT特征，保留全部12图对与支持分母；不覆盖旧观察器。

动态创新支线提出有条件的共同合法前缀；未知映射语义不能靠减一帧解决。sample注释投影程序V2在前审发现ZIP重复路径/特殊类型问题，V3修订待补审；截至本增补未发起sample请求、未看答案或视频。身份/容器栈本身已有强基线，新机制及跨场景确认未完成，`NO_METHOD_SELECTED/novelty_authorization=NONE/new_method_validated=false`。

导师汇报已交付73页主文与224页主账，47CSV共97829行与331来源文件；旧PDF是带日期快照，新增科研不冒充已经写入旧PDF。最新成果继续写主账和本段，课程会议/实际学生工时/导师认可未确认。

## S78 当前增补（2026-09-10T22:58:59.859520+08:00）

本段优先于下方历史当前状态。导师汇报第一版已完成：73页主文、224页原始主账、47个CSV共97829行、331份来源文件，目录 `/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/导师汇报_完整科研总结_2026-09-10`；适合零基础读者的指南和三分钟口述已写。不是新模型实验。

S77 root已于本次实际时间接受保存匹配的固定错误标签算术诊断，见`work/S77_generated_wrong_pose_control/ROOT_RESULT_ACCEPTANCE.json`。原执行日期09-09不变，A0/B主全四目标事件false，二级UNKNOWN，两个标签下生成匹配均无≤10px。不可推出完整相机错误或无效，NO_METHOD_SELECTED/novelty NONE保持。

创新原文核验见`work/S78_advisor_report_preparation/NEXT_RESEARCH_EVIDENCE_20260910.md`：官方身份/容器栈已是强规则基线；Perception Test合法cutoff仍有缺口。下一步先核source-only的18对保存匹配可视检查输入与合法前缀，未启动新的模型/视觉匹配，不重跑S70–S77。报告PDF内部的待root状态是整理快照，最新以本段及本轮增补为准。

# 当前科研记忆与接手入口

<!-- EXPERIMENT_NAME_LEGEND_20260912_BEGIN -->
> **S编号与具体试验名称说明（2026-09-12更新）**  
> 文档中的 `S86`–`S90` 是项目内部阶段编号，保留它们是为了让结果、日志和回执可以追溯；括号内是给新读者看的具体名称。编号不是论文术语、结果等级或“实验成功”的标志。S88–S90主要是数据资格/传输与协议审查，不能误读成模型性能实验。
>
> - **S86（单场景四目标几何条件注入基线实验）**：在一个已见静态场景、四个相关目标上，比较历史几何注入方式的真实生成链和RGB误差。
> - **S87（末端引导强度控制与多步引导必要性反例实验）**：复用S86缓存，比较末端处理强度与持续多步引导；它只检验该已见场景的有限反例，不验证GRC或长期几何收益。
> - **S88（RTMV相机JSON元数据与静态投影数据资格检查）**：核对归档身份、相机元数据和可访问的静态文件头；不是RGB-D配对性能实验。
> - **S89（RTMV配对数据TLS接续失败审查）**：记录两种TLS/传输接续尝试及其失败边界；失败本身不等于数据缺失或科学负结果。
> - **S90（RTMV归档配对数据恢复与索引协议审查）**：检查受限Range传输、归档成员身份、断点恢复和索引安全条件；已恢复的512B文件头不等于取得可用深度正文。
>
> 后续报告首次出现编号时应同时写成“**S86（单场景四目标几何条件注入基线实验）**”这类形式；后文可使用编号，但不要只写编号来替代试验名称。
<!-- EXPERIMENT_NAME_LEGEND_20260912_END -->


<!-- CURRENT_STATUS_BEGIN -->
更新UTC：2026-09-09T09:49:40.773114+00:00（北京时间UTC+8）。本段覆盖下方历史状态。

**最新完成：S74错误相机标签敏感性、S75五张真实历史照片的VAE解码检查，均已通过不同作者保存量复核。** S74复用638个真实匹配，固定20↔23、21↔22替代标签；四目标错误标签配对残差中位数均更大，146项独立算术通过，只说明本观察器能区分这组几何。S75真实加载一次ft-mse VAE并解码五份原缓存，实际17.499437秒；202项独立算术通过，root实际查看全五组原图/重建。匹配中位位移0.4735–0.5385px，但仅31.52–51.83%源特征有匹配，25个>10px离群点及最大480.846px保留。只削弱五历史中普遍大幅解码扭曲的解释，不证明生成latent兼容、相机正确或新方法。

报告：docs/S74_WRONG_POSE_CONTROL_RESULT.md、docs/S75_VAE_HISTORY_ROUNDTRIP_RESULT.md。原始解码、统计、独立复核和ROOT_RESULT_ACCEPTANCE在work/S74_wrong_pose_control与work/S75_vae_history_roundtrip。工作区outputs/S74_S75研究结果_2026-09-09保存76文件快照和真实照片配对；该快照中的S76是早期草案，不覆盖下述新源码。

**最新完成：S76相机相对响应单臂已结束并根审接受有限结论。** 真实执行2026-09-09T09:17:34.579246Z–09:42:04.467919Z，1469.888697秒return0，新增+5度单臂50步，沿用S70已接受A0而未重跑基线。历史顺序[19,18,13,12]、模型、相机中心、K、外观条件和实际随机流保持，重算相机后代。实际噪声/entry/50步/terminal RNG、模型元数据、条件/数组由不同作者308项核验通过。保存图像仅评分一次2.648151秒，不同作者19823项保存坐标/算术核验通过，无新模型/重匹配。

四目标M/N分别304/1281、254/1172、89/651、10/727；common C/Nc为302/1272、254/1160、88/632、6/681。全匹配配对identity−H中位53.274/51.421/38.173/5.622px，两组all4事件均TRUE，但23仅10点、5正5负，H中位102.651px，不能把插值中位为正当多数正确。root逐一看了4对原分辨率图：20/21布局相对保留，22变形模糊，23场景/构图变化严重。只支持匹配子集有限方向响应，不证明相机准确、严格H等变、未匹配区域或创新。N/Nc来自评分器记录而非独立重提特征，657匹配/650共同视野，全部尾差保留。

根审票work/S76_relative_camera_response/ROOT_RESULT_ACCEPTANCE.json SHA dfc73df22bf4d890587ad05c31223b8910fa2f1a467cef813827eecb4910f600；报告docs/S76_RELATIVE_CAMERA_RESPONSE_RESULT.md，图片visuals_01/target_20至23_pair.png与ALL_FOUR_TARGET_PAIRS.png，全为模型生成图。现无S76运行进程，不要重启已完成observer/session81333。下一最便宜对照建议：源审后用S73保存生成匹配做与S74相同固定错误标签20↔23/21↔22比较，保持分母/空值，不重生成或重匹配；仅置换S76共享局部yaw的H几乎无区分力。该建议尚未写成冻结合同或执行。动态记忆问题另需公平强基线与真实数据条件定义，不能直接把相机诊断当创新证据。

**科研工具已接通：DeepSeek Harness 0.1.2-rc.1与OpenRouter。** 既有Node24.19，127.0.0.1:3080真实认证HTTP200。项目工作区09:25:00Z通过正式API注册并在Chrome显示；凭据mode600且Git排除，禁止打印/复制state。第一次自动科研红队用V3于09:24:09.903996–09:24:33.230540Z真实返回，11514输入/687输出tokens、0工具事件，旧记录仍在Ungrouped，因为其真实cwd是子目录，禁止改写历史。用户指定以后所有DSH科研任务进入geometry-world-modeling专栏，原则v2.10已经记录；scripts/run_dsh_review.py从根目录启动并按唯一新session header显式attach，归组结果与模型返回分开核验。

第二次自动英文科研审查于09:41:58.132092–09:42:30.587362Z真实完成，32.455113秒，实际请求与返回都为openrouter/deepseek/deepseek-v4-flash-0731。记录11167输入/1153输出tokens、0工具事件；是session用量而非独立账单。session-3d41fa3c-73cb-4062-87ea-be48865e783e已正式归组，root实际UI查看并命名“创新审查 01｜事件记忆与固定预算”。root纠正模型意见中先验过度判断、要求相同selected evidence而抹掉选择干预、无提升即无信息等问题，未据模型建议改变S76。证据work/S76_relative_camera_response/dsh_event_memory_review_01/ROOT_ACCEPTANCE.json和ROOT_REVIEW_DECISION.md。原始私有state/凭据禁止打印或复制到交接。

**创新检索已进一步排除弱创新，尚未选定方法。** WorldForge/Latent-Reframe已覆盖推理相机纠正；LightGlue/selective-risk提醒匹配筛选偏差。ReMind预印本2605.25333v2和官方commit bf316a30b10f444e15adf5ddf710fa9f97e34ee9已核：事件anchor训练和历史cache替换primitive已有，所读公开5B推理用prefix/fullhistory，没有在该路径找到自动事件选择器；这不是新颖性证明。替换缓存本身调用生成器，必须计算总成本。

强基线进一步包括近期运动对+贪心覆盖+最近可靠事件anchor、任务相关后验信息选择（NeurIPS2013/2016）、RKN（ICML2019，单列训练/状态读出成本），以及BOCPD变点/分段状态过滤。协方差选择在错设静态模型下对变点前后等质量观测可打平，而预测误差不同；这是已有方法启发的符号反例，不是真实实验或新算法。IMM只核摘要/DOI，全文访问失败保留，不能说公式通读。最新各批NOTE/SOURCE_SCOPE位于work/S76_relative_camera_response/innovation_sources/dynamic_selection_adversarial_01与02，时间和缺失明确。下一研究问题应比较同eligible-history/feature/training access、同k和总compute下任务/变点感知选择能否提供额外预测信息，不给一方免费all-history摘要，不以打败错设弱基线称创新。

本轮三子agent槽分别承担创新原文检索、实现/接口和独立审查，采用实际有限批次；结束或空闲不是持续后台工作。DSH意见必须经根审和原文核验，多agent同意不提高科学证据强度。

**科学状态仍为NO_METHOD_SELECTED，novelty_authorization=NONE，new_method_validated=false。** proposal处于可信基线和失败分析；创新机制、跨场景长程确认、消融和论文贡献未完成，不按阅读批次估PhD/CCF A完成比例。S73所有生成接受匹配均>10px与共同支持92/48/6/0仍属观察器/内容/相机混杂，两个all4事件UNKNOWN不改变。M3 Max64GB，本机无远程GPU；无导师消息发送授权。

**用户指定OpenAI Harness文章已保存**到工作区outputs/Harness_Engineering_2026-09-09，共11文件。直接HTML403失败保留，官方网页读取接口正文转成离线HTML，不包含图片/脚本，不冒充原始HTML200。已审阅适用于本项目的短入口、可核验反馈和事实来源集中原则；没有把工具安装当科研创新。

关键既有证据与保护边界：

- S70完整真实生成三臂各50步，4439.151532秒，A0/A1全部latent/raw/uint8精确重放；平均MSE A0=A1 .13116666776908745，B .12528866263799618，B−A−.005878005131091268，较高几何支持A受益事件false。全16图已看；S73只复用其中旧图。原SD2.1 VAE身份UNKNOWN，使用声明ft-mse变体；目标已曝光，A/B内容顺序规范化混杂。见docs/S70_FIXED_CONTEXT_RESULT.md。
- S71全12对旧图诊断、不同作者305项算术和全8图查看完成，重复对照0位移；目标23只有3/7真参考对生成匹配，不足H估计。S72四真实对照638匹配、原Torch预处理/S68tensorSHA一致，125项独立算术完成。实际数据fr2_desk；S71引用fr1标定适用性错误已纠正，旧来源/快照保留，原近似ROS K未改。见docs/S71_FRAMING_DIAGNOSIS_RESULT.md、docs/S72_REAL_CONTROL_RESULT.md及work/S72_fixed_requested_geometry/S71_DATASET_ERRATA.md。
- B0/C1均原固定事件false，原C2 V9第二批前空检索失败，原三行协议不完整；S64单位修复是声明工程变体，不替代旧C2，不构成新方法。S66九帧已真实评分/独立复算/全图查看，主误差 .0006382446123931144、事件false，与S70不同任务指标不可比较。
- S67固定集合无selectedID/context变化；S68五历史实际CPU编码、S69 GT光学相机与原条件接口均完成且独立核验。S57旧观察器y/z翻转错误标签已撤回，不复活旧结论。S48/RAIMA完整同步数据与算力合同仍不满足；PC-DPM硬共享权重等旧方向已否决/与近邻重叠。
- 动态支线FloWM仅原代码/配置CPU准备，未实际加载权重或模型执行；Coffee Martini两流已下载校验，cam06前5秒10历史截图已看，人在操纵容器，不满足当前被动遮挡运动假设；cam00/t>=5s未看。不要称已进行动态生成实验。详细状态在本阶段保存的CURRENT_STATUS_before_S73备份与先前交接。
- 用户指定learning_research四文本及8核心外链、绘图库110文本等实际阅读范围在前轮记录；绘图库media/外链未全部查看，不能宣称所有字节通读。Supervisor handbook2.3、vibe-research-workflow、本地Claude科学批判与figure-designer用于本轮具体步骤。

最近已到期执行的流程检查2026-09-09T09:31:58.931181Z，实际间隔30.56027235分钟，真实PID/argv/监视新鲜度核后识别S76_RUNNING_OBSERVED。下一到期10:01:58.931181Z。09:01旧条目过时说明已追加勘误，原行保留。主账只经scripts/research_log.py追加，实验失败/旧协议/读取失败均保留。

本轮S76已完成，09:31检查描述的是当时RUNNING_OBSERVED；新根审/当前状态覆盖运行状态，但不倒改原检查或提前重置30分钟节奏。

<!-- CURRENT_STATUS_END -->

# 当前科研记忆与接手入口

更新UTC：2026-09-08T10:09:02+00:00；创新主线已从V2/V3过强因果语言收窄为RAIMA结果前测量候选。`INNOVATION_NORTH_STAR_V3.md` SHA `f0e5893ad4892f11f36641476f8858ca9347db4075b35b32faf5beaf4ce102aa`只定义stored∩ordinarily-selected∩addressable来源的AOIG、SEM、RCSU，`NO_METHOD_SELECTED/novelty NONE`。fresh对抗审查SHA `6482266e...4599`裁决PIVOT：Stage D只保留有限pilot；Stage C因主endpoint非唯一、8-scene低功效/无抽样框、三reference共享偏差、treatment/consumer版本、跨架构范围与计算预算而BLOCKED。新增一手碰撞SHA `91c300c4...7550`确认WorldTrace/LoopBench、ReWorld、MBench、E3C、What-If World、ICLR25 influence和ICLR26 ARC-JSD已占据宽泛addressability/回环/retrieval≠influence/3D edit/paired intervention/context attribution；只剩`ordinary-selected source × enumerated consumer × 3D support × withheld real reference`联合测量交集，仍不是首创证明。V4 source-only统计冻结包编写中。计算审计SHA `c762be65...eebe`用S40/C1真实计时外推Stage D最小1 seed约10.86小时、Stage C乐观串行36.21–56.18天；当前Stage C计算阻塞，不能事后删控制。

同轮执行状态：C1相机数值守卫V6 fresh primary仍以2 CRITICAL+2 MAJOR BLOCKED，V7 source-only修订中，未评分/未看C1像素。C2 V6 source-only回执SHA `acafa9ab...219a`已冻结并由作者/root在Python3.13/3.12隔离自测PASS，已修V5 parent PID、detached descendant和terminal publication已知问题；仍是0 prepare/attach/auth/launch/model/image/pixel，等两名非作者fresh审。S48 V6 fresh独立审查SHA `9c6900e1...f09a`给出3 CRITICAL+4 MAJOR+2 MINOR BLOCKED：replay自由scalar、localization可注入tail、reference无法证明从未conditioning，以及eligibility/valid-domain/typed sequence缺口；V7 source-only修订中，0 arm。最近七项流程实查为`2026-09-08T09:53:11.912956+00:00`，实际间隔31.044528分钟，`new_method_validated=false`。S40/C1真实生成事实和B0单行无严重事件保持不变。

更新UTC：2026-09-08T09:25:05+00:00；创新北极星V2已冻结，`work/S43_paradigm_shift_audit/INNOVATION_NORTH_STAR_V2.md` SHA `574311ced8f5bcbf2ad21854a0f7895195bc49d4fe968012d3f33bca7b662f36`。PC-DPM硬共享权重因consumer合理专业化数学反例与统一attention强基线被否决；generic stale-memory rejection/refresh又与GaME、Spatia、WorldMM、WorldCraft、SPMEM碰撞，不能单独作创新。当前唯一主线是架构受限GeoCausal accountability gap：真实检验Access–Use、Use–Location、Use–Benefit三类断裂；Interaction-Aware Provenance Arbitration只是在P0–P3全部通过后才选择的方法空间，`novelty_authorization=NONE`。独立V2对抗审查正在进行。

同轮执行状态：S48 V6四件套已经source-only冻结，主draft SHA `6611d5f803740207fcfcec44eae8f756076f0763cb3eff8349fe1065905c03a0`，V2 spec/reference/test SHA为`29014cf8...d19d2f`/`af6079dc...a5189`/`d05110ab...c89c`；作者与root分别在Python3.13/3.12各44 tests PASS，包含528个property cases与V5假Localization永久反例，但仍是0模型/0 arm/0 payload，fresh独立双审及G0/G1前不得运行。C2 V5 fresh primary SHA `8eb99073...47a7`以2 CRITICAL+2 MAJOR BLOCKED：supervisor/watchdog/worker parent PID矛盾、setsid后代逃逸却假报cleanup complete，以及terminal commit/path identity问题；V6作者修订中，0正式prepare/attach/auth/launch/generation。C1数值守卫V6 fresh primary SHA `0b30345a...eb16`也以2 CRITICAL+2 MAJOR BLOCKED：pre-lease report/receipt inode替换、审查字节与真正执行pathname脱钩、schema验证不全和攻击测试起点过晚；V7 source-only作者修订中，未盲分、未看像素。最近七项流程实查为`2026-09-08T09:22:09.241295+00:00`，实际间隔30.222700分钟，七项PASS只代表流程检查，`new_method_validated=false`。

更新UTC：2026-09-08T08:45:13+00:00；S45B C1数值相机守卫V6五源码已冻结，`FROZEN_SOURCE_SET.json` SHA `4156b62c26e57c0717914859901053fbf4967779337b4cd6d3401bd6be53d26d`，作者最终合成回执SHA `58e4b4a7431a5969be7b34f374f10c51939ac8e726f61b7721d99203d64938d0`。root已逐一重算七个文件SHA，并在Python3.13.0/3.12.14各fresh运行worker、supervisor与独立suite，六次returncode0；每个解释器分别报告合成数学PASS、50项故障/隔离检查PASS、15项独立检查PASS。证据仍严格限于source/static/synthetic：0 binding/lock/execution，0真实C1文件/tensor/pixel/model访问；下一门是两名非作者fresh V6 source review，V5票不继承。创新逻辑已另冻成`work/S43_paradigm_shift_audit/INNOVATION_NORTH_STAR_V1.md` SHA `7be61175ffa5902d1358b733fd04ab3a760094539ad721b127b12cf28aedfc8e`：推荐measurement先行的GeoCausal合同，PC-DPM仅作P0–P5全部存活后的条件方法；`novelty_authorization=NONE`。

更新UTC：2026-09-08T08:28:45+00:00；S48 V5 fresh独立统计/因果审查已经`BLOCKED`，报告 `work/S48_geocausal_kill_experiment/INDEPENDENT_STATISTICAL_REVIEW_V5.md` whole SHA `3a213ebaeec5463fe744d3aa8fc47c78edce9f5d4e63cbe6de1d16b1b4da9d93`，裁决2 CRITICAL/6 MAJOR/3 MINOR。两个决定性反例是：协议把已经除以255的RGB效应再次除以255，造成255倍单位歧义；以及跨source逐像素扣negative magnitude能把完全均匀的target direct effect雕刻成support内富集，实际8-bit合成反例仍通过原七项guard。V5原件已以SHA `b8b98ec9...767c`封存在`archive/S48_GEOCAUSAL_KILL_EXPERIMENT_PREREGISTRATION_DRAFT_v5_shab8b98ec9.md`。V6 source-only正在重写：统一uint8→[0,1]合同，Localization只用raw edit−matched-zero target effect，negative改独立veto，实现同路径dose=0、typed replay pair、strict uint8/periodic/chroma/local-shift guard，并补Benefit/reference与O-reinsert有限实现。0模型/0 S48 arm/0 C1/C2 payload；`execution_authorization=NONE`、`novelty_authorization=NONE`。最近一次七项流程实查是`2026-09-08T08:21:19.501352+00:00`，实际间隔33.464801分钟；下一目标约08:51:20Z。

更新UTC：2026-09-08T08:15:09+00:00；S47 C2 V5 source-only八文件候选已经冻结，回执 `work/S47_c2_confirmation_generation/CANDIDATE_STATIC_SELFTEST_V5.json` SHA `70487c0ee97229f8fc5d37b342181cec97e198635199d1e817ec228891126745`，测试源 SHA `cd07e502c020ac5fd74c4523213a70d6edab4a23b4f1f752e16224332dfdb683`。V5吸收V4双BLOCKED审查：prepare/authorization只接受唯一success-only终态，watchdog先于worker存在且作为直接父进程回收完整进程组，capability绑定supervisor/watchdog/worker及execution/output inode，七类科学输入从已哈希FD消费，VAE目录拒绝未知子文件，prepare/attach/auth/execution/output及祖先inode贯穿终态，runtime证据仅create-only追加。Python3.13.0与项目Python3.12.14均以`-I -B -S`通过，SIGKILL前后、SIGTERM及late descendant四类假进程探针确认无存活PID。仍是0正式gate/prepare/attach/auth/launch、0模型/科学包导入、0 C2图片正文/像素/生成；质量与创新未评估。下一步必须由两名不同非作者对精确八SHA fresh复审；双PASS前不得prepare，任何源码修改使V5回执失效。V4原件、primary `0036acc5...167c`与adversarial `03e19676...0cb1`继续保留且无V5权限。

更新UTC：2026-09-08T08:01:56.185837+00:00；S40与C1的实际本机两批生成、保存量readback和窄范围独立复核保持完成。B0主MSE `0.005278160708699555 < 0.01`，只是一行无严重差异事件；C1仍因计划yaw与ID8→ID0 c2w/K数值守卫未完成而未盲评分、未看像素，C2尚未生成。S45B V5虽有fresh primary PASS，但fresh adversarial给出3个CRITICAL并BLOCKED；V6只在source-only修macOS资源门、终态authority和逃逸后代，尚未冻结/绑定/执行。S47 C2 V3/V4双BLOCKED，V5 source-only正在修生命周期、路径身份、capability和成功终态；0正式prepare/attach/auth/launch、0模型/C2图像正文/像素。S48 V1–V4独立统计审查全部BLOCKED；V4的空间化sham反例与正负Benefit平均漏洞已推动V5。当前V5 SHA `b8b98ec9...767c`冻结：每`family×seed×sign`用`edit−matched-zero`直接pair，Localization用逐像素replay/negative control-excess，Benefit逐sign/target/replacement过门。source-only规范三SHA `a88efa8f...718de`/`2cacc5c3...359c7`/`f611e22d...7bb1`在Python3.13/NumPy2.4.6作者与root各23项synthetic测试PASS，Python3.12缺NumPy未运行；V5现正fresh独立对抗审查，仍不授权模型arm。源码静态审计只提出“slotwise latent保留、semantic embedding全局均值”的consumer-asymmetry假设，未获模型实证。`novelty_authorization=NONE`；自然失败、因果效应、收益、方法增益、创新和PhD／CCF A成果均未成立。

## 最新实质状态：C1真实生成/消费已闭环，V5数值守卫被对抗审查否决；C2与S48仍在执行前

- S43独立反方审查 `INDEPENDENT_ADVERSARIAL_SIX_STAGE_AUDIT_2026-09-08.md` SHA `e111d742...154f`。I3DM、TetherCache、Echo-Memory、CUE-R和visual evidence utility分别占据关键组件。剩余候选只是在限定架构中连接普通选择、post-selection全路径影响、干预前几何定位和独立signed benefit；单组件、组合叙事或检索未命中均不构成新颖性。
- S48 V1/V2/V3/V4原件与独立BLOCKED审查均保留。V4审查SHA `c7f55fc5...a0b4`用纯数学反例证明标量control不能消掉空间化sham，并指出正负平均`B_local`会让一侧改善掩盖另一侧损害。V5精确SHA `b8b98ec9...767c`已冻结送fresh审：直接pair、逐像素control-excess、逐sign/target/replacement门和分开的reference/common-valid域；只有C1/C2产生合格自然失败且V5/G7全部通过才可启动。
- S48静态机制审计SHA `cb68ad5e...1344`及Python3.12/3.13回执确认：`get_context_info`到`get_cond`之间存在可用干预边界，但当前返回值没有support；latent replace按slot保留，semantic path在`pipeline.py:1124`把source embeddings全局平均后广播。该不对称只是待真实干预的机制假设，不是质量失败或新方法。
- S45B V5五源码冻结SHA集见`FROZEN_SOURCE_SET.json` SHA `4be945c0...401f`，fresh primary PASS SHA `ad062bf9...55e`被fresh adversarial BLOCKED SHA `92950952...b640`否决：macOS `RLIMIT_AS`可在一次性lock后使worker未启动、seal存在替换窗口、`setsid`+关stdio后代可逃离PGID。V6只在source-only修复并扩展攻击测试；尚未冻结、binding、execution、盲评分或像素查看。
- S47 C2 V4 primary/adversarial review SHA `0036acc5...167c`/`03e19676...0cb1`双BLOCKED。共同或补充问题包括：失败prepare可被attach、success/failure授权回执并存仍被接受、capability minter/consumer范围不足、monitor SIGKILL后worker可reparent存活、科学输入/权重在哈希后按路径重开、runtime rename窗口及attempt目录身份未贯穿终态。V5须吸收两审全部问题后重新双审。
- 最近一次七项工作流实查为`2026-09-08T08:21:19.501352+00:00`，实际间隔33.464801分钟；迟到已原样记录，`new_method_validated=false`。当次检查器读取S45B V5 adversarial BLOCKED/V6 source-only、C2 V4双BLOCKED/V5 frozen待fresh双审、S48 V5 fresh review当时尚未落盘及最新顶会排重。S48 V5随后于08:27:58Z记录为BLOCKED；下一目标约08:51:20Z，不提前或回填。

- S39唯一受控加载在43.844049秒内返回0，峰值进程树RSS 17,005,658,112B；VMem、CLIP、CUT3R的missing/unexpected key为空，ft-mse VAE的missing/unexpected/mismatched/error为空。独立回执`work/S39_component_variant/loading_attempt_01/independent_loading_evidence_review.json`状态`PASS_S39_LOADING_EVIDENCE_REVIEW`、SHA `5707a2ca...e5a`。这只证明声明组件变体可加载，不证明生成、codec数值、质量或原VAE等价。
- S40实际manifest SHA `9951a789...debe` 经双审/metadata/full-resource gate后只启动一次CPU8/FP32生成。父外控2737.983865秒returncode0，采样峰值进程树RSS 25,862,127,616B；trace闭合327事件和两批历史1→5→9，第二批实际选择`[0,2,4,1]`。两份独立终态小证据审查均PASS；它们未读取tensor/image正文，只证明受控执行与元数据链，不证明位级缓存消费或质量。
- 首次受控readback `supervision_01/executed_01` 的list/tensor解析失败永久保留。v3.3的fresh `supervision_02/executed_02`随后通过独立结果复核，只在保存量消费与九帧像素身份范围成立；它不是画质或方法证据。
- B0在看图前冻结`M_outer4(ID0,ID8)`与严格`MSE > 0.01`事件。唯一技术有效盲评分得到MSE `0.005278160708699555`、PSNR `22.77517390576968 dB`，事件为false；独立复算逐位匹配，full-frame MSE `0.004389557269540995`。九帧真实PNG和contact sheet已导出并实际查看：路线结构可辨且没有黑屏/复制式/灾难性场景崩溃，但细节偏软，相机服从未获度量证明。单行不能外推长期无失败或结束三场景队列。
- S43最近邻V2含24条一手来源，扩展审计又检查VLB/MosaicMem/CaR/DreamX的后向、可访问前向和作者网络。`EXPANDED_CITATION_NETWORK_AUDIT.md` SHA `7c15c053...3907`、结构化JSON SHA `dd2549ba...5faf`；裁决`KEEP_CONDITIONAL_AFTER_EXPANDED_NETWORK_AUDIT`、`novelty_authorization=NONE`。Matrix-Game 3.5已占据3D patch provenance、几何支持、统一注意力和固定seed模块消融；MosaicMem V2只有作者主页`In Progress`信号，严格为`NOT_ASSESSABLE`。五条件联合缺口只是在明确已查范围未被推翻，不是新颖性证明。
- C1固定输入`jesus.jpg` SHA `d611976b...e1`、seed43和与S40相同的两批CPU8/FP32控制。唯一执行父回执SHA `44753718...b18`、worker SHA `5deea695...8f0`，returncode0；终态时间约18:48:33Z，外控2684.242237秒，峰值进程树RSS 24,187,961,344B，5192条monitor、327条trace、两批retained 1..8。root不独立的v2元数据审计SHA `14a31780...de1`为PASS但authorization NONE。不同作者外部执行终态审查SHA `3f185098...a09`已PASS。归档/trace审查原件SHA `64140bd6...764b`因缺监督器接口字段被阻断并保留；兼容v2 SHA `ba4425b0...c23a`经根复核PASS。没有打开归档payload、像素或图片。
- S45保存量readback已完成。root补严UTC内容顺序和实际作者隔离后，worker双审SHA `b3ddecad...6be`/`edaeb905...852`、supervisor审SHA `ff1ed145...ad0`、一次性terminal binding SHA `2645a159...85c`闭合。唯一执行外层SHA `801798bd...611`、worker SHA `54b45721...1a1`、report SHA `423e5fb8...f47`，returncode0、约3.57秒、峰值RSS205,438,976B、210项比较。不同作者结果审SHA `2b5e4bc3...ad4c`复核7199身份、102/327链和4766文件，确认ID2/4/1实际进入第二批。它只建立保存量和归档pixel身份；9个pixel body未打开、图片未查看。`requested_pose_K_guard_pass=false`是诚实缺门：身份传播不等于计划yaw及回到ID0的数值闭合。当前合法下一步是另行冻结并审查只读c2w/K守卫，通过后才绑定S46、双审评分源码、创建盲态证明并计算一次；看图必须晚于盲分封存。C2无论C1结果如何仍强制。

## 先读与长期要求

项目根目录是`/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling`；本任务工作目录`/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip`，outputs是给用户的日期快照。先读AGENTS.md、RESEARCH_PRINCIPLES.md v2.0、本文件和RESEARCH_LOG.md最新条目。阶段完整结果在docs/Sxx_RESULTS.md；当前完整交接docs/RESEARCH_HANDOFF_CURRENT.md。本次精简前的逐阶段详记完整保存在[历史记忆](docs/history/20260906T184709Z_before_S31_results/ROOT_RESEARCH_MEMORY.md)，没有删除历史证据。

用户是MSc新手，简单中文、本机自主推进、时间记录、每30分钟实查，Supervisor尤其02_Idea_Generation与本地Claude技能、多agent和原文检索。用Claude skills，不调用Claude模型/CLI。最终目标PhD深度/CCF A投稿质量，未完成，不能保证录用/导师反应。按强基线→失败→原因→方法；普通修复与已有组合不能改名作创新。没有发导师/他人消息授权。

`scripts/research_log.py.append_event`追加research_events.jsonl并渲染RESEARCH_LOG.md；补记用真实回执时间并注明记录时间。旧原件/失败/协议不改，不重复成功运行。UTC 2026-09-07T17:18:30.606513流程行错误沿用已撤回的C1 PASS，已在主账保留并纠正。修订检查器最近在2026-09-08T07:47:51.613286Z按实际间隔37.303350分钟完成七项检查并记录`new_method_validated=false`；下一目标约08:17:52Z，计划频率不冒充历史准点执行。

## 目前最关键的科学证据

| 阶段 | 实际结果及边界 | 完整记录 |
|---|---|---|
| S21/S22/S23 | 已见fr2_desk300帧CUT/TTT/FILT ATE8.254/2.848/1.858cm；278有深度配对/22缺失，完整300深度均值NA。全是已有方法。 | docs/S21_RESULTS.md–S23_RESULTS.md |
| S24 | fr1_xyz全798RGB→796配对/26.572059秒，CPU8/512DPT三法实际推理；ATE12.24063/9.68646/2.90258cm，8预定块FILT ATE较好，无灾难遗忘事件。7164行/6618pairs另式复核；图裁尖峰原FAIL保留，v2完整轴实际查看通过。 | docs/S24_RESULTS.md |
| S25 | 原VMem几何调用重放全历史并重置S/M；GA消费anchor self+后续other，不直接用raw camera_pose。state adapter60作者/92独立人工测试只是静态可用性，没做模型干预。 | work/S25_consumer_relevance/consumer_relevance.md |
| S26B | 真实新三法各400GA，原共同旧4导入历史。新4 AbsRel67.82589/93.54310/67.57302%；共同旧4已83.33823%。28行/40均值独立复核PASS。先查坏起点，不能直接归因记忆。旧focal使保存world点位变化，但0实际Surfel/cache/query事件。 | docs/S26B_RESULTS.md |
| S27/S27M | 保存量分析发现raw self不是全体GA实际输入，不准以4.4859%作公平优化起点。新1MST/3PnP/1backward/0Adam显示注册depth梯度断链；初始化与旧400终点逐位同。原断链发生在每次getter新ParameterStack；仅去detach仍不足。 | docs/S27_RESULTS.md |
| S28 | 匹配全部33初态的原A/修梯度B各真实400步；B梯度出现但AbsRel83.33823→87.47618%，loss更低。完整8行/800记录另式PASS。修getter只是恢复已知语义。 | docs/S28_RESULTS.md |
| S29 | 两零步初始化控制/2MST/6PnP/0Adam/0GT：s0=.1731799841按比例缩小全部局部深度，公共R/t相消；23检查及另一公式全786432点PASS。单位尺度不等于训练期固定尺度；S29当时未评分，S30之后评分其封存初态。 | docs/S29_RESULTS.md |
| S30 | C2t/C2a都修getter，各自33raw/深度/目标与S29逐字匹配，真实800Adam/反传、0新网络。C2t83.33823→87.47128%；C2a5.03905→42.37947%，原loss均显著下降。16行/66raw/800记录不同作者完整PASS，两图实际查看。 | docs/S30_RESULTS.md |
| S31 | 每臂一个自身初态全像素k，D*=kD400后评分。C2t84.05310%，C2a11.56681%，都仍输自身零步。8新行/2均值+原16行导入；0网络/GA/MST/backward，另式完整复核PASS。 | docs/S31_RESULTS.md |
| S32 | 固定4窗16RGB实际4model，3可用窗1200Adam；48行36评分12NA。普通k在两fr1窗接近零步，v2独立48表/1200保存日志PASS，原形状断言失败保留。 | docs/S32_RESULTS.md |
| S33 | 同S32初态普通公共pair尺度约束再1200Adam，64表旧48导入/新16；三可用窗AbsRel/RMSE/δ1均胜零步及k，绝对共同depth偏移均减小。独立64表/1200各类记录/2359296像素PASS，16照片快照完成。普通基线，不是新方法。 | docs/S33_RESULTS.md |
| S34 | 强旧4冻结，800实际Adam/反传；新4 AbsRel零步/自由/约束4.605912/4.347383/4.322076%。原map/render变化、候选全部八张同；两类独立数值与交付核PASS。普通控制，非新方法/完整视频。 | docs/S34_RESULTS.md |
| S35 | 五模块原循环记录接线准备；新人工检查3.110794秒/443.33MiB，成功与异常路径/原AST/NMS/RNG等PASS，另作者500归档载荷与133trace引用核PASS。0真模型，资源草稿仍不可执行。 | docs/S35_RESULTS.md |
| S39/S40/S42 | 声明ft-mse组件变体五件实际加载PASS；唯一两批576生成真实return0且终态元数据双审PASS。首次readback失败保留，v3.3 attempt02窄范围PASS；B0盲评分与独立复算一致，MSE .00527816，严格严重事件false。九帧真实图已导出/查看；C1/C2未完成。 | work/S39_component_variant/loading_attempt_01/；work/S40_declared_variant_generation/execution_01/；work/S40_result_readback/；work/S42_baseline_failure_preregistration/ |
| S43/S44/S45/S48 | S43六级合同只保留架构限定否证资格；Dual-Granularity Memory、Video Alchemist、Saber等又占据双记忆/per-source identity/source-aware mask，候选缩为跨consumer共享provenance+真实signed Benefit。S48 V1–V4统计BLOCKED，V5/normative包已冻结待fresh review。C1真实CPU两批生成returncode0并闭合1→5→9，终态/readback复核PASS、ID2/4/1进入第二批、九个pixel身份封存；yaw/回访c2w/K守卫V5 adversarial BLOCKED，V6 source-only未冻结，所以未评分/未看C1图。C2未生成。 | work/S43_paradigm_shift_audit/；work/S44_c1_confirmation_generation/；work/S45_c1_result_readback/；work/S45B_c1_numeric_camera_guard_supervised_v6/；work/S48_geocausal_kill_experiment/ |

S26原共同4已跑400步但独立clean参考12像素失配导致FAILED原件保留；新FP32dense参考全字节一致只许可IMPORT_VALIDATED，不追认PASS。S26B首次启动缺显式importlib.util在数组前失败保留；只补标准库bootstrap的第二次启动成功。S22原生CPU RoPE精度失败、S24原裁轴图、绘图环境失败均保留。不要把修复后的新产物覆盖历史失败。


## S34已完成的实际链条与结论

输入为已见fr2_desk首8档案，约0.235880秒，给定GT光学相机。共同旧4来自S29 C2a零步/S21原4头，新8头来自S21 cut3r档案；不同源不称前缀字节相同。旧depth0–3固定，所有8个focal仍可训练；两臂57真实初态raw/decoded/objective一致。普通getter梯度修复和尺度约束不算创新。

主生产UTC21:38:49.004084–21:40:48.662662，外控119.658477秒。真实2MST/14PnP/800Adam/800backward/4clean/806objective、0新model。共同旧packet一次与两400臂均PASS，zero取自由臂保存初態另clean，无第三MST。正式contract SHA2c51a060a294a335c3844b04dc78028bd687b724266792ea89f1a6cb597cb465。主session54299、consumer44064、独立80493均已exit0，不重轮询或重跑。

消费者UTC21:42:05.220522–21:42:18.700442，外控13.479520秒；共同493个旧Surfel只建一次，三份完整深拷贝追加。新点123/158/157，最终616/651/650；原512×288渲染可见48777/50726/50334像素。原focal缓存4→12，均值402.08610535/406.63647970/405.87696075再乘.65；同外参不等于同内参，渲染变化不是质量证据。

原票权数值变化，但三组有序候选均0–7、quota每项1，因为n=min14,k且k8。默认NMS缺原len5历史/真实latent状态，最终context未跑。相同合法缓存、相机和NMS状态下相同候选通向同条件仅为源码条件推论，不是已生成相同视频或所有后续请求无效的证明。

120文件完整终态封存21:44:22.805906；主评分实际21:44:44.835389–45.809354，首GT字节21:44:45.451549才读取。固定新4×3完整12行/3均值，每组547012有效GT、239420无效GT、0无效预测。AbsRel .046059116645085774/.04347382601427406/.04322076250691019；RMSE .23858161931309185/.23202392161346547/.23083091088459334m；delta1 .9672805089812623/.9703837623471877/.9706103051722855。

自由对零步收益.2585290631个百分点，约束再对自由仅.0253063507个百分点；index7两400AbsRel略差零步。自由pair有效log均值最大漂移.3306571869却平均深度改善，漂移本身不构成失败/遗忘。收束all-trainable伤害外推与尺度创新叙事，不继续该短窗调参。

不同作者consumer保存量与fsum票权21:44:44.832850–45.375239实际PASS；深度/raw另式核21:47:54.677414–58.014601实际PASS，12行/3均值/57共同初態/228初末raw/各800优化梯度尺度保存记录/1600尺度边界，AbsRel/RMSE差最多1.39e-17/5.55e-17。保存梯度未重新反传；地图核未独立重实现renderer或Octree，不能称物理可见性验证。完整回执和SHA见[S34完整报告](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S34_RESULTS.md>)。

最终报告bbfcd5ae6e28da63a7e2bce072a9e4b7c34059bfde83b92e52bc3460ff774c2b，22门最终表述审PASS，work/S34_independent_review/final_claim_review.json。两PNG作者和root已实际view，PDF/SVG未另渲染；work/S34_root_preparation/visual_review.json。快照/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/S34_固定旧地图三条件与真实照片_2026-09-07，220总文件/219载荷40763051B，含manifest40871308B；8原照片/12CSV/全部800各类日志/3渲染。manifest f007ad26376a9a9d5551a12e5cc4fb2a47ccccc9d1e1c971cde1fe922804b104；root219SHA、13MD仅链接改写、98链接、8原图核PASS，work/S34_root_preparation/snapshot_review.json。38大数组仅本地链接；最终表述/根QA另在ROOT，不回改封存包。

## S41当前：原VMem恢复与消费者诊断排重

资源观察UTC 2026-09-07T05:58:11.600000+00:00：官方`huggingface_hub 1.30.0 + hf_xet 1.6.0` attempt4在同一会话54832、PID8585中运行，固定repo/revision与单并发，临时文件实际2,049,463,215B；目标5,056,346,672B、完整SHA`675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4`。这只是资源传输，terminal receipt未通过前不得加载，且不启动重复下载。

独立S39接续审计裁决`READY_SERIAL_PLAYBOOK_BLOCKED_ON_ATTEMPT4_TERMINAL_SUCCESS`。成功后可直接用recovery目标；依次prepare、两名不同作者审实际core、attach、metadata gate、一次受控加载、另一作者审四份加载证据。`core_file_sha256`与规范`core_sha256`不可混用，manifest必须取attach回执实际路径。当前0冻结、0加载、0视频。

创新排重把普通mean替换、attention/router、source tag、geometry gate和点云更新全部判为已有近邻或普通baseline。只保留“冻结检索之后，单全局CLIP token是否真正影响回访，并能否把某来源影响定位到其几何支持区域”的诊断。主协议采用Gate0真实自然失败→Gate1 A0/A1→Gate2 A2–A5普通臂→必要时F00/F10/F01/F11同源图反事实；latent/Plücker置换仅为OOD绑定压力测试，不能证明通路主导。当前无方法增益，不能称创新或PhD/CCF A成果。

证据：`work/S41_vmem_xet_attempt4/S39_NEXT_STEPS_REVIEW.md`、`work/S41_clip_mean_innovation_audit/AUDIT.md`、`work/S41_gemini_adversarial_review/primary_retrieval_and_root_review.md`、`workflow_checks.jsonl`。

## S40历史：两批原流程入口准备完成

资源最新更新UTC：2026-09-07T04:43:28.864722+00:00。**原CLIP已完整下载，3,944,517,836字节及完整SHA于04:40:51通过。旧会话36631已退出0。原VMem低并发attempt3已单独启动，会话71130/PID84800，04:42:22仍活跃；临时文件当时0字节且Xet有1条TLS EOF警告，未判成功或失败。** 接续同一71130，不重启；外控总时限预计05:11:16UTC，精确终态以新receipt为准。它成功后才能冻结全部文件并实际加载。

更新UTC：2026-09-07T04:34:34.382312+00:00。**真实两批视频入口已完成源码准备和不同作者审查，尚未执行。** 保留原576分辨率、50采样步、400次几何优化和连续历史1→5→9，实际运行后还要核第二批确实消费第一批生成缓存。

正式HF认证已成功，ft-mse配置/权重已完整校验。CLIP仍为下载会话36631；04:33:01临时文件大小约2.88GB，未完成。原VMem两次传输失败均已结束，新的低并发attempt3先等待CLIP终态，不启动重复并行下载。真实加载、视频生成与质量比较仍未发生。

版本明确使用官方ft-mse VAE，原SD2.1来源仍UNKNOWN，不能称精确原版复现。继续按Supervisor强基线→自然失败→原因→方法；S38的CLIP平均问题仍待验证，新方法及PhD/CCF A质量目标未完成。

[最新准备报告](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S40_GENERATION_PREPARATION.md>)；[认证与下载记录](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S39_AUTH_AND_COMPONENT_LOADING.md>)；[完整时间账](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_LOG.md>)；[主记忆](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_MEMORY.md>)。以下旧状态按各自时间理解，不覆盖最新更新。

## S39历史与仍有效的资源记录：认证已恢复，资源与加载准备

最新接续UTC：2026-09-07T04:18:10.356553+00:00。CLIP会话36631在04:16:56工具检查仍运行，临时文件已实际写入1,140,213,633字节，未完成校验。冻结工具又经另一作者全文审查PASS；仍未执行prepare或加载。系统curl单次HF入口探测也TLS失败，未发CDN Range。下一轮先接续同一CLIP句柄，待其终态再独立恢复原VMem；不启动重复并行下载。详见[实际接续清单](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S39_auth_recovery/progress_handoff.json>)。

更新UTC：2026-09-07T04:11:35.212928+00:00。**S39官方设备认证已成功；用户亲自完成网页授权。ft-mse图像解码器的配置与权重均已完整下载并通过SHA校验。原VMem和CLIP尚未确认完整；当前没有新增模型或视频生成实验。**

原VMem第一次Xet真实传输后因重复TLS握手错误终止；官方普通HTTP第二次尝试也已明确失败，当前排查具体传输环节，不能把它们写为仍在运行。CLIP另一个下载会话36631仍存活，须接手先查其实际结果，不重复启动。旧S38的CLI401仅为历史，现在认证已解决。

独立源码审查已通过单独的“VMem + stabilityai/sd-vae-ft-mse”组件版本，并修正不完整权重加载可能被内部捕获的问题。它还不是已加载模型；原SD2.1 VAE身份仍UNKNOWN，因此不能称精确原版复现。下一步完成余下权重校验，绑定真实文件与审查回执，再尝试有时间/内存上限的真实加载。之后才是两批视频闭环、自然失败分析和方法实验。

研究仍遵循Supervisor 02_Idea_Generation的强基线→失败→原因→方法顺序；S38两agent的8篇论文学习与Gemini两轮核验已完成。保留“正确选图后CLIP平均是否损失回访细节”的待检验问题，普通加权不算创新。PhD/CCF A质量目标尚未达到。

[本轮实际记录](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S39_AUTH_AND_COMPONENT_LOADING.md>)；[模型访问现状](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/MODEL_ACCESS_CURRENT.md>)；[主记忆](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_MEMORY.md>)；[全部时间记录](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_LOG.md>)。旧封存结果保持，下面历史状态不覆盖此最新更新。

实际最近流程检查2026-09-07T03:59:36.922078+00:00，间隔27.835069分钟；下次目标04:26:36、截止04:29:36UTC。旧检查时刻不覆盖此条。

## S38历史：论文方法学习、Gemini与原资源

更新UTC：2026-09-07T03:37:44.061633+00:00（北京时间2026-09-07 11:37:44）。**S38两名agent完成8篇正式论文方法学习，Gemini Pro Extended实际完成两轮审查；没有新模型/生成实验。** 原答出现引用和架构错误，已经留原文与核验，未执行不成立的方案。优先保留“选图之后CLIP语义平均是否削弱回访内容”的诊断，普通锚点/加权不算新方法，须等真实基线和自然失败。

原VMem网页已获准，用户已明确授权，不再请求登录或同意。浏览器下载尚未观察到落盘；官方HF CLI固定revision一次401。原SD2.1 VAE身份仍UNKNOWN，具名ft-mse组件版本仅为恢复选项，未改S35原件门。真实两批1→5→9闭环、新机制、跨场景评价及最终论文演示仍未完成。

[本轮完整报告](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S38_PAPER_LEARNING_AND_GEMINI.md>)；[可读快照](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/S38_顶会论文学习与Gemini核验_2026-09-07/先读我.md>)；[模型访问现状](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/MODEL_ACCESS_CURRENT.md>)；[Gemini原答审查](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S38_paper_learning/gemini/root_review.md>)；[主记忆](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_MEMORY.md>)。已有S34/S35/S36/S37封存结果保持；下面历史内容不覆盖此最新状态。

用户已授权使用Gemini辅助和两agent学习；原则v1.6。A/B各4篇正式PDF及关键消融已读，独立引用复核另有作者。Gemini两轮有错误，root按原文/真实源码拒绝直接执行方案；不把模型选择当答案质量保证。当前proposal交付成熟度仍约四分之一（质性、非工时），阅读不替代真实创新与视频。

## S37历史：登录核验与执行取舍

S37阶段的登录/同意等待状态已经被S38更新；它曾正确记录当时限制，不是当前再次询问的理由。原报告docs/S37_RESUMPTION.md、7文件日期快照、有限复查16项回执保持。详细旧主记忆已保存到work/S38_paper_learning/current_before_update，原追加式主账保留所有历史时间。

## S36原组件来源恢复调查已完成

S36之后的锁屏检查记录已留在主账；**最新状态以本文件S39段为准，电脑现已解锁。**

更新UTC：2026-09-07T00:11:06.253294+00:00。**S36原模型来源核验完成，没有新模型实验。** 9个直接小HTTP请求均成功；原VMem作者公开渠道未找到新的正式权重入口。社区SD2.1候选和官方ft-mse发布相同VAE参数LFS指纹，但仍缺它们与原Stability SD2.1 VAE的来源连接；两配置仅版本元数据和sample_size不同，非空间分块算子关系是源码条件推断，未实测权重/输出。S35原件门和冻结材料保持。

S36当时电脑工具实测Mac锁屏，无法查看浏览器已有账号权限；该项已由后续S37解锁后的实际页面检查更新。S36当时的下一项为检查原HF模型是否已有访问；不自动申请或提交个人资料。原VMem/VAE身份齐备后，再统一补齐CLIP并冻结真实两批生成。没有新证据时，本次检索到此结束，不重复网站搜索、S35人工检查或短窗调参。

[S36报告](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S36_RESOURCE_RECOVERY.md>)；[28文件来源核验快照](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/S36_原模型来源核验_2026-09-07/先读我.md>)；[当前科研记忆](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_MEMORY.md>)；[实际时间账](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/RESEARCH_LOG.md>)。S34真实结果与S35人工接线交付继续有效，原完整视频、创新与PhD／CCF A质量目标仍未完成。

根4个新直接请求UTC00:00:23–00:01:14，共11387B；另一作者VMem5请求UTC23:55:58–23:56:55，共275331B，9请求合计286718B。另7个search queries和网页工具阅读，后台流量未知。原VMem公开16issues/1PR/20comments、Releases空、HF讨论0，没有新路线。VAE社区rev4e63672c03103b6c636b8fb4119ba982469b2955与官方ft-mse rev31f26fdeee1355a5c34592e401dd41e45d25a493发布同a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815、334643276B。两config SHA424117cb534ce03497c41305ed868980123917b2b6abba4bbaa615e968772903和92d3dfb746fca211a2c9e019e285f8597412211728dce3c5bcf4eda0f2d62e7e。

独立metadata/Git blob/源码核PASS（vae_relation_review_receipt.json）；sample_size只设空间tiling阈值，原use_tilingfalse，不能将条件性算子推断写成实测数值等同。启用tiling时576/latent72对256/32会触发、对768/96不会。社区↔ft-mse这条边不是原SD2.1 provenance，不可填VERIFIED_ORIGINAL_VAE_IDENTITY。0模型、GT、真实照片、旧预测数组、模型权重正文、重跑测试。

两处元数据筛选错误已修且留初始回执：rsync子串误命中系统sync、S20缓存误写hf_cache后实际补查huggingface-cache。CUA Mac锁屏事实见local_delta_supplement.json，现有账号权限未知。限定数据/原checkout模型名和实际cache目录未出现新原组件；不是全电脑扫描。报告SHAfd6f1939f963d378299e796aa5e013919a7c20cbfddfe06d87d72793cab144d6，28文件快照379810B载荷。下一轮若仍锁屏且无新原资源/来源，不再同网页检索或重复成功测试；按定时提示只保留必要状态检查并结束该次接续。

## S35已完成的接线准备与下一真实生成条件

最终报告见 docs/S35_RESULTS.md。五模块在 work/S35_generation_integration；原S20TraceWriter与原pipeline源码不改。原资源门绑定缺口、launcher第二阶段计时缺口已修，旧审查REVISION_REQUIRED和旧代码保留。真实运行草稿real_run_draft_not_ready.json SHAe877695b49f52d59910e141a76453ac3b13e16313535266206646dec26b5a465；未冻结、VAE身份未知，不能执行。

新人工合同e206b03c0843c9dacba4f7ba0f194b6e49346488d5b0e12a8423ae5f987b9200在UTC23:09:46.032190冻结；外控23:09:57.553586–23:10:00.664674，3.110793667秒、采样RSS464863232B、exit0，session47058已结束不再轮询。七源/三用途只首次执行，原9方法AST和Navigator配tiny两步/4×4解码模型，不是完整原网络。plain/observed像素、缓存、NMS、调用、RNG一致，计算模式/钩子恢复；成功历史1→5→9，第二批ID[0,2,4,1]，注入失败只保留首批5。源前审12门与实际运行回执均保存。

另一作者UTC23:14:44.039792–44.467441在0.427525秒内独立核560文件身份、500归档载荷、133trace引用、39/26条trace与102/83条archive事件，retainedID/阈值/模式报告/时序对应，executed_results_review.json SHA7e2c50593684789d8e58a4e340e03fcafcb051ce416b1cecd10c24c5250f7340。没有重跑测试/模型；完整RNG/对象身份/像素相等属于原测试内存断言，未独立重新执行。DRAFT实际拒绝23:06:58UTC exit2/0worker，仅验证草稿分支。全部0真照片/GT/权重/NPZ/模型/GA/原renderer。

最终报告1b8d88c979e61ee113f393a5df5321cdac7da98adfe7af350f5e723df20d447a，12项最终表述审PASS（report_claim_review.json）。[S35代码与全部人工记录快照](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/S35_原循环接线准备与人工检查_2026-09-07/先读我.md>)，589文件/588载荷35269955B，总35656833B，manifest f86a3205fc697a1635aa24489f2727d552f1fa36a31d94bc45c5ac9b038972e9；复制/26链接核PASS，work/S35_delivery/snapshot_review.json。10份交接另作者54链接核PASS；最终补快照链接与流程时点属于后续root小改，绑定current_records_final_receipt.json，原审查回执不回改。

后续不重跑成功人工检查、不补旧成功smoke、不继续短窗尺度调参。正向资源门、四模型加载、原50步/400GA、真实generated-cache消费和完整视频质量仍未执行。完整项目目标仍未完成。


本次UTC2026-09-06T22:37:32.708453+00:00纠正上轮遗漏：S20记录工具只有模块PASS、实际原循环接线与完整raw输出归档未完成（work/S20_protocol_review/trace_completion_review.json）。这两项可在不加载缺失权重时实现，当前启动S35准备，3agent分别接线/归档/源审、root负责资源门/runner。尚未集成执行或生成，不以人工检查冒充真实闭环；此前“只有外部资源可等”的判断被此具体待办纠正。

[下一决策及源码依据](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S34_next_decision/decision.md>)已接受：回到原S20两批生成1→5→9，只有实际第一批generated ID缓存被第二批条件消费，才叫闭环。原576×576/T8/50步/context4/target4/seed42，两批同worker不重播种；两次原Navigator5°转向，原NMS在len5初始化；初图作者changi，不能借用S34八帧或假latent补状态。原数学保留，S33修正不偷偷带入原baseline。

沿docs/S20_MINIMAL_VIDEO_PROTOCOL_DRAFT.md；四真实原组件齐备且加载/源码/观察器身份审定后才能另行冻结。建议CPU8/FP32、每批1800秒/45GiB是未验证预算，不是保证。主VMem与原指定VAE当前没有项目验收的完整本地资源，[最新有界资源检查](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S34_resource_refresh/report.md>)区分公开元数据、网络失败与有限本地扫描；不能说全电脑不存在或MPS/CPU必然不支持。不要反复401/环境smoke/无意义代理，不孤立下载暂无法启用的大组件以代替科研。

## 旧结果、技能与环境

S30–S33详细记忆已完整归档：[本次修改前的完整记忆](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/history/20260906T220746Z_before_S34_closure/ROOT_RESEARCH_MEMORY.md>)；逐阶段报告、原成功/失败目录和主账保持。S32/S33已完成16真实RGB新网络与累计2400Adam；S33三可用窗普通约束同时胜零步/k，缺pose窗全部NA，不能与S34混算新的独立实验。旧快照不覆盖当前主账。

Supervisor固定207bc6f7a1aa107e544099c2c7cc86816fba9628，通读59MD+70PDF页记录在既有reader目录；2.2强基线→失败→机制指导本轮反证。idea-evaluator否决已有尺度机制新颖性及短窗代理不能验证生成主张；Claude scientific-critical-thinking用于反例/焦距混杂/条件推断/证据边界；figure-designer用于完整轴与非实拍图标识。技能路径和具体应用见docs/IDEA_GENERATION_FOCUS_CURRENT.md，未调用Claude模型/CLI。

M3Max64GiB，无远程GPU；.venv-cut3r/bin/python为Py3.12/Torch2.7/NumPy1.26.4，科学CPU8/FP32，独立复算CPU1/FP64；overlay work/S17C_environment/site-packages。原512DPT3173761006B、SHA45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103，不重复下载/无理由重hash。绘图用既有HomebrewPy3.13/Matplotlib3.10.9，不改科学环境。

VMem39291e4f272f6b4f270691d930926ab5930f942e，CUT3R8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf；隔离源码work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R。原文件只读，修改通过冻结wrapper；祖先git覆盖HOME，不全量git add/commit。旧HTTP服务PID55105非实验，不动。14周proposal约前3周至第4周初交付成熟度，非工时；新方法/公平跨场景/生成闭环/最终论文演示仍缺，不标整个目标完成。


## S90一次有界网络索引真实结果（UTC 2026-09-12T07:55:51Z）

最终独立复审已通过的索引协议执行了一次冻结预算网络请求。起点12605440、Range长度512；实际结果为 HTTP 302、curl return 56、0新增正文、0新增头，重定向说明正文为1034B而本次512B上限触发 Maximum file size exceeded。checkpoint状态为 STOPPED_TRANSPORT，complete_view_ids为空，image/depth/json payloads requested均为0。现有候选Gate0仍为REJECT/DATA_NOT_AVAILABLE，未形成RGB-D配对或未来真值。此结果只说明传输边界，不是数据缺失证明、模型实验或科学负结果；不重复盲发同一请求。证据：work/S90_proxy_resumable_index/index_01/RECEIPT.json、CHECKPOINT.json、MATCHED_VIEWS.json。

## S92（保存数据未来误差尾部风险分解）：局部改善被高幅度恶化抵消

更新UTC：2026-09-12T08:14:56Z（北京时间16:14:56）。在不调用新模型、不采集新GT的前提下，对S15B保存的never/all_new预测和evaluation_gt执行固定尾部分析。四个目标的all_new MAE分别比never上升0.012776m、0.005024m、0.000979m、0.001503m；AbsRel上升0.014472、0.007696、0.005395、0.006582，但改善像素比例仍为0.5948、0.6317、0.6467、0.6459。恶化像素中最高5%的AbsRel恶化量占全部恶化量83.5%–85.5%；16×16空间块bootstrap只作为单段描述性区间。

该结果支持“少数高幅度恶化抵消多数小幅改善”的尾部诊断，可作为未来S91的风险敏感评价候选（mean AbsRel之外报告worst-5%/CVaR），但不能证明恶化来自几何风险，也不能验证GRC-Memory。状态DESCRIPTIVE_ONLY，S91仍需未见配对RGB-D、相机和固定预算。证据：work/S92_tail_risk_decomposition/PROTOCOL.md、RESULTS.md、results.json。

## S90 transport_v2（两次独立有界续接仍被传输阻断）

更新UTC：2026-09-12T08:17:50Z（北京时间16:17:50）。在不修改旧index_01的前提下，transport_v2建立独立index_02/index_03。index_02仅做不跟随重定向HEAD：HTTP302、TLS verify 0、curl18、0正文；因重定向说明体声明1034B而512B cap拒绝，未解析Location、未发Range。index_03加入ignore-content-length后：curl35、HTTP0、TLS verify 1、0正文，LibreSSL SSL_ERROR_SYSCALL，仍无Location、未发Range。两个checkpoint均STOPPED_TRANSPORT，0新header/body，complete_view_ids为空，image/depth/json payloads均为0。S90协议工程测试S90_TRANSPORT_V2_OFFLINE_PASS；停止重复RTMV请求，转向TUM/3RScan资格门。

这不是数据不存在的证明，也不是科学负结果；Gate0和S91继续阻断。证据：work/S90_proxy_resumable_index/transport_v2/FINAL_REPORT.md及index_02/index_03回执。

## S93 ALT-TUM-01（TUM RGB-D单序列最小资格检查）：部分可达但Gate0未通过

更新UTC：2026-09-12T08:22:32Z（北京时间16:22:32）。对官方TUM `freiburg1_xyz`执行小预算资格检查：完整ground-truth文本201100B、3000条位姿、约30.09秒；RGB/Depth AVI各只取65536B前缀，确认640×480 MPEG-4容器，但没有提取带原始时间戳的配对RGB/Depth PNG帧。官方格式页记录640×480、RGB 8-bit、Depth 16-bit、depth缩放5000和预配准；尚未把内参/单位绑定到实际帧，场景划分与许可仍UNKNOWN。状态GATE0_NOT_PASSED，不启动S91；下一步最多做一次帧级样本提取或转3RScan。证据：work/S93_ALT_TUM01/PROTOCOL.md、RESULTS.md、GATE0_RESULT.json。

## S93-FrameProbe 与 S94 评价合同更新

更新UTC：2026-09-12T09:14:53Z（北京时间17:14:53）。TUM帧级探针一次误用负Range语法，意外下载完整RGB AVI 8,059,298B；已标记unintended、保留失败审计、停止后续下载。Depth只取1MiB。两AVI均可解码为640×480 MPEG-4，但Depth输出8-bit RGB而非16-bit深度，时间仅为相对30fps PTS，没有可追溯TUM绝对时间戳，故不能绑定GT pose，S93 Gate0仍失败。S94独立评价合同离线通过：未来答案隔离、source identity、k=4及2/8敏感性、GPU/host/读取/选择/前向成本、mean/worst-5%/CVaR95、强基线和至少5轨迹×3查询；未运行S91。证据：work/S93_ALT_TUM01/frame_probe/RESULTS.md、receipt.json、VERIFY_FRAME_PROBE.json、work/S94_evaluation_contract_review/EVALUATION_CONTRACT.md。
## S94 ALT-3RSCAN-01（3RScan官方元数据、最小归档片段与RGB-D资格检查）

更新UTC：2026-09-12T09:19:09Z（北京时间17:19:09）。对官方3RScan仓库、文档、JSON元数据和样例ZIP头/尾执行了有界资格检查。官方资料称3RScan提供校准RGB-D、6DoF相机位姿、内参K、reference/rescan分组及跨scan变换；本机解析到478个场景组（385 train、47 validation、46 test）和1004个rescan条目。样例归档的中央目录显示两个scan，每个含51个color、51个depth、51个pose、`_info.txt`和mesh成员。

本机只取得`3RScan.json`、ZIP 512B头和65,536B尾部；没有取得完整RGB正文、16-bit depth正文、pose正文或`_info.txt`正文，尚未核验帧级同步、K具体数值、单位、深度有效率和完整许可。因此状态为`CONDITIONAL_CANDIDATE / GATE0_NOT_PASSED`，正式S91不允许启动。3RScan保留为比当前TUM更有价值的替代候选，但不等同于已获得数据或已完成实验；数据Terms流程不由agent代填。

证据：`work/S94_ALT_3RSCAN01/PROTOCOL.md`、`RESULTS.md`、`GATE0_RESULT.json`、`receipts/zip_central_directory_summary.json`、`receipts/scene_pair_summary.json`。官方来源、版本和使用条件已写入该实验结果。

## S94评价合同（固定预算未来几何风险记忆选择）

同日完成独立离线合同审查`S94_CONTRACT_OFFLINE_PASS`。合同冻结未来答案隔离、source identity全链路、主记忆槽位`k=4`及`k=2,8`敏感性、GPU/cache与host memory分列、读取字节/选择时间/前向次数、mean AbsRel、worst-5%、CVaR95、重投影误差、覆盖率、强基线以及至少5条独立测试轨迹×3个未来查询。合同要求选择进程不能读取任何未来文件，并规定Gate0、traceability、预算、公平性或尾部指标失败时停止GRC方法主张。

该合同仍是`PROTOCOL_ONLY / NOT_RUN`，不授予新颖性，也没有运行正式S91。证据：`work/S94_evaluation_contract_review/EVALUATION_CONTRACT.md`、`EVALUATION_CONTRACT.json`、`VULNERABILITIES_AND_REPAIRS.md`、`validate_contract.py`。

## 本轮证据边界

TUM S93-FrameProbe的误用负Range语法导致完整RGB AVI意外下载，已标记`unintended`并作为失败审计保留；不能把它称为合规采样或科研负结果。TUM depth解码为8-bit RGB且只有相对30fps PTS，故仍不能绑定GT pose。当前没有任何新方法、未见跨场景生成结果或GRC验证；创新状态仍为candidate/UNKNOWN，`novelty_authorization=NONE`。

## 创新前沿复核（2026-09-12）

独立创新代理核对了MemoNav（CVPR 2024）、Learning 3D Persistent Embodied World Models、Video World Models with Long-term Spatial Memory、WorldPlay、AutoScape、Spatia（CVPR 2026）、Geometry-as-context（CVPR 2026）和Latent Spatial Memory等原始论文/官方页面。结论是：泛化的“geometry-aware memory”、forgetting/informative memory、persistent 3D map、RGB-D future prediction、warp/geometry conditioning和latent spatial cache均已有近邻，单纯组合不能作为独立创新。

当前仍保留的候选问题是：在固定记忆与计算预算下，观测级校准几何风险是否能预测独立未来RGB-D/pose误差，并在完整消费者路径上超过recent/random、pose、coverage、confidence、persistent-memory和utility-only基线。审稿式潜力约7–8/10，但当前证据为候选/UNKNOWN；反事实单记忆效应潜力约7–8.5/10但数据和算力风险高；几何×外观2×2交互是可立即做的诊断，潜力约6–7/10，尚未证明跨场景规律。

本轮没有运行新模型代码，也没有把这些评分写成方法成立。报告：`work/agents/innovation_frontier_next.md`。

## 创新前沿 Round 2（2026-09-12）

第二轮审稿式原文检索进一步核对了GIM-World、C3、OUGS、Memorize When Needed、MosaicMem、HyDRA、RELIC、Mirage、Spatia和Long-Context SSM等工作。已覆盖部分包括几何长期记忆、空间检索、pruning/gating、固定容量、输出不确定性校准和闭环/重投影评价；GIM-World是最接近的部分覆盖者，但尚未看到“历史观测级校准几何风险→独立未来RGB-D/pose误差→完整消费者路径→source-level干预”的完整联合证据。

因此当前候选仍是一个可能独立的**评价问题/实验空白**，不是已成立的方法。最小可证伪实验和kill criteria已经写入`work/agents/innovation_frontier_round2.md`，包括k=4（敏感性2/8）、5条独立轨迹×3个future query、强基线、尾部指标、source identity和replay-noise控制。Gate0未通过前不运行S91。

## S95证据纠正：3RScan示例访问和时间语义（2026-09-12）

对官方仓库setup脚本的独立复核发现，`3RScan.v2.zip`被标为example data并由脚本直接wget；项目/文档又给出完整数据的Terms总规则，但未明确示例ZIP是否例外。因此此前“示例完整帧必须由用户先完成Terms”表述过强，已纠正为`sample access/permission scope = AMBIGUOUS_NOT_VERIFIED`，不提交表单，也不把许可猜测写成Gate0结果。Gate0仍因完整帧、同步、K、单位、深度有效率和pose正文未验证而失败。

3RScan的reference/rescan更安全的研究表述是“reference-to-rescan重访/变化评价”：FAQ定义reference为initial（通常最完整或first）并将其余作为rescan，论文语义涉及later point in time，但当前元数据审查没有建立精确逐scan时间戳或连续next-frame顺序，不能直接等同连续视频未来帧。

## S95 GIM-World核函数数学诊断（2026-09-12）

对GIM-World arXiv:2606.02436v1中Eq.16的平方角距离Gaussian形式做了独立数学诊断：4个大圆等间隔相机方向、位置和时间相同、sigma_r=pi时，4×4 Gram矩阵最小特征值为`-0.15846314545655754`，不是半正定核；同一局部Eq.17子集后验方差示例为`0.08703510995697616`，说明单个局部数值不一定立刻为负。该诊断与Feragen等CVPR 2015关于曲面上geodesic Gaussian一般不保持正定的结果一致，但**不是GIM-World代码复现，也不证明作者实际实现或论文实验失效**。它只提出强基线实现必须说明PSD处理或使用合法核近似。

证据：`work/S95_contract_semantics_audit/gim_kernel/RESULTS.json`、`README.md`、`run_gim_kernel_diagnostic.py`。

## S96/S97本地组件与RGB-D关联复核（2026-09-12 19:49）

S96按官方GIM高层默认与无时间敏感性设置，对4个固定位姿池共8个核矩阵执行有限谱审计；主结果均未出现低于`-1e-10`的特征值，独立NumPy/FP64复核74/74项通过，最大重建差异在记录容差内。结论只覆盖这8个保存位姿池的数值一致性，不证明GIM全局PSD、论文结果、RGB-D质量、未来预测或GRC-Memory成立。

S97原始最近邻诊断发现文件可读，但存在重复depth使用和跨GT间隔风险。随后按项目`src/tum_rgbd.py`的严格一对一规则（`|Δt|<0.020s`，唯一贪心）以及GT相邻间隔`>0.100s`建立连续支持区间并复核：fr1为792个RGB-D匹配、788个落在同一GT区间；fr2为2893个RGB-D匹配、2212个落在同一GT区间。保留帧全部640×480、RGB为8-bit RGB、depth为16-bit `I;16`且本轮无图像读取错误。fr2的681个匹配因GT支持区间规则排除，不能直接拿全序列做带GT评测。

两个序列均已参与早期开发，标记`DEVELOPMENT_SEEN`，不能作为held-out确认；本轮没有模型推理、没有启动S91、没有GRC方法验证。原S97最近邻结果保留，修正解释见`work/S97_dev_rgbd_pair_audit/S97_OFFICIAL_ASSOCIATION_CORRECTION.md`。

## S98固定窗口可行性审计（2026-09-12 20:27）

按S8冻结的8.840秒/24目标/50ms snap/GT间隔>100ms规则，对S97官方关联结果做窗口审计：fr1仅有2个合格窗口（不足三窗口）；fr2有6个合格窗口，可选0、2、5，但fr2仍是`DEVELOPMENT_SEEN`，不能作为held-out。拒绝均因连续时长不足，无snap超差或重复帧。本轮未运行模型、未读深度像素或GT位姿值；S91和GRC仍阻断。证据：`work/S98_dev_window_feasibility/RESULTS.md`、`RESULTS.json`。

## 最新研究状态：固定改写预算几何更新对照（S99），2026-09-14T14:23:37+08:00

已完成并独立验收25条件×4未来查询的100次几何消费者重投影；复用已见S15B真实模型输出，0次新增神经推理/VMem视频生成。每源固定39/196个16×16块（19.897959%），4源156块/39936源像素。这是source-block rewrite预算，不是GRC的k记忆槽位或相同改写幅度。

低不一致度平均共同域AbsRel=0.0795605800，随机20种子均值=0.0799777288，confidence_gain=0.0783648707。低D对随机3/4目标更好，但对confidence四目标均更差；delta1_all_gt=0.6612628097，也低于随机0.6644055417和confidence0.6621629832。低D worst5=0.4269007328略优confidence0.4291546159，不能说所有指标更差。按冻结规则STOP_LOW_DISAGREEMENT_ADVANTAGE_IN_THIS_SETTING，不把结果后更换指标/名字当创新。

共同域只占GT有效域55.08%–58.20%，已报告全GT正确率与coverage；固定数量≠固定幅度，来源身份与遮挡变化属于整个集合更新效应，不能直接识别单记忆因果。先冻结并封存预测、后读取已见GT评分，不宣称测试未见。

不同作者独立重写target20低D的projection/z-buffer，depth与source-ID逐值一致；GT前27检查、GT后100行及规则/聚合1896断言均通过，最大差0。root接受：work/S99_fixed_budget_risk_update/ROOT_RESULT_ACCEPTANCE.json；完整数值与边界：同目录RESULTS.md。

固定未来窗口可行性审计（S98）独立复算已完成：fr1仅2窗口，fr2 6窗口选0/2/5；fr2是旧S8重复确认，不是新增未见结果。8.840秒/24帧/50ms规则来自后续S8协议，不是原proposal逐字要求。S97两个TUM开发序列配对已审，尚缺可作独立未见确认的数据。正式S91未运行。

下一项候选：固定其它155个块的上下文，在每源39块不变时成对替换低D与confidence候选，先解决幅度匹配、背景交互、评价域和未来答案隔离；见NEXT_MECHANISM_HYPOTHESIS.md。目前是草案，未冻结/未运行。逐块空背景收益不可相加，不能当固定预算集合收益或oracle上界。SplaTAM官方固定commit代码已核，只有历史深度可作selector输入，未来查询深度只能作评分或明确oracle条件。

当前new_method_validated=false / novelty_authorization=NONE。不把局部负结果扩写成所有GRC无效，也不声称PhD或CCF A成果已成立。旧176页PDF为历史截点；本轮交付为更新Markdown、原始NPZ/JSON与复核证据，不声称PDF已改。

## S100固定上下文成对替换（2026-09-14）

在运行前审查`S100_FINAL_PRERUN_PASS`后，按冻结协议完成9对同源候选、3个来源、2个固定背景、4个目标查询的成对替换；预测封存后才读取已见GT。共144次主几何消费者重渲染，0次新增神经推理。匹配规则未放宽，未匹配来源2按设计缺失。

结果：全GT截断损失的平均收益B=low loss-confidence loss，在cap=0.5/1/2分别为-0.00000228936、+0.000000121567、+0.00000735581，接近零且随cap改变符号；36个pair-target组合中8个出现两个背景间反号（每个cap均为8）。这只说明已见消费者、有限背景和该损失下存在局部上下文依赖线索；不能证明可泛化交互、因果作用或GRC-Memory有效，也不能恢复S99已停止的低D平均优势主张。

证据：`work/S100_context_matched_swap/PROTOCOL.md`、`FREEZE.json`、`predict_01/SEAL.json`、`score_01/SCORES.json`、`work/agents/S100_final_prerun.md`、`work/agents/S100_claim_boundary.md`。下一步保持`new_method_validated=false`，进行独立封存复核并优先解决未见跨场景、真实记忆槽位预算和未来RGB-D/pose评测资格。

## S101/S103/S104远端准备与服务器核验（2026-09-15）

用户提供并授权使用的学校服务器入口为`ssh -i ~/.ssh/id_ed25519_superpod yliutz@superpod.ust.hk`。root实际只读登录返回`slogin-02`、账号`yliutz`、Python 3.10.12；显式加载`/etc/profile.d/modules.sh`后核得Slurm 23.02.6、账号`mscitspod2026`、`normal`分区及`gpu:8(S:0-1)`。两个5分钟smoke job（583967、583968）实际运行于`dgx-09`并返回NVIDIA H800 81559 MiB、驱动570.158.01；两者因可选torch打印的shell引号错误失败，但GPU探测成功，因此只接受“GPU已验证”，不接受“VMem forward已验证”。回执见`work/S101_GPU_RUN_MANIFEST.json`，私钥内容未写入任何项目文件。

S103已完成本机离线机制诊断：只读S100封存预测，72条pair-target/context记录，0新GT、0模型调用；support/identity变化稀疏，H_support/H_depth均失败，判定`MECHANISM_UNRESOLVED`。创新候选由独立审查收窄为SOCF与FGB-Future，二者仍是待证伪问题/协议，当前`new_method_validated=false`、`novelty_authorization=NONE`。正式GRC仍需合法独立held-out Gate0；GPU可解决算力，不能替代数据资格与近邻排重。

## S101后续：SuperPOD CUDA验证与ICL-NUIM候选获取（2026-09-15）

显式SSH命令`ssh -i ~/.ssh/id_ed25519_superpod yliutz@superpod.ust.hk`已验证。按HKUST官方Slurm流程，job 584006在`dgx-21`实际完成CUDA/PyTorch smoke：Python 3.10.21、torch 2.5.1+cu121、CUDA=True、NVIDIA H800、compute capability 9.0、2x2矩阵正确、峰值33,555,456B。之前两个引号错误job和一次默认identity认证失败均保留；没有运行VMem或正式GRC。

按冻结的ICL-NUIM候选，CPU job 583984完成官方`living_room_traj0_frei_png.tar.gz`下载（711,444,709B，SHA256 `4eca8c2e9f77c1bd7436c746d22ea6144b8c01fe9bc29a84e734186823f1f1ad`）。结构审计job 584045实际完成：1,509 RGB PNG、1,509 16-bit depth PNG、1,509 associations、1,508 pose rows；时间只有frame-index/30Hz规则，故Gate0状态仍`BLOCKED_TIMESTAMP_AND_EXPOSURE_AUDIT_PENDING`。官方页面和部分pose文本已在候选检索时读过，不能宣称零metadata暴露；该数据是synthetic，不能单独支撑动态实拍结论。

当前可执行GPU工作已写入`docs/GPU_EXPERIMENT_PLAN_AND_PROGRESS_20260915.md`，覆盖S0至当前旧结果清单和S102-S109（资格、跨场景VMem、k=2/4/8强基线、GRC、遮挡重访、反事实、尾部、多seed）实验合同。顶会精读近邻矩阵见`work/agents/innovation_topconf_matrix_20260915.md`；SOCF/FGB-Future仍是候选，绝不预先写成创新。定时heartbeat已根据上述真实结果更新，下一轮先完成Gate0和远端依赖，不把GPU smoke或数据下载当论文结果。

## S101环境与创新精读补充（2026-09-15）

SuperPOD依赖只读job 584098在dgx-09以1 GPU、4秒、exit0完成：torch 2.5.1+cu121与numpy 2.2.6可导入；diffusers、transformers、accelerate、cv2、imageio、scipy缺失。该事实已写入`work/agents/gpu_dependency_probe_20260915.md`，下一步补齐隔离环境并保存版本、来源、SHA和lockfile，不能把import成功当作VMem forward。

ICL pose独立审计确认官方轨迹文件1508行、8字段、首列连续1..1508且非官方定义的硬件时间戳；与包内1509条association的对齐仍需显式规则，机器决定`work/S102_gate0/ICL_NUIM_GATE0_DECISION.json`保持`BLOCKED_TIMESTAMP_POSE_ALIGNMENT`。不能把第三方loader推测当作缺帧解释，也不能在Gate0前运行正式GRC。

顶会原文精读卡已完成ViewRope与Spatia的问题、假设、算法、预算、差异和kill criteria，见`work/agents/topconf_min_experiment_cards_20260915.md`。它们收紧了“geometry-aware memory”的近邻边界；SOCF/FGB-Future仍是候选评价/机制，`new_method_validated=false`、`novelty_authorization=NONE`。30分钟heartbeat已根据584006、584098、584045及pose审计结果重写下一步，要求先Gate0与依赖复核，再按S103-S109顺序推进。

## 服务器环境复查（2026-09-15）

最新执行入口：CPU Slurm job `584449` 已提交，最近检查为 `PENDING (Priority)`。脚本 `work/S101_env_bootstrap/create_and_resolve.sh` 将创建个人 `gwm-cut3r-py311-20260915`（Python3.11）后做 CUT3R requirements 的 native pip resolver dry-run，15分钟上限、0 GPU；尚未声称环境创建或依赖安装成功。下一轮先读取该job的状态和 `/home/yliutz/gwm_env_bootstrap_20260915/` 回执，不重复提交。此任务不访问数据/GT/模型。ICL mapping清单的泛化“GT未访问”字段已纠正为实际边界：pose文本为资格审计读取，未来深度像素未读，GT未用于选择。

用户提示服务器可能已有依赖。只读核验确认 Anaconda3 `base`（Python 3.11.5）可导入 torch 2.7.0+cu126、transformers 4.48.3、accelerate 1.4.0、scipy 1.11.1、imageio 2.31.1、torchvision 0.22.0+cu126、Pillow 9.4.0 和 cv2 4.11.0；diffusers仍缺失。个人 `torch`（Python 3.10.21）缺 scipy、diffusers、transformers、accelerate、cv2、imageio；`geometry`虽在conda清单中但预期 `bin/python` 不存在。该结果修正了“服务器所有依赖都缺失”的粗略判断，但尚未证明VMem项目级import或forward可运行。下一步锁定一个环境、补齐diffusers、执行不读数据/GT的项目级import smoke，并记录版本与来源。

后续资格与环境复核显示：ICL 包内 association ID 为0..1508、pose ID为1..1508，丢弃 association ID 0 后配对子门PASS；整体 Gate0 仍因时间语义、单位、内参、坐标、split和GT隔离未完而阻断。共享 Anaconda base 在 H800 计算节点 job 584274 完成 CUDA/PyTorch/import smoke，仅 diffusers 缺失，但项目精确 NumPy/SciPy/Pillow pin 仍需隔离锁定。创新审查新增 `work/agents/innovation_falsification_matrix_20260915.md`，给出 SOCF/FGB-Future 相对强基线的唯一可辨识预测、统计门槛和淘汰用数学反例；创新仍未验证。
## 2026-09-16T00:39:01+08:00 — S102 Gate0 TUM metadata qualification completed; formal baseline still gated

修正远端 Slurm 资源配置后，H800 job 588524 成功完成 TUM Freiburg3 long office household 的元数据资格审查。归档大小 1,483,556,251 bytes，SHA-256 为 `c7cd8e1afb87c80e5744a356214819b110fa09b4744fa4ba0cc2382f9ba59e9c`；RGB 2585 行、depth 2509 行、groundtruth 8710 行，时间戳严格递增且唯一；20 ms 容差下 RGB-D 配对 2488/2585=0.962476；深度样本为 640×480、uint16、I;16。该作业只读取索引与一个深度样本，没有模型推理或未来GT评分。

科学状态仍为 `CONDITIONAL_DATA_QUALIFICATION_ONLY`：相机内参/畸变坐标系、深度单位、未来GT隔离窗、独立held-out场景和同候选池固定预算尚未全部冻结，因此 Gate0 未通过，正式 S103 VMem baseline 和 GRC/SOCF 方法实验不能开始。QOSMinGRES 原因已记录：SuperPOD 要求即使元数据作业也申请 `--gpus=1`；实际模块是 `slurm/slurm/23.02.6`。

最新预Gate线索：重影诊断发现最低RGB MSE可与高频二阶差分能量 6.7826×参考并存；SOCF-A、CVaR/DLV 仅完成封存/合成实现检查，均未证明未来收益或创新。顶会精读进一步确认几何记忆、反事实选帧和显式3D已有近邻，SOCF-A 只有在 history-only 冲突预测跨场景改善独立未来 RGB-D/pose 尾部误差时才可保留；否则降级为 FGB-Future 评价问题。当前 `new_method_validated=false`、`novelty_authorization=NONE`。

证据：`work/S102_gate0_tum/remote_receipts_588524/RESULTS.json`、`work/S102_gate0_tum/run_tum_gate0.slurm`、`work/ghosting_diagnostic_pre_gate_20260916/REPORT.md`、`work/SOCF_pre_gate_20260916/run_01/DECISION.json`、`work/cvar_dlv_prep_20260916/RECEIPT.json`、`work/agents/innovation_literature_scan_20260916.md`。

下一步：冻结并独立审查完整 Gate0 合同（内参/畸变、depth→metric z、配对、未来窗口与GT隔离、独立held-out）；通过后按预注册顺序运行 selector-free FGB-Future/S103 development baseline，再以同候选池同预算测试 SOCF-A、强基线、跨场景和尾部指标。
## 2026-09-16T00:45:00+08:00 — Minimal AGENTS/skills configuration audit

依据 OpenAI 官方 Astra 文章完成配置审查，并只做两项局部修正：将项目 `AGENTS.md` 的重复读档改为“会话开始、恢复/压缩或状态变化时完整读取；同一会话的窄任务按需读取，20分钟 heartbeat 仍执行完整检查”，并把过期的“暂无远程GPU”改为已验证的 HKUST SuperPOD H800/SSH/Slurm路径。`RESEARCH_PRINCIPLES.md` 的数据隔离、创新否决、记录和heartbeat要求保留，因为它们是用户明确的科研约束；`deep-research`、`idea-evaluator`、`tech-paper-template`、`vibe-research-workflow`的触发范围未发现需要改写的冲突。审计文档见 `docs/CONFIG_AUDIT_OPENAI_ASTra_20260916.md`。不改变任何实验结果或科学结论。
## 2026-09-16T01:01:00+08:00 — Persistent remote GPU execution rule and Gate0 contract validator

依据用户新要求，已规定所有训练或长时间GPU任务必须从远端 `tmux`/`screen` 持久会话启动和监控，并保留Slurm job ID、日志和退出状态；VPN断开只影响查看，不应停止作业。新增 `work/remote_tmux/launch_slurm_in_tmux.sh` 及说明，尚未提交正式训练。

Gate0机器可读合同 `work/S102_gate0_tum/gate0_contract_v1.json` 已生成并验证：结构检查 PASS、`reads_future_data=false`，但正式状态为 BLOCKED，九个合同部分仍缺证据（相机、深度、配对、pose、未来GT隔离、独立held-out、公平预算、checkpoint/code、独立读回）。第一次错误使用 `--contract` 参数，随后按脚本的 positional 参数重跑并得到预期 exit 2；失败已保留。故正式 S103 VMem baseline 预计在合同全部 PASS 后立即启动，当前不能宣称已开始。

创新检索agent继续发现 NeurIPS25 VideoTitans、PAGER、HSC、CVPR等近邻，SOCF-A仍须证明在匹配 surprise/uncertainty/pose/ray 控制后对独立未来RGB-D/pose尾部误差有增量预测价值；否则采用FGB-Future评价/负结果路线。
## 2026-09-16T01:08:00+08:00 — GPU start timing and innovation rotation

当前正式GPU实验仍未启动。Gate0合同验证器结构通过但正式状态 BLOCKED；剩余项为相机/深度/pose合同、RGB-D一对一完整计数、未来GT隔离、独立零暴露held-out、固定候选池/预算/配置和独立读回。若没有新的数据访问问题，预计独立审查完成后需数小时至1个工作日；合同新版本 `formal_status=PASS` 当天立即通过远端tmux/screen提交 S103（selector-free VMem development baseline）。S103基线家族和读回约1–2个工作日，正式FGB-Future/SOCF/GRC比较还需基线封存后约2–4个工作日。

创新岗位按轮次持续保留：当前 `/root/innovation_round3_counterfactual` 正在检索和设计可证伪反事实/尾部风险方向；完成后马上接替下一项有界原文或反证任务。当前仍为 `new_method_validated=false`、`novelty_authorization=NONE`。

证据：`docs/GATE0_AND_GPU_START_STATUS_20260916.md`、`work/S102_gate0_tum/gate0_contract_v1.json`、`work/remote_tmux/launch_slurm_in_tmux.sh`。
## 2026-09-16T01:16:00+08:00 — Gate0攻坚与正式GPU持久运行防护

围绕Gate0建立了逐字段证据清单、机器可读合同和验证器。当前合同结构 PASS、正式状态仍 BLOCKED；阻塞项未被猜测填充。根据远程启动器审查，新增 `work/remote_tmux/launch_formal_slurm_in_tmux.sh`：正式作业只有在远端Gate0验证器退出0且签名manifest存在时才会提交，并在tmux中记录Slurm/sacct回执；shell语法检查通过，尚未提交训练。

创新岗位已轮训到 `/root/innovation_round4_selective_prediction`，保持至少一个有界创新检索agent活动；其余岗位并行推进Gate0证据和执行审查。正式S103启动条件仍是新合同所有部分 PASS；启动后第一步为selector-free VMem baseline，不先运行GRC/SOCF。
## 2026-09-16T01:22:00+08:00 — S102 deterministic RGB-D pairing contract advanced

通过远端持久 tmux 会话 `s102-pairing` 提交 H800 Slurm job 588581，完成项目实际 matcher 的只读配对审计。2507 条候选边中接受2488条一对一配对；RGB丢弃97、depth丢弃21、已分配depth重复0；0个depth节点有多个候选、19个RGB节点有两个候选。结果已写入 `work/S102_gate0_tum/PAIRING_CONTRACT.json`，状态为 `PASS_PAIRING_ONLY`，不改变整体 Gate0 阻塞。

创新轮次已从 selective prediction 接力到 `/root/innovation_round5_mechanism_shift`，保持至少一个创新agent持续工作；当前候选仍需未来RGB-D/pose和强基线验证。
## 2026-09-16T01:31:00+08:00 — Gate0远端数据库存核对

为攻克Gate0核对SuperPOD `/home/yliutz/datasets`，当前只有已暴露的TUM Freiburg3 long-office archive和ICL-NUIM lr0；没有独立零暴露RGB-D场景。因此held-out identity仍是主要外部阻塞，不能把已有两套数据改名为盲测。相机/深度官方证据与RGB-D pairing子门已分别落盘，但整体合同仍 BLOCKED。没有读取未来GT或启动模型训练。
## 2026-09-16T01:48+08:00 — Gate0/GPU takeover update

为尽快推进 Gate0，已把两个历史含义明确拆开：**S103-GeoDiag** 是已封存的 72 条预测几何诊断，**S103-VMemBase** 才是待执行的 VMem 开发基线。Gate0 仍不是正式 PASS；当前唯一可接受的前置状态是新的真实 v2 合同达到 `PRE_RUN_READY`，之后才允许 development baseline，`POST_RUN_ACCEPTED` 仍要等预测封存和独立重算。

用户已打开的 Gemini 浏览器窗口已用于并行独立审查。Gemini 的建议与本地审计一致：拆开 pre-run/post-run，禁止用 S103 单独编号造成歧义，使用运行时/文件系统输入隔离代替 JSON 关键词扫描，dispatch 前重新计算 staged artifact SHA-256。Gemini 只作建议，未接收密钥或私有文件，不能授予 Gate0 PASS。

SuperPod 已从持久 tmux `s103-load-smoke-20260916` 提交并完成 H800 no-data model-load smoke，job **588611**，Slurm `COMPLETED|00:00:48|0:0`。回执显示 VMemModel、AutoEncoder、CLIPConditioner、ARCroco3DStereo 加载成功，23.96 秒、峰值显存 7.884 GB，权重 SHA `675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4`；`data_access=NONE`、`forward_completed=false`、无评分，不能称为 VMem 实验。完整回执已复制到 `work/S103_h800_model_load_smoke/remote_receipts_588611/`。

scene14 已有归档哈希（239153034 bytes，SHA-256 `d3011fe0c00c133b31899ed24c7bf49a00541a0c39d218c3b5647b3d781531b6`）和 frame000000 资格抽样。该样本的图像尺寸、depth zero count/max 与 pose 存在性已被读取，必须标为已暴露资格样本，不能当未见 future outcome；证据为 `work/S102_gate0_3dmatch/SCENE13_14_QUALIFICATION_EVIDENCE.json`。尚无 held-out 实验。当前下一步是完成 3DMatch source-specific adapter 与 enforced isolation 证据，再用真实文件创建并验证 `PRE_RUN_READY` development contract；`new_method_validated=false`、`novelty_authorization=NONE` 保持不变。

## 2026-09-16T02:21+08:00 — Apptainer probe does not yet unlock GPU baseline

No-data H800 model-load smoke 588611 remains the only successful GPU execution boundary. Compute-node `unshare` isolation job 588625 failed before model construction with CUDA error 304. Apptainer 1.1.9 capability flags were confirmed in 588626, but GPU probes 588659/588660/588661/588662/588664 failed at container creation or execution because the available empty/minimal sandbox could not expose a runnable bound Python environment. The probes did not read model, RGB-D, future outcome, or GT. Receipt: `work/S103_selector_free_baseline/apptainer_cuda_probe_receipts_20260916/RECEIPT.json`.

Current decision is `BLOCKED_GPU_ISOLATION_IMAGE`; do not start formal S103-VMemBase or GRC/SOCF. Next is a digest-pinned executable GPU image/rootfs or reviewed Pyxis image followed by synthetic allow/deny/escape and CUDA allocation checks. `new_method_validated=false`, `novelty_authorization=NONE`.

## 2026-09-16T02:37+08:00 — VMem transfer integrity PASS; Gate0 remains blocked

远端 `/home/yliutz/gwm_weights_20260915` 的五个必需文件已完成新一轮字节数和 SHA-256 对照，全部与本地一致。VMem 权重 SHA 为 `675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4`；完整回执为 `work/S101_env_bootstrap/VMEM_TRANSFER_INTEGRITY_RECEIPT_20260916.json`。本轮只读哈希，没有读取模型数据、RGB-D、future outcome 或 GT。

传输完整性现在为 PASS；已有 588611 no-data model-load smoke 使用同一 VMem SHA，不重复运行。Gate0 仍受 GPU 兼容隔离镜像和真实 v2 合同约束；下一步是实现审查、合同重绑定和合成 allow/deny/escape 探针。`new_method_validated=false`、`novelty_authorization=NONE`。

## 2026-09-16T02:53+08:00 — SOCF-A-v2 remains a conditional design

创新 agent 基于已验证权重和当前隔离阻塞，把 SOCF-A 收紧为一个可证伪假设：固定 VMem 预算下，用 history-only 的来源冲突特征预测替换某一来源后未来 RGB-D/pose 损失的有符号变化，并对方向不稳定样本 abstain。近邻包括 pose/redundancy retrieval、geometry/coverage selection 和 future-aware KV importance；最强竞争解释是该分数只是 pose、visibility、coverage、confidence 或 source identity 的代理。

最小实验必须等 Gate0、compute-node 隔离、selector-free baseline 和同池强基线全部完成；设计为一个合格 held-out query、k=4、一次匹配替换、3 次相同 RNG 重放、预测封存后再挂载 future scorer。任何效果不超过重放波动、被简单代理解释、方向不稳定或固定分母未来几何损失不改善，立即淘汰。当前仍为 `new_method_validated=false`、`novelty_authorization=NONE`。

## 2026-09-16T03:05+08:00 — SOCF-A-v2 adversarial confounder fixed

创新反证发现：来源替换造成的 signed delta 可能完全来自 renderer support/owner map 改变，包括 valid-pixel count、z-buffer visibility、source provenance 和 evidence density；这不是抽象风险，S99 已观察到比较条件 source identity agreement 很低且低不一致没有稳定优势。于是 SOCF-A 必须使用 SCMC 对照：同 candidate pool、k、forward count、seed/noise 和预算，并优先要求 intervention 前 target projection 的 exact support-mask equality，同时匹配 owner-count、pose distance、confidence。

若没有 exact match，必须标为 `UNTESTABLE_SUPPORT_MATCH`，不能用近似匹配冒充因果隔离。若 SOCF 与 SCMC 同步变化、效果不超过 replay variation，或被 coverage/owner/confidence 解释，立即淘汰。当前仍为设计，不运行实验。

## 2026-09-16T03:17+08:00 — SOCF-A-v2 RNG confounder added

第二个独立反证是 branch-dependent RNG：即使整数 seed 相同，来源替换分支也可能多消耗一次随机数，使 signed delta 只是执行随机性而非 source conflict。SOCF-A 必须预注册 NLPRC：冻结并 hash 初始 noise、Python/NumPy/Torch CPU/CUDA RNG states、deterministic flags、schedule、execution order、forward/output count，并在 retain/intervention 两臂前恢复相同快照；增加 byte-identical no-op 估计 replay envelope。

若 no-op 超过 envelope、locked replay 改变符号、SOCF 效果不超过预注册 95% replay noise，或 no-op 无法在同一容器执行，立即标记 `UNTESTABLE`/淘汰。当前仍不运行。

## 2026-09-16T03:29+08:00 — SOCF-A-v2 source-ID placebo added

第三个独立控制是 Source-ID Permutation Placebo（SIPP），用于区分 candidate-pool/source identity 代理。冻结每个 query 的 sealed candidate pool、source tensors/features、IDs/order、k、camera/history、checkpoint/config、完整 downstream recomputation、成本和 NLPRC snapshot，只置换 score→source-ID mapping，并在 sealed prediction 后再评分。

只有 source-aligned arm 在 support/coverage/owner 和成本匹配下超过 permutation placebo envelope，provenance 解释才保留；若效果在置换后仍存在、无法与 placebo 分离或 descendants 无法审计，立即降级/淘汰；无法运行则标 `UNTESTABLE`。当前仍为设计。

## 2026-09-16T03:40+08:00 — SOCF-A-v2 denominator audit added

第四个反证是 post-selection complete-case bias：即使 SCMC、NLPRC、SIPP 通过，若把没有 exact match、placebo 失败、abstain、invalid output 或困难 query 删除，SOCF 仍会被人为抬高。必须在 intervention/future scoring 前 hash 完整 eligible target-query universe，对 SOCF、controls、placebos 使用同一个 intention-to-treat 分母，并把所有失败保留在 feasibility ledger，标 `UNTESTABLE` 或 failure；complete-case 只能作次要分析。

若收益只在删掉这些样本后出现、各臂 query inclusion 不一致，或完整分母效果落在零/replay bounds 内，立即降级/淘汰。当前仍为设计。

## 2026-09-16T03:51+08:00 — SOCF-A-v2 claim boundary narrowed

在 SCMC、NLPRC、SIPP 和 ITT 分母控制之后，唯一可辩护的差异是 auditable source-level signed intervention estimand：history-only 预测保留/替换一个命名 memory source 后独立 future RGB-D/pose loss 的变化，完整重算 consumer，方向不稳定时 abstain。

但现有审查已指出 CUE-R、ViewRope/SplaTAM 和 cache abstention 等近邻。即使四项控制通过，若没有 residualized、跨 scene 和 horizon 重复的 held-out future geometry 增益，只能称 measurement/selection protocol；否则降级为 FGB-Future 或 negative evaluation。当前不作新方法主张。

## 2026-09-16T04:03+08:00 — SOCF decisive package frozen as future protocol

创新 agent 给出最小可区分实验，但目前不执行：Gate0、digest-pinned CUDA/container、selector-free VMem baseline、same-pool controls、合法 future scorer、2 条 calibration trajectory 和 1 条零暴露 held-out trajectory/scene 都必须先 PASS。冻结 pool/IDs/order、k=4、成本、camera、hash、conflict features、NLPRC states、abstention 和 SIPP permutations；calibration 做三次 locked F0/F1 replay，拟合 control-only 与 control+conflict；held-out 比较 SOCF、retain、SCMC、NLPRC no-op、SIPP。

使用预先 hash 的 ITT query universe 和固定 full-GT pixel denominator，所有 unmatched/abstain/invalid 保留。若效果接近 replay、符号不稳定、没有超过 controls、只靠删样本或只改善 RGB 而几何恶化，淘汰；即使通过，也先称 measurement protocol，不自动称新方法。

## 2026-09-16T04:14+08:00 — SOCF consumer recomputation guard added

创新反证发现 source swap 可能留下 stale mutable state，例如 cached latent/KV、attention/renderer buffer 或 source_pixel_identity，使 F1 并非完整 consumer recomputation。任何 signed effect 前，必须从相同 serialized pre-consumer state、fresh process 做 F0→F1 和 F1→F0，并 hash memory input、tokens/KV、attention、renderer support/owner/provenance 及最终 RGB/depth/pose 输出；要求顺序不影响结果且所有替换源下游节点重新生成或有明确 source-independent 审计。

若顺序改变输出、复用了未审计 stale buffer 或最终像素无法追溯到 frozen source IDs，立即停止并标 `INVALID_CONSUMER_RECOMPUTATION`。

## 2026-09-16T04:30+08:00 — SOCF stale-state closure reiterated

未来 SOCF 包必须先序列化 pre-consumer state，在 fresh process 中按两个顺序运行 retain/replacement，并 hash memory、latent/KV、attention、renderer support/owner/provenance 和最终输出。任何 order dependence 或 stale mutable state 都在 future scoring 前终止 estimand。

## 2026-09-16T04:41+08:00 — 不能削弱科学门；只合并行政 manifest

审查结论是 Gate0/container legality、selector-free baseline、SCMC、NLPRC、SIPP、ITT 分母和 order-reversal provenance 分别对应不同失败模式，不能删除或弱化。唯一安全简化是使用一个 immutable preflight manifest 和 shared frozen input/arm matrix，保留全部 arm、fresh-process 检查、完整分母和 `UNTESTABLE` 状态。

## 2026-09-16T04:53+08:00 — SOCF immutable preflight manifest schema fixed

未来 SOCF 仅允许使用一个 immutable manifest，包含授权/Gate0/container/baseline receipts、环境和全部 hash、ordered candidate pool、hash 后 ITT target universe 与固定分母、RNG/noise snapshot、F0/SOCF-F1/SCMC/NLPRC-no-op/SIPP arms、source→pixel provenance 与 order-reversal、prediction seal 和 future scorer receipt。所有缺失合法性、matching、provenance、replay 或 denominator 证据必须是 `UNTESTABLE_*` 或 invalid，绝不能写 PASS。


## 2026-09-16 — SOCF manifest ambiguity corrections

未来 SOCF 只有在所有 arm 输出和哈希冻结后才可写 `prediction_sealed=true`；此前 `future_scoring_permitted=false`，`PASS` 只表示所有回执齐全后的完成决策。预封存只记录 `denominator_spec_hash`，评分器完成后才写 `realized_denominator_hash`，不能把未来 GT 或实际有效像素数提前写入。SIPP 必须是只改变 score→source ID 对应关系的置换，保留 source tensor/feature/support/pose，并记录置换 seed/hash 与 arm pool hash。


## 2026-09-16 — Receipt status and pilot boundary

传输、CUDA、import 的 PASS 只属于环境证据；在明确的模型 forward Gate0 回执前，正式状态必须是 `NOT_RUN|BLOCKED`。单个 qualified held-out query 只能标 `PILOT_DIAGNOSTIC_ONLY`，不能称 protocol evidence；只有两条 calibration 加一条 untouched held-out scene/horizon 的完整包才可进入 protocol evidence。封存前只允许 `denominator_spec_hash`，评分器封存后才产生 `realized_denominator_hash`，未来 RGB/depth/pose 和实际有效像素数在封存前都不可读。


## 2026-09-16 — GPU image availability boundary

远端有 Apptainer/Enroot/Pyxis 的镜像接口，但 registry 权限、网络、配额、缓存和批准的 digest 都未知；没有拉取或批准任何镜像。正式阻塞仍是 `BLOCKED_GPU_ISOLATION_IMAGE`，不能把工具接口存在当作镜像可用。


## 2026-09-16 — 最新状态对账与正式启动门

旧心跳中的“VMem transfer partial”已被更新回执覆盖：`VMEM_TRANSFER_INTEGRITY_RECEIPT_20260916.json` 显示五个文件本地/远端 SHA 全部一致，当前是 `COMPLETE_SHA_VERIFIED`，不要重复传输。588611 只是无数据 model-load smoke，不能重复，也不是 formal forward。

正式 Gate0 仍是 `BLOCKED`，GPU 隔离是 `BLOCKED_GPU_ISOLATION_IMAGE`。即使未来 validator 返回 `PRE_RUN_READY`，正式启动还要有 `formal_launch_guard_receipt`，把 validator 结果、sealed manifest SHA、guarded wrapper、Slurm 脚本、run ID 和执行边界绑定起来。当前不能运行正式 S103、评分、GRC 或 SOCF。


## 2026-09-16 — Formal dispatch guard software closure

本地正式启动 guard 已补齐并通过 8/8 software-only 回归：tmux 成功后原子保存 `gwm-formal-launch-guard-receipt-v1`，绑定 validator 回执、manifest/contract/protocol、Slurm/generic launcher、predictor wrapper、execution boundary、run ID/scope 和精确命令。这个修复只关闭启动记录缺口，不等于 GPU 镜像、计算节点隔离、PRE_RUN_READY 或科学实验已经通过；没有提交远程 formal launch。


## 2026-09-16 — FGB-SI distinction narrowed by primary-source review

**Design-only candidate:** FGB-SI (source-intervention future-geometry measurement) estimates the signed effect of retaining versus replacing one named history source on an externally supplied, held-out future RGB-D/pose state in a fixed commanded coordinate frame, with complete consumer-descendant recomputation and source-to-pixel provenance.

Closest occupied mechanisms include ReWorld pose-indexed bounded memory/redundancy retrieval, Future Forcing future-aware KV selection/merging, and WorldRoamBench geometry/retention metrics. Generic future-aware fixed-budget memory or KV importance is therefore not a novelty basis. The scoped distinction is the auditable named-source intervention plus externally supplied, held-out future RGB-D/pose reference and provenance.

Falsify if the effect adds no held-out future value beyond pose/coverage/confidence/utility, disappears under source/common-bias controls or registration checks, cannot be traced to external geometry, or appears only in one scene/horizon. If so, retain FGB-SI only as a negative/evaluation protocol. No experiment or novelty validation is authorized.


## 2026-09-16 — FGB-SI pose wording correction

创新候选不能把当前 3DMatch 的 mapping-estimated pose 写成独立真值。统一改为“externally supplied, held-out future RGB-D/pose reference”；只有另有独立传感器/参考系证据时才使用 independent。


## 2026-09-16 — Formal launch receipt 的边界

`gwm-formal-launch-guard-receipt-v1` 的 `PASS` 只表示软件 dispatch guard 成功创建 tmux 并保存绑定回执，不表示 Slurm 已完成提交、predictor 已执行、计算节点隔离已通过或已有科学结果；还必须等待下游 worker/Slurm 回执。


## 2026-09-16 — 启动 guard 回归加强

本地 software-only 回归现在是 9/9：成功 fixture 会检查 formal receipt 的关键字段关系、实际 SHA、run/scope/session/path/命令、execution boundary，以及嵌入 validator 的 `PRE_RUN_READY` 和空 errors；修改 wrapper 文件也会被拒绝。仍然没有远程 formal launch 或科学实验。

## 2026-09-16T13:53+08:00 — S103 精确边界通过，Gate0 仅剩独立审查

`S103-VMemBase-scene13-w001-v1` 已冻结一个明确暴露的 development window（history 0/15/30/45，command/target 60/75/90/105）。预测侧 13 个输入、评分侧 12 个未来引用、188 个源文件、运行配置、四组模型权重、预测器/评分器/复核器和 digest-pinned SIF 都有精确哈希绑定。

持久 tmux 经 Slurm 运行了两次不加载模型、不做 forward、不打开未来 outcome 的精确隔离探针。589823 技术通过但容器清空环境导致回执缺少作业号，完整保留为失败的 provenance 尝试；修正后 589826 在 dgx-09 以 `COMPLETED|0:0|00:00:25` 通过，并在单个回执中绑定 job ID、窗口/运行时/评分清单/预测器 SHA。13 个允许输入和 188 个源文件及全部权重逐字节验证，stage/source/weights 只读，project/dataset/未来路径不可见，H800 CUDA matmul 通过。该 PASS 只属于技术边界，不是科学结果。

新 `GATE0_CONTRACT_CANDIDATE_v4.json` 的校验结果仍是 `BLOCKED`：216 个非审查 artifact 全部验证通过，唯一实质缺口是 3DMatch adapter 的独立接受和不同作者对冻结 protocol 的预运行批准。不得自签，不得在两项真实审查前启动 VMem forward、评分、GRC 或 SOCF。`new_method_validated=false`，`novelty_authorization=NONE`。

## 2026-09-16T18:43+08:00 — 内参一致性缺陷修复并重新冻结 v5

静态审查发现旧 predictor 将 history K 在拼接后重复减去一次 x=96，同时 query K 用 `K0*1.2` 缩放了整个 3×3 矩阵，使齐次元素从 1 变成 1.2。该错误会令 history/query 相机条件不一致，因此旧 v4、runtime v1 和隔离 job 589826 全部降级为已归档 superseded evidence，绝不能用于正式 forward。

新 predictor 使用唯一 `model_grid_K`：仅缩放前两行一次、仅裁剪一次，并在运行时验证八帧 K、主点和齐次行一致。新 SHA `534fd553...`；10/10 静态回归通过。runtime v2 SHA `732c2225...`；精确隔离 job 590696 在 dgx-27 以 `COMPLETED|0:0|00:00:49` 通过，回执 SHA `dc69ee8c...`。新 v5 contract SHA `f0597ad5...`、protocol SHA `bfc3e843...`，验证 216 个非审查 artifact 后仍只缺 adapter 独立接受和不同作者 protocol 批准。没有模型 forward、未来 outcome 访问或评分。

## 2026-09-16T21:44+08:00 — Supervisor 审查发现 all-8 相机中心化缺陷，v6 取代 v5

按 Supervisor-Skill 的小步验证原则复核官方 VMem 调用后发现，v5 predictor 只对四个 history C2W 做中心化，再把四个原始 query C2W 拼入；官方 pipeline 是先拼接 context+target 八个相机，再统一中心化和缩放。该缺陷会破坏 history/query 的共同坐标框架，因此 v5/runtime v2/job 590696 均降级为 superseded evidence，不能用于 forward。

新 predictor 先拼接全部八个 C2W，再调用官方 `get_translation_scaling_factor`，并运行时验证全部成对相对平移在共同中心化前后保持不变。predictor SHA `75af8cad...`，12/12 静态检查通过。runtime v3 SHA `7b635f37...`；精确隔离 job 591500 在 dgx-21/H800 以 `COMPLETED|0:0|00:00:30` 通过，回执 SHA `d3152f12...`，无模型加载/forward/未来 outcome 访问。

同时加固 Gate0：适配器与 protocol 审查必须包含不同作者身份、非空 findings 和明确 limitations；先绑定 adapter review 再计算最终 protocol SHA，任何预先批准的 base SHA 都会被拒绝。v6 base contract SHA `f866ce3d...`、base protocol SHA `b2ca7239...`，验证 217 个非审查 artifact 后仍只缺两项真实独立审查。正式 bundle v3 的负控制正确拒绝创建。若审查者立即可用且无新问题，预计 60–120 分钟可到 `sbatch`；Slurm 排队时间另计。没有真实审查者时启动日期未知，不得自签。

## 2026-09-19 源码核查：T1-5 的原生记忆版本在可行性上已关闭；位姿指标归属需更正

外部研究简报返回后，两条可在固定源码上直接核查的主张已核实。**两条都不利于本方。**

### 一、不存在合法的相机重标注接口——T1-5 的原生版本无需 GPU 即被关闭

固定源码中对 `self.c2ws` 的**全部写入**只有两处：`initialize` 的 `self.c2ws = [c2w]`（180 行），
以及生成循环里的 `self.c2ws.append(target_c2ws[j])`（1297 行）。**没有任何 setter、mutator 或公开方法
可以修改已存储的相机**；类名下以 `set|update|relabel|replace|correct|edit|assign` 命名的方法一个都没有。
另核实 `reset()` 不清除 `self.c2ws`——与 `initial_threshold` 泄漏同一模式。

后果：把"用支持的估计位姿替换已存生成帧的命令标签"送进**原生**的 surfel 构建与检索路径，
在不修改上游源码的前提下**无法实现**，而"不修改上游源码"是本项目的 FIXED 约束。

因此 **T1-5 的原生记忆反馈版本按可行性关闭，零 GPU 成本**。仍可实现的是绕过版本：在自建 harness 里
给同一组四张图供不同相机。但按外部审查的明确措辞，该版本只能证明**上下文相机元数据效应**，
**不能证明原生 surfel 累积或检索是因果中介**。原提案的机制主张不被绕过版本继承。

### 二、`pose_metric_cameractrl.py` 的协议归属写错了

该文件声称遵循 CameraCtrl（arXiv 2404.02101），并实现 `normalize_by_furthest`（最远帧归一化）。
但经核实的协议分布是：**CameraCtrl 用首两帧位移定标**；**CamCo（arXiv:2406.02509）与 CamI2V
（arXiv:2410.15957）才用最远相机归一化**；CameraCtrl II（arXiv:2503.10592）用拟合轨迹对齐；
SANA-WM（arXiv:2605.15178）与 Matrix-Game 3.5（arXiv:2608.29910）用 Umeyama Sim(3) 对齐。

所以本方实现的是 **CamCo/CamI2V 约定，不是 CameraCtrl 约定**，文件名与 docstring 均属误标。
"CameraCtrl-style" 只能作族标签，不能作可复现规格。该评价器从未产出任何数字，故无需撤回结果，
但在使用前必须改正归属并写明完整约定（位姿表示、参考来源、规范消除方式、误差单位与聚合、
支持集、失败处理、退化条件）。

### 三、该指标族的占据结论

位姿评价器本身是既有族的**标准实例**，非新颖：MotionCtrl、CameraCtrl、CamCo、CamI2V、Cavia、
CameraCtrl II、WorldScore、CamVerse、SANA-WM、Matrix-Game 3.5，以及被借用的 TUM ATE/RPE、
Zhang & Scaramuzza 对齐理论、KITTI 分段漂移。

原 Part 3 的四个门问题中，**三个已被占据**：生成域重建资格审查（PDI-Bench、SysCON3D）、
失败率保留在分母（CamCo、Cavia、CameraCtrl II、SysCON3D 的 attempted-set）、
生成静态区是否容许单一刚体相机（**SGC arXiv:2603.19048 直接对应**）。
仅"经校准的、生成图特定的位姿可识别性契约"仍为 `UNVERIFIED`——**这是检索限制，不是已确立的开放缺口**。

`new_method_validated=false`；`novelty_authorization=NONE`。

## 2026-09-19 自杀式核查：horizon 符号反转塌回已占据的轴

昨日几何评价器资格审查的副产物——检索相对固定偏移的优势随目标位置从 **+2.950 dB 摆到 −0.321 dB**、
跨越零点——本方曾把它列为轴 (d)（查询侧）上唯一活着的线索。**今天用已封存产物做零生成 CPU 分析，
自行否决。**

**第一步排除"离得近就好"。** 检索臂的最近上下文帧永远比 static 近**正好 10 帧**（检索取 bank 末端
+55，static 取 +45），在 +60/+75/+90/+105 四个位置上 gap 优势恒为 10。**恒定的距离优势不能解释
一个跨零的 3.3 dB 摆动。**

**第二步看上下文跨度，故事就出来了。** 检索臂跨度在 10/12 个窗口是 **10 帧**（聚簇在 bank 末端），
static 恒为 45 帧。两个检索跨度同为 45 的窗口（scene_14 w150、w200）在远目标**仍为正**
（+1.624 / +0.760）；跨度为 10 的窗口多数转负。**符号反转只在 6/14 窗口发生，不是普遍现象。**

**结论：该观察分解为两个已知效应——邻近优势（近目标帮助大、远目标边际递减）与聚簇劣势
（跨度 10 vs 45）。后者正是 Context as Memory（arXiv:2506.03141）占据的 FOV+Non-adj 结果。
所谓"符号反转"是这两者的交叉点，不是新问题。** 该线索关闭。

意义不在结论本身，而在成本：**这是第五个候选，也是第四个在花任何 GPU 之前死掉的**，
且是本方自己在约二十分钟 CPU 分析内杀掉的，没有等外部审查。

候选死亡台账：GRC/SOCF-A/FGB-SI（顺序错误，自杀）· 重复槽位修复（**跑完，−0.016 dB**，实验）·
T1-5（无重标注接口，源码）· lineage 融合（代数退化，外审提出本方验证）· horizon 符号反转（塌回已占据轴，自杀）。

`new_method_validated=false`；`novelty_authorization=NONE`。

## 2026-09-19 轴图与诊断更正：我的"四个候选同轴"是错的；查询侧在源码中被双重混淆

### 一、对本方诊断的三条更正

**1. "四个提案攻击同一条轴"——错。** T1-5 是相机标签重写,**那是对"图像内容与其相机条件化之间关系"的干预,属于轴 (b) 条件化表示或 (f) 几何—生成耦合,不是源选择**。它的失败确立的是**接口不可用**,不是选择轴上的又一个负结果。

**2. "该轴已饱和"——范围过宽。** 四次失败分别是:在确立消费者响应性之前就提方案、一次失败的局部干预、一个不可用的接口、一个冗余参数化。它们**强烈指控本项目的方法发现流程与所选干预边界**,不确立一般性的性能上限。

可辩护的表述是:**"在这个 pinned 消费者上,仅做选择的研究已耗尽其当前的证据正当性——不是耗尽其数学上可能的改进。"** 停这条线不需要一个普适的饱和定理。

**3. 代数结论既更强也更弱。** 更强:**给定精确的 q 与 D,共同目标平方误差矩阵对该融合目标零额外信息**。更弱:它**不**确立加权效应小、不确立估计 q 容易、也不确立非线性生成器不能对不同证据产生大响应。**参数充分性不是可达性能的上界。**
同理,对 `c·11ᵀ` 的不变性只说明**改单纯形权重不能处理该共模分量**,不说明改生成器对输入的变换不能处理。

### 二、新核实的源码事实:查询侧干预被双重混淆

在 pinned 源码中(不只公开 main):

```
1249:  get_context_info(target_c2ws, ...)                  ← 目标位姿驱动检索
1263:  all_c2ws = torch.cat([context_c2ws, target_c2ws])
1265:  get_translation_scaling_factor(all_c2ws)            ← 归一化作用在拼接上
```

**改变目标会同时改变(a)检索到哪些帧,与(b)相机归一化尺度。**任何查询侧干预在归因给"联合查询计算"之前,必须先控制这两条路径。

### 三、轴图(占据状态,引用已逐条核实标题)

| 干预点 | 状态 |
|---|---|
| (a) 证据读取 | **OCCUPIED**(Context as Memory / VRAG / COVRAG),本方的共同目标平方误差融合**额外代数受限**。项目层面 **NO-GO** |
| (b) 条件化表示 | **OCCUPIED**(EscherNet 2402.03908、PRoPE 2507.10496) |
| (c1) 持久状态表示 | **OCCUPIED**(VMem 索引视图记忆、GEN3C 几何缓存)。换数据结构本身不是机制主张 |
| (c2) 状态写入与修订 | **广义 OCCUPIED**,但与读取不同。只准入/排除帧的写策略会塌回 (a) |
| (d) 请求视图分解 | **OCCUPIED**(Flexible Diffusion Modeling 2205.11495、SEVA 2503.14489 已用 anchor-first 与目标分块) |
| (e) 跨调用转移动力学 | **OCCUPIED,但代数未穷尽**(Self Forcing 2506.08009、Stable Video Infinity 2510.09212) |
| (h) 调用内推理动力学 | **OCCUPIED**(Diffusion Forcing 2407.01392、History-Guided 2502.06764、Equilibrium Forcing 2608.14706) |
| (f) 几何—生成耦合 | **广义 OCCUPIED**(GEN3C、Voyager 2506.04225、FantasyWorld 2509.21657) |
| (g) 测量与评价 | 被 owner 要求的贡献类型排除 |

**(d) 与 (e) 都不比 (a)–(c) 更少被占据**;本方此前的印象来自未检索。

### 四、唯一值得表述的对象(未获授权)

**选择性有限视界误差增益训练**:在**固定证据读取图**的前提下,训练生成器在后续若干次调用上衰减**可识别的、保场景的**缺陷,同时保留对真实场景信息的敏感性。它改的是 G_θ,不是检索策略或前置加权头。

它绕开了杀死 lineage 的那个代数塌缩,理由已验证:`A₁=diag(2,¼)`,`A₂ᴬ=diag(2,¼)` 给 `‖A₂ᴬA₁‖₂=4`,而 `A₂ᴮ=diag(¼,2)` 给 `0.5`——**单步奇异值谱完全相同,两步增益差 8 倍**。故跨调用对象不能约化为四个单帧风险加同调用特征距离。

但它**远不充分**:无穷小各向同性扰动下该损失退化为 Jacobian 正则化;而"在自己生成的历史上训练"被 Self Forcing 占据,"注入并学习自身特征误差"被 Stable Video Infinity 占据,"使扩散生成收缩"被 Contractive Diffusion Policies 占据,"控制学习型递归系统的扰动敏感性"被 R2DN 2504.01250 占据。
**仅存的可能区分是三者的组合:选择性噪声方向衰减 + 有限视界生成历史传播 + 保留场景判别性记忆,且在固定证据边界上演示。占据状态:UNVERIFIED。**

### 五、裁定

**没有任何方向同时满足"离开轴 (a)、未被占据、代数非退化"。800 GPU-hours 的额度维持撤回。**

障碍被分解为三个不同成分:**旧约束确实是真实障碍**(冻结消费者把可实现的想法都逼向操纵证据);**pinned 消费者对特定干预仍是障碍**(相机接口不可用、两次局部上下文改动效应微弱),但这不确立其可训练转移缺乏可控传播模式;**子领域拥挤,但未确立穷尽**。

owner 的资金选择是:**在可训练递归转移上做一次明确不确定的方法发现**,还是**结束这条线**。不是在 lineage 融合与另一个已合格的顶会点子之间选。

`new_method_validated=false`;`novelty_authorization=NONE`。

## 2026-09-19 轴 (e) 占据核查:唯一幸存方向的门关上了

Astra 把"选择性有限视界误差增益训练"的占据状态标为 UNVERIFIED,并指出唯一可能的区分是三者合取:
(i) **选择性**方向衰减(压某些方向、**刻意保留**另一些) (ii) 在**模型自身自回归 rollout 的有限视界**上度量
(iii) **场景判别敏感性被保留且被验证**。我自己先跑了这个检索,**结果是负的**。

### 关门证据(摘要已全文读过,逐条对 (i)/(ii)/(iii) 判定)

**2606.14732 Steady-Forcing(训练型)——单这一篇就足以关门。**
> "mechanisms that improve spatial stability **tend to suppress motion**... we study this **stability–motion trade-off**... preserve background identity **while sustaining** plausible fluid dynamics over multi-minute autoregressive rollouts"

(i) ✅ 这个 trade-off **就是**选择性,且被当作核心问题陈述 (ii) ✅ 多分钟自回归 rollout
(iii) ✅ **且配了专门的测量**:他们指出 VBench "rewards drift-induced optical flow as Dynamic Degree while not directly penalizing texture hardening or flow stagnation"——即他们造了能抓住**假的**保留敏感性的评价。

**2609.12890 Internal-DW(训练型)——数学形式上最接近,且**预先堵死了我的 Q2 抗辩**。**
> "amplifying predictable signal and unpredictable noise **together**... bounded Wiener gains that **balance preserving predictable learning signal against suppressing unpredictable variation**... **outperforms gradient clipping and Jacobian regularization on all four**"

"这不只是 Jacobian 正则"这个论证,已经有人在长视界自回归设定下**做过并实证了**。

**2607.27110 FreqForcing(免训练)** low-freq 稳定 / **high-freq 保留动态**,并给出误差累积的频域刻画("低频带能量漂移"),Self-Forcing 上 24× 外推。(i)(ii)(iii) 齐。
**2602.14027 FLEX(免训练)** 低频内插 / 高频外推以 "preserve multi-scale temporal **discriminability**"。
**2512.12080 BAgger(训练型)** 从自身 rollout 构造纠正轨迹,标准 score/flow matching——就是"让缺陷在后续若干次调用衰减"的具体损失。
**2606.13035 TetherCache** TAME 把漂移记忆 token 统计对齐到可信分布,GRAB 保留时间多样性——带刻意保留的选择性纠正。
旁证:2605.14487 Head Forcing、2607.15849 TANGO、2601.21868(采样轨迹上的收缩,Lyapunov drift + Doeblin)、2602.04608(Jacobian 正则稳定长期积分,即那个退化本身)。

### 裁定:轴 (e) **END-LINE**

仍未被占的只剩一条极薄的缝:*在**状态空间方向**(而非频带、而非梯度路由)上陈述的误差增益目标,且在**固定的相机条件化证据边界**上*。我判定**不可辩护**,三条理由:
1. **频带就是一种方向分解**——"状态空间方向" vs "谱方向"是**重参数化**,不是不同机制;
2. FreqForcing 的频域刻画是正面证据,说明谱参数化**已经够用**来描述该现象;
3. 我在 pinned 消费者上**没有任何测量**显示存在谱账本抓不住的状态空间方向结构——而要拿到这个测量,本身就是我想论证的那个实验。**循环。**

### 方法论记录(v2.16)

**"占据性检索必须在提交方案之前跑,而不是在被质疑之后跑。"**
Astra 标 UNVERIFIED 的东西我本可以早三轮自己查。这次是我在**发出 prompt 之前**先跑检索、
并得到对本方不利的结论——这是正确顺序。同时:**"占据"是正面主张,单一反例即可证伪**,
故我的检索本身有系统性偏向"确认关门"的风险,已在 round-11 prompt 的 Q2 里请对方审计我的查询族。

`new_method_validated=false`;`novelty_authorization=NONE`;800 GPU-hours 维持撤回。

## 2026-09-19 Astra 第十一轮(gpt-6-astra / ultra,直接读仓库):END-LINE 确认,但我的一条理由被推翻

本轮首次让评审方**直接在仓库内运行并自行核查**,而不是信我的转述。它独立做了 arXiv 检索、读了 pinned 源码、算了哈希。

### 一、裁定

**Q4 = END-LINE。** 且 Q3 明确:**在当前约束下没有可提交的方法论文。**

### 二、它推翻了我的理由 ①(我接受)

我说"状态空间方向 vs 谱方向只是重参数化"。**这一条过强,撤回。**
频率是像素/时间坐标上的一组**固定基**;而证据切空间由相机、历史帧与场景保持约束定义,
是**输入条件相关且非线性**的。二者只有在额外假设存在**固定可逆线性映射**时才能称为重参数化。

裁定不变,但支撑理由更换为:
1. 该区分**只是待检验的猜想**——必须先在冻结权重上测有限视界增益,并检验是否存在谱特征与梯度路线**解释不掉的残差**;项目没有这个测量;
2. 而这个 frozen probe **本身属于 owner 已排除的 measurement/evaluation 工作**,不能改名当方法贡献;
3. "固定 evidence-read graph"在本消费者上**不是无条件成立的**——查询侧双重混淆未封存前,测到的是查询、归一化与生成器的混合效应。

### 三、它更正了我的源码断言(我已独立复核)

我写"`self.c2ws` 只有两处写入、无 setter"。**按"所有状态 mutation"算并不完备**:另有 line 1360 `self.c2ws.pop()`。
我自己查了:该 pop 位于 **`undo_latest_move()`**(1336 行),对
`latents / encoder_embeddings / c2ws / Ks / pil_frames` **五个列表成组回滚**并回退 `global_step`。
除 `reset()` 外这是唯一的公开 mutator。**T1-5 结论不变甚至更硬**:没有任何路径能改一个**被保留帧**的相机标签——
pop 连内容一起删,pop+append 只能重新生成内容,给不出"同内容、异相机标签"。
准确表述应为:**两处写入/创建、无 setter、另有一处成组删除。**

### 四、Q2 检索审计:确认偏差属实,但没找到反例

它点名我漏掉的六个查询族,每族都返回了真实论文:
exposure bias / teacher forcing(1506.03099、1610.09038、1011.0686 DAgger)·
cross-frame error correction(**2601.05966 VideoAR**,摘要明写 Cross-Frame Error Correction,第一轮就该出现)·
Koopman / 各向异性收缩(2608.25879)· camera-conditioned(2606.09507 Prisma-World、2608.29910 Matrix-Game 3.5)·
4D self-forcing / revisit(2602.21929、2607.05376、2607.21848、2512.18741)· 记忆角色选择(2603.21366)·
以及直接把 state-space + AR video + 长期场景记忆放一起的 **2505.20171**。

**准确结论:我的检索不足以支撑"全领域已占据"这个普遍命题(正面命题,一篇反例即可推翻);
但补搜没有发现任何同时满足"非频谱、非梯度路线、固定相机证据边界、冻结权重可先验检查、且已形成可训练方法主张"的反例。**
故停 axis (e) 仍是正确的**项目决策**,而不是一个领域定理。

### 五、引用与仓库事实核查

**13/13 引用全部为真、标题吻合。**其中 **2609.12890 Internal-DW 确实存在**——Astra 本轮 export.arxiv 单篇抓取返回空,
它谨慎地把该篇降级为"你提供的线索"。那是 API 瞬时故障(其日志里有同样的 `ParseError: no element found`),我重试后拿到全名。该篇仍是支柱。
它对仓库的两条断言我也复核了:三份 pinned 副本 SHA-256 均为 `90a45f452a4f734b...`;
修复覆盖"10 个受影响窗口中的 8 个,另 2 个无符合预声明策略的第四个 distinct candidate"——与 TECHNICAL_REPORT §5.3 完全一致。

### 六、终止交付物(Astra 措辞)

**冻结生成器的可复核诊断/取证技术报告**:记录检索器状态泄漏、查询—归一化双重混淆、有限 panel 上的上下文对照、
重复槽位修复失败及其适用边界。**不能包装成方法贡献,也不能改名为 owner 已排除的 measurement/evaluation 贡献。**
所有数字按证据等级原样保留(order-invariance 11/11 是软件/协议有效性证据,不是方法收益;
+0.242 dB 是有限的、暴露过的开发序列上的 RGB PSNR,不是 held-out 泛化)。
明确反对"以'先测再决定'为名恢复 800 GPU-hour"。

`new_method_validated=false`;`novelty_authorization=NONE`;800 GPU-hours 维持撤回。

## 2026-09-19 分层数字对账:数字没错,但我的排版制造了一个假分解

评审在第十一轮提出:泄漏分层按窗口数等权加权得
`(2×0.000 + 4×(−0.015) + 8×0.436)/14 = 0.244857…`,而主对比是 **+0.242**,
并正确指出"把三个 stratum 均值四舍五入到三位小数"解释不了这 0.0029 的差。

**逐位核对结果:数字全对,不存在不一致。**
分层表的估计量是 `clean − leaked`,它分解的是结果表的**第四行**
`memory_nms_on_clean − memory_nms_on(leaked) = +0.245 dB`(SD 0.711,6/14),
**不是第一行**的 `memory_nms_off − static = +0.242 dB`。
加权均值 `3.428/14 = 0.24486 → +0.245`,**与第四行逐位吻合**。

`docs/RETRIEVAL_ARMS_RESULT_20260918.md` 原文其实写明了表头是 `mean of clean − leaked`。
**是我在转述时把它弄丢的**:今天的 ledger 条目和 round-11 prompt 的 Q3 里,
我都把"leak stratified: NULL +0.000 / PERMUTATION −0.015 / CONTENT +0.436"
**紧贴主对比排列却没有重述估计量**,于是一个认真的评审自然去和 +0.242 对账,
发现 0.0029 的缺口并合理地怀疑存在未披露的加权差异。

**这次的危险程度高于一般笔误:两个对比只差 0.003 dB。**
一个 0.003 的错配不会触发任何直觉警报,也不会被任何量级检查抓到;
它只会在有人做精确对账时暴露,而大多数读者不会做。
若无人对账,一个错误的分解关系就会随报告流出,并在他人引用时固化。


## 2026-09-19 第十二轮:逐条放宽 C1–C5 的审查 → END-LINE-STANDS

owner 选择"松掉某条 FIXED 约束"。约束原文(`TECHNICAL_REPORT_20260918.md:98`):
> Frozen: no training(C1), no fine-tuning(C2), no new weights(C3), no modification of the upstream source(C4)。
另加 `:67` 的 C5:one dependency group, one frozen consumer。

### 结论:没有任何放宽到达"已建立为未占、非退化、且允许作为方法贡献"的方向

| 放宽 | 到达什么 | 为何不 admissible |
|---|---|---|
| C1 / C2 单放 | **空操作**——C1 单放仍被 C2/C3 挡住,C2 单放本身就是 training 仍被 C1 挡 | 没有可持久化干预,无可达轴 |
| C3 单放 | 接入外部已训练 checkpoint 做重排/固定特征 | 轴 (a)/(b)/(f),被 2606.02479、2504.06672、2406.10126、2503.03751、2506.04225 占 |
| C1+C2 | 微调现有 `model_wrapper`/`denoiser`(62/72 行,采样 1270–1278) | 轴 (e)/(h),被 Self Forcing、BAgger、Steady-Forcing、Stable Video Infinity、2602.04608 占 |
| C1+C3 | 在 `get_cond`(1267 行)外训练 selector/adapter/geometry branch | 被 FantasyWorld、LongLive-RAG、RAGME 占 |
| C1+C2+C3 | 完整可训练 | 绕过了 common-target 单步代数陷阱,**没绕过占据** |
| **C4** | **最便宜**:fork 里加 retained-frame camera relabel setter(还须同步重建 surfel,否则 stale geometry),并可显式清 `initial_threshold` 泄漏 | 轴 (b)/(f),被 EscherNet、PRoPE、2605.15182、2603.16871、GEN3C、Voyager、FantasyWorld 占。**买到的是"接口可用",不是 admissible direction** |
| C5 | 跨 consumer 复制同一冻结干预 | 首先落在 owner 已排除的轴 (g);包装成 consumer-agnostic method 则被 2406.10126、2606.02553 占 |

**成本账(事前估计):** C1+C2+C3 最小 pilot 约 800 GPU-hours,原型级约 3,000,且需要
训练数据 + 独立 held-out(ScanNet++ v2 申请 lead time 2–6 周,尚未开始)+ supervisor scope 批准。
**至少 6 周,本学期不可稳妥完成。** C4 只需 0 GPU(纯 CPU 不变量门),1–3 天,但只得可行性。

Q3 **拒绝排名**:"C4 最便宜但预期 admissible contribution 为零,把它排第一会把 feasibility 错写成 novelty。"
Q4 **拒绝编造门槛**:"我不伪造一个训练门槛来给已经被占用的方向制造授权。"

### 核查

9/9 新引用全部为真、标题吻合。4/4 代码行逐字命中:
62 `self.model_wrapper = VMemWrapper(self.model)`、72 `DiscreteDenoiser(...)`、
1267 `cond = self.get_cond(...)`、1270 `do_sample(...)`。三份 pinned 副本 SHA 复核一致。

### 两条彼此独立的 END-LINE 理由(重要)

1. **占据**——依赖文献判断,可被单一反例推翻;
2. **日程与算力**——即便占据判断全错,C1+C2+C3 在本学期也执行不完,且 tranche 已撤回、数据申请未启动。
**理由 2 不依赖任何文献判断,因而比理由 1 更稳健。**

### 我的盲区(自陈)

第十二轮 prompt 的 Part 3 里,**是我明令"axis (g) measurement/evaluation 被排除,不许往那边引"**。
因此本轮从未评估**第六条约束 C6:"贡献必须是 method"**。
在所有方法轴关闭之后,C6 才是真正的 binding constraint,而它恰恰是**唯一零成本**的放宽。
这一条必须交回 owner,不能由我或评审代为排除或代为恢复。

`new_method_validated=false`;`novelty_authorization=NONE`;800 GPU-hours 维持撤回。

## 2026-09-19 泄漏可达性:自查完整链路——"前进后转身"即触发,`reset()` 清不掉

在 pinned 源码(SHA `90a45f45…`,三份一致)中逐行走通了从用户动作到脏读的完整链:

| 环节 | 位置 | 事实 |
|---|---|---|
| `move_backward` / `move_forward` | `navigation.py:185/234`(kwarg 在 187/236) | 显式 `use_non_maximum_suppression=False` |
| 禁用分支 | `pipeline.py:704-705` | `else: self.initial_threshold = 1e8` ——**无条件写** |
| `_turn` | `navigation.py:321` | `generate_trajectory_frames(interpolated_poses, interpolated_Ks)` ——**不传 NMS 参数** |
| 签名默认 | `pipeline.py:1318` | `use_non_maximum_suppression=None` |
| 透传 | `pipeline.py:1249` | `get_context_info(target_c2ws, use_non_maximum_suppression)`,`None` 原样传入 |
| 解析默认 | `pipeline.py:678-679` | `if ... is None: use_non_maximum_suppression = self.use_non_maximum_suppression` |
| 配置值 | `configs/inference/inference.yaml:16` | `use_non_maximum_suppression: true` |
| 启用分支赋值守卫 | `pipeline.py:681-682` | `if use_nms:` → **`if is_second_step:`** ——只在该条件下才赋值 |
| 无条件读 | `pipeline.py:708` | `current_threshold = self.initial_threshold` |
| slot-0 先于阈值循环 | `pipeline.py:711` | `selected_indices.append(sorted_frames[0])` ——这解释了 slot-0 在 14/14 中不变 |
| `reset()` | `pipeline.py:135-150` | 清 `rgb_vae_latents / rgb_encoder_embeddings / poses / focal_lengths / surfels / surfel_Ks / surfel_depths / Ks / surfel_to_timestep / all_pil_frames` 等 11+ 字段,**不清 `initial_threshold`** |

**结论:触发条件是"任意一次 move,随后一次 turn"——导航交互中最基本的动作序列。**
禁用分支无条件写 `1e8`;启用分支只在 `is_second_step` 赋值,否则读到陈旧的 `1e8`,
使 NMS 在阈值意义上失去抑制作用。且 `reset()` 不清除,故"重新开一段"仍然继承。

**这把该发现从"我们自建 harness 里的一个怪癖"提升为"公开发布系统在普通用户路径上可达的状态依赖缺陷"。**
但下述两点尚未确认,不得先行断言:(i) 当前 public main 是否仍如此;(ii) 论文 benchmark 的评测脚本是否走这条混合路径
——若评测每个对象只用单一 NMS 设置,则影响范围是**交互/导航用户**,不是论文表格。已交由独立核查(R13-A)。

## 2026-09-19 R13-A 公开可达性核查:缺陷在**当前公开发布版**中,上游无人报告;但不得声称论文数字受影响

### 更正我上一条的夸大

我写"触发条件是**任意一次** move,随后一次 turn"。**过头了,撤回。**
启用分支的赋值守卫是 `is_second_step = len(self.pil_frames) == 5`(`pipeline.py:674`),
**恰好在 5 帧时转向,阈值会被重新赋值**,不读脏值。另有 `pipeline.py:631-633`:
`len(self.pil_frames) == 1` 时提前返回,先于阈值分支。

**精确的触发序列是"点两次移动,再转向"**(静态控制流推导,`target_num_frames: 4`):
① 第一次 Forward/Backward —— 仅 1 帧,`:631-633` 提前返回,不写阈值;生成后 1→5 帧。
② 第二次 Forward/Backward —— `len>1`,`:704-705` 无条件写 `1e8`;生成后 5→9 帧。
③ 点 Turn —— `_turn` 不传参 → 配置 `true`;帧库为 9,**不满足 `is_second_step`**,
   启用分支不重写,`:708` 读到上一步留下的 `1e8`。

### 已核实(我独立复算了最要害的一条)

**公开 HEAD = `39291e4f272f6b4f270691d930926ab5930f942e`(2025-07-25)。
从该 commit 下载的 `modeling/pipeline.py` 为 1431 行,SHA-256 `90a45f452a4f734b…`,
与本项目三份 pinned 副本逐字节相同。**(我自己 `git ls-remote` + `curl` + `shasum` 复核通过。)
**即:我们分析的就是当前公开发布版本,缺陷仍在。**

- README 的 Usage 只有 `python app.py`;`app.py:19-23` 是**模块级全局 `MODEL = VMemPipeline(...)`**,
  所有 GUI 操作共享同一对象。`app.py:204-219` 把 `y_angle≠0` 分派到 `turn_left/right`,否则 `move_forward/backward`。
- `reset()` 不是用户可见操作(README 全文无 `reset`),但经 `initialize()` 内部调用;
  它**不清 `initial_threshold`**,且该属性**在 `__init__` 中根本没有初始化**。
- **上游无人报告或修复**:GitHub API 对 `initial_threshold` / `get_context_info` /
  `non_maximum_suppression` / `reset` 四个精确词的 issue+PR 搜索 `total_count = 0`;
  仓库共 16 issues、1 PR(#15)、7 commits;`modeling/pipeline.py` 路径历史只有初始 commit。

### 不得声称的事(R13-A 明确否定)

**不能推出"论文 benchmark 数字已被污染"。** 公开树里**没有 VMem 自己的 evaluation driver**
(`eval` 路径都在 `extern/CUT3R/eval` 下,属 CUT3R);唯一通用入口 `VMemPipeline.__call__`
(`:1408-1429`)先 `initialize()` 再生成且**不传 NMS 参数**,沿配置单一设置运行,**不是混合序列**。
故当前可建立的范围是:**交互/导航用户路径**,不是论文表格。
作者未随仓库发布的评测脚本、HF Space 的实际调用顺序,本轮无证据。

### finding type 的先例(9/9 引用已核实为真)

严格等价的先例**未检出**(search-bounded,非"不存在")。最接近的:
- **2607.21686 Persistent Computational State: A Session-Centric Runtime for Generative World Models**
  ——同领域最近,把 serving 丢弃 world-model 运行时状态作为可测失效,在 Cosmos3 / WorldMem / Matrix-Game 2.0 上做恢复实验。
- **2405.03672 Cutting through buggy adversarial example defenses: fixing 1 line of code breaks Sabre**
  ——"读已发布代码→定位 bug→量化修复前后效应"的方法论先例。
- 旁证:2609.04748(LLM serving 的 cache 状态未 reset 导致 16-bit 36.2% / 4-bit 75.0% 轨迹改变)、
  2609.04875、2606.20545、2606.00793、2606.27537、2207.07048、1911.07698。

R13-A 自列 5 条不可验证项(未运行 demo、未取得作者评测脚本、未审计 HF Space、检索有界、未复算本项目 14-window 数值)。

## 2026-09-19 R13-B 发表先例调研:诊断类工作能进主会,但本项目材料未达门槛

25/25 引用已核实为真(Henderson 1709.06560、Engstrom 2005.12729、Agarwal 2108.13264、
Dacrema 1911.07698、BLEU 2006.06264、resize 2104.11222、MIL unit tests 2310.17867、
PLAID 2404.14989、TREC 2301.10493、contamination 2310.17589/2311.09783/2407.07565 等)。

### 先给负面答案(R13-B 的 Q5 置顶)

**即便放宽"贡献必须是 method"这条约束,现有材料也还没达到可发表的 diagnostic contribution 门槛。**
它足以支撑"一个冻结 VMem consumer 中存在可复现跨调用状态依赖,并在一个暴露开发 panel 上量化了影响"
这一**单系统 forensic case study**;未达到已发表先例反复出现的更高门槛。

### 真正区分"已发表诊断论文"与"没人发的技术报告"的三项(观察性,非定理)

**① 结论影响** —— 不只发现 bug,而是证明读者会得出不同结论
(Engstrom 改写 PPO/TRPO 归因;Dacrema 11/12 被简单方法超过;TREC gap 18%→5%;Agarwal 显示 point estimates 可反转)。
**② 跨独立单元的外部效度** —— 让发现脱离单一 code path 后仍可检验。
**③ 可被他人采用的 test / protocol / artifact** —— rliable、MIL algorithmic unit tests、held-out contamination benchmark。

**明确不是区分项:** 样本量绝对阈值(先例从单系统复现到 294 篇不等);effect 很大(不充分);
负结果(ReScience C / MLRC / NeurIPS E&D 明确容纳)。**"有一个 bug"本身也不够** ——
门槛接近 `bug + consequence + scope + reusable audit`。

### 逐项对照本项目

**已有:** 真实 defect 与后果、较严谨的因果门(11/11、pre-scoring census、NULL 字节同一性、预声明后如实丢弃的修复)。
**缺口(结构性,加 seeds 补不上):**
1. 无第二个 released consumer / 版本 / 任务 / dataset family → 无法估计该系统家族中的普遍性;
2. 无 held-out —— 两条 sequence 已被用作 exposed development data;
3. **未证明该 defect 改写了 VMem 原论文的已发表结论或 ranking**;
4. audit artifact 尚未被独立作者采用或跨系统复核,"可迁移 protocol"目前是设计意图而非外部验证过的产物;
5. 14-window RGB PSNR 多数 effect < 0.5 dB 且异质性大,无 SE / CI / 检验 / bootstrap;
6. 只有单一 pixel metric。

### venue 现实

**"诊断工作不能进主会"是错的** —— AAAI / ICLR / NeurIPS / ACL / CVPR 都有先例;
但主会先例的共同条件是跨越单一 codebase、或改变 benchmark/metric/algorithm comparison、并交付可复用工具。
更现实的窄路线:**TMLR**(editorial policies 明确收 reproducibility studies 与揭示 strengths/weaknesses 的实验研究)、
**NeurIPS 2026 Evaluations & Datasets track**(evaluation 为核心智力贡献,收 rigorous reproduction/auditing/stress-testing 与 negative analyses)、
**MLRC**(已整合为 NeurIPS 2026 官方路线,但需先被 TMLR 接收)、**ReScience C**、SIGIR/ECIR reproducibility track。
**Registered report 不适用** —— 两条 sequence 已作为 exposed development data 用过,不能事后改写成预注册。

### 我的判断:成本结构与方法路线根本不同,但最强的那项可能拿不到

缺口 2/5/6 便宜(封存 held-out、不确定性分析、加一个非 PSNR 评价维度)。
缺口 1/3 需要放宽 **C5**(one dependency group, one frozen consumer)——
但**不需要 C1/C2/C3**:全是冻结模型的推理,没有训练、微调或新权重。
**缺口"结论影响"是三项强区分项里最强的一项,而 R13-A 已确认对 VMem 论文表格拿不到**
(公开树无 VMem evaluation driver,`__call__` 单一设置运行)。

若要走这条路,可能的重构框架是:把贡献从"VMem 有个 bug"改成
**"有状态记忆/检索类视频系统的 reset 语义不完整;这是一个能检出它的审计协议;在 N 个已发布系统上应用发现 M 例"**,
把现有材料降级为其中一个 worked example。**这只是一个待检验的框架假设,不是已验证方向**;
且 **2607.21686 Persistent Computational State 已在 Cosmos3 / WorldMem / Matrix-Game 2.0 上做多系统运行时状态工作**,
占据风险必须先查。

`new_method_validated=false`;`novelty_authorization=NONE`;800 GPU-hours 维持撤回。

## 2026-09-19 R14-C 占据核查:重构框架**未被占据**,但最强反对意见是"跨域改名"+"缺少语义 oracle"

13 篇引用已核实为真(含 2607.21686、DeepCruiser 1812.05339、DL bug studies 1906.01388/2307.13777/2401.03069、
ML testing survey 1906.10742、MIND 2602.08025、2602.23152、2609.03673)。

### Q1/Q2:未被占据

**最危险的邻居 2607.21686 Persistent Computational State 被逐节读完(arXiv HTML + 29 页 PDF)**,判定为**不占据**:
- §1.2–§2 把失效写成 **runtime 在 request boundary 丢弃**状态,§3 边界明确把 model code/RNG 留在 framework ——**是 serving/runtime 层,不是对已发布模型实现内部写读路径的源码审计**;
- §4 的 `Fingerprint(M,D,ε,probe)` 是对可寻址 runtime buffer 做 necessity/sufficiency/redundancy **动态消融**,不是静态 reset 完备性检查;
- **全文未出现对模型类 `reset()` 的审计**;"initialize" 仅在 §7.2 作为重新初始化 CUDA 的进程语境出现;
- 未报告任何"分支 A 写属性 → 分支 B 有守卫地读 → reset 未清除"的实例。
**其 `snapshot completeness`(§3, I4)不能改称 `reset completeness`;其 return-consistency test(§6)不能改称 reset audit。**

五条件 predicate 作为**组合**未被占据,但各部件都有强邻居:软工的 test pollution / order-dependence
(PolDet、PRADET、ODRepair、NIO)已有成熟的动态检测与修复,并报告真实项目的 prevalence 与修复结果。

### Q4:最强结构性反对意见(这是真正要解决的智力问题)

**① 审稿人会视为 test-pollution / order-dependence 的跨域改名**,除非证明模型生命周期语义带来不可约的新对象。
**② 更尖锐的语义问题:在没有明确 reset/initialize contract 时,"该字段没被清除"并不自动等于 defect——它可能是有意的持久化状态。**
审计必须证明该字段**按公开生命周期语义应当被清除**,而不仅仅是"它没出现在某个函数体里"。

**这条我接受,并认为它是本方向能否成立的枢纽。** 没有 defect 的语义 oracle,整个 audit 退化为风格检查。

### 源码边界更正(重要)

**真正满足五条件静态链的字段是 `initial_threshold`,不是 `c2ws`。**
`reset()` 确实不清 `self.c2ws`,但 `initialize()` 随后在 `:180` 用 `self.c2ws = [c2w]` **重建**它,故 `c2ws` 不构成 reset omission。
另:条件 5(冻结权重行为后果)在**公开 demo 路径上仍是 UNVERIFIED** ——
我们有静态可达性 + 自建 harness 上的 `+0.245 dB`,但**没有运行公开 demo**。二者不可混写。

### 我自己动手的第二系统审计:Self-Forcing = **NEAR**,不是 HIT

浅克隆 `guandeh17/Self-Forcing` HEAD `33593df3e81fa3ec10239271dd2c100facac6de1`:
- **相同的结构性风险模式**:`demo.py:136` 模块级全局 `pipeline`(与 VMem 的全局 `MODEL` 同构);
  `causal_inference.py:36` 只初始化 `self.kv_cache1 = None`,**`self.crossattn_cache` 在 `__init__` 中未初始化**;
  **没有 `reset()` 方法**,靠 `:110-133` 的 `else` 分支手工部分重置;
  `demo.py:309-310` 还**绕过守卫直接调用** `_initialize_kv_cache/_initialize_crossattn_cache`。
- **但**:`else` 分支对 `kv_cache1` 的 `global/local_end_index` 与 `crossattn_cache` 的 `is_init` 都做了重置,
  `causal_diffusion_inference.py:110-124` 对 pos/neg 两路也都重置。
**我没能证明存在可达的脏读,故诚实归类为 NEAR 而非 HIT。** 这本身是有用的数据点——
说明该缺陷类**不是**这类代码库的普遍现象,`M/N` 里的 `M` 可能很小。

## 2026-09-19 R14-D 跨系统可行性:**零 GPU 足以关闭广度缺口的静态部分**;发现第二个 HIT(GEN3C)

8/8 新引用已核实为真。**它正确区分了两个同名 Voyager**:
`2305.16291`(MineDojo LLM Minecraft agent,按模态排除)vs `2506.04225`(视频扩散),我此前差点混用。

### 审计结果(固定五条件谓词,10+ 系统,均带 commit SHA 与行号)

| 系统 | C1 | C2 | C3 | C4 | 判定 |
|---|---|---|---|---|---|
| VMem `39291e4f` | ✓ | ✓ | ✓ | ✓ | **HIT**(参照系统) |
| **GEN3C `db2ffe12`** | ✓ | ✓ | ✓ | ✓ | **HIT** |
| MagicWorld v1 `a378d67d` | ✓ | ✗ | 不确定 | ✓ | NEAR |
| Self-Forcing `33593df3` | ✓ | ✓ | ✗ | ✓ | CLEAN |
| LongLive v1 / v2.0 | ✓ | ✓ | ✗ | ✓ | CLEAN |
| Matrix-Game 1 `71c3cd7f` | ✓ | ✓ | ✗ | ✓ | CLEAN |
| FramePack `97fe5dbe` | ✓ | ✓ | ✗ | ✓ | CLEAN |
| MemFlow `7ed51477` | ✓ | ✓ | ✗ | ✓ | CLEAN |
| Cosmos umbrella | — | — | — | — | NOT-INSPECTED(无单一完整实现) |
| Voyager(MineDojo) | ✓ | ✓ | ✓ | ✓ | `chest_memory` 是 HIT 但**按模态排除** |

**它对 Self-Forcing 的判定(CLEAN)比我自己的 NEAR 更有依据**:C3 失败,因为公开调用路径上的重置是显式的。我采纳其判定。
**CLEAN 是诚实的负例**,恰恰是这份 survey 可信的原因——不是把每个系统都说成阳性。

### GEN3C HIT:我自己逐行复核通过

`nv-tlabs/GEN3C` HEAD `db2ffe12ced12ddafcec5e0422ee46ce8520746b`(CVPR 2025 Highlight,NVIDIA Toronto AI Lab):

```python
# gui/api/server_cosmos_base.py:46-71
async def seed_model(self, req):
    if self.pose_history_w2c:
        self.model.clear_cache()          # :53  缓存已清
        self.pose_history_w2c.clear()     # :54
        self.intrinsics_history.clear()   # :55
    ...
    model_result = seeding_method(...)    # :62-70  可抛异常
    self.model_seeded = True              # :71  仅成功后才写
```
异常源已核:`gen3c_persistent.py:208` `raise NotImplementedError("Seeding from multiple frames requires providing depth values.")`。
`server.py` 捕获并返回 **HTTP 400**,服务存活、客户端看到干净错误,**内部状态已不一致**。
`server_base.py:60` `self.model_seeded = False` 初始化,`:122` `if not self.model_seeded: raise` 读取 → 放行 → 对着空缓存推理。

**最有说服力的细节:同一概念在两层各有一个名字几乎相同的标志,只有一个被清。**
`clear_cache()`(`gen3c_persistent.py:551-553`)把**模型自己的** `self.model_was_seeded = False` 清了;
**服务端**的 `self.model_seeded` 没清。**重复的生命周期状态跨层不同步——这正是该缺陷类存在的机理。**

### Q5 可行性裁定(关键)

- **零 GPU 足以关闭条件 1–4 的广度缺口。** 两周内一人可审 **9 个模型家族(约 13 个发布变体)**。
  限制因素不是读代码的速度,而是确认混合序列确实从文档化 API 可达、区分 UI 状态与实例状态、跟踪分支漂移、逐一核对许可。边界案例(如 MagicWorld)还需第二名复核者。
- **零 GPU 不足以支撑行为影响主张。** "条件 5 不是'代码抛错'" ——
  可发表的行为主张必须在冻结权重下展示可复现的输出/质量/状态差异,并把陈旧状态路径与干净重置、与普通生成失败区分开。
  **审稿人很可能把纯静态的跨系统表格视为 code-risk 证据,而非已证明的外部效度。**

### 我的判断:两个 HIT 的**后果类型不同**,这是必须处理的问题

VMem 的是**陈旧阈值 → 细微行为改变**(我们自建 panel 上测得 `+0.245 dB`);
GEN3C 的是**陈旧标志 → 非法状态被放行**(静态预测的 error/invalid-state 后果,未运行)。
二者不是同一种"后果",不能在同一张表里当作同质证据聚合。这一点在写作时必须显式处理,不得模糊。

`new_method_validated=false`;`novelty_authorization=NONE`;800 GPU-hours 维持撤回;本轮零 GPU。

## 2026-09-19 我自己的 oracle 提案:两个 HIT 可统一为"代码库自我声明的生命周期"

R14-C 提出的最强反对意见是:没有 reset contract 时,"字段没被清"不等于 defect——可能是有意持久化。
我认为这两个已验证实例给出了**不需要询问作者、也不是风格偏好**的 oracle,且二者是同一族:

| 系统 | 意图在**哪里被代码库自己声明** | 违反形式 |
|---|---|---|
| **GEN3C** | **另一层**:`gen3c_persistent.py:551-553` `clear_cache()` 把模型自己的 `self.model_was_seeded = False` 清了 | 服务端 `gui/api/server_base.py:60` 的 `self.model_seeded` 从不被清 |
| **VMem** | **构造函数**:`initial_threshold` 在 `__init__`(`pipeline.py:47-135`)中**出现 0 次**,故 fresh 对象根本没有该属性 | 混合序列 + `reset()` 之后,该属性存在且为 `1e8` |

**统一表述(构造器等价性 / 跨层一致性 oracle):**
> `reset()` 应把对象恢复到与**新构造对象**行为等价的状态;
> 若同一概念在多层各有表示,生命周期路径应一致地清理它们。
> **参照点是代码库自身的构造函数与自身的清理声明,不是审计者的偏好。**

已验证的支撑事实(我自己复核):
- `initial_threshold` 在 VMem `__init__` 中 **0 次出现**(grep 计数,行范围 47–135);
- 我们自己的 `arm_state_isolation_test.py` 早已把这件事写进代码:`:70` 先 `pipe.reset()`,
  `:79-80` 仍必须 `delattr(pipe, 'initial_threshold')`,并在 `:85` 记录
  `FRESH_HAS_THRESHOLD = hasattr(pipe, 'initial_threshold')`、`:185` 记录 `reset_alone_is_insufficient`。
  **即:该 oracle 不是事后为论文构造的,它是我们在做别的事情时被迫实现的。**

**注意边界:** 这个 oracle 必须容许合法例外(已加载权重、刻意保温的缓存、RNG 状态等),
不能退化为"reset 必须清空一切"。它约束的是**语义状态**,不是资源状态。
该区分如何形式化,是这条路线成立与否的关键,已交 R15-E 压力测试。

## 2026-09-19 R15-E 语义 oracle:**我的提案被部分推翻**;GEN3C 成立,VMem 降级为 INTENT-ORACLE-UNRESOLVED

### 我错在哪(接受)

我提出"构造器等价 + 跨层一致"作为统一 oracle,并把 GEN3C 的**两个近同名标志只清一个**当作主要论据。**这个强调是错的。**

**"某字段没出现在 `reset()` 里"最多是静态异常信号,不是充分证据。** 可辩护的 oracle 必须把判定对象
提升到**公共生命周期合同**:先写出用户可调用 API 的可观察前置/后置不变量或**事前固定的等价调用关系**,
再用代码路径与执行结果证明违反。**字段是否应被清除只能作为归因,不能作为 oracle 本身。**
按 R15-E 的排序,"跨层 duplicate-state consistency"只排第 4,**适合归因与候选排序,不能单独定罪**;
"peer-group non-uniformity"排第 6,**最容易退化成 style checking**——正是原反对意见警告的那件事。

### 逐实例裁定

**GEN3C —— 有可辩护 oracle,但理由不是我说的那个。**
最强证据是**公共准入安全不变量**:`model_seeded == True` ⇒ `request_inference()` 放行 ⇒
**因此它必须代表一个可用的 3D cache**。清缓存后重新 seeding 抛异常、服务捕获返回 400、
旧的 `True` 保留、推理仍被放行 —— 这是该不变量的反例。
`model_was_seeded=False` 的跨层清除是**加强归因的佐证,不是唯一依据**。

**VMem —— 降级为 `INTENT-ORACLE-UNRESOLVED`,不再计为 HIT。**
未在 `__init__` 初始化、NMS-off 写、部分 NMS-on 读、`reset()` 不清 —— 这些足以证明
**跨调用依赖的可达性与未初始化风险**,但**不足以证明它"按公开生命周期本应被清零"**。

### 我复核 R15-E 时发现它一处精度错误(对我方更不利)

R15-E 说该 relation "可由 `initialize()` docstring 的 'Reset internal state' 支持"。**不准确:**
- `initialize()` 的 **docstring**(`pipeline.py:151-152`)写的是
  "This method **sets up** internal state without generating additional frames";
- "`# Reset internal state`" 是 **`:162` 的行内注释**,不是 docstring;
- **`reset()` 完全没有 docstring**(`:135` 起直接赋值)。

按 R15-E 自己的排序第 7 条,"单独依赖注释或变量名只能作弱证据"。
**故 VMem 的文档合同比 R15-E 假设的更薄,其 UNRESOLVED 裁定反而更站得住。**

### 最佳 oracle(采纳其表述)

> **公共生命周期关系 oracle:**对一个**预先写入**并由文档/API 语义支持的关系 R,
> 若两条调用序列从等价公共初态出发,R 声明它们在**公共可观察结果**
> (成功/失败、错误类别、准入、返回值,或固定随机流下的输出)上应相等或满足指定变换,
> 则观察到 R 被违反即可判定生命周期缺陷;**字段是否清除只作后续归因。**

这是唯一能同时应对"作者没写 reset"和"内部字段只是实现细节"两种反对的定义。
**前提:R 必须来自公开合同或事前冻结的产品语义,不能看过结果后再创造。**

### metamorphic 路线

(a) **在条件成立时 sound**;(b) **一般思想已被占据**(变形测试 Chen/Liu、PolDet/PRADET/ODRepair/NIO),
故"使用 metamorphic relation"本身**不能作为新颖性主张**;(c) 原则上两实例都可检验,**但尚未执行**。

### 方向状态

**不关闭整个方向,但关闭一个过强版本**:
- ✗ 关闭"reset peer 不齐 + 跨层近名字段不齐 = 已证明缺陷"的静态总 oracle;
- ✓ 保留 GEN3C 的公共 admission invariant 作为可复核 HIT;
- ⏸ VMem 暂停为 INTENT-ORACLE-UNRESOLVED,除非**先冻结再执行** fresh/reused 或 reset/no-reset 的公共 metamorphic relation;
- 若该 relation 无法从 VMem 公开 API 合同中成立,VMem 应正式判为**没有可辩护 oracle**。

**对 rename objection 的诚实处理:** 一般状态污染/顺序依赖 oracle 已有成熟先例;
本项目只有在**"面向生成器/世界模型公共 API 的生命周期合同 + 可重复用户后果 + 领域特有关系"三者同时成立**时,
才可能超出已有测试污染工作。

**当前 M/N 因此从 2 个 HIT 降为 1 个可辩护 HIT。**

## 2026-09-19 R15-F/G + 我的复核:新 HIT **CausVid**,并找到**最强的 oracle 实例**

15/15 新引用核实为真。审计总数升至约 20 个系统。

### 新 HIT:CausVid ——我独立复核,且比报告描述的更强

`tianweiy/CausVid` HEAD `adb6a5ecd07666b4d0290042915c8406e6d5ce22`(arXiv:2412.07772):
`causvid/models/wan/causal_inference.py:37` `self.kv_cache1 = None`;`:100` `if self.kv_cache1 is None:` 守卫初始化;
`else` 分支(`:113-115`)**只重置 crossattn**:
```python
# reset cross attn cache
for block_index in range(self.num_transformer_blocks):
    self.crossattn_cache[block_index]["is_init"] = False
```
**KV cache 索引完全未重置**,随后直接进入去噪循环。全仓库 grep:`kv_cache1` 只出现在 `:37` 与 `:100`,**没有任何 reset 路径**。
公开入口 `minimal_inference/longvideo_autoregressive_inference.py:61-71` 以 `--num_rollout` 在同一 pipeline 上**重复调用 `inference()`**(README:42-46)。

### **最强 oracle 实例:后继实现自己补上了那段重置**

对照 `guandeh17/Self-Forcing` `33593df3` 的同名文件 `pipeline/causal_inference.py:123-132`:

| | `else` 分支 |
|---|---|
| CausVid | `# reset cross attn cache` → 重置 `is_init`,**完** |
| Self-Forcing | 同样的 crossattn 重置,**再加** `# reset kv cache` → 重置 `kv_cache1[...]["global_end_index"]` 与 `["local_end_index"]` |

Self-Forcing 是 CausVid 代码的**直接后继**(同名文件、同类结构、同样的 `_initialize_kv_cache` /
`_initialize_crossattn_cache`、连 `# reset cross attn cache` 注释都相同),补上的那段带着自己的注释 `# reset kv cache`。

**这是本项目迄今最强的意图证据:不是审计者的判断、不是风格规则、不是构造函数论证,
而是生态中最接近该代码的后继实现明确声明了那个重置是必须的。**
按 R15-E 的 oracle 排序,这属于第 1–3 档(公开合同 / 事前关系 / 文档化生命周期),**远高于我此前提出的第 4、6 档论证。**

### 三个 HIT 的 oracle 状态各不相同(必须分开写)

| 系统 | oracle 类型 | 状态 |
|---|---|---|
| **CausVid** | **后继实现声明**(Self-Forcing 补上同一重置) | ✅ 最强 |
| **GEN3C** | **公共准入安全不变量**(`model_seeded ⇒ usable cache`) | ✅ 成立(R15-E 裁定) |
| **VMem** | 无同类声明 | ⏸ **INTENT-ORACLE-UNRESOLVED** |

**注意:CausVid 没有 reset 方法,故"reset 漏清"论证对它不适用;它靠的是后继实现的对比。
三者的 oracle 依据互不相同,不能在论文里当作同质证据聚合。**

### 扩展审计结果(约 20 系统)

**HIT 3**:VMem(oracle 未决)、GEN3C、**CausVid**。
**NEAR 2**:MagicWorld v1;**PlayGen**(`app.py:194-207` 的 `disconnect()` 清了 command/queue/config/online_player,**漏了 `user_zeta[user_id]`**;C4 按"文档化公开路径"严格解释保守判为 NEAR)。
**CLEAN 12+**:Self-Forcing、LongLive v1/v2、Matrix-Game 1、**Matrix-Game 2.0**(`:517` 每次公开 `inference()` 开头把四个 cache 全置 `None` ——**正确范式,极佳对照**)、FramePack、MemFlow、Pyramid Flow、HunyuanVideo、DIAMOND、CogVideoX、AlayaWorld、ViewCrafter。
**OUT-OF-PREDICATE**:Open-Sora、Yume、Hunyuan-GameCraft、HunyuanWorld、Wan 2.1/2.2、Oasis、**WorldMem**(已实核:`app.py:305-325` 有 `reset()` 清 memory latent/actions/poses/c2w/frame index,`:563` 接线;状态经 Gradio State 显式传递)、Cosmos-Predict2。

### R15-G:零 GPU 能走多远

**严格意义上条件 5 仍不能零 GPU 完成**——它要求冻结权重下的行为后果。但:

**E1(GEN3C,0 GPU,已核可行):** seam 存在且**不需改发布源码**。我逐条复核:
`server_base.py:30` `class InferenceModel():` ——**普通类,未继承 `ABC`**(只 import 了 `abstractmethod`),Python 不阻止构造;
`server_cosmos_base.py:32-38` `CosmosBaseModel.__init__` **只调 `super()`,不构造内层模型**;
官方 debug seam(`GEN3C_API_DEBUG=1`)**复现不了该 HIT** ——`server_debug.py:30` 在 `__init__` 就把 `self.model_seeded = True`。
桩只需 4 个小方法 + 小 NumPy 数组,**无 torch 权重**。断言链:seed A 成功 → seed B 清 cache 后抛错、外层 flag 仍 true → `request_inference` 仍放行(202/task)且 inner cache 为 None。
**含 clean-control**:让失败路径显式清外层 flag,则 inference 必须被拒(400)——证明不是"任何失败都能排队"。
成本 **0 GPU-hours**,< 1 wall-clock day。成功后标 `MEASURED_SERVER_CONTRACT_CONSEQUENCE`,同时保留 `frozen_weight_generation_consequence=UNMEASURED`。
**诚实边界**:HTTP route 层需 test-time monkeypatch,**不是由公开配置选出的**;若要求"不改 harness、纯公开配置即可选中桩",答案是**否**。

**E2(VMem,0 新增 GPU):** 复用已封存的 zero-diffusion census ——14 窗口中 **12/14 的 padded retrieval IDs 发生变化**,slot 0 在 14/14 相同。
支持一个**限定的**条件 5:**selector 输出改变**。不支持"生成帧改变"或跨场景外部效度;后者由已有的真实生成结果 `+0.245 dB` 支撑,且属暴露面板。
**从 JSON 读回是档案审计,不能称为重新执行了 selector。**

**总结:最小可审证据包 = GEN3C wrapper 后果 + VMem selector 后果,新增 GPU-hours = 0;
但把两者写成同一层面的"冻结模型行为",审稿人很可能拒绝。**

`new_method_validated=false`;`novelty_authorization=NONE`;本轮零 GPU。

## 2026-09-19 R16-H 执行前 spec 审查:**裁定不执行**——我的 E1 设计有三处实质缺陷

封存的 spec(`c97f4f2`,SHA `080ffc5bcf1f160e...`)经 codex 在**执行之前**对抗审查。
**裁定:当前 sealed spec 不应执行。保留原文件不变,另写新 spec 重新 seal;replacement text 不得回写。**

### 三处实质缺陷(我接受)

**① Q1 成立:失败是 harness 自己制造的。**
spec 写明桩的 `seed_model_from_values` "call 2 raises a controlled exception"。
于是即便 P2 成立,它直接证明的只是**发布版 `seed_model` 如何处理一个由 harness 注入的任意异常**,
**不是 GEN3C 的发布版 seeding 实现会不会产生该异常**。它无法把 `gen3c_persistent.py:208` 变成实际触发源。

**修正路线(可行,零权重零重模型构造):** 导入发布版 `Gen3cPersistentModel`,用 `__new__` 取得
**不执行 `:79-131` 重构造**的 probe;call 2 把 kwargs **原样交给发布版 `seed_model_from_values`**,
禁止 proxy 自己 `raise`;`req_B` 必须是**合法**多帧 `SeedingRequest`(`n>1`、`depths=None`、相机矩阵可逆),
使执行真正到达 `:208`;记录异常类型、精确消息与 traceback 中的发布版 path/line。
probe 的 `clear_cache` 也应绑定**发布版** `Gen3cPersistentModel.clear_cache`(`:551-553`)。
**若导入失败,结果是 E1 INFEASIBLE,禁止退回到"复制同一异常文本的桩"。**
诚实边界:S1 的成功路径仍是轻量 adapter,**发布版归属只覆盖清理路径与 call-2 校验路径**。

**② Q2:P3 只有同步准入证据**,没有实际推理后果;需要把 admission 与 execution 分开观测。

**③ 我未声明的前提会让 S1 在桩被调用前就崩。**
`CosmosBaseModel.__init__`(`:32-38`)**不创建** `pose_history_w2c` / `intrinsics_history` /
`aabb_min` / `aabb_max` / `self.model`,而 `seed_model` 在 `:51` 和 `:54-55` 立即读/清两个历史列表 →
按 sealed S0 执行会先 `AttributeError`。

### 其他未声明前提(全部需写进新 spec)

- `seed_model:74-76` 在 `req.depths is None` 时调 `self.model.get_cache_input_depths().cpu().numpy()` → `req_A` 必须给 non-None depths;
- 请求 dataclass 有真实校验:`api_types.py:53-69` 形状检查、`RequestBase.__len__`(`:101-102`)、
  `world_to_cameras()`(`:71-75`)调 `np.linalg.inv` → **相机矩阵必须可逆,不能用全零**;
- `min/max_frames_per_request`(`server_cosmos_base.py:226-234`)都返回 `self.model.frames_per_batch`
  → `req_C` 帧数必须**恰好等于**它;request id 必须唯一(`server_base.py:124-125` 拒重复);
- `request_inference` 需要**正在运行的 event loop**;
- `run_inference`(`:134-135`)在 inner call 之前就追加 pose/intrinsics history,**失败也会留下新状态**。

### 对"零 GPU"的两条实质威胁

**⑦ `run_inference`(`server_cosmos_base.py:156-162`)无条件创建 `torch.cuda.Event()`** ——
"让 Task 跑完"**不是纯 CPU 默认路径**;no-driver/CUDA 异常**不得**写成 released execution,
而 monkeypatch CUDA 会破坏"发布代码执行"的归属。

**⑧ import 链被我低估:** `gen3c_persistent.py:1-19` **模块级**导入 MoGe、torch、Gen3cPipeline;
`server_cosmos_base.py` 的 torch 是方法内导入但仍需装包;`api_types.py:16-28` → `encoding.py:16-22` 需要 cv2。
**故"零 GPU"成立,但"零环境搭建"不成立。**

### Q6:值不值得跑

**当前版本不值得跑。** 即便"成功",主要观测也只是"harness 自己决定抛异常后 outer flag 没被清掉"。
**修正并重新 seal 后价值有限**:可作为低成本的 server/API lifecycle witness,
把静态可达性变成发布版 validation branch 的可复现执行证据,并明确区分 admission-only 与实际下游失败。
**若资源只能二选一,应先做冻结权重下的实际 consequence;修正版 E1 不能替代生成质量或冻结权重结论。**

### 方法论价值

**这是本项目第一次在"改还合法"的时刻抓住实验设计缺陷。**
若照原 spec 执行,产出会被"你证明的是自己桩的行为"一击打穿,而那时 spec 已冻结、无法补救。
**执行前对抗审查的成本是一次 codex 调用,收益是避免一个注定被驳回的结果。** 应固化为常规。

## 2026-09-19 Preflight(非实验):依赖分层实测 + 审查者预测被动态证实

**这不是 E1,不产生任何关于缺陷的主张。** 它只做两件事:测依赖分层,核审查者的断言。

### 依赖分层(实测,非假设)

在干净 venv 中只装 `numpy` + `loguru` + `opencv-python-headless`,从 `G3/gui/api` 导入:

| 模块 | 结果 |
|---|---|
| `encoding` | IMPORT-OK |
| `api_types` | IMPORT-OK |
| `server_base` | IMPORT-OK |
| `server_cosmos_base` | IMPORT-OK |

**Tier A 无需 torch / CUDA / 权重**——因为 `server_cosmos_base.py` 的 torch 是**方法内导入**(`:46-47`、`:98-100`)。
**Tier B(发布版 `:208` 的 raise)需要重链**:`gen3c_persistent.py:1-19` 模块级导入
`moge.model.v1.MoGeModel`、`torch`、`Gen3cPipeline`、`cosmos_predict1.utils`、`cache_3d`。
故"零 GPU"成立,**"零环境搭建"不成立**。

### 审查者 assumption #1 被动态证实

```
CosmosBaseModel()                     → 无参构造成功
  model_seeded        = False         ← 发布版默认
  model               = <ABSENT>
  pose_history_w2c    = <ABSENT>      ← 审查者预测
  intrinsics_history  = <ABSENT>      ← 审查者预测
  aabb_min / aabb_max = <ABSENT>
  InferenceModel.__bases__ = ['object']
  is ABC subclass          = False
```

两条结论:
1. **`InferenceModel` 确实不是 ABC**(`__bases__ == ['object']`),我此前的静态判断由动态确认;
2. **`pose_history_w2c` / `intrinsics_history` 在构造后确实不存在** →
   按我原 sealed spec 的 S0 执行,`seed_model:51` 会在桩被调用前 `AttributeError`。
   **审查抓到的是真缺陷,不是假想缺陷。**

这条记录支持一条更一般的判断:**执行前审查的价值可以被事后独立验证,不必只凭信任。**
本例中它的三条反对里,至少这一条已由实测确认。

## 2026-09-19 R17-I 分解审查:分解**在限定后成立**;E1 裁定为 **DESIGNED_NOT_EXECUTED**

### 我的表述被纠正(接受)

我写"**任意**异常都会留下 stale=True"。**过宽。** 可辩护的命题必须限定为:

> 在**已成功 seed** 的实例上,一个公开 schema 可表达的多帧无 depth 请求,
> 若**实际进入 released seeding call** 并抛出普通异常,则 wrapper 会留下外层 stale flag,admission gate 放行。

四条边界:
1. 失败前外层 flag 若为 `False`,失败后仍为 `False` —— **必须是"成功 seed A → 失败 seed B"序列**;
2. 异常必须发生在**清理之后、`:71` 之前**。`:47` 的 torch 导入、`clear_cache`、history `.clear()`、
   `req.world_to_cameras()` 处的失败**不适用**该结论;
3. "可达"只能读作**静态的 route-to-wrapper 分支可达性**,不是每种部署配置都已确认;
4. 直接构造 `CosmosBaseModel` 不足 —— 缺成员导致的 `AttributeError` 是 harness 初始化失败,不是目标异常。

### 我 preflight 结论的自我更正

我记了"Tier A 无需 torch"。**只对了一半。** 模块确可导入,但 released `seed_model` 的**第一条语句**
(`server_cosmos_base.py:47`)就是 `import torch`。我实测:无 torch 时
`asyncio.run(m.seed_model(None))` → `ModuleNotFoundError: No module named 'torch'`,
**且发生在任何清理之前**——恰好是上面边界 ② 的反例,由我亲手造出。
故 **"clean venv 无 torch" 只证明 module importability,不证明可原样调用 released wrapper。**

### GEN3C HIT 的范围被收紧(我复核)

`server.py:77-84`:debug 模式或 `model_name=="debug"` → `DebugInferenceModel`;
仅 `cosmos`/`cosmos-predict1` → `CosmosModel`。
`server_cosmos.py:92-96`:**仅当 `gpu_count == 1`** 才 `self.model = Gen3cPersistentModel(args)`,
否则 `MultiGPUInferenceAR`。

**精确区分:stale-flag 缺陷位于基类 `CosmosBaseModel.seed_model`,与 GPU 配置无关;
而发布版 `:208` 这个具体触发源是单 GPU 路径特有的。** `MultiGPUInferenceAR` 是否有同形触发源:**未审计**。

### Q2:审稿人视角

审稿人**可以**接受"released raise 的静态可达性 + wrapper 的异常无关控制流"作为
**代码级条件性缺陷**,因为两个前提都能在 source 上独立核查;端到端运行不是该窄命题的逻辑必要条件。
**但不会把它等同于 end-to-end released-trigger demonstration。** 运行仍承担独立证据职责:
证明所用 checkout/导入路径/路由确实选中这些 released 文件、合法请求确实穿过序列化与 dispatch、
具体配置确实是 `Gen3cPersistentModel`、观察到真实异常与 traceback、以及可被他人复现。

**`request_inference`(`server_base.py:128`)只同步创建 Task;拿到 Task/HTTP 202 仍是 admission,不是 downstream execution。**
真实 inner cache 的首次相关使用在 `gen3c_persistent.py:308`。

### Q4 裁定:**不值得为 E1 现在建 Tier B**

Tier B 的增量只是把 S2 的异常归属从 harness 注入提升为 released `:208` 实际调用;
它**仍不自动提供空 cache 的 downstream runtime 证据**,更不提供生成质量或冻结权重影响。
在这个成本/证据增量比下,不应为一个较窄的审稿人争议建立重依赖环境。

**本轮诚实裁决:E1 = `DESIGNED_NOT_EXECUTED`。静态结论单独保留,标签为
`STATIC_RELEASED_REACHABILITY_PLUS_EXCEPTION_AGNOSTIC_WRAPPER_CONTROL_FLOW`。**

**禁止使用的标签(记录在案以防日后漂移):** `MEASURED_RELEASED_TRIGGER`、`END_TO_END_RELEASED_FAILURE`、
"released `:208` observed"、真实 inference/runtime consequence、视频/图像质量、prevalence、
published-result impact、新方法验证。
若将来注入 `sys.modules['torch']` shim 执行,只能标 `MEASURED_WRAPPER_SEMANTICS_UNDER_DEPENDENCY_SHIM`,
**不得称 native runtime**。

### 方法论

连续两轮执行前审查:第一轮拦下一个会被"你证明的是自己桩"打穿的设计,
第二轮拦下一次为有限证据增量而做的重依赖环境搭建。
**两次都是在"改还合法"的时刻。成本各一次 codex 调用。**

## 2026-09-19 CausVid oracle 的血缘关系:**明文确认**,但须守住一条边界

我此前把"Self-Forcing 是 CausVid 代码的后继"作为**推断**(同名文件、同类结构、同样的注释)。
**现已明文确认,不再是推断:**

`guandeh17/Self-Forcing` `README.md:98` 原文:
> "This codebase is **built on top of the open-source implementation of
> [CausVid](https://github.com/tianweiy/CausVid)** by Tianwei Yin and the Wan2.1 repo."

旁证(全部 grep 实见):
- `SF/model/causvid.py:8` — `class CausVid(BaseModel)`,即在自身代码库内实现 CausVid 作为对照;
- `SF/model/__init__.py:2,9` — 导出 `CausVid`;`trainer/distillation.py:61-62` — `distribution_loss == "causvid"` 时实例化;
- `SF/wan/modules/causal_model.py:727` — "See Algorithm 2 of CausVid paper https://arxiv.org/abs/2412.07772";
- `SF/model/ode_regression.py:16` — "See Sec 4.3 of CausVid";
- `SF/README.md:83` — ODE 初始化"与 CausVid repo 所述过程相同";
- 文件对应:`SF/pipeline/causal_inference.py` ↔ `CV/causvid/models/wan/causal_inference.py`。

### 可辩护的表述与不可辩护的表述

**可辩护:** 明确声明建立在 CausVid 开源实现之上的后继代码库,
在**对应分支**中包含 KV index 重置(`# reset kv cache` → `global_end_index` / `local_end_index`),
而 CausVid 在同一位置**没有**。

**不可辩护(必须避免):** "Self-Forcing 修复了 CausVid 的 bug。"
补上那段重置可能是 (a) 有意修复,也可能是 (b) Self-Forcing 不同 rollout 结构的必然要求。
**两者本轮都未确立**,不得择一宣称。

### 这对 oracle 强度的影响

R15-E 的 oracle 排序中,"跨层 duplicate-state consistency"只排第 4,**不能单独定罪**。
但本例不是同一代码库内的跨层比较,而是**明文承继关系下的同位置差异**——
证据来源是**后继作者自己的 README 声明**,而非审计者的相似性判断。
**这把它从"我认为应该清"提升为"生态中最接近该代码的实现在同一位置清了"。**
仍需回答的是:该差异是否具有公共可观察后果(条件 5),以及它是否构成 CausVid 的
**公共生命周期合同**违反——后者尚未确立,因为 **CausVid 没有 reset 方法,也没有相应文档合同**。

故 CausVid 当前状态:**静态 HIT,oracle 证据最强,但仍未达到 R15-E 要求的
"公开合同 + 事前冻结关系 + 公共可观察违反"三件套。**

## 2026-09-19 **撤回:CausVid 不是 HIT,是 CLEAN。我的"最强 oracle 实例"无效。**

**这是我今天第二次撤回一个已经当作头条报出去的发现。** 必须完整记录。

### 我错在哪

我声称:Self-Forcing 的 `else` 分支补上了 CausVid 缺失的 KV index 重置,
而这构成"后继实现声明意图"的最强 oracle。**两层都错了。**

**第一层:CausVid 的 KV cache 根本没有那两个字段。**
`causvid/models/wan/causal_inference.py:48-60` 的 `_initialize_kv_cache` 建的字典**只有 `"k"` 和 `"v"`**:
```python
kv_cache1.append({
    "k": torch.zeros([batch_size, 32760, 12, 128], ...),
    "v": torch.zeros([batch_size, 32760, 12, 128], ...)
})
```
全仓库 grep `global_end_index|local_end_index` → **零匹配**。
Self-Forcing 是**自己新增**这两个字段(配合其 `local_attn_size` 滚动缓存设计,`SF:283-292`),
**因此它那段重置不是在修 CausVid 的缺失重置——那两个字段在 CausVid 里不存在。**

**第二层:CausVid 本来就不需要跨调用重置。**
`causal_inference.py:140` — `current_start = block_index * num_frame_per_block * frame_seq_length`,
其中 `block_index` 是**每次 `inference()` 内重新开始的局部循环变量**(`num_blocks` 每次调用重算);
`causal_model.py:140-141` — 按绝对位置写入 `kv_cache["k"][:, current_start:current_end]`;
`causal_model.py:143` — 只读 `kv_cache["k"][:, :current_end]`。
**位置每次从 0 重算、缓存被从头覆写、读取范围恒在本次已写区域内,`current_end` 之外的陈旧内容从不被读。**

**结论:CausVid = CLEAN。** 审计表中 HIT 数由 3 降为 **2**,其中 VMem 的 oracle 仍未决,
故**可辩护的 HIT 只剩 GEN3C 一个**。

### 根因:我犯的正是那条被反复警告的错误

R15-E 早就说过:**"某字段没出现在 reset 路径里"最多是静态异常信号,不是充分证据。**
我接受了这个结论,却在 CausVid 上**又一次只看 `else` 分支的不对称,没有追消费端**。
Stream F 的审计也同样:它的 C2 理由是"`else` 只重置 cross-attention 的 `is_init`",
**观察到了不对称,但没有验证 KV cache 是否存在需要重置的索引状态**。它不存在。

**这是一个假阳性,而且是本方与外部复核同时漏掉的。**

### 立即生效的审计规程修正

**任何 HIT 判定必须追到消费端,证明存在真实的陈旧读取;
仅凭"未发现 reset 路径"不得判 HIT,只能判 SUSPECT-UNTRACED。**

依此重审现有判定:
- **GEN3C 仍成立** —— 其陈旧 `model_seeded` 被 `server_base.py:122` 的准入门**直接读取**,
  且该读取**不是每次重算**的;消费端已追到。与 CausVid 形成对照:
  CausVid 的消费端参数每次重算,GEN3C 的消费端是持久标志。
- **VMem**:消费端已追到(`pipeline.py:708` 无条件读 `self.initial_threshold`),故陈旧读取真实存在;
  但 oracle(该字段"本应被清除")仍 UNRESOLVED。
- **CLEAN 判定普遍安全**,因为它们的依据是"找到了显式重置",而非"没找到"。
- **NEAR 判定(MagicWorld、PlayGen)需按新规程重审**,本轮未做。

### 方法论

**同一条错误我在一天内犯了两次:第一次是 oracle 提案,第二次是 CausVid。
两次都是把"结构不对称"当成"存在缺陷"。**
外部复核在第一次纠正了我,但第二次它自己也漏了 —— 说明该错误不是我个人的疏忽,
而是这类审计的**系统性失效模式**,必须用规程(追消费端)而不是靠警觉来防。

## 2026-09-19 第二个假阳性:PlayGen 的 `user_zeta` 是内存泄漏,不是陈旧读取

`GreatX3/Playable-Game-Generation` HEAD `c3e541987f1d99a3e263db3f6f0b77d74a41b602`(arXiv:2412.00887)。
原判 NEAR,理由是 `disconnect()`(`app.py:194-207`)清了 `user_cmd` / `user_queues` / `user_config` /
`online_player`,**漏了 `user_zeta[user_id]`**。结构属实,但按新规程追消费端后**不成立**。

**键是 Socket.IO 会话 id。** `user_id = request.sid` 出现在全部入口(`app.py:81, 87, 107, 176, 196`);
`request.sid` 每次连接新生成。写入在 `:126` 与 `:149`,读取在 `:136`(守卫 `user_id in user_zeta.keys()`)
与 `:146`,全部发生在 `model_inference(user_id, stop_event)`(`:120`)的 per-user 线程内。
`disconnect()` 设 `stop_event` 并 `inference_thread.join()` / `result_thread.join()`,**读取循环终止**。

**重连获得新 sid → 不同字典键 → 残留的 `user_zeta[旧sid]` 永远不会被任何后续路径读取。**
故漏掉的 `pop` 是**内存泄漏**,不满足"在后续公开调用上被真实读取"这一条件。**降级,不计 HIT/NEAR。**

### 目前为止我自己按新规程复核的结果

| 系统 | 原判 | 新判 | 消费端为何不成立 |
|---|---|---|---|
| **CausVid** | HIT | **CLEAN** | 位置每次调用重算,缓存从头覆写,`current_end` 之外从不读 |
| **PlayGen** | NEAR | **降级** | 键是每连接新生成的 sid,残留条目无路径可读 |
| GEN3C | HIT | **仍成立** | 陈旧 `model_seeded` 被 `server_base.py:122` 直接读,且不重算 |
| VMem | HIT | 陈旧读取真实(`:708` 无条件读),但 **oracle 未决** |

**四个非 CLEAN 判定里,我自己已找出两个假阳性。** 这不是个别疏漏,是该谓词在实际使用中的
**高假阳性率**。两次的共同形态都是:**观察到 reset 路径的结构性不对称,未追消费端。**

### 对方向可行性的直接影响

若一次仔细的审计在 4 个阳性里出 2 个假阳性,那么**基于这种方法的跨系统 prevalence 主张不可信**,
除非每一个阳性都带消费端追踪证据。这正是交给 R18-J 的 Q4 问题,本方先行给出自己的判断:
**当前证据只支持"逐例追踪过的个案",不支持任何 `M/N` 形式的普遍性陈述。**

并且我此前写的"CLEAN 判定普遍安全"**也是错的**:GEN3C 恰恰有显式 `clear_cache()`
(`gen3c_persistent.py:551-553`,清了内层 `model_was_seeded`),缺陷却因**外层另一个字段**未清而存在。
**"存在显式重置"同样不能判 CLEAN;必须证明后续路径读到的每个字段都被重置或重算,包括其他层。**

## 2026-09-19 GEN3C 通过严格检验,并得到一个更干净的缺陷陈述

用杀死 CausVid 与 PlayGen 的同一把尺子重检 GEN3C,**它通过,且证据比原判更强。**

### 外层 `model_seeded` 的完整赋值/读取清单(全仓库 grep,已排除 `model_was_seeded`)

| 位置 | 操作 |
|---|---|
| `gui/api/server_base.py:60` | `= False` —— **全代码库唯一赋 False 处,且在 `__init__` 内** |
| `gui/api/server_base.py:73` | `= True` —— 基类默认 `seed_model`,docstring:"By default, no seeding is required so the default implementation just returns." |
| `gui/api/server_cosmos_base.py:71` | `= True` —— 成功 seed 后 |
| `gui/api/server_debug.py:30, :50` | `= True` |
| `gui/api/server_base.py:122` | **读取**(准入门) |

**`model_seeded = False` 在 `__init__` 之外零结果。一旦置 True,发布代码中没有任何路径把它改回 False。**

### 与两个假阳性的对照(这正是新规程的判别力)

| 系统 | 消费端的值 | 结论 |
|---|---|---|
| CausVid | `current_start` **每次调用重算** | CLEAN |
| PlayGen | 键 `request.sid` **每次连接重生成** | 降级 |
| **GEN3C** | **写入后永不重置** | **HIT 成立** |

三者形态互不相同,而同一条规则把它们正确分开。**这说明规则本身有判别力,不是事后合理化。**

### 更干净的缺陷陈述(取代我此前所有表述)

> **一个单向(monotone)的就绪标志,守卫着一个生命周期可清空(non-monotone)的资源。**

基类把该标志设计成**一次性闩锁**(默认实现直接置 True 并返回,因为"默认无需 seeding");
Cosmos 覆写加入了真实 seeding,**保留了闩锁语义**,但它所守卫的 3D cache 是**可清空的**
(`gen3c_persistent.py:551-553` `clear_cache()` 把 `cache=None`、`model_was_seeded=False`)。
两者生命周期不匹配,故存在"资源已清空而闩锁仍闭合"的状态。

**这不是风格判断,而是可陈述的结构性质:守卫者单调、被守卫资源非单调。**
它也自然解释了为什么内层 `model_was_seeded` 被清而外层没有——内层跟随资源,外层是闩锁。

### 当前可辩护资产(按新规程)

**HIT:GEN3C(1 个,消费端已追,范围限于 `gpu_count==1` 且 `model_name ∈ {cosmos, cosmos-predict1}`)。**
VMem:陈旧读取真实(`pipeline.py:708` 无条件读),**oracle 未决**,且有已测效应 `+0.245 dB`。
CausVid、PlayGen:已撤回。
CLEAN 判定需按"显式重置不足以判 CLEAN"重审(R18-J 进行中)。

## 2026-09-19 R18-J 系统性重审:**该方法学不能支撑 prevalence 主张**

### 更正后的计数(分母必须逐字照抄,不得简写)

**主分母 N=20** = R15-F 中已完成 commit 锁定、公开调用边界与条件 1–4 审计的 video/world-model 候选,
去掉 10 个 OUT-OF-PREDICATE 与 2 个 modality exclusion(32 行审计框中的非 OUT 部分)。

| 类别 | 计数 |
|---|---|
| **静态 HIT** | **2/20 —— VMem、GEN3C** |
| NEAR | 2/20 —— MagicWorld v1、PlayGen |
| CLEAN | 15/20 |
| SUSPECT-UNTRACED | 1/20 —— Matrix-Game 1 |
| **冻结权重下已测行为 HIT** | **0/20 measured** |

敏感性:若把 class-level 状态与公开 API 配置不匹配纳入条件 1–3,Matrix-Game 1 成为第三个 HIT,即 3/20。
**这只是谓词边界敏感性,不得与主结果混写。** 机械按 32 行相加得 2/32,但该分母混合了 OUT 与 modality,**不是 prevalence 估计**。

### 我的两条撤回被独立确认

**CausVid HIT → CLEAN**:与我的追踪一致——cache 字典只有 `k,v`,仓库无 index 字段,
每次 `inference()` 重算 `block_index/current_start/current_end`,写 `[:,current_start:current_end]`、只读 `[:, :current_end]`。
**"旧结论把 reset 分支不对称误当成消费证据。"**
**PlayGen 未升级**,并指出:若严格要求 `self.x` 实例字段,该行**甚至应为 OUT**。

### 我没发现的新情况:Matrix-Game 1

`inference_bench.py:88-97` 写的是 **class-level** TeaCache(`cnt, num_steps, previous_modulated_input, previous_residual`),
不是每次调用的实例 reset;consumer `teacache_forward.py:101-121` 在非起点/终点**先读旧 input/residual**,
计算分支 `:123-233` 才写回。而 `--inference_steps` 与 `--num_steps` 是 CLI 上**分别暴露**的公开参数,
故 call A=40、call B=50 时 B 确实读到 A 的 class-level 值。
固定 benchmark 的 50/50 包络会让 `cnt` 完整回绕,故主表保守标 SUSPECT-UNTRACED。

### Q3:谓词本身确有问题,已给出替换版本

旧条件把"有字段""某分支没 reset""同一对象可再次调用"近似当成 stale read —— **这正是 CausVid 假阳性的来源**;
而 GEN3C 反向证明**单层 reset 不能推出 CLEAN**。替换为三条:跨层所有权识别 → 跟到实际 consumer 并证明无先行重算/覆盖 → 检查所有外层 gate、别名与失败路径。
**条件 3 必须允许 `SUSPECT-UNTRACED`,不得在"未找到 reset"与"HIT"之间跳跃。**

**强制的最小证据四元组(这是真正可交付的审计产物):**
```
(writer on call A, public sequence A→B, exact consumer on B,
 dominance check showing no recompute/overwrite/reset covers it)
```
缺任一项最多 `SUSPECT-UNTRACED`;有意的 history/AR 状态另标 `INTENDED-CONTINUATION`,**不得用来填补缺口**。

### Q4 裁定(原文)

> **This methodology cannot support a prevalence claim.**

理由:CausJid 方向的假阳性与 GEN3C 方向的假阴性**都能通过一次代码复核**;候选集是
**启发式/便利取源的样本,不是抽样框**;各项目的公开 API、配置包络与 intended continuation 不同;
C5 未测量;单个 reviewer 极易把结构信号写成结论。

**故 2/20 只能称"本便利审计框中静态代码路径满足新规则的计数",不得称
"world models 中 stale-state defect 的发生率"。**

要支撑 prevalence,至少需要:预注册总体与纳入规则、**独立双人逐 consumer 复核**、
把 OUT/未检查明确分层、对每个 HIT 做冻结权重的失败/干净 reset 对照。
**即便全部做到,也只能支撑一个定义清楚的审计框内的 prevalence,不能外推到所有公开或闭源系统。**

### 诚实的资产盘点(今日收盘)

- **GEN3C**:oracle 干净(公共准入不变量 + 单向闩锁守卫可清空资源),消费端已追,**但无实测后果**;范围限 `gpu_count==1`。
- **VMem**:消费端已追(`:707-708` 读,`:716-750` 续用),**有实测效应 `+0.245 dB`**,但 **oracle 未决**。
- **两者互补而不重叠:一个有 oracle 没后果,一个有后果没 oracle。**
- **审计四元组**是本方向唯一明确成形、且已被实战检验(正确重分类 CausVid)的可交付产物。
- 已撤回:CausVid、我的构造器等价 oracle、跨层近名字段 oracle、后继实现声明 oracle。

`new_method_validated=false`;`novelty_authorization=NONE`;C6 未松开;全天零 GPU。

## 2026-09-19 VMem oracle 的最强候选:公开的会话边界控件不能隔离 pipeline

R15-E 判 VMem 为 INTENT-ORACLE-UNRESOLVED,并指出唯一出路是**事前注册的公共 metamorphic relation**,
且 relation 必须来自**公开合同或产品语义**,不能是审计者觉得应该等价。我在 pinned 源码中找到了候选来源。

### 已核实的源码事实

| 位置 | 内容 |
|---|---|
| `app.py:22` | `MODEL = VMemPipeline(CONFIG, DEVICE)` —— **模块级单例,导入时创建一次** |
| `app.py:23` | `NAVIGATORS = []` |
| `app.py:181` | `NAVIGATORS.append(Navigator(MODEL, ...))` —— Navigator **包的是同一个 MODEL** |
| `app.py:190` | `NAVIGATORS[0].initialize(...)` |
| `app.py:694` | `gr.Button("Choose New Image", variant="secondary").click(...)` —— **用户可见的新会话控件** |
| `app.py:369-370` | 处理器注释 `# Clear any existing navigators`,随后 `global NAVIGATORS; NAVIGATORS = []` |
| `app.py:363` | 注释 **`# Clear visualization directory to prevent users from seeing each other's generated images`** |

**"Choose New Image" 清的是 `NAVIGATORS`;新建的 `Navigator` 仍包着同一个 `MODEL`。pipeline 对象从不重建。**
而 `initialize()` → `reset()`(`pipeline.py:135-147`)**不清 `initial_threshold`**。
故**用户可见的新会话控件不能把 pipeline 恢复到初始状态**。

### 为什么这比之前所有候选都强

这和 GEN3C 的形态**完全平行**:**一个被代码库自己声明的会话边界,没有覆盖后续路径读取的全部状态。**
而且这里的声明是**双重的**:一个带标签的用户可见按钮 + 处理器自身关于"清理"与"防止跨会话泄漏"的注释。
**它不依赖"某字段没出现在 reset 里"这种已被判定为不充分的论证。**

### 必须守住的边界(否则重蹈今日两次覆辙)

1. `:363` 那条"防止用户看到彼此生成图像"的注释针对的是**可视化目录**,不是 pipeline 状态。
   **把它当作 pipeline 状态隔离意图的证据是外推**,必须标明。
2. 按钮标签 "Choose New Image" 蕴含"新会话"仍是**从标签推断**,不是 API 文档陈述。
3. R15-E 的警告依然适用:**若等价关系只是审计者认为应当等价,问题只是从"字段意图"换成"relation 意图"。**

**故当前状态:oracle 候选显著增强,但未成立。** 需要的是把 R 事前写定并执行,
且 R 的语义来源必须在执行前声明清楚,不得事后挑选最有利的解释。

### 与 GEN3C 的结构对比(两个 HIT 的共同形态)

| | 声明的会话边界 | 未被覆盖的读取 |
|---|---|---|
| GEN3C | `seed_model` 清 cache/histories;`clear_cache()` 清内层 `model_was_seeded` | **外层 `model_seeded`**(`server_base.py:122` 读) |
| VMem | "Choose New Image" 清 `NAVIGATORS`;`initialize()` 调 `reset()` 清 11+ 字段 | **`initial_threshold`**(`pipeline.py:708` 读) |

**共同形态:被声明的重置覆盖了大部分状态,漏掉一个仍被后续读取的字段;
且漏掉的那个都位于与重置动作不同的所有权层级(GEN3C 是外层 wrapper,VMem 是被共享的单例 pipeline)。**
这比"reset 不完整"更精确,也可被证伪——只要找到一个漏掉字段与重置同层的反例即可。

## 2026-09-19 R19-K 裁定:**VMem = `NO-DEFENSIBLE-ORACLE`。我的最强候选被否决,我接受。**

外部复核读到了我刚推送的候选(引用 `RESEARCH_MEMORY.md:2048-2056, local c1c8eb6`)并**否决**了它。
否决理由正是我自己标出的那条边界——但它判定该边界是**致命的,不是可以带着走的**。

### 否决理由(逐条,我接受)

**(a) `initialize()` 的 docstring/签名不足。** 它只说用一张图与相机参数建立内部状态、不额外生成帧
(`pipeline.py:149-161`),**没有**任何关于历史无关性、跨复用对象确定性、或等价于新构造的陈述。
签名本身不能补上这个承诺。README 只给安装/演示用法(`README.md:42-57`),无生命周期等价陈述。

**(b) `initialize()` 调 `reset()` 并重建 `c2ws` 不构成合同。** `reset()` 无 docstring;
`:162` 的 `# Reset internal state` 是**实现注释,不是完整公开合同**。
另:因为 `initialize()` 在 `:180` 重新赋值 `c2ws`,**c2ws 的不对称只是归因证据,不是 oracle**。

**(c) "Choose New Image" 被否决。**
> "A user-facing session boundary is a plausible intent, but the source does not state the needed
> observable relation 'same image/camera/intrinsics produce the same retrieval selection regardless
> of prior pipeline history.' Treating the label as that exact contract would be an **auditor's inference**."

并且 `:362-363` 那条注释关心的是**防止用户看到彼此的文件**,不是 pipeline 选择输出的相等性
——**正是我自己标注为"外推"的那一点**。

### 它纠正了我一个从 R15-G 一直带着的错误假设

我一直以为 VMem 的"retrieval-set-differs"路线是**零 GPU**的。**不是。**
构造器加载 VMem/VAE/CLIP/CUT3R(`pipeline.py:47-90`);`initialize` 执行 VAE 与图像编码(`:173-177`);
非平凡的上下文选择使用 surfel 渲染(`:631-647`);公开轨迹准备要跑扩散(`:1269-1298`)。
**选择身份只有在"等价的 bank 已经存在"之后才能避开最终扩散**;
而复用已封存 JSON 或手工预填字段**就离开了公开序列,因而根本没有检验 R**。

我已复核:三个档案脚本**都硬编码 `device = 'cuda'`**
(`nms_off_threshold_independence.py:77`、`arm_state_isolation_test.py:82`、`leak_regime_census.py:93`)。

### Q2:已封存材料不构成该检验

`isolate_arm_state` 调了公开 `reset()`,但**随后直接**清空可变列表、字典、`global_step` 并
`delattr(initial_threshold)`(`:68-80`),回执自身也把它标为"reset 加清除每个可变检索字段加删除 initial_threshold"
并记录 `reset_alone_is_insufficient`(`:181-186`)。
**这证明的是 harness 为使两臂可比所需要的东西,不证明 VMem 的公开 reset 合同承诺了某种跨历史可观察结果。**
`delattr` 是关于 harness 隔离需求的证据,也很可能是所测效应的来源,但**其本身不是公开合同违反**。

三个档案各自只授权更窄的陈述(595599 顺序不变性门 / 595614 零扩散普查 / 595625 阈值独立性),
**没有任何一个比较"新构造 pipeline" vs "已使用 pipeline + 仅公开 `initialize(...)`" 然后做同一公开观测。**

### 最终盘点(今日诚实结论)

> **GEN3C 是唯一可辩护的 HIT,但没有实测后果;
> VMem 是唯一的实测效应,但没有可辩护的缺陷 oracle。**

`+0.245 dB` 作为**已执行两臂的测量**依然真实,但**在没有 oracle 的情况下不能被提升为生命周期缺陷**。
VMem 应记录为**有实测效应的 worked example,不附带缺陷主张**。

`new_method_validated=false`;`novelty_authorization=NONE`;C6 未松开;全天零 GPU。

## 2026-09-19 GEN3C 上游披露检查:同样零报告;并标明一条我不得越过的约束

R13-A 对 VMem 做过上游检查(四个精确词 issue+PR `total_count = 0`),**但从未对 GEN3C 做过**。现补上。

我自查(GitHub Search API,`repo:nv-tlabs/GEN3C`):

| 检索词 | issue + PR `total_count` |
|---|---|
| `model_seeded` | **0** |
| `seed_model` | **0** |
| `clear_cache` | **0** |

仓库规模作对照:`open_issues_count`(含 PR)= **33**,stars = **1424**。
故**该条件在上游同样未被报告**——与 VMem 情形一致。
边界:这是"截至本日公开可见的 issue/PR 搜索结果",不是"作者从未私下讨论过",
也不排除 GitHub 搜索索引的延迟或范围限制。

### 我不得越过的约束(主动标明)

`AGENTS.md` 明载:**"No messages to the advisor or others are authorized."**
**向上游提交 issue、发邮件或以任何方式联系 maintainer,都属于"对外发消息",没有授权。**
我不会执行,也不在 owner 明确决定前建议执行。

同时记录一个需要 owner 判断的事实性问题:本条件位于**已发布研究代码的服务端准入门**。
它的性质是**鲁棒性缺陷**(需要运维者自己的服务被按特定序列驱动,后果是内部状态不一致),
**不是权限提升或数据泄露**。研究代码的惯例处置通常是提 GitHub issue 而非安全通告。
**该判断与是否披露、何时披露,均属 owner 决定,不由本记录代为决定。**

## 2026-09-19 R20-L 终局裁定:**STOP**

### 裁定

> **STOP.** owner 仍要求 method 贡献。已核验记录中**不存在幸存的、已验证的方法方向**,
> 且**没有任何剩余检查能把下面两个部分资产变成方法**。
> 在当前 scope 下,不再证成任何新的 GPU 运行、训练、权重下载、上游消息或候选检索。
> **这是终局处置,不是"该代码不可被研究"的断言。**

唯一的条件性未来是 **owner 对 C6 的人类决定**(接受 audit/measurement 交付物);
**该决定尚未作出,且即便作出也不会把这项工作变成方法。**

### Q2:为什么两个资产不能拼成完整主张(我原本想这么做,被驳回,我接受)

> **`(oracle, no consequence)` + `(consequence, no oracle)` ≠ `(oracle and consequence)`。**
> 两个实验的 consumer、状态所有者、公开合同、干预序列全都不同。
> VMem 的测量不能验证 GEN3C 的 cache-admission 路径;
> GEN3C 的准入 oracle 不能追溯地把 VMem 那个 **harness 定义的**干净臂变成公共 metamorphic relation。

**把二者的并集当作同一个缺陷类,正是四元组被引入来防止的那个错误:
writer / public sequence / exact consumer / dominance check 四项必须属于同一个案例。**
配对文档只有在**明确标注为审计或 worked-example 报告**时才合法;
**不得**呈现为方法、通用 stale-state prevalence 主张、或"陈旧状态导致世界模型质量下降"的证据。

### 上游披露:独立双方一致

它的 GEN3C 检查与我的独立检查**完全一致**:同一 GitHub REST API、
`model_seeded` / `seed_model` / `clear_cache` / `model_was_seeded` 四词,**issue+PR 与 commit 检索均零匹配**。
另核 NVIDIA 安全页面,无相关条目。**与 VMem 情形一致:两个系统的该条件在上游均未被报告。**

### 给导师的事实性陈述(可原样宣读,无修饰)

> 本项目审计了已发布、冻结的世界模型代码中的上下文选择与生命周期状态。
> 它确立了 VMem 的一个陈旧读取,并在有限的、已暴露的 14 窗口面板上测得
> `+0.245 dB` 的 clean-vs-leaked 对比,**但未能找到把该对比称为缺陷所需的公共 oracle**;
> 它确立了 GEN3C 已发布代码中的服务端准入/闩锁不匹配,**但未测量冻结权重下的下游后果**。
> 审计四元组经受住了对抗性复查并重新分类了 CausVid;
> 构造器等价 oracle、跨层近名字段 oracle、后继实现声明、"Choose New Image" oracle、
> 以及"retrieval-set 路线零 GPU"的假设,**均已撤回**。
> 便利面板不是 prevalence 样本,冻结权重下已测 HIT 计数为 **0/20**,**未验证任何方法**。
> 未决项为:VMem 的真正公共 R、GEN3C 的冻结权重后果、以及任一项目 maintainer 的确认。
> **在方法贡献要求未变的前提下,记录在案的终局处置是 STOP。**

`new_method_validated=false`;`novelty_authorization=NONE`;800 GPU-hours 维持撤回;全天零 GPU。

## 2026-09-19 事故与恢复:后台 codex 进程静默回退了 45 行账本

**发现方式:** 收尾核对时 `grep -c "R20-L 终局裁定" RESEARCH_MEMORY.md` 返回 **0**,
而该条目明明已由 `a8ec3e7` 提交(该 commit 的 stat 显示 `RESEARCH_MEMORY.md | 45 ++++`)。

**根因:** 我在一个持有 `workspace-write` 的 `codex exec`(R20-L)**仍在运行**时执行了 `gwm-sync`。
该进程把 `RESEARCH_MEMORY.md` 回退成它读入时的版本(2232 → 2187 行),
随后我的同步把这次回退**与收口文件一起提交**为 `a75a603`,提交信息为
"add consolidated lifecycle-audit closeout document",**完全没有提示删除**。
该进程退出时又从工作树删除了 `docs/LIFECYCLE_AUDIT_CLOSEOUT_20260919.md`(但它仍在 HEAD 中)。

**所有表面指标都正常:** push 成功、`git status` 干净、三处哈希一致。

**恢复(无损,未做任何破坏性操作):**
- `git checkout -- docs/LIFECYCLE_AUDIT_CLOSEOUT_20260919.md` → 148 行还原;
- 从 `git show a8ec3e7:RESEARCH_MEMORY.md | tail -45` 取回原文并重新追加 → 2232 行,条目在位;
- 保留 codex 对**自己报告**的那处修改(`AGENTS.md:15`; `AGENTS.md:15` → 单个,无害去重)。

**已落地的防护:** `gwm-sync` 新增并发写入者守卫(exit 8),
在 fetch 前 `pgrep -f 'codex exec'`,发现存活进程即拒绝同步。原则记为 v2.21。

**这是今天第二次同步器缺陷**(v2.17 是"先 commit 后 fetch 把陈旧变成回退")。
两次的共同点是:**同步器把"当前工作树"当成"我的意图",而工作树可能被别的因素改写。**

## 2026-09-20 **OWNER DECISION: C6 RELAXED**(人类授权,非工具推定)

owner 明确指示:**松开 C6** —— 即取消"贡献必须是 method"这一要求。

### 该决定改变什么

- **审计 / 测量 / 评价类贡献现在是可接受的交付物。**
- **轴 (g) 测量与评价随之解禁。** 关键事实:该轴此前被标为"被 owner 要求的贡献类型排除",
  **它是被要求排除的,不是被文献占据排除的**。
  八条轴中其余七条我都做过占据性检索;**(g) 从未被评估过**,因为评估了也不可用。
  **故 (g) 是唯一占据状态未知的轴。**
- R20-L 的 STOP 裁定的前提是"owner 仍要求 method 贡献"。该前提已不成立,**裁定条件失效**。
  但 R20-L 同时说明:松开 C6 **不会**把已有工作变成方法。这一点不因授权而改变。

### 该决定**不**改变什么(逐条列明,防止授权蔓延)

- `new_method_validated=false` —— 不变;
- `novelty_authorization=NONE` —— 不变;
- **800 GPU-hour tranche 维持撤回** —— C6 与算力授权是两件事,owner 未提及算力;
- **对外消息仍被禁止**(`AGENTS.md`),不得联系任何 maintainer;
- 不得训练、微调、下载权重;
- R13-B 的差距分析仍然有效:即便 C6 松开,现有材料**仍未达到可发表的 diagnostic contribution 门槛**
  —— 缺跨系统外部效度(2/20 静态、0/20 实测)、缺 conclusion impact、artifact 未被外部采用。

### 我对 "为什么还没有新方法" 的回答(记录在案)

1. **八轴全占。** 冻结消费者把可实现想法全逼向轴 (a),而该轴被占且**额外代数受限**
   (共同目标平方误差融合下矩阵项对最优权重零贡献,数值验证 4.4e-16)。
2. **松 C1–C5 够不着。** C1/C2 单放空操作;C3 落在已占的 (a)/(b)/(f);
   C1+C2+C3 绕过代数陷阱但未绕过占据;C4 只买到"接口可用"。
3. **够得着也跑不完。** 最小 pilot 约 800 GPU-hours,原型级约 3000,需训练数据 + 独立 held-out,
   ScanNet++ v2 申请 lead time 2–6 周未启动;至少 6 周,本学期不可行。
4. **流程问题(我认)。** Astra 第十轮:四次失败"强烈指控本项目的方法发现流程与所选干预边界"。
   项目把大量时间投在测量基础设施与完整性门上,真正开始机制搜索时可执行空间已很窄。

**下一步:对轴 (g) 做占据性评估——这是八条轴中唯一从未被评估的一条。**

## 2026-09-20 R21-M 轴 (g) 占据评估:**AXIS-G-OCCUPIED —— 八条轴全部关闭**

C6 松开后,轴 (g) 是八条轴中唯一占据状态未知的一条(此前被标为"被 owner 贡献类型要求排除",
**是被要求排除,不是被文献占据排除**)。现已评估完毕。

### 裁定

**三个子区全部被占,且是在"可发表的一般性主张"这一层面被占:**

| 子区 | 状态 |
|---|---|
| (g1) metrics | OCCUPIED —— 从 FVD/VBench 式视频度量到相机/几何专用世界模型度量 |
| (g2) benchmarks | OCCUPIED —— 相机控制、交互、长视界稳定性、记忆/revisit 套件 |
| **(g3) experimental-validity machinery** | **OCCUPIED** —— 我预判"被占得少得多",**预判错误** |

### 关掉 (g3) 的两篇(我已逐条核实标题为真)

- **arXiv:2607.07196 — *Validate the Dream Before You Trust Its Verdict: Admissibility for
  World-Model Simulators***:规定生成式世界模型作为 test oracle 时必须先被 accredited,
  其裁决才能算作 assurance evidence;定义 **L0–L4 admissibility ladder**
  (生成质量 → 动作鲁棒性 → OOD/envelope → 失败归因 → 模拟裁决向现实的迁移)。
  **这是本项目 validity gate 思路的一般化版本,且已发表。**
- **arXiv:2606.31672 — *WorldRoamBench: An Open-World Benchmark for Long-Horizon Stability of
  Interactive World Models***:在物理评分**之前**发布显式 validity gate。

### Lead 2 亦被直接填掉

我曾寄望于 Steady-Forcing(2606.14732)自己喊出的评价缺口
("VBench 奖励 drift 引起的光流作为 Dynamic Degree,却不直接惩罚 texture hardening 与 flow stagnation")。
**该缺口已被 arXiv:2608.28694 *SNF-Bench: Separating Static Drift from Natural Flow in
Long-Horizon Fixed-Camera Video Generation* 填补。**

### 其余已核实的占据证据(10/10 引用为真)

WBench(2605.25874)· WorldMark(2604.21686)· PlayWorld(2608.13552)·
Omni-WorldBench(2603.22212)· MBench(2606.00793)·
Geometry-Aware RoPE for Consistent Video World Model(2602.07854)·
Quantitative Video World Model Evaluation for Geometric-Consistency(2605.15185)·
**Preregistration for Experiments with AI Agents(2606.11217)** —— 连预注册也被占。

### 对项目的意义

本项目的 order-invariance gate、pre-scoring census、byte-identity gate、pre-declared discard、
审计四元组,**作为 worked audit 仍然有用,但其原则已不再是未被占据的**。
窄表述("没有论文恰好具有本项目的 retrieval-arm 字节同一性/顺序/溯源门")
被标为 **UNVERIFIED 且 search-bounded**,**不能支撑 AXIS-G-OPEN**:
审稿人可以指出直接的 world-model validity-gate 先例,再把本项目的包归类为
**单消费者实现,缺乏跨系统外部效度与外部采用**。

**结论:在"冻结消费者 + 零 GPU + 本学期"三约束下,八条轴均已被占。
这不再是推断,而是逐条检索加引用核实的结果。**

### 仍未被检验的唯一假设

**这张轴图本身可能就是错的工具。** 十三轮问的都是"方向 X 被占了吗",
从未问过"这个领域里一个被接收的贡献长什么形状"。该问题已交 R22-N。

## 2026-09-20 贡献形态分析(我的第一遍,**待 astra 复核,勿当结论**)

十四轮来所有占据检索都问同一个问题:**"方向 X 被占了吗?"**
该问法预设:**新颖性是靠在固定轴图上找一块无主机制获得的。**
本轮第一次问另一个问题:**这个领域里一篇被接收的论文,贡献长什么形状?**

### 我的初判分类(8 篇,摘要已实取)

| 论文(会议) | 形态 |
|---|---|
| GEN3C(CVPR 2025 Highlight)2503.03751 | ④ 表示替换(显式 3D cache)+ ① |
| EscherNet(CVPR 2024)2402.03908 | ④ 表示替换(相机位置编码)+ ⑤ 规模扩展 |
| VMem 2506.18903 | ④ 表示替换(surfel-indexed view memory) |
| Diffusion Forcing(NeurIPS 2024)2407.01392 | ② **问题重构**(统一 next-token 预测与 full-sequence diffusion 两族) |
| Self Forcing 2506.08009 | ① 新机制(针对已命名问题 exposure bias) |
| **rliable(NeurIPS 2021 Outstanding)2108.13264** | ⑦ **负面结果** + ⑧ 测量 |
| **Deep RL that Matters(AAAI 2018)1709.06560** | ⑦ **负面结果** |
| **Implementation Matters(ICLR 2020)2005.12729** | ⑦ **负面结果** |

### 两条初步观察

**观察一:形态 ① 在本样本中是少数。**
世界模型那批的主导形态是 **④ 表示替换** ——
GEN3C 换成显式 3D 缓存、EscherNet 换成相机位置编码、VMem 换成 surfel 索引记忆。
**而本项目十四轮全部对着 ① 优化。** 若 astra 在更大样本上证实该分布,
则结论不是"没有创新空间",而是**"一直在找错种类的东西"**。

**观察二:形态 ⑦(负面/局限结果)是高规格的真实形态,本项目从未尝试。**
rliable 获 NeurIPS Outstanding Paper;Deep RL that Matters 为 AAAI;Implementation Matters 为 ICLR。
三者共同结构:**"这个领域相信的东西经不起检验。"**

### 必须同时记录的限制(防止自我说服)

**⑦ 之所以能发,是因为它推翻了领域所相信的东西。**
本项目的负面结果(预声明修复失败 −0.016 dB、15/20 CLEAN、0/20 实测)
**是关于本项目自身 harness 的,不是关于领域信念的**。

唯一可能触及领域信念的是 VMem 那条:
**其论文宣称 surfel-indexed memory 带来一致性,而实测其检索在 12/14 窗口选到不同帧集合。**
但 R19-K 已裁定:**缺可辩护 oracle,不能把该测量提升为缺陷主张。**

**故本条记录是"待检验的形态假设",不是新方向。**
`new_method_validated=false`;`novelty_authorization=NONE`。

### 执行状态

R22-N 连续三次 `Selected model is at capacity`(82k / 131k / 22k tokens)——
**容量错误,非逻辑失败**。未静默更换模型(owner 明令每轮须用 astra ultra),第四次重跑中。

## 2026-09-20 R22-N 贡献形态分析:**SHAPE-AVAILABLE**(第一个非纯关闭的结果)

`PRODUCED_BY=gpt-5.6-sol/xhigh; PENDING_ASTRA_REVIEW` —— astra 五次容量拒绝(见下),owner 授权替代。

### 先纠正我自己的初判

我上一条记了"形态 ①(既有任务上的新机制)在样本中是少数"。**未被证实,撤回该措辞。**
本轮明确:2/18 的平铺分布是**刻意平衡取样的产物,不是领域估计**;我自选的 8 篇同样不具代表性。

**能站住的更弱结论:形态 ① 显然不是唯一被接收的形态,
而项目此前"只找机制"的搜索目标不具代表性。** 要真实比例需随机、按会议分层的语料。

### 裁定:SHAPE-AVAILABLE —— measurement / validity apparatus

**面向审稿人的主张(逐字保留):**

> **For stateful released video/world-model systems, reset correctness cannot be inferred either
> from a field being absent from `reset()` or from a reset call being present. A four-tuple audit
> that links the writer on call A, the public A→B sequence, the exact consumer on B, and a
> dominance proof that no recompute/overwrite/reset covers that state is a falsifiable validity
> apparatus that reclassifies apparent lifecycle hits and exposes order-dependent stale-state paths.**

**关键点:今天两个方向的错误恰好是该主张的内容,不是失败。**
CausVid 假阳性 = "字段不在 reset 里不能推出缺陷";GEN3C 假阴性 = "存在 reset 调用不能推出干净"。

### 已核实的被接收先例(两条 proceedings 直链均 HTTP 200)

- **VBench: Comprehensive Benchmark Suite for Video Generative Models** — **CVPR 2024**,arXiv:2311.17982
  <https://openaccess.thecvf.com/content/CVPR2024/html/Huang_VBench_Comprehensive_Benchmark_Suite_for_Video_Generative_Models_CVPR_2024_paper.html>
- **WorldModelBench: Judging Video Generation Models As World Models** — **NeurIPS 2025 Datasets and Benchmarks Track**,arXiv:2502.20694
  <https://proceedings.neurips.cc/paper_files/paper/2025/hash/4ec03ed08a3fcb59e1c815b5598beff1-Abstract-Datasets_and_Benchmarks_Track.html>

本轮 11/11 arXiv 引用经我独立核实标题吻合。

### 从未尝试过的形态,以及为什么(Q3)

1. **Regime extension** —— 从未尝试。**是冻结消费者 + 零 GPU + 撤回额度的刻意后果,不是疏忽。**
2. **Scaling / efficiency** —— 从未尝试,同样被算力与消费者约束阻断。
3. **System integration 作为新颖性主张** —— 从未尝试;项目有 wrapper 与审计基础设施,但从未把"组合"当作可发表主张。

问题重构、新能力定义、负面/局限、测量 —— **在生命周期审计这一轮才被触及,且只到探索性/静态证据层级。**

### 存活条件(6 条,全部零 GPU / CPU 范围)

1. **先冻结**四元组、判定类与 dominance 规则,再重审;发布 manifest、代码路径、哈希与负控制;
2. **独立复核者对标签盲审**,报告一致性,并与两条朴素规则("字段不在 reset 里"、"存在 reset 调用")对比
   —— **关键结果必须是可复现的重分类,不是挑出来的轶事**;
3. **再加 2–3 个独立发布系统**,含**已知干净的负控制**与一个阳性案例;**无声明抽样框则不得声称 prevalence**;
4. 至少一个阳性案例给出端到端后果**或**完全可复现的静态非法状态 trace;
   **若只有静态证据,须称 static lifecycle defect,不得暗示生成视频退化**;
5. artifact 必须 **CPU 可运行且可被采用**:一条命令、不可变输入、trace 输出、字节同一性、
   HIT/measured HIT/NEAR/CLEAN 四类明确分离;
6. **VMem 的测量必须与审计主张分离** —— 现有对比不得被用来制造缺失的 oracle/后果合取。

### 最强反对意见(接受)

不是四元组不自洽,而是**现有证据尚未建立外部效度与结论影响**:面板是便利取样;
GEN3C 静态案例无端到端运行;VMem 有测量但无可辩护 oracle;`+0.245 dB` 是暴露开发序列上的泄漏对比、仅 RGB PSNR。
**"15/20 CLEAN"是看起来像可靠性的计数,不是 prevalence 结果。**

若独立复核、跨系统案例与可采用的 CPU artifact 无法产出,**正确的降级是 `INSUFFICIENT`。**

### 执行层记录:容量诊断

astra 五次 `model is at capacity`(82k/131k/22k/3.7k tokens,以及去 priority 后仍拒)。
**诊断结论:`service_tier="priority"` 池饱和是其中两次的真因,不是模型不可用。**
`gpt-5.6-sol` 去掉 priority 后可用;`gpt-6-astra` 去掉 priority 后仍拒 —— astra 本身饱和。
**以后遇 capacity,第一步应去掉 priority 再试,而非直接换模型。** 我前四次重试因一直带 priority 而白跑。

`new_method_validated=false`;`novelty_authorization=NONE`;冻结消费者约束不变;800 GPU-hours 维持撤回。

## 2026-09-20 R23-O Astra 复核:**推翻 sol 的 SHAPE-AVAILABLE,降级为 INSUFFICIENT**

我在 prompt 里写过:"十四轮'否'之后第一个'是',恰恰最可能是动机性推理"。**它确实没站住。**

### 四条彼此独立的降级理由

1. **Q1 新颖性未证成,目前看像是已有机制的领域迁移/组合。**
   四元组是"有用的、保守的内部审计契约",但 R22-N **未证明它是一个新 oracle**,
   而非 state-pollution 与 order-dependence 既有机制在生成模型上的领域特化组合。

2. **Q2 两条朴素规则失效是反例,不是贡献。**
   未检出任何已发表来源把"两条朴素规则都失效"写成具名的双向定理(标 **UNVERIFIED**),
   **但其各个方向都不令人意外**:PolDet(消费者已知前即存在污染)、
   PRADET 与 test-independence(动态识别 reader/order 关系)、
   ODRepair/iFixFlakies(reset helper 不完整)、NIO(重复执行暴露自污染)。
   **两个项目内案例只确立领域相关性,不确立新颖性或发生率。**

3. **Q3 R22-N 自身的推理有普适主张超出受限证据**,且其 static-HIT 分类
   **把 VMem 未决的 oracle 与 GEN3C 的静态 oracle 混在一起**。

4. **Q4 独立复核条件当前无法满足**,且那六条**遗漏了语义生命周期 oracle 与基线不可约化检验**。

### 最重要的缺失条件(Astra 原话要点)

> **最重要的缺失条件是 semantic oracle。"不在 `reset()` 里"只是异常信号。**
> 审计必须声明:公开边界何时承诺隔离、何时持久化是有意的 history/autoregression、哪些状态被允许存活。
> **dominance 证明也需要声明范围**:确切 commit、公开 API/配置包络、别名、异常、对象替换、动态分派。
> **"任何地方都不存在覆盖"不能仅因一次本地源码搜索没找到赋值就成立。**

### 关于独立复核者(直接影响可行性)

> **"owner 控制的重标注或另一个在环模型,都不是独立盲审者。"**
> 若无法获得环外复核者,该主张**必须停留在受限的内部审计协议层级并标记 `INSUFFICIENT`**。

我事先就把这个问题写进了 Q4:**我供不了独立复核者**——我是审计者,astra 已在环十六轮。
它确认:这不使整个想法逻辑上不可能,**但确实阻断了当前设定下的可发表验证包**。

### 其他被点名遗漏的条件

(i) 预注册的抽样框与版本/commit 同一性;(ii) 对 PolDet/PRADET/order-reordering/ODRepair/NIO 的**基线对比**;
(iii) 测试已知假阳/假阴的**变异或有限状态控制**;(iv) 已发布 artifact 的**独立再执行**;
(v) 明确区分**静态代码可达性 / 语义缺陷 / 已测输出后果**的错误分类学。

### 重新考虑的最低路径

冻结生命周期契约与范围 → 建立**预注册的真值套件**(含已知假阳/假阴控制:
absent-but-recomputed、reset-present-but-wrong-scope、conditional/late reset、
overwrite-before-consume、intentional history continuation、genuine stale consumer)→
对上述既有工作做基线对比 → 取得环外复核 →
**关键结果必须是有效性判定的改进,不是两个轶事。**

### 记录纪律

R22-N 的 SHAPE-AVAILABLE 我已按当时证据记录;**本降级以同等显著度记录**,不追溯删改前条。
`new_method_validated=false`;`novelty_authorization=NONE`;冻结消费者不变;800 GPU-hours 维持撤回。

## 2026-09-20 R24-P 无约束生成:**我的八轴图在结构上是不完整的**

本轮首次反转流程:**不给轴图、不给占据表、不给已关闭清单,只生成不评判。**
产出 896 行,Part A(冻结+零 GPU)与 Part B(假设解冻)合计 45+ 个机制级候选,**全部未经占据筛查**。

### Part C:八槽的十一个结构性盲点(示例引用 6/6 已核实为真)

**根本诊断:** 八槽把搜索空间建成一个**单一运行时管线的 intervention topology**
(证据读 / 条件表示 / 持久状态 / 目标分解 / 跨调用转移 / 几何耦合 / 调用内采样 / 测量)。
它适合回答"**在现有消费者的哪个节点动手**",**但不是论文贡献的完整本体**。

> **"增加第九个内部轴还不够;不少贡献改变的是边界、数据、任务或判定规则,
> 无法定位到任何一个运行时节点。"**

| 盲点 | 会被我的枚举错分/漏掉的真实工作 |
|---|---|
| C1 任务/能力定义与 action-observation contract | **Genie** 2402.15391 —— 塞进"条件表示"会丢掉 action contract 本身 |
| C2 数据引擎、监督与课程 | 2406.17711 —— 归入 retrieval 会混淆"训练数据选择"与"在线 context 选择" |
| C3 学习目标与训练—推理契约 | **Diffusion Forcing / Self Forcing** —— 叫"within-call inference dynamics"**会漏掉训练契约** |
| C4 系统/编译器/硬件/资源合同 | **FlashAttention** 2205.14135 —— **八槽没有"执行介质/资源合同"这一维** |
| C5 benchmark/数据集/验证协议**作为对象** | VBench、WorldModelBench —— 对象是可复用的评测边界,不只是给 VMem 加指标 |
| C6 交互闭环、策略与用户协议 | Genie、**GAIA-1** 2309.17080 |
| C7 不确定性、风险、拒答与 assurance | **2512.05927 World Models That Know When They Don't Know** |
| C8 理论性质与因果可辨识性 | 横跨所有节点,不能指向单一 slot |
| C9 表征学习范式 | **2404.08471(V-JEPA)** —— 归入"条件表示"会把训练 regime 与部署条件混为一谈 |
| C10 跨层共同设计与可复现 artifact | 八槽会把这种科学结论错误缩成"measurement" |
| C11 **应改用多层地图** | `object of change × time of intervention × claim/stakeholder`,每项链接 evidence contract |

**C11 是可操作的修正:** 一个候选可同时落在 data+training+runtime,**不应强迫它选唯一 slot**;
这样"生成→筛选"的顺序才不会再被我自己的轴图提前截断。

### Part D:我二十三轮都没问过的那个问题

> **"我们真正要交付的贡献对象和 estimand 是什么,谁会据此改变决定;
> 在不预设内部干预轴的情况下,哪个最小证据合同足以让这个决定可复核?"**

口语版:先问**"我要改变的是系统、任务、证据合同,还是读者对 world model 这个词的判断?
谁会因为这项工作采取不同动作?"** —— 而不是先问**"哪个内部槽位还空着?"**

> 旧流程默认:固定一个消费者,找一个尚未被占的内部干预,就可能得到方法论文。
> **这个默认把四个层次压扁了。**

**最要害的一句:**
> **"它避免把'没有找到第九个槽位'误当成'没有研究问题'。"**

### 正确顺序(采纳)

**先固定 `claim + estimand + stakeholder + minimal evidence contract`,再从 A/B 中选一个可证伪机制。**

### 必须同时记录的限制(防止把这条当成突破)

1. **这不证明存在创新。** 它证明的是**搜索被框错了**,而在正确框架下的重新搜索**尚未进行**。
2. **45+ 候选全部未经占据筛查**,按今天的记录,先前每一轮占据检索的结果都是"已占"。
3. Part B 的候选需要解冻 + 算力 + 时间三者同时满足,**本学期仍不可行**。
4. R23-O 刚刚把诊断方向降级为 `INSUFFICIENT`;**本轮不改变该裁定**。

`new_method_validated=false`;`novelty_authorization=NONE`;800 GPU-hours 维持撤回。

---

## 2026-09-20 R25-Q / R26-R:合同筛选(先 claim 后占据)——**第一次出现幸存者**

两轮均为 `codex exec -m gpt-6-astra -c model_reasoning_effort="ultra"`(去 `service_tier="priority"`)。
本轮**刻意把 occupancy 推迟**,按 R24-P 的处方执行:
先固定 `claim + estimand + stakeholder + minimal evidence contract`,再谈占据。
前二十三轮的顺序是反的,所以每一轮都只能返回"已占"。

### R25-Q(Part A,零 GPU / 冻结消费者)

范围自动扩到 R24-P 的全部 55 项 A 候选(A1–A25、A45–A60、A87–A100;
原文 `CODEX_R24P_GENERATION_20260920.md:30-219、:538-648、:798-894`),不是我 prompt 里写的 25 项。

**裁定:LIVE 10 / NEEDS-RESOURCES 16 / NO-CLAIM 27 / NO-STAKEHOLDER 2 —— 45/55 本轮不存活。**
(我独立重数表格状态列,四个数字吻合。)

十个幸存者全部是**选择层**(retrieval/selection)claim,**都不宣称生成质量**:
A4 多假设 query 共识 · A5 覆盖–距离–新颖性重排 · A6 遮挡/深度风险优先 ·
A14 自适应候选预算 · A22 受限 source counterfactual replay ·
A89 per-frame mass cap · A90 per-surfel 贡献归一化 · A91 校准 focal/principal point ·
A92 min/softmin 轨迹距离 · A94 重复 source-ID 衰减。

**Q4 = 有。** 本周零 GPU 可执行。决策价值最高的首个产物是
**A6 的 CPU-only selector risk receipt**(本轮未创建该文件):
逐候选 projected conflict / hole / visible-area、固定 K 选择、
distance-only 与 clean-geometry 负控制、预登记聚合规则与 kill threshold。
明确边界:"只判断选择层风险 proxy,不调用 VMem、不读 future outcome、不宣称生成质量。"

按决策价值/单位成本排序:A22 > A6 > A5 > A14 > A4。
A22 有前置条件——**只有在 exact replay / 几何 source artifact 可读时才成立**,否则立刻降为 NEEDS-RESOURCES。

45 个死亡候选的共同失败模式(Q3),第 6 条最重要:
> 生成轮次仍隐含 slot-first 偏差:先问哪个内部位置能改,再补 claim。

即 R24-P 诊断出的病,在 R24-P **自己生成候选时仍然存在**。

### R26-R(Part B,需解冻)

**裁定:本学期没有任何 Part B 路径能完成一个可辩护的决定性结果,即使 owner 今天解冻。**
死因不是候选没价值,而是每条活路线都需要**尚不存在的独立 held-out 证据**;
走 ScanNet++ v2 还要 owner+supervisor 签字并等 2–6 周,而账本已记录 term mostly consumed。

最便宜的条件路径:**B21 质量—新颖性双门控写入**,约 200–800 H800-h、6–14 周,
外加 ScanNet++ 的 2–6 周关键路径;须解除 F/T + W + U + C。

**Q4 建议:现在不要解冻。** 先要 owner 回答四件事(目标是否改为 8–14 周后续工作 /
是否签 ScanNet++ 申请 / 给完整 bundle 还是单项空授权 / 是否把第二 consumer 与独立复核写进验收)。
理由:空授权只买到 wrapper、首轮图或开发面板,买不到能经受审查的 method result。

### 两轮独立给出的同一条源码更正

R24-P 说 `self.c2ws` "只有两处写入"。两轮**各自独立**指出这不完整:
`:180` 绑定、`:1297` append,但 `:1360` 还有 undo 路径的 `pop()` 原位删除,且无 setter/property。

**我独立复核:`grep -n "self\.c2ws" pipeline.py` 共 21 处,
其中仅 180 / 1297 / 1360 是 mutation,其余全为读取或注释行。更正成立。**
其余行号声明(`get_context_info:1249`、`torch.cat:1263`、
`get_translation_scaling_factor:1265`、R24-P 的 B1@225、S/M/L/XL@223)逐条复核,全部命中。

### 我造成的两个缺口

1. **B36–B55 未筛。** R24-P 实际生成了 55 项 B 候选,我的 prompt 只写 B1–B35。
   R26-R 在正文第 7 行主动声明了这个边界,没有顺带裁定。20 项待补。
2. **并发删除。** 见 `RESEARCH_PRINCIPLES.md` v2.22:R25-Q 在收尾自检时
   `rm` 掉了 R26-R 的产物。全文从日志 heredoc 回显中复原,
   109 行/33275 字节,与 R26-R 自测一致,SHA-256 `aed2ac16f93fa496...`。

### 授权状态(未变)

`new_method_validated=false`;`novelty_authorization=NONE`;800 GPU-hours 维持撤回;
对外消息仍被禁止。**"LIVE" 不等于"新"** —— 本轮明确不做 occupancy,
十个幸存者是否被占据,是下一轮的事。

---

## 2026-09-20 R28-T:B36–B55 合同筛选(补上我留的缺口)

`gpt-6-astra` / `ultra`,跑在**隔离 git worktree** 里(v2.22 首次实施)。
R24-P 的 B36–B55 原文在 `CODEX_R24P_GENERATION_20260920.md:435`(B36)至 `:776`(B55)。
**我独立复核:`:650-781` 区间有 19 个 `### B` 标题,加上 `:435` 的 B36 恰好 20 项,与声明一致。**

**裁定:LIVE 6 / UNPRICED 14 / NO-CLAIM 0 / NO-STAKEHOLDER 0 / NOT-FALSIFIABLE 0。**

六个 LIVE:B36 资源感知稀疏注意力 · B39 自然失败挖掘器 · B45 几何因果干预目标 ·
B46 分位数校准与 conformal 拒答 · B48 空间哈希/八叉树神经缓存 · B49 pose-graph/地图联合优化。

### 与 A 侧判然不同的分布,以及它给出的理由

A 侧 27/55 是 NO-CLAIM;B 侧尾部 **0** 个 NO-CLAIM。R28-T 明确解释了为什么不是宽松:
> 这些候选都能指出潜在决策者和一个可证伪的结果;**未定义合同不应被偷换成"不可证伪"**。

即 UNPRICED(合同未闭合)与 NOT-FALSIFIABLE(原则上无法证伪)是两种死法,
把前者写成后者会高估自己的筛除严格度。这条区分我接受。

### Q1:没有任何 B36–B55 候选胜过 B21

B39 的原始 S–M 只是候选生成阶段的粗量级,不能当作已比 B21 便宜;
B36 约 M–L,B45/B46/B48/B49 至少 M–L;B55 与全部 UNPRICED 连任务/接口合同都没闭合。
**B21 仍是最便宜的可信条件路径**(~200–800 H800-h、6–14 周 + ScanNet++ 2–6 周关键路径,须 F/T+W+U+C)。

### Q2:本轮唯一的新信息——一扇更窄的授权门

**B36 / B48 / B49 若实现为 exact runtime kernel 与经典 pose-graph、不学习任何新权重,
可以走 `H+SN+U+C` 的系统 bundle,免去 `F/T+W`。**
这是 26/28 两轮里唯一一处"授权面可以更小"的发现。
但它是**条件性**的:一旦改用 learned mask / learned cache / learned weighting,立刻退回 `F/T+W+U+C`。
且没有任何尾部候选能绕开 `H`(独立 held-out)或 `C`(算力),
也没有任何候选能把"单独给 U"变成决定性科学结果。

### Q3:不改变"现在不要解冻"

与 R26-R 一致,且四个前置问题不变。

### v2.22 首次实施结果:有效

R28-T 跑在 `$SP/wt_r28t`,主工作树在整轮期间只有我自己的两个 PROMPT 未跟踪文件,
worktree 内 `git status` 只有它自己的一个新文件。**兄弟进程互删没有复现。**

### 授权状态(未变)

`new_method_validated=false`;`novelty_authorization=NONE`;800 GPU-hours 维持撤回。
R28-T 自述其嵌套 codex 调用两次失败(`Operation not permitted`;
换临时 `CODEX_HOME` 后 `401 Unauthorized / Missing bearer`),**没有虚构外部裁定** —— 这是正确处理。

---

## 2026-09-20 R27-S:占据检查**未完成** —— codex 账户额度耗尽

这一轮是整条新管线的关键一环:对十个幸存者做占据检查。**它没有产出任何文件。**

在 395,697 tokens 处被打断:
```
ERROR: You've hit your usage limit.
try again at Sep 26th, 2026 1:12 AM.
```
`S_EXIT=1`,`work/agents/CODEX_R27S_*` 不存在,`git status` 只有我自己的两个 PROMPT 文件。

**十个幸存者是否被占据,目前无答案。** 不得把本条记录当作"未被占据"。

### 一个我差点犯的归因错误

日志里有大量成篇的表格与参考文献(WorldMem、VideoTitans、PAGER、HSC、LoRA3D、STORM、
FGB-Future/SOCF-A/DLV 的证伪矩阵等)。**这些不是 R27-S 的产出。**
它们是 R27-S 在检索途中读取并回显的**仓库既有文件**:
`work/agents/innovation_literature_scan_round2_20260916.md`、`innovation_live_20260915.md` 等,日期为 09-15/16。
`grep` 出来的"实质性散文"里,绝大部分属于这一类。
**如果直接把它们当成本轮占据结论记进账本,就是凭空制造了一份没有人做出的裁定。**
依据:那两个文件在仓库里可检索到,且早于本轮五天。

### 它留下的确实属于自己的东西:检索轨迹

R27-S 的 web search 查询串是它自己的行为记录,可以用。这些查询指向的先例**高度具体**,
且多数是**有名字的经典方法**,不是泛泛的"有人做过类似的":

| 幸存者 | R27-S 正在查的先例 |
|---|---|
| A4 query 共识稳定性 | Nogueira & Brown,*Measuring Stability of Feature Selection*(JMLR) |
| A5 覆盖–距离–新颖性重排 | Carbonell & Goldstein 1998 **MMR**(SIGIR);`arXiv:2604.05259` |
| A6 遮挡/深度风险优先 | *Neural Visibility Field for Uncertainty-Driven Active Mapping*(CVPR 2024) |
| A22 受限 source counterfactual | **ContextCite** `arXiv:2409.00729` |
| A89 per-frame mass cap | **H2O Heavy-Hitter Oracle** `arXiv:2306.14048` |
| A90 per-surfel 贡献归一化 | **EWA Surface Splatting**(2002) |
| A91 校准 focal/principal point | Zhang,相机标定(IEEE TPAMI) |

### 我自己核验的部分(非 codex 产出,标明作者)

用 arXiv API 直接查证,四个 ID 全部为真且标题相符:
- `2409.00729` = *ContextCite: Attributing Model Generation to Context*
- `2306.14048` = *H₂O: Heavy-Hitter Oracle for Efficient Generative Inference of LLMs*(2023-06-24)
- `2604.05259` = *Coverage Optimization for Camera View Selection*(2026-04-06)
- `2602.07854` = *Geometry-Aware Rotary Position Embedding for Consistent Video World Model*

读了后两篇摘要,给出**初步、非结论性**的判断:

**COVER(2604.05259)对 A5 威胁最大。** 它的核心是
"minimizing a tractable approximation of the Fisher Information Gain, which reduces to
favoring viewpoints that **cover geometry that has been insufficiently observed by past cameras**",
并在 "fixed and embodied data acquisition scenarios" 上评测。
覆盖准则本身已公开发表。
**但对象不同**:COVER 是 *active* view selection(决定相机下一步去哪,采集阶段),
A5 是 *passive* retrieval(在冻结生成器前挑已观测帧)。
按 registry 四元组,`object of change` 与 `time of intervention` 都不同。
**这指向 ADJACENT 而非 OCCUPIED,但 delta 是否够一个 reviewer 接受,我没有答案。**

**H2O 对 A89 是反向的。** H2O 是*保留* heavy hitter(目标是吞吐/显存),
A89 是*抑制*单帧吸走全部质量(目标是 weighted unique support)。估计量不同。同样偏 ADJACENT。

**以上只读了两篇摘要,不构成占据裁定。** 正式裁定需要按 claim 三元组逐条做完,
且要读到具体章节而非摘要。这件事**没有做完**。

### 结论

新管线的前两步(合同筛选 A / B)已完成并有结果;**第三步(占据)被额度中断**。
`new_method_validated=false`;`novelty_authorization=NONE`;800 GPU-hours 维持撤回。

---

## 2026-09-21 R29-P1:GPT-6 Pro 占据裁定(五个 A 侧幸存者)—— **无 codex 外部复核**

渠道:本机 `ChatGPT.app`,档位 **Pro, 5 of 5**,经 AppleScript 驱动(见 `AGENTS.md` 新增章节)。
原因:codex 额度耗尽至 2026-09-26;`gpt-6-pro` 在 ChatGPT 账户下经 codex 调用返回
`400 not supported`,但在 app 内本来就可用。

### 总裁定

**五项全部 ADJACENT,无一 OCCUPIED。** 但它同时给出第二个、更重要的结论:

> 当前结论不是"五项已被文献全部占位",而是
> **"五项都没有被精确占位证据直接杀死,但按现在的主张,没有一项足以独立支撑一篇有竞争力的方法论文"。**
> 这两个结论必须分开。

它明确拒绝给任何一项 OPEN,理由是:**不会用"没搜到完全相同的三个指标名字"来声称开放**,
并主动声明检索未穷尽(SLAM/SfM/MVS 补充材料未全查,部分全文链接无法访问),
因此 ADJACENT 意为"已核实近邻不能直接占掉此估计量",而非"已证明不存在更近的论文"。

| 候选 | 裁定 | 它对贡献大小的判断 |
|---|---|---|
| A4 query 共识 | ADJACENT | 小;"加扰动、投票、更稳定"不够 |
| A5 覆盖–距离–新颖性 | ADJACENT | **很小**;高度接近覆盖优化与去冗余的应用 |
| A6 遮挡/深度风险 | ADJACENT | **五项中最可能形成实质几何结果** |
| A14 自适应预算 | ADJACENT | 有工程价值;通用"自适应更省算力"剩余为空 |
| A22 source 反事实 | ADJACENT | 有审计价值;删源归因本身无方法新颖性 |

建议:A22 当测量资格检查,A5 当强基线,A4 当稳健性控制,只给 A6/A14 很小的 CPU 证据预算。

### 它提出的、我没想到的致命反驳(全部接受)

1. **A4 的稳定性可以被无用选择器赢下。** 永远返回同一组 K 帧,扰动不稳定性恒为零。
   因此 A4 即使成立也未建立部署价值。还须防止把"每次重跑共识"偷换成
   "预生成一张固定共识列表应对所有扰动"——后者是构造性地消除变化。
2. **A5 的 hole-rate 与 coverage 可能不是两份独立证据。** 若用同一目标像素全集和互补定义,
   `hole-rate = 1 − coverage`。且若 duplicate 仅指重复 frame ID,无放回选择自动保证无重复,
   那不是几何结果。最强基线是**直接贪心最大化边际联合覆盖**,不是 MMR 的某个加权版本。
3. **A6 存在伪改善路径:** 选择器丢掉难像素后,只在剩余重叠区算冲突率,冲突率自然下降。
   **必须先固定可比较的评价区域和分母,再调权重。** 另:目标真值深度可用于评估,
   但若部署时不可得就不能进入选帧风险分数,否则测到的是"带额外信息的选择"。
4. **A22 的归一化可能无定义:** 若无干预复放方差为零,"除以复放方差"就没有定义;
   不得事后加一个方便的极小常数再把巨大比值解释成强因果证据。
   更根本的:**身份支持 ≠ 深度必要性** —— 两个 source 提供完全相同深度,A 因 tie-breaking 被记为身份;
   删 A 后 B 接管,深度完全不变而身份改变。这不是归因失败,也不证明 A 没被用到。
5. **A14 必须与一组充分调优的固定预算比**,而非只比一个明显过大的预算;
   且须计入停止判据、投影、候选生成与打分的全部 CPU 成本。
   "先把所有候选算完再宣布只用了前一部分"不构成节省。

### 引用核验(我自己做,13 条)

**零编造。** 10 个 arXiv ID 全部真实且标题完全吻合。具体数字抽查:

- DIBR `1802.03079` Table:`AVERAGE NUMBER OF PIXELS IN HOLES (PER FRAME)`,
  Ballet 2PV=**877** → 2PV+2CV=**96** / 2PV+SW=**210**,减少率 89.02%/76.09%。
  我自行验算 877→96 = 89.05%、877→210 = 76.06%,与论文一致。**连"选择性 warping 反而留下更多孔洞"的反直觉方向都对。**
- Tao `2110.00696`:`IMI 275.20 ms` / `Tao 47.39 ms`,紧邻 Table VII,故该行确在 Table VI。
- JMLR 18(2018) 1–54,§6.2 `Figure 12: Comparing the stability of LASSO and different
  parametrisations of Stability Selection in four classification/regression data sets`
  (Spambase/Boston housing/Sonar/Madelon)。**注意实为三作者**(Nogueira, Sechidis, Brown)。
- The Visual Computer 2025/07 DOI `10.1007/s00371-025-03944-3` 解析正常。
- MMR DOI `10.1145/290941.291025`:ACM 返回 403,**未能访问核验**(标为未验,非错误)。

**唯一瑕疵:** Al-Jazzazi `2505.15636` 原文为 "**up to** 30-40% decrease"(上界),
Pro 转述为"可减少**约** 30%–40%",把上界说成典型值。方向正确,程度轻微夸大。

### 一次我差点记下的假错误

初核 VMem 时我用最新版,发现消融在 **§4.4** 且全文 `FOV` 出现 **0 次**,
与 Pro 所称 "§4.6 含 temporal-only / FOV-overlap / top-K 消融" 不符,一度判为引用错误。
**排除版本差异后:v1 确为 `4.6. Ablation Study`,且紧邻文本为 `Temporal | Field of View (FOV) | VMem`。**
Pro 原文写的是"所核 **v1** 的 §4.6" —— 版本、节号、内容三项全中,最新版只是重编号并改了措辞。
**是我忽略了它标注的版本。** 这是今日第三次险些记入不实内容(前两次:
险将仓库旧文件当作 R27-S 产出;R25-Q 删除 R26-R 成果)。

### 对我自己"主动 vs 被动"防线的修正

我(以及 Pro)都判定 COVER `2604.05259` 与 NVF `2406.06948` 属 ADJACENT,
理由是 active acquisition ≠ passive retrieval(`object of change` 与 `time of intervention` 均不同)。
**但 Pro 指出这条防线不足以排除所有近邻**,并举出 The Visual Computer 2025 那篇
submodular view selection——它正是**从已有视图中**结合质量与覆盖做选择。
我核验该文献真实存在。**因此"别人都是主动采集"这条辩护被实质削弱,必须停止依赖它。**

### 状态

`new_method_validated=false`;`novelty_authorization=NONE`;800 GPU-hours 维持撤回。
**本轮无 codex 仓库内复核** —— Pro 读不到仓库,所有仓库事实均由我转述,
它无法履行 "verify, do not trust"。待 9/26 额度恢复后由 astra 补做。

---

## 2026-09-21 **OWNER DECISION C7:走 world model 创新路线,接受跨学期**

Owner 原话:针对"想做 world model 创新 → 必须解冻(训练/微调/权重/算力),
而且要独立 held-out 数据,ScanNet++ 申请 2–6 周还没启动,本学期做不完"——
**"没事 走这个"。**

### 这条决策确定了什么

1. **方向选定:Part B(需解冻的世界模型路线),不是 Part A(选择层)。**
2. **明确接受本学期无法完成**,目标改为跨学期工作。
   这直接推翻了 R26-R/R28-T 全部 `TERM-IMPOSSIBLE` 标记的**决策含义** ——
   那些标记本身仍然成立(事实没变),但它们不再构成否决理由。
3. **A 侧五个幸存者退居次要。** 它们仍是有效的零 GPU 工程/测量件,
   但不再是主线交付。理由见同日 R29-P1:
   按当前表述没有一项能独立支撑一篇有竞争力的方法论文,且它们**不是世界模型创新** ——
   全部是选择层主张,明确不宣称生成质量,不改变模型如何表示或预测世界。

### 这条决策**没有**确定什么(必须显式补齐,不得推定)

- **未确定解冻哪几项。** R26-R 的记号:`T`(从头训练)、`F`(微调/LoRA/adapter)、
  `W`(新 head/adapter/权重)、`U`(上游/消费者/状态写回改动)、`MC`(多消费者/真实 action interface)、
  `C`(恢复可用 GPU-hours)。**R26-R 明确警告:只给单项是"空授权",
  会把候选停在接口或首图,买不到能经受审查的 method result。**
- **未确定具体候选。** B 侧 55 项中,真正触及世界建模的是
  B3(增量 neural field/tri-plane 记忆)、B4(可写可删可修订记忆控制器)、
  B5(长程 recurrent world-state token)、B8(世界坐标扩散+可微渲染)、
  B9(静态/动态 slot 分解)、B10(闭环轨迹规划)。
  注意:R26-R 推荐的 **B21 是"最便宜的可信路径",不是"最像世界模型创新的路径"** ——
  这两个判据在本次决策后已经分离,不得混用。
- **未改变授权旗标。** `new_method_validated=false`;`novelty_authorization=NONE`。
  这两项记录的是"结果是否已验证",与方向决策无关,不因 C7 变动。
- **未恢复算力。** 800 H800-hour tranche 仍为撤回状态;恢复需另行决定。
- **对外消息仍被禁止**(`AGENTS.md`)。

### 立即进入关键路径的事项

**ScanNet++ v2 申请是当前最长前置项:2–6 周,需 owner 与 supervisor 双签,尚未启动。**
它不消耗 GPU、不依赖解冻范围、也不依赖候选选定 —— 因此**应当最先启动**,
否则无论后续怎么决策,都会被这 2–6 周卡住。
(依据:`docs/proposal_v2/NEW_PROPOSAL_DRAFT_20260919.md:82-97,112-147`,
由 R26-R 与 R28-T 两轮独立复核。)

### 与 proposal 的关系(须向 supervisor 说明)

现行 proposal `NEW_PROPOSAL_DRAFT_20260919.md` 的机制是 **lineage-aware memory fusion**,
且第 24 行明写 **"Retrieval is held fixed"** —— 它冻结检索、只改融合。
该 proposal 已因代数缺陷被标记 **NO-GO as written**(最优权重下矩阵项提供零额外信息,
本项目数值验证误差 4.4e-16),800 GPU-hours 被 reviewer 撤回。
**C7 选择的 B 侧路线与该 proposal 不是同一机制**,需要新的 proposal 或实质修订,
不能当作原 proposal 的继续执行。

---

## 2026-09-21 R30-P2:GPT-6 Pro 审查 C7 决策 —— **B4 主实验 NO-GO**

渠道同 R29-P1(ChatGPT.app,Pro 5/5)。提示词要求它**攻击**这个决策而非配合,
并明写"不要因为 owner 已经决定就手软"。

### 裁定

> **审稿结论:这项决策目前是错的,应撤回"B4 已具备执行条件"的判断。**
> "选择 B4、只开放 F、继续禁止 U/W/C"不是一个困难但可以逐步推进的研究方案,
> 而是**一个关键依赖没有被授权的方案**。接受跨学期,并不会自动获得写回接口、
> 训练与评估算力、独立测试数据。
>
> 当前状态应记录为:**方向选择尚未转化为可执行研究合同;B4 主实验 NO-GO。**

### 第一个停滞点不是训练,也不是首图

**是"第一次把 gate 决策接进状态提交"。**

形式化:`x̂_t = G_θ(R(M_t, c_t), c_t, ξ_t)`,`M_{t+1} = W_0(M_t, x̂_t)`。
B4 必须引入 `a_t = g_φ(...)` 使 `M_{t+1} = W_gate(M_t, x̂_t, a_t)`,
且 `a_t` 必须**实际影响**接受写入/合并/衰减/撤销/恢复。

> 具体卡点:新生成视图及其几何被提交到 surfel memory / cache 时,**谁被允许执行 gate 的决定?**
> 现在的答案是:**没有。U 禁止改变这条状态更新路径。**
> 你可以写一个输出 `accept=False` 的函数,但既有写回仍照常提交,
> **它只是旁观检测器,不是 gate。**

四级停滞表(当前最多能得到什么):

| 层次 | 停滞点 | 最多得到 |
|---|---|---|
| 方法接入 | 首次将 gate 接入状态提交/删除/恢复 | 接口规格、旁观评分、离线模拟 |
| 真实学习 | 对指定模型执行真实训练所需算力 | 训练代码/配置/CPU 小模型测试 |
| 闭环验证 | gate 改变历史后重新生成后续轨迹 | 旧日志上的分析,非干预后真实轨迹 |
| 主张成立 | 独立自然失效长轨迹上评估污染与召回 | 开发集个案,非合同要求的泛化证据 |

并指出:**旧轨迹重放不能免费替代闭环实验。** gate 一旦改变 M,后续生成输入就变了;
沿用旧系统生成的后续帧只是"固定后续内容下的离线记账"。

**对我的直接提问"空授权是否已经发生",它答:是,而且停在接口层,比首图更早。**

### 它抓到的、我没看出来的逻辑不一致(最重要的一点)

> 负责人的决策存在明显不一致:
> 因为 Part A 只是决定"给生成器看哪些旧帧",所以认为它不属于世界模型创新;
> 却因为 B4 决定"哪些帧继续留在状态中",就视为已经进入世界模型创新。
> **从读侧移动到写侧,不足以完成这种升级。**

判别标准(它给的):
> 在相同、合法的状态管理协议与证据输入条件下,新方法是否**改变了模型对未来视角、
> 遮挡后重现内容及跨视角几何的预测能力**?
> 而不是:修掉错误的 reset 或 cache latch 后,系统是否更少出错?

`write/merge/decay/rollback` 是**操作清单,不是已成立的研究机制**;
给这些操作加一个 learned gate 也不自动改变贡献类型 ——
学一个缓存准入分类器,仍可能只是**学习型状态管理**。

### 它更正了我的两处说法

1. **`T`(从头训练)不是 B4 的逻辑必需项。** `H+SN+T+W+U+C` 与 500–2,000 H800-h
   是**某条实施路线的报价,不是从 B4 主张必然推出的最小资源定理**。
2. **"固定 wrapper 原型不算决定性结果" ≠ "任何非学习方法都不能有决定性结果"。**

另:`F`/`W` 边界未写清。LoRA(`2106.09685`)冻结原权重训练低秩增量,
**结果仍包含需要使用的参数**。若 `W` 禁止创建/保存/加载/评估任何适配参数,则 F 与 W 直接冲突;
若 `W` 仅禁止把权重作为最终交付物,训练本身未必被禁。**它拒绝把这一点夸大成不存在的逻辑定理。**

### 三个不能省的实验条件

1. **主基线必须是"修复已知生命周期缺陷后"的 no-gate 系统。**
   原版有 bug、我的 gate 没 bug,不能单独证明 gate 的研究增量。
   **若修复已知缺陷后 B4 收益消失,应终止主张,而不是把修 bug 的收益计入 gate。**
2. **等容量必须覆盖 gate 实际可用的全部记忆** —— 旧版本、影子状态、待提交缓冲区、
   方法可读的日志,都不能藏在"主缓存之外"免费使用。
3. **"污染少"必须与"仍在做有用的记忆更新"联合成立。**
   永不写入/频繁清空/总退回种子状态的系统很容易少污染,但同时失去探索、召回和进展。

### 现在**确实**能做、且在正路上的一件事

**"B4 前置状态正确性资格包"** —— 四个契约:调用局部状态契约、reset 契约、
资源就绪契约、失败与恢复契约。不需要 GPU,不需要独立场景。

**关键:它明说"即使撤回 F,它仍然可以做。F 对此几乎没有贡献。"**
也就是说 owner 刚授权的那一项,对当前唯一可执行的工作**没有用处**。

防"安慰奖"的条件:必须直接成为后续 B4 的**准入条件** ——
一个 gate 连 reset、失败后状态、版本恢复都处理不好,就没有资格进入污染率与召回评估。
并须区分**程序正确性 oracle**(可在 CPU 建立)与**几何内容 oracle**(不可由前者冒充)。

### 用两个缺陷做更强框架:可行,但改变研究性质

它承认存在比原 B4 更贴合现有证据的框架 ——
"自回归三维记忆生成系统的跨模块状态生命周期正确性",
并明确划出两个缺陷**直接支持**与**不直接支持**的结论:

| 缺陷 | 直接支持 | **不**直接支持 |
|---|---|---|
| VMem 阈值跨调用残留 | 控制状态作用域/初始化/reset 是否与声明一致 | 生成几何内容因此普遍错误;学习 gate 能识别这种错误 |
| GEN3C 清空后就绪失配 | 资源失效/初始化异常与 readiness 是否一致 | 长轨迹语义污染可被检测且不损召回地修复 |

> 你现在有的是**生命周期缺陷的证据**,不是"一个学习型污染检测器应当存在、应当有效"的证据。
> 对确定性的生命周期不变量,通常应先采用确定性的执行约束。
> **让模型学会绕过未初始化字段或失配 latch,是在学习容忍程序错误,而不是证明世界建模能力。**

但它同时判定:这个框架**更明确地属于系统正确性研究,而非 owner 指定的模型本体创新**。

### 引用核验(我自己做)

- `2106.09685` **LoRA: Low-Rank Adaptation of Large Language Models** ✅
- `2506.08009` **Self Forcing: Bridging the Train-Test Gap in Autoregressive Video Diffusion** ✅
- `2510.09212` **Stable Video Infinity: Infinite-Length Video Generation with Error Recycling** ✅
  后两篇正是其"通用自回归训练失配/自纠错微调不新"论断的依据,描述与标题吻合。
- TTAB、Hypothesis、Boost 异常安全:未核(支撑性引用,非关键论断)。

**它自己的诚实披露:** "没有取得与你锁定版本一致的完整复现材料,
因此**不声称独立复现了那两个缺陷**" —— 正确处理,未冒充仓库内核查。

### 三条路(它给的),需 owner 选择

1. **仍以世界模型创新为目标** → 撤销 B4 作为已获准主方向,
   把生命周期工作保留为**前置正确性工作**,重新选一个真正改变
   世界状态表示/转移/证据修订能力的 Part-B 主张。
   **"没有哪个候选应仅凭'属于 Part B'获准执行。"**
2. **坚持原 B4** → 至少补齐:窄范围 `U`(写回干预权)、独立长轨迹评估数据、
   真实闭环算力、完整重放;学习型实现还要解决 F/W 边界与训练数据。
   **且必须明确它首先是状态管理方法,不能预先认定达到世界模型创新门槛。**
3. **坚持当前零 GPU / 无 U / 无 held-out** → 只做正确性资格包与数据/授权手续,
   **不得记作 B4 方法实验已经启动。**

### 状态

`new_method_validated=false`;`novelty_authorization=NONE`;
800 H800-hour 维持撤回(它另指出:新方案应提出**新的、分阶段**预算申请,
旧数值不是当前已授权资源,也不是免复核的预算依据)。
**本轮无 codex 仓库内复核**,待 9/26 由 astra 补做。
