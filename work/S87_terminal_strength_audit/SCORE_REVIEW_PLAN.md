# S87 不同作者统计复核计划

准备状态：仅源码/固定计划；尚未读取本轮真实预测、mask 或参考数组，也未运行评分。`check_saved_scores.py` 不导入 root 评分器/生成器、不重跑模型、几何、解码或 raw 量化；raw→uint8 已由另一个独立派生核器及评分器前置核验。root 绑定完整生成、派生复核和评分封存回执之后才允许一次新建统计复核回执。

固定24新行，顺序为三种 λ(.5,.75,1) 各 Gpaste 后 Gterminal，每组目标20–23；旧 S86 16行单列原样保留。主分母每帧995328通道、四帧3981312，除255²=65025。原 bool mask 支持/孔洞及完整分母不变。旧图已见，同场景四相关目标，不能当24/40独立场景。

独立算法：对每个 RGB 通道先形成 int16 有符号差，再数511个[-255,255]差值直方图，用 Python 任意精度整数累计 `count*diff²`。这与评分器 int64 平方数组求和的实现不同。整数 SSE/分母/空集/类型、完整24行CSV与JSON、6组全图/支持/孔洞汇总、6整体+24逐目标新减Gguide差、精确反例符号与三个有限包络（含全部整数平局）逐项核验。

评分数学值使用精确 `Fraction`，每区域空集MSE为None/CSV空字段；四帧中任一空集使等权均值为NA，pooled独立按完整总分母计算。旧Gguide比较量从已绑定旧行的SSE/通道重新组成精确Fraction，并核旧摘要的显示值；不从浮点分数倒推SSE或用四舍五入挑最优。

**提前固定容差**：全部整数/布尔/字符串/None/文件SHA严格相等。浮点展示与精确Fraction转binary64之差限于 `16*epsilon64*scale + 16*minimum_subnormal64`；普通比例/均值scale为精确结果绝对值。区域等权均值的差由两已舍入均值相减，scale用两均值绝对值之和，避免消去后用过小尺度。该界只容纳至多四项均值与一次差的binary64展示舍入；不能容纳像素、整数SSE、分母或选择范围错误。主判据始终精确比较新totalSSE与13571317266，包络按整数保留全部平局。无法由展示精度分辨的区域差记录精确有理数方向，不用浮点近零代替真值。

只使用本批六策略计算 Gpaste/Gterminal/all_six_new 三包络；旧.25不加入，G0旧完整链只保留一次。所有已完成预定结果同时核验，不逐目标选λ，不调指标、不扩强度。

未来 `SCORE_REVIEW_BINDING.json` 由 root 写，须有accepted、checker_sha256、review_plan_sha256、scorer_sha256、scoring_contract_sha256、generation_receipt_sha256、derivative_review_sha256、scoring_receipt_sha256、scoring_input_binding_sha256；核器CLI仅接该文件的精确SHA。固定未resolve的R/.venv-cut3r/bin/python、NumPy1.26.4；120秒/1GiB，输出只新建 `INDEPENDENT_SCORE_REVIEW.json`，异常保留、不重试、不临时改标准。实际结果只支持保存量描述评分一致，不支持画质/几何真值/纯时机效应或创新验收。
