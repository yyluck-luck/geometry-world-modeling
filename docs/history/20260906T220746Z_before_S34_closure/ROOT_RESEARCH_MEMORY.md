# 当前科研记忆与接手入口

更新UTC：2026-09-06T20:50:23.707580+00:00；北京时间=UTC+8。**S32/S33主执行、评分、独立数值、结果图及照片快照交付完成。普通共同尺度约束取得本地三窗净收益；S34八帧真实消费者设计已选定，实际800步和原地图/三次渲染已完成，主评分及消费者独立复算PASS；深度独立核待运行。新方法与完整视频仍未验收。**

## 先读与长期要求

项目根目录是`/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling`；本任务工作目录`/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip`，outputs是给用户的日期快照。先读AGENTS.md、RESEARCH_PRINCIPLES.md v1.4、本文件和RESEARCH_LOG.md最新条目。阶段完整结果在docs/Sxx_RESULTS.md；当前完整交接docs/RESEARCH_HANDOFF_CURRENT.md。本次精简前的逐阶段详记完整保存在[历史记忆](docs/history/20260906T184709Z_before_S31_results/ROOT_RESEARCH_MEMORY.md)，没有删除历史证据。

用户是MSc新手，简单中文、本机自主推进、时间记录、每30分钟实查，Supervisor尤其02_Idea_Generation与本地Claude技能、多agent和原文检索。用Claude skills，不调用Claude模型/CLI。最终目标PhD深度/CCF A投稿质量，未完成，不能保证录用/导师反应。按强基线→失败→原因→方法；普通修复与已有组合不能改名作创新。没有发导师/他人消息授权。

`scripts/research_log.py.append_event`追加research_events.jsonl并渲染RESEARCH_LOG.md；补记用真实回执时间并注明记录时间。旧原件/失败/协议不改，不重复成功运行。实际最近流程检查2026-09-06T21:46:54.948419+00:00，间隔26.555分钟；下一检查目标2026-09-06T22:13:54.948419+00:00，30分钟截止2026-09-06T22:16:54.948419+00:00。

## 目前最关键的科学证据

| 阶段 | 实际结果及边界 | 完整记录 |
|---|---|---|
| S21/S22/S23 | 已见fr2_desk300帧CUT/TTT/FILT ATE8.254/2.848/1.858cm；278有深度配对/22缺失，完整300深度均值NA。全是已有方法。 | docs/S21_RESULTS.md–S23_RESULTS.md |
| S24 | fr1_xyz全798RGB→796配对/26.572059秒，CPU8/512DPT三法实际推理；ATE12.24063/9.68646/2.90258cm，8预定块FILT ATE较好，无灾难遗忘事件。7164行/6618pairs另式复核；图裁尖峰原FAIL保留，v2完整轴实际查看通过。 | docs/S24_RESULTS.md |
| S25 | 原VMem几何调用重放全历史并重置S/M；GA消费anchor self+后续other，不直接用raw camera_pose。state adapter60作者/92独立人工测试只是静态可用性，没做模型干预。 | work/S25_consumer_relevance/consumer_relevance.md |
| S26B | 真实新三法各400GA，原共同旧4导入历史。新4 AbsRel67.82589/93.54310/67.57302%；共同旧4已83.33823%。28行/40均值独立复核PASS。先查坏起点，不能直接归因记忆。旧focal使保存world点位变化，但0实际Surfel/cache/query事件。 | docs/S26B_RESULTS.md |
| S27/S27M | 保存量分析发现raw self不是全体GA实际输入，不准以4.4859%作公平优化起点。新1MST/3PnP/1backward/0Adam显示注册depth梯度断链；初始化与旧400终点逐位同。原断链发生在每次getter新ParameterStack；仅去detach仍不足。 | docs/S27_RESULTS.md |
| S28 | 匹配全部33初态的原A/修梯度B各真实400步；B梯度出现但AbsRel83.33823→87.47618%，loss更低。完整8行/800记录另式PASS。修getter只是恢复已知语义。 | docs/S28_RESULTS.md |
| S29 | 两零步初始化控制/2MST/6PnP/0Adam/0GT：s0=.1731799841按比例缩小全部局部深度，公共R/t相消；23检查及另一公式全786432点PASS。单位尺度不等于训练期固定尺度；S29当时未评分，S30之后评分其封存初态。 | docs/S29_RESULTS.md |
| S30 | C2t/C2a都修getter，各自33raw/深度/目标与S29逐字匹配，真实800Adam/反传、0新网络。C2t83.33823→87.47128%；C2a5.03905→42.37947%，原loss均显著下降。16行/66raw/800记录不同作者完整PASS，两图实际查看。 | docs/S30_RESULTS.md |
| S31 | 每臂一个自身初态全像素k，D*=kD400后评分。C2t84.05310%，C2a11.56681%，都仍输自身零步。8新行/2均值+原16行导入；0网络/GA/MST/backward，另式完整复核PASS。 | docs/S31_RESULTS.md |
| S32 | 固定4窗16RGB实际4model，3可用窗1200Adam；48行36评分12NA。普通k在两fr1窗接近零步，v2独立48表/1200保存日志PASS，原形状断言失败保留。 | docs/S32_RESULTS.md |
| S33 | 同S32初态普通公共pair尺度约束再1200Adam，64表旧48导入/新16；三可用窗AbsRel/RMSE/δ1均胜零步及k，绝对共同depth偏移均减小。独立64表/1200各类记录/2359296像素PASS，16照片快照完成。普通基线，不是新方法。 | docs/S33_RESULTS.md |

