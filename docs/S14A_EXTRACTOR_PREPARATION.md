# S14A：评分前诊断特征提取器准备记录

本文记录程序准备，不是新方法结果。作者为独立分工的 feature-extractor agent；测试由同一作者编写，不能标成不同作者审计。真实30输入特征提取、训练、门控、阈值选择、重新评分均尚未运行。父任务须先冻结协议、输入清单及最后源码身份，再决定执行。

## 要回答的问题和本轮边界

S14候选希望判断“什么时候几何来源选图可能不如姿态回退”。本阶段只整理两种既定动作在评分前留下的信息，建立可核对的15列输入。集合交叠、权重集中度、熵和姿态距离都是普通诊断量，不是新算法创新。它们是否能预测受损、是否超出同信息普通门控的能力，尚无结果。

本轮读取了项目AGENTS、当前记忆、最新日志、S14输入结构清单与创新候选文稿。为核字段语义，只查看了允许集合中的两个示例JSON：S7 block0 stride8的prediction_only_selection.json，以及S12 S7 block0 query20的selection.json；这属于既有字段检查，不是特征表运行。另只读记录器和选择器源码，没有打开S12 records/summary、S13数值结果、评分NPZ、原照片、GT或预测数组。

使用本地Claude scientific-critical-thinking的测量定义、混杂、输入可用性和证据边界原则；不调用Claude模型/CLI。Supervisor idea-evaluator在已完成的S14候选审查中规定本阶段只能做前置验证，本实现不重新宣告新颖性。未使用临床GRADE评分；这份输入合同不需要生成式示意图，表格足够说明。没有新增网络文献判断，因此不重复已有定点检索。

## 输入合同

入口为 `scripts/extract_s14_prediction_features.py`，只依赖Python标准库。命令要求 `--manifest` 和新的 `--output`；`--root`默认为入口所在项目根。

运行时实验输入必须**恰好30份**：

- `results/S7_event_replay/block{0,1,2}_stride8/prediction_only_selection.json` 共3份。
- `results/S8_event_replay_v2/block{0,1,2}_stride8/prediction_only_selection.json` 共3份。
- `results/S12_matched_budget/selections/{S7,S8}_block{0,1,2}_query{20,21,22,23}.json` 共24份。

manifest必须含 `schema: "s14a-prediction-feature-manifest-v1"`、`extractor_sha256`以及30条 `inputs: [{"path": "项目内相对路径", "sha256": "64位小写SHA"}]`。每项只能有path/sha256；路径集合必须与代码内完整固定域相同。缺项、重复、额外输入、错SHA和符号链接重定向均拒绝。可由父任务从现有inventory的json_inputs筛出上述30项，**程序不自动打开inventory**，也不沿输入内任何路径去读取其它文件。

协议/manifest/源码本身是控制文件，不算30份实验JSON。程序读取manifest和自身源码以验证冻结身份；所有30实验文件的字节SHA全部匹配后才开始JSON解码，特征只取下述字段。JSON解析会解码完整允许文件，其它键不参与特征或输出；这不是操作系统沙盒或流式隐去未知键。已见查询和研究团队已知旧答案的事实也不会因输入隔离而消失。

运行完成前再次读取30输入、源码和manifest，保存前后SHA。第一轮SHA通过的字节缓存在内存，之后从同一缓存解码，避免先哈希再重新打开解码造成输入身份缝隙。计数来自实际执行分支，包括哈希读取尝试数、成功数、JSON解码数、特征行数、最终所用pair数，不是系统级文件访问追踪。

## 精确字段语义

来源侧只用每个query的 `maps.A0P0.official_trace` 与 `maps.A0P0.readouts.official`；不分析其它图变体、readout或stride。姿态侧用独立selection JSON的原 `trace` 和 `full20_*`距离/顺序。两端ID必须位于0–19，候选各14个不同ID，最终各4个不同ID。

源码定位：`src/vmem_retrieval_kernel.py::process_retrieved_spatial_information`、`src/rgbd_retrieval.py::select`、`src/s7_event_replay.py::decision_trace`、`scripts/run_s12_matched_budget.py::make_selections`。

`weights`是原renderer可见来源的权重：按来源累计 `cos/(1+depth)`，再对来源总和归一化；其中已有实现首次遇到来源时初始化后又累加一次，该历史行为不在S14A中修正。它们不是测量准确率、经过校准的置信概率或独立样本频率。`candidate_counts`是离散候选配额，当前主域为20个ID中14个1、6个0；**不能把配额当成概率来算熵**。程序只用它核候选身份。

姿态“距离”是原选择器组合量 `0.1 × 保存的预测坐标中的欧氏平移距离 + 旋转角（弧度）`；距离函数本身没有另做平移归一化。因此列名不写米、厘米或单独角度。query距离统一取S12保存的全20 FP32值，并核两条trace的候选距离精确一致；不重新计算相机、平均姿态或PyTorch排序。pair距离来自原FP64 NMS比较。这里的f32/f64指历史记录产生时的精度，特征运算由Python float与math.fsum完成，不称全程FP32。

