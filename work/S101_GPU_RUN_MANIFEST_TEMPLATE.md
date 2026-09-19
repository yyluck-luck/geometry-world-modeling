# S101 学校 GPU 迁移运行清单模板

状态：`TEMPLATE_ONLY_NOT_SUBMITTED`（2026-09-15）。这是远端运行前的记录模板，不代表已经连接学校服务器。

## 用户提供的 SSH 入口（仅记录命令，不记录私钥内容）

用户于 2026-09-15 提供了学校服务器登录命令：

```bash
ssh -i ~/.ssh/id_ed25519_superpod yliutz@superpod.ust.hk
```

其中私钥文件只保留在本机 `~/.ssh/`，禁止复制到项目、日志、共享目录或远端实验目录。首次连接仍需记录主机指纹、远端调度器、GPU 型号、CUDA/驱动版本和项目路径；在这些信息完成只读核验前，不把 SSH 命令本身当作服务器可达或 H800 已确认的证据。

## 必须先填的远端信息

```text
host: superpod.ust.hk  # 用户提供；只读连通性和环境仍待核验
user: yliutz          # 用户提供；权限范围仍待核验
port: UNKNOWN
scheduler: UNKNOWN  # slurm/pbs/interactive/other
gpu_model: UNKNOWN
cuda_driver: UNKNOWN
remote_project: UNKNOWN
data_root: UNKNOWN
identity_file: ~/.ssh/id_ed25519_superpod  # 路径记录；不复制密钥内容
host_key_fingerprint: UNKNOWN
```

主机和账号已由用户提供，但调度器、数据许可、主机指纹、远端路径和 GPU 型号仍未确认；不在记录中猜测值。可先执行只读 smoke test，禁止在资格门通过前提交正式 GRC 作业。

## 上传冻结对象

- Git/source commit：待填
- `work/agents/gpu_experiment_contract_20260915.md`
- `work/agents/proposal_alignment_20260915.md`
- `work/agents/innovation_priority_20260915.md`
- `RESEARCH_PRINCIPLES.md`、`RESEARCH_MEMORY.md`、`RESEARCH_LOG.md`
- 数据 manifest 与 RGB-D/K/pose/timestamp SHA：待填
- 权重身份与 SHA：待填
- 运行协议版本：待填

禁止上传 OpenRouter key、DSH state、SSH 私钥或无关个人文件。

## 远端执行顺序

1. 环境 smoke test（单样本、无 GT 读取，保存 `ENV_RECEIPT.json`）。
2. 未见场景 RGB-D/相机配对资格审计（S102）；失败即停止。
3. 跨场景 VMem 长时程几何基线复现（S103）；确认真实神经 forward。
4. 固定记忆槽位选择对照（S104，k=2/4/8）。
5. GRC-Memory 风险校准选择实验（S105，仅使用历史可见输入）。
6. 遮挡后重访压力测试（S106）。
7. 源级反事实记忆干预（S107，先确认 replay 噪声可控）。
8. 尾部/几何定位分析（S108）与多 seed/资源审计（S109）。

## 每个 job 必须产生

`PROTOCOL.md`、`FREEZE.json`、`ENV_RECEIPT.json`、`RUN.json`、selector 选择记录、prediction seal、GT 后评分、完整分母/missing 统计、失败日志、GPU 显存和 wall time、独立复核回执、SHA 清单。

## 不能跳过的停止条件

未来答案提前泄漏、held-out 资格失败、预算或候选池不一致、GRC 不超过 confidence/coverage、收益随场景或指标反转、replay 噪声盖过干预效应、或只有模型加载没有真实 forward 时，停止方法主张并保留全部结果。

当前科学状态：`new_method_validated=false`，`novelty_authorization=NONE`。
