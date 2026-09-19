# S32 元数据选窗规则（先固定，再执行选择）

固定时刻 UTC：2026-09-06T19:13:16.817126+00:00

本文件写入时，本轮尚未读取两个场景的 rgb.txt、depth.txt、groundtruth.txt 数据内容，也未计算 N 或选择实际起点。已读项目原则/最新记忆、S31_next_decision 及既有时间关联/光学相机源代码。S31 已知结果用于决定三种普通对照，不用于给这里的候选窗口打分。

1. 场景固定为本机原始 TUM freiburg2_desk 和 freiburg1_xyz，使用既有 S21/S24 的原始目录。fr2 不切换到 timestamp_guard 派生目录。两场景各取原 rgb.txt 全部有效 RGB 记录按时间升序的总数 N；零基索引。对 j=1,2 固定起点 i=floor(j*(N-4)/3)，各取 i,i+1,i+2,i+3 连续四条原 RGB，共四窗口十六帧。不能先过滤 pose/depth 后再计算 N。
2. 不使用 RGB 画面、GT 深度覆盖或像素、已有或未来的深度误差/loss/k/改善来选窗。只核文件索引、时间戳、允许相机元数据与预算。若 N<4、规则窗口重叠、必需 RGB/pose 缺失或元数据歧义，保存原选择与失败原因；不移动、补帧、换窗、换场景。sensor 配对缺失保留 NA，不能因缺深度而替换输入。
3. pose 和 depth 分别在各自**全序列**时间表与全 RGB 表上做原一对一匹配，再查选定的原 RGB。沿 S21 原 associate/S23 等价实现：offset=0，候选 abs(rgb_time-other_time)<0.02 秒（严格小于），按 (绝对时间差, RGB时间, other时间) 排序，贪心使用未被占用的时间键；不是逐窗最近邻，也没有插值。沿既有 float 时间语义，同时保存原时间字符串和十进制差供查阅。若选中 pose 时间有重复来源行，则标为歧义、不自行选末行。深度记录重复/路径歧义同样保留并报错。
4. 允许的相机为 TUM optical c2w，世界米制；匹配姿态的 tx,ty,tz,qx,qy,qz,qw 可作为共同 oracle 控制元数据，不能称纯 RGB 或盲测。选中姿态核七个值有限、四元数范数与 1 差<1e-3（沿 S26B）；不额外翻转 Y/Z，不拟合轨迹。当前不生成/冻结 FP32 c2w tensor，后续由原控制准备代码转换。
5. 当前只读 txt/已有 JSON/源码/文档；不打开、解码或 hash RGB/深度图片和预测 NPZ，不读取窗口分数。图像/深度内容 SHA 留空，后续实际字节封存时记录。不能把本轮未读字节写成历史未见。允许的 GT pose 文本字节读取、选中坐标解析须据实记入本轮暴露记录。
6. 暴露清单分开核 fr2 的 S21/S22 前300个配对 RGB、S23 sensor 配对读取记录，以及 fr1 的 S24 全796配对 RGB/轨迹评分。fr1 共798原 RGB，其中未配对两条不代表都输入过模型。具体画面被人打开、其他早期阶段的RGB/深度曝光、窗口分数查看史无法确认则写未知；不据“已见场景”推出每张深度已读，也不据“本次新选”推出未见。
7. 四窗口各自独立 reset/fresh CUT3R 512DPT 推理；禁止复用原全序列带历史 anchor 的 other 头。固定为首次四帧消费者初始化阶段，非 old4→new4 完整链。后续共享 C2a 既定单位初始化规则的零步/400步/S31全窗口单标量三普通对照；本次没有生成模型预测、初态或评分。
8. 建议预算每窗 fresh CUT3R CPU8、外层 FP32、原已核 RoPE 精度路径，最长180秒、RSS≤16GiB；每窗 GA 最长120秒、RSS≤4GiB，四窗。模型/GA不并发累加RSS，实际权重/source/reset/代码/总预算须后续独立协议冻结，本文件只固定选择与建议上限。失败保留、不自动重跑或换窗。

直接协议/源码依据：docs/S23_GEOMETRY_DIAGNOSTIC_PROTOCOL.md；scripts/s23_geometry_diagnostic.py::associate；scripts/s21_baseline.py::prepare 与 work/S21_baseline_preparation/ttt3r_original/datasets_preprocess/long_prepare_tum.py::associate；docs/S24_BASELINE_EXPANSION_PROTOCOL.md；scripts/s26b_consumer_baseline.py::control_input。这里只读相关源段，不执行其模型/图片函数。
