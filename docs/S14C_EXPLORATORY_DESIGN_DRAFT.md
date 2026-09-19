# S14C探索草案：既定四图的预测分散差与支持差是否同向

状态：DRAFT_FOR_INDEPENDENT_PRE_RUN_REVIEW。作者 /root/s14c_operational_design。只批准设计准备；真实提取、标签联结须由根另行冻结最终源码、输入与本协议后执行。本文件不是新颖性裁定、未知数据预注册或效果结果。

## 1. 给新手的一句话

同一个查询已经有两套“四张照片”的选择。我们先只看模型自己预测的位置，计算哪套照片的预测更分散；全部计算封存以后，再看以前保存的真实支持评分，检查“更分散的一套是否往往支持更少”。这一步只找描述性联系，不学习新算法、不改选图，也不能证明分散导致错误。

这是STEM、New Setting中的普通应用诊断，范围比S14正式审查中的C2窄。它依赖每个query的既定选择而变化，**没有query目标像素、投影可见性、深度次序或遮挡定义**，因此名称必须是“已关联点、既定四图的预测分散”，不能写“目标视图联合冲突”“新高阶机制”或C2已实现。原C2要求仍保留在正式审查中，不因本诊断通过而解除。

## 2. 固定域和唯一主量

沿用S7/S8两场景各block0–2、query20–23，共24个已见且相关查询；A0P0、stride8、历史ID0–19。G为原来源14方案的最终四图，P为S12姿态14方案最终四图；各有14候选和4输出，沿用原NMS和ID。候选数相同不表示候选ID相同、输入信息相同或成本相同。两动作不重新计算。

对某块记忆点j，S14B给出每个历史来源帧f的质心c(j,f)与首写半径r(j)>0。这里只读质心，不把帧内多个像素当作多个来源。令F(j)为该点全部已存来源ID，k(j,S)=|F(j)∩S|。

两方共同域固定为 J(q)={j: k(j,G)≥2 且 k(j,P)≥2}。相同点域可避免直接把不同点群的平均值相减；但它是由预测关联与两套选择共同限定的条件子集，可能偏向重叠较多的区域，仍不能消除选择偏差。

当k(j,S)≥2时：

- e(j,S)= [Σ_{f<g, f,g∈F(j)∩S} ||c(j,f)−c(j,g)||²] / [choose(k(j,S),2) × r(j)²]。
- E(q,S)=Σ_{j∈J(q)} e(j,S) / |J(q)|。
- **唯一主scalar x(q)=E(q,G)−E(q,P)**。正值表示G在共同点域中的预测更分散。

先各点内pair等权，再点等权；不得按像素数、pair总数、来源票或query评分加权。每点k仅2–4。r是S14B原点首写半径，不用新平均半径、不加epsilon、不clip/winsorize/log变换。e无量纲。保存x、两端E和全部点级分量作为复核来源，但只x是主相关分析量。

e是普通pairwise平方距离平均，等于[2k/(k−1)]×该选中子集帧间方差/r²。此恒等式可作为不同公式的人工/独立核对，不是新信号。S14B全来源A、B、D不进入本分析：m=2的A=B、D=2B不提供三种独立特征。本阶段也不把x变成新路由或四图优化目标。

## 3. 缺测、覆盖和来源数报告

所有24query保留。J为空时，E_G/E_P/x与来源数基线记JSON null、CSV空值，status=NO_COMMON_MULTISOURCE_POINTS；不能填0或改为单方点域。相机基线仍可保存，但主要比较用同一可计算query集合。

每query必须报告n_map_points（块全部记忆点数）、n_G_multisource（kG≥2点数）、n_P_multisource、n_common、n_common/n_map_points、n_common/n_G_multisource和n_common/n_P_multisource，分母0时比例null；另保存全部kG,kP∈{0,1,2,3,4}的25格计数，其和等于n_map_points。它们用于呈现缺测和条件域，不是新增待挑选特征。保留J所有point_id和各自kG/kP、所用source ID/pair、eG/eP。

