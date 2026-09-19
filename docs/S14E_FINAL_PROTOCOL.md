# S14E：已知相机条件下的真实深度诊断协议

状态：运行前整合稿，待独立前审和最终身份冻结。此次尚未因撰写本协议读取真实数组或运行模型。最终执行以冻结manifest中的本文件SHA为准。

## 问题与范围

在同一段20张真实历史照片和给定目标相机条件下，CUT3R不读取目标照片的深度预测，能否比普通历史点云重投影及历史常数距离提供更有用的几何？本轮只测已有TUM fr2_desk、S8 block0的4个相关且已见目标，是组件的探索性质量诊断，不是新算法、独立新场景、论文SOTA比较或视频结果。

即使模型获胜，也只能支持进一步研究；模型未胜时保留全部结果，不改主指标或对齐方法挽救。工程正确性通过与质量高低分别判断。S14C已反驳的粗历史分散设想保持停止，不重新调权包装。

## 已知输入与答案隔离

- 固定 `results/S8_cut3r_cpu_v2/frozen_inputs.json` 的block0：frame0..19为history，frame20..23为四目标，全部顺序保留。
- history相机在对应RGB时间插值；目标相机在各自配对深度PNG的时间插值。给定TUM轨迹与标定是三方法共同允许的条件，应明确标注GT pose input，不能声称所有GT均未使用。
- 轨迹位置线性插值，归一四元数最短SLERP；不外推，最大邻接时间差0.1秒。保存插值上下时间和alpha。
- 新模型阶段恢复S14D状态，无history RGB重读。基线只解码旧S8 NPZ的0..19历史self点图和camera_c2w；逐键白名单，禁止先把全NPZ解码再丢弃query。S14D两历史pose字段仅按准备脚本明确白名单使用。
- 四个目标RGB不参与预测/评分数值。四个深度PNG在预测、基线和参数封存后由独立评分进程打开；代码/文件身份可先做字节SHA检查，字节读取与数组解码分开计数。

## 坐标、尺度与标定

以预测history c2w为(R_i,p_i)，已知米制history c2w为(G_i,g_i)，固定float64公式：

```text
A = R_0 @ G_0.T
u_i = A @ (g_i - g_0)
v_i = p_i - p_0
D = sum_i dot(u_i, u_i)
N = sum_i dot(u_i, v_i)
s = N / D                 # 模型单位/米
c = p_0 - s * A @ g_0
R_query = A @ G_query
t_query = s * A @ g_query + c
depth_m = self_z_model / s
```

D≤1e-12 m²、s非有限或s≤0时停止并保存失败；不取绝对值、不截断、不换成反向OLS、不逐query拟合、不使用目标深度定尺度。首相机方向固定，历史平移全部参与。旧审计中的反向回归未采用，以 `work/S14E_calibration_audit/scale_definition_clarification.md` 为勘误依据。

R含旧FP32预测误差，禁止悄悄SVD修正。旋转检查atol=1e-5；来回变换检查atol=1e-5、rtol=1e-5，单位与对应坐标一致。独立数值复算默认atol=1e-6、rtol=1e-5；数组schema、状态身份、缓存pose和Q0 parity按字节精确核对。原始误差与残差照实报告，不因真实结果不好更换这些值。

按TUM官方已配准数据建议使用ROS默认K=(525,525,319.5,239.5)。640×480先resize299×224、crop[37,0,261,224]；像素中心映射固定得到：

```text
K = [[245.2734375, 0, 112],
     [0, 245, 111.5],
     [0, 0, 1]]
```

深度uint16/5000转米，fr2修正系数已应用，不重复乘1.031。GT使用nearest resize/crop，无额外畸变校正、插值补洞、距离裁切或平滑内区。来源：[TUM文件格式与标定](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats)，细节与人工坐标核查见S14E坐标审计。

## 模型预测与普通基线

