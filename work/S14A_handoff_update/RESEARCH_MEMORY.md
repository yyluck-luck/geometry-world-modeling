# 当前研究记忆

更新：2026-09-06，S13独立数值及成稿复核已完成；当前进入S14候选/输入准备。每30分钟科研检查与接续任务已启用，仍没有新方法有效性或完整视频证据。精确时点见RESEARCH_LOG.md；原始事件只追加到research_events.jsonl。继续工作前读本文件和最新日志。

## S13完成与S14当前接续（优先于全部历史下一步）

- results/S13_oracle_headroom_retry01/run_metadata.json已核为completed：UTC2026-09-06T02:48:28.386855至02:48:29.863422，候选封存02:48:28.447459，解码前标记02:48:28.565916。该完成事件此前未及时写主账，本轮以运行元数据为时间来源补记，不能写成刚运行。
- 24个已见查询，主A0P0/stride8，三池各选四；独立bitset实际枚举164328个组合，72个池最优摘要及48个当前分数的整数/ID/tie精确一致；query等权Fraction均值，派生门1e-12、最大差1.0269563e-14。独立审计UTC03:20:17.724135–03:20:19.519370完成，全部组合分数另存。源14池内余量S7test2.732103pp、S8test6.349001pp；姿态14为1.593045pp、10.053341pp。Oracle使用测量答案并放松原NMS，不是纯NMS误差、可部署收益、视频或创新证据。
- 默认results/S13_oracle_headroom保留UTC02:46:33的数组读取前冻结路径失败；V1冻结保存在docs/S13_ORACLE_EXECUTION_FREEZE_V1_RETIRED.json。修正后V3静态检查17门通过，V2冻结SHA b11569862df2af20af64fb06d3ba7324fe441ae2a6e9297d0750a9f0527028fb；当前runner SHA05f354207744a0659bd4a9a743e6e58137b4e9f8d6d22e2b8a83548c144d7fbf。静态字符串/结构检查不等于不同作者的数值复核。
- 协议偏差：设计写绑定S12 summary及独立审计，实际52输入没有直接绑定这两项；新审计只事后核现存文件与S12审计匹配，没有修复原事前合同。原S13环境版本与结束源码身份未存，仍披露限制。结论是数值PASS且协议偏差已披露，见docs/S13_INDEPENDENT_AUDIT。
- 本轮并行3 agent分别做独立S13整数bitset重枚举、带原文检索的新候选审查、交接文档事实审查。根维护时间账本和当前文件夹交接总览。使用Supervisor idea-evaluator与本地Claude科学批判/头脑风暴SKILL说明；没有调用Claude模型或CLI。
- docs/S13_RESULTS、reports/S13两CSV（48逐query策略行/6分层）和差距PDF/SVG/PNG已成稿；不同报告作者1707字段/事实检查通过，一处14池并列范围措辞已修。PDF有Poppler字体类型警告但独立渲染无可见缺陷，非阻塞项；数值和图表未改。S12审查回执旧MD哈希另存docs/S12_MANUSCRIPT_HASH_ERRATUM_2026-09-06，旧文件/ZIP未改。
- S14定点候选评估完成：12搜索、3问题组、5直接近邻+2背景、7原文快照。C1优先相对姿态回退的受损风险预测，C2备选跨图冲突，均只允许前置诊断；门控、LTT、MVS一致性已有先例。见docs/S14_INNOVATION_CANDIDATES_REVIEW。独立审读中提出同信息/同GT监督/同容量学习门控基线与场景级iid风险条件，两个agent服务403后正式补充文稿未落盘，根将据已有材料接续，不冒称已完整完成独立审查。
- S14输入只读清单已保存work/S14_feature_feasibility/inventory.json，JSON与NPZ头核查完成，未解码预测/评分数组或产生特征/新选择；最小方向是6份评分前selection JSON加24份S12选择记录。所有query几何仍依赖已见query RGB，不能直接推广到生成前只有轨迹的接口。
- 定时任务automation已更新为每30分钟科研流程检查与接续，ACTIVE，绑定原聊天；没有新增重复任务。每轮按docs/RESEARCH_WORKFLOW_CHECKLIST.md核技能、创新反证、实验、工具检索、多agent和记录，然后继续实质工作；默认重要变化才通知。电脑和应用需运行，不能将设定频率当历史每次准点执行的证明。
- 下一步：完成S14输入合同和候选独立审读的落盘接续；冻结最小GT隔离特征提取器并独立核查，先只产诊断特征不拟合/路由。新训练/校准/测试按新物理场景预先划分，与同信息/监督/容量普通门控对比。旧24查询只作探索或软件核验，不重跑成功S4–S13。

## S12历史接续（S13以下旧状态已由顶部更新取代）

