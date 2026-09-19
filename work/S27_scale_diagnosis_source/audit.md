# S27：原消费者尺度合同与初始化审计（SOURCE ONLY）

**优先发现：原深度 forward 路径中的 `ParameterStack(...).detach()` 断开了注册深度参数与目标，必须先核实实际梯度，而不能把 `requires_grad=True` 当成深度已更新。** 源码未发现 S26 把生成器的相机归一化漏传给 GA 的转接错误；原 GA 本来就不接收那份归一化相机。固定 image pose 也不固定 pairwise scale。初始化会估计Sim(3)尺度；目标函数层面有缩小几何的可行路径，但它**不等于原Adam能沿该路径更新深度**。本次大误差的具体来源仍需区分。

本轮起因是 root 报告 S26B 深度误差偏大。此 agent 没有读取该批预测、传感器 GT、共同相机数组或评分数值文件，没有运行模型、PnP、MST、GA 或数值扫描。只读原源码、冻结合同 JSON 和前期接口文档。原失败、冻结代码和主账不改。下文 `VMEM` 指 `/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem`，固定 commit `39291e4f272f6b4f270691d930926ab5930f942e`。

## 1. 相机/单位实际路由

| 路径 | 精确源码与合同 | 结论 |
|---|---|---|
| 导航输入 | `navigation.py:25–39,105–149,202–236` 用调用者给定的 c2w，在其 world 单位中按 `step_size` 移动和插值；`app.py:181` 设置0.1。`navigation.py:300–307` 转身保持相机中心。 | 源码没有把0.1认证为传感器测量的0.1米。给定相机定义重建所使用的坐标单位；真实导航存在纯旋转的源路径，但本轮没有运行该路径。 |
| 持久原相机 | [pipeline.py:179](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/modeling/pipeline.py:179>)–185保存初始相机；1245取 target slice；1263以 `torch.cat` 新建 context+target 的生成条件；1297保存原 target。1318–1334与1420–1429中调用者轨迹整体归一化被注释掉。 | 生成条件的后续原地修改作用于新cat，不回写持久 `self.c2ws` 或 target 的平移单位。 |
| 生成器局部归一化 | [pipeline.py:1089](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/modeling/pipeline.py:1089>)–1120把新cat平移居中，按 `camera_scale`/首相机半径取缩放；1128–1131翻Y/Z并缩放c2w/w2c平移。`configs/inference/inference.yaml:19` 的camera_scale=2.0只经此路径使用。 | **只用于生成条件，不是原 GA 的预处理步骤。** 不应为修深度误差在S26事后把GT相机居中并套2.0归一化，除非另立明确的诊断条件。 |
| GA 相机 | [pipeline.py:950](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/modeling/pipeline.py:950>)–955 deepcopy原c2w并翻第1/2列；976–988直接传 `poses` 与历史depth。`surfel_inference.py:406`直接转交prepare_output。 | 翻的是相机轴，平移列未缩放。GA输入是该world frame的光学c2w，深度沿相机+Z。生成用的K没有传入GA；生成K的归一化坐标与GA估计的像素focal不能混用。 |
| S26 转接 | [s26_consumer_baseline.py:113](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/scripts/s26_consumer_baseline.py:113>)–121按TUM行中的xyz与xyzw构造c2w，保持原平移，FP32后封存。`saved_heads_adapter.py:164–205`只clone给定c2w/旧depth，原400/.01函数原样调用。S26B复用该控制输入；attempt2只加标准库导入bootstrap，原child runner保持。 | 按已冻结“TUM optical c2w、meter translation”输入语义，直接进入轴翻转**之后**的GA接口是相符的；等价pipeline输入是 `C_TUM·diag(1,-1,-1,1)`，不是再翻一次TUM。此源审不重新认证TUM原始标定、相机时间对应或实际矩阵内容。 |

因此源路径没有支持“漏了camera_scale=2所以深度小”的结论。全局平移居中在理想几何中不改深度；它可作为以后数值条件性检查，但不是自动合法的准确率修复。原归一化、FP32编码及初始化epsilon并非严格数值等变，不可只凭代数宣称任意改原点结果必然逐值相同。

## 2. 固定了什么，尺度从哪里来

[surfel_inference.py:174](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/extern/CUT3R/surfel_inference.py:174>)–203依次创建新scene、preset旧depth（若有）、preset全部pose、MST、GA、clean。六个关键原文件与本次使用的S17C隔离源码逐字相同，身份见receipt；没有发现这些尺度函数被兼容补丁替换。

