# 当前科研记忆与接手入口

更新UTC：2026-09-06T16:27:25.223775+00:00；北京时间=UTC+8。**S24三个796帧真实基线、S26B三个8图原GA和统一评分/不同作者复算均已完成。S26共同旧4和S26B首次启动失败均保留；S26B第二独立启动入口PASS。当前S27正在准备保存数据尺度诊断和源码目标分析，没有新的GA。最终质量目标未完成。**

## 目标、原则与接手

用户是MSc新手，要求简单中文、本机自主持续推进、时间记录、每30分钟实查、Supervisor及本地Claude skills、多agent与原文检索；不是调用Claude模型/CLI。最终目标PhD深度/CCF A投稿质量，当前未达到；不保证录用或老师反应。先强基线→真实剩余失败→可证伪机制。读取AGENTS.md、RESEARCH_PRINCIPLES.md v1.4、最新RESEARCH_LOG.md；通过scripts/research_log.py追加research_events.jsonl。旧原件/失败/协议不改，不发导师消息。

最近实际流程检查2026-09-06T16:43:13.214233+00:00，间隔28.378分钟；过去稍超30分钟的记录保留，不称定时器准点触发。

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

## 正在推进：S27尺度诊断准备

从S26B坏结果出发，先定位共同旧4为什么已有大深度误差。work/S27_scale_diagnosis_source源审进行中：preset_pose关闭norm_pw_scale并不冻结可训练pair log-scale；原函数名l1_dist但实际为加权逐点3D欧氏距离，没有metric-depth prior。同中心时共同收缩可能减小loss，但尚未实证本次原因；固定旧depth会破坏该共同收缩。另初始化align_multiple_poses实际为Sim3，不能信注释SE3。历史未保存post-MST depth/pair-scale，不能倒造初始状态；将来必要时仅重放MST、0优化，另记为新计算。

优先新发现：get_depthmaps→ParameterStack的detach切断注册depth梯度，两个源审及极小原helper人工反传已确认实现性质；不等于历史真实梯度已记录。S27M common4真实保存头MST-only/一次backward准备中，0 Adam步，尚未执行。

S27保存量事后描述已于16:37:34–16:37:38UTC完成，results/S27_saved_scale_diagnostic：132分布/56误差/20组/1600旧trace，0新模型/GA。共同旧4 raw self AbsRel4.4859%、GA83.3382%，GA/raw中位0.169–0.173；全8最大相机基线2.543cm、common4为1.037cm；不能由短基线直接判collapse。other坐标为anchor view，不能直接当j帧传感器depth评分。work/S27_scale_objective_review独立审理论与最小人工反例，非真实实验。根正完成S26B报告交接，暂不自动新GA或方法改动。

## 创新问题与技能具体应用

重点docs/IDEA_GENERATION_FOCUS_CURRENT.md与Supervisor handbook2.1/2.2/2.3；固定207bc6f7a1aa107e544099c2c7cc86816fba9628。reader已读59MD+70页PDF（12skills/18中文章/28refs/README），126其他文件只索引。五路首轮全完成，work/S23_innovation_*，没有成立新方法。idea-evaluator先排致命缺陷，Claude科学批判区分代理、消费者与生成结果。

原VMem每几何调用重置S/M、重放全历史；GA不用raw camera_pose，只消费anchor self与后续other。自由ATE改善不能验收proposal。S25四臂state adapter仅静态，60作者/92独立小测试，不是模型干预结果。

新源码线索work/S26_commit_consistency_source/audit.md：旧depth/pose固定但旧focal优化，重建旧world可变；提交的Surfel旧点不重写。另surfel_Ks累计所有历史focal快照、查询用均值、undo未同步。已有S26B保存点位差的数值证据，尚无真实提交地图/伤害/创新证据。 普通focal冻结/重建旧图/修缓存必须作工程对照；old-only冻结不能误用会冻结整个8帧栈的preset_focal。S26B完整旧4描述诊断已完成，0新GT/GA，不称真实Surfel/cache运行。

work/S26_consumer_novelty_check已核G-CUT3R/Pow3R/MapAnything/TCO/RayMap3R五篇原方法；TCO重要直接近邻，泛化相机条件/loss反馈/ray门控不足以是新方法。不能靠换名或图好看认定创新。另work/S26B_commit_prior_check四篇原文BAD SLAM/BundleFusion/ElasticFusion/DSO排除普通地图同步、重积分及按变化预算修图的新意；保存点变化可能只是工程问题。

## 环境、完整生成与proposal缺口

M3Max64GiB、CPU8、无远程GPU；.venv-cut3r/bin/python：Torch2.7/NumPy1.26，work/S17C_environment/site-packages为evo/Matplotlib overlay。原512权重data/cut3r/cut3r_512_dpt_4_64.pth完整3173761006B，SHA45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103，不重下。祖先Git覆盖HOME，不全量git add/commit。

完整VMem视频未执行，原主权重gated、VAE缺口未解。work/S25_official_resource_recheck核7官方小URL未找到替代；未擅自认证申请或下载未知替代权重。本地消费者研究仍可推进，不把资源缺口扩大成整个项目无法进展。

原14周proposal：1–3文献/基线、4–5失败、6–9方法、10–12评价、13–14交付；当前成熟度约前3周到第4周初，不是实际学生工时。主要缺口仍是新机制、公平跨场景确认、生成闭环、最终论文演示。
