# 当前科研记忆与接手入口

更新UTC：2026-09-06T17:00:27.160735+00:00；北京时间=UTC+8。**S24/S26B真实基线与消费者评分完成；S27保存量诊断和S27M真实MST/一次反传已完成。4注册depth梯度均None，新MST深度与旧400步终点逐位完全一致；根因定位推进到明确梯度断链。S28匹配初态A/B两臂各400步已完成且评分更差（83.3382→87.4762%），独立复核/报告正在整理。最终质量目标未完成。**

## 目标、原则与接手

用户是MSc新手，要求简单中文、本机自主持续推进、时间记录、每30分钟实查、Supervisor及本地Claude skills、多agent与原文检索；不是调用Claude模型/CLI。最终目标PhD深度/CCF A投稿质量，当前未达到；不保证录用或老师反应。先强基线→真实剩余失败→可证伪机制。读取AGENTS.md、RESEARCH_PRINCIPLES.md v1.4、最新RESEARCH_LOG.md；通过scripts/research_log.py追加research_events.jsonl。旧原件/失败/协议不改，不发导师消息。

最近实际流程检查2026-09-06T17:10:57.461784+00:00，间隔27.737分钟；过去稍超30分钟记录保留，不称定时器准点触发。

## 已完成的真实证据

- S21/S22，同fr2_desk已见300帧：CUT/TTT/FILT ATE 8.254/2.848/1.858cm，已有方法。FILT原生CPU精度兼容失败保留；一行RoPE精度统一后24头精确相同才跑300。S23复用预测，278深度配对/22缺失，完整300均值NA；278描述AbsRel4.6235/3.2608/3.0618%，逐帧RMSE均值.392691/.325125/.340982m。>8m少量GT占FILT大量SSE，未证明传感器错或遗忘。见docs/S21_RESULTS.md至S23_RESULTS.md。
- **S24已完成**：fr1_xyz全798RGB→796严格20ms配对，26.572059秒，场景早期已见，非盲测。同512DPT/CPU8，CUT→TTT→FILT真实全头/pose完成后统一评分。主ATE12.2406289/9.6864554/2.9025811cm；RPEt .01442914/.01581448/.00638827m。FILT预定8块ATE均较低，不能据非零误差宣称灾难遗忘。最终报告docs/S24_RESULTS.md，主results/S24_baseline_expansion/scoring，多跨度results/S24_horizon_diagnostic。
- S24全起点1秒/5秒RPEt RMSE：CUT .153804/.183083m，TTT .107212/.126482m，FILT .034825/.040754m；不重新对齐。7164行/6618有效配对不同数学重算通过，主表不同作者、horizon同作者另一公式，非外部复现。work/S24_independent_numeric_review。
- S24原主图裁掉TTT尖峰的问题保留FAIL图，另存scripts/plot_s24_baseline_v2.py，只改完整共同纵轴。work/S24_reporting_v2已实际查看PASS报告尺寸；不称最终排版认证。WS outputs/S24_796帧真实结果_2026-09-06含报告、图表、9张未经修改实拍、数值及SHA清单。原session53980/20829都exit0，不再轮询/重跑。

## S26/S26B消费者：结果完成，失败保持

S26原共同旧4真实400GA+clean完成后，独立参考12/786432值失配导致FAILED；11半像素取整翻转、1清零传播已定位。新dense-gather FP32参考与原保存结果全字节一致。29项保存量核验只许可IMPORT_VALIDATED，不追认原PASS；历史PnP/module库存/postfinal等NOT_RECORDED保留。work/S26_clean_recovery。

S26B parent冻结SHA147357aa1b24caeb813c01fd822cb96f754c2573437d0db6ac8a05b7cbd4d90c，16:10:22UTC。原首次启动16:11:01缺显式importlib.util在任何数组前FAILED；work/S26B_execution/dispatch_receipt.json仍FAILED。第二启动仅显式标准库bootstrap、原worker/scorer源码不变，合同SHA15912f6f012cad51986bb67669997da1a9fc4fae08d16eb0c3d88c9cf9a7cb46，成功外控work/S26B_execution_attempt2/receipt.json，16:17:18.533534–16:19:06.814613UTC，session38953已exit0。

仅新增CUT/TTT/FILT三个400GA=1200步，0新网络；共同旧4是导入历史输出，0重复GA。原三源PIL/28头拼装PASS复用。已见fr2_desk首8帧、0.235880秒、共同GT相机显式oracle输入；旧depth是预测不是sensorGT，旧depth/相机/pp固定，focal和新depth按原GA声明可训练，但S27源码发现depth梯度断链，真实更新需下一项新检查。所有封存后评分，不拟合尺度/不切远点/不按conf筛选。