执行前独立审读提出上述距离措辞修正，根仅改此段，源码/人工检查不变。作者原准备回执对应的MD已另存 `work/S14A_extractor_boundary_checks_v2/preparation_before_wording_correction.md`；不把旧回执哈希改成新文稿，最终执行冻结应绑定当前修正版本。

## 固定15列特征

以下G表示来源14方案，P表示姿态14方案。C为候选集合，S为最终四图集合；w是保存的20个来源权重，p=w/Σw。集合ID和阶段不是模型输入。

| 输出列 | 明确定义与来源 |
|---|---|
| `candidate_intersection_count` | 两个14候选集合交集大小，0–14整数 |
| `candidate_jaccard` | 候选交集大小/候选并集大小 |
| `selected_intersection_count` | 两个最终四图集合交集大小，0–4整数 |
| `selected_jaccard` | 最终集合交集大小/最终集合并集大小 |
| `source_weight_hhi` | Σp²；集中度，不称可靠性 |
| `source_weight_max_share` | max p；只反映来源票集中程度 |
| `source_weight_normalized_entropy` | −Σp log p / log20；零权重仍占20个槽，0log0按0处理 |
| `source_weight_gap_14_15_raw` | 验证原weights为[0,1]内精确可表示的有限FP32值，降序第14减第15按FP32最近偶数舍入；精确核既存cutoff_gap_14_15后直接使用保存gap。不是Python双精度直接相减、candidate_counts间隔或再次归一化的差 |
| `pose_query_distance_gap_14_15_f32` | 全20保存FP32距离升序，第15减第14；本域要求无tie |
| `source_selected_query_distance_mean_f32` | G最终四个ID对应全20保存FP32距离的算术均值 |
| `pose_selected_query_distance_mean_f32` | P最终四个ID对应同一全20距离的算术均值 |
| `source_selected_pair_distance_mean_f64` | G四图六个保存pair距离的均值 |
| `source_selected_pair_distance_min_f64` | G六个保存pair距离的最小值 |
| `pose_selected_pair_distance_mean_f64` | P四图六个保存pair距离的均值 |
| `pose_selected_pair_distance_min_f64` | P六个保存pair距离的最小值 |

熵与HHI归一化是为了消除已保存浮点权重和不恰好为1的舍入，不是更改原选择权重。纯函数允许一般有效单一来源权重，其归一化熵定义为0；真实主域仍强制完整20个ID。空权重、全0、负值、非有限数、重复ID都会失败，不填0蒙混过关。

元数据固定为 `stage, block, query, split, arm, stride`，单独列于metadata_columns。stage/block/query/split只能用于分层识别和溯源，不能进入后续拟合。JSON显式给feature_columns，CSV虽并列元数据与特征，消费者必须只采用feature_columns列表。开发/测试字样沿用旧数据标签，不表示本阶段获得新测试集。

## 最终四图的六个pair如何核验

没有保存所有190个历史pair，程序也不会重算190个距离。对每方原trace，读取最终selected次序，并定位后三个最终ID各自被接受的NMS step：第二张须有与第一张的1个比较，第三张须有与前两张的2个比较，第四张须有与前三张的3个比较，总共六个。

必须严格匹配既有接受次序、比较ID次序和全部六个无向pair。行级溯源保存原step索引、comparison索引、两个ID和原距离。拒绝步骤里的偶然比较不替代被接受步骤中缺失的数据；若存在非空fallback、缺失pair、重复ID、非有限值或接受次序不符，停止并保存失败，不设0，也不找其它评分数据填补。

成功运行预期是24行，每行两方各6个，共288个**pair使用记录**。某个物理pair可能在多个query或两方重复使用，288不是288个独立pair、更不是新距离计算。

## 输出、失败与记录

成功的新目录包含：

- `features.csv`、`features.json`：全部24行×15列特征，以及6项元数据。
- `row_provenance.json`：每行两份来源路径/SHA、query指针、候选/最终ID、归一化前权重总和、12条pair来源。
- `input_identity.json`：30输入前后SHA。
- `frozen_manifest.json`、`extractor_snapshot.py`：本次实际控制文件副本。
- `run_metadata.json`：实际UTC开始/结束、环境、源码/manifest前后SHA、计数、输出SHA与状态。

输出目录存在就拒绝，不覆盖历史。manifest格式或源码SHA失败发生在建目录前，调用方要记录控制台错误；建目录之后的输入/字段/特征错误写failed元数据。若缺pair等发生于部分行计算之后，不写部分成功feature表；已经创建的失败目录保留，修订后用新目录重试。后续独立核查应读取冻结快照，而非默认把live源码当作历史执行版本。

## 已做人工检查和未做事项

`scripts/check_s14_feature_boundaries.py`使用人工数据：手算均匀/稀疏/单来源权重；15列已知结果；空/全零/负/NaN权重；重复ID；缺pair/Infinity/fallback；重复JSON键；错误文件/源码SHA；非法路径；重复清单项；已有输出。它不读取真实实验文件，也不生产真实特征表。

