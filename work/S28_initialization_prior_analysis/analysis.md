# S28 初始化尺度：源码结论、近邻与最小强对照

记录时间见 `completion_receipt.json`。本轮只读取已完成的 `work/S27M_independent_result_review/alignment_description.json`、相关源码和公开原文；没有读取真实 NPZ/传感器深度，没有模型、MST、GA、评分或数值重拟合。以下“已知观测”来自该 JSON，不冒充本轮独立数值复现。

## 1. 先纠正因果解释

**同步变换点图和预测相机后，再转回预测相机坐标，公共旋转和平移代数相消，尺度保留。因此约130°的朝向不一致不能直接解释深度缩小。**

已记录的共同旧4帧初始化 Sim(3) 尺度为 `0.1731799840927124`，变换后相机中心对给定中心的 RMSE 为 `0.002127957198480677 m`。JSON 中约129.75–130.69°是“mapped predicted orientation 与 given orientation”的逐帧差；它不是直接报告公共R的旋转角。小中心误差也不代表相机完整朝向或深度正确。

### 源码顺序及定理

实际文件为本项目冻结的 VMem 内嵌 CUT3R `cloud_opt/dust3r_opt/init_im_poses.py`，并非假定当前网络仓库主分支等于已运行版本。

1. `minimum_spanning_tree` 先用原实际消费的 anchor-self / other 点图建立点图集合；未给出的相机通过 `fast_pnp` 求出。这里的预测相机是 **MST/PnP 初始化相机**，不是未被该消费者采用的原网络 `camera_pose` 七维头。
2. `init_from_pts3d` 对多个已知相机调用 `align_multiple_poses`；同时以同一个 `trf` 变换所有点图和初始化相机，再把相机旋转块除以s。
3. 求depth时使用局部变量 `im_poses[i]`（同步变换后的预测相机）：`geotrf(inv(cam2world), pts3d[i])[...,2]`。
4. 之后 `_set_pose(self.im_poses,i,cam2world)` 对已固定相机不写入，因为其 `requires_grad=False` 且没有 `force=True`。实际优化场景仍使用给定相机。共同旧4深度可被初始化写入；已有旧depth被固定的8帧分支需分开，不套用“所有8帧重写”的说法。

令变换前的点为P、预测相机为 `(Q_i,c_i)`。公共相似变换为 `(s,R,t)`，s>0。源码得到：

\[
P'=sRP+t,\quad Q_i'=RQ_i,\quad c_i'=sRc_i+t.
\]

精确算术下：