- 先读docs/S12_EXISTING_EVIDENCE_AUDIT与S12_COVERAGE_NOVELTY_SCOUT。现有192地图条件均20来源→14唯一候选→姿态排序/NMS选四，票权只影响候选形成；旧全20姿态对照候选数量不同。同候选ID下票权不再进入NMS。已有分数/字段新复算只读JSON，未产生新pose14选择。
- 定点检索15查询、五核心原文/44文件SHA。COVRAG、I3DM当前v2（3+last共4）、AnchorWeave已有新增覆盖贪心，BoostMVSNeRFs是更早代价体先例。普通greedy coverage不能作为当前C0唯一论文创新；docs/S12_COVERAGE_IDEA_EVALUATION已独立63项+论证审读PASS，终稿SHA0609fd79acbe54ca54ce8e82f2556f12f624fc8185014aeec3df10ccd2fa8ff2。C0未运行，不当数据否定，也不否定所有新的表示/机制。没有新全领域综述、Claude模型或缓存B恢复。
- 新诊断协议docs/S12_MATCHED_BUDGET_PROTOCOL.md（最终含机器合同SHA60eebbfe82a4661917d3d4a887c847e39bfb23245b48452bea737a9adda78e60）：全部24相关已见query，只24新pose14 decision_trace；从20个FP32姿态距离排序取14、ID升序counts各1、原NMS/前5历史初阈值，4输出。只重算原20距离/排序及6阈值校准，不额外重跑旧all20 NMS；原steps没有完整pair表，新路径需原FP64 geodesic实际计算并保存。两方都用预测几何，只区分来源记忆筛选与姿态筛选，不称有/无几何或同计算成本。
- 主格A0P0/stride8；S7dev4、S7test8、S8test12分列，不合并场景，其他7图/密度格完整列相关敏感性。192配对行不是192新query。先封存全部24新选择，再只解码旧48scoring NPZ的support/valid，核两密度相同、复算768旧读出/48上界，再给新ID评分。分母valid，50mm实测支持并集，不是视频质量。GT历史已见，必须称事后探索性补充。
- 最终scripts/run_s12_matched_budget.py SHA ccc36d5a7a0efcce82c7354818b878e91464e3822b680259e6dd03d504e7f6d5，5原函数完整AST保持。独立前审PASS后根于UTC23:03:39.093102冻结，SHA0a4be192f46bea9f7b717e5fe66fdd74f053f5fcb8f2af9c47a3c6eb71921988；4源76输入9审查。design-only V1保留，不作最后批准依据。根120项JSON/NPZ头检查只读结构，作者及独立纯AST预检都无新选择。
- 实际results/S12_matched_budget UTC23:03:49.724151–23:03:50.572765一次完成；24新decision_trace、2029距离，seal23:03:50.513138、首decode23:03:50.515653，峰值234258432字节。768旧率/48上界严格复现，192配对；没有性能比较。主A0P0stride8：S7test源14 91.907175980% vs pose14 94.246136664%，差−2.3389606843pp（0/4/4）；S8test 80.281293398% vs75.898373732%，差+4.3829196654pp（11/1/0）。源/姿态同样用预测相机，不能说无几何；也不是一般新方法或视频优越证据。
- 不同作者审计首轮UTC23:04:17.048807–23:04:17.747241 PASS23647，2029距离独立方程精确、24全NMS/48support/768旧率/192差和两ZIP91成员通过。审计器结果前已准备，SHA9df235e2a45680571f46027cd25948e32c1d9f7e0dd086c505106ba66b9dc2c9，距离/ID/整数精确，均值/pp统一1e-12预定门；没有失败。中文docs/S12_RESULTS与4CSV已生成，初次8249门文稿核查发现的解码前时间标签已闭环修正，最终文稿核查为PASS_AFTER_TEXT_CORRECTION；只改三处文字，CSV未变。
- S12用户交付已于China 07:29:27完成：outputs/选图是否有用及ip-/选图是否有用入口、151载荷/153成员ZIP，4238688字节、SHA1727aed902ac3d40feddba80a4297305399d5a786fdbb1c515478e8dc48c40ae；逐载荷CRC/SHA/大小和原源未变通过。归档完整性不等于新机器执行或完整视频生成。
- S13只完成设计，尚未读新评分数组/执行枚举：主A0P0/stride8、全部24已见query，分别枚举来源14、姿态14及全20池的四图组合，量化当前选图距知道GT后的支持上限的余量。见docs/S13_ORACLE_HEADROOM_DESIGN；oracle不是可部署选择、新颖性或视频证据。
- S13来源/候选域只读预检已通过：24主行、48候选池、48份NPZ header共528门；support/valid载荷解码0、组合评分0。首次过严地假定NPZ只含两个字段，核实既有额外字段后仅修正header成员判定并重跑；见results/S13_oracle_headroom_preflight/receipt.json。尚未独立审查或冻结入口。
- S13入口scripts/run_s13_oracle_headroom.py已静态准备：候选池和组合hash先封存，随后才读support/valid；预定164328个组合，不跑renderer/model/NMS/投影。只完成py_compile与--help，尚未运行主入口或解码数组/产生分数。入口SHA1b627823504c7b647db3841ed4fd72338c5354787c832490a517602bcde046b7。
- 下一步独立审读S13设计和完整入口，核oracle边界、组合计数、输入身份与汇总逻辑；通过后才写执行冻结，暂不开发新的路由/覆盖候选凑创新。

## S11历史接续记录（后续已进入S12）

