# S87 后续普通硬选择：输入可行性与最小草案

状态：**SOURCE_ONLY_DRAFT_NOT_EXECUTED / NO_METHOD_SELECTED**。实际检查 2026-09-10 23:30:26–23:32:36 UTC；只读既有 JSON/文本/源码，以下科学文件身份和 schema 均从回执转录，**未打开、哈希或解码真实数组字节**。当前 S87 合同不变。root 已确认本稿收敛为最廉价 RGB 整像素草案；是否值得执行由 S87 的已核结果与可见结构决定，不自动追加实验。

**判断：已有文件足以实施一个无需模型、无需目标 GT 的普通 RGB 残差排序选择；不足以判定哪个候选物理正确。** 深度赢家、候选数、深度间隙和两预测相近都不能补上这一缺口。最小草案不引入新的几何评分模块，也不把它的成败推广到 latent 硬替换或50步采样链。

## 1．回执里究竟有什么

本稿路径简称：R=/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling；P=R/work/S85_fixed_geometry_warp/execution_01；E=R/work/S86_fixed_warp_consumer/execution_01。下列 shape 是回执声明及既有保存范围，不是本批重算验证。

### S85：能追来源、排序和投影冲突，不能辨认真遮挡

| 固定文件 | 字节与 SHA-256 | 可用信息 |
|---|---|---|
| P/INPUT_GEOMETRY.npz | 12586026；e8ed5f82c4dda3453e912c1bb600d928615e17822ddc254989df8fd6798d12cf | source_depth FP32[4,384,512]、source_colors FP32[4,384,512,3]、source_K_saved FP32[4,3,3]、source_c2w_saved FP32[4,4,4]；history_ids/target_ids int64[4]；target_c2w FP64[4,4,4]、target_K FP64[3,3]。 |
| P/TARGET_20.npz | 162235122；c5a00ca9b20131cfdfa571d9aca8084346251374de0f47ac31325894729acb8a | 31字段；候选长 C=2273304。 |
| P/TARGET_21.npz | 157968034；471e618e73a2f793cdefe46ac8e2f7466c35de79ece12faaeb0f3f47a847207e | 同31字段；C=2135656。 |
| P/TARGET_22.npz | 146338446；ba127ac8bd5fac5cbded242fabc1fa39444be9b72fc1c955b91e2cab4882efd3 | 同31字段；C=1760508。 |
| P/TARGET_23.npz | 138865338；582ab7c20a18596917b0425ede50dfa50800f6dfc7c6c151c8363b17f2c9616e | 同31字段；C=1519440。 |

每目标的选择相关字段包括：`mask` bool[576,576]、`warp_rgb` FP32[576,576,3]、`candidate_count` int32[576,576]；`winner_Z/second_candidate_Z` FP64[576,576]；两者各自的 history_id int16、source_row int8、pixel_id int32、slot int8，均为[576,576]。完整候选保存 target_index、Z、source_row、pixel_id、slot、weight、rank、winner 八项[C]数组，故失败候选未被只保留赢家的摘要抹去。另有源状态、target_xyz/uv与四邻足迹，可追投影步骤。

历史源行对应 **[12,13,18,19]**；完全平局时的优先序为 **19/18/13/12，再源像素ID**。target_Z升序的首项是赢家；第二项可以与赢家Z相等，**不是第二个不同深度层或第二个不同物体**。weight只决定正双线性足迹资格，颜色直接复制赢家，未加权平均。孔洞 mask=false、RGB=0、缺失ID=−1/Z=NaN；黑填充不是真实黑物体。

这些字段允许计算“在现有预测和固定相机下谁更近、来自哪里、与谁竞争”，也可按ID从 source_colors 查回其他候选的颜色。它们不提供对象身份、真正可见性、目标实测深度或经校准的误差概率。S85明确没有 confidence 过滤、深度阈值或点云清理；其保存输入不含 learned confidence 字段。几何来自 S83 FINAL_BEFORE_CLEAN，预测Z不能冒称独立公制真值。扩大到多候选渲染并非本最小草案所需，故未来最小执行也不必再读这批约618 MB的投影档案。

### S86：可直接比较两个输出候选；G0末态支持另一个更贵粒度

