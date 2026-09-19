# 本轮实际使用的skills与工具

本清单记录实际应用及落地证据，不把“已安装”“已阅读”和“已执行全部配套工具”混写。研究仍以用户指定的HKUSTDial/Supervisor-Skills为主；此前固定上游版本见vendor/provenance.json。Claude目录提供本地技能文件，本项目没有调用Claude模型或执行Claude CLI。

## 2026-09-06 S13/S14新增应用入口

当前阶段完整应用映射和范围审查在 `docs/S13_RESEARCH_SCOPE_AND_SKILLS.md`。Supervisor idea-evaluator加本地Claude scientific-brainstorming产出12查询/7原文的S14两候选；Claude scientific-critical-thinking用于S13不同实现数值审计、交接事实审查与S14A输入合同。tech-paper-template仅类型分流，benchmark-paper-template完成五支柱/六段/章节及缺口，不冒称成熟benchmark或新方法论文。

figure-designer指导S13全三分层差距矢量图；本机Matplotlib/Fraction真实生成48行CSV和6行分层，不使用生成图片。pre-submission-reviewer相关成稿检查产出不同作者1707项核验及只读PDF渲染，保留字体警告。S14A独立代码前审用人工FP32反例拦下旧gap运算语义差异，最终V2闭环后S14A真实30JSON提取与360值独立复算已完成，不能说人工tests或输入整理证明方法有效；详见docs/S14A_RESULTS.md。OpenAI Docs官方核读和应用工具完成30分钟接续更新。

没有为增加技能数量重跑既有模型、PDF或Draw.io。科研创新、部署前query相机、同信息/监督/容量强基线及新场景仍按真实进度留缺项。

| skill / 工具 | 实际用途 | 可查成果 |
|---|---|---|
| Supervisor-Skills：deep-research | 搜索前冻结3个RQ；3独立视角广搜/窄搜/反证，串行分类比较，原始来源独立复核 | LITERATURE_RESEARCH_BRIEF_V2、四份EVIDENCE、25篇LITERATURE_SYNTHESIS_V2、独立引用审查及修正回执 |
| Supervisor-Skills：idea-evaluator | 对原无条件均值优越主张触发CRITICAL早期否决，停止五维打分，不用分数掩盖反例 | IDEA_REASSESSMENT_V2；最近5项工作逐机制对照 |
| Supervisor-Skills：tech-paper-template | 前置判断当前贡献是机制评价，路由至benchmark-paper-template；未假装已完成方法论文七格 | EVALUATION_PAPER_SCOPE_AUDIT中的类型判断 |
| Supervisor-Skills：benchmark-paper-template | 五支柱、构建过程、六段逻辑、章节和未完成项审查 | EVALUATION_PAPER_SCOPE_AUDIT；NOT READY及具体缺项 |
| Supervisor-Skills：figure-designer | 设计H1/H2/H3机制图，选择完整逐查询热图和同预算图表，保留共同覆盖说明 | reports/S7_design原生Draw.io，S6_memory_analysis三图、S7_analysis两图及图注 |
| Claude本地：sci-scientific-brainstorming | 假设反转、粒度变化、三种不同贡献方向及强反例 | NOVELTY_CANDIDATE_REVIEW：A事件诊断/B省计算/C集合冲突，各5项近邻与退出条件 |
| Claude本地：sci-scientific-critical-thinking | 检查位置与关联联动、NMS夹带、代理指标与样本单位 | S7_EVENT_REPLAY_PROTOCOL、S7_PRE_RUN_REVIEW、S7_INDEPENDENT_AUDIT与S7_REPORT_REVIEW |
| Claude本地：sci-hypothesis-generation | 三个可同时成立、可反驳的机制假设；每假设独立页，预测与失败条件明确 | reports/S7_design/下一轮研究假设与实验设计.pdf及.tex；主文4页、附录2页 |
| PDF skill＋XeLaTeX | 实际编译、字体与缺字检查、逐页渲染查看 | hypothesis_build_log.json、hypothesis_qa.json；结果PDF另存reports/S6_S7 |
| Draw.io 30.0.4 | 原生可编辑节点和连线，真实导出SVG/PNG/PDF | drawio_export_log.json：3导出返回0；drawio_qa.json |
| 文献检索工具 | 打开作者论文、官方会议信息和官方仓库；未用聚合摘要代替所需方法证据 | 各EVIDENCE查询记录；引用复核25项、两项限官方原文索引摘录 |
| 独立科研分析程序 | S6从实测PNG重建；S7从事件重建地图、匹配、渲染后票权/排序和支持 | S6的3453项与S7的9827项通过；次数不等于独立样本或创新数量 |

## 适配与未使用范围

