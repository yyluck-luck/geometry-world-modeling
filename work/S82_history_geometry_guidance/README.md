# S82：普通历史几何引导生成基线（尚未运行真实生成）

当前已完成：恰四历史缓存/来源可行性审查；原文最近邻；纯目标槽融合函数；17项作者合成张量检查；另一作者源码到论文静态核对。没有新的CUT3R建图、几何优化、真实warp编码或生成。

`latent_geometry_guidance.py`只实现普通凸融合。零strength/no-target-support会返回原对象，但输入有限性/形状检查仍执行；所谓不作算术指不作融合运算，不是零成本。历史槽保留当前denoised，不主动恢复历史缓存。数值测试为人工张量；静态审查不是sampler集成验证。源码与测试绑定SHA原样保留。

下一项优先任务：用且仅用历史[12,13,18,19]（fresh state、revisit=1、eval、512 DPT）一次推理，保留原始heads；生成槽仍按[19,18,13,12]。按INPUT_FEASIBILITY固定known-pose对齐路径，明确K/优化预算/清理行为及真实读回，然后形成可渲染几何。现有53份元数据的有限检索中没找到等输入缓存；不得改用额外历史或目标的旧缓存，也不得用S81传感器评分深度替代RGB-only预测。

最小生成比较：G0原生成、Gpaste同warp末端像素合成、Gguide同warp在采样中引导。渲染/编码/几何优化成本也计入，warp覆盖、洞、边界与全图评价都保留。原Euler即使churn0仍抽随机噪声，未来须保持真实RNG流，不能只说种子相同。

WorldForge/Gen3C已覆盖基本warp/mask融合、自适应引导及保守mask降采样；本原型不叫新方法，也不算完整复现。先跑普通基线找剩余失败，再决定一个可证伪的机制问题。参见UNCERTAINTY_NEAREST_WORK.md和FUSION_SOURCE_AND_NOVELTY_REVIEW.md。

NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false。


当前更新：S82真实四历史预测已完成并接受，成功目录execution_geometry_03，前两次技术失败保留。优先读S82_RESULTS.md及ROOT_GEOMETRY_RESULT_ACCEPTANCE.json。S83固定相机/K诊断准备中，尚未做真实对齐/新生成。
