# S67：固定平移查询下的相对深度→选图诊断

这是人工干预的已保存数值诊断，**两臂同 query、不同相对深度**；不是查询变动扫描、真实平移观测、自然失败、视频收益或新方法。问题来自 S66 `NEXT_SCIENTIFIC_DECISION_REVIEW.md`（SHA `62f3ee5fad654b3a2438585e42af2594cefb7021857b8f38635cf96e89ef02ae`）和 S65 中文说明。只用旧 C2 V9 同一份五来源、515 surfel、真实四类 cache；原 S63/S64/S66、失败和 cohort 不变。

## 原路径复用与读取

从冻结 S63 `replay_context.py`（SHA `b36e788d486bd3d15126f8c2d40fffef9f9e5dee4dcb91cbc31fd2553104e1a5`）核同一字节后，仅 AST 抽取 Decoder、load_inputs、fingerprint、exact、check_maps、原六方法提取器等九项 helper。**不抽取/调用旧 main 或 run_arm**，不重跑原失败 renderer，不读 S61 golden NPZ。原 pipeline/util 和单位 adapter 身份仍由 S63 原 PINS 固定；额外只核前述决策、S65说明、S63协议和实际成功终态的 SHA。

为避免重写已核读取，load_inputs 原样读取 seq50真实 cache、56目标、58几何/query、60已见空图、62空检索及64阈值：1496 唯一原 blob、1,631,256 B，每份即时落 readlist 并核 SHA/shape/dtype/finite。旧空图仅随原 helper 解码，不作为本次新臂 oracle。禁止 pil/RGB/color/surfel_depths 分支、模型、完整 pipeline 导入、get_cond、编码/去噪/生成。作者阶段只源码/已见 JSON，科学正文和 renderer 均为0。

## 结果前固定的两臂与查询

1. 原 saved raw renderer pose 记为 `Q0`。用原 `average_camera_pose`（SciPy rotation→quaternion→mean）及原 y/z 列翻转，从保存的 target 末一帧重建 Q0，要求与归档 pose 精确相同。
2. 五个历史 c2w 的中心与 Q0 中心 C 必须在转换到 float64 后**逐项精确相等**。不能用相对微小场景过宽的绝对长度容差。所有515点在 Q0、五个历史实际 CV camera、最终 query 的所需投影深度均须正且有限；不删除零/负点挑有效子集。失败记录实际中心或非正索引/计数，停止兼容性声明。
3. 扰动前参考深度 `z_i=solve(Q0.R, X_i−C)_z`，`m0=median(z_i)>0`。A geometry 原样。B 固定 `λ_i=m0/z_i`、`X'_i=C+λ_i(X_i−C)`、`r'_i=λ_i r_i`；normal、source_ids、surfel_to_timestep、cache和K不变。B位置以float64表示，半径float；验实际B参考深度相对m0误差≤1e−10。不是换统一尺度，半径/法线安排不证明完整图像等价。
4. **只定义一个实际平移** `δ=0.1*m0*Q0.R[:,0]`，不使用A/B各自适配后的单位计算δ。两臂 target均升float64（原R元素值精确保留）再同加δ；原函数仍只用末目标构造查询。共同query定义为这份 promoted target 经原构造所得 rawpose。平移须精确为 C+δ，旋转须等于同dtype未平移构造值；相对旧Q0的共同dtype旋转差实际报告，不先假定逐字节不变。每臂真实 renderer hook 必须收到同一个已固定rawpose，focal和kwargs与原保存值精确一致；两臂最终rawquery指纹也须相同。
5. 用原 y/z 翻转后的五个历史 camera 和各自实际保存K，核 A/B 全515点投影最大绝对差≤1e−10，单位为**保存K的原生图像坐标**，不猜标定或把它冒充像素。辅助新query投影使用真实 renderer focal/principal points，因此以像素报告最大/中位位移及超过1e−6 px的点数。没有真实目标像素、深度答案或法线/遮挡/全图等价验证。

## 原选帧与输出

两臂独立深拷贝，按 A→B 各调用现有 S61 `render_in_canonical_units` 一次；其内部原 renderer 恰一次，原 retrieval 恰一次，原 get_context_info/NMS/真实缓存 gather 不改。每臂保留实际单位票，单位可因几何/query变化而不同；不能把各自表示单位变化改成各自移动查询。CPU8/FP32 NMS、context4、translation weight0.1、512×288、visualize=False、原focal×0.65保持。允许原函数按历史重算 initial_threshold；两臂该历史状态须相同。

每臂报告：有效索引支持、cos≥0支持（cos=0也计来源）、实际来源成员集合、原权重和每来源配额、最终有序 IDs、真实四类 context 每slot的实际/期望FP32 bytes SHA。五来源非空池配额应各1；不只报k，不预定ID列表，也不强制成员不足4时仍返回4项。ID必须唯一、合法且数量匹配原候选池。输入、分支副本及实际挂接cache/geometry前后指纹均一致；B的声明干预已在分支前完成。maps/context NPZ、固定geometry/projection NPZ、每臂JSON、完整读入/最终receipt均保留。

原空集合、非有限权重或其他异常记该臂无效/失败，仍尝试另一个独立分支；兼容性前提失败则不运行任何臂。任何输入突变立即停止。没有 fallback、参数重试、旧失败重现或 golden 比较。外部终止可能只留下部分文件，以root真实退出记录为准。

若两臂有效且ID不同，只记选图敏感性，不判断对错/收益。若投影已分歧但ID相同，否决**这个固定案例**的所选来源ID中介解释，停止为它追加生成；不推广为几何无用。若投影无有效变化，记无信息，不能写同样的否决。成员/配额/ID全项均报告，原单位变化也单列。独立新机制和正确性答案仍未建立。

## 唯一执行

源码冻结、root及非作者核验后，由root一次执行 `.venv-cut3r/bin/python -B work/S67_translated_query_diagnostic/diagnose.py`，外控≤120秒；内部阶段与收尾检查110秒，禁止自动延长。`execution_01` create-only，已有目录不重跑，全部产物0444。return0只表示固定配对诊断完成（可能无效应/无信息），不是方法通过；无效输入/分支或失败return2。`--compile-only`仅核 S63源与编译，不导入科学库、不读科学正文、不执行 renderer。作者检查及最终SHA见交付票；纠正须另建文件。