- `optimizer.py:102–121` 冻结全部 **image pose**，并强制 `norm_pw_scale=False`。`base_opt.py:163–169` 的 **pairwise pose** 是另一组可训练8维参数，包含log-scale；274–284仍返回每条边的自由正尺度，并把它乘到rotation和translation。`get_pw_norm_scale_factor:266–272` 在False时仅返回1，即“不执行默认尺度归一化”，**不是固定尺度为1**。runner的检查文字“metric pair scale”只能证明此开关与pose冻结，不能当米制准确性证明。
- `optimizer.py:29–40,166–176,218–246`：无旧depth的common4中全部注册depth标为requires_grad=True；后续8图旧4标False、新4标True。**这只是声明，深度forward的detach使它不等于真实梯度可达。** focal的get路径没有同样detach，pp默认中心固定。`depth_to_pts3d:251–261` 用给定pose与当前depth/focal重建world。输出的单位意图来自给定camera translation，不能保证其估计数值正确。
- `optimizer.forward:269–288` 只比较重建world与经过各边Sim(3)变换的预测点。`commons.py:48–52,78–82` 中 `dist='l1'` 实际是**逐点三维欧氏距离**乘log-confidence，非三个坐标绝对值之和；全像素按各端面积平均。没有传感器depth项、保持CUT原米制尺度的先验，或image-pose独立损失项。旧depth是约束，不是新增真值监督。

**具体梯度路径（独立静态核对，微型原函数数值核验由另一agent负责）：** `forward269→get_pts3d263→depth_to_pts3d255→get_depthmaps244`，后者调用 `ParameterStack(self.im_depthmaps,is_param=False)`。`ParameterStack:309–320`先只看第一个参数的requires_grad，再 `torch.stack(...).float().detach()`；若首项True就创建一个新的临时 `nn.Parameter`。common4中这个临时叶子可有grad，但注册的 `im_depthmaps.*` 已断开；old4+new4中首项False，整个临时stack不需梯度，后4原参数同样断开。`base_opt.global_alignment_loop:533–545` 在循环前把**注册参数**交给Adam，临时叶子不在此列表。原forward未见其他连接注册depth的目标项。

因此应预期：正常梯度路径下，原depth的 `.grad` 为None；400步可调整focal/pairwise参数、降低loss，却不能仅凭该forward更新原depth。实际是否如此应以最小真实保存头forward/backward查证，不在本页伪称已运行。MST中的 `_set_depthmap` 是 `.data` 写入，仍能在优化前设置depth；这与梯度断开不矛盾。该问题来自未改动的原源码，不是S26 adapter新加的数学。它更像原实现缺陷，**不是创新成果**；未来修复须另立版本并做真正梯度/公平比较，旧400步执行和旧分数仍保留。

## 3. 初始化可能改变尺度，且当前历史记录不足拆开阶段

`base_opt.py:473–485` 明确走 `init='mst'`，不会因为pose已知自动改走 `known_poses`。`init_im_poses.py:174–184,195–203,239–248` 先从星形预测构建点图，对未有pose的帧估计focal/PnP，失败可能回落identity。

[init_im_poses.py:103](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/extern/CUT3R/cloud_opt/dust3r_opt/init_im_poses.py:103>)–114把预测相机对齐到known poses，**实际是Sim(3)，虽注释写SE3**。367–382向每个camera center附加沿z的小杆，杆长对源/目标各自取 `max(median_pair_distance/100,1e-6)`，再调用 `roma.rigid_points_registration(compute_scaling=True)`；尺度绝对值低于1e-6才替换1。由此源/目标预测运动尺度差、PnP退化、极短基线和epsilon均可能影响初始s。它们尚未在本次数据上量化。

随后116–129用点配准设置各edge尺度；由于norm=False，s_factor=1。133–139的初始depth由**对齐后的预测im_pose**反变换点图得到，而 `_set_pose` 对已冻结image pose跳过写入（`base_opt.py:243–247`）；因此源上允许“计算初始depth用的pose”和“优化实际固定pose”存在残差。MST可写入标True的新depth，标False的旧depth会拒绝写入；后续Adam的深度梯度问题见上一节，不能仍沿用“新depth继续优化”的旧描述。

**可用性限制：** S26B `SceneObserver:236–254`仅记录MST计数/固定约束、PnP成功与focal；255–271记录每步loss/lr。未保存raw PnP pose、Sim(3)的s/R/t、MST后depth/edge-scale。`pairwise_state.npz`在clean时保存的是最终状态（275–294）。所以“400步loss下降”不能区分初始化已压缩和后续缩小；不得伪造历史MST快照。共同旧4的IMPORT_VALIDATED也不补出当时未落盘字段。

