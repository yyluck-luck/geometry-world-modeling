# S14E 完成后成稿事实审查

结论：**PASS，无未解决阻断项。** 审查记录时间为 2026-09-06T17:37:06.911713+08:00（UTC 2026-09-06T09:37:06.911713+00:00）。本审查实际读取四阶段运行回执、全部12行JSON/CSV、对齐记录、图表回执与最终中文报告，并实际查看4×5对照PNG。

最终受审文件：`docs/S14E_RESULTS.md`，SHA256 `eed5fb1cb21264a5bf92d303be1c8762f40116d3e929ae2a5708fa80dfe5396d`。如其后修改该报告，应按新版本重新检查受影响内容，不沿用本回执覆盖未审文字。

## 审查角色与边界

审查者为 `s14e_camera_calibration_audit`，不同于prepare/predictor作者、score/figure作者及根数值核验作者，但曾参与本轮标定审计与运行前审查。因此这是**团队内不同作者的成稿事实审查**，不是外部第三方复现。

本次没有重跑CUT3R、prepare、score或独立数值程序，没有解码真实NPZ、原始RGB/深度PNG或轨迹。对照图PNG属于已生成的报告产物，已进行视觉检查；读取其内容不计新实验。380项自动检查只验证保存文本的转写、身份、时间和链接，不增加科学样本或新的实验结论。独立数值程序先前实际完成的868项检查由其自身回执提供证据，本审查核其868条均为passed，不冒称本审查重新完成了数值复算。

## 核对结果

| 项目 | 事实与审查结论 |
|---|---|
| 真实执行 | prepare、模型、传感器评分、独立核验均有实际SUCCESS/PASS回执。prepare与模型caller返回0且无超时/RSS越界。报告所列阶段北京时间、2.095439秒/12.996054秒外部耗时、145276928/5935628288字节RSS均与记录一致；没有作算法加速比较。 |
| 输入与来源 | prepare仅解码41个历史白名单数组，读取20926行共同允许的相机轨迹。模型阶段17个数组、5次ray query、图像encoder 0、history forward 0、原始图像打开0。相机GT是共享输入，不能描述为没有任何GT。 |
| 状态与控制 | 五字段状态在5次查询后均与恢复前身份相同。call0使用zero占位，六输出与旧Q0控制逐字节一致；call1..4为四个目标条件。报告没有混淆旧call1和新call0，也没有把未保存的三个旧S8状态声称已逐字节核过。 |
| 封存顺序 | 准备完成≤condition封存<模型开始；模型完成<组合预测封存<首次目标深度hash≤首次打开。4张目标RGB在评分成功之后才为报告读取。这个顺序由保存回执与时间核查支持，不是操作系统级任意文件隔离证明。 |
| 尺度与单位 | 最终采用正向OLS的s=1.1146619883400035模型单位/米，固定self-z/s。history RMS=0.04417737652322564模型单位，报告明确单位；目标深度未参与拟合。遵循尺度勘误与最终协议，不使用旧审计反向OLS。 |
| 三方法均值 | 四query等权δ1为93.0974%/85.8008%/69.8127%；模型比重投影高7.2966个百分点。共同域MAE为20.2195/24.3221/42.9607厘米，AbsRel为0.091057/0.105155/0.190290。米到厘米转换与全部报告表格一致。 |
| 分母与完整性 | 保留全部12行及20–23四个相关目标。全GT域δ1缺预测算失败，覆盖率与正确率分开；共同有效域比较误差，own域也在CSV保留。167400是相关像素访问次数，不是独立样本数。 |
| 图表 | 4行×5列完整，4真实RGB、4传感器GT与12方法预测均清楚区分。全部16张深度图共享0.947522688243398–10.068619415887262米完整色域，灰色为无效值；未见裁字/缺行/缺色条。图回执声明无深度截断、平滑和逐面板调色，6个图表产物身份匹配。SVG含矢量文字和栅格数据，未宣称照片为矢量。未进行论文缩版字号验收。 |
| 创新与一般性 | 报告将本轮定位为现有CUT3R组件在已见TUM单段的质量诊断，未声称新算法、未见场景、SOTA、独立场景显著性或完整VMem视频效果；新方法、Bonn实测及视频仍未完成。 |
| 固定协议与原则 | 前审绑定的15份源码/接口/协议/原则文件仍与原SHA一致；此前218项人工检查与真实质量样本分开。没有按此次评分改尺度、head、掩码或主指标。长期原则要求的证据分层、技能实际应用范围、记录与作者角色区分在报告中得到保持。 |

## 文字修正与保留事项

审查中提出一项非数值措辞修正：新手段原“物体离相机有多远”可能被理解为射线欧氏距离，根作者已改为“物体在相机前方的深度，也就是沿相机光轴的距离”。本回执绑定修正后的最终SHA。没有改动模型、指标或冻结文件。

审查读取时曾误用 `results/S14E_known_camera_queries/metadata.json`，文件不存在；随即使用实际 `run_metadata.json`。该次只读路径错误未启动实验、未改结果文件，不计作科学失败或一次模型运行。人工准备阶段既有失败、勘误与反例保持原样。

科学判断使用已读本地Claude `sci-scientific-critical-thinking` 的测量效度、输入混杂和结论强度要求；Supervisor `idea-evaluator` 的最近工作/可验证性限定延续前审，未重新虚构完整创新评分。此阶段没有调用Claude模型/CLI，没有为数量新增无关工具或重复检索。官方标定及CUT3R语义沿用已完成的原文/源码审计，最终协议与尺度勘误为直接依据。

## 可追溯证据

- `work/S14E_completion_review/factcheck_receipt.json`：380项逐条检查及所读文本/图表身份。
- `work/S14E_completion_review/check_report_facts.py`：仅文本与产物核对的脚本，不导入生产评分函数、不读原始数组。
- `results/S14E_known_camera_prepare/run_metadata.json`、`alignment.json`、`condition_seal.json`。
- `results/S14E_known_camera_queries/run_metadata.json`；`work/S14E_execution/prepare/`与`model/caller_receipt.json`。
- `results/S14E_known_camera_score/run_metadata.json`、`metrics.json`、`metrics.csv`。
- `results/S14E_known_camera_independent/verification.json`：原868项数值/身份检查PASS，166身份、106数组、4深度，模型调用0。
- `work/S14E_reporting/figure_receipt.json`、`s14e_all_four_targets.png`与全部12行CSV。
- `docs/S14E_FINAL_PROTOCOL.md`、`work/S14E_calibration_audit/scale_definition_clarification.md`、`work/S14E_pre_run_review/final_review_receipt.json`。

根可将本完成审查加入交付与主账；本审查者未修改研究主记忆、主账、生产程序或冻结文件。