S26原共同4已跑400步但独立clean参考12像素失配导致FAILED原件保留；新FP32dense参考全字节一致只许可IMPORT_VALIDATED，不追认PASS。S26B首次启动缺显式importlib.util在数组前失败保留；只补标准库bootstrap的第二次启动成功。S22原生CPU RoPE精度失败、S24原裁轴图、绘图环境失败均保留。不要把修复后的新产物覆盖历史失败。

## S30最新实际执行与交付

实际18:12:29.415572–18:13:32.552760UTC，63.137115秒，work/S30_launch/receipt.json PASS，session78388已exit0。正式合同work/S30_scale_optimization_preparation/contract.json SHA000fa5d5b19cc516a581b382e457dcf8e03494da50b220d8f32c0ad0b16224a3。每臂400原Adam/.01/linear，1MST/3PnP/1clean，403objective含3次无更新观测；相机/pp固定，depth/focal/pair pose原声明可训练。全两端点封存后评分，共同GT相机显式oracle，不是完全无GT实验。

独立保存量复核18:21:29.386122–31.143825UTC，16完整评分/16组浮点/8差/66raw/800记录，AbsRel/RMSE最大差2.22e-16；梯度范数来自记录没有重算。work/S30_independent_numeric_review/receipt.json；session29860已exit0。

WS outputs/S30_优化损坏准确起点的真实证据_2026-09-07，90文件/89载荷7778316B，4原始实拍、两图、完整16评分与800步。manifest SHAb3e920ba3c0404f5c34389291576d20f091223a355f5b96839ab717de72cfeb9；作者68链接/root89载荷SHA核通过。图作者/root实际view PNG；PDF/SVG未单独栅格渲染。S28/29历史快照保持。

## S31已完成的精确边界

正式合同work/S31_scale_shape_preparation/contract.json SHA85d535ca913ed5a913cd259070bacd8b316a34e40aef1a55dd5043303b5f2587，runner94f7678f，protocol6c035724。不同作者源前审work/S31_independent_pre_review/final_pre_review.json SHA616c4f896091df2c747aa2c23de2b9d97f0ed4633d1664aa104659c7651b8793。每臂固定FP64 v=logD400-logD0，k=exp(-mean_all(v))；无逐帧k/shift/GT拟合/掩码/挑步。两臂D*先封存才原四GT新评分。不是优化器内部gauge控制，也没有拼接旧world/pair冒充新消费者。

实际主计算18:39:38.377241–39.991019UTC/1.613648秒；外控2.064877秒/RSS161890304B。root独立式18:39:40.439971–41.224466UTC/.784328秒；外控1.033285秒/RSS147668992B。CPU1、180s/2GiB两阶段实控。work/S31_execution/dispatch_receipt.json PASS；session91126已exit0，不再轮询。

