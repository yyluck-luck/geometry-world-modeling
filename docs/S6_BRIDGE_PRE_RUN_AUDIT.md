# S6 桥接代码运行前独立审查

审查记录时间：2026-09-05T15:49:31.227694+00:00（北京时间23:49:31）。审查者为独立于这两份桥接代码作者的子任务；本子任务此前负责S6模型入口，因此不把模型入口本身称为第二作者独立审查。此次只读源码和现有测试，未运行完整S6、未重新加载模型、未改被审查代码。唯一新写入文件为本审查记录。

结论：在已冻结的三块24图、本机默认数据路径下，未发现会造成提前使用实测深度/GT、两种尺度混用、坐标翻转错误或查询写入显式记忆的明确阻断问题。发现一处应补齐的复现证据缺项：运行归档尚未包含真正执行完整选图的 `src/vmem_retrieval_kernel.py`，已通知主任务。下述结论是静态代码审查，不能替代执行后的文件与数值复算。

## 审查版本

| 文件 | SHA256 |
|---|---|
| `docs/S6_MEMORY_BRIDGE_PROTOCOL.md` | `03af5253e22e7f82064edce5acd3c18f7ca1ebe294eab790e7fdc85eacf02392` |
| `scripts/run_s6_memory.py` | `2a1b33a734a11d646e5cdfea7b560a4b0ea0e132338f42fc6ac90288105ac4be` |
| `src/s6_memory_bridge.py` | `aceaa7828e794289aa580c63605bd3988216ca6832cba45be40d28756b8993cd` |
| `src/rgbd_memory.py` | `f7f2ee5632182ea4c1204150d2076040a20922f2624e880c0a3ca6339e12152b` |
| `src/rgbd_retrieval.py` | `6f5188f7f72b66e93af27ab5a368cd09fcea2166715f1bf4cd0545a686ec3cd6` |
| `src/vmem_retrieval_kernel.py` | `35825a3989f368906cba08808616f0c6922ff08d0a92c7205fddb4822652e2b3` |
| `src/vmem_memory_kernel.py` | `c1bd1a0bb52df48e73f2766ab564e6cec5b9ec665fcf7972a3cbbeb8070210a6` |
| `src/learned_pair_metrics.py` | `604a1be2f2090f76dc103d9515e4f98945f925d6a9675b31fc026b847451339a` |
| `src/rgbd_metrics.py` | `86bf20460895dbc601f712abff327bf7200949c9438eb49d5206b473b3645148` |
| `src/tum_rgbd.py` | `e6018d81e7958fad5e3fb75f59866f291067336a0cdf0cfb2f1b9197f1b3fff4` |
| `scripts/evaluate_cut3r_pair.py` | `3a07baa7f650dab82ed30d6bfa2f67b8d314f82f04437129f9b58f2f101bfc53` |
| `tests/test_s6_memory_bridge.py` | `4655a0031d75c91af1ef35f09651bc32c1b626f219f1371165056d691159a2a1` |

另检查 `retrieval_diagnostic.ObservedKernel`、`rgbd_experiment.residual_stats` 与官方独立CUT3R `src/dust3r/utils/image.py` 的224图像变换。后者来源固定提交 `8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf`。

## 选图与评分隔离

`run_s6_memory.run` 的第一阶段只读取冻结输入清单、S6完成元数据、模型NPZ、兼容性证据和前20张RGB。`load_run` 中虽然计算self/other点图的描述量，但没有打开实测depth或GT，也没有调用其所在模块导入的 `dataset_index`。被审查的相关模块导入阶段只定义函数/类，没有自动读取TUM测量文件。

外层先完成全部三个block，每个block完成stride8和12的两种地图与四次查询。每个案例将最终ID、候选、权重、控制组、建图记录与初始记忆digest写入 `prediction_only_selection.json`，并将该文件SHA加入主记录。全部六个案例离开此循环之后，才设置 `selections_sealed_utc`、将主记录落盘，然后首次调用 `read_trajectory` 和读取测量PNG。评分时重新读取每个选图JSON并核对其封存SHA；只修改内存里的评分副本，不重写封存JSON。

