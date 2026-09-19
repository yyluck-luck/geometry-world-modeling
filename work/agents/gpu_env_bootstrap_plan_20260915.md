# SuperPod 隔离依赖环境方案与 dry-run 回执（2026-09-15）

**审查目的：** 为后续真实 VMem/CUT3R 运行准备可复现的个人环境，不污染已有 `torch` 环境。  
**科学边界：** 本轮只解析依赖和环境元数据；没有导入项目代码、没有加载研究模型、没有读取 RGB/depth/pose/GT，也没有提交正式 GRC。

## 1. 本地 requirements 解析

项目当前有三条依赖线：

| 文件 | 关键固定版本 | 作用 |
|---|---|---|
| `requirements-cut3r.txt` | Python 未写死；`torch==2.7.0`、`torchvision==0.22.0`、`numpy==1.26.4`、`scipy==1.16.2`、`transformers==4.48.3`、`accelerate==1.4.0`、OpenCV、Pillow10.3 等 | CUT3R/图像推理准备 |
| `requirements-retrieval.txt` | `torch==2.7.0`、`numpy==2.3.5`、`scipy==1.16.2` | retrieval 几何路径 |
| `requirements-rgbd.txt` | 继承 retrieval；`Pillow==11.3.0`、`matplotlib==3.10.6` | RGB-D/绘图路径 |

存在一个必须显式处理的统一环境冲突：CUT3R 固定 `numpy==1.26.4`，retrieval/RGB-D 固定 `numpy==2.3.5`。不能把两个互斥 pin 写进同一个最终环境并声称可复现。建议维护两个个人环境：

```text
gwm-cut3r-py311  : CUT3R requirements，numpy 1.26.4、Pillow 10.3.0
gwm-rgbd-py311   : retrieval + rgbd requirements，numpy 2.3.5、Pillow 11.3.0、matplotlib 10.6
```

若代码确认两条路径可共用一个 NumPy 版本，必须另建新 requirements 版本并重新做完整测试；不能在安装时静默覆盖 pin。

## 2. SuperPod 已有环境与模块（实际只读）

登录节点通过 Anaconda 模块发现：

```text
Anaconda3/2023.09-0
conda envs: base, geometry, torch
torch env: Python 3.10.21, torch 2.5.1+cu121, torchvision 0.20.1+cu121,
           numpy 2.2.6, Pillow 12.3.0
geometry env: no packages listed
```

可用模块包括：

```text
cuda11.8/toolkit/11.8.0
cuda12.2/toolkit/12.2.2
nvhpc-hpcx-cuda12/23.11
slurm/slurm/23.02.6
```

现有 `torch` 环境不能直接满足 CUT3R：Torch/torchvision 版本不同、NumPy pin 不同，且前一轮 import probe 已确认 `diffusers`、`transformers`、`accelerate`、`cv2`、`imageio`、`scipy` 缺失。不得在该环境上直接 `pip install -U`。

## 3. Python 版本兼容性 dry-run（实际结果）

在当前 Python 3.10.21 环境中执行了无安装 pip dry-run（新 Slurm job 见第 4 节）。实际错误为：

```text
scipy==1.16.2: No matching distribution found
versions 1.16.0–1.16.3 require Python >=3.11
```

这不是科学代码失败，而是当前 Python 3.10 与项目固定 `scipy==1.16.2` 的硬冲突。随后执行：

```text
conda create -n gwm_s101_py311_dryrun python=3.11 --dry-run --json
```

返回码为 0，Anaconda solver 可解析 Python 3.11.16 及基础包；这是 dry-run，不代表环境已创建。

一次跨平台 pip metadata 探针能找到 `torch-2.7.0-cp311` 和 `torchvision-0.22.0-cp311`，但由于人为指定 `manylinux_2_28` 平台，`numpy==1.26.4` 被错误排除。这个结果不能当作 NumPy 不可用；应在真实 Linux/Python 3.11 环境中用本机平台标签重新解析。

## 4. 真实 Slurm dry-run job