C2t k1.2728267635863444，AbsRel.8405310395783584、RMSE1.7358592534233022m、delta1.000003668809251269408；C2a k1.5505380808239486，AbsRel.1156681167701237、RMSE.3674165247915667m、delta1.920872098614643。相对自身初态AbsRel分别恶化.007148738755245243/.06527761892375104。两组各validGT540363/missing246069/invalidPred0。

相对初态log-change平方和公共/帧间/帧内占比C2t82.979993/.645462/16.374545%，C2a85.683393/.110465/14.206143%。这是log变化分解，不是GT误差解释率、真实三维形状毁坏或已证尺度根因；没有新增D*==D0二元纯比例门。

root参考work/S31_root_numeric_review/recompute.py SHA42e2314f010e6d04a880a15d8a05bf342b13a8f92b599e6bc97bcad270532365，标量log(b/a)+fsum/原始矩，与作者log差/中心平方和独立；全1572864像素v/D*、92代数量、新8评分/2组/16差/CSV通过。D*最大差0，v最大4.72e-16，AbsRel1.11e-16、RMSE4.44e-16；不重复原16端点评分/历史梯度。完整docs/S31_RESULTS.md；WS outputs/S31_尺度恢复后仍输给起点_2026-09-07快照46文件/45载荷2357454B，4原始RGB，manifest SHA1b5f0575a336d9f881738d670f0661d20e6dd0118c50e4d20c8bd3db09634128；作者45链接/root45载荷SHA及源报告核验通过。

## 已完成的S33决策：普通共同配对尺度约束

S32已完成固定新窗内部三对照，结果削弱了S31非均匀伤害普遍不易恢复的动机。接受work/S32_next_decision/review.md唯一建议：MST后保存raw log pair scale平均m0，以exp(m0-mean(current log scales))实例级因子约束有效尺度几何均值。当前mean不detach，norm_pw_scale布尔不变避免改变adaptors，整个3×4矩阵沿原getter缩放。保留depth/focal/pairR,T与相对尺度训练。普通DUSt3R既有机制，明确Reject其创新叙事。

S33正式contract work/S33_preparation/contract.json SHA44a817a74afe10a16b758cc8fa6f7a17781d34d41ac575dd24e73b1ac1101400，源47身份及异作者/根前审通过，20:21:37.068277–20:23:02.862184UTC实际完成，85.793940秒，3PASS/1缺poseNA，PID36281/session39485已exit0。work/S33_launch/receipt.json；主评分20:24:46.482439–46.990395UTC实际PASS，session62695已exit0。新臂各400步/120s/4GiB/CPU8，三个可用窗共1200Adam、0网络。先33真实初态全字节匹配S32，再只跑一次固定版本；旧48行完整导入，新增四窗16行且缺pose仍NA，不扫参、不新k后处理。机制影响与超过零步/k的精度净收益分开判。之后回到proposal实际跨chunk消费者，不以短窗数量代替创新。

Supervisor第2章、idea-evaluator与Claude科学批判用于强对照、反例、因果/相关和完整分母。五路初轮idea cards work/S23_innovation_*均完成且未成立新方法；Supervisor固定207bc6f7a1aa107e544099c2c7cc86816fba9628读者已读59MD+70PDF页。具体应用docs/IDEA_GENERATION_FOCUS_CURRENT.md。

## S32 已完成（A/B/评分/独立复核）

选择规则先固定于2026-09-06T19:13:16.817126UTC；元数据选择19:16:27.746289–29.406784UTC。fr2_desk原N2965选987–990/1974–1977；fr1_xyz原N798选264–267/529–532。不能按配对成功列表重选。原全序列strict20ms一对一pose关联下fr2_desk_j1四帧均缺pose，因此A仍推理四窗16RGB，B只三个可执行窗，原四窗×三端点×四帧=48行/12组分母保留，缺窗三组NA，不插值或扩大阈值。

根实际于19:21:52.668533–680122UTC只读16RGB字节封存（0像素解码/0sensor深度/0预测数组）。原选择work/S32_selection/selected_windows.json SHA4574c2635851e83f5389da0d099819e7cbfd2ad9b8fe543ddf163e0fbf7e6cc6；给A/B使用work/S32_input_freeze/selected_windows_rgb_sealed.json SHAac2c04437afa62fbaa5f03e5159ba06960131d9a2405afd5f94eef0c2f9ed318，sensor.sha256仍null。fr1这8张RGB在S24已推理/轨迹评分，fr2这8张不在已核S21前300，其他暴露unknown；不是盲测。

