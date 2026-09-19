# S14C执行前审查：普通预测分散与支持差的探索

状态：PASS_FOR_FROZEN_EXPLORATORY_EXECUTION。审查者 /root/s14c_operational_design，与生产作者和独立核验器作者不同；我也是本阶段设计草案作者，因此这是不同实现作者的代码前审，不冒称完全外部的方法新颖性评审。完整身份与实际时间见work/S14C_pre_run_review/receipt.json。

## 结论与允许范围

最终生产实现通过静态审读、作者39项人工检查及本审查者另写的26项手算/平均秩检查；独立核验器的输入/输出接口、隔离顺序、身份/容差和独立性声明通过核读。没有未解决的执行阻断项。根可冻结32个预测输入、1个标签输入、最终源码、设计与本前审后，执行一次有界探索。**这里没有读取真实测量行或标签，也没有得到S14C实际相关结果。** 前审通过不等于算法有效、创新成立、跨场景泛化或完整视频完成。

本主量是同一query已定G/P四图在共同历史关联点上的pair平均平方分散差，x=G−P；label为旧支持差y=P−G。共同域缺失按null处理，不以零伪造一致性。它没有目标像素可见性/遮挡，不能称C2联合冲突已实现。

## 真实输出读取前明确的合同澄清

根与设计/生产/独立核验作者在真实32预测输入和标签解码前明确：只计算两场景与六块共8组，每组4个signed Spearman，合计32项；全24query仅完整行表/计数，**不计算pooled rho**。草案中“全24总表只作描述”此前不够明确，本段和manifest.group_contract将该选择具体固定。保留原草案SHA，不宣称在看结果后追认。这个选择不是挑选哪个场景结果好，全部24行和8组均须报告。

固定group_contract为scene_groups=[S7,S8]，block_groups=[S7:0,S7:1,S7:2,S8:0,S8:1,S8:2]，minimum_valid_rows=3，valid_domain=all_four_metrics_finite，tie_rule=exact_sealed_float_equality_average_ranks，pooled=rows_and_counts_only_no_rho。metrics按生产四列顺序：disagreement_g_minus_p、source_count_p_minus_g、camera_pair_p_minus_g、query_distance_g_minus_p。

独立核验先用不同求和公式复算预测scalar，并按预定atol=1e-12、rtol=1e-10核对；再对**已通过数值核对的封存scalar原值**独立计算秩，精确相等才tie，不用容差并列，也不让独立求和舍入拆开原有tie。独立者使用自己的秩算法，不复用生产rho。该语义同样在真实结果读取前确认，不事后改浮点门。

根确认实际顺序：measure → 根核seal/成功记录/身份 → associate → 不同实现全量核验。独立核验器内部先重建并核测量，再首次读该核验进程的标签。生产准备文稿先前“标签联结前根独立核测量值”超出了现有入口，已由作者保留旧稿后澄清；本流程不再作该不实承诺。生产measure封存和associate核seal仍是硬顺序，不降低为同时提前读labels。

## 静态核对结果

| 范围 | 已核内容与边界 |
|---|---|
| 输入与身份 | 32预测路径完整固定：两份S14B CSV、6份原prediction_only_selection和24份S12 selection；label唯一固定S12 records.json。预测32文件全部SHA通过后才从缓存解码，不沿JSON内路径访问新文件。源码/manifest/输入前后身份核对；外部控制材料由根caller负责。 |
| 输入白名单 | points只数值化phase/block/stride/point_id/m/radius；frame表读质心/来源及计数结构。旧W/B/A/D/within_variance不进入主量。CSV整行文本解析不等于只打开几列的文件系统沙盒。 |
| 连接与动作 | 六块point ID连续、point-frame唯一、m=来源数、radius有限正且平方可表示；G/P候选14、最终4、0–19 ID、NMS接受次序、六pair和共用query距离一致。来源20个0/1配额也与G候选核对。 |
| 量与共同域 | 仅kG≥2且kP≥2点进入两方同一J；先选中来源pair等权，再共同点等权；帧内像素数不作额外权重。两端E及x、来源数、六pair相机分散和query距离差方向正确。 |
| null与覆盖 | 空J保留null和NO_COMMON_MULTISOURCE_POINTS，相机量仍保存。总点/两端eligible/common三分母和完整25格来源数计数均保留；不删除合法同选四图x=0的query。 |
| labels与封存 | measure阶段没有score文件读调用，32预测输入的八个载荷由第九个seal文件绑定；associate先核完整seal/SUCCESS/源码/manifest/零评分读/24行再读唯一label。标签动作和候选原序精确联核。 |
| label算术 | 各保存support精确等于整数num/共同正den；y直接取保存geometry14_minus_pose14_pp的负号，再精确核100*(P.support−G.support)。不把整数先作差的不同舍入顺序强加为逐位标准；valid分母不随预测J改变。 |
| 统计 | 三基线方向事先固定，四量使用同一有限query集合，精确tie平均秩；n<3或某变量/label常量则对应rho=null并给原因。某基线常量不使主量失效。不计算p值、pooled rho、拟合、阈值或路由收益。 |
| 输出与预算 | 24行、逐点pair/来源、25格、seal、JSON/CSV、实际成功阶段计数和身份均保存；拒绝覆盖结果目录，异常输出保留。根caller负责600秒timeout和child RSS/全部外部控制前后核。没有程序内1GiB硬限或性能优越性承诺。 |