因此，当前源码中“前一块开始评分再继续下一块选图”的路径不存在。模型入口先前为完整性校验读取过深度文件的字节哈希不等于本桥接阶段使用深度数值；本审查的隔离结论针对建图、选帧与评分的数据流。

## 两种尺度及坐标

`normalize_predictions` 只读取self-view的Z和预测camera_c2w。首图全部正有限Z的中位数确定 `n`，不使用conf、其他帧深度分布、S5实测校准比例或raw-other点图。所有深度乘n；相对姿态先计算 `inv(P0) @ Pi`，再只将平移乘n。self X/Y由裁剪K重新反投影，首帧相机坐标作为记忆坐标。

第二阶段才用 `first_frame_scale(first_normalized_depth, measured_first_depth, first_mask)` 计算c。这个函数要求相同形状、有限正预测与测量，取有效首图像素比值中位数；没有查询depth拟合。评分读取的地图数组经 `points * c` 后乘首图GT旋转、加首图GT平移，产生新数组。建图对象、NMS阈值、封存ID及归一化地图文件均不被此操作修改。

裁剪参数直接得到 `(fx,fy,cx,cy)=(245.2734375,245,112,111.5)`。官方640×480输入的224路径先缩成299×224，再裁 `[37,0,261,224]`，与当前LANCZOS RGB变换一致。模型深度没有额外上采样。`make_selector` 使用显式224方形K，再按width/224缩放；标量focal取fx/fy均值，保留固定上游0.65拓宽与居中主点近似。这个近似已在协议中承认，不能将实际surfel渲染称作严格完整K渲染。

记忆点和法向在光学坐标中构造；送入VMem选图的相机姿态经过 `optical_to_vmem`，其内部 `get_transformed_c2ws` 翻回光学姿态供投影。评分直接使用光学记忆坐标和GT光学姿态，没有再套一次VMem翻转。

## 记忆构建、来源与查询只读

原224网格的中心、右、下像素均先通过正有限Z、conf_self≥1、当前帧正有限Z的0.999分位筛选；之后检测相邻Z差≤0.05，利用原相邻像素射线叉积求法向。长度>1e-12后归一化，法向按相机到点方向翻向。半径按冻结的stride、Z、平均焦距和绝对余弦计算；世界/记忆法向只乘旋转。像素剔除与采样剔除分别记录，阶段内计数不重复。

`build_memory` 最多接受20张，入口实际明确传入四组 `[:20]`。来源ID由这20次有序循环生成0..19；查询图没有传入 `Memory.add` 的路径。复用的 `Memory.add` 对旧点树和旧位置做帧内冻结、候选按索引排序、显式距离≤阈值且法向点积>0.6。每帧只给匹配旧点加一次count；frame_mean先取本帧匹配点质心，再按历史帧等权更新位置，不更新旧法向、半径或颜色。

`_check_history` 检查点数、counts长度、完整映射键、非空且不重复的来源列表，以及来源ID范围。`memory_digest` 包含每点位置/法向/半径/颜色的形状和值、所有counts和顺序确定的来源映射。每个实际method×width查询前后都会重新计算digest并与建图完成时的值比较，变化即抛错。选图结果还检查四个不同ID均为0..19。控制组recent4固定16..19；nearest4在相同归一化预测姿态和0.1平移权重下计算，不采用NMS。初始NMS阈值只来自前五个预测姿态的固定距离集合，且两方法共享。

## GT支持与几何评分

`measured_target` 沿用S4：原测量除5000，5×5邻域全有效且各邻居与中心差不超过50mm，外两像素无效；深度与mask均NEAREST缩放、裁剪。取 `[::2,::2]` 得到112×112固定目标网格。GT在RGB时间做平移插值和旋转SLERP，拒绝超0.1秒插值间隔及外推。