- S10候选src/s10_vectorized_renderer.py SHA3e079d0bbbaed962b24bce599a5cf7198b6bbc2891ac3c91761f4ea5c4f0e521与原选择器保持不变。地图域预先冻结后新增168候选调用，继承并重开S10的24条件，总192条件三数组C字节及完整trace通过。仍为两场景、24相关已见查询、48地图变体，含S7开发段，不是192独立样本或新泛化验证。
- 地图域UTC21:58:21.216269冻结，21:58:21.425345–21:58:47.197244执行，预算墙钟25.771907秒、峰值461340672字节。不同作者重开192条件576对数组与完整trace；另同作者不同脚本独立累票、按保存距离回放NMS，均通过。状态是重建身份摘要，未重新算相机距离。见docs/S11_RENDERER_REGRESSION_INDEPENDENT_AUDIT、S11_RENDERER_REGRESSION_RESULT_AUDIT。
- 来源域30人工条件：六张A0P0/stride8地图各q20，追加最小缺失/删末项/逆序/只留0/只留0,1,2各6。每条从原映射独立复制，几何、相机、K、20历史、counts不变，不是物理新观测或实际merge轨迹。原renderer不读来源，参考用严格实参守卫回放旧缓冲并重新选图；候选实际渲染。共30候选+36参考回放（含6原来源baseline），原renderer0次。
- 来源UTC22:09:25.636205冻结，22:09:25.679556–22:09:35.609286执行，预算墙钟9.929738秒、峰值268025856字节。30两臂全同，18错误实参全拒。前三组18编辑中陈旧trace拒12（6/6/0），有序ID改3/6/0；逆序六条完整trace没变。两欠源组各6返回相同1/3张，不验证完整视频消费者。上下文含占位latent/embedding，不是实际模型特征。
- 来源不同作者审计v2 UTC22:10:28.505785–22:10:30.063167 PASS：60实际render/180数组、60实际context/300数组对独立重建值bytes同，30映射、66次票权/保存距离NMS回放及三ZIP75成员全核。六baseline仅trace/身份无另存NPZ；逐调用实参未另存，守卫执行仍结合冻结源码/运行记录。初次审计器整数键标签TypeError保留，只修str(k)，不改实验。见docs/S11_SOURCE_REGRESSION_INDEPENDENT_AUDIT。
- 执行前新记录器工厂将旧S7末尾两处硬要求4改maximum，恢复后完整AST全同，原文件/实际选择器不变；记录ID必须匹配实际返回。尺寸整数、负对照逐次存证等也在冻结前修正。两域实际实验均一次完成，失败准备稿与审计器保留。
- docs/S11_RESULTS.md经独立108项文稿核查PASS，SHA8176cbff8b325ee88795b6d848e728ff190a93945e44daacc8b40999fa28fad0；已补证据链接和占位上下文范围，用户交付outputs/扩展输入验证及ip-/扩展输入验证入口已完成。没有新模型/原图GT解码/计时，勿重跑成功S4–S11、下载权重或覆盖旧报告。S10的7.78倍只限原24已见查询的计时范围，不因S11通过而扩张。固定NumPy2.3.5，不声称跨版本正确。
- 下一阶段回到科研用途：结合已有同预算、同NMS对照与已核文献，分析几何记忆何时帮助选图，再按Supervisor-Skills审查具体用途、新颖性和最小可反驳实验。停止无止境软件回归；不恢复已暂停的固定查询缓存候选B。新方法需与S10普通优化基线比较。新一轮检索/idea-evaluator尚未开始，不写成已完成。完整VMem、视频质量、真实学生工时/会议/最终提交仍未完成。

- S11证据于2026-09-06T06:23:19+08:00完成归档：41030015字节，712载荷/714成员，SHAb6fa04ffdccf22b2e43ece734f59371b8c6f7a391d01978e91649469caf04783；全部CRC/SHA/size及原文件未变通过，入口47链接与快捷方式通过。仅归档验证，不是新环境执行。docs/S11_DELIVERY_RECEIPT；ZIP冻结后主账追加完成事件再同步用户快照，旧S10 PDF/ZIP SHA保持。

## S10历史接续记录（后续已有S11，以下下一步不再作为当前任务）

- 候选src/s10_vectorized_renderer.py SHA3e079d0bbbaed962b24bce599a5cf7198b6bbc2891ac3c91761f4ea5c4f0e521只用NumPy批量化原polygon像素内循环；工厂恢复原循环后AST全同，保持投影、顺序、16边形、整数像素、epsilon1e-15和strict depth。原Python float与FP32比较身份不改，固定NumPy2.3.5；显式FP64会破坏相等。没有缓存历史查询或读参考代替运算；普通工程优化，不称新算法创新。原kernel SHA35825a…保持。
- 独立人工设计36手工+24seed20260906=60案例，baseline_v2补epsilon错误变体后先过；UTC21:08:55.878852设计冻结后，21:09:17.868679–.988459候选60/60三数组bytes相等，5错误变体均拒。另重开120NPZ、180对数组1046检查过，4NumPy官方原文与探针核过。人工证据不是实拍、不是形式证明。
- 独立静态预审PASS，根UTC21:18:19.793677另冻结12源码/同S9的52输入及11审查证据；docs/S10_RENDERER_COMPARISON_EXECUTION_FREEZE SHA db22d71b37c9a44ece98008f8ff422886a7bdc604efd79d6f0000b55f1532204。协议SHA b78d2f079e61bab4c92b7704bbbd632b8daa051b4c68ca6e4526b761d116a1bc；runner 00dbae5db3c7a09dca78a428951db2074103b54d8f2c23a4daea17b7e6a96554。
- results/S10_renderer_comparison实际UTC21:18:19.892873–21:22:37.828402，257.935542秒，峰值296910848字节。48初始正确性于21:18:56.836360全过，再48预热，21:19:32.903664开始240测量；总336调用全部三数组bytes（含±0）及完整票权/配额/排序/NMS/有序ID门通过。每次336 render+336 trace都保存；没有计时重跑或失败实验。双方相同observer、未插桩完整get_context_info，小占位上下文，CPU8线程。
- 预定主估计160297341076/20612083586=7.77686255769291；原均1335.811175633ms→候171.767363217ms，耗时减少87.141344%。S7比7.3774861966、S8比8.3023090901、AB7.7893475706/BA7.7643521665。24查询五次中位数比6.5833432503–9.1313452986。全部120正式对AB/BA60/60，单查询3/2或2/3。只限两场景24已见查询、六A0P0/stride8/160图，含S7 dev，不是新泛化、独立N120、完整VMem速度或视频质量结果。全进程内存不是两版内存比较。
- 不同作者results/S10_renderer_comparison_independent_review UTC21:23:03.115900–.506894一次PASS12738，重开336NPZ的1008实际数组对24旧参考bytes全同，336trace106050叶全同，5组/24query/120pair统计重新计算一致，12源52输入/672文件/两ZIP通过。未导入生产验证或汇总。docs/S10_RENDERER_COMPARISON_INDEPENDENT_AUDIT。
- 另比较作者不同脚本results/S10_renderer_comparison_audit_v2 UTC21:24:41.707738–42.487010 PASS224547，另独立累票24缓冲并从已保存距离回放NMS，完整summary与原SHA ccb5c9bccc50c9184a17c5dee48c3fcc688a479ab318e7d613316c63f3106ce4相同。首次审计在427项因docstring去缩进比较错误停止，旧目录保留，只修审计器，原实验/数值门未改。不得称不同作者。未保存完整运行对象的状态相同仍依赖执行指纹和代码，而非事后重建。docs/S10_RENDERER_RESULT_AUDIT。
- reports/S10三页《保持选图结果的本机提速实验》已用本机XeLaTeX编译，全部3页最终渲染视觉PASS；图例移到绘图区外、表格列宽修正。全部24query图（五重复中位数及range非CI）、五组/24query/120pair/336call CSV与完整中文docs/S10_RENDERER_COMPARISON_RESULTS.md。报告SHA ff7cd065169e481e3ad3c5ae0380a43adfa050757633311d6c859b60121483b0，qa.json实际记录。
- 独立文稿审查docs/S10_MANUSCRIPT_REVIEW于UTC21:31:32.377875–.386492通过8192项：7187CSV字段、117MD/TeX数字、SVG48点/96范围端点；MD SHA323304328dd36b19500c184c2bdd937198235d0ae8c2c0fb72b4e2d4ff63a47b，TeX ed817229544f11bc858b8fae31b94f991a0cc2d798f517c380868ea427ab8ef5。此前两次审稿器自身CSV顺序假设/二进制印刷舍入误拒保留，只修审稿器，用Decimal核正文正常半入；报告/实验未改。无剩余必修项。
- 下一步另立更宽的软件正确性回归：已有四图/两档密度及来源变化，保持S10实现和基线，结果前冻结具体选择和界限。这个方向是工程候选适用性，不扩写论文创新。真正省计算方法若再提出，必须以S10更强普通实现作基线并重新做近邻排重。不要重跑S4–S9模型/下载/评分或这次成功计时；完整VMem/课程真实活动仍未完成。
- S10交付于2026-09-06T05:34:29+08:00保存：outputs/渲染提速实验与ip-/渲染提速实验入口，三页PDF/图/完整CSV/原记录/审查齐全。新ZIP18233684字节、1019载荷/1021成员，SHA bff4ca275891391319a0ae0214bcea8d7f18a25679b39db6625939c69cb78e63，全部CRC/SHA/size与源不变通过；仅归档验证不是新机/模型执行。docs/S10_DELIVERY_RECEIPT。ZIP保持冻结快照，主记忆/日志在其后追加交付完成事件并同步用户文件夹。
- 已实际读取当前automation.toml：heartbeat仍ACTIVE，实际INTERVAL=10分钟（比历史记忆30分钟更新），不修改/重复创建。依主记忆接续，只有实质变化通知。

