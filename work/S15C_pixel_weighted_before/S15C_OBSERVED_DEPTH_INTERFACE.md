# S15C 校准与评分程序接口

本文件对应 `scripts/s15c_observed_depth.py`。科研合同由根任务写入 `docs/S15C_OBSERVED_DEPTH_PROTOCOL.md`；此处只定义实现和输出。当前完成代码及人工数据测试，未执行真实 S15C 评分。

## 命令

```text
.venv-cut3r/bin/python scripts/s15c_observed_depth.py calibrate \
  --manifest ABSOLUTE_MANIFEST_JSON --manifest-sha256 FROZEN_SHA256 \
  --output NEW_CALIBRATION_DIRECTORY

.venv-cut3r/bin/python scripts/s15c_observed_depth.py score \
  --manifest ABSOLUTE_SAME_MANIFEST_JSON --manifest-sha256 SAME_FROZEN_SHA256 \
  --prediction-seal ABSOLUTE_SEAL_JSON --prediction-seal-sha256 EXTERNAL_SEAL_SHA256 \
  --output NEW_SCORE_DIRECTORY
```

两个输出目录必须不存在。失败保留 `run_metadata.json`、已完成产物和逐项输入追踪；不得重用失败目录。成功退出 0，执行中失败退出 1。CPU 模式，BLAS/OpenMP 线程环境固定为 8；无 Torch、模型推理、训练或 RGB loader。内部信号限制 600 秒，0.1 秒监测进程 RSS 高水位≤8 GiB，并记录峰值与实际时间；这不是性能基准。根任务也可加外部独立监控。

## 同一个预先冻结的 manifest

```json
{
  "schema": "s15c-observed-depth-manifest-v1",
  "frozen_utc": "带时区的实际封存时间",
  "runner": "本程序绝对规范路径",
  "python": "实际解释器绝对路径，可为venv符号链接",
  "history_seal": "原S15A_HISTORY_COMBINED_SEAL.json绝对规范路径",
  "history_seal_sha256": "固定原S15A seal的64位小写SHA256",
  "history_predictions": "原S15A结果目录/predictions.npz",
  "history_metadata": "原S15A结果目录/run_metadata.json",
  "controls": ["原理、协议、来源和本阶段准备回执等md/py/json绝对规范路径"],
  "identities": {"允许输入的绝对规范路径": "64位小写SHA256"},
  "samples": [{
    "index": 0,
    "rgb_path": "与原模型history_images精确一致的绝对路径",
    "rgb_sha256": "与原S15A精确相同的SHA256",
    "rgb_timestamp": 1000.0,
    "depth_path": "当前真实depth PNG绝对规范路径",
    "depth_sha256": "获取并核验后冻结的SHA256",
    "depth_timestamp": 1000.001
  }],
  "contract": {
    "device": "cpu", "wall_seconds": 600, "max_rss_bytes": 8589934592,
    "resize": [299,224], "crop": [37,0,261,224], "depth_divisor": 5000,
    "calibration_indices": [0,1,2,3],
    "evaluation_indices": [4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19]
  }
}
```

上例 samples 只示范一行格式；实际必须完整 20 行，index 从 0 到 19，RGB/depth 两边各 20 个不同 PNG。时间戳是有限数字，分别严格递增，每对绝对差≤0.025 秒。不能用新的易例替换原 S15A RGB。`identities` 恰好是 `runner ∪ controls ∪ history_seal ∪ 20 depth PNG`；不要加入 manifest 自身形成哈希循环。历史 RGB/预测等由原 S15A seal 绑定，不再塞进当前 identities。

calibrate 验证原 S15A seal 全部身份，其中流式 SHA 会读取旧 RGB 和权重字节，但不会解码 RGB。随后核当前控制/首 4 depth 身份。后 16 depth 的路径/SHA 是已知控制信息，但 calibrate 不 hash、不打开、不解码这些文件。源 S15A 元数据与原 manifest、20 RGB 顺序、预测 SHA、完成/封存时间都必须相互一致。

原 predictions.npz 把 XYZ 储存在同一个 `frame{i}_pts3d_in_self_view` 数组中。因此程序实际解码 **20 个 self-pointmap 数组**，各 `[1,224,224,3] float32`，只消费 Z 通道；不能把它写成“只解码独立 Z 数组”，也不解码其余五种预测 head。校准后 Z 转 float64。GT 要求原生 PNG 640×480 且 NumPy `uint16`，PIL nearest resize/crop，然后除以 5000，无 remap。

## calibrate 输出与规则