同一组选图必得x=0，不删除这些合法零；空J的同组选图仍遵守null。多个query出现相同选择、相同x时保留并报告重复数，不把它们宣称独立重复证据。共同域很小时如实列数量，不看到标签后新增最少点数门槛。

## 4. 普通基线与相同分析输入

预先固定三个基线，方向不能看到label后翻转：

| 名称 | 公式 | 正值的预设含义与局限 |
|---|---|---|
| b_source_count | mean_J [k(j,P)−k(j,G)] | G的历史来源更少；少来源可能信息不足，也可能仅少重叠，不保证更差 |
| b_query_distance | mean_{f∈G} d(f,q)−mean_{f∈P} d(f,q) | G到query更远；取两方共享的S12 full20_distances_float32 |
| b_camera_diversity | mean_{6 pairs∈P} d(f,g)−mean_{6 pairs∈G} d(f,g) | G相机分散更小；多样性也可伴随更大遮挡，因此方向只是预先假设 |

d沿用历史复合距离0.1×预测平移欧氏距离+旋转角，不能称米。内部六pair只用原trace被接受步骤已存距离，不从拒绝步骤补缺pair，不重算相机或平均姿态。查询相机源自已观察query RGB，不声称生成前仅轨迹时可部署。

x和三个基线都从同一份冻结预测侧输入档案、相同24query、相同G/P动作和同一标签定义计算；没有模型容量、训练/调参预算差异。它们各自读取不同字段，所以本轮是“不同普通观测量的描述性对照”，不是相同完整信息下的学习器比较。**不能因为x比某一单变量相关高就称新增独立信息**；未来若主张条件增益，需要让普通学习器取得相同质心/来源/相机信息，并在新独立场景上另冻协议。本轮不运行I3DM、MVS或COVRAG，不声称胜过它们。

## 5. 评分前32输入及标签文件

预测侧恰好32文件：

1. results/S14B_observation_disagreement/points.csv：字段白名单phase,block,stride,point_id,m,radius；允许解析完整CSV文本，但不把旧W/B/A/D列转为分析数值。
2. results/S14B_observation_disagreement/frame_centroids.csv：phase,block,stride,point_id,frame,n_obs,c_x,c_y,c_z；within_variance不作输入。
3. results/S7_event_replay/block{0,1,2}_stride8/prediction_only_selection.json，共3份。
4. results/S8_event_replay_v2/block{0,1,2}_stride8/prediction_only_selection.json，共3份。
5. results/S12_matched_budget/selections/{S7,S8}_block{0,1,2}_query{20,21,22,23}.json，共24份。

G的字段位置为 /queries/{query-20}/maps/A0P0/readouts/official 中selected/candidates及同级official_trace；P为对应S12 selection.trace.selected与pose14_ranked_candidates。语义须遵照scripts/extract_s14_prediction_features.py中的source/pose trace核对和selected_pairs字段规则；允许复用字段/验证定义，不重新运行S14A或打开其特征CSV/JSON。

标签侧唯一文件是results/S12_matched_budget/records.json，按writer scripts/run_s12_matched_budget.py:457–482静态确认，当前设计作者没有解码它。该文件含192旧配对条件；只消费 main_comparison==true 且 arm=="A0P0"、stride==8 的24行，精确键为(stage,block,query)，不能把192当独立样本。

G的历史整数/支持字段来自old_readouts.official.{selected,supported_pixels,valid_pixels,support}；P来自pose14同字段。两方valid_pixels须为相同正整数、num在[0,den]、保存support精确等于num/den，ID集合/原顺序和候选身份须与已封存预测侧记录完全相同。

**主标签y(q)=−geometry14_minus_pose14_pp，精确核对y=100×(P.support−G.support)**。正值表示G相对P损失支持，单位百分点。数学上等于100×(numP−numG)/den，但不能要求不同浮点运算顺序逐位相等，标签固定复用S12保存差值，不改原值。支持分母是原query valid像素，不能按J、选择方案、预测有效性缩减。y不裁为max(0,y)，不二值化，不设“受损阈值”。

