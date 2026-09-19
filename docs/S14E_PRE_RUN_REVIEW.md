# S14E 独立运行前审读

**结论：PASS，可以按最终协议冻结并执行本机已授权实验。** 这是运行前正确性与证据边界审查，不代表真实缓存已经兼容、模型查询已经成功、深度效果已经胜出或项目已经完成。最终机器回执为 `work/S14E_pre_run_review/final_review_receipt.json`，包含本次实际时间与完整已审源码/协议SHA；冻结工具必须逐项比对这些身份。

审读者s14e_camera_calibration_audit独立于prepare/predictor作者、score作者与根核验器作者。按当前AGENTS、RESEARCH_PRINCIPLES及最终S14E协议审读；本任务没有解码真实RGB、目标/历史实测深度、轨迹、NPZ，没有读取权重、调用CUT3R模型或修改生产源码、旧实验报告、主账。人工fixture中的PNG/NPZ均明确由本次检查器生成。

## 已审范围与独立证据

| 部分 | 实际核查 | 结论与证据 |
|---|---|---|
| 状态恢复predictor | 原S14D/source及官方direct接口；五字段dtype/byte、17数组白名单、Q0zero与旧call1精确parity、每call保存、encoder/state计数、异常停止 | 独立118项检查，含6个正常/后续call失败场景和2个main早期失败场景；`predictor_independent_v1/receipt.json` |
| 相机准备prepare | 20history身份、40个S8历史数组+1个S14D history_poses，GT相机共享条件，最终正向OLS，插值/K/目标转换/物理基线/source tie | 独立36项数值检查：SciPy SLERP对照、带噪20history正向拟合、target转换、退化/负尺度、标量逐点z-buffer/来源/常数/空洞；`prepare_numeric_independent_v2/receipt.json` |
| 封存后score | 静态规则、combined seal、跨prepare/model条件绑定、GT首次hash/open时序、self_z/s、δ1全分母及own/common误差 | 独立57项检查，含完整生成数据成功CLI和model开始早于condition封存的阻断CLI；`score_independent_v1/receipt.json` |
| 根不同公式核验器 | 不导入生产函数；历史源数组逐键byte、SciPy姿态、fsum、分量连续投影、scatter z-buffer、整数最近邻、评分与身份绑定 | 最后6组边界复查通过，含原半像素反例exact关闭、raw27严格阈值、巨大finite误差、50176×2像素索引；`independent_verifier_boundary_closure.json` |
| 冻结与外部caller | 准备/模型/组合seal路径、99上游源码及旧权重身份、审读SHA门、GT hash不提前、600秒/32GiB与失败目录 | 独立人工“审后源码变化”阻断门通过，`freeze_identity_artificial/receipt.json`；caller按源码审读，复用于prepare/model；score使用带seal/SHA的专用CLI |

表内独立机器检查数合计218，计数是程序/数学检查，不是218个科研样本；人工场景也不是新增真实场景。作者另外完成的37个prepare人工检查、41数组完整人工CLI及63个score自检，与上述不同作者检查分开保留，不合并宣传为独立复现。

## 最终单位与输入边界

唯一主定义是模型单位/米：A=Rpred0*Rgt0.T，u_i=A*(g_i−g_0)，v_i=p_i−p_0，s=Σu_i·v_i/Σ||u_i||²，c=p_0−s*A*g_0。target model pose=(A*G_q,s*A*g_q+c)，主深度=self_z/s。D≤1e−12 m²或s非正/非有限时阻断。原审计的反向OLS明确未采用，参见 `work/S14E_calibration_audit/scale_definition_clarification.md`；两种含噪回归不能互取倒数。

20history用RGB时间，4target用已配对depth时间；最大轨迹插值间隔0.1秒，禁止外推，RGB/depth差不超过20ms。K224固定fx245.2734375、fy245、cx112、cy111.5。GT uint16/5000，nearest 299×224后crop[37,0,261,224]，不重复深度系数、不侵蚀、不补洞。目标RGB不参与数值；GT pose是公开允许的相机条件，不宣称完全无GT输入。

官方带平移ray仅作训练一致的条件编码；基线由self Z、共享K和预测history pose按标准pinhole重投影，统一尺度、NaN空洞、精确最小z及最早来源tie。主head固定self Z，不用其他head或目标标签调整对齐。raw有效GT全部作为δ1分母，预测缺失计失败；own/common误差的分母独立保存。4个已见相关帧不当作独立样本，胜负不自动构成创新或视频质量证据。

## 本次发现并关闭的问题

1. **两种OLS定义曾混用。** 原稿及回执不改，另立明确勘误与人工反例；最终设计、prepare、score、核验器均采用model/metric正向尺度。
2. **旧Q0控制文字不一致。** 旧设计NaN/call0保留，最终协议明确zero与旧query_call_1，当前new call0为parity，new call1..4才是质量query。
3. **两个SUCCESS目录可能误拼。** score现于任何GT hash/open前核model frozen manifest实际condition路径/哈希等于该prepare；核prepare完整payload seal及prepare完成≤condition封存≤model开始。独立人工错误时序证实零GT访问即阻断。
4. **阈值等价代数不等于FP64相同判定。** 人工raw27对应GT0.0054，p0.00675时乘法式会与max除法式不同；独立器保持固定逐float quotient判定，精确mask门未放宽。大finite误差使用fsum缩放/hypot避免无谓溢出；原源码保留。
5. **半像素量化边界。** 人工恒深2且平移半像素，独立分量投影与生产矩阵运算会因FP64次序导致1568来源、896mask差异。修正为先独立核连续相机/像素坐标至原容差，再按明确的生产FP64运算次序量化，由不同scatter-min归约核深度/tie。原反例及源码快照保留，修订后exact mask/source通过，未放宽整数门，也未依据真实分数调公式。
6. **核验身份期望被覆盖。** 根核验器现先将3个执行manifest和combined seal绑定实际metadata，并以setdefault保护原冻结SHA；不以“当前重新hash”覆盖旧期望。freeze initial逐项核最终review.sources；model再次将权重/rope/兼容层/99源码绑定S14D身份。

本审读自身的prepare数值测试第一版在**最终JSON报告序列化**时，因对匹配NaN空洞计算max差得到NaN而报错。数值断言没有失败；原程序/失败回执保留，仅把报告差值限制为有限配对项，新V2通过，比较规则和容差未变。更早坐标审计的1.421e−14舍入断言也已有独立保留记录，均不算真实实验失败。

## 执行前尚须真实验证的门

上述来源、schema和数学检查不能代替将要发生的真实缓存核验：S8/S14D history pose与state_feat/mem锚必须实际精确一致；否则保留失败并停止，不绕过它重新混接。恢复Q0六输出逐字节门必须实际通过才调用4个新条件。所有输出/参数封存并经跨阶段身份/时间核验后，score才能首次访问目标深度。外部强杀只据caller与最后落盘状态解释，不编造未持久化的精确计数。

根在最终回执落盘之后运行freeze，后续源码或协议任何变化都需要明确新版本及相关复核；不要更改本最终回执以追认已执行版本。调用freeze本身会读旧NPZ和允许轨迹的文件字节核SHA，但不解码其数组；这项范围与后续prepare的真实41数组/轨迹解码要分别记账。

Supervisor idea-evaluator的可验证性/公平基线早门及本地Claude scientific-critical-thinking的构念效度、测量偏差、输入混杂与透明性原则已落实到以上修正和边界检查；没有将普通接口/标定/评价包装为创新，没有调用Claude模型或CLI。
