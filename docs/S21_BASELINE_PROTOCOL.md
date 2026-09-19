# S21：先复现几何强基线，再从真实失败提炼方法

本轮按用户最新要求，优先实际基线与失败分析；仍遵循Supervisor vibe-research-workflow的小步复现、固定规则、保存失败，以及本地Claude scientific-critical-thinking的对照公平、构念与证据边界。idea-evaluator用于失败证据形成后的具体候选，不预先许诺创新。

## 问题与范围

比较TTT3R官方树内`cut3r`和`ttt3r`两个状态更新选项在同一真实序列上的相机轨迹误差；额外用原CUT3R运行相同前4帧，核查迁入TTT树的cut3r数值兼容性。此项是本机FP32局部算法复现，**不是完整VMem生成复现，也不是论文TUM-dynamics全基准复现**。本机fr2_desk是此前研究已见场景，不能称独立未见场景。

## 预定规则

- 原始RGB：本机官方TUM freiburg2_desk。按TTT官方`long_prepare_tum.py`时间关联：候选时间差严格小于0.02秒、升序贪心一对一，再按RGB时间排序；stride=1，取前300对。300是官方脚本提供长度之一。只用时间与文件身份选帧，不看预测或GT坐标挑片段。
- 所有算法只输入RGB，ray_mask=False，update=True，reset=False，revisit=1；没有GT相机、深度或动态遮挡mask输入。原图640×480，经官方`load_images_for_eval(size=512,crop=True)`成为512×384。裁剪以launch主块覆盖后的实际参数为准。
- 同一公开CUT3R 512 DPT权重：3173761006字节，SHA256 `45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103`，复用此前已验证本地文件。载入仅允许既有已审OmegaConf类型，weights_only=True。
- TTT3R官方commit `edd6d8c000aaf2ef0f588403e1b3bd3300a54cc4`，只设置官方`model.config.model_update_type`选项；执行`inference_recurrent_lighter`。原CUT3R commit `8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf`执行`inference_recurrent`，前4帧作为源码迁移兼容检查。
- CPU、FP32、8线程、seed=0、无训练。沿用官方local from_pretrained返回的模块training标志，不悄悄更改；记录dropout/BatchNorm存在性。沿用已验证signed RoPE CPU适配，两树pos_embed原文件应完全相同。新增保存/观察钩子只记录返回值，不改张量或随机状态。
- 两个300帧运行分别重载权重并清空状态。TTT tree cut3r与ttt3r均保留官方attention路径，故二者的实际计算量不等价于未经修改的原CUT3R高效attention实现，不用该比较主张原系统速度优势。
- 原始4帧与TTT-tree cut3r前4帧六个输出头的兼容容差：atol=0.0005、rtol=0.0001；pose另以atol=0.0001、rtol=0.0001检查。容差在新预测前固定；不通过时保留结果并撤回“原CUT3R兼容”主张，先调查，不能放宽后冒充预定通过。
- 主指标：官方evo路径的全序列Sim(3)对齐ATE RMSE（米）；辅助：相邻帧RPE translation RMSE（米）、rotation RMSE（度）。300帧全部纳入，按匹配的GT时间一一对应，299相邻对。另保留逐帧误差、全部五个60帧时间段摘要、最差帧供事后失败分析；这些摘要是探索，不据此挑最优规则。
- 时间戳关联可读GT文本字节，但不将GT坐标解析成模型输入。两个方法预测封存且兼容门完成后才作GT坐标评分。旧场景已有曝光如实说明；不声称形式化盲测。
- 数值复核：原evo指标与独立NumPy/SciPy Sim(3)、相邻SE(3)误差计算对照，atol=1e-6、rtol=1e-5。这是同作者不同实现复算，三agent因服务额度中断，**独立作者审查仍缺**，不假称审查完成。
- 资源：每次上限1800秒、进程树RSS 32 GiB，由外部父进程监控；失败/超时/输出缺失都保留，任一主方法不足300帧则主配对结果不完整。无自动降分辨率或删难帧。

本轮不新增方法；预期产物是可信基线比较和仍然失败的具体实例。某方法没有胜出也完整报告。几何轨迹提升不自动等于视频一致性提升。

来源：[TTT3R官方代码](https://github.com/Inception3D/TTT3R/tree/edd6d8c000aaf2ef0f588403e1b3bd3300a54cc4)、[CUT3R官方评测](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/docs/eval.md)、[MonST3R预处理](https://github.com/Junyi42/monst3r/blob/main/datasets_preprocess/prepare_tum.py)。本轮TTT源码逐文件Git blob身份与访问时间见work/S21_baseline_preparation/source_manifest_v3.json及source_receipts，早期网络失败保留。