## S9历史接续记录（后续已有S10，以下下一步不再作为当前任务）

- S8证据ZIP已做本机隔离复算：run_04 UTC20:26:06–20:26:19完成，14253数学检查通过，五份输出与原审计字节SHA相同，9个OS/Python探针通过。复用既有.venv、允许祖先目录metadata，禁止原数据/实验源码字节回读和网络；不是新环境安装或模型/renderer/23803项全树GT派生重跑。前三次路径/隔离适配失败保留。docs/S8_PACKAGE_INDEPENDENT_AUDIT；新工具ZIP359312字节，SHAf071b07924cb5a99ff71180712b692c8fc1fb8cb748f9aca5611399c6f3f81fe。旧主ZIP不改。
- 候选B经idea-evaluator完整复评和独立审查：Accept with Revisions，仅允许前置诊断；不开发当前固定查询/固定来源/点组证书，不称已经新颖或加速。五核心原文Teller1993/Yi2003/Gkorgkas2015/VMem2025/COVRAG2026及近期筛查、39来源SHA完成。普通缓存/保守证明/精确top-k均已有强前例；新组合价值未知。docs/S9_B_NOVELTY_EVIDENCE、S9_B_IDEA_REASSESSMENT/REVIEW。
- 官方真实调用每批先选择后生成/建图，context=4时只取批尾1pose。相机/焦距均值/来源/点数可能变化；get_transformed_c2ws仅固定翻轴，不是地图依赖变换；原merge不更新旧点位置。四人工桩调用检查在UTC20:30:55.943–20:30:56.055通过，独立94项只读核对，非真实模型/renderer/命中率。所有7个stub与翻轴前平均pose范围写明，文稿修正后PASS。docs/S9_B_WORKLOAD_APPLICABILITY/REVIEW、S9_B_CALL_TRACE_REVIEW。
- 重要文字更正：原配额n=min(14,来源数)，当前调用每个入选来源仅1次。S7/S8各96个official查询记录均20来源→14不同候选，candidate_no_nms各96同；两all20控制各96为20不同候选。全768保存读出均0重复、0已保存距离并列；5272项只读核查。旧稿“并列含重复副本”不能作为实际现象解释，旧数值/源码/冻结PDF保持，另附docs/S9_B_CANDIDATE_QUOTA_CORRECTION及768/192CSV。
- S9组件计时已完成：docs/S9_COMPONENT_PROFILE_EXECUTION_FREEZE UTC20:39:15.152814，SHA8e9c0a84cea827cf11d01f793e21ce46a9c2ce579206cc6678d3d006805fa9cd，10源码+52输入。results/S9_component_profile UTC20:39:15.255981–20:42:24.365026，189.109秒/峰值257933312字节，24warmup+120测量=144调用严格输出回归全过。S7/S8各12已见query，仅stride8/A0P0，含旧dev；CPU8线程/FP64几何/默认FP32sort/160平方。原renderer真重跑、没有新模型/GT/PNG。平均总1306.492204ms，renderer1293.503280ms占99.005817%，votes11.777447ms占.901456%，sort+NMS1.083251ms占.082913%，其他.128227ms。是插桩observer与占位context的组件成本，不是B加速或完整视频延迟。
- S9独立汇总results/S9_component_profile_audit_v3在UTC20:46:56.098447–.159003完成2671项检查（2043重算/386完整性/166metadata/72保存trace/4AST），262汇总标量及summary文件SHA全同dfa2fd1d423a3f310a9a6f00b9668fde3526c8944a2c888d11ff33e0bede57de。24初次保存trace/7671标量直接比较；144新render未逐次保存，独立对其只核原运行旗标+冻结验证源码，不冒称重新比较144套新render。前两审计器失败（浮点逐项求和、docstring去缩进）保留，原容差/summary未改，计时没重跑。结果表25单元及解释33检查PASS；最终完成段由根任务按回执更新。
- 下一步为保持相同输出的渲染工程对照另冻结协议。先定位CPU圆盘光栅化优化，保证动态相机也能正常计算；普通向量化/缓存按工程改进而非新算法创新。不要重跑S4–S8模型/下载，别把已见S7/S8称未见验证；完整VMem和真实课程活动仍未完成。用户新入口ip-/研究方向与耗时诊断对应outputs/下一步研究方向，S7/S8旧入口附明确候选文字更正。
- S9成果04:51保存：新证据ZIP6567480字节、129载荷/131成员，SHA3cf687d82190d3f30f7568508c1e1d5390d63f606c4b899ac42ae747e613a4e2；全部CRC/SHA/size通过，只有归档验证，不称新机运行。docs/S9_DELIVERY_RECEIPT。主记忆/日志用户快照在归档后继续更新，旧ZIP保持冻结时点。已再次实际读取automation配置，持续推进任务仍heartbeat/ACTIVE，不重复创建。

