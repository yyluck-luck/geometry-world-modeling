# S14C独立核验准备

这是独立核验器的执行前准备记录，不是S14C真实测量或标签关系结果。入口为 `scripts/verify_s14c_selection_disagreement_independent.py`，最终源码SHA、人工回执和实际时间见 `work/S14C_independent_preparation/preparation_receipt.json`。根负责冻结与实际运行；本作者未解码真实32输入的CSV/JSON，也未读唯一真实评分文件或任何真实NPZ。一次人工CLI路径误配置曾读1份真实预测JSON字节做SHA，立即被身份门拦截，详见末段，不能把本团队准备字节读取总数写成0。

本作者先读AGENTS、当前RESEARCH_MEMORY、最新RESEARCH_LOG和S14C草案，确认S14B已成功、不重跑。此前已实际阅读的本地Claude scientific-critical-thinking技能继续用于测量构念、不同算法复算、共同点域偏差、缺测与相关非因果；没有调用Claude模型或CLI。S14C只核已选四图的预测分散，不能补出目标投影、遮挡或新机制。

独立性边界：只通过消息接收生产输出schema，未阅读或导入 `measure_s14c_selection_disagreement.py` 的数值函数。原S14A提取器只作为历史字段/trace定义阅读，S12 writer只用于读取标签字段定义；没有导入它们或重跑成功阶段。准备期可消费生产作者完全人工的输入/输出作接口核验，清楚记录人工路径；这不属于真实预测或标签访问。

核验从32个固定预测输入的字节缓存开始：先核全部SHA与路径白名单，再解码同一缓存的两份CSV和30份JSON。CSV只数值化point/m/radius、point-frame质心及其计数等允许字段，旧W/B/A/D/within_variance不参与。本作者人工CSV故意让被排除的字段含非数字字符串，以验证其没有进入数值计算。

每块重建全部point来源字典，核无重复point-frame、地图point_id完整、m等于质心来源数、半径正且平方有限非零。由原官方G和姿态P保存动作重建共同域J，精确核原候选/选中图顺序、25格coverage、全部共同点ID及选中来源/每个pair。主e使用平移中心平方和：`e=2/(k-1) * sum(||c-mean(c)||^2) / r^2`，区别于生产的显式pair距离遍历。逐pair分量用同公式的k=2情况复算。帧内像素数不作权重；主E对点等权；空域保持null。

三个基线方向固定：来源数为P−G，相机内部六pair平均为P−G，query距离平均为G−P。相机pair只从accepted trace步骤取已存距离，按原step/comparison索引精确核保存值及六pair身份，不从拒绝步骤补值或重算姿态。浮点计算一律 `abs(actual-reference)<=1e-12+1e-10*abs(reference)`；整数、IDs、保存标签、保存距离、CSV到封存JSON的数值往返精确，不放宽容差。

根在真实提取前确认的group_contract覆盖草案中pooled描述的歧义：只2场景+6块共8组，每组4个signed Spearman，合计32项；24查询全表及计数保留，**不算pooled rho**。四量使用同一有限值query集合；n<3或对应变量/标签constant返回null及固定原因，不因一个baseline常量删除其余项。

Spearman数值语义经根事前确认：首先独立重算全部封存scalar并按固定门核验；随后对这些已核验的封存原始浮点值独立计算秩，以严格遵守“相等值才tie”。不能让独立求和的微小舍入差异人为拆开或合并原本并列的值，也不用容差并列。秩保存为两倍平均秩的整数，Pearson的协方差及方差分子用整数乘积/求和，最后才除平方根。这是独立rank实现，非使用生产rho或复制生产秩。

CLI合同：

```sh
python3 scripts/verify_s14c_selection_disagreement_independent.py --manifest docs/S14C_EXECUTION_MANIFEST.json --measure results/S14C_selection_disagreement --associate results/S14C_exploratory_association --output results/S14C_independent_verification
```

上述是待根运行命令。manifest必须绑定 `independent_verifier_sha256`、生产源码、恰好32预测输入、唯一score_input及根给定group_contract。调用必须已有对应associate目录；核验程序仍先核测量seal全部八载荷、输入、逐点结果、24rows、来源及计数，并保存独立预测重算，之后才首次读取本程序的唯一评分文件。它不声称研究者从未见过旧数据，也不把独立核验放在生产associate之前；生产measure本身必须先封存且被associate验证，时间和零评分读取计数同时核对。

评分只消费保存192条件中24个main A0P0 stride8行，核全键、G/P动作与候选身份、相同正den、整数num、保存support精确num/den；y原值为保存差的负号，精确核writer表达式。joined的原scalar/label不可重算后改写，全部24行精确与封存测量/标签源匹配。

输出新目录，拒绝覆盖。成功和失败都保存实际UTC、Python/平台、源码SHA与源码快照、比较数和错误上下文；成功还核全部输入、measure九文件、associate载荷和manifest/source前后SHA。日志中标明先完成测量核验再读score。失败目录与初版人工失败不删除。

人工测试从字面量生成32预测档案、24query与192标签条件，覆盖同选四图零值、来源交换、重复像素不改变权重、k=2恒等式、不均衡k相同pair平均、空共同域null、25格计数、方向、ties/constant/n<3、非法radius、重复/越界点帧、缺query、标签错位/den不同，以及seal前标签拒读。初版人工runner有一个括号语法错误，发生在执行前；已保存原代码与错误记录，修正后46项通过。最终源码同46项检查见artificial_checks_final_source.json。

完整接口人工集成消费生产作者 `work/S14C_implementation/artificial_v2/synthetic_root/` 的人工字面量产物，byte复制生产snapshot后外部运行CLI，未读/导入其数值函数。integration_v1漏传 `--root`，生产默认主项目；UTC06:47:57.736490–06:47:57.749156实际读取 `results/S12_matched_budget/selections/S7_block0_query20.json` 的字节校SHA，首项与人工manifest不同即停止。其input_hash_reads_before=1，CSV/JSON解码0、score字节/解码0、测量行0。原integration_receipt初设real_input_files_read=0并不符合这个失败，`integration_v1/scope_correction.json`明确纠正；原始回执/失败目录均保留。这是人工CLI路径配置错误，不是科学测量失败。

integration_v2显式人工 `--root`，生产measure/associate成功；独立入口发现生产原人工标签fixture只有24个main条件，与真实writer合同192不同而拒绝。integration_v3只把人工非main条件补到192，24个main原值不改，独立代码不改。UTC06:49:03.621081–06:49:03.840864全链PASS：30,585项精确、1,080项浮点，最大差8.881784197001252e-16。完整代码/输入/输出均在该新目录，根与输入身份补充回执见integration_v3/identity_receipt.json。它只证明人工接口和数值复算相容，真实测量/关联仍待根冻结执行。