A用原embedded src.dust3r.inference.inference而非S21 inference_recurrent，遵守原pipeline eval；每窗fresh child和一次_init_state，原PIL预处理，保存全部六头并和实际原star核字节。沿用S17 isolated CPU RoPE wrapper，不重复安装S21helper。A runner work/S32_preparation/run_inference.py SHA6246b7255a324653279429be770dcc7c07a478729bea9d172b182cb35fb7851d；candidate SHA7c9612253d32d18bb3da09f51212c33ade65b3255c460e80770b08e31be226a6。根与另作者前审通过；正式contract SHA1749d83fac56a8c7f50b74d37e2278239df25534318967fa93f4798eb5054124。A于19:31:56.287428–19:32:45.845997UTC实际完成，49.558569秒，全4窗16张/4model/96张量，0GA/GT。PID19822与session42209已exit0，不重跑。完整docs/S32_A_RESULTS.md；根19:33:18.581872核32载荷SHA PASS。预算每窗CPU8/180秒/16GiB，全部4窗顺序，0GA/GT。

B正式合同work/S32_preparation/B_contract.json SHA340c1b7b9e246fb088db8a50194d3003e1e384ecb05a24dc901bda2ff7bdca60，runner7552b65cf9913eafecec781437bc898f962e00df1d845a57130abe4c82d4cfcd。19:44:57.116681–19:46:23.507731UTC实际86.391050秒，3PASS/1预定UNAVAILABLE，3MST/9PnP/1200Adam/1200反传/3clean/0新模型/0深度GT。各可用窗33初态、getter等值、完整深度梯度/403objective和原clean/world门通过。原PIL和A同字节，单位C2a光学GT相机不额外翻YZ。session24526已exit0。

全部终态19:46:37.571841UTC封存，19:46:37.572186后根才哈希12GT字节；正式评分manifest SHA091ab3c69fd62c50a57d3ce12f7b404abff370d8fb229381e103a2db4fc2e722。评分19:46:37.613956–38.252142UTC，48行/12组，36评分12NA。fr2_j2 AbsRel零步/400/k为.11494392575341525/.4000580817845543/.1233071413120855；fr1_j1 .1320508279097008/.17458343268373921/.13197832704614743；fr1_j2 .10164119158986874/.1930582033179873/.10207058669956759。全四窗均值NA；预定三pose窗等权描述均值.11621198175099494/.2558999059287603/.11911868501926685。session14846已exit0。

fr1_j1 k后AbsRel微好但RMSE/δ1差，fr1_j2 k后δ1微好但AbsRel/RMSE差，不宣称统一胜败。原400全三窗三指标变差。k为1.5097525374456764/1.0522366571684552/1.1147604607409525，非GT拟合。S32入口原inference/PIL/eval不同于历史S30 recurrent，跨阶段差异不能仅归因于换窗。完整数据docs/S32_RESULTS.md。

独立v1 19:56:22.719640–23.565284UTC在raw叶shape断言失败：注册叶原本384×512而非一维，旧FAILED/已读9端点与首窗400日志事实保留，当时尚无GT像素解码。v2只改这一个断言，经异作者+根审并冻结。20:06:31.028251–33.752619UTC实际PASS，外控3.116821秒/RSS435339264B、CPU1/120秒/2GiB。完整48行/12组/2359296尺度像素/198初末raw/1200优化与1200保存梯度记录核，12GT另由OpenCV解码；AbsRel/RMSEmax1.11e-16、δ1/恢复深度max0。没有重反传或梯度数值证明，SS比例/RMS未另式重算。work/S32_independent_numeric_review_v2/receipt.json，session81845已exit0。

本轮原文检索补充work/S32_nearby_literature/novelty_exclusions.md：Scal3R已保留局部几何、改多参考相对位姿；LASER已研究跨窗口分层尺度。不要将其宽泛主张当原创，S32先验证给定相机消费者优化失败。原文阅读范围与归档失败均记录；没有复现这些方法。