## 用户与目标

用户是科研新手，要求简单中文、自主在本机推进全部项目、维护实际时间与行动记录，不再逐步询问。指定HKUSTDial/Supervisor-Skills，可用电脑/本机文件/适用skills和检索。项目目标为Geometry-aware World Modeling，帮助AI生成空间漫游视频时记住同一环境。原proposal和旧稿在上一级目录，不能覆盖。未授权给导师或他人发送消息。用户明确只使用Claude本地skills，不调用Claude模型；当前从未调用Claude。可用本机Draw.io与XeLaTeX，已确认实际安装。

设备M3 Max/64GB，暂无远程GPU；Torch MPS可用，CUDA不可用。课程真实学习每周至少12小时、至少4次导师会议及纪要，报告截止2026-12-28；没有已完成活动的证据，不能把自动运行计为学生工时或会议。

## 已完成且验证的实验

- S0/S0b：各216人工记忆配置；原版首次写入位置保留，匹配仅加来源。12索引诊断分离默认Octree漏查。合并取搜索顺序首个合格点，不是最近邻。21.05mm/19.88mm是离散锚点偏差，不能称连续表面误差。
- S1：完整官方最终选帧路径，192合成配对配置并重复验证。8共享来源的72个受扰动配置全部不换帧。20分区中2cm只有低分辨率1/6换、高分辨率0/6；40cm同4/6两档换并降低辅助参考覆盖。小误差损害检索的证据不稳定。S0/S1是分开实验，不是同实例完整传播链。
- S2：真实TUM freiburg1_xyz已完整下载，448204271字节，SHA256 a0236d97b8c30cd93b653656d2b6c293ff7c982a4130ef2a1a8beecdb124ef98。798RGB/798深度，792配对、789有合格位姿；24帧QA通过。有效观察26.59秒、单一环境。深度除5000，不重复尺度修正；Kinect/轨迹/标定均非无噪三维真值。
- S3：18案例、36地图、72配对查询条件、144查询×检索宽度记录，12个实际相机查询（测试8）。22:41:40到22:46:45实际运行，0异常，独立4544检查通过。另独立从NPZ复算72记录，核心源码hash一致。

S3主结果（test块1/2、stride16、原始测量）：两档宽度均0/8最终换帧、支持变化0；平均逐查询中位深度差30.289→27.992mm，平均逐查询MAE260.856→259.265mm；共同像素平均仅3.908%有效目标（450–646像素），自身覆盖10.845→10.585%。不能只说几何更准。stride24原始测量3/8换帧，支持只+0.02098百分点；人工20/50mm条件有正有负。nearest_pose4支持93.820%高于本轮VMem组件90.837%，但它无NMS，不是单因素归因，也不是视频质量结论。

S3事后残差诊断覆盖全部8主查询，不改冻结指标。4235common像素中≥100mm为1392→1366，≥500mm881→864。点投影同格不保证同物理表面，边界/遮挡/位姿为候选原因，未确认唯一原因。

## 当前研究判断与文稿

暂不扩展复杂GeoTrust gate，不把simple frame_mean当创新。原版已有清理、置信度/深度过滤和来源关联，不能称无筛选。更新位置不自动等于选图变好；目前没有完整视频证据。S3使用实际Kinect输入，绕过CUT3R与完整上游清理。

新结论：docs/S3_RESULTS.md。完整英文正文：docs/TECHNICAL_REPORT.md；7篇文献及fresh引用审查：docs/LITERATURE_VERIFIED.md、REPORT_CITATION_AUDIT.md。逻辑/文字审查：TECHNICAL_REPORT_REVIEW.md。原proposal交付未全部完成，见PROJECT_DELIVERY_TRACKER.md。

工作区outputs中6页本地实验研究报告.pdf与8页中文科研汇报.pptx已完成逐页检查；英文报告/复现包/记忆快照还需在最终本轮结果到齐后同步。旧outputs文件保持。

## S4真实模型已完成

完整权重2994205002字节，SHA256=7a7d83e47f822e040980c8f5aff4c15aa94366d469d3ceae51fa30cc2f62327d。无需下载。官方独立CUT3R提交8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf，224 linear中间检查点，不是VMem/final512。

