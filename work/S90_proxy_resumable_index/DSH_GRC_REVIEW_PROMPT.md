# Independent red-team request: GRC-Memory and S90 evidence plan

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


The user is an MSc beginner targeting a PhD-depth, top-conference-quality Geometry-aware World Modeling project. Treat all novelty as unvalidated.

## Verified local evidence

- In the existing S87 single seen static scene, a simple terminal blend at strength 0.75 achieved lower four-target mean RGB MSE (0.0511675816620) than the older 50-step geometry-guided arm (0.0524222225291), while target 22 became worse (0.07483243 versus 0.06826439) and visible ghosting remained. This refutes only the claim that multi-step guidance is necessary for that mean MSE; it does not validate geometry or a new method.
- S90 restored a fixed RTMV archive route through the current local proxy. One frozen 512-byte Range at offset 11460608 returned exact HTTP 206, TLS verification result 0, exact archive size 12064450560, and a valid tar header `00000/00134.depth.exr`. No RGB/depth body or model was run.
- Real matched RGB/depth/camera views are not yet available. Data risk remains high.

## Candidate being challenged

GRC-Memory (Geometry-Risk-Calibrated Memory Selection) asks a New Problem + Method question: under fixed memory and compute budgets, select history that safely helps predict future geometric state.

Each history-query pair has observable pre-selection features derived only from past observations and the requested target camera. A scalar predicted geometry loss should summarize reprojection, depth-consistency, and visibility evidence. A held-out calibration split would produce a risk upper bound. A learned or geometric utility surrogate predicts future-state value without reading held-out future ground truth at selection time. The selector then maximizes utility subject to cardinality/cost and calibrated-risk constraints, and updates when observations arrive.

The decisive hypothesis is: lower pre-selection geometry risk is associated with lower held-out future position error, and risk-aware selection beats recent-frame, camera-distance, random, coverage, Fisher/EIG, confidence-only, and utility-only selectors under identical eligible history, features, k, and compute.

## Primary-code observations already made

- Official Conformal Risk Control commit `3eff946390a8f188b1e5ab700fce21a66a215e7c`, `core/get_lhat.py`, selects a global lambda from an n-by-lambda monotone bounded loss table using an empirical-risk correction. It does not justify taking `Q_(1-alpha)` directly on a three-component residual vector or assigning an independent quantile to every candidate.
- Official FisherRF active-mapping commit `8b196cd22b1f4030f205778ad14b23fbd796c3b7` ranks candidate poses and paths by Fisher/Hessian-derived EIG. It chooses informative future views, whereas GRC-Memory chooses safe/useful past memories; the objectives differ, but EIG is a required strong baseline.
- Official NVF commit is locally cloned. Its active mapper averages ray entropy to score candidate cameras, and its visibility code projects points into camera FOV and composes opacity-derived visibility. Visibility and uncertainty are therefore prior components, not standalone novelty.

## Review tasks

1. Identify the two strongest fatal flaws in the candidate as currently stated.
2. Correct the mathematical formulation so it is computable at inference and does not leak future targets.
3. State exactly which conformal guarantee is defensible, including exchangeability/shift assumptions and whether it is marginal, conditional, per-candidate, or set-level.
4. Explain why simple sums of per-item risk and a casual `(1-1/e)` claim may fail under interactions, constraints, and non-submodular learned utility.
5. Give the cheapest runnable unit/counterexample tests that can be done now without claiming scientific validation.
6. Give the minimum real-data experiment that could reject the core hypothesis, including splits, baselines, metrics, and stop rule.
7. Decide separately: adopt, revise, or reject (a) conformal calibration, (b) Fisher/EIG, (c) NVF-style visibility, and (d) the full GRC-Memory story.

Use only this material. Do not invent citations, results, or novelty. Keep supported facts, assumptions, counterexamples, and next tests separate.
