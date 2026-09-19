# S30 最终不同作者源码前审

记录：2026-09-06T18:11:16.612069+00:00。**当前候选源码前审通过，无剩余阻断；可由 root 另行冻结并运行。** 这不是实验或指标已经通过。

候选 SHA `d5e7326875cffaf314fadd48e7b5f43e4fd63d7afda3f7d3a63498bd8e04c86f`。Runner `8b7d794536d62262c9c5b2c5df3c7e91841c50af13a89b7c0c4f51f998a46418`，scorer `75b92de89c66a0a7039dd105908543b82f07c4d58069601a977a383393c9410e`。全文读取 run/score/prepare/contract/notes 和三份 diff、derivation proof；没有修改作者源码、历史结果或主账。完整身份在同目录 JSON。

七项必要门均已落实：

1. `verify_s29_initial_state` 在第一个 Adam 前，将本臂完整 33 项 raw 元数据／名字／shape／dtype／flags／张量 bytes、已有 loss_before 与对应 S29 objective、alignment 输入与返回值逐位比较。C2t 只对其自己的 C2t，C2a 同理；没有要求两种尺度间初态相同，也没有 decoded 逆编码恢复。
2. S28 observer 的原分支已全部替换：两臂无条件安装同一已验证 getter，Adam 前与 trace 后两处都要求四注册 depth grad 非 None 且有限；原冻结项、参数／buffer 对象与 optimizer 成员门保留。最终报告 active=true 与实际执行一致。
3. 每臂 403 objective 的来源仍为原 400 次 forward + getter 边界 2 次 no_grad + clean 前 1 次 postfinal。新增 S29 比较直接使用已有 loss_before，没有新增 scene()；原循环每次一个 backward/Adam，仍为 400 行。S29 的零步 sentinel 没被带入新执行路径。
4. 原 GA worker AST 仅改臂名、n=4、common_old_depth_original4 路由。s/T 表达式与 S29 相同，R0 保持；原 objective、Adam、clean、独立 clean/objective/backprojection 与源身份检查未改。S30 回执另用 s30_contract_sha256，原 manifest_sha256 仍正确指 S26B。
5. S29 初态维持 PASS_INITIALIZATION_EXECUTED 与 zero counts，S29 validation 必须 hypothesis_passed=true。旧 seal_producers/decode_outputs 仅接收两 S30 真实终点；S29 初态读取其封存的 depth，验证 FP32/(4,384,512)，没有伪造 conf、clean 或 producer。终点 clean 不改几何的旧门保留。
6. 所有两臂终点文件与每臂四份 S29 参考文件先校验并写 pre_score_seal，之后才评分解码，再读同四张 GT。父评分数学原函数复用；(mode,endpoint,index) 的固定循环生成 16 行和四个完整四帧均值。final−initial 只在双方有定义时计算，null 保留，无尺度拟合、置信度筛选或最好步选择。
7. 冻结合同精确 SHA、源文件身份、S29 真实回执／引用文件 SHA、旧评分政策及四 GT 的 JSON 来源都已核对；没有打开所引用 NPZ/PNG。资源按原候选 120 秒/4 GiB 每臂、120 秒/2 GiB 评分，禁止覆盖或自动复跑。

实际轻量检查：标准库 AST/compile 三份 Python；由当前源码重新派生 worker/observer/getter，三份 diff 与作者保存版逐字相同；核原 arm 梯度分支已消除、各自 S29 比较块唯一且无额外 scene()。两个 --help 均 exit 0。AST 进程未导入 NumPy/Torch/OpenCV/SciPy，0 真实数组／GT 字节读取，0 MST／网络／GA／backward。结果见 AST_and_diff_check.json。

保留边界：这里判定代码按预定设计执行，未验证未来实际初态能通过逐位门，也未证明尺度控制会提高深度精度。完整 400 步通过与科学结果改善分开；四帧、已见 GT camera 组件对照，不能扩大成盲测、泛化、生成视频或新颖性证明。无需在本轮增加其他实验或审查层。
