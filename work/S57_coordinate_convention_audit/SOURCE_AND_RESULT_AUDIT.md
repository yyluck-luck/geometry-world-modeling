# S57坐标约定审计：反向信号来自观察器漏掉轴转换

**结论：确认一处观察器坐标约定错误，不能把原“与请求不一致”标签当作生成基线缺陷。** 冻结生成源码在构造射线前翻转相机的y、z两列；S57直接对转换前的归档旋转使用OpenCV针孔公式，漏了这一步。对当前纯yaw，这正好反转预期光流。按源码修正后，只用全部保存对应点复算：B0为13对名义请求一致、1对不确定、1对零运动端点；C1为14对不确定、1对端点。**这是结果暴露后的保存数据重算及观察器勘误，不是基线变好、新推理或算法收益。**

## 精确源码链与公式

本次独立重算三个源文件SHA，分别与B0及C1实际生成manifest绑定的SHA完全相同：

| 源码与行号 | SHA256 | 核实的语义 |
|---|---|---|
| [pipeline.py:1124](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_environment/isolated_vmem_source/modeling/pipeline.py:1124>)，关键1129–1139 | `680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255` | `all_c2ws[:, :, [1, 2]] *= -1`先执行，随后取逆并传给`get_plucker_coordinates`。 |
| [util.py:65](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_environment/isolated_vmem_source/utils/util.py:65>)，65–99、154–176 | `30a97451f7a895e99ab881e97249f564e6b97eca2b5ea4d8f83953c26c4cf65e` | 图像网格是index+0.5，X向右、Y向下；`K^-1[u,v,1]`的z为正。相对w2c再取逆产生射线；归一化和`center×ray`不反转方向。 |
| [navigation.py:217](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_environment/isolated_vmem_source/navigation.py:217>)，217–221、250–307 | `6d267365d5dcccf9f7cd6d535f19f80521f60a9634dffb35b9af398407389fcf` | 前进沿负local z；正yaw命名为左转，采用Y向上的旋转。这与归档相机采用OpenGL式基轴相符。 |

令归档相机旋转为`R_i`，`D=diag(1,-1,-1)`，消费器实际旋转为`R_i D`。D同时翻两轴，行列式为+1，**不是左右手性的反射翻转**。因此从图i到图j的同一空间射线对应关系应为：

`H_ij = K_j (R_j D)^-1 (R_i D) K_i^-1 = K_j D R_j^-1 R_i D K_i^-1`。

原[observer.py:45](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S57_camera_observer_calibration/observer.py:45>)使用`K_j R_j^-1 R_i K_i^-1`。纯yaw满足`D R_y(θ) D = R_y(-θ)`，故这是有明确源码依据的符号修正，不是尝试正负两种结果后选较好者。K保持原576分辨率、中心287.5、焦距约565.232的index坐标换算；半像素修正本身没有解释几十像素的反向残差。

**历史与目标都转换。** pipeline的1264行把`context_c2ws`和`target_c2ws`拼成新tensor，再于1268调用get_cond，1129对全部相机执行D。1298行归档的是原`target_c2ws`，不是已转换的拼接tensor。构造Plücker时相对第一张上下文相机的坐标归一化不会消除D：它在任意两相机间仍留下上述两侧D。另一个`get_transformed_c2ws`在950–955行也作相同列转换。

训练语义边界：本机固定发行源码的主要生成入口与上述转换一致，`get_value_dict`（util.py:207–244）另提供从传入c2w生成正z射线的通用路径，但它不是本次生成调用链。本次两个本地VMem副本的非extern文件清单未找到训练器/训练数据预处理；故**不能宣称逐项核过checkpoint训练输入约定**。负z约定位于Navigator和进入射线函数前的转换，不能把它错归为`get_plucker_coordinates`内部使用负z。

## 全部30对的原样对应点复算

实际运行UTC：2026-09-08T16:47:58.841490–16:47:58.922771；耗时0.081096秒，NumPy1.26.4。只读取JSON中9350对已保存对应点，没有新特征匹配、RANSAC拟合、像素读取、模型加载或C2访问。全部30对、格子覆盖、拟合一致性及六项阈值均保留。独立线性求解路径重算原主残差，最大差为0；输入及源文件执行前后SHA相同。

| 行 | 修正后标签，分母固定15 | 例子：原请求残差→源码转换后残差 |
|---|---|---|
| B0 | 13 `CONSISTENT_WITH_CORRECTED_NOMINAL_REQUEST`；1 `UNKNOWN_AMBIGUOUS`（0→5）；1端点 | 0→4：106.290180→1.545357px；0→5：79.368579→1.730016px，仍不确定。 |
| C1 | 13原覆盖/匹配不确定原样保留；0→1变为`UNKNOWN_AMBIGUOUS`；1端点 | 0→1：22.726366→4.087413px；0→4：99.068799→4.970132px，覆盖不合格，不能升级解释。 |

两个0→8端点的相机请求都是单位映射，残差完全不变：B0为0.7257969674647461px，C1为0.6569644494410187px。原观察器结果和控制均未改写；全部逐点残差与阈值见[保存对应点重算](ALL_30_SOURCE_D_CORRECTION.json)，实现见[独立脚本](recompute_saved_matches.py)。

## 当前能排除什么，仍不能说明什么

原B0的大幅“反向请求残差”可由漏掉D解释，应撤回由此推导的相机服从失败说法。13对只是原单纹理控制阈值下、匹配支持区域内的名义投影一致；不等于物理标定相机、全场景三维正确或长时记忆有效。

C1仍可能受匹配分布、纹理缺失、真实图与生成图的外观变化、模型默认K与真实照片不符、生成变形或局部运动不足影响；此处没有足够证据区分。不能把13个UNKNOWN删掉，也不能把局部流幅度估计当成相机真值。校准与验证使用同一纹理的局限仍在，修公式没有补出独立校准集。

本审计没有改变S42阈值、ROI、分母或原B0/C1主MSE；C2仍独立接续。低RGB误差和正确运动方向均未识别某条历史来源的因果作用，更未识别其收益。保持`NO_METHOD_SELECTED`、`new_method_validated=false`、`novelty_authorization=NONE`。本次应用本地科学批判技能的竞争解释与构念效度检查；根任务负责记录主账及发布勘误。