用户明确要求自主推进、不再逐步提问，因此brainstorming等skill示例中的对话提问没有机械执行；学术判断通过可审查的假设、反例和独立复算记录，而不编造用户参与或导师认可。

hypothesis-generation中的假设质量、预测、反驳和排版方法已应用；其默认NanoBanana/Gemini配套生图流程没有运行。本轮使用用户已有Draw.io制作可编辑机制图、标准绘图工具绘真实数值，不宣称完成外部AI生图及其自动审图。引用按已核实语料覆盖需要，不为模板数量目标凑未经核查文献。

Claude的sci-scientific-schematics与dia-diagram-design只阅读并判断适用性；前者依赖未运行的外部图像API，后者偏HTML/SVG品牌流程，本轮未应用其完整流程。发现5643个skill路径涉及重复副本及符号链接，不能说调用了5643个不同技能。原路径、解析路径和SHA见LOCAL_SKILL_TOOL_INVENTORY.json。

本清单没有声称使用所有安装技能，也没有把软件存在等同成功执行。实际时间依据研究日志、导出/编译及运行元数据；学生工时、导师会议、投稿和新视频仍不能从这些自动记录推算。


## S8设计阶段的继续应用（2026-09-06）

继续落实Supervisor-Skills评测设计与本地Claude科学批判思维的已读原则：外部场景来源核实、GT时间缺口排除、先冻结后取图、三块全部外部测试、不按新图调参、一般变化与S7具体模式重复分开、完整负结果和相关查询计数。证据S8_EXTERNAL_SCENE_PROTOCOL/S8_DESIGN_FREEZE/S8_PRE_RUN_DESIGN_REVIEW。只完成设计与实现预检，尚无S8新场景实验结论；没有调用Claude模型。下载器故障测试是工程验证，不是科研样本。


## S8实际执行与结果呈现（2026-09-06）

Supervisor-Skills评测设计和Claude本地科学批判思维的应用已推进到真实新场景：V1元数据失败保留、V2看图/结果前技术修订另冻、全局弃用区间不按结果调、全部12预选查询完整呈现；主具体符号未重复与敏感性固定抵消0/12照实报告。独立派生23803/采样1554/结果14253检查，报告10166复算及218原稿表格核查均记录实际范围，不把检查数当样本数。paper-writer/pre-submission-reviewer原则落实到证据强度、完整负结果、训练接触未知、投票与读出计数/时间措辞纠正；figure-designer原则落实到全部查询曲线/低共同覆盖及不同纵轴标注。PDF skill结合用户已有XeLaTeX编译五页新报告、修复表格段落和照片尺寸后逐页渲染查看。此前Draw.io可编辑图继续保留，本轮未冒称重新绘制。没有调用Claude模型，也没有生成伪装实拍的图片。

证据：S8_RESULTS、S8_MANUSCRIPT_REVIEW、S8_INDEPENDENT_AUDIT、reports/S8/report_qa.json；完整CSV/逐查询几何另存。S8的旧具体模式未重现不自动证明诊断框架新颖或无价值；后续idea-evaluator仍需对具体改进可证伪性与已有工作重叠单独审查。

## S9原文反证、适用性及组件成本（2026-09-06）

再次实际应用Supervisor-Skills的idea-evaluator，完整读取主技能与fatal-flaws、five-dimensions、lifecycle-capability-matching、paradigm-shift-probe参考。先判F4实际用途缺口，区分未检验效率机制与被数据否定的几何主张；五篇最近原文按对象/机制/粒度/设定比较，39份来源文件哈希归档。五维5/6/5/5/6只为机制暂评、无速度数字；新手工时与能力未知不补造。独立审稿修复必然变化、无依据周数及24查询单位三处后PASS。

已读科学批判思维的控制混淆和证据分层原则继续用于：固定源码调用审查、人工桩范围明确、768保存读出纠正重复候选说明、S8包隔离审计限制、S9先冻52输入/10源码再计时。144原组件调用严格回归，计时与完整视频性能区分；只定位99%左右的渲染成本，不声称实现加速。证据S9_B_IDEA_REASSESSMENT/REVIEW、S9_B_NOVELTY_EVIDENCE、S9_B_WORKLOAD_APPLICABILITY、S9_B_CANDIDATE_QUOTA_CORRECTION及S9_COMPONENT_PROFILE_*。

没有为了技能数量调用不适用的绘图、图像生成或外部服务；本轮没有调用Claude模型、重做旧PDF/Draw.io或重新进行全领域综述。

## S10保持输出的工程比较与报告（2026-09-06）