实际成功CPU/MPS输出分别results/CUT3R_cpu_2frames_signedrope_sync和CUT3R_mps_2frames_signedrope_sync，23:13:07/23:13:20完成。748443655参数全部匹配、两图14输出数组有限；设备间全部原数组atol=rtol1e-3通过。前向CPU0.878秒、MPS6.284秒，单次无预热，不排名性能。运行加外部signed-RoPE及阻塞输入搬运；源码未改但执行已适配。原CPU负索引失败、原MPS输入搬运异常保留，见docs/S4_RUNTIME_AMENDMENT.md。不要重跑已完成pipeline。

S4协议+head修正均在模型输出前冻结；runtime修正发生在失败后。只CPU首图拟合尺度1.1583864704；第二图留出37325像素MAE32.324mm、中位24.368mm、p9067.788mm、30mm内55.721%。相对旋转差0.929度、平移向量差19.836mm。MPS共享CPU尺度。仅一对图，不是benchmark或视频结果。

正确S4完整结果results/S4_cut3r_pair_verified/，23:14:21完成。先前results/S4_cut3r_pair/因归档相对路径失败，status=failed，保留不能作为完成结果。报告docs/S4_RESULTS.md；两张图已逐张查看。独立185项复算已经通过，见docs/S4_INDEPENDENT_AUDIT.md。

## S5已完成

使用S3完全相同的三块各24张RGB，每块独立进程、reset全False、update全True。CPU三块23:20:38–23:21:35完成，504数组有限，峰值均6.425GB，无16GiB预算超限。results/CUT3R_S5_cpu/sequence_metadata.json与raw_outputs_verification.json。

S5评分23:22:00完成：results/S5_cut3r_sequence。每块首图单一尺度1.15842060/1.12772993/1.12851093；主8图（B1/B2尾4）平均逐图MAE72.120671mm，中位差均值50.170819mm，p90均值148.629168mm，30mm内35.1766%，AbsRel6.5396%，相对首帧旋转差2.052259度、平移向量差60.388853mm。69个非校准帧描述包含主8，不是新增69个独立样本。所有72图和曲线已逐图查看，误差非单调，不从S4/S5不同图片的数字差推断长度导致漂移。

S5独立4516项核验通过，原depth重建mask/目标逐值一致；S4独立185项通过。docs/S4_INDEPENDENT_AUDIT.md、S5_INDEPENDENT_AUDIT.md。参数/输入/保存输出FP32，但官方encoder内部RoPE使用FP16，见S5_PRECISION_CLARIFICATION.md；非负FP16适配与原fallback CPU/MPS各自逐值一致，未跑CUDA。

英文S4-S5补充docs/LEARNED_GEOMETRY_REPORT.md，3条文献fresh-context核验通过docs/LEARNED_REPORT_CITATION_AUDIT.md。旧S0-S3 TECHNICAL_REPORT/PDF/PPTX保留阶段快照。新4页中文补充PDF已逐页查看，修正嵌图字体大小；36秒MP4完整72帧对照回放已核编码并抽查3处，不是新视角生成。outputs和reports/S4_S5将同步新交付。

## S6已完成运行与独立数值审查

协议docs/S6_MEMORY_BRIDGE_PROTOCOL.md已在推理前冻结，SHA03af5253e22e7f82064edce5acd3c18f7ca1ebe294eab790e7fdc85eacf02392。使用224 linear self Z＋已知裁剪K＋预测pose重建XY；无VMem完整512DPT/全局优化/clean，非完整生成。建图选图纯首图预测中位数归一化，不读测量depth/GT；全部六案例23:55:19封存后才测量评分。

results/S6_cut3r_cpu模型23:45:16完成。前20历史update=True、尾4False；60历史帧420数组与S5严格相同，查询潜在state两字段每次与历史锚点一致，独立1945检查通过。state原张量未保存，独立审查为记录与代码验证。此前S5结果不覆盖。

results/S6_memory_bridge在23:51:09–23:55:21完整运行6案例12地图、24配对条件、48条件×宽度；实际查询12/主测试8。测试stride8平均逐查询共同像素MAE367.526→347.882mm，中位差均值117.809→101.300mm，但共同像素平均仅2.749%有效测量、180–288像素；自身覆盖8.804→8.096%。两档宽度均4/8换帧，参考支持91.907→93.272%，+1.365百分点；最近预测姿态4图对照93.472%仍更高。stride12支持+1.663百分点，但几何MAE441.308→447.767mm、中位差162.173→265.968mm变差。以上已通过3453项独立复算；支持和mask逐值相同、投影depth最大差约4e-15m，详见docs/S6_INDEPENDENT_AUDIT.md。不要把支持代理当视频改善或一般化优越性。

新一轮deep-research任务书docs/LITERATURE_RESEARCH_BRIEF_V2.md固定RQ与3个清洁上下文独立视角，三视角与定点补充29项语料已归档，正在串行合成综述。之后按idea-evaluator区分已被对照否定的强主张和仍未测试的方向，再用tech-paper-template核对逻辑。

用户找不到照片，已把实际72张原RGB逐字节整理到工作区outputs/实验用的真实照片_72张，并在ip-目录建立同名入口；全部SHA与S5冻结清单一致。完整798原图在data/tum/rgbd_dataset_freiburg1_xyz/rgb。

S5复现包221952929字节、538payload；核心离线独立核验通过，附加help检查找到两个下载器忽略help的问题已修。旧ZIP不改，新成果连同修复进入下个新包。历史JSON绝对路径保留，不包含raw/weights/完整clone；仅Markdown副本规范化路径。S6当前默认项目内路径完成，外部--data/--runs结束归档仍有relative_to限制，未宣称任意新机端到端成功。

## 持续接续

