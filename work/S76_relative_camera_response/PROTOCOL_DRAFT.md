# S76：固定图像网格噪声的目标相机相对响应 pilot（源码草案，未运行）

核心问题：已有S70 A0绝对取景明显偏离请求；保持其历史、相机中心和实际随机流，只把四个目标视角各自本地yaw转+5°，生成器的输出变化是否更接近这个预先确定的几何方向，而非完全不动？本轮是固定一次随机实现下的全系统相机干预诊断，不是完整相机精度、真实场景重建、统计确认或创新方法。

## 实际源审可行性

S70 root已接受生成与评分，A0/A1 latent/raw RGB/uint8精确重放；回执包含完整pre-do_sample RNG文件、实际初始noise SHA、50步前后RNG SHA、terminal SHA和model value/modes SHA。因此可以**优先复用旧A0，仅生成一个新yaw臂**。这些状态本批只作为元数据读取，实际state/noise字节恢复仍须未来运行核验；不能以相同seed代替它。

`SOURCE_BOUNDARIES.json`保存本批实际读取源/回执的SHA，以及旧资产元数据pins。`pilot_rules.py`给出无I/O、无模型的旋转、H、FOV、恢复RNG及同匹配评分函数；它故意没有实验入口。仅编译检查，不读取科学数组或运行几何计算。本轮尚不能直接启动生成。

最小实现复用S70 worker的 `load_code`、`read_conditions`（manifest只保留geometry）、`load_models`、`model_snapshot`、`rng_capture/rng_json/rng_sha`、`save_array`等已审函数，**不调用其三臂run**。动态载入该模块时验证源码SHA，不能改写原文件。复用S69原AST提取器只取原相机helpers和Consumer两个方法，不导入完整pipeline/CLIP/CUT3R。需要新写一段只运行yaw臂的连接代码和有限评分入口，避免再搭通用平台。

## 唯一干预与全部下游重算

固定S70 geometry槽序 `[19,18,13,12,20,21,22,23]`。从S69保存的 `optical_c2ws_fp32` 出发，历史四槽完整不变，所有八相机中心、K、mask、历史latent/embedding不变。四个目标旋转矩阵右乘同一

`Q = [[cos(5°),0,sin(5°)],[0,1,0],[-sin(5°),0,cos(5°)]]`。

这是绕各自本地光学+y轴（图像向下）的右手正旋转；旧正前方物体预测向新画面的左侧移动。角度与符号此刻固定，不能结果后反向、换角度或选择其中一个目标。

重走S69路径：`consumer_raw = new_optical @ diag(1,-1,-1,1)`，原 `get_translation_scaling_factor`，原 `get_cond`；不能向已经翻轴/缩放的post_cond再重复翻/缩放。中心不变使自然scale/centering应与旧一致，运行时核全部平移、history相机和appearance条件字节相等。原c/uc crossattn与replace保持完整相同；concat mask通道不变；所有c/uc射线按新相机重算。完整返回的 `all_c2ws/all_Ks/input_masks`进入原MultiviewCFG。

S70原guidance也读取相机，四个目标也在同一视频中耦合。因此这是**一次四目标联合的全系统相机干预**，不能称只测ray injection或各目标独立因果效应。几何后代不能为了“公平”冻结。

## RNG与模型可比性

保持S70相同六原源、权重、版本/backend、CPU8 FP32、eval、sampler0 MultiviewCFG、50步、cfg2/cfg_min1.2、T8/576²、原full8 decode/chunk1和原tensor_to_pil分支/截断规则。不能用S75的新固定PNG量化方式替代S70路径。

模型构造和新条件/采样器准备完成后，读取并核common_rng.json原文件SHA，再递归将Python序列恢复tuple、NumPy keys恢复uint32、Torch state恢复CPU uint8；核canonical SHA后**紧邻原do_sample前**恢复。恢复后不要新增随机操作。

