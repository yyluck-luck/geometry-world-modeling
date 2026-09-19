# S34 固定评分协议（源码准备；须根冻结后运行）

三个条件固定为 old_fixed_zero、old_fixed_free_400、old_fixed_common_scale_400。只评各自新帧 4–7，共 12 行、3 个四帧等权组。共同旧 0–3 不进入质量均值。数据为 S26B 已见 fr2_desk 前八配对帧，本轮不重选、不新增数据、不拟合尺度。

本轮只有四张 sensor GT 深度：索引 4–7，身份逐项继承 work/S26_scoring_preparation/candidate_scoring_inputs.json。准备阶段只读其 JSON，不读取 PNG 字节或数组。共同 GT optical c2w 是 producer 的明确输入，不能写为无 GT 实验。所有 common_old 和三个端点的 PASS 回执、正式合同、全部输出必须封存，消费者必须到达记录下来的终态，之后评分才可读这四张 GT。

主指标原样调用封存 scripts/score_s26b_consumer.py 的 depth_metrics、load_sensor_depths、aggregate。sensor 480×640 uint16/5000，以 floor((2i+1)*source/(2*target)) 最近邻映射到预测 384×512。所有正有限 GT 像素构成分母，不用 confidence 或远距阈值筛点。预测在有效 GT 上有非正/非有限值则该帧 AbsRel/RMSE 为 NA，delta1 仍按完整有效 GT 分母计失败；空 GT 保持 NA。delta1 严格 <1.25。四帧全定义才可给组均值。禁止按有效帧替代、逐帧/全局 k、最优步或答案调参。

全部四个 packet 要求 6 个 FP32 字段 depth/point_cloud/conf/focal/pp/c2w 及固定形状。解码后的共同旧 depth 和三个端点旧前缀用预定 atol=rtol=1e-5 检查 log/exp 往返；这是输出检查，不代替 producer 对冻结叶对象、flags、raw bytes 和 grad 的实际门。

消费者保存的地图、渲染、来源票权只描述差异；不拿渲染 depth 简单 resize 与 sensor GT 比作可见性准确率，不把配额叫默认 context IDs。若消费者阶段 FAIL，评分可以继续评已封存的三份合法几何端点，但报告必须显式标明消费者不可用，不能据此宣称完整 S34 PASS。

CPU1、120秒、2GiB，调用前至少10GiB空盘，外部监督；目录已存在即拒绝覆盖，失败保留，不自动重试。此评分 0 网络、0 MST、0 Adam、0 backward、0 clean。新结果必须另式核算后再标为独立复核通过。相邻四帧不是独立场景样本，不据此声称新方法或视频质量收益。