S32完整用户快照已封存：WS outputs/S32_新片段三对照与真实照片_2026-09-07，共213文件/212载荷16104288B、16原始实拍、48CSV/1200步与1200梯度记录、代码/合同/原失败及独立PASS。manifest SHAdf7087cb58a1cf01e071c1861ad794ffe80143e58d023e01b4425d71548f081a；作者118活动链接与根115关键链接存在，根212载荷SHA及报告源SHA核通过。work/S32_full_delivery/root_check.json，实际2026-09-06T20:12:49.589387+00:00。图作者及root实际view PNG，PDF/SVG未另渲染；plotted_data旧PENDING是首次制图历史字节，当前v2PASS见新图注/回执。大66文件仅本地链接，不表示便携独立数据包。

## S33当前证据（主执行/评分/独立复核/交付完成）

报告docs/S33_RESULTS.md SHA b5ef591b30636b07565ad41896f9ff50ec4eb4ec0a79ed90cb4d3e3dff65ba1c，最后不同作者表述审work/S33_independent_review/final_claim_review.json SHA b9e33546e0f599fba6e4447592c845670c630298f108cfe5687ec62372ea3b9b。正式评分manifest83be08e12d3102487cf31f902c396db49567cfdbc63cbfeba12b02d3ab1665ab；root全4终态+83文件字节封存后，新12GT各解码一次，原48JSON/CSV字节前缀导入，新16行（12评分4NA），全64/16组48评分16NA，原全4窗均值NA。

新common_pair_scale_400三窗AbsRel .1082468488084908/.12635472579419396/.09050791658909195；RMSE .2334223200622032/.18702431861467145/.10564948878286015；δ1 .9001358440917699/.9617826810078398/.9847124500835656。各窗三项都优于自身零步和k；三固定pose窗描述均值AbsRel.10836983039725889、RMSE.1753653758199116、δ1.9488769917277251。已见开发窗、GT相机，不作统计或创新结论。

真实新增3MST/9PnP/1200Adam/1200backward/3clean/0model；与本轮S32A/B合计16RGB新推理及2400Adam。每窗33原初态全字节匹配S32，原403objective/梯度及clean/world门通过，400scale日志检查有效log均值m0保持。独立保存量reviewer已实际PASS，见下；共同depth mu三窗绝对值均减小，没有把pairscale门代替深度分析。

work/S33_mechanism_analysis推导J(a)<=aJ(1)+(1-a)C只是条件性代数：显式非负权重假设，未验证实际conf域/未算C。数学审原稿1918...、明确假设修订88b5...与revision_closure均保留，无新GT或模型。下一old4→new4真实消费者接口设计审中，NMS需历史状态，不擅自设置默认阈值假装原链。S33四条件图及照片快照已完成，旧S32完整快照不改。

S33独立reviewer work/S33_independent_numeric_review/recompute.py SHAcd9807f6dea18946a14d3f36e02be707e131a57aef88751de2b1804e4331b41e；candidate5ec8b8190dcdd65dff45e12e16b8b9a8657dbe9dbdd4e202d4b65d889538469a，binding9103e9c8e1e269022b5ae2588db8ce32b30b33c327bee87f98fb6bedab4b55d9。37身份、全部8scorer controls，源审后20:39:24.560079–28.089159UTC真实PASS，内部3.528963秒/外控3.606174秒/RSS568213504B、CPU1/120秒/2GiB；session68526已exit0。全64表旧48只导入，新12评分4NA；99同旧初态raw、198新初末raw、1200 optimization/gradient/scale保存记录和2400scale前后边界；12GT独立OpenCV解码；AbsRel/RMSEmax4.1633e-17/2.7756e-17，δ1/无效比例0。保存日志不等于重算梯度，逐步完整3×4门仍是producer recorded，非独立矩阵重算。

完整2359296预测像素math.log(new/initial)+fsum，三个mu .008700187887605607/.006447767859862911/.013280945477424934，相对原自由400 -.411945754910324/-.05091804830157587/-.10863954841589202绝对值均减少。没有新k/GT拟合/SS/RMS，微正mu不是强制等于起点。实际mu结果和精度净收益分开报告，普通已知尺度约束不升级成创新。

