# 附件审查：对话中新增事实主张的独立核验

<!-- EXPERIMENT_NAME_LEGEND_20260912_BEGIN -->
> **S编号与具体试验名称说明（2026-09-12更新）**  
> 文档中的 `S86`–`S90` 是项目内部阶段编号，保留它们是为了让结果、日志和回执可以追溯；括号内是给新读者看的具体名称。编号不是论文术语、结果等级或“实验成功”的标志。S88–S90主要是数据资格/传输与协议审查，不能误读成模型性能实验。
>
> - **S86（单场景四目标几何条件注入基线实验）**：在一个已见静态场景、四个相关目标上，比较历史几何注入方式的真实生成链和RGB误差。
> - **S87（末端引导强度控制与多步引导必要性反例实验）**：复用S86缓存，比较末端处理强度与持续多步引导；它只检验该已见场景的有限反例，不验证GRC或长期几何收益。
> - **S88（RTMV相机JSON元数据与静态投影数据资格检查）**：核对归档身份、相机元数据和可访问的静态文件头；不是RGB-D配对性能实验。
> - **S89（RTMV配对数据TLS接续失败审查）**：记录两种TLS/传输接续尝试及其失败边界；失败本身不等于数据缺失或科学负结果。
> - **S90（RTMV归档配对数据恢复与索引协议审查）**：检查受限Range传输、归档成员身份、断点恢复和索引安全条件；已恢复的512B文件头不等于取得可用深度正文。
>
> 后续报告首次出现编号时应同时写成“**S86（单场景四目标几何条件注入基线实验）**”这类形式；后文可使用编号，但不要只写编号来替代试验名称。
<!-- EXPERIMENT_NAME_LEGEND_20260912_END -->


核验时间：2026-09-11（Asia/Shanghai）。范围是附件 `c7e912b3-3c59-4889-a546-53021e91f41e/pasted-text.txt` 中声称的 COVRAG、WorldTrace、SWIM，以及 2×2 和“零额外完整引导链”。本文件只做来源和协议核验，不重跑模型、不修改主账。

## 结论

### COVRAG：已在本地原文记录，主张基本成立但不能扩大

项目已有原文快照 `work/S12_literature_sources/covrag_arxiv_v1.html`，SHA-256 为 `a95bc73710488c700924cc80ede4ae969054249c77127786a04537dcdc90830d`；`docs/S12_COVERAGE_NOVELTY_SCOUT.md:18`、`docs/S14D_TARGET_VIEW_NEAREST_METHODS.md:10-18` 和 `docs/S9_B_NOVELTY_EVIDENCE.md:77-91` 均给出可定位的章节和边界。记录的机制是：用源深度/姿态把历史内容投到目标网格，维护二值覆盖，并按剩余覆盖的边际增益贪心选择历史帧（§4.1–4.3，Eq.2–4，Algorithm 1）。因此，“普通 coverage/残余覆盖选帧已经有直接先例”可以保留。

附件把它概括成覆盖最大化检索，方向正确；但不能说 COVRAG 已验证了本项目的几何风险或未来位置误差，也不能说已完成代码复现。项目原文记录明确：这是 predicted-depth projected pixel occupancy；没有目标实测深度核真，覆盖不等于正确表面可见性。COVRAG 的会议接收状态也未在本地独立核定，应称 2026 arXiv 预印本。

### WorldTrace：已记载为可寻址记忆近邻，但不是“变点/风险模型”证据

`docs/LITERATURE_SYNTHESIS_V2.md:36` 将 WorldTrace 列为生成影像的条件/世界状态工作，并正确链接 arXiv:2608.07408；同一行前一项 Spatia 才是 arXiv:2512.15716。此前本报告把相邻 Spatia 编号误读成 WorldTrace 编号，现更正。`RESEARCH_PRINCIPLES.md:105` 也把 WorldTrace 作为“address/consume”近邻压力的一部分。该证据支持“可寻址视频世界模型记忆已有先例”，但不能扩张为 GRC 全部问题。

它不支持下列更强表述：WorldTrace 已提出几何风险校准、逐条历史记忆的未来位置误差预测、变点检测，或与 GRC 完全相同的选择目标。附件若把 WorldTrace 直接写成“已占据 GRC 的全部问题”，属于过度外推；应保留具体差异（地址化记忆/读取机制 vs. 项目候选的风险前测量和 held-out 几何评价）。

### SWIM：本地没有“世界模型变点”证据；公开原文指向另一类工作

对项目 `docs` 和 `work` 的精确检索没有找到把 SWIM 定义为动态世界模型变点检测器的原文条目。网络原文入口 `https://human-world-model.github.io/` 将 SWIM 定义为 **Structured World Models from Human Videos**：从人类视频预训练结构化动作/世界模型，再用少量机器人轨迹微调并规划；它不是 Bayesian change-point、共同合法前缀或视觉记忆失效模型。对应论文 PDF 入口为 `https://human-world-model.github.io/resources/swim_paper.pdf`。