**真实新4结果**：AbsRel CUT67.8258911%、TTT93.5431038%、FILT67.5730241%；逐帧RMSE均值1.400540/1.902778/1.394245m。共同旧4已AbsRel83.338228%、RMSE1.725768m。因此先查共同起点尺度/坐标条件，不能直接解释成记忆能力差异。新4有效GT访问547012，缺239420，无无效预测。不同作者OpenCV逐行全像素复算28行/40均值PASS，最大差2.22e-16，非全部JSON辅助字段/外部复现。

预冻结旧4全部786432像素/方法描述：世界点位移均值CUT2.34637cm、TTT0.60429cm、FILT2.11660cm。focal算术分解解释绝大部分差，剩余最大范数<2.61e-7m；旧depth/pose原容差通过、pp相同。只是保存量变化，不是focal干预反事实/GT伤害；TTT位移小但深度更差。假设pool12/current8焦距差1.7702/0.3969/1.6401%，0实际Surfel/cache/query或视频。

最终报告docs/S26B_RESULTS.md，work/S26B_reporting两图已实际查看PASS报告尺寸；完整数据results/S26B_consumer_baseline、work/S26B_commit_diagnostic/results、work/S26B_root_numeric_review。WS outputs/S26B_真实地图优化与失败诊断_2026-09-07含8张原始实拍、图表与数值。已结束进程不用轮询，不再重跑任何成功阶段。

## S27与S27M：已完成的失败机制证据

S27保存量事后描述实际16:37:34.549560–16:37:38.250474UTC完成，results/S27_saved_scale_diagnostic：132分布/56误差/20组/1600旧trace，0新模型/GA/MST。共同旧4 raw self AbsRel4.485928%、GA83.338228%，GA/raw中位0.169–0.173。三法new4 raw self约4.32545/4.56873/4.41181%，GA67.82589/93.54310/67.57302%。self不是全体GA实际输入，不能称逐帧同一深度优化前后；other为anchor坐标，只作分布不直接对j帧GT评分。全8最大baseline2.543cm，common4 1.037cm；短baseline不直接证明塌缩。GT/pred比例oracle描述而已，没有应用修正。

S27M新诊断实际16:51:19.465645–16:51:24.729366UTC。固定原common4头/8PIL同输入次序/seed0/CPU8/原几何代码，1原MST/3PnP/1目标forward/1backward，0Adam、0新网络、0sensor depth。所有4注册im_depthmaps gradNone，临时未注册叶grad有限非零，focal与pair参数有grad。所有注册参数名称/对象/值均保持。重放MST深度全部786432元素与旧common终点逐位相同，raw SHA a68a166a3007a083b656794f5d8a3ab3f62840ebf33f4ac0faddab27bc3203b4；初loss1.2425107955932617也等旧trace首项。新MST不是旧历史快照，不补造历史逐步depth。

S27M合同SHA6afaa53445b618840991de4f5c49c61013628b5a571d79c078d247a07ac0ee56；script583083e7db3bc6649f056b68fd53d1c9bd773bcc313fc708de6bab6e15b9df70。结果results/S27M_mst_gradient_diagnostic/receipt.json PASS_DIAGNOSTIC_EXECUTED，外控work/S27M_execution/diagnostic/receipt.json PASS，6.173291秒/RSS860291072B，session70514 exit0，不再重跑。父611身份和实际载入overlay/geometry核验通过，原代码未编辑。

独立保存量复核work/S27M_independent_result_review/16:54:54–55UTC：全depth位级复算、FP32log-exp回转通过；25注册+1临时梯度记录核验是源绑定，未重新反传，不冒称梯度范数独立重算。记录的Sim3 s=.173179984，中心残差RMSE2.128mm但映射朝向与given约130度；mst最终固定c2w==given。不能称整体对齐良好，也不能单据130度认定深度缩小原因，源码已核公共R/t同步变换后取局部z代数相消，留下s；无全像素新验证，见work/S28_initialization_prior_analysis。约130度差不能直接解释标量缩小。

源码get_depthmaps→ParameterStack的detach+临时新Parameter解释真实注册depth断图。仅去detach仍会被新Parameter断链。原preset_pose关闭norm_pw_scale不是冻结pair scale；原l1_dist为加权点3D欧氏范数；align_multiple_poses实际Sim3。work/S27_scale_objective_review理论/微小人工反例不计真实实验；所有深度自由同中心的共同缩放与实际断图路径/固定旧depth分清。

报告docs/S27_RESULTS.md；图work/S27_reporting已作者和root实际查看；WS outputs/S27_深度未更新的真实证据_2026-09-07含完整报告/数值/8原始实拍/SHA清单。原S26B报告仍保存真实1200步但已澄清depth不一定更新。上游小范围检索work/S27_upstream_context有原代码及Issues6/8/9：使用反馈不是同源故障或新颖性证明，未核全历史PR。

## S28实际已完成：仅修梯度不够