S33用户快照WS outputs/S33_尺度约束四条件与真实照片_2026-09-07，178文件/177载荷17130154B（含manifest17216516B）、16实拍/完整64CSV/新1200各类记录/图/独立代码及实际回执。manifest SHAa54bd7c2d7bbc59baea3bc1797c003e9cf082412e3f8e3510169271954819c72；作者94活动链接、根90关键本地链接和177载荷SHA核验通过，work/S33_delivery/root_check.json。链接方便版报告只改目标，原文精确字节另存S33_RESULTS.md.source.txt。根先错用旧索引名、又错要求改链接版逐字等于原文的两次checker失败均保留，未改实验数据。图作者/root实际view PNG，PDF/SVG未独立渲染；旧PENDING版本已归档，plotted_data历史原字节保持，最新状态见caption/实际回执。

## 下一项S34：已有八帧的真实消费者pilot（实现中，未运行）

根已完整阅读并接受work/S33_next_decision/review.md SHA3e7e8e4406c0db7134dd189ec4344eb4953bb593a8df8f35a55127dcee06e2e2为唯一后续；completion_receipt3d97a14aa798d8acb2d31692d21601811d7229edc7b5be37eb7a7a5bdad7ec94。不继续三个已见短窗扫参。建议复用S26B的fr2首8已封存CUT头/原PIL相机；共同old4用S29 C2a零步预测，在副本新做一次原clean并原kernel建共同旧地图。各臂深拷贝完整旧图；比较zero/free400/七边common-scale400，2新MST/14PnP/800Adam、共4次clean/0模型。未来预算旧packet+map120s/4GiB，两GA各240s/8GiB，三端点append/render共120s/4GiB，评分120s/2GiB，CPU8顺序/评分CPU1、空盘10GiB。只是建议预算，未冻结/执行。

旧4 original4与8帧cut3r前4 archives SHA不同，不能称跨源逐字相同；合法性是所有臂共享同一历史old depth外部约束，不能贴原400假标签。相机文件SHA共同c004c415b5bca43ae9a22cf63b542e7171eec29e31bf985c7e36327d1f5c0194，未来需核实际数组。原MST尝试setter，但False/force guard应拒写旧depth，必须实际preset/MST/400/clean检查旧raw冻结+log-exp容差1e-5；只新4有梯度，不能搬S33全depth训练断言。旧focal仍训练，不顺手修focal cache。零步使用同自由臂内存初态及clean副本，不重启第三次MST。

实际消费边界为原Surfel append、原512×288 renderer、自查询给定第8相机、process_retrieved_spatial_information来源票权。默认NMS只len5建initial_threshold，4→8缺历史latent/NMS状态，默认最终context IDs明确未执行，不能关NMS/伪造cache。render不是TUM原传感器射线网格，不用简单resizeGT声称可见性准确率。0.235880秒已见pilot，不是未来视角/长序列/视频验证。若旧depth冻结已使自由400足够好，接受强反例并收束all-trainable外推；变化≠质量改善。S34目前仅设计，下一需新最小wrapper/协议和源审冻结，未启动。

## 环境、完整生成与proposal缺口

M3Max64GiB，无远程GPU；.venv-cut3r/bin/python为Py3.12/Torch2.7/NumPy1.26.4，科学CPU8/FP32，S31保存分析CPU1/FP64。overlay work/S17C_environment/site-packages；原512DPT权重3173761006B SHA45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103，不重复下载。图用既有HomebrewPy3.13/Matplotlib3.10.9，不改科学venv。

VMem commit39291e4f272f6b4f270691d930926ab5930f942e；CUT3R8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf。实际几何隔离源码work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R；阶段patch通过冻结wrapper生效，不把未改的原文件宣称已永久修复。祖先git覆盖HOME，不全量git add/commit。

完整VMem视频未执行，原主权重gated/VAE缺口仍在，work/S25_official_resource_recheck记录官方有限核查；未申请个人访问/登录/擅自替换未知权重。此缺口不阻止本机消费者研究。14周proposal交付成熟度约前3周到第4周初，不是工时；新机制、公平跨场景、生成闭环、最终论文演示仍缺。
