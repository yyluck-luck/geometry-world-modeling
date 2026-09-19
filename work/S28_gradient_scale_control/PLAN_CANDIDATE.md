# S28：深度梯度修复的匹配工程对照（计划候选，未运行）

**研究问题：只恢复注册深度参数的梯度，是否能修复原消费者深度；还是原目标／初始化的尺度问题依然存在？** 先做普通实现修复的因果对照，不称创新。依据 Supervisor 2.2 的“强baseline→失败分类→根因→针对模块”，本轮仅改变一个深度读取表达式，暂不改变初始化旋转、相机尺度或加先验。

准备依据：原VMem commit `39291e4f272f6b4f270691d930926ab5930f942e` 的源码审计 `work/S27_scale_diagnosis_source/audit.md`。Root于本轮通知S27M实际PASS：注册depth无grad、临时leaf及focal/pairwise有grad；新MST depth与旧common4最终depth全部元素相同。此agent本轮未读取真实数组，以上是root转交的实测依据，执行合同须绑定S27M正式回执。Root另提示预测/给定相机orientation对齐存在大残差，**不能因center对齐好就称camera整体对齐好；S28保留原旋转与原MST，不同时修两个因素。**

## 唯一实现变化与旧depth冻结

原 `optimizer.py:245–249`：

```python
res = ParameterStack(self.im_depthmaps, is_param=False).exp()
```

候选仅替换该函数中的这一表达式：

```python
res = torch.stack(list(self.im_depthmaps)).float().exp()
```

其余raw/逐图reshape与所有原函数不变，不全局修改ParameterStack。只删 `.detach()` **不够**：原helper随后仍会 `nn.Parameter(...)` 重新造叶子，且用首项requires_grad决定整栈状态。直接stack保留原叶子依赖；`preset_depth` 已将旧4的叶子标False，因此旧depth继续无grad，新4标True的叶子可以收梯度。不得把整栈重新包装为一个新可训练Parameter、把旧4解冻或按首帧flag把新4也冻结。此最窄修复限定本pilot相同H/W、CPU FP32；不声称解决异形图的通用padding。

先做必要的合成梯度合同检查（真实GA之前、结果单独标synthetic）：原函数与修复函数在同一FP32输入下depth/shape/数值相同；全4可训练与旧4False+新4True两种配置的原叶子梯度符合各自flag；注册名称、对象与值不因getter改变。它验证实现，不是准确率证据。common4主对照没有旧depth，不能仅凭它声称真实8图旧/新冻结已端到端验证。

## Root已选定：两次新common4，严格匹配起点

| 臂 | 原始输入／约束 | 变化 | 新预算 |
|---|---|---|---|
| A：original matched control | 原S21 original4六头、相同原8PIL准备顺序但仅前4入星形；共同给定optical c2w，depths=None；image pose冻结、pp中心固定、所有focal/pairwise参数保持原设置 | 原get_depthmaps与原autograd路径 | 原MST/PnP＋400 Adam步，linear/.01，CPU8/FP32/seed0 |
| B：gradient-only repair | 与A逐文件同输入，同原MST/PnP/初始化、目标/权重/clean/优化器/随机种子 | 仅上述getter表达式，**原MST完成之后、第一步GA之前**启用 | 同A，400 Adam步 |

原common4历史400步保持原编号与结果；不当作这次新A。之所以新增匹配A，是旧运行没有完整raw focal/pairwise初始化快照，S27M的部分decoded输出也不能无损逆编码回全部原参数。两新臂分别原样初始化，在第一步前核**全部注册parameter和buffer的名称、shape、dtype、值，以及parameter flags**逐字相同；B不匹配即停止，不把“same seed”当成已确认相同初态。保存原始raw参数／buffer，后续不用解码再编码推测起点。

总新增 **2次原初始化＋800 Adam步＋0网络**。这是新因果对照的明确成本，不是重命名或补记旧实验。主B不加尺度prior、不调lr/niter、不改旋转/pose normalization、不使用GTdepth初始化。首次原目标标量和所有forward输入在修复前后逐值相同；只允许梯度图连接变化。若不相同，属于实施错误，不能开始400步。

## 必须实际观察的量

