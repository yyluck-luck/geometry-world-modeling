# Threshold counterexample and CRC boundedness clarification (S90)

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


## Executed check

`threshold_consumer_loss_counterexample.py` was run as a deterministic synthetic test. With `k=1`, loose threshold `0.20` admits and selects high-utility candidate A (held-out future loss `0.10`). Tight threshold `0.05` rejects A and selects lower-risk candidate B (held-out future loss `0.60`). The consumer loss increases by `0.50`. This is an artificial logic counterexample only: it uses no RGB, depth, camera, model, or GRC implementation.

The result rejects the stronger statement “tightening a geometry-risk threshold must improve the world-model consumer loss.” A threshold can be monotone in estimated risk while the downstream loss is non-monotone because utility and risk are different quantities. The GRC hypothesis therefore needs prospective held-out consumer-loss tests at pre-frozen thresholds; risk-score monotonicity alone is insufficient.

## CRC wording correction

The official *Conformal Risk Control* theorem states an **upper bound** `sup_lambda L_i(lambda) <= B < infinity` almost surely, together with non-increasing, right-continuous loss curves and `L_i(lambda_max) <= alpha`. It does not require losses to be nonnegative. The project’s `[0, B_L]` convention is a stronger and convenient engineering restriction for geometric losses, not a necessary condition of the original theorem. If losses can be negative, the theorem’s proof still uses the upper bound `B`; changing to `[0,B_L]` should be described as project-specific normalization.

The theorem also requires exchangeable loss functions. A time-drifting world-model trajectory, or a policy whose features/thresholds were fitted using the same calibration answers, does not automatically satisfy this assumption. The safe protocol is to freeze the policy family and all preprocessing before calibration, replay that complete policy per calibration query, and report only the resulting marginal expected consumer loss unless stronger assumptions are proved.

## Reproducibility receipt

See `threshold_consumer_loss_counterexample_results.json` for UTC start/completion timestamps, Python/platform, script SHA-256, and the full values. No old result or protocol was modified.
