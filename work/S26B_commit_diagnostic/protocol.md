# S26B：旧几何与 focal 一致性的描述诊断协议（仅准备）

本协议检查同一旧帧的深度和相机固定时，优化后的 focal（以像素计的焦距）是否伴随旧点图变化，并计算全部变化量。它不评分真实几何，不判定有害，不实际构造 Surfel、地图提交或查询缓存。当前作者只读源码和记录并写准备文件，**没有执行本诊断、读取 S26B 输出 NPZ 字节或数组、读取传感器 GT、运行模型或 GA**。作者与 S26B runner 作者不同，但此稿尚未通过另一个人的执行前审查。

依据 `work/S26_commit_consistency_source/audit.md` 与其固定 VMem commit `39291e4f272f6b4f270691d930926ab5930f942e` 的源码结论。使用 Supervisor handbook 2.2 的“先验证 baseline 的具体问题”路径，以及已实际读取的本地 Claude `sci-scientific-critical-thinking/SKILL.md` 中测量有效性、混杂、选择偏差和因果边界要求。本轮是局部设计与工程准备，不声称完成新的文献综述、技能全部流程或独立实验复现；不调用 Claude 模型。这里保留公式和输入检查表，不额外生成与这个简短数值协议无关的图片。

## 1. 冻结、执行入口与输入门

脚本为本目录 `diagnose.py`。另一作者静态审查完成后，由 root 在调用记录中冻结三个实际 SHA：脚本、本协议、`work/S26B_preparation/run_manifest.json`。不得用运行时自算 SHA 代替已经记录的冻结。父 S26B manifest、旧脚本及结果均不修改。

未来命令模板（本轮没有执行；尖括号须替换为审后记录的实际值）：

```text
.venv-cut3r/bin/python work/S26B_commit_diagnostic/diagnose.py \
  --parent-manifest-sha256 <frozen-parent-sha> \
  --script-sha256 <reviewed-script-sha> \
  --protocol-sha256 <reviewed-protocol-sha>
```

NumPy 使用项目现有环境；脚本把四个常见 BLAS 线程变量设为 1。没有模型、Torch、GA、RGB 或 GT 加载器；本脚本不提供自动重跑或自动修改冻结的选项。结果目录固定为 `work/S26B_commit_diagnostic/results`，现存即拒绝，失败产物保留；未来有改动另立版本。完成数据运行后才可谈运行检查是否通过，本准备不把手工阅读写成测试 PASS。

顺序不可交换：

1. 校验调用者三 SHA、父合同的旧 4 / 新 `[4,5,6,7]` / 完整有序 8 帧；只读取父绑定的 runner 与 importer 源码验证其 SHA。
2. 四目录 `results/S26B_consumer_baseline/{common_old,cut3r,ttt3r,filt3r}` 的 receipt 全部为相同父 SHA 下的 `PASS`，mode、frame_count 为 4/8/8/8；各 `inputs_seal.json` 的 SHA、相机身份、按序 head 记录、共同旧输入 receipt 与相容性 receipt 互相匹配。
3. common-old 必须明确 `IMPORT_VALIDATED_SAVED_ORIGINAL_GA` / `IMPORT_VALIDATED`，新 GA/step 为 0，历史 step 为 400；恢复回执的状态与 SHA、原 output SHA、父 continuation 冻结的 output SHA 全部一致。原 S26 的 `FAILED` 不改变，历史未录信息原样进入本次 input seal。
4. 三个 8 图 GA 必须完整 400 次迭代和 Adam step、一次 clean；保存的参数 flags 为全 pose 固定、全 focal 可训练、pp 固定、旧 4 depth 固定、新 4 depth 可训练。核 hash 绑定的 observer 日志含 `post_MST_constraints/post_GA_constraints/post_clean_constraints/GA_call_exit` 和一致 flags。日志的意义来自被绑定源码中每次 checkpoint 前的冻结参数逐值检查。本诊断**不重新读取内部参数快照，也不把继承检查说成新的参数级独立复算**。
5. 全四个 output NPZ 字节 SHA 与各完成 receipt 匹配后才解码任何一个 NPZ。相机和 compatibility 采用共同源 SHA 与生产者验证继承，本诊断不重新解码控制相机或已存 head。
6. 六个键必须恰为 FP32 有限数组：depth `(N,384,512)`、point_cloud `(N,384,512,3)`、conf `(N,384,512)`、focal `(N,1)`、pp `(N,2)`、c2w `(N,4,4)`；depth/focal 正，conf 非负。异常即失败，不删异常像素补算。

`sensor_gt_read=false` 仅表明本次工具流程的读取边界，不恢复研究者未知结果状态；本片段早先已见，其给定相机也是 S26 的显式 oracle 控制输入。后续 root 是否已读深度分数须按其真实状态报告，不把本协议写成盲测。

## 2. 先验证固定条件与反投影

每种 8 帧方法 B 的旧索引 0–3 均与 common-old A 比较，相同网格不裁切、不对齐、不按 conf 过滤。旧深度使用原 log/exp 往返容差 `atol=1e-6, rtol=1e-6`；旧 c2w 使用既有给定相机容差 `atol=1e-5, rtol=1e-6`；pp 要数值完全相等。保存 depth/pose 的字节相等、数值相等、全组件绝对差统计和超容差组件数。固定条件任一失败，保存原因并停止解释 focal/world；不继续选择另外的方法讲故事。

反投影统一在 Float64 用分量表达式独立实现，不调用原优化器：

