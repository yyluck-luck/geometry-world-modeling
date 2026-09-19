# S22 v2：控制CPU位置编码精度后复现FILT3R

v1原生FILT CPU运行4帧成功，但20/24输出兼容条件不通过，FILT300未执行。原失败保留于results/S22_filt_baseline。源码差分明确找到：CroCo encoder调用RoPE前，CUT3R/TTT原代码在CPU也把q/k转FP16；FILT新增CPU分派为FP32。四帧中的第0帧已出现差异，早于任何FILT状态更新。此处是需要单因素验证的实现混杂，不是算法有效性结果。

## 唯一数值改变

另复制124份已核FILT源码，仅改`src/croco/models/blocks.py`的`_rope_cast_context`返回dtype：CPU恢复torch.float16，与原CUT3R/TTT精度一致。CUDA仍为原FP16，其他上下文/模型/状态更新不变；原文件、补丁和原始Git blob身份都保留。新树是**明确适配版**，不能声称逐字节原FILT CPU代码。外层权重和输入仍FP32；以后报告“CPU FP32”时须注明该原内部半精度转换。

模型与实验条件继承v1：同一512 DPT权重、同300已见fr2_desk照片、官方crop=True、无GT输入、CPU8、seed0，官方FILT超参数不变。旧协议见S22_FILT_BASELINE_PROTOCOL.md。先跑新树cut3r4与S21已存原4帧六头对照，**完全保持旧容差**。若仍失败，停止FILT300并调查，不放宽门。若通过，再以共享精度运行FILT300。

新增4帧的科学目的只验证这一已定位的数值混杂；不是重复成功阶段。记录器依然只观察原返回值与299次gain事件，不修改状态。其记录发生在当前帧head输出之后，影响的是后续状态。全部300帧六头输出必须保存。

## 评分与边界

沿用已冻结三指标：全序列Sim(3)对齐ATE RMSE、相邻RPE translation/rotation；全部300帧、299相邻对、五段摘要。每次1800秒与32GiB进程树RSS限制。S21结果此时已经可见：本修订只根据源码/首帧兼容失败恢复相同精度，不根据GT选择超参数或修改FILT公式；公开参数及原4帧容差都未改变。它仍是已见探索的新增强基线。

此版本回答“共同原CUT3R数值精度下的FILT方法”，不用于声称原生CPU精度的最优效果或速度。后者若成为研究问题需另版公平地重跑全部方法，不能混用现有数值。精度控制通过只关闭一个代码混杂，不能关闭跨场景、新方法、完整生成或PhD/CCF A质量缺口。

冻结后所有身份在work/S22_filt_shared_precision/run_manifest.json。不同作者审查仍缺，根任务源代码差分自审不冒充独立作者审查。v1失败和v2结果均需写入最后的报告。