只修get_depthmaps保留注册叶梯度，其他ParameterStack构造不改；未来old4冻结/new4训练逐叶flag保持。root选新A原路径/newB修复各400步，核MST后全部raw参数/buffer完全相同，明确新增原A是为了匹配初态，不覆盖旧基线。只运行common4，先不用sensor GTdepth/newmetric prior，不同机制分开。S28最终不同作者源码前审PASS，work/S28_independent_review/final_review.json SHA601e1248157d851a515eb0de793babe88c961fba38be103aa5c6344530859af7。root原getter AST人工2种场景4配置/3backward .653s通过，work/S28_root_getter_semantics；人工不是效果证据。正式合同work/S28_gradient_scale_control/contract.json SHA7a80b96b0c75a97987b527ee214263bf1308e78f7f97cfb382bfc76355b7fbd4，已启动，外层work/S28_launch/receipt.json，阶段work/S28_execution，结果results/S28_gradient_scale_control。实际外控17:17:35.092849–17:18:37.390167UTC PASS、session62467 exit0，正式合同前后SHA同，不再轮询或重跑。original与gradient_only各400新步/1MST/1clean，0新网络。A/B全注册raw参数+buffer初态逐字相同，getter值/初loss相同；B400步4depthgrad非None有限，旧A全程无depthgrad。两臂独立clean全像素0失配、目标与世界反投影原门通过。外控A29.612s/RSS1047199744B，B31.599s/RSS1059225600B（含诊断开销非性能benchmark）。

两臂封存后统一4GT评分：A AbsRel83.33822755%、RMSE1.725768278m；B AbsRel87.47618457%、RMSE1.803446930m；delta1均0，validGT每臂540363，missing246069，invalidPred0。postfinal原目标A .015937957912683487，B .005106816999614239；B各帧mean(pixel depth/init ratio)为.763532/.794409/.796510/.807059，A为1。仅修梯度使depth真实更新却更差，此已见4帧反例不能扩大成所有场景或尺度机制已成立。work/S28_independent_numeric_review在准备、work/S28_reporting图在制作；本轮原先progress.json RUNNING是迭代快照，终态以producer/caller PASS为准。

剩余尺度和初始化方向再单列工程控制，普通修bug不称创新。

## 创新问题与技能具体应用

重点docs/IDEA_GENERATION_FOCUS_CURRENT.md与Supervisor handbook2.1/2.2/2.3；固定207bc6f7a1aa107e544099c2c7cc86816fba9628。reader已读59MD+70页PDF（12skills/18中文章/28refs/README），126其他文件只索引。五路首轮全完成，work/S23_innovation_*，没有成立新方法。idea-evaluator先排致命缺陷，Claude科学批判区分代理、消费者与生成结果。

原VMem每几何调用重置S/M、重放全历史；GA不用raw camera_pose，只消费anchor self与后续other。自由ATE改善不能验收proposal。S25四臂state adapter仅静态，60作者/92独立小测试，不是模型干预结果。

新源码线索work/S26_commit_consistency_source/audit.md：旧depth/pose固定但旧focal优化，重建旧world可变；提交的Surfel旧点不重写。另surfel_Ks累计所有历史focal快照、查询用均值、undo未同步。已有S26B保存点位差的数值证据，尚无真实提交地图/伤害/创新证据。 普通focal冻结/重建旧图/修缓存必须作工程对照；old-only冻结不能误用会冻结整个8帧栈的preset_focal。S26B完整旧4描述诊断已完成，0新GT/GA，不称真实Surfel/cache运行。

work/S26_consumer_novelty_check已核G-CUT3R/Pow3R/MapAnything/TCO/RayMap3R五篇原方法；TCO重要直接近邻，泛化相机条件/loss反馈/ray门控不足以是新方法。不能靠换名或图好看认定创新。另work/S26B_commit_prior_check四篇原文BAD SLAM/BundleFusion/ElasticFusion/DSO排除普通地图同步、重积分及按变化预算修图的新意；保存点变化可能只是工程问题。

## 环境、完整生成与proposal缺口

M3Max64GiB、CPU8、无远程GPU；.venv-cut3r/bin/python：Torch2.7/NumPy1.26，work/S17C_environment/site-packages为evo/Matplotlib overlay。原512权重data/cut3r/cut3r_512_dpt_4_64.pth完整3173761006B，SHA45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103，不重下。祖先Git覆盖HOME，不全量git add/commit。

完整VMem视频未执行，原主权重gated、VAE缺口未解。work/S25_official_resource_recheck核7官方小URL未找到替代；未擅自认证申请或下载未知替代权重。本地消费者研究仍可推进，不把资源缺口扩大成整个项目无法进展。

原14周proposal：1–3文献/基线、4–5失败、6–9方法、10–12评价、13–14交付；当前成熟度约前3周到第4周初，不是实际学生工时。主要缺口仍是新机制、公平跨场景确认、生成闭环、最终论文演示。
