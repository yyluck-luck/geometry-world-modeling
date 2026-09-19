# S104 结果记录：SuperPOD 环境构建与 CUT3R 首次成功前向

**批次状态：`CONSOLIDATED_BACKFILL`（归位补记）**
**独立复算：未完成**
**科学结论：无。本批次不产生任何 GRC 证据，不解开 Gate 0。**

---

## 0. 这份文档的性质

本文是**补记**,不是当时写下的记录。2026-09-15 全天在 HKUST SuperPOD 上的工作,其脚本、SLURM 输出和回执当时散落在集群家目录 `/home/yliutz/`,项目主账 `research_events.jsonl` 的最后一条停在 **2026-09-15T02:33:48+08:00**,因此当天 02:30 之后的工作**从未入账**。

本文所有时间来自**两类可核来源**,不是事后回忆:

1. SLURM 日志正文内自带的自报 UTC 时间戳(如 `date -u +%FT%TZ` 的输出);
2. 文件 mtime。

下表同时给出两者,凡有出入均以日志正文为准并注明。

---

## 1. 环境事实(先确认我们在哪里)

| 项 | 值 | 来源 |
|---|---|---|
| 登录节点 | `slogin-01` / `slogin-02` | 本次只读登录 |
| 集群 | HKUST SuperPOD,Ubuntu 22.04.3,x86_64 | `/etc/os-release` |
| 调度 | Slurm 23.02.6,账号 `mscitspod2026` | `sinfo` / `sacctmgr` |
| 分区 `normal` | 23 节点 `dgx-[04-06,09-10,13-15,21,23,26-29,31,35,37-39,46,51-52,54]`,不限时 | `sinfo` |
| 分区 `cpu` | 2 节点 `intel-[01-02]`,限时 12:00:00 | `sinfo` |
| 家目录 | `sc-superpod-nfs.hpcstorage.ust.hk:/home` (NFS),200 G,已用 39 G | `df -h` |
| 实际取得 GPU | **NVIDIA H800,81559 MiB**,driver 570.158.01 / 580.x | 各作业 `nvidia-smi` |

> **重要更正**:项目历史文档(`RESEARCH_PRINCIPLES.md`、`README.md`)写的是"本机 M3 Max 64 GB、暂无远程 GPU"。这句话描述的是**原来的 Mac 工作站**,不是本机。本机是 SuperPOD 登录节点,**没有本地 GPU**,一切模型运算必须经 `sbatch`/`srun`。该表述已过期,应在下一轮记忆更新中修正。

---

## 2. 作业时间线(北京时间 UTC+8)

| 作业号 | 时间 | 内容 | 结果 |
|---|---|---|---|
| 583967 | 02:30:00 | S101 GPU smoke #1 | ❌ FAILED |
| 583968 | 02:30:21 | S101 GPU smoke #2 | ❌ FAILED |
| 583984 | 02:36:32–02:37:50 | 下载 ICL-NUIM `living_room_traj0` | ✅ 711,444,709 B |
| 584004 | 02:49:11 | GPU 探针(dgx-21) | ⚠️ `torch_available False` |
| 584012 | 02:52 | 归档结构审查 v1 | ❌ FAILED |
| 584045 | 02:54 | 归档结构审查 v2 | ✅ |
| 584274 | 03:25 | torch/cu126 环境自检 | ⚠️ `diffusers` 缺失 |
| 585900 | 10:45:58–10:46:07 | 环境导入烟测(dgx-05) | ❌ `modeling` 导入失败 |
| 585928 | 10:47:46–10:48:14 | 环境导入烟测(dgx-14) | ❌ `add_ckpt_path` 失败 |
| 585971 | 10:51:13–10:51:43 | 环境导入烟测(dgx-09) | ✅ 全部 IMPORT_OK |
| 586074 | 10:58:29–10:58:51 | ICL-NUIM 抽样解码(`cpu`/intel-01) | ✅ |
| 586628 | 13:13:09 | CUT3R 前向 #1 | ❌ `weights_only` / OmegaConf |
| 586634 | 13:19:53 | CUT3R 前向 #2 | ❌ `No validated RoPE implementation` |
| 586684 | 13:44:07 | cuRoPE 编译 #1 | ❌ 无本地 CUDA |
| 586691 | 13:47:07 | cuRoPE 编译 #2 | ❌ `nvc++: Unknown switch: -fwrapv` |
| 586699 | 13:53:53 | cuRoPE 编译 #3 | ✅ `.so` 316,048 B |
| **586719** | **14:08:34–14:09** | **CUT3R 前向 #3** | ✅ **SUCCESS** |

