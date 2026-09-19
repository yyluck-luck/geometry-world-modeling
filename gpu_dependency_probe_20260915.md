# SuperPod 依赖只读审计（S101，2026-09-15）

**目的：** 在正式 VMem/GRC 运行前，确认已配置的 `torch` 环境中常用依赖是否可以导入。  
**范围：** 只读 Python import/version 探针；不运行 VMem、不打开项目数据、不读取 RGB、depth、pose 或 GT。  
**资源：** Slurm `normal`、`account=mscitspod2026`、1 GPU、5 分钟上限、8 GiB 内存、2 CPU。

## 1. 执行与纠错记录

第一次探针 job `584095` 因临时 Python `-c` 字符串括号错误失败，未执行任何依赖 import；失败输出和 job 目录不覆盖。修正后以新的 job 执行，不把失败当作依赖缺失：

```text
job=584095
node=dgx-09
failure=SyntaxError: closing parenthesis ']' does not match opening parenthesis '('
```

第二次使用 base64 传递只读 Python 代码，避免 shell 引号/换行问题：

```text
job=584098
node=dgx-09
partition=normal
account=mscitspod2026
alloc=cpu=2,node=1,billing=2,gres/gpu=1
exit=0:0
runtime=00:00:04 (time limit 00:05:00)
```

实际探针逻辑对每个模块调用 `importlib.import_module`，再读取模块或 distribution version；异常单独记录，不会因为一个包缺失而提前退出。

## 2. 实际版本与导入状态

```text
HOST=dgx-09
PYTHON=3.10.21
torch=IMPORT_OK version=2.5.1+cu121
diffusers=IMPORT_FAILED ModuleNotFoundError: No module named 'diffusers'
transformers=IMPORT_FAILED ModuleNotFoundError: No module named 'transformers'
accelerate=IMPORT_FAILED ModuleNotFoundError: No module named 'accelerate'
cv2=IMPORT_FAILED ModuleNotFoundError: No module named 'cv2'
imageio=IMPORT_FAILED ModuleNotFoundError: No module named 'imageio'
numpy=IMPORT_OK version=2.2.6
scipy=IMPORT_FAILED ModuleNotFoundError: No module named 'scipy'
```

`torch`、`numpy` 可以直接导入；`diffusers`、`transformers`、`accelerate`、OpenCV 的 `cv2`、`imageio`、`scipy` 在该环境中缺失。此次探针没有执行 `torch.cuda` 运算，CUDA 基础可用性已由独立 job 584006 验证；本回执不把依赖导入结果当作 VMem forward 成功。

## 3. 可运行性分级

| 依赖 | 状态 | 含义 |
|---|---|---|
| `torch` 2.5.1+cu121 | **可直接运行** | 可导入；同一环境的 CUDA/H800 基础 smoke test 已独立通过 |
| `numpy` 2.2.6 | **可直接运行** | 可导入；版本已记录 |
| `diffusers` | **需安装/环境补齐** | import 失败；不能声称扩散生成链可运行 |
| `transformers` | **需安装/环境补齐** | import 失败；不能声称文本/视觉编码器链可运行 |
| `accelerate` | **需安装/环境补齐** | import 失败；不能声称 accelerator 分布式/设备管理可运行 |
| `opencv-python` (`cv2`) | **需安装/环境补齐** | import 失败；不能直接运行依赖 OpenCV 的图像预处理 |
| `imageio` | **需安装/环境补齐** | import 失败；不能直接运行视频/图像 I/O |
| `scipy` | **需安装/环境补齐** | import 失败；不能直接运行依赖 SciPy 的几何/数值路径 |

## 4. 对 S101/S103 的影响

1. SuperPod 的 GPU、Slurm、PyTorch 和 NumPy 基础层已通过低成本探针；这只说明计算节点环境和基础张量库可用。
2. 当前 `torch` 环境不能直接运行依赖上述缺失包的 VMem/扩散/图像 I/O 代码。禁止在正式实验中临时 `pip install` 后不记录版本、来源和 lockfile。
3. 下一次环境准备应在独立新目录中补齐依赖，并记录每个 wheel/conda 包的版本、来源、SHA、Python/CUDA/PyTorch 兼容性；安装后重跑本依赖探针和不读 GT 的 import smoke test。
4. 若研究代码实际使用项目内已有 vendored 包或另一 conda 环境，必须以真实 `import` 路径和 `sys.path` 为准，不能用包名“理论上已安装”替代测试。
5. 依赖补齐成功后仍不能进入正式 GRC：必须先获得合法 held-out RGB-D/K/pose/timestamp 并通过完整 S102 Gate0；当前 TUM development 数据保持阻断。

## 5. 安全与科学边界

- 运行命令未访问 `data_root`、模型权重、RGB、depth、pose、future query 或 GT；没有上传文件或提交正式 GRC。
- 仅记录 job ID、节点、资源和包状态，不记录 SSH 私钥、OpenRouter key、cookie 或其他凭据。
- job `584095` 的语法失败和 job `584098` 的成功均保留；依赖缺失是环境事实，不归因于科研方法失败。
- `new_method_validated=false`；`novelty_authorization=NONE`。

## 6. 结论

**`DEPENDENCY_PROBE_PARTIAL_PASS`**：基础层 `torch 2.5.1+cu121` 和 `numpy 2.2.6` 可导入；六个潜在运行依赖（`diffusers`、`transformers`、`accelerate`、`cv2`、`imageio`、`scipy`）缺失。当前只能说 H800/PyTorch 基础环境可用，不能直接开始 VMem/GRC。下一步是隔离补齐依赖并重新做无 GT 环境验证，随后仍受 S102 held-out Gate0 约束。