## 4. 可由源码推导的退化例子（非数据发现、非新方法）

令固定相机中心为 `C_i`，像素射线为 `r_i`；`X_i=C_i+R_i d_i r_i`。边e变换后的预测为 `Y_ei=s_e Q_e P_ei+t_e`。固定focal、权重和旋转；无任何depth被preset时，对任意 `0<λ<1` 取：

`d'_i=λ d_i; s'_e=λ s_e; t'_e=C_0+λ(t_e−C_0)`。

每个新尺度为正；原log-scale和signed-log translation可表示任意有限λ下的参数（极限及浮点下溢另论）。这是**直接重参数化目标的解析候选，不是沿原autograd图的可达更新**。则逐点残差严格满足：

`X'_i−Y'_ei = λ(X_i−Y_ei)+(1−λ)(C_i−C_0)`。

如果全部中心同C0，原欧氏距离目标满足 `L'=λL`。在权重非负且原loss>0时，缩小可降低目标，λ趋零的infimum为0；并非“程序一定走到0”或“准确depth已被证明错误”。若中心不同，在固定非负权重下有 `L' ≤ λL+(1−λ)B`，B为按原面积/权重聚合的camera-center距离地板。**短时间跨度不等于B已小，必须实际测camera baseline；非零baseline也不代表必然坍缩。** 此推导只给出可行竞争路径，不给出本次优化轨迹的原因。

最强反例：old4 depth已固定时不能把全部depth乘λ，所以该精确退化不能原封不动用于三个8图臂；给定分离相机、预测一致或尺度初值已良好时，也可能有正确的有限解。common4若已坏，后续共用旧depth会继承错误约束；这仍需已存数值确认，不由本页假定。纯旋转尺度不可观测和通常的尺度正则/已知标定控制不是创新。

## 5. 最小诊断，先0新GA，再决定是否需要新运行

| 要区分的原因 | 最小所需量与动作 | 能说什么／否决条件 |
|---|---|---|
| 输入单位/轴/帧对应错误 | root已有共同camera、输出c2w、原frame元数据；核相同帧/给定pose和轴翻转往返。保存头的独立self-depth仅作前消费者参照；不能拿未消费head直接替代原GA。 | 合同不符则先修转接并新立版本；合同相符仅排除该错误，不认证尺度。此处不重读GT或扩指标。 |
| 最终解的几何尺度/形状问题 | root从已存common4输入/输出与final pairwise state报告depth分位数、final edge scale（scaled旋转块列范数/行列式需先核uniform-scale）、focal与camera baseline。如用已评分sensor诊断常数尺度，要标GT oracle，保持原分数不变。 | 常数scale能解释误差是诊断，不是可部署修复；不能据后验scale把原主结果改好。 |
| 原目标是否鼓励缩小 | 仅common4，在**原固定camera**下对保存最终状态实施上面的解析λ路径，用原输入/权重/全像素重算原目标；另独立重算残差恒等式。预先固定少量λ如0.25/0.5/1/2，仅诊断，不挑最好值发布新成绩。0模型、0GA、0GT，但这是新数组重算，应由root另行记录后执行。 | 若缩小增加loss或效果仅舍入，否决“该最终状态附近仍受此方向驱动”；即使能降loss，也不证明优化实际走过该路径。已old-depth固定的8图不能沿此不合法路径比较。 |
| 初始化已有偏差，且真实深度梯度断开？ | **优先common4：** 相同保存头/控制相机/源/seed，只重放原MST/PnP，保存初始化depth/focal/pw-scale，然后做一次真实原目标forward/backward，在任何Adam step前停止。记录每个注册depth参数的grad是否None和optimizer成员关系；比较重放初始化depth与旧common最终depth。 | 0 Adam步；一次新反向传播是诊断，不能计作原历史。MST→旧final相等加原depth无grad才支持初始化主导；不等则先查RANSAC/seed/环境或额外写入，不能隐瞒不兼容。原400步不重跑。 |

本页只准备上述区分，不批准/执行新运算或改lambda/scale先验。先定位合同与尺度，再决定更长/更大基线组件对照；不把8帧pilot的大误差直接推广为原VMem长生成失败。沿用Supervisor第2章先baseline failure/根因，本地Claude科学批判用于上述可证伪条件与证据边界。
