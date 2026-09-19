# C1实际测量：原定严重回访差异未出现

更新UTC：2026-09-08T15:38:42.087959+00:00（北京时间UTC+8）。**C1已真实盲评分，并用封存的另一套数学实现实际复算，全部预定数值一致。** 它是已完成模型生成数据的测量，不是又运行一遍生成模型，也不是模拟数据实验。主评分与独立复算均已得到不同作者的结果复核；最终复算结果复核于15:38:10.575668 UTC通过。

## 当前两组结果

| 预注册行 | 主MSE（未舍入） | 严格大于0.01 | 实际状态 |
|---|---:|---|---|
| B0 / changi / seed42 | 0.005278160708699555 | 否 | 已生成、盲评分、独立复算和展示 |
| C1 / jesus / seed43 | 0.00464396063251803 | 否 | 已生成、盲评分、实际独立复算一致、九帧展示 |
| C2 / living_room / seed44 | 未产生 | 未判定 | V8进入第一批23/50后收到SIGTERM，完整批次0 |

C1主比较固定为ID0（预处理真实输入）与ID8（请求回到起点后的生成图），使用原四块背景区域147456个像素、442368个RGB标量。PSNR为23.331114704908824 dB。另四块区域、全帧及三组生成—生成配对均完整保存在机器报告，不挑某个诊断值替换主结果，也不把两种场景的分数差称为方法提升。

所有完整生成均为声明的 `VMem + sd-vae-ft-mse` 组件变体、本机CPU8/FP32、两批50步，**不是原SD2.1 VAE精确复现**。输入相机参数符合预定闭环，并不证明画面真的服从相机。

## 对创新路线意味着什么

原S42要求三组全部技术有效且至少两组出现严格事件。评分前已写明：若B0与C1都为否，则C2即使为是也最多1/3，无法满足2/3。C2仍按原协议完成，当前整体状态保持`INCOMPLETE_C2_STILL_REQUIRED`，不伪造完整终态。

这说明当前**九帧、小转角、两批设置中的预设严重回访差异**没有获得前两组支持；不证明整个模型无缺陷，也不证明长时序、遮挡或动态场景已解决。我们不能降阈值、换区域或挑生成对来挽救这条窄假说，更不能据此写“记忆均值导致稳定失败”。

按Supervisor、pengsida科研方法及已核ICML文献，下一步应先完成已有基线，明确放弃不受支持的解释，再从proposal要求但尚未验证的困难条件中提出一个新的、独立的研究问题。更长轨迹、遮挡和来源冲突目前只是可能的检索/设计方向，尚未作为新实验运行或新方法验证。S53原草案不因本结果自动获准；ICML建议的同起点去噪记录也仍未实现。

## 可见图片与证据

- [全部九帧接触表](../results/S44_C1_confirmation_generation/visual_qa_all9/C1_all9_contact_sheet.png)：ID0真实输入，ID1–8模型输出；完整时间顺序，无选图或调色。
- [九帧导出说明](../results/S44_C1_confirmation_generation/visual_qa_all9/README.md)和[逐帧观察](../results/S44_C1_confirmation_generation/visual_qa_all9/VISUAL_QA_OBSERVATION.json)：PNG解码与权威RGB逐字节相同。首次查看在评分及实际复算之后，未见整体空白/崩坏；仅缩放后接触表QA，未逐帧放大或验证几何。
- [主评分](../work/S46_c1_blind_scoring_preparation/C1_score_attempt_01/report.json)及[独立结果复核](../work/S46_c1_blind_scoring_preparation/C1_score_attempt_01/independent_result_review.json)。
- [实际独立复算](../work/S46_c1_blind_scoring_preparation/C1_independent_recompute/execution_01/report.json)、[最终结果复核](../work/S46_c1_blind_scoring_preparation/C1_independent_recompute/execution_01/independent_result_review.json)及[外部退出记录](../work/resumption_20260908/S46_C1_RECOMPUTE_FORMAL_ORCHESTRATION.json)。
- [结果出现前的解释规则](../work/S46_c1_blind_scoring_preparation/C1_RESULT_INTERPRETATION_BEFORE_SCORE.md)及[原S42协议](../work/S42_baseline_failure_preregistration/PROTOCOL.md)。

## 实际时间与接手边界

| 事件 | UTC（2026-09-08） |
|---|---|
| V12保存相机数值实际执行 | 15:11:44.872589–15:11:45.355323 |
| 数值结果独立复核完成 | 15:18:57.018182 |
| 主盲评分实际执行 | 15:28:44.402084–15:28:44.528780 |
| 主结果独立文本复核 | 15:33:32.213841 |
| 不同数学实现实际复算 | 15:34:45.527104–15:34:45.645130 |
| 首次完整接触表查看时间上界 | 15:35:39（不是重构出的精确查看起点） |

C1分数和图片现在均已被root看到；原盲态证明仅描述15:28评分前状态，不得复制成新尝试的证明。原V11失败、中间passed=false记录和C2中断保留。后续恢复C2必须使用合法的新尝试，不能覆盖或重用V8。

当前`NO_METHOD_SELECTED`、`novelty_authorization=NONE`、`new_method_validated=false`。本轮新增的是可信基线测量和假说约束，没有新增经验证原创算法，也不以工具调用、源码审查次数或阅读量表示PhD/CCF A达标比例。
