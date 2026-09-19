# GeoCausal核心图设计与完整性审计

## 1. Figure type

- Type: `solution-overview`，当前不是最终motivated-example Figure 1
- Reason: 尚未得到通过相机守卫的自然失败；现在若画“现有方法失败、我们成功”的Figure 1会虚构结果。当前可以诚实画出待检验的证据合同和已有执行边界。

## 2. Paradigm recommendation

- Paradigm: 左到右的“普通运行证据→因果审计→条件式决策”三段solution overview
- Why this paradigm: 它能在30秒内解释为什么“存了/选了”不等于“正确且有益地用了”，并把每个未来实验直接挂到一个节点。
- Alternatives considered and rejected:
  - `Existing vs Ours`：当前没有经验证的新方法效果，不能画绿色成功输出。
  - `Performance teaser`：只有B0一行且无严重事件，没有可用于主张优势的数据。
  - `Running example + failure`：等C1/C2发现通过相机门的自然失败后再制作；不得用合成失败代替。

## 3. Layout sketch

- Canvas: 1200×520，最终双栏宽约178 mm；白底、紧凑画布。
- Panels:
  - 左侧`A. Ordinary VMem run`：Source ID进入Store，普通Select选出来源，Address把它送到consumer；下方只放已验证事实“C1 readback: ID2/4/1 entered second-batch conditioning”。
  - 中间`B. GeoCausal audit`：post-selection coherent intervention进入全部appearance paths；输出差异图与199个matched masks比较；独立withheld real return reference给出signed benefit。
  - 右侧`C. Conditional action`：只有前门全通过才进入Accept / Reject / Re-observe；以虚线和`future method, not validated`标记。
  - 底部灰色证据条：B0 MSE 0.005278、C1未评分、C2未生成、novelty authorization NONE。
- Arrows and connections:
  - Store→Select→Address使用实线蓝箭头，表示普通执行链。
  - Address→Influence→Localization→Benefit使用紫色实线，表示待验证合同。
  - 任一审计门到`STOP / downgrade`使用红色虚线；Benefit到条件决策使用绿色虚线。
- Colour assignment:
  - 已观察执行事实：Okabe–Ito blue `#0072B2`。
  - 待检验审计：purple `#6A51A3`加圆角实线框。
  - 条件成功路径：green `#009E73`，同时加`PASS`文字。
  - 阻断/停止：vermillion `#D55E00`，同时加八角STOP形状。
  - 未验证状态：grey `#6B7280`加虚线。

## 4. Labelling and annotations

- Element names: `Store source`, `Ordinary Select`, `Address consumer`, `Post-selection Influence`, `Geometry Localization`, `Signed Benefit`, `Accept / Reject / Re-observe`。
- Critical highlights:
  - 中央大字：`Stored / selected ≠ used correctly ≠ beneficial`。
  - Influence下标：`all appearance paths; exact replay + two edits + sham`。
  - Localization下标：`true support vs 199 matched masks`。
  - Benefit下标：`withheld real reference; B_local + B_matched`。
- Font sizes: 14–18 pt原画布；缩放进双栏后不低于8 pt。
- Colour palette: Okabe–Ito/ColorBrewer兼容；所有颜色同时由边框样式、形状和PASS/STOP文字编码。

## 5. Tool suggestion

- Primary: draw.io，保存可编辑`.drawio`，导出SVG/PDF。
- Alternative: TikZ，仅在论文版式最终稳定后重绘。
- Reason: 当前图是模块化协议图，本机draw.io可离线编辑和矢量导出；实验结果图以后用Matplotlib生成。

## 6. Universal rule audit

- [x] Vector format: `.drawio`可编辑源与最终PDF；`pdffonts`确认Helvetica/Helvetica-Bold以CID TrueType嵌入。draw.io的SVG含HTML文字fallback PNG，只作辅助预览，不作为论文最终文件。
- [x] Font size: 原图不低于14 pt，按双栏缩放后目标≥8 pt。
- [x] Colour-blind safe: 蓝/紫/绿/朱红且有形状/线型/文字双编码。
- [x] Self-contained caption: 首句明确该图展示的是待验证合同，不是已证实增益。
- [x] Honest axis range: 不适用；无数据坐标轴。
- [x] No chartjunk: 无3D、阴影、渐变或装饰图标。

## 7. Integrity gate result

- Gate 1：PASS，solution overview不是结果图。
- Gate 2：PASS，三面板、节点、箭头、颜色均具体。
- Gate 3：PASS，全部为真实VMem/GeoCausal实体名。
- Gate 4：PASS，draw.io适合架构/协议图。
- Gate 5：PASS。最终PDF已用Poppler按180 dpi实际渲染并目视复核；无裁切、重叠、黑块或断箭头，PDF文字可提取，最小原始字号14 pt按178 mm双栏缩放后约8.4 pt。
- Gate 6：BLOCKED FOR FINAL FIGURE 1。自然失败尚未获得，不能声称与Introduction中的失败例一致。
- Gate 7：不适用；当前无实验图。

## 8. Severity summary

- 0 CRITICAL，1 MAJOR，1 MINOR。
- MAJOR：最终Figure 1必须等待C1/C2真实自然失败；当前图只能叫方法/审计概览。
- MINOR：SVG导出含文字fallback raster；论文使用已核PDF。数据结果产生后再决定是否把底部状态条移到补充材料。
- Top three actions first: 完成C1/C2自然失败门；若出现合格失败，用同一真实episode制作最终Figure 1；论文插图使用已核PDF。

## 自包含caption草案

**The GeoCausal Memory Contract is a proposed audit, not a validated gain.** A source counted as memory success by ordinary storage, selection, and addressing must still pass three intervention-based gates: it must causally influence the output through all appearance paths, concentrate that influence on its pre-treatment geometric support beyond matched spatial nulls, and improve an independently observed return view relative to fair alternatives. Any failed gate stops or downgrades the claim; an accept/reject/re-observe policy is considered only after cross-scene confirmation.
