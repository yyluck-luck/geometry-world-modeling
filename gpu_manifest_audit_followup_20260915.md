# SuperPod Slurm 环境只读核查回执（S101 follow-up）

**核查日期：** 2026-09-15（Asia/Shanghai）  
**核查身份：** 远端环境只读探针；未提交作业、未读取项目数据或 GT、未上传文件  
**目标别名：** `superpod.ust.hk`（本机已有 SSH alias；不在本文件记录用户名、端口、密钥路径或指纹）

## 1. 实际执行的只读命令

本轮使用 BatchMode 和无密码/无交互认证，避免弹出密码提示或写入凭据：

```sh
ssh -o BatchMode=yes -o ConnectTimeout=12 \
  -o PreferredAuthentications=publickey \
  -o PasswordAuthentication=no \
  -o KbdInteractiveAuthentication=no \
  -o StrictHostKeyChecking=ask \
  superpod.ust.hk \
  'hostname; command -v sinfo; command -v sbatch; \
   nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader'
```

命令只会读取远端主机名、Slurm 可执行文件位置和 GPU 驱动摘要，不访问 `data_root`、项目文件、RGB、depth、pose 或 GT。此前还准备了 `sinfo`、`sacctmgr`、`squeue` 的只读查询，但由于 SSH 认证在远端命令执行前失败，未实际执行这些查询。

## 2. 真实结果

```text
RETURN_CODE=255
STDOUT: (empty)
STDERR: Permission denied (publickey,password,keyboard-interactive).
```

本机有效 SSH 配置的非敏感结论：

```text
forwardagent no
stricthostkeychecking ask
host alias resolved: superpod.ust.hk
known_hosts records for alias: present (fingerprints intentionally omitted)
```

这证明本机能够将 alias 解析到 SSH 连接阶段，且没有使用 `StrictHostKeyChecking=no` 或 agent forwarding；**不能证明账号认证成功、Slurm 可用、account/partition/GPU 参数可用，也不能证明学校服务器已授权本项目。**

本机 `ssh-add -l` 的只读检查返回 `The agent has no identities.`；该状态解释了为什么公钥认证未完成，但不应据此猜测应使用哪一个私钥或把私钥上传到项目。

## 3. 当前状态判定

| 项目 | 状态 | 证据/限制 |
|---|---|---|
| SSH 网络/主机阶段 | `REACHABLE_TO_AUTH_STAGE` | 远端返回认证错误，而非 DNS/连接超时；主机 key 记录存在，具体指纹不写入项目 |
| SSH 用户认证 | `BLOCKED_AUTHENTICATION` | BatchMode 公钥认证返回 255；没有可用 agent identity；未尝试密码或交互登录 |
| Slurm account | `UNKNOWN` | 未能执行 `sacctmgr`；不猜测 account 名称 |
| Slurm partition/QoS | `UNKNOWN` | 未能执行 `sinfo`/`scontrol`；不猜测 partition 或 QoS |
| GPU 型号/显存/驱动 | `UNKNOWN` | `nvidia-smi` 未运行；不把本机 M3 Max 或其他历史环境当作远端 GPU |
| 作业提交 | `NOT_SUBMITTED` | 没有执行 `sbatch`/`salloc`/`srun`，没有产生 job ID |
| GT/数据读取 | `ZERO` | 远端命令在认证前失败；本轮未访问数据路径和任何 GT 正文 |

## 4. 最小 smoke-test 命令（仅在认证恢复后使用）

下面只是**待认证后、确认 account/partition 后**的最小只读环境探针模板，不是当前可直接执行的提交命令。占位符必须由学校服务器实际查询结果替换；不允许凭猜测填写：

```sh
srun --account=<VERIFIED_ACCOUNT> --partition=<VERIFIED_GPU_PARTITION> \
     --gres=gpu:1 --time=00:05:00 --mem=8G --cpus-per-task=2 \
     --job-name=geometry-env-smoke --pty bash -lc '
  set -eu
  hostname
  date -u
  command -v python
  python -c "import sys; print(sys.version)"
  command -v nvidia-smi
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
  python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"NO_CUDA\")"
'
```

