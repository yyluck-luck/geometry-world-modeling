# academic-figure-generator 全仓读取与本项目用法

完成记录时间：2026-09-08T14:08:30.653926+00:00（北京时间 22:08:30）。这是接续中断前阅读后的团队覆盖报告，不是逐文件工时记录。正式发布时刻、逐文件 SHA256 与范围见同目录 `academic_figure_generator_coverage.json`。

## 读取范围与证据

- 来源：[LigphiDonk/academic-figure-generator](https://github.com/LigphiDonk/academic-figure-generator/tree/0a2bec6bb56d6b47143a81909f8d818716bdcbab)，固定 commit `0a2bec6bb56d6b47143a81909f8d818716bdcbab`；本机副本 `vendor/academic-figure-generator/`。
- 118 个 Git 跟踪文件全部盘点、校验身份：110 个文本逐行全文覆盖，其中 5 个为空文件，非锁文件文本共 11,403 行。中断前 WIP 记录 47 个全文已读文件；本代理接续读完余下 63 个，并重新全文读取两个独立 SKILL.md。旧阅读记录不是本代理亲历，coverage 将两者分别标记。
- `frontend/package-lock.json` 采用完整 JSON 结构读取：lockfileVersion 3，382 个 package 条目（含根条目），381 个依赖条目均有 registry.npmjs.org 地址与 integrity；2 个安装脚本标志对应 esbuild、fsevents。没有把 5,682 行自动生成锁文件称为逐行语义精读，也没有执行其安装脚本。
- 7 个二进制只登记格式/大小/哈希，未解码查看：SQLite 数据库、四张示例图、两张 logo。源码阅读完成不能称为“全部图片已看过”或“数据库内容已审查”。
- 三个长文件分段完整读：system_prompt.py 第 1–240、241–550 行；phase2-technical-design.md 第 1–320、321–670、671–950 行；ProjectWorkspace.tsx 第 1–310、311–585、586–835、836–1147 行。一批输出曾截断 figure_types.py 约 119 token，随后重读第 1–100 行补齐，余段已在原输出完整返回。
- 最终 118 项 SHA256 全部与初始 inventory 匹配，Git 工作区无改动。本轮没有运行仓库程序、构建前端、安装依赖、调用 Claude/图像/OCR API、提交凭据或生成图片。因此以下功能判断是源码判断，不是运行验收。

## 仓库各部分实际提供什么

| 范围 | 阅读所得 | 本项目如何使用 |
|---|---|---|
| README、LICENSE、环境样例、配置 | MIT；个人版前后端、SQLite 与本地文件存储，依赖外部模型生成内容 | 固定版本并使用独立技能；当前没有科研必要性安装完整平台 |
| `academic-figure-prompt/SKILL.md` | v1.0.0；四层描述：全局、分区、跨区标注、风格。默认白底、细边框、受限配色；8 个选择含自定义 | 采用明确数据流、语义配色、可读标签与图例；尺寸、公式只能来自已知事实 |
| `academic-figure-prompt-pastel/SKILL.md` | v4.0.0；白底、柔彩 token、圆角字体、轻阴影、按内容分配面板；4 个选择含自定义 | 作为汇报示意图备选风格。保留纯白和有含义的 token，减少阴影；不能把自称 ICML/ICLR 风格当会议官方标准 |
| backend API、models、schemas、配置及中间件 | 文档/项目/提示词/图片/配色 CRUD，文件解析与生成状态管理 | 不影响科研方法；不能拿网页上的 completed 直接当实验成功 |
| 文档服务 | PDF 按字号启发式分段，DOCX 按 Heading，TXT 按 Markdown 或段落分割 | 公式、表格、图片和双栏顺序仍需核对源文档；这里未用它解析本项目 proposal |
| ClaudeCodeService | 从独立 SKILL.md 加载 system prompt，经 Claude Agent SDK 请求，`allowed_tools=[]`；每节内容截到 8,000 字符；解析输出 JSON | 用户只授权 Claude 的技能，不调用 Claude 模型；由当前助手直接使用该规范，避免内容截断被误称全论文理解 |
| image_service / images API | 默认 api.keepgo.icu，OpenAI 风格 `/v1/images/generations`，固定 gemini-3-pro-image-preview；HTTP 同步调用放入 executor，结果保存为 PNG | 这是仓库自己的第三方接口，不等于用户已经登录的 Gemini 网页或 Google One 权益；本轮不调用该接口 |
| OCRService | 将文件编码后发到用户配置的 PaddleOCR layout-parsing 服务，返回 Markdown | 文件会离开本机；当前没有调用或配置。继续优先已有本地解析工具 |
| frontend 页面和 16 个 UI 组件 | React 19/Vite/TypeScript、项目树、章节选择、生成设置、状态轮询、图片下载和编辑 | 仅理解使用成本与输出边界，不把搭平台当成研究创新 |
| `.omc` 元数据、初始化与种子脚本 | 元数据为仓库历史；init_db.sh/seed_color_schemes.py 仍包含 PostgreSQL、Alembic、MinIO 与 user_id 假定 | 历史文件与当前个人版不同；不照着旧脚本初始化我们的研究环境 |
| Phase 2 两份文档 | SVG/Draw.io 可编辑输出、FigureSpec V2、Vision enrichment、Celery/MinIO 工作流均为设计和实施计划 | 清单里无相应 exporter/exports API 实现；不能称仓库现已提供可验证的可编辑图导出 |

锁文件的实际解析版本为 React/ReactDOM 19.2.4、Vite 7.3.1、TypeScript 5.9.3、Axios 1.13.6、Zustand 5.0.11、Tailwind 3.4.19。这只是固定仓库的版本，不是本机已安装版本或当前最新版本。

## 对创新优先级最有用的判断

这个仓库帮助表达机制，不提供新的世界模型算法。现在最有用的动作是把问题、已有路径和待验证因果关系画清楚，使老师能看出我们到底打算检验什么；不是提前画一个“新模块已经成功”的架构。

当前依据 `work/S51_innovation_math_guidance/LITERATURE_AND_MATH_ADDENDUM.md`、`work/S52_next_discriminating_prediction/RESEARCH_DECISION.md` 和本轮重新读取的 `vendor/vmem_snapshot/modeling/pipeline.py:1123`：VMem 的语义分支将来源向量求平均，再复制为每相机的单 token；另一条 context-latent 路径仍按来源保留条件。均值映射丢失来源分解是标准线性代数性质，**不能推出整个模型没有来源信息，更不能推出生成受损或新方法有效**。

本轮没有查看 C1/C2 像素或改动它们的实验规则。运行数量与当前状态以 root 的最新主账为准；这份静态仓库报告不覆盖后续实验进度。`new_method_validated=false`，本读取任务新增经验证原创贡献为 0。

## 与科研证据冲突的模板要求怎样处理

1. 独立技能要求展示配色并等待用户确认。用户已多次明确授权自主推进、不为常规选择提问，因此当前草稿自主选 A/Okabe-Ito；柔彩备选选 P2/Cool Research。这是用户持续授权覆盖技能的常规确认步骤，不虚构用户曾亲自选色。
2. 仓库要求高信息密度、许多缩略图、示意波形/热图；后端 template prompt 甚至要求忽略论文内容并填入结构占位图。**科研图不采用这些填充性要求。** 未测量的热图、损失下降、散点分簇、置信区间、最佳指标、照片差异均不生成；没有内容时删掉面板，不填假结果。
3. 两个技能风格不同：普通版细边框，pastel 版微阴影；后端旧 system prompt 又禁止阴影。一次图稿只选择一个明确风格，不能要求生成器同时满足冲突指令。版式模板不是会议官方政策。
4. 已有 Supervisor `figure-designer` 区分 motivated example、方法概览与结果图，并要求可读的矢量输出。我们采用其“具体例子说明问题”的逻辑，但当前尚无已确认的新方法成功对照，所以此时只能交付**问题示意草稿**，不能称完整论文 Figure 1 已满足失败/成功证据门。未来实际照片与结果面板直接使用原始实测输出；图文/箭头用矢量，照片保留原始像素，不机械排斥必要的 raster 数据。
5. 标准数学、绘图质量、阅读仓库和代码修复均不增加原创贡献。ICML、NeurIPS、ICLR、CVPR 等启发仍要落到最近工作差别、可推翻预测、强对照和真实收益。

## 可以直接实施的 Figure 1 草稿

**工作标题：** Does a recalled view actually help a revisit?（检索到的历史画面真的帮助重访了吗？）

**当前类型：** 面向导师的研究问题示意，不是结果图、完整方法图或已验收的论文 motivated example。以后若有真实自然失败，再将同一场景的实际失败与可信对照放入正式 Figure 1；当前不预画赢家。

**布局：** 双栏宽 178 mm × 86 mm，三面板。左 25% 为线描房间与三次相机位置，标注“schematic revisit”，不仿造真实照片。中 45% 为已核源码中的两条条件路径；三枚来源符号只表示示例 K=3，不代表已执行的某组检索数量。右 30% 为三个不同的开放问题：影响输出、影响是否落在几何支持区、是否降低独立参考误差。右侧用问号与虚线，避免勾号或绿色成功暗示。

**标签和公式：** 中间上路为 e₁,e₂,e₃ → c=(e₁+e₂+e₃)/3 → semantic condition；下路为 source latents → latent condition；两路进入 VMem generator。相机和噪声是共同输入。小注只写“Mean path merges source features; latent path remains”。不写“VMem loses all memory”。

**语义配色：** 已有语义路径蓝 #0072B2、已有 latent 路径深灰 #546E7A、待检验关系橙 #E69F00；纯白背景，黑/深灰正文。颜色加实线/虚线与直接文字双编码。实际字号按最终插入尺寸保持 ≥8 pt，主标签 9–10 pt；如果公式拥挤就移到图注。

**图注草案：** “VMem combines a mean semantic condition with a separate context-latent path. The diagram illustrates a revisit and three questions for source-specific memory evaluation: output influence, spatial localization, and signed benefit against an independent reference. The mean-path property is a source-code and mathematical observation; the questions on the right remain unvalidated. All room drawings and source tokens are schematic, and no empirical comparison is shown.”

**工具路线：** 使用已读独立技能生成下面的版式提示词。若需要 AI bitmap 草图，交给当前可用的正式 image generation 工具或经实际访问核实的 Gemini；提示词/输出/采用理由记录在本地。论文最终结构、文字和公式使用本机 Draw.io/TikZ 等重建为可编辑矢量；真实指标直接由原始表格经 Matplotlib/PGFPlots 生成。本报告未调用这些绘制步骤。

### 英文提示词草稿（采用普通版四层结构，尚未送入生图工具）

```text
Create one research-question schematic for a geometry-aware video world-modeling project. The title is “Does a recalled view actually help a revisit?” The figure explains a source-code observation in VMem and several open evaluation questions. It does not present a new method or an experimental improvement. Use a white landscape canvas with three panels. The left panel occupies approximately one quarter of the width, the middle panel occupies slightly less than half, and the right panel uses the remaining width. Keep all placement measurements as invisible layout instructions. Do not render rulers, crop marks, coordinates, or layout measurements.

=== PANEL A: SCHEMATIC REVISIT ===
Draw a restrained line illustration of a room containing a chair and a window. Add three small camera symbols linked by a curved path that returns near its starting position. Label the panel “Schematic revisit”. Use simple geometric line art without photorealistic texture. No camera position is ground-truth data. Below the illustration, place three small white source cards with blue outlines labeled “Source 1”, “Source 2”, and “Source 3”. Each card contains the same simple chair outline viewed schematically from a different direction. Label the cards collectively “Illustrative selected views, K = 3”. These are conceptual source identifiers, not measured retrieval results. Do not draw a failed reconstruction, a corrected reconstruction, a difference map, or a before-and-after claim.

=== PANEL B: TWO EXISTING CONDITION PATHS ===
Title this panel “Existing VMem conditioning”. Draw an upper semantic path in blue and a lower context-latent path in dark grey. The upper path has three labeled feature symbols “e₁”, “e₂”, and “e₃” feeding a mean operation. Render the exact formula “c = (e₁ + e₂ + e₃) / 3” beside that operation. Connect the result to a block labeled “Semantic condition”. The lower path has separate source symbols feeding a block labeled “Context-latent condition”. Keep the separate-source structure visible in this lower path. Both conditions connect with solid arrows to one block labeled “VMem generator”. A small side input labeled “Camera and noise” also enters this generator. Its output is a plain outlined rectangle labeled “Generated revisit”, with no invented image inside. The rectangle is a symbol of an output, not an empty slot requesting an imagined result. Place the short annotation “Mean path merges source features; latent path remains” beneath the two paths. Do not suggest that the semantic mean proves the entire model has lost source identity. Do not highlight any component as ours or novel.

=== PANEL C: OPEN QUESTIONS ===
Title the right panel “Questions to test”. Use three vertically aligned text-and-symbol items connected from the output by orange dashed arrows. The first item reads “Output influence?” and contains two small neutral output symbols, without a visible difference invented between them. The second reads “Spatial localization?” and contains a simple outlined region icon labeled “Geometric support”, without a heatmap. The third reads “Signed benefit?” and includes a neutral reference-card symbol labeled “Independent reference”, without a numeric score. Keep a visible question mark for each item. No item has a check mark, upward trend, winning color, or success badge. Add the small footer “Hypotheses pending empirical validation”.

=== GLOBAL ANNOTATIONS ===
Use solid connectors for source-code-established condition paths and dashed connectors for questions requiring experiments. Include a concise legend stating “Solid: existing path” and “Dashed: planned test”. Explain every abbreviation in the caption or labels. Preserve a single clear left-to-right reading direction. The room, cameras, and source tokens are schematic illustrations only. Do not invent tensor sizes beyond the explicitly stated K = 3 illustration. Do not add metrics, charts, error bars, attention maps, model accuracy, citations, logos, or conference award references.

=== STYLE SPECIFICATIONS ===
Use white #FFFFFF throughout, blue #0072B2 for the existing semantic path, dark grey #546E7A for the context-latent path and structural lines, and orange #E69F00 only for open-question connectors. Use dark #333333 body text. Use thin outlines, modest corner rounding, and a consistent readable sans-serif font. Typeset mathematics cleanly in a compatible mathematical font. Keep labels legible at the final printed width; target 9–10 point primary labels and at least 8 point annotations after scaling. Let content determine spacing and do not fill space with decorative scientific-looking plots. No gradients, heavy shadows, perspective effects, glossy tokens, or photorealistic room images. Preserve semantic distinctions through words and line styles as well as color.
```

柔彩备选只改变样式：使用 P2 的浅蓝 token #B3E5FC、浅靛 #C5CAE9、文字 navy #1565C0 和圆角字体；所有标签、箭头含义、证据边界与待验证问号完全不变。token 色彩不表示新颖性或实验优劣。

## 交付自核及下一步

- 阅读覆盖与身份：完成，逐文件 JSON 可核；二进制未视觉检查，锁文件只有结构检查。
- 提示词科学内容：已对照 S51/S52 和实际 `get_cond` 片段；显式保留另一条件路径，未把标准数学称新定理。
- 图型：已明确为研究问题草稿。正式论文 Figure 1 仍需真实失败例子、正文 running example 一致性和相关证据。
- 图像视觉质量、字号、灰度可读性、矢量结构：尚未绘制，未验证，不能填 PASS。
- 下一步先由 C1/C2 的可信评分决定是否存在适合展示的自然失败；将真实反例与最近 ICML/其他顶会机制差别结合后，再决定正式图的核心主张。不要让建图平台或漂亮示意图占用算法与判别实验的优先级。

附：静态阅读发现 ProjectWorkspace 只轮询 `processing`，而后端写 `generating`；OCR 按钮请求的路由不在已读 documents API 内；template_mode 在 schema 中存在但生成服务调用未使用。这些是源码层的接口不一致，未运行复现。本次不修理外部平台，避免偏离用户研究主线。一次误查旧路径 `vendor/VMem/vmem/pipeline.py` 返回不存在，随后从现有 S51 路径定位并实际读取正确的 `vendor/vmem_snapshot/modeling/pipeline.py`，没有把错误路径写成证据。