已按用户全流程一直跑要求创建当前任务每30分钟heartbeat，ID automation，ACTIVE，仅有实质进展/失败/需实际动作时汇报。不要重复创建。自动可做工作全部结束后暂停；不能把完整视频或课程真实活动标成完成。

VMem权重本地不存在且访问受限，代码有CUDA路径；独立CUT3R已成功也不等于VMem全流程。后续根据已核验真实学习估计推进，不靠挑例或大扰动制造研究动机。

每轮完成/失败/纠正/转向通过scripts/research_log.py追加真实时间。已有原始结果和冻结协议不覆盖。源码快照保留运行时状态；workspace outputs只作用户交付快照，项目才是主账。

## S7已完成并通过独立审查

冻结01:03:17.688、实际运行01:03:18.258–01:05:23.096，协议SHA4484c8f08c27c94f3f4b6654f131faa72bb07c47efdf25e50426526d5d37e068。results/S7_event_replay共6案例24地图96地图查询384读出，仍12不同查询/主8。逐观测(frame,u,v)、A0/A1事件、P0/P1重放、原render和全部决定已保存；对角地图/来源/建图逻辑/票权/选择/投影严格复现S6。

独立9827检查（9147复算/663完整性/15metadata/2源码顺序）01:09:47–01:09:54通过。独立穷举核12路径每帧首匹配、24地图、96render到票权、384完整排序/NMS及支持；投影最大差约4e-15m。未重跑模型、光栅渲染、从原预测重构观测或从PNG重建支持；复用已独立核实S6测量并逐值核对。原环境、错误环境、filter schema审查失败完整保留，原容差不变。

主stride8 official四地图A0P0/A0P1/A1P0/A1P1支持91.907176/91.474634/90.639705/93.271907%；固定A0位置效应−0.432542pp，固定A1+2.632202pp，差中之差+3.064744pp。stride12位置效应+1.840910/+1.842940pp，交互仅+.002030pp，不能称普遍强交互。B2稀疏四查询A0P0→A1P0→A1P1的ID为[12,11,13,9]→[12,11,6,7]→[12,11,13,9]，轨迹负/位置正支持精确抵消；主密度B2四臂均相同。

只去NMS不保证好：A1P1主支持−1.283670pp、敏感性−1.458219pp；全20候选带NMS91.154065%、不带93.471823%。四臂common仅1.935790%/0.532697%有效目标，不与S6两臂mask的几何均值混比。S7_RESULTS与S7_REPORT_REVIEW通过84表格条目/384CSV核对；NMS措辞已改姿态（位置与朝向）。

25篇综述LITERATURE_SYNTHESIS_V2及独立引用审查完成，TTT3R额外微调/WorldRoamBench估计转折两限定已修；2篇仅官方原文摘录不冒称独立全文通读。原强均值普遍优越主张按idea-evaluator拒绝；候选诊断按benchmark-paper-template审查NOT READY，跨独立场景/消费者验证/独立新颖性未完成。

Draw.io30.0.4已真实导出并查看原生图；XeLaTeX已编译6页运行前假设报告，主文4页+2附录，逐页QA。reports/S7_design和outputs/研究机制图有.drawio/.tex/.pdf及日志；S6–S7新结果PDF5页已完成并逐页QA，S7新包398253550字节、1155payload，SHAe9c778e2946a25f5ea10f2ad563f4b222a220775e2ec0bc98914b32a7d1f0383；独立干净解包离线核验已通过，见docs/S7_PACKAGE_AUDIT.md。已完成的运行前假设文件保留历史快照，不覆盖成事后假设。

下一步：另立独立场景协议检验机制是否重复。本轮结果PDF、文献、机制图、复现包、独立隔离审查和用户快照已完成。不能把全部课程项目/完整视频标完成。当前没有活跃模型或实验进程；不要重跑S4–S7或下载已存在权重。

包的最终独立范围：68测试/4444S3/76份S4S5深度记录/3398项S6包内与10293项S7包内复算，141本地链接和23help通过；不将改变范围的计数冒称原套重跑。S6源ZIP内有201100字节轨迹副本，包内审查仅核其哈希，复用归档S5位姿，没有重做原GT插值。主包历史QA路径笔误已追加更正、原ZIP不变；最新文稿快照与主账比ZIP冻结时间更新。

用户入口：ip-/最新研究结果指向workspace outputs/新一轮研究结果；ip-/实验用的真实照片_72张指向原始相机照片副本。结果PDF5页、假设PDF6页、Draw.io原生图、LaTeX源、完整384项CSV、25篇综述和skill应用清单均已保存。已确认heartbeat automation仍ACTIVE；后续只在实质变化时通知，不创建重复自动化。


## S8新场景已完成并通过独立审计（2026-09-06）

全部新实验已结束，不再重复下载/推理/重放。唯一新增TUM fr2/desk相对fr1是另一物理场地与另一实体Kinect，仍同数据集/同类设备；全部3块test、每块20历史+4只读查询，12相关查询不是384独立样本或12个场景。

原包03:00完成，1893351095字节/SHA1a0756d72510a26e26e2a02bf0b6c69c2796619fca531e176fc2e5110173807c。V1设计SHA5b6563643d4deb69dd7f66789ebf0f0620666cac372858831aa96fd376186df6及首次失败data/cut3r/S8_fr2desk_inputs均保留：原GT20957行，有一个float重复键1311868229.576；七个位姿token仅文本不相同，不能断言物理位姿冲突。

V2于03:38:23.939设计冻结，协议SHAd4ae1781696f4918b65129b82f52698ab07b1642fdf744f74501187a96984431，docs/S8_DESIGN_FREEZE_V2.json。严格abs(t-d)<=.051全局邻域排31行，派生20926GT，最近两侧gap.1066999435>.100，旧全部采样/模型/指标规则不改。新data/tum/fr2_desk_timestamp_guard原行byte保留，另5932文件独立bytecopy；原源树与官方TGZ完整不变。派生GT SHA f19dc674dc43b6c4957038e1a22906122c19c60893e664dafb0e0abe537906ca。独立派生23803检查PASS，没用位姿/像素调规则。

