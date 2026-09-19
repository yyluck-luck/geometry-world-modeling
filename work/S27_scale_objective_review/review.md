# S27 独立尺度目标审查：理论方向成立，但不能据此解释真实运行

**结论：同中心、全部 depth 可改变且 pair scale 不归一化时，目标确有共同收缩使损失按比例缩小的数学路径。非零短基线和固定旧 depth 都限制这条论证；它不是当前真实低质量输出的根因证明。更优先的源码问题是 `ParameterStack` 切断了原 depth 参数的梯度，因此“depth 标为可训练”不能直接解释成 Adam 实际更新了它。**

本审由 `research_novelty_routes` 独立于 root 的源审作者完成。只读源码/记录，执行极小人工张量；无模型前向、GA、优化器 step、真实输出 NPZ 或传感器 GT 读取。接续时读过主日志中的 S26B 汇总，因此不自称未知结果或盲测；以下推导不使用其误差数值。报告应用 Supervisor 2.2 的 baseline→具体失败路径，和已读 Claude 科学批判技能的测量有效性、替代解释及因果限制要求。不是新文献综述或新方法。

## 原函数真正优化的对象

源根为 `work/vmem/extern/CUT3R/`（工作区完整路径与文件 SHA 见本目录 `review.json`）。关键定义如下。

| 对象 | 该源码路径 |
|---|---|
| image pose | `optimizer.py:102–121` 对全部给定相机 preset 后冻结，最后**无条件** `norm_pw_scale=False`。不等于 pair pose 也固定。 |
| pair pose/scale | `base_opt.py:163–169,266–285` 每边自由 quaternion、translation 参数和 log-scale；`s=exp(log_s)`，实际 pair 仿射是 `s Q Z + s τ`。false 分支归一化因子为 1，`base_scale=.5` 不再作为有效共同尺度约束。 |
| 点图 | `optimizer.py:251–288`：`X_i=c_i+R_i d_i[(u-cx)/f,(v-cy)/f,1]`。focal 全栈可训练，pp 默认固定中心。 |
| old/new depth 声明 | `preset_depth` 用 prefix zip 写 log depth 并固定旧帧；新帧参数仍标为可训练。**实际梯度连通性另见下面的问题。** |
| pair adaptors | 默认 `allow_pw_adaptors=False`，初始 0，经 exp 后 `(1,1,1)`，本路径无可训练的 xy/z adaptor。 |
| head 点/权重 | 预测点与 confidence 为 NoGrad；`_stacked_pred_i/j` 与 `_weight_i/j` 是缓冲区。默认权重 `log(conf)`，整个优化中固定；后置 clean 的 `im_conf` 不是这些 loss 权重。 |
| loss | `commons.py:78–79` 名称 `l1_dist`，实际是**每点欧氏范数** `||X-Y||₂` 乘权，不是坐标绝对差之和。两端分别按 `total_area_i/j` 除，最后相加，不除总权重，也没有当前尺度分母或深度尺度先验。 |
| anchor | 原 star 的 0 是每边的共同图端，不是自动固定的 image-0 三维点坐标或 pair scale；无旧 depth 的 common4 不能仅凭 anchor 命名认为尺度被锚定。8 帧时旧0深度固定，focal 仍自由。 |

原模型默认 `conf_mode=(exp,1,inf)`，`postprocess.py:142–148` 给 `1+exp`，所以通常 log 权非负；本轮不读取真实权数组。下面的代数齐次式不要求权非负，但“loss 非负/严格下降”和三角上界须明确采用非负固定权。若初始 loss 已为 0，不能说继续缩小会严格改善。

## 严格成立的缩放族及限制

令固定相机中心都为任意共同位置 C；保留各相机旋转、focal、pp、pair rotation、预测点和权重。pair 的世界平移写作 `t_e=s_e τ_e`。对任意 `α>0`，考虑：

`d'_i=α d_i; s'_e=α s_e; t'_e=C+α(t_e−C)`。

因此 `X'_i=C+α(X_i−C)`，`Y'_ei=C+α(Y_ei−C)`，每个残差都变为 `α(X−Y)`。固定分母和权重下 **`L(α)=α L(1)`**。正 loss 在 `0<α<1` 时下降，α→0 给零下确界；有限 log-depth/log-scale 不取 α=0，不能把极限称有限参数的零尺度最优点。

参数化需写正确：对应原代码的 raw translation 是

`τ'_e=τ_e+(1−α)C/(α s_e)`。

当 C=0 时，raw τ 保持不变而实际世界平移自动随 s 缩小。**不能同时把 s 和 raw τ 都乘 α**，那会把世界平移缩成 α²；C≠0 时只缩 s 也不对。此处是可行参数族，尚不是梯度流或 Adam 路径证明。

若中心不同，选参考 C，并仍只缩深度、保持 image pose 不变，则端点 i 的精确残差为

`r'_ei = α r_ei + (1−α)(c_i−C)`。

非负固定权给上界

`|L(α)−αL(1)| ≤ |1−α| B(C)`，其中 `B(C)` 是按原两端面积分母加权求和的 `||c_i−C||₂`。

因此“短基线可能提供弱尺度约束”是有条件的可检验判断；基线相对当前几何残差/尺度有多短，不能只看厘米数。`B<L(1)` 是沿此可行族对 `0<α<1` 改善的充分条件，前提仍是全部 depth 可改变。相反，任何正但很短的基线也可在初始正确拟合 `L(1)=0` 时使收缩**增加**损失。人工 0.01 m 基线例子验证了这个反例；它不是当前相机基线测量。

