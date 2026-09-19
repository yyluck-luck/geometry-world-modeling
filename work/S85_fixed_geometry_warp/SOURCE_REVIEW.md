# S85 独立源码前审

审查时点：2026-09-10T20:18:04.761515+00:00

**结论：GO，允许 root 执行这一个已冻结的四历史 × 四目标投影批次；没有发现实质 blocker。** 此结论只针对实现与合同，尚未验收真实结果。

## 精确版本

- `project_fixed_geometry.py`：`344ad059365bc775af0c8336eeffdaf0b44c073626aca3a4c3a10e138c2d3019`（19083 B）。
- `CONTRACT.json`：`bcf4801ff1619ec74e5714e2ba90c556a6abb6c45f48b2f3185b2eb9925a333b`（17834 B）。
- `check_projector_synthetic.py`：`269163f28752cb963949eba05d4773237f68a5d849e9fb868c41b36939c98fcd`（8467 B）。
- `AUTHOR_SYNTHETIC_01.json`：`c694a8778ec69a68121f439f850c67c929bce9653d80145d092cb0c1ec3d96d6`（1877 B）。
- `AUTHOR_PRECHECK.md`：`e9dbbfe1e31f6275216364fb5b03c2222ce8325cbd68faa1e3f56066339c8930`（3165 B）。

## 已完成核查

- **source_and_contract**：Full 359-line runner, full contract, full 151-line artificial checker, author receipt and precheck read; current frozen byte identities verified; AST parsed only.
- **input_identity_scope**：Two fixed original NPZ archives, exact whole-file and seven consumed field shape/dtype/body checks. S83 selected field metadata independently matched accepted textual receipt. S69 identity and S72 actual K matched textual metadata. No real archive was opened during this review.
- **geometry**：Saved source camera-Z and original integer 512x384 source grid; actual FP32 K/P promoted to FP64. Optical target c2w selected by IDs20..23; exact K principal point287.4000244140625 retained. Source backprojection and target R-transpose transform implement frozen optical convention, without scale fit or axis conversion.
- **statuses_and_footprints**：Mutually exclusive source nonfinite/nonpositive, target nonfinite/nonpositive, outside and valid states; target Z tested before division. Closed target center domain[0,575]^2, positive four-neighbour footprint weights only; no clipping, epsilon or snap.
- **selection**：Lexicographic target pixel/Z/history19,18,13,12/source pixel order; slot is harmless final deterministic key. Weights qualify candidates only. Winner RGB is copied exactly. Second candidate is full-order item2 including same-Z ties.
- **full_denominators_and_schema**：All4 histories retained for each of4 targets:16 pairs and3,145,728 source-point rows, not independent scenes. Dense status/XYZ/UV/four-slot tables, all candidates including losers, winner/second, mask and RGB schemas align with implementation. Empty-candidate path retains complete holes.
- **information_isolation**：No target RGB/sensor depth/model/optimizer imports or reads. Source colors come from frozen S83 original RGB01; unused confidence/world-point fields are not decoded. Fixed source100-step state is not selected by S84 sensor score.
- **bounded_failure**：One fixed execution_01, exclusive mkdir/file creation, no automatic retry.300s alarm,10GiB sampled self peak RSS,2GiB output cap with reserve; sequential target saves. Partial files and traceback survive failure. Resource controls are not a kernel hard memory limit, as contract states.
- **artificial_evidence**：Author single successful artificial run is bound to this exact runner and was inspected, not rerun. Literal q footprint exactness is correctly separated from FP64 same-pose coordinate closeness. Endpoints/outside, all-hole, nonfinite, Z<=0, rotation, equal-Z ordering and unweighted colors are represented.

## 边界

本次只读源码、合同与既有文本回执，进行了 AST 解析；没有导入运行投影器，没有重跑作者已成功的人工检查，没有读取真实 PNG/NPZ 数值、模型或传感器。原输入 SHA 及实际字段数值仍由执行时校验，随后由独立输出复算核对。

单批包括 16 对、每对 196,608 个源点记录；3,145,728 条记录不等于独立场景。孔洞与未命中保持显式未知，候选数、覆盖和第二候选不代表准确率或真实遮挡。普通硬深度选择不构成新方法验证。

300 秒是内部闹钟限制；10 GiB 是分阶段自进程峰值 RSS 检查，合同未声称操作系统硬内存隔离。root 应据实际退出、回执和文件验收，不能用人工测试或纸面内存估计替代真实记录。源码/合同冻结后启动由 root 负责。

下一步只准备独立输出核验器，待 root 阅读并授权后从原输入复算；本前审不提前宣布结果 PASS。