取样03:41:11完成：完整2893配对后GT过滤，6合格窗选0/2/5；manifest data/cut3r/S8_fr2desk_inputs_v2/S8_inputs.json，SHA873c9ef3deae7a8caaa816620d0b5e803ea7ef277e90e316486810f0f80b83f7，独立1554检查PASS。72RGB03:41:38核验/原byte复制完成，3联系表根任务已全看，未换样；outputs/独立场景验证/真实照片_72张已有实际照片。GT/depth像素未用于选样。

最终docs/S8_EXECUTION_FREEZE_V2.json于03:43:00.566971冻结38源码/证据项+三测量文本。results/S8_cut3r_cpu_v2三块CPU03:43:00.669–03:44:16.148完成，504有限输出/查询只读全过，峰值约6.25–6.43GB；旧S6/S7核心源未改。results/S8_event_replay_v2在03:44:47.150–03:46:37.731完成6案例24地图96原render/384决定，全选择03:46:35.739942封存，GT位姿.742042、depth.765586才首次解码。首图评分尺度1.6318344742/1.9161179741/1.6838325796，只有封存后用于测量。

主stride8 official四图支持80.281293/80.281293/80.798944/80.817906%。P_A0=0，12/12集合与顺序不变；P_A1=+.0189618724pp，4/12换集合（全B1，2升2降8同），无order-only；A_P0+.517650437、A_P1+.536612309，主交互+.0189618724。B0/B2主四图不变。旧S7主A0负/A1正的具体模式未重复；不要用新稀疏负/正替代主预定检验。

stride12四图80.281293/80.264250/80.418673/82.190625%；P_A0−.017043241、P_A1+1.771951982，A_P0+.137379270/A_P1+1.926374492，交互+1.788995223pp；固定A0P0→A1P0→A1P1路径有序ID抵消/支持抵消/联合都0/12。主2升2降跨查询平均接近零，不称同查询机制抵消。候选去NMS主A1P1−4.232669694pp（2升10降），敏感性−1.050538937；全20带NMS76.234741%、无75.297582%，两档四图均同，仍只选4张。不能说去NMS/全候选一律好。

主四图共同MAE620.618497/650.077310/628.257566/647.849410mm；共同coverage2.209054%（86–330像素）；稀疏MAE742.340879/746.481678/740.755112/742.256933mm、coverage.691937%（36–89）。主对角自身coverage8.632588→8.178929%，共同中位差167.889748→193.660231mm。主支持小幅正但几何坏，不能单报支持改善。两臂共同coverage2.997990/.979585%另表；全部几何N=12，每块4，零共同/自身=0。仍有遮挡/稀疏投影/位姿候选解释，没确认唯一原因。

独立results/S8_results_audit_v2在03:47:23.729–03:47:34.554一次通过14253=11607复算+2046完整性+597metadata+3源码顺序。从72原PNG/派生GT重建支持、观测、地图、事件、投票/完整384决定，投影max7.1054e-15m，几何统计max3.1832e-12mm；原容差1e-9/1e-10不变。没有重跑模型或surfel polygon renderer，内部状态原张量未保存，仍记录审计。详见S8_INDEPENDENT_AUDIT。

报告另10166检查通过（384CSV字段3456、summary1880、独立audit272等），补充96行per_query_geometry及DiD/两臂覆盖/有效N，results/S8_report_audit。docs/S8_RESULTS.md完整中文；S8_MANUSCRIPT_REVIEW核218条原MD/tex表格，四组措辞/时间笔误已修。reports/S8/新场景独立复验报告.pdf五页逐页视觉QA过，SHAc214a5dd20501c766a3c73a024720983534cd3be3778e04ca0dbe222d5a32fa9，3416047字节；页1最终定义增补另根任务核V2并绑定report_qa.json。旧报告不改。

训练接触：docs/S8_MODEL_DATA_OVERLAP_REVIEW核官方13份code/doc、论文及权重静态pickle metadata，未发现TUM训练直接证据，但完整训练/祖先来源不足，TRAINING_UNSEEN_NOT_ESTABLISHED。只称本研究留出场景，不能说发布模型已证明训练未见；没有调用Claude模型。

新outputs/独立场景验证有PDF、中文全文、384CSV/96几何表、图、LaTeX源、72原图、全部冻结/审计快照。ip-/独立场景验证已是该outputs目录入口。新科研证据包_S8.zip325899547字节，692成员（691payload含包README+1manifest），SHAafae809a350cb8565674f1326443db11ee5c9a4a7b12f0bdb7ea0ebf9d2c05d3，全部CRC/SHA/size与原源不变通过；明确不含后写报告PDF/全文、完整数据、3GB权重及环境，历史JSON绝对路径保持，尚未做新机端到端或独立隔离重算，不能冒称已做。说明docs/S8_EVIDENCE_PACKAGE.md/json。

下一步具体顺序：先对S8证据包做独立隔离的可复核性检查，必要时另存只读路径适配工具（旧包不改、原容差不变、明确仅包内数学而非模型重跑）。随后按idea-evaluator和原候选审查重新核具体改进方向的新颖性与最小可证伪实验；优先考虑固定输出的检索省计算是否有独立价值，不因S8不重现而再调选图规则。新S9若立项须另冻结，已经看过的S7/S8只能当现有测试/软件回归，不能宣称新方法未见数据。完整VMem/视频仍未完成，真实课程学习/导师会议/提交不能代做或虚构。当前无活跃模型/下载/重放进程；heartbeat继续自主本地后续，不重复原成功实验。