实现必须先核所有32预测文件字节SHA，再从同一缓存解码和计算全部24行，保存prediction_rows.csv/json、point_components、全部来源和seal文件/SHA。完成seal并验证后，才首次读取/解码标签records.json；不为方便在同一提前JSON加载中暴露label。最终manifest事前绑定标签SHA可以仅字节hash，必须明确hash不等于未知研究者状态恢复。已知旧汇总及研究者见过数据决定本阶段始终探索性。

## 6. 单一描述性分析和可推翻预测

对x、b_source_count、b_query_distance、b_camera_diversity分别计算与同一y的**signed Spearman**，方向始终按上文。采用相等值平均秩、秩的Pearson相关，不调用自动p值报告；浮点相等即tie，不以容差合并不同值，不微扰破tie。

预定呈现层级：每场景12query各一组；每块4query各一组；全部24query总表只作已见域描述并提示混合场景可能逆转。每组分析使用x与三个基线均有限的相同query集合，明确n_total/n_common_valid、排除身份和原因。若有效n<3，或任何被分析变量/标签秩方差为0，该项rho=null并给原因；不人为填0。每组各变量使用相同可用query，但某变量constant只使其自身rho不可计算，不删除整组的其余项。

唯一方向性问题H：x越大，y是否往往越大？若任一可计算场景rho_x≤0，则“两个既有场景均呈正相关”的有限命题被本描述推翻；如为null则不可识别；如两场景均>0，只报告同向现象，不能称因果、稳定预测、实用收益或新颖性。不设置看到效果才改的门，不因基线方向不理想而翻号或取绝对值。完整报告三个基线的signed rho；本轮不挑最佳相关当部署规则、不设算法胜负门槛、不作显著性/置信区间/风险保证、bootstrap、交叉验证、回归或阈值拟合。

最终保留全部24行、全部6块和2场景，不能仅展示同向块。点、pixel、frame、pair计数只作计算量与来源说明，统计单位为相关query；仅2已见物理场景不能支持总体外推。本轮不能验证“超过所有普通基线的条件增量信息”，那是明确未完成项。

## 7. 必要反例和何时停止

人工软件检查至少覆盖：同组选图x=0；来源帧交换不改值；每帧重复像素不改变已固定质心的权重；k=2单pair与方差恒等；不均衡来源数但相同pair平均；两套选图无共同多来源点→null且不填0；相机基线正负方向；平均秩ties/constant/n<3；非法radius、重复point-frame、缺/重复query、越域帧、标签错位/不同den、封存前打开标签检测、输入/代码改动拒绝。

科学失败案例事前列明：多图共同错但彼此一致可漏检；正确曲面不同采样可表现为分散；选中图一致但未覆盖query亦可失败；固定历史匹配阈值先筛掉最矛盾的观测；半径、点密度与首写来源影响尺度；共同点域偏向重叠较多部位；低分散和来源数/相机距离可能解释同一现象。没有空间可见性时，这些原因无法被本轮排除。

输入/身份/数值/连接失败即停止、保存原失败目录；修复须新目录，不改容差迁就数据。空域/constant如实交付，不人工扰动制造信号。若不能形成可解释描述或关系不稳定，收束此普通代理量；不能从“没找着相关”推出所有跨图一致性方法无效。后续若需要真正query空间测量，最小新输入是固定query相机/内参和预测图上point_id可见映射或逐帧深度对应；要另定投影、遮挡、no-overlap和公平MVS基线，不能拿本32文件静态量顶替。

## 8. 执行、独立复核与预算

根冻结32预测输入+1标签文件、设计、最终生产与独立源码、人工检查、不同作者前审为新manifest。生产和独立核验均拒绝既有输出目录，记录实际UTC/环境/读取计数/输出哈希、开始结束源码/manifest/输入身份；根另核控制文稿。旧S14A/S14B/失败/ZIP不改。

建议生产仅Python标准库，独立核验用已有.venv Python3.12/NumPy2.3.5；无需安装包/下载权重/模型或renderer。独立者从同样32文件另重建子集/point与rank，不导入生产数值函数；整数/ID、保存原值与标签精确核对，计算浮点atol=1e-12、rtol=1e-10，预定不可事后调宽。另核所有point-components与24行、分组rho、null原因和seal在首次label读取前完成。

