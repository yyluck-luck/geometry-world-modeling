# S28 figure-designer 实际应用与质检

完成时间：2026-09-06T17:24:59.592148+00:00。完整绘图输入只有两个 `gradient_depth_trace.jsonl`、各臂 `receipt.json`、评分 `metrics.json` 与 `receipt.json`；六文件 SHA 和实际运行命令见 `plot_receipt.json`。最终状态 `PASS_SAVED_LOG_FIGURE_VISUAL_QA`，是已有记录绘图通过，不是新实验数值审计。

## 1. Figure type

Supporting experimental-results figure：比较同一工程修复的优化轨迹、几何量变化与最后的外部误差。

## 2. Paradigm recommendation

选择两个时间序列折线图加一个逐帧配对点图。折线保留每步；点图适合此处仅两个方法、四个帧和一个明确的聚合项。未选 grouped bar，因 AbsRel 集中在 83–88%，点图可明确标示 75–95% 的可视范围而不引入有长度含义的截断柱形；没有重复运行，所以不画箱线或误差条。热力图或流程图不对应当前数据。

## 3. Layout sketch

7.5×3.2 英寸横排三联。左：0–399 已完成步的更新前 objective，加实际 400 步后收据值菱形；中：F0–F3 四条修复轨迹及全部原曲线，后者精确重合在 1 且文字明确标记；右：F0–F3 和独立分隔的等帧均值，每行两点，灰线仅连接配对而非置信区间。无跨图因果箭头。

## 4. Labelling and annotations

使用 Original 与 Gradient-only repair，不标 Ours。Okabe–Ito 色盲友好蓝 `#0072B2` 和橙 `#D55E00`；方法另以虚实线／圆与方形区分，中图四帧另用实／虚／点／点划线及圆／方／三角／菱形。正文标签 8–9 pt，原生画布最小 8 pt。左图明确 log scale，右图百分数，图注定义 AbsRel 和“逐像素深度比例均值”。终点保留负结果，未画未测的逐步 GT 误差。

## 5. Tool suggestion

实际用 Matplotlib 3.10.9 与可复现 `plot_s28.py`，导出真正向量 PDF/SVG 及显示 PNG；PGFPlots 可在确定最终论文模板时再考虑。没有手工改图，也没用图像生成模型。

## 6. Universal rule audit

- Vector：PASS，PDF 不含 image object，SVG 无 image 标签。
- Font：原生 7.5 英寸宽 PASS；后续论文若缩窄，需要重新布局，尚未做最终版式检查。
- Colour-blind / dual encoding：PASS，色彩之外有线型与点形。
- Caption：PASS，首句讲客观负结果，量纲、初态、一次运行及限制均明确。
- Axes：PASS，完整 0–400 步、不截尾、不平滑；loss log 明示，中图 0.6–1.1，配对点图 75–95% 明示。没有 GT 比例校准。
- Chartjunk：PASS，无 3D、阴影、面积暗示或显著性星号。

## 7. Integrity gate result

1–4、7：PASS。第 5 项通过实际 `view_image` 逐版检查；第 6 项 motivated-example 与 Introduction 一致性不适用于此辅助实验图。未声称已作整篇论文送审。

## 8. Severity summary / 实际工作记录

最终原生图 0 CRITICAL、0 MAJOR、0 未修 MINOR。首版图例偏挤、B 终点标签近轴，第二版长 xlabel 靠近边界，均仅改排版并重看；旧版与 QA 留在 `render_v1/`、`render_v2/`。

最初 `.venv-cut3r` 和 Codex bundled Python 均无 Matplotlib，两次在 import 阶段失败，分别留在 `attempt_01_missing_matplotlib/` 和 `attempt_02_bundled_missing_matplotlib/`；未安装或更改实验环境。最终使用本机 Homebrew Python `/opt/homebrew/opt/python@3.13/bin/python3.13`，实际命令、秒数和各次 SHA 均保留。所有重做仅是绘图，无模型／GA／传感器评分／NPZ读取。