## 前审修正与人工证据

初读中提出三项具体合同缺口，均在真实执行前修复：标签候选身份未联核；空共同域缺明确status；缺point/pair访问计数。最终源码逐项核到候选/配额检查、null状态和来源/点/pair计数。它们是实现准备修正，不是从真实结果中挑规则。

生产作者的V1人工39项通过后，另发现失败途中已解码计数应逐项更新；旧源码/检查器保存在pre_counter_revision，最终V2再通过39项。前审没有把同作者自检当独立审计。

本审查者另构造不同的三维点、非共同点、不均衡来源数，以手算分数检查pair→point权重和共同域分母：两端均值7/6和143/48，差−29/16；这些都是**人工数据**，不是项目真实分散值。连同基线正负、25格、同组零、空域null、平均秩ties、负相关/常量/n<3，共26项在最终生产源码下PASS，实际UTC和源码身份见scalar_check_receipt.json。不导入独立核验器或共享其数值函数。

独立核验器作者自己的人工检查与生产人工产物接口集成见其准备回执。本审查只阅读该核验器的导入、常量/CLI/run、seal和身份/比较接口，以及准备文稿和回执；没有读取或转发其dispersion/query_measure/build_measurement等数值函数体。核验器没有导入生产数值函数；这支持作者独立性分工，但不是进程级文件访问证明。

接口审查发现核验器最初对associations.json只期待rows，而生产还含固定interpretation字段；已要求按真实接口核明确字段，不把此准备期误拒伪称真实实验失败。其最终人工集成和源码身份绑定在本回执。最终核验源码下46项独立作者人工检查PASS；integration_v3于UTC06:49:03.621081–06:49:03.840864全人工链PASS，30,585项精确、1,080项浮点检查，最大差8.881784197001252e-16，且显式人工root/32输入与来源身份已核。这些不是实际资料效果。早期人工runner括号语法错误发生在执行前，原失败已保留，不伪称执行成功。

需要披露一个准备期范围偏差：独立作者的integration_v1外部人工CLI漏传--root，沿用生产默认主项目，UTC06:47:57.736490–06:47:57.749156实际读了一份真实评分前selection JSON字节作SHA，首项与人工manifest不匹配即停止；CSV/JSON解码、score读取、测量行均0。原人工回执的“real_input_files_read=0”是错误假设，另有scope_correction.json纠正且旧记录保留。因此不能说整个团队本轮准备完全未碰真实文件字节。integration_v2已显式人工root，因人工fixture只有24行与核验192条件合同不符而拒；v3仅补人工非main条件后通过，真实数据与最终核验源码未因此修改。上述是人工环境/fixture错误，不是S14C科学关系的负结果。

## 实际范围与后续交付

本审查读取代码/设计/准备文稿与人工回执；真实S14B CSV行、S14A特征表、S12逐query标签、NPZ payload、RGB/GT读取均0。审查者仅运行人工纯函数，不运行真实生产/核验入口。没有新的文献命题，此前同一阶段已完成的技能与定点原文检索足够，不机械重复；继续应用Supervisor idea-evaluator的可验证范围及Claude scientific-critical-thinking的构念、混杂、缺失、相关非因果原则，不调用Claude模型/CLI。

真实执行成功后，根仍需报告全部24行/8组、共同域覆盖、重复选图与重复x计数、任何缺测query身份及原因、负向或不确定现象，并取得独立全量数值回执。点/pair和检查次数不叫独立样本。若失败，保留原目录与身份后排查，不扩大数值容差或翻转相关方向。旧S14A/S14B与冻结成果保持不变。