外部调用者600秒超时，观察CPU峰值RSS；预期数据规模可本机完成，1GiB为观察预期而非未实现硬限或速度承诺。预算最多24×2×6×该块点数的pair访问量，按实际计数记账；不同query重复访问不算新增独立pair。此草案没有运行任何真实提取/标签分析或人工实验。

## 9. 技能与近邻定位

实际读并应用Supervisor idea-evaluator：先定位普通应用诊断，F6检测“计划能验证什么”，把可检验主张收窄为已见域描述；F1检测“新增机制是什么”，本版本明确没有新方法机制。针对该诊断本身不存在已被数据反驳的核心机制，因为本次尚未读标签；不能错误触发CRITICAL拒绝。若作为投稿方法则贡献未成立，当前裁定Accept with Revisions，仅准执行准备、待独立前审。

五维从5起：Higher/Stronger/Broader保持5（无方法效果/泛化证据）；Faster/Cheaper保持5（复用档案可降低本次探索成本，但非对照算法收益）。Application类别技能给3–6个月参考，不是用户工时或承诺；用户新手、M3 Max 64GB、无GPU，适配限本机小型诊断，科研发表生命周期和每周有效小时未知，黄灯。四个范式问题均无足够证据判Yes：未证明领域忽视该问题、革命窗口或Hamming优先级，不称颠覆式创新。计算风险低、接口工程中等、泛化数据风险高、期限未知；通过范围限制应对，不能拿工具数包装价值。

本地Claude scientific-critical-thinking只读取SKILL及scientific_method/experimental_design/statistical_pitfalls相关部分：应用测量有效性、共同域选择偏差、相关非因果、场景混杂、缺失机制、预设分析和完整报告。没有调用Claude模型/CLI；表格与公式已直接表达本协议，不新增无用AI示意图，不把临床GRADE机械套入本组件研究。

本轮实际做3组定点搜索（跨视图一致性+选图/记忆；I3DM+COVRAG；Pixelwise View Selection），并打开以下原始来源；不是完整综述。最相近机制和差异为：

| 原始工作 | 核读范围及关系 |
|---|---|
| Minseok Joo、Dogyun Park、Taehoon Lee、Kyujin Lee、Hyunwoo J. Kim，Retrieve What's Missing: Coverage-Maximizing Retrieval for Consistent Long Video Generation，2026 v1 | [原文§4.1–4.2](https://arxiv.org/html/2606.02479v1#S4.SS1)：目标视图投影覆盖和互补选择。本诊断只对既定动作做历史关联点分散汇总，缺其目标空间覆盖，不等于复现或改进COVRAG。 |
| Jia Li、Han Yan、Yihang Chen、Siqi Li、Xibin Song、Yifu Wang、Jianfei Cai、Tien-Tsin Wong、Pan Ji，I3DM，2026 v2 | [原文§3.2](https://arxiv.org/html/2603.23413v2#S3.SS2)：目标视图条件的隐式3D评分。本轮无训练、无NVS特征、无空间评分，未运行其方法；对象/输入不同不自动构成创新。 |
| Johannes L. Schönberger、Enliang Zheng、Marc Pollefeys、Jan-Michael Frahm，Pixelwise View Selection for Unstructured Multi-View Stereo，2016 | [作者PDF](https://demuc.de/papers/schoenberger2016mvs.pdf)本轮网络打开内部错误，改读已有作者PDF派生文本§4.2/4.5：几何视角先验和前后向重投影一致性。本轮质心pair距离没有投影与遮挡语义，是较粗普通代理，不能冠名其完整基线或新一致性机制。 |

检索结果还出现WarpRF等线索，未全文核读不作为本次方法事实依据。未从搜索摘要引用效果数字。实际命令、读取范围、SHA、检索成功/失败和未做事项见work/S14C_design/receipt.json。主账、当前memory和冻结旧材料由根维护，本作者未修改。