模型固定已有224 linear CUT3R、原commit/权重、CPU8线程、seed0、已有精度和signed RoPE兼容。官方ray编码按训练/接口原样：origin=t，direction=normalize(R K^-1 pixel+t)；它是模型条件编码，不能当成物理纯方向用于基线反投影。

恢复S14D五字段state后，先用旧Q0 **zero**占位/旧ray/旧pseudo K，验证本轮call0六输出与旧 **query_call_1.npz** byte一致；通过才依序调用四个新条件，即本轮call1..4。全部zero占位，img_mask=false、ray_mask=true、update=false、reset=false；图像encoder实际处理0，ray encoder共5次；状态始终不变。此处统一旧设计草案第5节的NaN/call0表述，旧草案保留，最终以zero/call1为准。

每call返回就保存全部六head。主深度固定self z/s；不得看到答案后改用other或置信过滤。RGB head输出是模型tensor，不等于真实目标图或完整视频。外部caller限制600秒、监测RSS32GiB，记录实际时间/内存与退出状态。

基线B1用20history全部正且有限self-z及保存的预测history pose，标准pinhole反投影到模型世界，再投影到共享的目标相机。最近像素floor(u+0.5), floor(v+0.5)，z-buffer保留最小正z；同z来源tie取history/raster索引小者。无点为NaN，不补洞。每个history不得用GT位姿单独纠正，已知history轨迹只用于上述同一全局对齐。

基线B2是20history全部正有限self-z的一个全局像素中位数/s，四图全像素同值；无有效history时停止。采用通常偶数中位数，不读目标答案。三方法信息条件有共同来源，但运算路线不同，不声称成本相同。没有四图选择/NMS，不混同S12实验。

## 固定评分与复核

GT valid为裁剪后finite且>0的全部像素。主δ1=预测正且有限且max(pred/GT,GT/pred)<1.25的像素数/全部GT有效数；无预测也计失败，空GT域记null。

逐query三方法全部列出：GT有效数、预测覆盖率、主δ1、各自有效交集的MAE/AbsRel/RMSE；另给三方法共同有效域像素数和相同误差，避免稀疏方法只在容易像素评分。主率给两个基线差值及等query均值；不将4个相关query或几十万像素当独立试验，不报告显著性或拟合调参。

prepare与score各自静态manifest在真实执行前固定，模型manifest在condition封存后绑定。根在模型与基线完成后生成 `s14e-combined-prediction-seal-v1`，包含 `sealed_utc` 和所有实际产物绝对path→SHA；评分命令传入seal SHA。评分须核全部身份、完成状态和时间顺序后才首次打开目标深度。

不同作者前审恢复/parity、读取域、投影、尺度、缺失分母及人工边界；根或独立agent用保存数据和不同归约公式复算尺度、zbuffer、射线与评分，不重跑模型。独立核验器使用SciPy SLERP、fsum、scatter最小归约、整数nearest映射；标量评分预定atol=1e-10/rtol=1e-10，所有计数/掩码/来源保持精确。连续投影先用分量公式核至既定容差，离散像素量化保持生产的明确FP64运算次序，再以不同scatter归约复查：人工半像素反例表明等价代数重排也可能改变round边界，不能放宽离散掩码门。δ1使用同一浮点除法定义，不能改乘法不等式后要求掩码逐位相同。所有失败与修正追加记录。脚本读取追踪不是操作系统级任意文件隔离证明。

## 实际技能应用

Supervisor idea-evaluator：应用F1最近工作与F6可验证性早门。官方CUT3R项目已展示虚拟视角query能力，本轮没有自创方法，不虚构创新五维评分。最近工作见S14D_TARGET_VIEW_NEAREST_METHODS.md及[官方项目](https://cut3r.github.io/)。

Supervisor vibe-research-workflow：编码阶段明确输入输出、拆分准备/预测/评分、保留修正与交接；不将用户私下阅读或逐句确认写成已完成。本地Claude scientific-critical-thinking：构念效度、答案隔离、缺失偏差、探索标签与结论强度。方案图沿用已有可编辑Mermaid，实验图使用实际数组与标准绘图库。
