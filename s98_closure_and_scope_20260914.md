# S98 收尾与范围独立审查

- 审查日期：2026-09-14（Asia/Shanghai）
- 审查对象：`work/S98_dev_window_feasibility/`、`work/agents/s98_window_independent_recompute/`、S8 协议、原始 proposal。
- 目的：判断 S98 是新科学发现还是对既有 S8 的重复确认，并纠正“proposal 规定”和“没有读取 GT/文件字节”等表述。

## 结论先行

1. **8.840 s、24 帧、50 ms、100 ms、至少 3 窗口不是原始 proposal 中写出的规定。** 原始 `Yiyang_LIU_Proposal.pdf` 只规定一学期项目范围、基线/失败分析、候选机制、评测维度和周计划；没有出现 8.840、24 帧或 50 ms。这些数值属于项目后来冻结的 S8 外部场景评测协议（`docs/S8_EXTERNAL_SCENE_PROTOCOL.md` / `_V2.md`），不能向导师说成“proposal 明确规定”。更准确的说法是：**“为落实 proposal 的可复现评测目标，项目在 S8 阶段另行冻结了窗口合同。”**
2. **对 fr2，S98 主要是重复确认旧 S8 采样结果。** 独立脚本没有导入生产窗口函数，重新实现时间关联和窗口选择；结果与 `data/cut3r/S8_fr2desk_inputs_v2/sampling_metadata.json` 的 2893 配对、6 个窗口、选择 `[0,2,5]` 一致。因此这是独立复核/可复现性确认，不是新的模型实验或新方法发现。
3. **对 fr1，S98 是新的资格边界审计，但仍不是 proposal 科学结果。** 它把“整条开发序列能否按 S8 自动产生至少 3 个固定窗口”单独问清楚，发现只有 2 个窗口。这是一个新的数据资格负结果，解释了为什么早期预先指定的两个约 8.84 s 窗口不能外推为“三窗口自动生成能力”；它不提供生成质量、几何误差、未来预测或创新方法证据。
4. **S98 的创新贡献为 0/10（资格工程审计），不能提高当前 GRC/PhD/CCF-A 完成度。** 它的价值是阻止后续把开发数据窗口数量误报成独立验证，并保留一个明确的 Gate0 约束。

## 数值和状态复核

- 主审计 `RESULTS.json`：`PASS_DEVELOPMENT_WINDOW_AUDIT_NOT_HELDOUT`，`formal_s91_run=false`、`model_inferences=0`。
- 独立重算：fr1 `FAIL_FEWER_THAN_THREE_WINDOWS`（792 严格 RGB-D 配对，788 个同 GT 区间，2 窗口）；fr2 `PASS_AT_LEAST_THREE_WINDOWS`（2893 配对，2212 个同 GT 区间，6 窗口，选择 `[0,2,5]`）。
- 两个序列均为 `DEVELOPMENT_SEEN`，因此 fr2 的“满足三窗口”只表示开发输入合同可构造，不是 held-out 确认。S91 仍未运行，GRC 仍未验证。
- 没有发现 snap 超过 50 ms或24帧重复导致的拒绝；窗口不足来自连续时长/GT 支持区间。这一说法与独立 `SUMMARY.json` 的 `attempt_reason_counts` 一致。

## “没有解析 GT 位姿值”和“读取文件字节”的精确边界

- 两个 S98 脚本都读取 `groundtruth.txt` 的**完整文本**：`Path.read_text()` 逐行读取，检查每行 8 列，并把第 1 列 timestamp 转成 float 来划分 GT 连续区间。
- 它们没有把后 7 列 `tx ty tz qx qy qz qw` 转成数值、没有插值/比较位姿、没有访问深度像素。因此可以说：**“未解析或使用 GT 位姿数值；只使用 GT 时间戳。”**
- 两个脚本的 `sha()` 又对 `rgb.txt`、`depth.txt`、`groundtruth.txt` 调用了 `read_bytes()` 以保存 SHA-256；所以不能说“没有读取 GT 文件字节”。
- 本轮没有打开 RGB/Depth 图像二进制，也没有解码深度像素；这是与“没有读取 GT 文本”不同的事实。S98 报告中的“没有读取深度像素”准确，但“没有读 GT 位姿值”应加上“没有解析/使用数值字段”。

## 建议给主报告的替换句

> S98（固定连续窗口开发资格审计）按项目在 S8 阶段冻结的窗口合同复核本地开发序列。8.840 秒、24 个等距目标和 50 ms 吸附门是 S8 评测协议，不是原始 proposal 的逐字规定。独立重算确认 fr2 的既有 6 窗口及 `[0,2,5]` 选择；对 fr1 新增的整序列资格审计发现仅 2 窗口。脚本读取 RGB/depth/GT 时间表并计算 SHA，未解码图像或深度像素，也未将 GT 的位姿七个数值字段解析为几何量。该结果是开发数据资格/可复现性证据，不是模型效果、未来几何真值或 GRC 方法验证。

不要使用：

- “proposal 规定 8.840 s/24 帧/50 ms”；
- “从未读取 GT 文件”或“没有读取 GT 字节”；
- “S98 完成了三窗口测试/验证了三场景”；
- “S98 产生了创新方法结果”。

## 证据路径

- 原始 proposal：`/Users/rocket/Desktop/HKUST IT/ip-/Yiyang_LIU_Proposal.pdf`
- S8 固定规则：`docs/S8_EXTERNAL_SCENE_PROTOCOL.md`、`docs/S8_EXTERNAL_SCENE_PROTOCOL_V2.md`
- S8 原始 fr2 metadata：`data/cut3r/S8_fr2desk_inputs_v2/sampling_metadata.json`
- S98 主结果：`work/S98_dev_window_feasibility/RESULTS.json`、`RESULTS.md`
- 独立重算：`work/agents/s98_window_independent_recompute/fr1_xyz.json`、`fr2_desk_timestamp_guard.json`、`SUMMARY.json`、`REPORT.md`
- 独立脚本：`work/agents/s98_window_independent_recompute/recompute.py`