`measured_support` 从同一有效查询测量点反投影到GT世界坐标，再逐一投影到20张历史GT视角。先要求正相机Z和连续像素位于视野内，再使用 `np.rint`，并再次检查舍入索引边界；要求历史测量mask有效，历史投影Z与测量Z差≤50mm。源遮挡比投影点近或远超过阈值都不算支持。各方法的四个已封存ID取支持并集，分母为相同的有效查询像素数，变化乘100成为百分点；辅助控制和all20使用同一支持张量。此mask计算不依赖任一方法的地图或预测查询depth。

`project_depth` 对评分副本的地图点作GT投影，`np.rint(uv/2)`投到112网格，并使用 `np.minimum.at` 保留最小正Z。几何主指标使用同一个测量有效mask与两种方法投影同时有限的交集；另保存各方法自己的覆盖率和指标。`residual_stats` 不按预测误差筛点，空交集返回显式空指标，保留大残差。24个条件记录、48个条件×宽度配对由固定循环产生，末尾检查数量；实际相机查询仍为12张，不能把重复条件当新增独立样本。

## 发现与验收边界

1. **待补归档依赖。** 审查版本的 `sources` 未包含 `src/vmem_retrieval_kernel.py`。`ObservedKernel` 继承该文件，实际完整渲染、权重和NMS均在其中。因此必须将其加入 `source_sha256` 与 `experiment_source.zip`，以使本轮完整选图的源码证据可复核。这是归档完整性问题，不是已发现的算法或数值错误；已在模型桥接运行前通知主任务。
2. **本地默认路径范围。** 归档以 `p.relative_to(ROOT)` 组织路径。此次默认项目内数据/推理目录满足该约束；若未来用项目外 `--data` 或 `--runs`，结束归档时可能报错，应在另一次可移植性修复中明确处理。不能把当前脚本的参数存在本身当作任意外部路径均已验证。
3. **静态审查不等于运行通过。** 已阅读8个桥接测试函数，覆盖裁剪射线、纯预测归一化、法向/半径、筛选计数、来源约束、两种地图、完整选帧与digest字段；本子任务未执行这些测试。实际S6模型状态检查已有独立原始证据，但本审查没有重做模型状态运算。完成后还需依据封存文件独立重算全部GT支持与几何指标，并核实六案例的选择封存时间早于测量评分阶段。

当前不能从此审查声称选图改善、几何更准、跨场景有效、完整VMem成功或生成视频改善。


## 追加：运行源档缺项修复核验（2026-09-06T00:31:58.492600+08:00）

此段为运行后的独立补记，前文历史审查未改。追加前原文件SHA256：`6da63f44b32609c8a74eba3ce209deffbe767d09f9de5c6d2769bbd407df3da0`。

实际S6运行的 `run_metadata.json` 中 `source_sha256` 已含 `src/vmem_retrieval_kernel.py`，SHA256为 `35825a3989f368906cba08808616f0c6922ff08d0a92c7205fddb4822652e2b3`；`experiment_source.zip` 内同名文件与当前文件逐字节SHA一致。实际入口 `scripts/run_s6_memory.py` 的SHA256为 `fcf8705d910edc75b684972096dde07513be1fb849a37f5c751df983fd9e5f29`，与前文审查时入口版本不同；其归档列表已加入检索核心。运行源档30项全部与元数据、当前文件相符，核验结果见 [S6_independent_audit/verification.json](../results/S6_independent_audit/verification.json)。

因此，前文待补归档项在实际归档版本中已经解决。实际运行记录开始于UTC2026-09-05 15:51:09.107，晚于原审查记录15:49:31.228；此时间关系依据保存的运行/审查记录，补记没有捏造修复发生的秒级时间。源档ZIP SHA256：`089b395f7fb4c75bb718d32cdbef89be3fe4587b3b827271b4912024a4bb5cbd`。

本次同时从原PNG和GT独立复算S6全部支持与几何评分通过，详见 [S6_INDEPENDENT_AUDIT.md](S6_INDEPENDENT_AUDIT.md)。源档修复核验不等于重新执行VMem渲染/NMS或模型内部状态比较。