14:09 之后**本机无任何后续动作**。

---

## 3. 逐步详情

### 3.1 作业 583967 / 583968 — GPU smoke(两个都失败)

两个 5 分钟 job 都真实分配到 `dgx-09`,并返回了 H800 身份:

```
dgx-09 / 2026-09-14T18:30:00Z / NVIDIA H800, 81559 MiB, 570.158.01 / Python 3.10.12
NameError: name 'TORCH_AVAILABLE' is not defined
```

**失败原因**:可选 torch 打印段落里的 shell 引号错误,与 GPU、CUDA、模型无关。

**边界**:**不能**把这两个 job 算作 VMem forward、模型加载或任何科学实验。它们只证明了 GPU 可以被分配到。

### 3.2 作业 583984 + 归档审查 — ICL-NUIM 数据资格

下载回执(`icl_nuim_download_receipt.txt`,自报 UTC):

```
url     = https://www.doc.ic.ac.uk/~ahanda/living_room_traj0_frei_png.tar.gz
mode    = download_only_no_unpack_no_model_no_gt_score
bytes   = 711444709
sha256  = 4eca8c2e9f77c1bd7436c746d22ea6144b8c01fe9bc29a84e734186823f1f1ad
```

归档结构审查 v1(584012)**失败**:

```
struct.error: unpack requires a buffer of 13 bytes
→ audit_icl_nuim_archive.py:21 的 PNG IHDR 解析读越界
```

v2(584045)**成功**——修复后仅读结构,不解码像素:

| 项 | 值 |
|---|---|
| 成员数 | 3020 |
| `rgb/*.png` | 1509 |
| `depth/*.png` | 1509 |
| association 行 | 1509(1509 对全部存在) |
| 位姿成员 | `livingRoom0.gt.freiburg`,1508 行 |
| RGB 样例 | 640×480,8-bit,color_type 2 |
| Depth 样例 | 640×480,**16-bit**,color_type 0 |

**Gate 0 判定: `BLOCKED_TIMESTAMP_AND_EXPOSURE_AUDIT_PENDING`**

两条阻断理由(原文):

1. `timestamp_semantics`: **"frame_index_only; official TUM-compatible archive has no sensor timestamp column"** —— 只有帧序号,没有硬件传感器时间戳。按 30 Hz 反推的帧号**不等于**真实时间戳。
2. `depth_semantics`: 需要官方 ICL-NUIM 换算(标定页规定 z 坐标换算与 **负 `fy`**),尚未执行。

审查脚本自带的隔离声明(必须保留):

> "GT pose text is present for qualification but must remain inaccessible to selector until prediction seal."

### 3.3 作业 586074 — 抽样解码(真实读取像素)

在 `cpu` 分区(intel-01)对 5 帧(id 1, 2, 3, 750, 1508)做真实解码,**不跑模型,不用未来 GT 做选择**:

- RGB:5/5 `OK`,PNG / 640×480 / mode `RGB`
- Depth:5/5 `OK`,PNG / 640×480 / mode **`I;16`**
- **`zero_count = 0`,`nonzero_count = 307200`** —— 5 帧深度**无零值像素**,全部 307200 像素有效
- 深度原始 uint16 范围示例:id 1 → [8215, 17160];id 750 → [4325, 12860]

每帧 RGB/Depth 的 sha256 均记录在 `slurm-586074.out`。

### 3.4 作业 585900 / 585928 / 585971 — VMem 源码导入烟测

`remote_project_import_probe.py` 只做 `importlib.import_module`,**不读数据、不读权重、不跑模型**,三个 job 的 `data_access` / `weight_access` / `model_execution` 全为 `false`。

失败到成功的过程:

| 作业 | 节点 | `modeling` | 失败原因 |
|---|---|---|---|
| 585900 | dgx-05 | FAIL | `No module named 'modeling'`(PYTHONPATH 未含源码根) |
| 585928 | dgx-14 | FAIL | `No module named 'add_ckpt_path'` |
| 585971 | dgx-09 | **IMPORT_OK** | 五个模块全部导入成功 |

