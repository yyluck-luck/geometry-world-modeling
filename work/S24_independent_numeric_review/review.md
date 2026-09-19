# S24 已对齐轨迹的数值复算

结论：**本轮范围内 PASS，未发现数值或配对不一致。** 实际执行 UTC 2026-09-06T15:43:07.395348+00:00 至 2026-09-06T15:43:07.617075+00:00。这是对已公开、已保存的轨迹进行复算，不是新盲测、模型复现或方法效果实验。

## 身份与实现

本复算作者与 `scripts/score_s24_baseline.py` 作者不同，但曾编写 `scripts/s24_horizon_diagnostic.py`。因此对主评分是团队内不同作者复算；对 horizon 是**同作者的新数学路径检查**，不能称不同作者独立审计或外部复现。父任务已收到此身份说明。

新 `recompute.py` 不导入原评分器，使用标量 quaternion 的 SE(3) 逆与乘法；旋转角为 `2 atan2(norm(q_xyz), abs(q_w))`，不使用原 4×4 数值逆 / trace-acos 路径。平移通过 SE(3) 逆的 `-Rᵀt` 与组合计算。统计采用排序后的线性分位数和标准库 `math.fsum`；时间用父 JSON 数字字面值的 Decimal 加减及逐项线性搜索，区别于原 bisect。

没有重新拟合、改变或优化全轨迹 Sim(3)。转换前检查原 SO(3) 与 homogeneous 行；quaternion 单位化是表示舍入处理，不是额外场景对齐。先通过小人工 SE(3)、半周转、Decimal 边界和空统计检查，再读允许的 aligned pose NPZ。

## 实际覆盖

- 三方法 cut3r / ttt3r / filt3r，各 796 个完整帧。检查冻结父/子 manifest、主/horizon PASS与指标SHA、原horizon控制身份、三份aligned NPZ与已存horizon seal的SHA；全部17项输入身份在复算结束重新核对。
- 每方法相邻 795 对、1秒 766 对、5秒 645 对；尾部 NA 分别1、30、151。每个 horizon 的索引0和全部796起点保留；逐项核最早合法终点、时间、实际dt、floor秒分箱和尾NA。共7164行，其中6618有效配对、546尾NA行。
- 全部有效配对的平移/旋转误差与 `all_pairs.csv` 比较；9组全局汇总、27×9=243个秒箱的数量、RMSE/median/p90/max与JSON及CSV均比较，包含空箱/无有效端点箱的null。
- 主评分的全部2388逐帧ATE、三组795相邻RPE、NPZ中保存的误差向量、逐帧CSV，以及官方/矩阵三指标均复核；24个100帧分块保留跨块起点归属，末块96帧/95对。
- 总计168086项标量/身份/结构比较，0失败；这是程序比较计数，不是独立科学样本数。

沿用原容差 `abs(actual-reference) <= 1e-6 + 1e-5*abs(reference)`，未放宽。最大逐对差：平移 2.07e-15 米；旋转 9.83e-11 度。主表最大差 7.57e-14；time/endpoint相关数值差为0。差异位置和完整各组计数见 receipt。

## 资源与产物

CPU库线程固定1；外监控限制180秒、1GiB，20ms间隔观测进程树RSS，超限杀进程。实际子进程数值阶段 0.222 秒，含启动监控 0.315 秒；采样峰值 65978368 字节（约 62.92 MiB）。采样峰值不是连续精确峰值测量。

- `recompute.py` SHA `b65732550403dcda295b2856ce7b47c5feb3aaae8a2966fa47078d70482c6200`。
- `run_monitor.py` SHA `dab386aa05571cbd01f1da7c194b6bc8d534b400a0df4defecb4c83352941577`。
- `receipt.json` SHA `d7cb7a314de57e4b4b192aa8b2ded733efc559d0e2eef2057b0405f7b6b195ea`。
- `caller_receipt.json` SHA `b122cf478ee6dea040575c8ef1664652f62ac60ba54c93f998b3470ed3f08210`。
- `independent_all_pairs.csv` 保存全部复算配对，`independent_summary.json` 保存各组/秒箱重算统计；stdout/stderr与SHA链保留。

未读取sensor depth或RGB，未读取新的模型pointmap，未运行模型/GA，未改原结果、未来协议或S26评分器。aligned NPZ中的GT pose在本次明确解码，不能标为0 GT读取；准确范围是0 **sensor GT**读取。原主receipt没有给aligned NPZ单独封存SHA，身份继承的是随后horizon读取时的seal，此限制未追溯抹去。

本轮不能证明原始预测→全局对齐估计无误，也未重新验证原模型输出或GT配对来源；只证明本次读取的已对齐数组在指定规则下重算得到保存的数值。没有自动找事件、判断遗忘、声称生成收益或项目完成。