继续落实Supervisor-Skills的评测设计/idea-evaluator证据边界和已读Claude本地科学批判思维：先60人工边界、5故意错误变体及独立静态检查；保持Python float/FP32弱标量比较语义，4份NumPy官方全文与本机探针核查；根另冻结12源码/52输入后实际同进程AB/BA配对。不拿S9历史时间当本轮对照、不把24已见查询/五次重复包装成新样本、不用7.78倍工程差异冒称论文创新。执行前相等门补C bytes区分±0；每次保存真实数组与完整trace供事后核验。

实际再次阅读并应用figure-designer主文件及experimental-results/tools/design-rules：选择全部24查询的两面板分组点图，五次中位数及min/max范围，双编码/共同零起点/可读字体，矢量PDF/SVG和完整CSV。根逐页检查图例位置并修复。PDF skill读取、按合同一次调用artifact启动标记，用用户已有XeLaTeX编译三页中文报告，最终全部3页渲染查看，零溢出/缺字警告；延续本项目LaTeX制作流程。没有为这类数值图调用生成式图片或重新用Draw.io画无必要流程。

不同作者12738检查实际重开336 NPZ/1008数组及336trace，另同作者不同脚本224547检查含独立累票/NMS分支/全部汇总复算。同作者审计首次docstring缩进误拒及修复均保留；没有改原实验或计时重跑。来源、范围、有限正确性与跨版本限制写在S10各审查和S10_FIGURE_DESIGN_AND_QA。没有调用Claude模型、重新推理CUT3R或产生冒充实拍的新图。

## S11更广输入与来源控制（2026-09-06）

继续应用已读Supervisor-Skills和Claude本地科学批判思维的证据分层、控制混淆、事前固定与反例原则：地图域192条件明确168新增/24继承；来源域固定五规则、全部合格行、六预选查询，不看可见性或改选幅度挑样本。独立只读集审查证明来源不在renderer依赖内，实参守卫拒绝18个错误；参考回放与候选真实渲染分别记录。来源不足合法返回1/3，旧记录器硬要求4在运行前修正，不改实际选择器。逆序六条件的零变化照实保留，来源人工变化不称真实建图或视频证据。

通过不同作者读取实际数组/完整trace、独立规则重建与按保存距离NMS回放核验；同作者不同脚本复算单独注明。来源审计器第一次标签错误和修正保留，原实验判据/输出不改。S11没有性能重测、新模型、照片生成或Claude模型调用；没有为增加技能数量重做PDF/Draw.io。本阶段没有新一轮文献综述或完整idea-evaluator，新方法用途与新颖性复评是下一步。可审查证据为S11两份协议、执行冻结、前置审查、三份结果审查及S11_RESULTS。

## S12用途诊断、创新否决与公平对照（2026-09-06）

实际重读并应用Supervisor-Skills的idea-evaluator及其fatal-flaws、five-dimensions、lifecycle-capability-matching、paradigm-shift-probe：先以五篇定点原文核普通新增覆盖贪心的重叠，当前C0定位得到CRITICAL的Reject and Pivot；没有用更多实验或更换措辞把已知规则写成新方法。该判断只否决当前简单规则的创新定位，C0没有运行，不能写成被数据反驳。定点近邻检索不是新的全领域deep-research综述，范围和原文链接固定在S12_COVERAGE_NOVELTY_SCOUT。

继续采用benchmark-paper-template的评测公平性原则，但只做其相关部分，未冒称完整成熟benchmark工作流：发现旧all20基线与源14候选数不同后，另冻结两方均14候选、同4输出、同NMS的24个已见查询诊断；两方都使用预测几何，故不写成“有几何/无几何”或同计算成本。新pose14选择封存后才读support/valid用于评分，S7开发、S7测试、S8测试分列，192地图/密度行只作为相关敏感性，不当独立样本。独立数值审计23647门和文稿机械8249门的实际范围分别记录，不将检查门数包装为样本数。

pre-submission-reviewer的宏观归因、证据范围、夸张词与可读性检查用于中文Markdown/CSV的最终核对；一项“首次解码”时间标签经审查改为准确的解码前标记，并补明记录型decision_trace和1e-12派生均值容差。此阶段没有调用Claude模型、没有生成图片、没有重新运行PDF/Draw.io或完整VMem；S12_RESULTS、S12_MATCHED_BUDGET_INDEPENDENT_AUDIT、S12_MANUSCRIPT_REVIEW及其冻结/CSV是可查证据。


## 2026-09-06 13:08定时接续

新增不同作者S14正式方法审读（idea-evaluator四参考、本地Claude科学方法/实验设计/统计陷阱），根纠正裁定对象后最终落盘；另agent用官方场所与统计原文完成新场景计划。根做输入映射、24文件字节身份、5定点补充检索和28项纯公式复算，S14B只写测量草案。没有模型/GT/新数组实验；没有Claude模型调用。证据见S14_RESEARCH_DECISION_2026-09-06。