| 文件 / 回执字段 | 类型与 shape | 文件 SHA-256 |
|---|---|---|
| E/warp_rgb01.npy | FP32[4,3,576,576] | aa8bd7de61135d8235600c8edba186404333f8664ca4ba55e24ca9a303c64ed8 |
| E/image_mask.npy | bool[4,1,576,576] | 7b568a61a70136df3f88a84d5d5bdc76d4eba9e0b37e3ed892384da4fce30209 |
| E/G0/targets_fp32.npy | FP32[4,3,576,576] | b3776a65159b2989a00c5299d8e77811b0b144eb776dcab0ecd49553a1d0ec41 |
| E/ENCODED_WARP.npz | W FP32[8,4,72,72]；m FP32[8,1,72,72]；history_slots bool[8] | 170159f1d87544f60823ec5149cdf323d7a150de2f440c25f3d160aa08dd8f86 |
| E/G0/LAST_STEP.npz | sigma/next_sigma/sigma_hat FP32[8]；x_tilde/raw_clean/used_clean/output FP32[8,4,72,72] | 2dc7eb4cbc23eae7faad3a1e5234319340ae078606e849f9fa91e2c1cd806c8b |
| E/G0/all8_latents.npy | FP32[8,4,72,72] | 85772cd3fda7d8f0121f7e04ec5a315ee1de17c145027864408aa7b90113c286 |

目标顺序 **20/21/22/23**，8槽中历史顺序 **19/18/13/12**。G0末步元数据为mode=G0、step=50、gamma=0、complete=true；七张量连续body身份已在本目录 PROTOCOL_DRAFT.md逐项列明。它可提供未经末端引导的clean、原Euler状态及输出核验，**没有G0物体深度、正确相机对应点或形状标签**。m是avg8支持比例，并非错误概率；编码后的W也不携带可直接解读的独立物体假设。

## 2．粒度不同，所回答的问题不同

| 粒度 | 选择单位 / 最小代价 | 边界 |
|---|---|---|
| RGB整像素（本稿唯一草案） | 同一像素的3通道一起来自G0或warp；无需编码/解码 | 避免该像素直接软平均；相邻像素仍可能选不同来源，出现接缝/错形，不保证整个对象一致。 |
| latent标量 | 一个空间格的一个通道；需原末步Euler及全8槽VAE解码 | 最贴NVS公开实现，但通道可交叉、VAE非局部；还须定义软m怎样变为合法排序集合。本稿不增加此臂。 |
| latent整空间格 | 同格全部通道一起选 | 与NVS公开标量排序不同；并非RGB整像素/对象选择，仍要解码。 |
| 整图 | 一个目标全选G0或部分warp | warp有洞，仍须定义洞区处理；缺乏选择正确整图的独立准则。不能当对象级多假设推断。 |

