# S15A 独立复核程序接口

程序 `scripts/verify_s15a_history.py` 由不同于 runner 作者的 agent 实现，不导入 runner、Torch、CUT3R、PIL；真实执行时只做文件字节哈希，并解码本次三份输出 NPZ。20 张 RGB 和约 3GB 权重会被流式哈希，但不解码照片或反序列化权重；没有模型前向、trajectory/depth/target读取或准确率计算。程序采用 NumPy 2/SciPy 环境 `.venv/bin/python`。

## 封存与运行

父任务在真实运行和 caller 已完成之后建立 combined seal：

```json
{
  "schema": "s15a-history-combined-seal-v1",
  "sealed_utc": "实际UTC时间",
  "manifest": "/absolute/docs/S15A_HISTORY_EXECUTION_MANIFEST.json",
  "run_dir": "/absolute/results/S15A_bonn_history",
  "caller_receipt": "/absolute/work/S15A_execution/model/caller_receipt.json",
  "verifier": "/absolute/scripts/verify_s15a_history.py",
  "identities": {"绝对规范文件路径": "SHA256"}
}
```

identities 必须恰为以下并集：manifest.identities；manifest 本身；run_dir 中七份输出（run_metadata.json、predictions.npz、state.npz、history_poses.npz、frozen_manifest.json、source_snapshot.py、checkpoint_load.txt）；caller_receipt；verifier。重复角色共享一个键。caller/其他控制源码如已在 manifest.control_files，自然包含在并集中，无需再次附加未授权文件。seal本身由命令行 SHA 固定：

```text
.venv/bin/python scripts/verify_s15a_history.py \
  --seal /absolute/combined_seal.json \
  --seal-sha256 事前封存的SHA256 \
  --output /absolute/全新验证目录
```

程序拒绝已有输出目录，失败写 `verification.json` 并保留所有判定及 traceback。当前阶段只做代码和人工数据准备；实际运行必须由根给出完成后的 seal。不能用运行前的计划替代实际封存结果。

## 独立检查范围

先核外部seal SHA、所有文件身份、精确输入/输出集合，之后才打开输出数组。逐一检查120官方预测、5字段状态、2份姿态数组的键、形状、dtype、有限性、连续字节SHA及metadata对应；NPZ解压成员的声明长度受预定数组规模约束。模型自视角z只描述正值数/极值，单位标为未对齐模型单位，不能称米或效果。

姿态编码前三位平移与输出矩阵平移进行字节比较；每帧 `camera_pose` 与汇总编码字节相同。用 SciPy `Rotation.from_quat(q[:,[1,2,3,0]])` 独立处理官方 wxyz 排列，SciPy归一化四元数；与官方Torch多项式不是同一实现。旋转矩阵比较固定 `atol=1e-6, rtol=1e-5`，另核预定 SO(3) 完成门槛与齐次底行。原始640×480不硬猜，只核metadata每帧尺寸/模式完整并如实输出。

检查计数包括：20次历史图片打开/解码、一次历史forward、一次包含20帧的image encoder、一次内部未选择的dummy ray encoder、0目标查询/目标RGB/目标depth；核两次完整输入身份记录、导入源码冻结、实际caller命令和时间顺序。此处是对封存运行记录与数值的团队内独立复核，不是操作系统级监控所有syscall的证明，也不是外部团队复现。

runner和caller均须成功，caller固定600秒、32GiB RSS且实际monitor成功。verifier自身另有600秒alarm、每检查点32GiB进程RSS门槛、流式哈希和有界已知数组；自身资源门槛不冒称另一个外部监控进程。

## 人工准备结果

`work/S15A_verifier_preparation/artificial_checks.py` 构造全套假的文件/元数据/127数组，完成一次全流程并进行10项失败边界检查（平移、四元数排布、底行、旋转、非有限、dtype、shape、byteSHA、seal后篡改等）。伪造权重仅普通短字节；测试中临时把模块内期望权重digest换成假字节digest后恢复，生产源码没有修改或绕过真实固定权重门槛。假输入PNG后缀文件不是有效图片，程序没有图像解码器。

完整人工成功链997项判定；11个准备检查组都通过，实际 UTC 2026-09-06 09:51:24.356004—09:51:24.562586。人工姿态期待值由轴角 Rodrigues 构建，复核器使用SciPy；最大旋转差约4.10e−8。人工资料放fake_case等目录，绝不统计为实拍、真实模型或新来源准确率。真实执行的判定项数随实际控制文件数而变，不应强行要求997。
