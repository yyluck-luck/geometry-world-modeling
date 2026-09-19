# RAIMA V3 本机计算可行性审计

- 核算时间基准：2026-09-08T09:50:00.746851Z（北京时间 17:50:00）
- 状态：`PLANNING_ESTIMATE_ONLY`
- 新模型运行：`0`
- 结论：Stage D 的最小单 seed 审计可在本机串行尝试；V3 当前 Stage C 全量设计不适合在单台本机上直接连续执行。
- 证据边界：下列时间由两次已经完成的真实 VMem 两批运行外推；不是 S48/RAIMA arm 的实测时间，也不是性能承诺。

## 1. 真实计时输入

只使用已经独立核过终端证据的两个真实两批 CPU 运行作为量级参考。

| 运行 | receipt SHA256 | 第一批最长时间 | 第二批最长时间 | 总耗时 | 峰值进程树 RSS |
|---|---|---:|---:|---:|---:|
| S40 declared variant | `4c771df1e46f96e218b92f01339b55ebd056ef002fdc28e0083a5bb0907300d4` | 1376.9829202500114 s | 1361.0114883329952 s | 2737.9838646250137 s | 25,862,127,616 B |
| S44 C1 baseline | `44753718ca666d134ac9500ffcd6ada6b0e7e4e6ce6cbfc3bfa9f50de85dcb18` | 1349.0542943750042 s | 1335.1962920000078 s | 2684.242237083032 s | 24,187,961,344 B |

算术均值：

- 两批总耗时：`2711.11305085402285 s = 45.1852 min`
- 第一批：`1363.0186073125078 s = 22.7170 min`
- 第二批：`1348.1038901665015 s = 22.4684 min`

本机物理内存实查为 `68,719,476,736 B`（64 GiB）。单进程历史峰值约 22.53–24.08 GiB。为给操作系统、模型加载瞬态和证据守护进程留余量，本审计按一次只运行一个生成进程估算；不把理论上可能同时容纳两个进程写成可用吞吐。

## 2. S48 V6 每个 seed 的最低 arm 数

按冻结协议的最低结构计数：

1. A0 的 F00 与 3 次 replay：`4` 个 fresh target process；
2. 两种 edit family × 两个符号 ×（F11 edit/zero、negative edit/zero、positive edit/zero）：`24` 个 fresh target process；
3. 合计：`28` 个 target process / seed。

该计数尚未包含 Pilot-B 的 F10/F01、CLIP/LPIPS、失败重试、reference 渲染、相机门和人工审计时间。

为了给当前本机路线一个透明的下界，假设每个 seed 只创建一次可证明等价的第一批快照，之后每个 target process 的成本近似一次历史第二批：

`T_seed_lower = mean_phase1 + 28 × mean_phase2`

得到：

| 规模 | target process 数 | 串行时间下界 |
|---|---:|---:|
| 1 seed | 28 | 39,109.9275 s = 10.8639 h |
| 5 seeds | 140 | 54.3193 h |
| Stage C 的 80 个 scene-trajectory-seed 组 | 2,240 | 869.1095 h = 36.2129 d |

若 Pilot-B 额外需要暂按 `16` 个 target process / seed 计入，总数变为 `44`：

| 规模 | target process 数 | 串行时间估计 |
|---|---:|---:|
| 1 seed | 44 | 60,679.5898 s = 16.8554 h |
| 5 seeds | 220 | 84.2772 h |
| Stage C 的 80 个组 | 3,520 | 1,348.4353 h = 56.1848 d |

## 3. 这些数字没有包含什么

这不是完整 wall-clock 预算。至少还缺：

- S48 V7 之后实际 hook、renderer、reference 和 metric 的实测成本；
- fresh process 启动、模型重载、证据落盘与文件校验开销；
- 不合格相机、reference 或 hook 的预注册失败率；
- CLIP、LPIPS、flow、placebo、支持域构造与统计汇总；
- 两个独立审查人的复核时间；
- 因温度、内存压力或磁盘 I/O 造成的波动。

因此 `36.2–56.2 d` 应理解为当前协议在乐观复用假设下的串行生成量级，不是上界。

## 4. 结果前决策

### A. 本机只承担 Stage D 最小否证

在 C1/C2 合法 baseline、S48 V7 source 双审和 G0–G1 全部通过之后，先做一个预注册 source-target、一个 seed 的最小 arm，预算约 `10.9 h` 起。它只能验证 hook、量级、控制和自然失败是否存在，不能估计系统性频率，也不能授权创新主张。

### B. 快照复用必须先证明等价

若要复用冻结的第一批状态，必须证明它与每个 fresh full run 在模型状态、RNG、source identities、consumer inputs 和输出上满足预注册等价门。只能减少重复第一批成本；28/44 个 target arm 的第二批成本仍在。

### C. Stage C 需要额外算力或经统计复核的两阶段设计

当前 8 scene × 2 trajectory × 5 seed 的确认设计若不改，需加速硬件或可审计的并行资源。若未来采用序贯停止、分层抽样或减少 arm，必须在看确认性像素前由独立统计审查重新冻结门槛；不能把 Stage D 结果用于事后删控制。

### D. 不用计算压力修改科学结论

本报告只改变执行安排。它不把 8 scene 降成 1 scene，不把 5 seed 降成 1 seed，不删除 negative/positive/replay/sham/placebo，也不把局部 pilot 改称确认实验。

## 5. 当前裁决

`LOCAL_STAGE_D_FEASIBLE_AFTER_ALL_GATES; STAGE_C_COMPUTE_BLOCKED_IN_CURRENT_FORM`

这不是研究失败。它说明下一项真正有信息量的工作应是：先用最小 Stage D 检查候选现象是否存在，再根据真实效应和失败结构决定是否值得为 Stage C 获取加速计算或冻结更高效且统计上可辩护的设计。