为确认计算节点网络/解释器对固定 SciPy 的行为，本轮在已核验的 `normal` 分区申请了 1 GPU、2 分钟上限、2 GiB 内存、1 CPU，并只执行 `pip install --dry-run --no-deps scipy==1.16.2`：

```text
job=584188
node=dgx-09
partition=normal
account=mscitspod2026
NumTasks=1, NumCPUs=2, gres/gpu=1
runtime=00:00:03 (time limit 00:02:00)
exit=1:0
```

真实返回与登录节点一致：Python 3.10 不满足 SciPy 1.16.2 的 Python>=3.11 约束。该 job 没有安装任何包，没有导入项目模块，没有访问数据或 GT。失败目录和输出保留。

## 5. 推荐的隔离安装方案（命令草案，不代表已执行）

### 5.1 CUT3R 环境

```bash
. /etc/profile.d/modules.sh
module load Anaconda3/2023.09-0
conda create -n gwm-cut3r-py311 python=3.11 pip -y
conda run -n gwm-cut3r-py311 python -m pip install \
  torch==2.7.0 torchvision==0.22.0
conda run -n gwm-cut3r-py311 python -m pip install \
  numpy==1.26.4 scipy==1.16.2 pillow==10.3.0 \
  transformers==4.48.3 accelerate==1.4.0 einops==0.8.1 \
  roma==1.5.1 opencv-python-headless==4.11.0.86 \
  tqdm==4.67.1 omegaconf==2.3.0
```

Torch CUDA wheel 的实际索引（PyPI 默认、cu126 或学校镜像）必须先以 native Python 3.11 dry-run 确认；安装后必须记录 `torch.version.cuda`、driver、GPU 型号和每个 wheel SHA。不能根据当前 `+cu121` 环境直接假定 Torch 2.7 的 CUDA 构建。

### 5.2 RGB-D/retrieval 环境

```bash
. /etc/profile.d/modules.sh
module load Anaconda3/2023.09-0
conda create -n gwm-rgbd-py311 python=3.11 pip -y
conda run -n gwm-rgbd-py311 python -m pip install \
  torch==2.7.0 torchvision==0.22.0 \
  numpy==2.3.5 scipy==1.16.2 \
  Pillow==11.3.0 matplotlib==3.10.6
```

这是安装草案。正式执行前需要把完整命令、索引、lockfile 和资源预算写入新版本冻结文件；如果下载 Torch CUDA wheel 超过学校配额，保留失败并改用服务器已有、SHA 已核验的镜像。

## 6. 当前可直接运行 / 需补齐 / 未知

| 项目 | 状态 | 证据 |
|---|---|---|
| Python 3.11 基础环境 | **可准备** | conda Python 3.11.16 dry-run 返回 0；尚未创建 |
| Python 3.10 + SciPy 1.16.2 | **不可行** | job 584188 的实际 pip resolver 明确拒绝 |
| 现有 `torch` env | **不可直接运行 CUT3R** | torch2.5.1/vision0.20.1、NumPy2.2.6、关键包缺失 |
| CUT3R 完整依赖安装 | **需安装** | 新隔离环境和 native Python 3.11 resolver 尚未执行 |
| RGB-D/retrieval 完整依赖 | **需安装/分环境** | NumPy/Pillow pin 与 CUT3R 不同 |
| Torch 2.7 CUDA 索引与 wheel SHA | **未知** | cp311 metadata 可见，但 CUDA variant/完整依赖未在 native env 核验 |
| VMem 模型及权重 | **未知/未允许运行** | 本轮没有加载模型或权重 |
| 合法 held-out 数据 | **未通过 Gate0** | 现有 TUM 仍是 DEVELOPMENT_SEEN；ICL-NUIM 仅 acquisition freeze |

## 7. 风险与后续门