[NVS-Solver v2 §5](https://arxiv.org/html/2405.15364v2#S5)已提出排序替换来避免平均模糊；[固定源码923–980行](https://github.com/ZHU-Zhiyu/NVS_Solver/blob/40c6555e53f45d6532a00b5c1e13aaa120dc9973/src/diffusers/schedulers/scheduling_euler_discrete.py#L923-L980)实际按C×H×W标量绝对差排序。下述RGB三通道距离、精确配额和稳定平局是**明确声明的普通适配差别**，不是论文原实现，也不是新算法贡献。最近工作已有这类选择动机，不能靠改粒度或命名建立新颖性。

## 3．唯一最小草案：固定四分之一合法RGB像素，按残差复制

本节是可以交给实现者的确定规则，**未写执行器、未执行**。固定一项策略，不扫描比例；比例 **ρ=1/4** 取自已有S86末端.25参照，不由S87分数挑选。

1. 仅以表中前三个S86数组为科学输入。核文件/body身份、shape/dtype/有限性、四目标顺序。按原Gpaste逐帧分支将G0 raw转换为RGB01，再clamp[0,1]；不从旧uint8开始混合。warp直接用已保存RGB01，合法集合E_t严格等于原image_mask，不加入深度gap、置信度或新可见阈值。
2. 在每目标合法像素内，先将RGB01数值提升FP64，计算残差 `d_i=(a_R−w_R)²+(a_G−w_G)²+(a_B−w_B)²`，固定括号顺序为 `(R项+G项)+B项`。按 `(d_i, C-order像素ID)` 升序。N_t为合法像素数，K_t=整数N_t//4，选前K_t项；精确平局按像素ID，不靠不稳定排序。空集合保留全G0并记录K=0，不能除零或临时改比例。
3. 选中的整个RGB三元组直接复制warp，其余保留转换后的G0。没有软插值、形态学或再次渲染。逐帧按S86同量化次序形成uint8；保留全部4目标。未选位置的raw须与转换并clamp后的G0相同，uint8须与该G0按原流程量化后的值相同；不要求新RGB01 raw与旧未转换raw相同。这里的保护仅针对RGB数组，不能反推latent选择也局部。
4. 保存每像素资格、FP64残差、排序名次（洞区−1）、selected mask，以及N/K、raw/uint8和实际时间/资源/失败。仅此策略4条新frame记录；引用旧G0/Gpaste(.25)和已验S87普通末端结果，不把它们记作新重演，也不挑每帧最优。
5. 选择过程不读参考、目标深度或S87的逐像素误差。新输出全部封存后才可沿用既有full/support/hole、完整分母、uint8量化和整数SSE评分。不新增事后主指标；完整图的重影/接缝观察仍只作非盲描述，不提升为正式感知或相机准确评分。

这是**不使用GT即可唯一算出的启发式**，不是GT-free正确性证明。低残差首先说明两候选相近，可能只是共同错误。ρ是被替换像素的名义比例；它不等于每像素软强度.25，也不等于实际干预剂量。即使3K_t与.25×3N_t相差不足3个标量，硬选择改变量的平方和与软融合仍不同；本比较不能单独识别“是否保留形状”的因果效应。

资源草案：CPU、纯NumPy、0模型/0VAE/0新链；只读三个数组约33 MB（按回执body估计，非新测量），每次排一个目标、N_t≤331776。拟上限60秒、RSS1 GiB、单次输出128 MiB、不自动重试；这些是待正式冻结的预算，不是实测速度。来源数据加载与评分分别记时；不为此另建框架。

## 4．致命缺口与停/走判断

**最致命的是不可识别性。** 同一组已存输入可能对应“warp位置正确、G0位置错误”或相反解释。只观察这些输入的确定选择器会作同一决定，不能保证在两种真实情况中都对。S85最小Z和大gap只针对预测候选排序；没有误差界，也不知道隐藏表面是否本应遮挡。G0与warp残差为零仍可能共同错位。把候选ID保持一致最多保留来源，不等于保留真实物体。

仅在S87全部实际结果及完整图验收后，root判断**仍有一个低成本、具体的软叠加问题值得排除**时，才值得考虑本额外诊断。若普通S87末端已经达到所需描述分数且不存在尚待解释的明显结构缺陷，停止继续rank试验。若当前瓶颈已经是请求相机/真实物体位置能否确认，应优先独立场景与可靠参考，不能连续更换RGB算子来回避测量缺口。

即使此RGB策略得到更低MSE、更少可见叠影，也只支持这个已见例子的普通末端作用；不证明几何更准、新方法或latent/多步收益。若更清晰但位置仍错，不算解决相机问题。若无改善，收束这一个固定RGB规则，不自动扩比例、mask或更贵链，**也不能据此否决NVS的latent硬替换或50步链机制**。后续动作仍由明确剩余问题决定。

## 5．本批源核范围

全文读S85 CONTRACT.json（SHA bcf4801ff1619ec74e5714e2ba90c556a6abb6c45f48b2f3185b2eb9925a333b）；读其execution_01/RECEIPT.json的5项artifact身份、INPUT_GEOMETRY及TARGET20完整schema，另三目标核字段数、候选长度与第一/第二Z的schema（SHA 2e34772a25750973db8afa76bc94d04875acd87bff6cb66540f278191bccad05）。S86全局RECEIPT中warp_rgb/image_mask/encoded_warp、G0回执中arrays/last_step/last_metadata逐项读取；两回执SHA分别2fd8749808c617a5583163e929fa3310e458c029c9b9e7c96cbe7f754efe694a、4ab7fb0553bee32b5971c62f89184b6bbcf32b0373a3bb94fcd046a0bffb6f07。原运行回执中的PENDING字样是历史封存状态，不能覆盖之后的root接受。

源码实读S86 generate_with_fixed_warp.py 179–190、291–326（SHA 98c5f2f409c88817851f1b3ff74f987879d6274c27b36995bbb69bb76f1bdbd9），sampler_hooks.py 168–192（SHA 2521dac2e07d0809eaecf23c37e6f41a5d157435ef7e5d010eec8ce840933ae4）。NVS的版本/源码范围复用本目录 SHAPE_FAILURE_MECHANISM_REVIEW.md，没有新增联网、模型、真实数组读取或评分。本稿未改任何已有协议、科学执行文件、结果或主账。完整初稿回读时钟：2026-09-10 23:34:54 UTC。