585971 同时报告 1024×1024 FP16 matmul 耗时 185.23 ms(torch 2.7.0+cu126)。

**边界**:`IMPORT_OK` **只说明 Python 模块可导入**,不说明 VMem 前向可运行、权重可加载或结果正确。

### 3.5 作业 586684 / 586691 / 586699 — 编译 cuRoPE CUDA 扩展

CUT3R 的 2D RoPE 需要自编译 CUDA 扩展 `curope`。三次尝试:

| # | 作业 | 结果 | 原因 |
|---|---|---|---|
| 1 | 586684 | ❌ | 登录/计算环境未加载 CUDA toolkit,`kernels.o` 与 `-lcudart` 均找不到 |
| 2 | 586691 | ❌ | 换用 `nvhpc` 的 `nvc++`,不认 `-fwrapv`;且 PyTorch 警告编译器不匹配 |
| 3 | **586699** | ✅ | `module load cuda12.2/toolkit/12.2.2` + `CC/CXX/CUDAHOSTCXX=/usr/bin/g++` |

第 3 次产出(`S104_curope_build_586699/`):

```
curope.cpython-311-x86_64-linux-gnu.so   316048 bytes
sha256 1f28c09198b56e26954581a991a7bdbffe5fc15a16fc445401705fa5721ab516
IMPORT_OK <module 'curope' ...> True NVIDIA H800
```

CUDA 12.2 与 PyTorch 编译用的 12.6 有 minor 版本不一致警告,**保留**,未试图消除。

### 3.6 作业 586719 — CUT3R 前向成功(本批次唯一科学产物)

**输入**:ICL-NUIM `living_room_traj0` 的 4 张真实 RGB 帧,id 1/31/61/91,640×480 → 512×384。
**关键隔离**:脚本硬编码 `FORBIDDEN = ("depth", "pose", "gt", "ground_truth", "trajectory")`,任何 RGB 路径含这些子串即抛错;回执明确记录 `depth_access: false`、`pose_access: false`、`gt_access: false`。

两次失败的原因(必须保留,它们是真问题):

1. **586628** — PyTorch ≥ 2.6 将 `torch.load` 的 `weights_only` 默认改为 `True`,CUT3R 官方 checkpoint 内含 OmegaConf 对象 → `UnpicklingError`。
2. **586634** — 通过一次**窄范围**兼容垫片(仅在路径 SHA 已记录后,对该 checkpoint 强制 `weights_only=False`,并写入回执的 `loader_compatibility` 字段)解决后,继续跑到 `pos_embed.py:137` → `RuntimeError: No validated RoPE implementation for this device`。**根因是 cuRoPE 扩展没编译**(见 3.5)。

**最终成功回执**(`artifacts/jobs/S104_cut3r_calibration_586719/RECEIPT.json`):

| 字段 | 值 |
|---|---|
| `status` | `SUCCESS` |
| `device` | NVIDIA H800 |
| `torch` / `cuda` | 2.7.0+cu126 / 12.6 |
| `model_path` | `/home/yliutz/gwm_weights_20260915/cut3r_512_dpt_4_64.pth` |
| `model_bytes` | 3,173,761,006 |
| `model_sha256` | `45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103` |
| `load_seconds` | 7.912522085942328 |
| `inference_seconds_sync` | 10.663249660981819 |
| `peak_memory_bytes` | 3,641,906,688(≈3.39 GiB) |
| `forward_completed` | `true` |
| `rgb_sha256` | 4 条,见回执 |
| `raw_outputs_sha256` | `ff493fdeee5f2a09a6321ce567a73ffd331d1954e2eb97a368bb80b61aa938e2` |

模型身份:CUT3R `ARCroco3DStereo`,`freeze='encoder'`, `state_size=768`, `head_type='dpt'`, `output_mode='pts3d+pose'`,`img_size=(512,512)`,`<All keys matched successfully>`。

**S104 尚未完成的部分**:作业名叫 `calibration`,但脚本只做到**保存原始预测** `raw_outputs.pt`(86,540,736 B)。**标定评分(与 ICL-NUIM GT 深度对照)从未执行。**

---

## 4. 产物与证据