因此附件中“SWIM 正是世界模型中的变点”不能作为事实引用，当前应标为**未核实/很可能名称混淆**。检索结果还显示 SWIM 这一缩写有无关含义（例如 Selective Write-Verify for Computing-in-Memory），更加不能仅凭缩写建立近邻关系。若要主张“变点记忆已有直接先例”，应另找并逐段核对真正的世界模型 change-point 论文；本次没有将 SWIM 计入该证据。

### 2×2：是竞争解释诊断，不直接验证 GRC 的核心预测

本地设计 `work/S88_independent_geometry_data/INNOVATION_COMPETING_EXPLANATIONS.md:23-45` 和 `work/S89_matched_view_index/innovation/GEOMETRY_VS_APPEARANCE_DIAGNOSTIC.md:43-49` 定义了几何来源（预测几何/独立源几何 oracle）× RGB 末端算子（`.75`/`1`）的四格。它可以检验：重影是否随几何来源、颜色复制强度及其交互而变化；在独立位置/轮廓参考、固定随机流和多场景重复下，它是有判别力的受控诊断。

但它**不直接验证** GRC 的第一轮假设
`低几何风险的历史 -> 更低的未来位置误差`，原因有三点：

1. 四格没有实现“从候选历史中选择记忆”的策略，也没有 `a_i/q_i`、固定 `k` 或选择后风险；它改变的是一个几何输入轴和一个 RGB 端点轴。
2. 预测几何与独立几何的差是 oracle 的来源替换合并效应，不等同于由过去可计算的风险分数对历史排序。
3. 若没有输出封存后的独立未来位置/轮廓真值，四格只能说明合成 RGB 差异；即使有该真值，一次四格也只能检验竞争机制，不能建立跨场景风险—未来误差关系。

因此它应写作“最小竞争解释/因果诊断门”，而不是 GRC 方法验证。GRC 仍需要 prospective、时间/场景隔离的候选特征、固定预算选择、独立 future geometry 评分及与 recent-k、camera-distance、coverage、utility-only 等基线的比较。

### “零额外完整引导链”：对当前已见场景成立，对外推不成立

`INNOVATION_COMPETING_EXPLANATIONS.md:25-36` 的“0额外完整引导链”依赖 S86/S87 已保存的普通底图和末端状态，复用同一已见静态场景、同一源 RGB/相机/投影规则，仅派生 `.75` 与 `1` 两个端点。它确实能减少本地计算，并且不必重复已成功的多步生成。

这句话不能被解释为“无需额外计算即可验证 GRC”或“已经跨场景”。它依赖同场景缓存和已见结果，因而只能产生低成本的诊断信号；缓存派生也不能替代新场景的独立 RGB-D、相机配对和未来位置真值。任何使用该协议的报告都应明确标为 saved-state/endpoint diagnostic，并保留 S87 的旧场景选择偏差。

## 对附件评分/结论的纠正建议

- COVRAG：`direct nearest precedent` 可保留；“已复现/已证明风险”删除。
- WorldTrace：`addressable memory precedent` 可保留；“已占据 GRC 全部问题”降为待比较差异。
- SWIM：删除“变点模型”描述，改为名称未核对；不要将其计入变点先例。
- 2×2：改称 controlled diagnostic；只有独立未来位置真值、重复和跨场景后，才可谈对 GRC 假设的支持。
- 0 extra chain：标注为同场景 saved endpoint reuse；不能当新实验、跨场景验证或方法收益。

本核验支持的总体状态仍是：`NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false`。

更正记录：本轮初稿的 WorldTrace 编号归因错误来自阅读同一表格相邻链接，并非项目旧综述错误；项目旧综述的 WorldTrace 链接已由 root 复核为 arXiv:2608.07408。

## 极小合成 2×2 逻辑核验（非真实实验）

脚本 `two_by_two_logic_check.py` 已执行；结果 `two_by_two_logic_results.json`，脚本 SHA-256 `69465fc7a09ff38fb5ef11e6fca80bc3014cdacf964989603d0f9578f50a1cb8`，结果 SHA-256 `4ef4d5b54c520a556b2897e77f8222b130a167d5f4e10ec732c3fc759d6f0a87`。场景 A 中两种 memory 的交互项均为零，但 low-risk memory 的四格平均未来损失更低；场景 B 中 memory_B 具有非零交互项，但两种 memory 平均损失相同。四项断言全部通过。因此，2×2 交互既不是 GRC 收益的必要条件，也不是充分条件；该结果只是代数/合成逻辑反例，不能替代真实 RGB-D、独立未来几何真值或跨场景实验。