新臂要检查实际noise body SHA、sampler-entry SHA、全部50步rng_before/rng_after和terminal SHA均与A0相同；原sampler_step即使churn0也有randn_like路径，保留它。旧epsilon字节未存，因此只能主张固定原调用路径和状态流对应，不能说已逐字节比对所有epsilon。跨进程比较旧model value/modes SHA；对象ID/data pointer只在新进程前后自检，不能和旧地址比较。

图像网格的原始噪声保持原位置，**不warp、不输运、不插值**。这固定了外生噪声的一次实现；不是几何附着的噪声实验，更没有“同noise应满足精确H等变”的定理。EquiVDM反证边界及其他创新检索原文由专职检索agent单独记录，不能用本pilot给出违背其噪声条件的定理式结论。

任一实际流/权重/运行路径身份不符，就保留新臂并标记不可与旧A0作该固定流比较；不立即自动重跑A0、重抽seed或调角度。若实际证据显示必须用新运行路径，再另冻一对fresh baseline/yaw，保留本次失败，不以结果好坏决定重试。

## 预定H、共同视场与同匹配对照

对四个目标逐一用同K、同中心与实际进入消费者的old/new旋转（FP32转FP64）计算：

`H_old_to_new = K @ R_new.T @ R_old @ inv(K)`。

这是纯旋转的预定理想针孔几何，不拟合F/H、不读新生成图校正方向/尺度、不依赖深度。FP32旋转近似正交误差保留，不做结果后正交化。默认投影只接受齐次z>1e−12且有限的点。

在新生成图片产生前，按全部576×576整数像素中心构造old→new及new→old共同视场mask，并记录两个方向的像素数/总像素数、H和逆H。边界是坐标[0,575]。这只是预定可见视场，不保证无遮挡、外观一致或产生正确对象对应。

使用旧A0和新yaw各目标的原S70量化图，固定SIFT1500、3layers/.04/10/1.6、BF L2双向k2、ratio<.75和互惠ID；不RANSAC、不配准或按残差过滤。保存所有四目标、所有源/目标feature数量、互惠匹配ID/xy、匹配缺失分母与覆盖。

每个相同接受匹配 `(x_A,y_yaw)` 同时计算identity残差 `||y-x||`、H残差 `||y-project(H,x)||` 和paired差值 `identity-H`。**同一批点**用于二者，不分别挑inlier。报告全部有限投影匹配的q25/50/75/95/max、符号计数；另完整报告共同视场子集：x与y都在图内、H(x)与H^-1(y)也在各自图内。所有不足、behind-camera、非finite、共同FOV之外计数保留，null不能补0。共同子集由预定H和已观察匹配条件化，不是独立真值样本。

逐目标检查paired差的median是否>0，仅描述预定方向是否更符合输出对应关系。全部四目标的数值/失败并列，不汇总掩盖某个失败；未见图片和对应点本批没有读取。无需额外挑阈值。match availability与共同FOV覆盖可能限制方向判读，成功仍不能说明绝对camera正确、图像真实或新方法成立。

## 当前开放实现项

1. 编写单yaw臂runner：绑定S70旧接受链、S69数组；原get_cond重算与外生/不受干预字段守卫；恢复实际旧common RNG并逐步核身份。
2. 编写保存条件/H/FOV的结果前阶段、单臂actual生成和保存后固定SIFT评分；生成和评分分开，先封存新输出。
3. 按S70有界观察器窄改为1臂；建议保留单臂1800秒+合理加载预算、RSS45GiB、≥10GiB磁盘，具体总上限在最终runner冻结时确认。不要误复用S75的180秒短预算。持续监测、保留部分产物，无自动retry。
4. 对最终runner/scorer进行不同作者源审并冻结SHA；实际执行后独立复算H、保存坐标与匹配统计。源码草案compile PASS不代表这四项已完成。

这些是可由团队继续完成的实现事项，无需新增用户授权；未请求用户批准、没有提出购买/远程资源依赖。本步不编辑主账、旧源码或旧结果。