该探针应绑定一个独立的 development/synthetic fixture，不能指向 held-out RGB、depth、pose、future query 或 GT。执行时必须保存 `ENV_RECEIPT.json`、scheduler job ID、stdout/stderr、退出码和实际资源信息；若学校不允许交互式 `srun`，应先使用同等约束的短时 `sbatch`，但仍不得运行长作业。

推荐在取得认证后先执行的只读查询（不提交作业）：

```sh
sinfo --noheader --format='%P|%G|%c|%m|%l|%a'
sacctmgr -nP show assoc where user="$USER" format=Account,Partition,Cluster,DefaultQOS,QOS
squeue -h -u "$USER" -o='%i|%P|%T|%M|%j'
```

输出需脱敏保存，不把用户名、密钥、cookie 或 token 写入科研日志。只有 account、partition、GPU 资源和调度规则被实际核验后，才可填入 S101 manifest。

## 5. 安全与科研边界

1. 本轮未使用密码、没有关闭 host key 检查、没有启用 agent forwarding、没有读取或上传项目数据。
2. 不应通过复制私钥、把 OpenRouter/DSH 凭据写入远端环境、或使用 `StrictHostKeyChecking=no` 来“修复”认证失败。
3. 认证失败是外部访问依赖，不能写成模型或数据科学失败；保留本回执后，等学校提供/确认合法的登录方式。
4. 认证恢复后仍必须先做 account/partition/GPU 的只读核查，再做不读 GT 的环境 smoke test，最后重新执行 S102 Gate0。当前 TUM development 数据不能升级成 held-out。
5. 远端环境探针成功只表示运行环境可用；没有合法 held-out RGB-D/K/pose/timestamp 和 prediction seal，不能开始正式 GRC 或宣称 proposal 几何结果已验证。

## 6. 分歧纠正：显式 identity 后的成功只读核查

随后发现前一次 `Permission denied` 使用的是 SSH alias 默认 identity；root 的实际成功命令显式指定了项目专用 identity。为解决分歧，本轮用同一显式 identity 重跑，并在远端先加载 `/etc/profile.d/modules.sh`，再加载 `slurm` 模块。此前一次 source 失败的原因是远端命令先开启 `set -u`，而 `/etc/sysconfig/modules/init.sh` 读取了未定义的 `ENABLE_LMOD`；修正为先 source、后开启 `set -u`。

### 6.1 登录节点只读输出（实际）

实际命令为：

```sh
ssh -i "$HOME/.ssh/id_ed25519_superpod" -o IdentitiesOnly=yes \
  -o BatchMode=yes -o StrictHostKeyChecking=ask \
  yliutz@superpod.ust.hk \
  'set -e; . /etc/profile.d/modules.sh; module -t avail; \
   module load slurm; scontrol --version; \
   sinfo --noheader --format="%P|%G|%c|%m|%l|%a"; \
   sacctmgr -nP show assoc where user="$USER" \
     format=Account,Partition,Cluster,DefaultQOS,QOS'
```

敏感的用户名、端口、identity 路径和 host key 指纹不写入回执正文。远端实际关键输出为：

```text
HOST=slogin-02
SLURM=23.02.6
SINFO
cpu|(null)|224|515303+|12:00:00|up
normal|gpu:8(S:0-1)|224|1996800|infinite|up
ASSOC
mscitspod2026|normal|slurm|msccsit2026_normal_qos|msccsit2026_normal_qos
mscitspod2026|cpu|slurm|cpu_qos|cpu_qos
MODULES
cuda12.2/toolkit/12.2.2
Anaconda3/2023.09-0
nvhpc-hpcx-cuda12/23.11
```

登录节点没有 GPU；`nvidia-smi` 和 CUDA/PyTorch 必须在 Slurm GPU allocation 中执行。

### 6.2 正确 CUDA/PyTorch 最小 smoke test（实际 job）

没有使用 heredoc 或易混淆的 shell 引号；直接调用已核验的 torch 环境 Python，且只执行 2×2 CUDA 矩阵乘法：