`X(d,P,pp,f;u,v) = R [d(u-cx)/f, d(v-cy)/f, d]^T + t`。

全部 4+8+8+8 帧、每个像素、三个 world 分量都核保存 X 与自身 d/P/pp/f 重建 X 相符。继承已定 `atol=1e-5, rtol=1e-5`；参考量是保存 X，即判断 `abs(rebuilt-saved) <= atol + rtol*abs(saved)`。不重新拟合 SE3/Sim3，不把坐标变换后的减小当一致性提高。

这些是执行与数值一致性容差，**不是可感知错误、几何伤害或科研效果的阈值**。不同方法实际焦距可能不同；focal 不受人为异常阈值筛选。不能从“超过数值容差”推导 GT 更差。

## 3. 全旧 4 帧、全像素记录

每方法固定 4 帧，每帧 `384*512=196608` 个像素，合计 `786432` 个像素，全部保留；三方法并列。逐帧记录共同和当前 focal、signed delta、abs(delta)/共同 focal，pp 与 c2w 完整矩阵及 delta、pose 平移差范数；depth 的逐像素 signed delta 和绝对差统计。

对每个旧像素定义：

- `actual = saved_X_B - saved_X_A`。
- `focal_only = X(d_A,P_A,pp_A,f_B) - X(d_A,P_A,pp_A,f_A)`。
- `nonfocal = X(d_B,P_B,pp_B,f_B) - X(d_A,P_A,pp_A,f_B)`。
- `stored_residual_delta = (saved_X_B-rebuilt_X_B) - (saved_X_A-rebuilt_X_A)`。
- `remaining = actual - focal_only`；保存 `actual-focal_only-nonfocal-stored_residual_delta` 的逐帧最大绝对闭合残差。

保存每像素全部向量、norm、depth delta、两份重建残差、component-level 容差布尔量和 any-component 超容差像素量；没有 mask。重建残差只是数值残差，不能在未证明时全部命名为浮点舍入原因。每帧的 actual / focal-only / remaining 欧氏范数给全量 count、mean、median、P95（NumPy linear）、min/max、RMSE；全旧 4 帧合并给同样统计。超 world 容差像素比例以全部 196608 为分母，A 的各 world 分量为相对容差参考。这里没有推断统计；像素不是独立实验样本。

`focal_only` 是把已存字段代入同一几何公式的算术分解，**不是把 focal 冻结后重新运行 GA 的反事实结果**。其解释范围是哪些保存字段足以解释点位差；无论分解是否闭合，都不能消除不同输入上下文、图边数或优化目标的混杂。

## 4. 新 4 摘要与可选缓存算术回放

三个方法的新索引 4–7 全部给 depth 完整网格统计、world x/y/z 各分量统计、focal、pp、c2w。common-old 无新帧 counterpart，因此此处只有数值水平，不能作新帧改善结论。实际深度 GT 主评分由另一个已冻结评分器完成，诊断不读取或复制其分数。

统一为三方法计算明确标记的假设两轮 4→8 算术回放：

`f_pool12 = 0.65 * mean(concat(f_A[0:4], f_B[0:8]))`

`f_current8 = 0.65 * mean(f_B[0:8])`。

保存全部 4/8 focal、按 frame 的快照计数 `[2,2,2,2,1,1,1,1]`、两数和差值、相对差，以及代数核对项 `0.65*(mean(f_A)-mean(f_B))/3`。没有按差值选择方法，也没有把 current8 当作已证明正确的政策。

**S26B 没有实例化 Surfel、construct、query 或 cache。** 这里只重放已读源代码中列表追加/均值的算术，不是实测缓存事件、不产生渲染或 context ID、不证明生成结果改变。也不研究 undo 或未满 4 新帧路径。

## 5. 产物、解释与停止边界

未来实际运行将保存 `receipt.json`、`input_seal.json`、`fixed_conditions.json`、`world_reconstruction_checks.json`、三份 `*_old_pixel_diagnostics.npz` 和 `summary.json`。receipt 在解码前记录 attempt 标记，每个完整解码 mode 后更新，避免中途失败仍声称未接触数组。成功前重哈希所有实际读取输入及源码/协议；输出 SHA 写 receipt。外部 caller 应记录命令、实际起止、进程退出码、冻结三 SHA 和资源用量。脚本自身 `PASS` 只表示描述计算与规定门完成，不表示方法成功。

必须随结果保留的混杂与否决：

- 原 CUT 的 common4→TTT 仓库兼容 CUT8 同时有源实现边界、4/8 帧头上下文、3/7 条 star 边、MST 初始化与联合目标变化；不是只改变历史长度。TTT/FILT 使用 CUT 共同旧深度，更大偏移也不自动更差。
- 如果 focal/world 没有超数值容差变化，这个 pilot 不支持相应局部不一致；不得人为加噪声、挑主点外最坏像素或改阈值使其出现。pool/current 相同同样保留。若有变化，仍只到“保存量发生变化”这一层。
- 短至约 0.236 秒的已见 8 帧组件不能说明自然长程遗忘、因果伤害、生成提升或可发表创新。后续是否值得测真实地图/query，必须另行设计并遵循公平控制。
- 冻结旧 focal、重积分旧图、同步缓存是应先比较的普通工程控制；任何一个差值不使这些操作自动成为新方法。原先“后代覆写旧 Surfel 坐标”的反证继续有效。

本轮交付仅供 root 静态审查、冻结、随后在全部真实生产者门通过后决定执行。本作者本轮不自行执行，没有新数值结论。