\[
(Q_i')^{-1}(P'-c_i')
=(RQ_i)^{-1}sR(P-c_i)
=sQ_i^{-1}(P-c_i).
\]

所以 `z_after = s × z_before`。若随后有共同尺度归一因子h，则为 `h s × z_before`；本地 `preset_pose` 令 `norm_pw_scale=False`，`get_pw_norm_scale_factor()` 返回1。公式用逆矩阵表达，不依赖把稍有浮点误差的R当作严格正交矩阵；真实浮点乘法/逆矩阵/存储仍不保证逐字节相等。本轮没有做全像素验证。

**可以说：** 给定该源码路径，0.173的公共尺度会乘到初始化局部depth上，R/t不会独立改变该局部z。**不可以说：** 130°导致0.173，或纠正R就一定恢复深度。若只替换R而保留同s并同步变换点图/预测相机，理想depth完全不变。

还有一个不同的问题：保存的depth按mapped predicted camera取z，之后世界点却按固定given camera解释。相机朝向/中心不一致可能影响重投影与pair残差，但这属于坐标/模型一致性，不能和上述标量缩放混成一个因果结论。仅换成 `given^{-1}P'` 取z也不是安全修复：可能产生负z或离开原像素光线；需要独立完整实验。

## 2. 已知旋转不等于已知尺度

本地 `align_multiple_poses` 为每个相机加入中心c和一个 `c + epsilon * z_axis` 端点，`epsilon=max(median_pairwise_center_distance/100,1e-6)`。源与目标各自计算epsilon。随后RoMa拟合自由s/R/t。因此这是以人工长度的短z轴端点弱引入朝向，**不是严格使用完整给定旋转**；它没有用相机x/y轴，也不能只由该端点单独确定绕z轴的roll。忽略floor时，端点长度约baseline的1/100，相应平方项有小量级，不能据此断言本次目标中各项实际占比。

对最简单的orientation-constrained Sim(3)对照，可先仅利用完整朝向得到公共旋转，再固定它求尺度/平移：

\[
R_* = \operatorname{Proj}_{SO(3)}\bigl(\sum_i w_i G_i Q_i^T\bigr),\quad
x_i=c_i-\bar c,\ y_i=g_i-\bar g,
\]
\[
D=\sum_iw_i\|x_i\|^2,\quad b=\sum_iw_i(R_*x_i)^Ty_i,\quad
s_*=b/D,\quad t_*=\bar g-s_*R_*\bar c.
\]

这是旋转的chordal平均加固定R后的普通一维最小二乘，不是新算法。若各姿态没有同一个一致的公共R，第一步仅是折中；不宣称所有姿态被精确满足。D=0时中心信息不能确定尺度；b/D<=0时没有该公式下的正尺度内部解，应报告不兼容/退化，不临时夹到某个“好看”的值。

在源中心固定的条件下，目标中心扰动给出：

\[
|\delta s|\leq\frac{\sqrt{\sum_i w_i\|\delta y_i\|^2}}{\sqrt D}.
\]

这说明中心跨度相对噪声小时尺度估计可能敏感；并未根据四帧数据估计噪声或条件数。即使旋转完全已知，纯旋转/共中心也不产生长度信息。已知米制平移在非退化且预测可靠时能约束尺度，但毫米级运动不保证它压过预测误差。`epsilon`的数值floor提供的是算法约定，不是物理尺度观测。

## 3. 五项最接近的原论文/官方实现

本轮是有界近邻检查，不是全领域系统综述或“已找到2026最强方法”的证明。已查关键词覆盖：known camera poses/global alignment/scale；metric depth priors；orientation-constrained similarity registration。只依赖原论文与作者官方实现；未将搜索摘要中的方法或性能数字当证据。

| 原工作与核验范围 | 与当前问题的关系 | 本项目可借用的最简单对照及差别 |
|---|---|---|
| **DUSt3R**，Shuzhe Wang、Vincent Leroy、Yohann Cabon、Boris Chidlovskii、Jerome Revaud，CVPR 2024。读§3.2–3.4及官方初始化实现。 | 原pointmap GA已包含相似变换；论文为避免零尺度解对edge尺度乘积施加约束。已知pose初始化与本地路径有直接源码亲缘，但不能把原论文所有设置等同VMem修改版。 | 原目标/初始化应作强基线；“归一化尺度以免坍缩”本身已有。当前对象是米制CUT头与给定相机的初始化接口。 [原文](https://arxiv.org/html/2312.14132v3#S3.S4) · [官方源码](https://github.com/naver/dust3r/blob/main/dust3r/cloud_opt/init_im_poses.py) |
| **CUT3R / Continuous 3D Perception Model with Persistent State**，Qianqian Wang、Yifei Zhang、Aleksander Holynski、Alexei A. Efros、Angjoo Kanazawa，CVPR 2025。读§3.1与§3.3。 | self/world/pose为各自监督的输出，论文明确名义米尺度；不能把self/world严格等同，也不能像任意尺度DUSt3R一样默认抹掉其米制先验。 | 原metric self-depth直通是不可省略的简单对照；它利用原消费者未逐帧消费的self头，必须披露这个输入差别。 [原文](https://arxiv.org/html/2501.12387v1#S3) · [官方实现](https://github.com/CUT3R/CUT3R) |
| **RoMa 官方3D旋转/配准库**，NAVER维护；这里核官方算法文档，不冒称新近重建论文。读weighted rotation averaging、rigid registration、special_procrustes。 | 明确实现chordal旋转平均与Kabsch/Umeyama点配准，支持尺度可选；文档指向Umeyama 1991，但本轮未通读1991原论文。 | 用完整相机旋转先求R、再解s/t是经典工具组合，强对照而非创新；不需训练/新权重。 [官方文档](https://naver.github.io/roma/#weighted-rotation-averaging) · [配准API](https://naver.github.io/roma/#roma.rigid_points_registration) |
| **Pow3R**，Wonbong Jang、Philippe Weinzaepfel、Vincent Leroy、Lourdes Agapito、Jerome Revaud，CVPR 2025。读§3/§3.1与官方README。 | 已将K、相对pose、稀疏/稠密depth作为网络条件；self/other额外头也已有。其论文该版本使用scale-invariant回归，不能拿“支持depth prior”自动等同保留本项目的米单位。 | 排除“把已知相机或深度喂回去”这种宽泛新颖性；它是学习式两图条件模型，本项目最便宜阶段是已有头的无训练初始化控制。 [原文](https://arxiv.org/html/2503.17316v1#S3) · [官方实现](https://github.com/naver/pow3r) |
| **MapAnything**，Nikhil Keetha等，3DV 2026（原arXiv 2025，读v3/2026-01-23）。读§3/§3.1及官方项目。 | 已把旋转/平移输入分离，并显式编码depth/pose metric scale；输出ray depth、rays、poses与全局metric scale。 | 解耦姿态、形状、尺度不是空白。潜在后续需证明原消费者在可观测/不可观测区间如何可靠使用已有米制头，而非再搭一个泛化先验编码器。注意其ray depth不同本项目轴向z。 [原文](https://arxiv.org/html/2509.13414v3#S3) · [官方项目](https://map-anything.github.io/) |

## 4. 优先的简单强对照（全部尚未运行）

先用common原4帧定位；不要同时重做三路8帧、改学习率和冻结策略。所有控制都继续隔离sensor-depth答案，不使用已见GT比例挑初始化或正则强度，不按误差删帧。给定相机是原有共同输入，新的self头访问则单独披露。

| 对照 | 精确变化与允许输入 | 最便宜的判别及不能声称的东西 |
|---|---|---|
| **C1 完整朝向约束的Sim(3)** | 使用同一保存MST/PnP相机Q/c和原given G/g；完整旋转平均得到R后，只按中心解正s/t；其他初始化流程保留。不要把网络raw pose替换成MST pose而不说明。 | 先在新合同中做小型解析对照，完整报方向/中心残差、s和退化状态。若R改善而s仍小，否决“修正旋转即恢复深度”。旋转不能凭空给出米尺度；没有本次胜负预测。 |
| **C2 米制尺度固定对照** | 分清两种不等价操作：C2a仅把公共初始化s固定为1，保留相同MST局部点图/相机和原消费头；C2b直接采用每帧原raw-self z，不作GT拟合。C2b可作为固定深度消费者基线，但不是原输入不变。 | C2a隔离公共尺度乘法，理想下保留pre-Sim3局部z；C2b是强的metric depth passthrough，S27已给其直接深度评分，不值得仅为重复该表再跑。要测其进入消费者后的行为，需另立matched合同。固定尺度未必改善不准确的pointmap形状或射线。 |
| **C3 普通先验正则** | 最小版只对标量s加入朝s=1的普通先验，例 `J = sum w||s R x-y||² / D + lambda*(s-1)²`，D>0，R固定且不看sensor。 | lambda=0是C1、lambda→∞是固定s=1；最简单lambda=1仅作事先固定的等权对照，非最优理论值；闭式 `s=(b/D+lambda)/(1+lambda)`，非正值明确失败。D=0时数据不可辨识，s=1只来自先验。不要按本8帧GT调lambda；也不要把普通正则包装创新。 |

后续若改成逐像素 `log-depth` prior 或修复ParameterStack梯度通路，属于不同干预。必须先验证梯度确实通到实际参数，并分别保留“源码修复”“初始化控制”“先验”的效果；只添加损失项但原depth无梯度不能叫有效深度优化。这一轮未读新的梯度结果文件，执行证据由根任务/负责agent维护。

## 5. 尚未测的预测和创新边界

- **源码可证伪预测**：固定s与同步变换规则时仅改变公共R/t，初始化z应在数值精度内不变；如不符，应先查路径/参数是否改变。不是对传感器准确率的预测。
- **待数据判别**：强制完整方向一致是否改变正尺度解、原米制先验是否优于中心拟合、普通lambda=1先验是否已经足够；本轮均无数据结果。
- **公平比较要求**：C2b额外利用self头，区别于C1/C2a的同消费头；所有方法如使用新common旧depth，在后续8帧比较时都必须共享同一新common条件，不能与原S26B不同旧图直接归因给方法。原结果全部保留。
- **必要失败情形**：pure-rotation/共中心无平移尺度观测；错误米制预测会使s=1先验有偏；MST/PnP相机不满足单一全局刚体关系会使方向约束折中；self/other冲突与focal错误可能使修尺度后仍无法一致对齐。
- 按idea-evaluator，当前仅使用F1近邻排重与F6可验证性检查；这不是完整论文idea评分。简单约束R、固定s、加prior均不支持新方法新颖性。要进入PhD/CCF A目标，需要这些强对照后仍有可重复的实质问题及新机制证据；本轮不作“已经创新”的结论。

## 文件和阅读范围

`source_read_manifest.json`列实际读过的章节/函数、当前版本与本地快照状态；`source_fetch_receipt.json`保留公开文本下载的真实成功/失败。部分HTML本地归档遇TLS EOF，但对应原文已由web工具打开并阅读；不把保存全文当成全文通读，不隐藏下载失败。这里没有改项目docs、主账、已冻结脚本或历史结果。