1. **梯度与参数。** 两臂记录首步及末步注册depth、focal、pairwise参数的grad有无、有限性及范数；无优化额外叶子加入。A的原depth无grad是预期诊断，B应连到全部4个注册叶子。每步要求相机/pp等冻结参数不变；任何新参数、非有限梯度/预测或错误冻结立即停止并保留产物。
2. **每步loss与深度变化。** 保留400个实际step、lr、原更新前loss；同步记录各帧注册log-depth和解码depth的均值/min/max、相对初始化的变化量，以及edge尺度/focal。按原分母记录，统计不依赖GT或clean mask。初始和最终完整raw参数、depth/world/focal/pw-scale均保存，必要时每25步附分位数。对齐日志时明确before-step／after-step，不能把第399步前loss当最后一步后目标。
3. **原数学核验。** 两臂完整原400步与clean执行计数；最后额外一次无更新原目标求值与独立目标公式复算、depth→world重建、修正过的独立clean参考，沿用已确认规则和容差。梯度修复不授权放宽任何旧数值门。
4. **深度评分。** 两臂全部封存后才用原S26/S27相同的4帧共同有效像素、传感器深度映射和主指标（原尺度AbsRel、RMSE、delta1、无效预测量）。不拟合scale、不按confidence删点，不扩新场景或只选改善帧。输入/评分早已见，明确这是已见common4工程诊断，非盲测、泛化或生成增益。

## 如何解释与停止

- 初态或修复前后forward数值不相同：停止，先修实施；不得读新评分后倒改设计。
- B仍无注册depth梯度：修复不完整或真实路由不符，停止；不同时加scale prior掩盖。
- B有有限grad且depth改变、准确率改善：只证明这个已见小组件的bugfix收益；仍要评价更大基线／消费者／生成。不能把常规autograd修复称为PhD/CCF A创新。
- B有grad、原loss下降但depth整体缩小或原尺度误差仍差／更差：保留负结果，说明只修autograd不足。深度统计与edge尺度轨迹是机制线索，不能仅凭loss下降宣称“优化更好”，也不能直接认定所有剩余误差均由尺度退化导致。
- 若B数值稳定但几乎不动：先核grad/实际Adam成员/step及初始目标驻点，不能靠增加步数或挑新的lr临时追求效果。
- 无论哪种结果，本批只跑预定两臂；不自动挑片段、扩超参、再跑四种基线。实际超时/RSS或数学门失败均保留FAILED，是否新开下一阶段由root根据证据决定。

## 尺度约束如需后续研究，必须另开对照

S28不加任何尺度项。若它证实“梯度恢复但尺度仍失准”，下一轮先用常规对照区分初始化、标定和目标，保持独立因素：

- 锁定MST的edge scale只是**固定现有估计**，不能叫metric truth；若初始化已偏，它会把偏差锁住。给定camera baseline提供原world单位，但本已是共同oracle相机条件，不能算新增部署传感器能力。
- 从同一anchor0已消费的CUT self pointmap构造深度尺度约束，只能称**模型预测先验**，不是GT；该头的米制倾向未必可靠。若后续考虑它，另冻准确公式、只依赖预测的有效mask、硬/软约束选择与权重；不在本片段已见GT上挑权重。使用非anchor self头还会增加原GA未消费的信息，必须单独说明输入差别。
- 真实相机K／外部量尺若作为输入，须先有已授权、独立来源和所有方法相同的信息合同。**禁止拿sensor GTdepth、由它计算的中位比例或最优scale当prior／旧depth／早停依据。** 评分后oracle scale只允许作为诊断旁表，原主分数不变。
- 原初始化orientation与深度相机分解的残差是另一个候选原因；S28先不动它，避免把旋转修复和gradient修复混成一个收益。

普通冻结、预测尺度正则、修缓存、地图重建必须先作工程对照；它们本身已有传统方法依据。只有常规修复之后仍有重要、可复现且传到真实生成消费者的剩余失败，才讨论新机制。

## 执行前交付与本轮记录

本轮只在 `work/S28_gradient_scale_control/` 写计划／独立派生代码，原源码与冻结S26/S27文件不改；尚未运行模型、GA、任何真实数组或合成梯度测试。计划使用Supervisor 2.2错误根因路线与本地Claude科学批判的因果控制／指标构念边界。Root审S27M实测后已选择新A/B匹配起点；实际S28还需独立前审、冻结输入/源/容差/评分及资源上限，再执行。

建议待冻资源：两臂顺序新进程、CPU8，每臂600秒／16GiB RSS；输出预留2GiB，原权重不加载。该预算是保守建议，非实测耗时；800步外加诊断统计成本分别记录。若采用新代码，必须保存唯一表达式diff、完整原函数AST对照、所有活动模块身份、raw初态SHA和运行回执。
