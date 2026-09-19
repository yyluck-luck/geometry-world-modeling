# S14E 尺度定义勘误：以最终设计的模型单位/米为准

本勘误只澄清**尚未执行的 S14E 主对齐协议**。原审计报告及 receipt 保持字节不变；原公式作为未采用候选保留。此次未读取真实RGB、深度、轨迹、NPZ，未运行模型。

## 错误在哪里

我在前版审计第4节将“首历史相机方向锚定、20历史平移最小二乘”具体化为**模型预测位移作自变量、米制位移作因变量**，并误写成根已确认的主策略。根与设计实际选择相反的回归方向：**米制GT位移作自变量、模型预测位移作因变量**。二者有噪声时不是互为倒数，不能仅改变量名、把乘法换成除法而声称同一拟合。

前版“尺度乘self_z”只与前版未采用的metric/model拟合自洽，**不适用于最终S14E主协议**。本勘误替代原审计中关于已采用OLS方向、目标坐标转换、深度乘除与主策略确认的表述；其余K、时间戳、官方编码/物理pinhole分离、输出head语义及GT隔离结论不变。原receipt中的root_confirmed_contract也按本勘误解释，不能作为最终尺度定义。

## 最终唯一主公式

用 G_i/C_i 表示第i个history RGB时刻GT c2w的旋转/平移，用 R_i/p_i 表示相同history的模型预测c2w。下式全部float64：

```text
A = R_0 @ G_0.T                        # metric-world → model-world rotation
a_i = A @ (C_i - C_0)
b_i = p_i - p_0
D = sum_i dot(a_i, a_i)                # 单位 m²，i=0..19
N = sum_i dot(a_i, b_i)
s_model_per_metric = N / D            # 模型单位 / 米
c = p_0 - s_model_per_metric * A @ C_0
X_model = s_model_per_metric * A @ X_metric + c

R_query_model = A @ G_query
t_query_model = s_model_per_metric * A @ C_query + c
query_depth_meters = self_z_model / s_model_per_metric
```

设计主门为 D≤1e−12 m²、s非有限或s≤0时阻断，不能abs、clip或换拟合；未用目标深度校准。求和虽在数学上可利用A正交性写成GT位移范数，生产和独立复算需按预定容差比较，不能假设FP64运算顺序逐位相同。

标准重投影仍为 X_history=z_i*K⁻¹p，X_model=R_i*X_history+p_i，X_query=R_query_model.T*(X_model−t_query_model)，得到光轴z后除以同一s。相机R保持正交，不把s塞进rotation。不得对每个target重新拟合s。

## 一个纯人工反例

固定A=I、原点锚定，两条GT位移为1、2米，模型位移为1、3模型单位。最终采用的OLS得到 s=(1*1+2*3)/(1²+2²)=7/5=1.4模型单位/米；其倒数是5/7。前版反向OLS却给(1*1+3*2)/(1²+3²)=7/10=0.7米/模型单位，并不等于5/7。两尺度乘积为0.98而非1。

该反例仅确认统计定义差别，不代表任何真实相机误差。后续独立前审必须核prepare中的N/D与predictor/score中的同一s单位，尤其不能把旧审计反向OLS与新score除法混接。

实际记录时间与原稿SHA见同目录scale_definition_clarification.json。根最终设计为docs/S14E_KNOWN_CAMERA_DESIGN_DRAFT.md第2、4、6节；本澄清以本次读取版本为依据，后续冻结仍需核最终源码与协议身份。