```sh
ssh -i "$HOME/.ssh/id_ed25519_superpod" -o IdentitiesOnly=yes \
  -o BatchMode=yes -o StrictHostKeyChecking=ask \
  yliutz@superpod.ust.hk \
  'set -e; . /etc/profile.d/modules.sh; module load slurm; \
   srun --account=mscitspod2026 --partition=normal --nodes=1 \
     --gpus=1 --time=00:05:00 --mem=8G --cpus-per-task=2 \
     --job-name=gwm_s101_cuda_smoke \
     /home/yliutz/.conda/envs/torch/bin/python -c "..."'
```

实际 Slurm 回执：

```text
job=584006
partition=normal
account=mscitspod2026
node=dgx-21
alloc=cpu=2,node=1,billing=2,gres/gpu=1
exit=0:0
runtime=00:00:07 (time limit 00:05:00)
PYTHON=3.10.21
TORCH=2.5.1+cu121
CUDA_AVAILABLE=True
CUDA_COUNT=1
GPU=NVIDIA H800
CAPABILITY=(9, 0)
MATMUL=[[2.0, 2.0], [2.0, 2.0]]
ALLOCATED_BYTES=33555456
PEAK_BYTES=33555456
```

这次 job 是**真实 CUDA/PyTorch 环境 smoke test**，证明 H800 上 torch CUDA 基础调用可用；它没有导入 VMem、读取 RGB/depth/pose/GT、加载研究模型、生成视频或提交正式 GRC。它也不证明 VMem forward 已成功。

## 7. 更新后的状态判定

| 项目 | 更新状态 | 证据/限制 |
|---|---|---|
| SSH 认证 | `PASS_EXPLICIT_IDENTITY` | 显式 identity 登录成功；前次 alias 默认 identity 失败保留为历史分歧 |
| Slurm | `VERIFIED_READONLY` | Slurm 23.02.6；account `mscitspod2026`；GPU partition `normal`；`gpu:8(S:0-1)` |
| GPU | `VERIFIED` | job 584006 在 `dgx-21` 取得 1×NVIDIA H800；显存/compute capability 已由 PyTorch 实测 |
| CUDA/PyTorch | `SMOKE_PASS` | torch 2.5.1+cu121，CUDA 可用，2×2 CUDA matmul 正确；非 VMem forward |
| 正式 GRC | `NOT_ALLOWED` | Gate0 尚未通过；不读取 held-out 答案，不提交正式 GRC |
| GT/数据 | `ZERO` | smoke 命令未访问数据根目录和任何 GT 正文 |

## 8. 仍需遵守的边界

1. 这是对“root 成功 / 本 agent 前次失败”分歧的纠正记录，不删除前次失败回执；差异来自显式 identity 与模块加载顺序。
2. 只有环境 smoke test 通过，不能把 VMem forward 或研究结果写成已验证；下一步仍需合法 held-out 数据的完整 S102 Gate0。
3. S102 的 ICL-NUIM 候选目前只是 acquisition freeze；下载、解包、逐帧 manifest、许可证和 RGB-D/K/pose/time 语义检查仍未通过前，不得把它作为正式 held-out 结果。
4. 不把 account/partition/GPU 参数用于提交长作业；任何正式实验仍需新版本冻结、GT 隔离、预测封存和独立复核。

## 9. 本轮结论

**`SUPERPOD_CUDA_PYTORCH_SMOKE_PASS_FORMAL_GRC_BLOCKED`**：显式 identity + 显式模块加载后，SuperPod Slurm、account、GPU partition 及 H800 CUDA/PyTorch 2×2 smoke test 已真实核验。前次 `Permission denied` 和 source `ENABLE_LMOD` 错误已保留并解释。没有提交正式 GRC，没有读取 GT。下一步是先获得/验证合法 held-out 数据，执行完整 S102 Gate0，再考虑 S103 真实 VMem forward。

科学状态保持：`new_method_validated=false`；`novelty_authorization=NONE`。
