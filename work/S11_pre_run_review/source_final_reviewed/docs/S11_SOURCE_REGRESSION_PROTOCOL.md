# S11来源变化控制：执行协议

本协议在新来源条件执行前制定，落实另存的S11_SOURCE_EDIT_DESIGN。与192既有地图条件的回归独立冻结，不能混合样本或沿用其PASS。普通S10候选不改，本轮不计时、不读新图像/GT、不运行模型或原renderer。

## 固定域与两臂

只使用S10相同52封存文件，仍以S7/S8三块A0P0/stride8/width160，query20为六个基础地图查询。先加载原24查询只是复用既有loader的验证，过滤只保留六个q20，不运行其他query。每块首先核原buffer有正的有效投票像素；不合格就停止，不挑替代query。

五规则固定按append_min_missing、drop_last、reverse、only_0、only_0_1_2执行。每个条件从原mapping副本起；全部来源行按设计统一改动，不以可见性或结果选行。每个列表非空、唯一历史整数ID0–19；几何/顺序/法向/半径/颜色/counts、相机、20个历史上下文、K、阈值均保持。这里不是实际merge或新照片输入，原counts不重建。

每块先6个总计的原mapping baseline replay，完整结果核旧封存trace。随后30个编辑条件各执行reference_replay与candidate，两臂独立相同输入副本。总计66次完整get_context：36次参考缓冲回放、30次候选真实渲染，原renderer0次。旧24候选S10条件不重复执行，无预热或单次性能计时。

参考原get_context内部仍真实重算投票、配额、距离与排序/NMS；仅renderer改为有守卫的旧buffer回放。候选运行固定S10真实renderer加未改原get_context。两臂同样按其新mapping计算，不能拿旧mapping的结果要求新版不变。

## 回放许可与负对照

静态独立AST确认原renderer不读self/mapping，只读surfels的position/normal/radius及显式相机、焦距、主点、尺寸和disk_resolution。每块从冻结输入按原平均姿态、翻轴、surfel_Ks均值×0.65构造预期渲染实参；真实get_context传入回放器时严格核形状、类型、C原字节身份。geometry指纹不包含mapping，完整state_identity包含mapping；二者用途分开。

每块在候选前做三次纯守卫负对照：独立副本的相机[0,3]、第一surfel位置[0]、第一焦距分别加0.001。总18次都须在回放返回数组前被拒绝；它们不调用选择器/原renderer。比独立设计的两个建议项增加一个焦距项，在此事前固定。

另把每块原mapping baseline实际trace故意当作新mapping计算结果，逐值比较official_trace与official_decision（仅实际计算字段，不比较variant名、mapping摘要或输入哈希）。18个append/drop/reverse条件中至少一个须拒绝陈旧trace；12个欠源边界不能代替此门。每个条件均保存是否检测到、相对旧结果有序ID是否改变；不因结果大小更换测试。逆序不假定与旧mapping同trace或同ID。

## 记录器适配与精确门

原S7 decision_trace的计算已使用maximum=min(4,k,history)，仅末尾两个长度检查硬写4。新脚本在内存中通过AST精确把这两个验证常数换成maximum；原源码、全部排序/NMS计算和合法ID范围保持。反向恢复该条件后整个函数AST必须相同，保存原/适配全文与回执。原错误字符串保留；实际get_context没有改动。适配仅扩大记录器适用域，不能改变真实选择器。

每次记录selected必须逐值等于当前真实get_context返回ID。baseline适配记录必须复现旧四图记录；only_0必须返回[0]，only_0_1_2必须返回恰好{0,1,2}且两臂顺序完全相同，不强补4。20个历史帧始终不变；这不是历史帧数1/3的特殊分支，也不覆盖空来源、空检索、五历史帧初始化或NMS=False。

每次实际候选三数组对原封存shape/dtype/C bytes零容差一致，含±0。同条件两臂完整official_trace/decision、原返回ID、所有上下文tensor身份与实际值相同；保存每臂render.npz、context.npz、trace.json、调用前/后state_identity.json。调用后完整输入状态须与调用前相同，不要求编辑后的mapping等于旧mapping。baseline来源原trace、每条件mapping、渲染实参身份和每个负对照均保存。

## 冻结、环境、资源与失败

入口scripts/run_s11_source_regression.py；CLI --freeze --protocol --output。新执行冻结schema=s11-source-only-execution-freeze-v1、status=approved_for_execution，含实际frozen_utc、protocol_sha256、固定S10 freeze SHA db22d71b37c9a44ece98008f8ff422886a7bdc604efd79d6f0000b55f1532204、精确CONTRACT、13个execution_source_sha256、同S10的52个input_sha256、设计/独立预审的review_evidence_sha256。

所有源、输入、协议/冻结与review前后核SHA；三ZIP封存源/52输入/审查，源包另含两冻结与协议。冻结先于运行，数值模块导入前线程环境8；Python3.12.14/NumPy2.3.5/Torch2.7.0/SciPy1.16.2，Torch intra/inter8、默认FP32排序，原FP64几何。复用S9 Python读写守卫，拒原PNG/权重/未列结果/网络/子进程，新写入仅全新结果目录；不是OS沙箱。

600秒总墙钟和16GiB峰值RSS软守卫，原生代码可能推迟信号。只存总资源预算时间，不从参考回放和候选时间推算速度。任一门失败就保留当时目录和异常，已返回的真实renderer缓冲尽量保存，即使选择器后续失败；不覆盖失败、改旧源或调整判据以求通过。状态completed要求30条件、6baseline、18实参拒绝、18编辑内至少1陈旧trace拒绝，以及所有原文件不变。

最终结论仅为人工来源编辑与低来源数的组件一致性；不证明真实地图更新轨迹、缓存命中率、跨NumPy版本、未见泛化、视频质量或论文创新。独立复核应重开每次实际数组/上下文/trace、重建确定mapping与对应票权，不能只读PASS标志。