| 路径 | 内容 |
|---|---|
| `MANIFEST.json` | 69 个归档文件,每个含源绝对路径、字节数、sha256、源 mtime;**69/69 sha 与源一致** |
| `EXTERNAL_ASSETS.json` | 7 项未复制的大文件/第三方资产,含路径、字节数、sha256 |
| `artifacts/scripts/` | 10 个当时实际执行的脚本,逐字节副本 |
| `artifacts/jobs/` | 6 个作业输出目录(16 文件),含 3 份 `RECEIPT.json`、3 份 `STARTED.json`、封存的 `raw_outputs.pt` |
| `artifacts/slurm_logs/` | 18 个 sbatch stdout(`slurm-*.out` + `gwm_*.out`) |
| `artifacts/env_bootstrap/` | 17 个环境构建日志与 pip freeze |
| `artifacts/data_receipts/` | 数据下载回执、归档结构审查、抽样解码、导入探针、环境烟测日志 |

**归档完整性核对(本次实际执行)**:

- 69/69 文件 `sha256_matches_source == True`
- 封存预测 `raw_outputs.pt` 的归档 sha256 == 回执内记录的 `ff493fde…` ✅
- CUT3R 权重 sha256 == 回执内 `45f7e98a…` ✅
- 抽查 `RECEIPT.json` 与原件 `diff` 无差异 ✅

**未复制的资产(按项目"记录绝对路径与 SHA,不复制大文件"的规则)**:

| 文件 | 字节 | sha256(前 16) |
|---|---|---|
| `cut3r_512_dpt_4_64.pth` | 3,173,761,006 | `45f7e98a0a64dbeb` |
| `vmem_weights.pth` | 2,666,266,624 | `88440ee859aca3d2` |
| `open_clip_model.safetensors` | 3,944,517,836 | `0084e75319a50ad8` |
| `diffusion_pytorch_model.safetensors` | 334,643,276 | `a1d993488569e928` |
| `living_room_traj0_frei_png.tar.gz` | 711,444,709 | `4eca8c2e9f77c1bd` |
| `vmem_source_only.tar.gz` | 357,741 | `de001a234e97fdf8` |

`vmem/` 解包树共 242 文件(冻结快照 196 文件,差额为 `.so` 与 `__pycache__`)。

---

## 5. 边界：本批次**没有**证明什么

1. **没有新科学结论。** 全部产出是环境、编译与一次单模型前向;`new_method_validated=false`、`novelty_authorization=NONE`、`NO_METHOD_SELECTED` 状态**不变**。
2. **不解开 Gate 0。** ICL-NUIM 仍缺硬件时间戳、深度单位未换算。这 4 帧是**合成场景**,不是未见真实场景。
3. **4 帧不是 4 个独立实验。** id 1/31/61/91 在 30 Hz 下相隔约 1 秒,同一轨迹、同一房间,不构成跨场景或长期证据。
4. **未与任何 GT 对照。** 回执三处显式记录 `depth_access/pose_access/gt_access = false`。本次前向**只是保存了预测**,没有评分。
5. **GPU 身份与模型前向是两件事。** 583967/583968 只接受"分到了 H800";586719 才接受"一次 CUT3R 前向完成"。二者不可互相替代。
6. **独立复算未完成。** 本批次只有执行回执与作者自检,**没有不同作者的数值复算**,按项目规则不能升级为已验收结果。
7. **尚未检查 `raw_outputs.pt` 的实际内容。** 该文件是否可加载、包含哪些键、数值范围如何,**本次未验证**。

---

## 6. 下一步

1. **对 `raw_outputs.pt` 做只读结构检查**(不评分):确认可加载、键、张量形状、是否有 NaN/Inf。
2. **S104 收尾评分**:先查 ICL-NUIM 官方标定页核实深度换算语义(负 `fy`、z 换算)与曝光语义,**不得猜测**;核实后再读 GT 深度评分。评分定位为**组件资格检查**,不是 GRC 证据。
3. **Gate 0 决策(需用户拍板)**:ICL-NUIM 因缺时间戳受阻。或在 TUM RGB-D 中选一个**未见过**的序列(有真硬件时间戳、K、pose、深度,项目已有 `src/tum_rgbd.py` loader),或把 ICL-NUIM 的帧序号语义正式写成已接受局限并补曝光审计。
4. **修正过期记忆**:文档中"M3 Max 64GB、暂无远程 GPU"须更新为本机实际情况(SuperPOD 登录节点,`sbatch` 取 H800)。