若旧 depth 固定且保留其 focal/pose/pp，旧 `X_old` 不随 α 缩放；相应残差变为

`r'_old = α r_old + (1−α)(X_old−C)`。

所以 common4 的无旧深度共同收缩路径不能原样迁移到三种 8 帧结果。所有 star 边都包含旧 anchor0，其正权且非退化的点分布对自由 pair 尺度/平移形成实际约束；一个点、全零权或退化点图则不足以保证尺度可识别。focal 自由还允许横向几何改变，故“冻结 depth”也不等于排除所有其他退化；不能据此宣布 8 帧系统绝无尺度问题。

## 先排除梯度断开的实现问题

`optimizer.py:307–317` 的 `ParameterStack` 先读 `params[0].requires_grad`，再执行 `torch.stack(...).float().detach()`；必要时封装成一个新的 `nn.Parameter`。`get_depthmaps` 以 `is_param=False` 调它。`base_opt.py:533–569` 的 Adam 则持有 `net.parameters()` 中原先注册的参数。

从这个代码路径看，临时 depth stack 与原 `im_depthmaps` 之间的自动微分链被切断。提取原两个 helper、仅用两张每张 2 元素的人工深度参数验证：

- 原两张均 trainable：临时 stack 成为新叶子，反传后它有梯度，但两张原参数的 `.grad` 都是 `None`；临时叶子不在原参数集合。
- 第一张 frozen、第二张 trainable：临时 stack 的 `requires_grad=False`，第二张的训练标记也不能穿过这条前向链。

这些是 **实际执行过的小 helper/autograd 检查**，不是完整优化器运行。对于本轮读取的未改源码前向，这个断链是确定的实现性质；但尚未用当时的 post-MST/post-GA 深度或梯度记录证明任何真实 run 的历史过程。MST 的 `_set_depthmap` 会在 GA 之前直接初始化可写的新深度；不要把初始化给的尺度误称为随后 400 步学出来的尺度。也不能从 optimizer 列表/flags、总 loss 下降、400 步计数推断某个原 depth 参数收到梯度。

这使“共同尺度收缩是可行函数族”与“当前 Adam 沿其移动”分离。即使理论族成立，也应先核真实使用的源码身份和原 depth 的梯度/前后数值；否则更直接的解释可能在初始化或断链，而非尺度目标本身。

## 最便宜的后续判别与普通对照

1. **先核更新路径。** 本轮已完成源码 helper 的小反例。下一项只在另行授权的最小组件检查中记录每个原 depth 参数的 gradient presence/norm、post-MST 与 post-GA 全量差；没有历史快照就写未记录，不回填。若原参数确有从其他路径来的梯度，须定位该路径并修正本页推论。若断链成立，先作普通 autograd 工程修正及旧 depth 仍固定的检查，不把它包装创新。
2. **再核目标可行族。** 对适用的无旧深度问题，事先固定 α 集合（例如 `[0.5,0.8,1,1.25,2]`），在完整固定分母下做保存参数的 objective profile，分开全部自由 d 的理论扰动与真实可更新量。8 帧不得偷改冻结的旧 d 来制造更低 loss。全 α 与失败都保留；仅 profile 降低不足证明原优化轨迹发生收缩，更不足证明 GT 或生成受害。本轮不执行这一真实数据 profile。
3. **普通尺度锚定对照。** 以合法来源给一个固定 pair scale、或对平均 log-scale 加显式约束，并记录尺度来源；也可保留一个有非退化结构的旧 depth anchor。直接打开 `norm_pw_scale=True` 会固定 pair 几何平均尺度为 `.5`，同时影响初始化因子，**不是自动得到正确米制尺度**；与给定相机的标定相容性必须检查。改变梯度实现、anchor 或尺度目标都需新版本、同输入/预算对照；不用评分 GT 拟合锚点。

可证伪预测只有两条：A）未改 helper 的原 depth 梯度链应断开；B）满足无旧 depth、同中心、固定内参和固定权的人工/可行参数族应有 `Lα=αL1`。任一前提不满足，不能借本理论宣布 collapse。若普通梯度修正/尺度锚定已解决问题，应按工程控制结束，不立“新尺度方法”。

人工检查完整量、源码身份与实际时间见 `artificial_checks.json`；它的 PASS 只指上述小型代数与 helper 检查。

## 与同伴源审稿的措辞核对

本稿完成独立推导后，已全文读取 `work/S27_scale_diagnosis_source/audit.md`。两稿关于 pair scale 非固定、欧氏目标、共同中心恒等式、短非零基线不必收缩，以及 old-depth 破坏共同缩放的结论一致。该稿另外检查的相机归一化路由和 MST Sim(3) 初始化属于其源审范围，本审未独立重做所有 pipeline/navigation 调用链，不能把它们记成本文新复核。

需要更正的表述是该稿第2节“common4中全部depth可优化”“新4继续优化”，以及第3节“新depth可优化”：应写成**原参数的 requires_grad 标记为真，但实际 `ParameterStack` 断开原深度参数的梯度链；初始化仍可直接写新 depth**。仅把它们用作可行参数族的描述可以，不能理解成当前 Adam 已在优化这些原参数。此问题已发给 root，由原作者维护该稿，本审不修改同伴文件。

没有为重复核验继续开额外实验。曾发出一个源码 sanity 子任务，root 指出其与其他检查重复后已立即中止；没有收到可采纳的完成结论，本报告不使用或计入它的结果。下一项真实 common4 保存头的零优化 MST/一次 backward 由 root 另行安排，本审不执行。