首 4 帧所有有限正预测/正 GT 成对像素一起计算 `s=median(pred/GT)`，单位为模型单位/米；偶数中位数取两个中间值的算术平均。每帧必须至少有 1 个成对有效像素。ratio 算术非有限、s 非正/非有限则失败，不删掉异常后再取 median。常数基线用这 4 帧**全部正 GT** 的全局 median，包括预测缺失处的有效 GT。

| 文件 | 内容 |
|---|---|
| `calibration.json` | schema=`s15c-pooled-calibration-v1`；`s_model_per_meter`、`constant_depth_m`、总/逐帧成对计数和 GT 计数、规则、源预测 SHA、manifest SHA |
| `calibrated_predictions.npz` | `model_depth_m`，`[20,224,224] float64`；`constant_depth_m`，0维 float64 标量 |
| `calibration_gt.npz` | `calibration_gt_depth_m`，`[4,224,224] float64` |
| `frozen_manifest.json`、`source_snapshot.py` | 使用时的 manifest 原字节和本程序源码 |
| `run_metadata.json` | schema=`s15c-observed-depth-run-v1`，mode=`calibrate`，阶段/实际时刻、SHA读取/数组与PNG解码轨迹、计数、依赖、资源和产物SHA |

原有非正或缺失预测保留；不为改善 coverage 自动修补。若有限原预测除以 s 产生非有限值，作为算术失败记录。

## root 生成 prediction seal 后才 score

```json
{
  "schema": "s15c-calibrated-prediction-seal-v1",
  "sealed_utc": "校准实际完成之后、score之前的真实时间",
  "manifest": "与calibrate完全相同的外部manifest绝对路径",
  "manifest_sha256": "相同SHA256",
  "calibration_dir": "校准输出目录的绝对规范路径",
  "identities": {"校准输出目录全部文件的绝对规范路径": "对应SHA256"}
}
```

seal 必须覆盖校准目录全部文件，含上述 6 个必要文件；排除全部 20 个原始 depth PNG。校准 GT 数组属于已允许的先前校准输出，可以封存。score 验证 seal、先前校准记录和恰好首4帧访问，确认后16帧原 depth 连哈希都未被校准步骤读取。再核原 S15A 身份、当前控制和后16 depth SHA；原 first4 PNG 不重开。随后只解码 `calibrated_predictions.npz` 的 2 个数组和后16张 GT。

## score 输出与指标

保存 `scores.json`、`per_frame_metrics.csv`、总 `arrays.npz` 和 16 个 `per_frame_arrays/frame{i}.npz`，以及来源快照、输入 prediction seal、执行元数据。每帧有 model/constant 两行，共 32 行。

`delta1_all_gt` 使用 `max(pred/GT,GT/pred) < 1.25`，严格 quotient 比较，不改写乘法不等式；分母为全部有限正 GT，预测缺失算失败。coverage 是正有限预测与 GT 有效域交集占全部 GT 的比例。own MAE/AbsRel/RMSE 在各方法自己的交集算；common 在两个方法共同交集算。不做阈值删点、深度裁剪、置信过滤、逐帧尺度拟合或 shift。

`means` 为 16 帧等权主平均。若某指标任何一帧缺失，主平均为 null，完整显示 `contributing_frame_counts`；另列 `available_frame_descriptive_means`，不能将后者冒称完整16帧成绩。空 GT、空交集和非有限误差状态分别保存，全部预定帧保留。数组保存 GT/预测、有效域、共同域与 δ1 成功 mask，便于不同作者复算。

## 已做的人工验证

`work/S15C_preparation/artificial_checks.py` 使用人工小数组与人工 640×480 深度 PNG 做 20 项检查。涵盖池化/偶数 median、预测缺失时常数分母、空校准帧失败、严格 δ1 浮点边界、missing 分母、共同域、空 GT 的完整平均、两模式输入计数、预测 seal 损坏、depth SHA 改变、seal 目录外身份在哈希前拒绝以及 uint8 拒绝。一个其他 head 放了 object canary，若被误解码会触发 `allow_pickle=False` 失败；成功说明当前路径没有打开该 head。

该人工目录的 `bad_seal` 和 `changed_depth` 是刻意触发的负向程序检查，保留为测试证据，不是失败的真实科研实验。程序读取 `docs/S15A_HISTORY_COMBINED_SEAL.json` 和原 manifest 的 JSON 结构以编写接口；没有读取真实 NPZ、真实 depth PNG 或运行模型。真实执行及不同作者独立核验由根任务随后安排。
