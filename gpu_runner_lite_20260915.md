# H800/S103 VMem runner checklist (plan only)

依据 `work/S103_H800_VMEM_BASELINE_PREFLIGHT_20260915.json`、S101/S102 receipts；本文件不代表已运行实验。

## 1. No-data model-load smoke

前提：远端源码包完整验 SHA；`vmem` 与 `extern/CUT3R` 双 `PYTHONPATH`；Python/torch 环境固定。S101 job 585971 已证明 H800、CUDA 和项目 import 可用，但不等于权重加载。

运行前门：对 VMem、CUT3R、OpenCLIP safetensors、ft-mse VAE 及 VAE config 记录远端字节数/SHA，并与 S103 preflight 比较。OpenCLIP 的本地 SHA 已在 S103 preflight 核验；远端 VMem 传输仍为 partial，故当前状态 `BLOCKED_WEIGHT_TRANSFER`，不得加载或宣称通过。

加载门：VMem 用 `torch.load(map_location="cpu", weights_only=True)`，去 `module.` 前缀后 `strict=True`；missing/unexpected keys 必须均为 0。VAE 只用固定 config 与 `diffusion_pytorch_model.safetensors`，禁止静默替换模型。

smoke 必须 `eval()` 并记录 Python/torch/CUDA、GPU/驱动/显存、参数与 buffer 数量/dtype/device、wall time/RSS。严禁读取 RGB/depth/pose/GT、split/condition NPZ，严禁 forward、采样、CLIP encode、renderer 和 scoring。回执字段必须明确 `data_access=false`, `gt_access=false`, `forward_calls=0`, `sampling_calls=0`。

产物：`SMOKE_RECEIPT.json`、stdout/stderr、`sha256_manifest.json`、`pip_freeze.txt`、nvidia-smi、作业 ID/主机/Slurm 状态。任一 hash、配置或 strict key 门失败，保留失败目录，不写 PASS。

## 2. 首个冻结 VMem calibration/development baseline

仅在权重传输完整、上述 smoke 成功、implementation/pre-run audit 通过后执行。S102 当前只允许 synthetic ICL controlled scope：history `[1,31,61,91]`，calibration/development targets `[121,151,181,211]`；held-out `1056..1508` 必须在 prediction seal 后才可由隔离 scorer 打开。单场景、frame-index/30Hz、非真实世界和非跨场景结论。

冻结门：封存 S103 preflight、S102 split/GT-isolation manifest、所有源码/环境/权重/config SHA、seed 42、CUDA fp16、576×576、4 context + 4 target、50 steps、输入顺序和预算；冻结时间早于解码和运行。

实现门：运行 declared VMem pipeline，不引入 GRC selector 或其他选择策略，不改网络/采样数学。预先检查并封存 target/history IDs、mask、条件形状、latent/output dtype。

运行门：记录实际 forward、50-step 计数、每 target 输出、失败/超时、显存峰值、wall time、I/O 和 RNG/seed；不得减步数、分辨率或帧数。中断保留 partial receipt。

封存门：先保存 raw outputs/latents、target IDs、输入/权重/source hashes、环境及所有文件 SHA，生成 `PREDICTION_SEAL.json`；seal 前不得读 held-out GT。随后独立 readback，再运行隔离 scorer。

评分门：只报告预注册 RGB-D/pose/reprojection、coverage/missing、失败样例和成本。结论限于“该 synthetic split 上可复现 VMem 行为”，不得推出 GRC benefit、真实泛化或 novelty。

## Receipt 顺序与停止规则

`01_source_weight_manifest.json` → `02_model_load_smoke/SMOKE_RECEIPT.json` → `03_prerun_audit.json` → `04_baseline_run/INPUT_MANIFEST.json` → `RUN_RECEIPT.json` → `PREDICTION_SEAL.json` → `05_independent_readback.json` → seal 后 `06_heldout_score/SCORING_RECEIPT.json`。

每份 receipt 要有 schema、实际 UTC、job/host、路径、SHA、状态和 next step。权重 partial/hash mismatch、配置漂移、Gate0/审计未过、未来数据提前访问、预算/seed 变化或 seal 缺失，立即标记 `BLOCKED`/`FAILED`，保留原件；不启动正式 GRC。当前 `new_method_validated=false`、`novelty_authorization=NONE`。