首次19项于UTC2026-09-06T03:53:17.437120–03:53:17.470225通过，环境为本机Python3.13.0（Homebrew，macOS26.7 arm64），回执保存在 `work/S14A_extractor_boundary_checks/receipt.json`。随后仅增加运行元数据中的源码和manifest结束SHA明示字段，当时版本于UTC03:54:42.142553–03:54:42.155775再次19项通过，回执为 `work/S14A_extractor_boundary_checks_v2/receipt.json`；旧回执保留，不是失败重试。该历史入口SHA为 `188061a33c107043f7396c401affb10b5112fcd71db941159c9cde9dbedf12f3`，人工检查器SHA为 `ce4977be088e30e51574c2342da3fba2bac708d4d252c279b478b63f0fb5b5eb`。`--help`也已实际执行成功，没有调用主提取入口。此后独立预审发现下面的浮点语义缺陷；这19项通过不能代替独立审读。

尚未做：真实30输入的提取器运行、修订版不同作者复审通过、特征有效性检验、标签联结、场景外测试、阈值/模型拟合、路由动作、模型或renderer推理、速度收益/视频质量判断。程序准备只能支持下一步的输入可用性核对，不能说“新创新已验证”。当前query位姿仍来自已见query RGB，因此也不声称生成前只有轨迹时可直接部署。

## 独立预审后的FP32差值修订

根任务转达独立预审发现：原 `src/rgbd_retrieval.py::select` 的cutoff_gap先由NumPy FP32标量相减，再转Python float保存；初版提取器对保存权重直接用Python float相减，非近值输入可能得到不同结果，误拒合法记录。用人工a=0.029999999329447746、b=0.0010000000474974513可复现：原FP32差是0.028999999165534973，Python双精度差是0.028999999281950295。原19项只含容易相减的权重，未覆盖该错误。

UTC04:00:11保存了修前源码、检查器、当前准备文档与SHA回执至 `work/S14A_extractor_before_fp32_gap_fix/`；该文档快照已包含根此前修正的预测平移距离措辞。现实现只依标准库 `struct` 和 `fractions.Fraction`：先逐一验证保存权重/gap处于[0,1]且能精确表示为binary32；对降序第14/15权重求精确有理数差，以初始binary32结果及相邻两个可表示值到精确差的距离选最近者，恰好中点按尾位偶数选择。该有限单位区间内binary64近似相减再转binary32的初始估计至多偏一个binary32步长，因此邻居检查覆盖可能的双重舍入；包含subnormal，不做flush-to-zero。这样无需引入任意浮点容差，也不要求双精度相减本身一定精确。

最后对已保存gap作**精确相等**检查，特征直接复用验证通过的保存值。HHI、熵、两端集合、query距离和pair特征定义均未变化。新检查增加给定非近值回归和整行保存gap验证、两种偶数舍入中点、subnormal及宽指数差、非FP32权重、超出单位区间、错误顺序、错误保存gap/双精度gap拒绝。

修订版26项人工检查于UTC2026-09-06T04:00:53.647649–04:00:53.661208全部通过，回执 `work/S14A_extractor_boundary_checks_v3/receipt.json`。修订入口SHA为 `cb550ce7a61ca4c40a9fd7a257a75aa9bc1b6445a905f4e648a96c1e979e8d0e`，检查器SHA为 `e6f1795c1ef83cffab1d7da2993cc74e710a36a64002be08e19a776d2f125101`。实际真实输入提取仍0次，等待根任务的不同作者复审及最终冻结；不修改主协议、manifest或主日志。

### v4：混合符号零修正

独立复审另指出：当左值−0.0、右值+0.0时，精确差是零，但原候选构造会从负零位模式生成空区间。这是合法零权重输入的边界缺陷。UTC04:04:08.226787完整保存v3源码、检查器、文稿及SHA至 `work/S14A_extractor_before_signed_zero_fix/`，随后仅在精确差为0时直接返回+0.0，未改变其它差值处理。helper对exact==0的中间校验零规范为+0.0，属于数值校验，不主张对signed-zero位模式逐位重现。下游仍验证并直接复用保存gap，包含保存的负零符号，不另改保存数据。

增加(−0,+0)、(+0,−0)两项人工检查及下游保存gap复用验证，v4共28项于UTC04:04:08.326806–04:04:08.338988全部通过，回执为 `work/S14A_extractor_boundary_checks_v4/receipt.json`。**当前待复审入口SHA**：`1dff7df7acff1ac565fb103968495a37a34dff0b94c51c24499406beaf62c005`；检查器SHA：`95959f91e1910729d9838d41d50fb03d103bf22c6dfd8571bc21094d93582dec`。没有扩展其它功能，真实输入提取仍0次，原v3回执保留。父任务与research_novelty_routes已收到新身份，等待独立复审。