1. **环境污染风险：** 不要改动现有 `torch` 或 `geometry`；每个新环境使用独立名称和新目录。
2. **版本冲突风险：** 不要把 NumPy 1.26.4/2.3.5 合并为一个未经测试的环境；不要用安装顺序掩盖 pin 冲突。
3. **CUDA wheel 风险：** Torch 2.7 的 CUDA variant 和 H800 driver 兼容性必须以实际 `torch.cuda.is_available()`、`torch.version.cuda`、2×2 matmul 和 wheel SHA 验证。
4. **资源风险：** Torch CUDA wheel 可能很大；先记录 dry-run/磁盘配额，避免在长作业中临时下载。
5. **代码依赖风险：** import 全部通过也不等于 VMem forward；之后仍须做不读 GT 的真实模型 smoke test。
6. **科研数据门：** 依赖补齐后仍不能运行正式 GRC。必须先对新合法 held-out RGB-D/K/pose/timestamp 运行完整 S102 Gate0，并在 prediction seal 后才可读取未来 GT。

## 8. 结论

**`ENV_BOOTSTRAP_BLOCKED_PENDING_ISOLATED_PY311_PLAN`**：SuperPod 的 CUDA/PyTorch 基础层已验证，但项目固定 SciPy 版本排除了当前 Python 3.10；Python 3.11 conda 基础环境 dry-run 可解析。建议建立两个隔离 Python 3.11 环境分别服务 CUT3R 与 RGB-D/retrieval，先做 native resolver dry-run，再安装并锁定版本。目前没有安装新包、没有污染默认环境、没有运行 VMem/GRC、没有读取 GT。

## 9. 后续只读复核（2026-09-15，补充而非改写历史）

随后对共享 Anaconda base 环境做了独立、只读的 import probe。该环境路径为
`/cm/shared/apps/Anaconda3/2023.09-0`，Python 3.11.5；登录节点上报告为：

```text
torch|IMPORT_OK|2.7.0+cu126
torch.version.cuda|12.6
torch.cuda.available|False    # 这是登录节点，不是 GPU 计算节点
torchvision|IMPORT_OK|0.22.0+cu126
numpy|IMPORT_OK|1.24.3
scipy|IMPORT_OK|1.11.1
PIL|IMPORT_OK|9.4.0
transformers|IMPORT_OK|4.48.3
accelerate|IMPORT_OK|1.4.0
cv2|IMPORT_OK|4.11.0
imageio|IMPORT_OK|2.31.1
diffusers|IMPORT_FAILED|ModuleNotFoundError
```

这解释了最新账本中“base 可做进一步准备”的判断，但它仍不能直接作为正式冻结环境：NumPy/SciPy/Pillow 与 `requirements-cut3r` 的精确 pin 不同，`diffusers` 缺失，且登录节点 CUDA=False 不能代替计算节点 GPU smoke。此前关于个人 `torch` 环境（Python 3.10.21、torch 2.5.1+cu121、六个包缺失）的记录仍然有效；两套环境不可混写。下一步应在个人命名的 Python 3.11 环境完成 native resolver、锁定文件和计算节点 import/GPU smoke，再决定是否允许项目级模型加载。

## 10. 共享 base 的计算节点 smoke（job 584274）

为排除登录节点与 GPU 节点差异，提交了一个 1-GPU、2-CPU、8 GiB、5 分钟的只读 smoke job（`normal`、`mscitspod2026`）。作业在 `dgx-09` 于 13 秒完成，退出码 0；没有读取项目数据、GT、权重或运行 VMem/GRC。关键输出：

```text
torch 2.7.0+cu126; torch.version.cuda=12.6
CUDA_AVAILABLE=True; CUDA_COUNT=1; NVIDIA H800
2x2 matmul=[[7.0,10.0],[15.0,22.0]]
torchvision 0.22.0+cu126; transformers 4.48.3; accelerate 1.4.0
cv2 4.11.0; imageio 2.31.1; numpy 1.24.3; scipy 1.11.1; PIL 9.4.0
diffusers IMPORT_FAILED (ModuleNotFoundError)
```

因此共享 base 的 CUDA/PyTorch 和大部分 CUT3R 周边依赖在 GPU 节点上可运行，但仍只能标记为 **PREPARATION_SMOKE_PASS**：缺少 `diffusers`，且 NumPy/SciPy/Pillow 未满足项目锁定版本。该结果不授权直接运行 VMem 或正式 GRC；应先决定采用个人隔离环境还是经过审批、可复现地补齐 base 的依赖，并重新记录版本与哈希。
