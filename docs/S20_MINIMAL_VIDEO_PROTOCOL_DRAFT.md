# S20 最小真实视频闭环协议草案

**状态：源码审查及协议草案，未执行生成、未加载模型、未读取新图片或权重。** 本轮 root 仅推进隔离依赖和完整 Pipeline/Navigator 的禁止联网、禁止模型实例化导入检查。下述是权重、环境和观察器就绪后，另行冻结的真实运行合同；不是当前已经具备运行条件或已经生成九帧的声明。

目标是完成原作者单图导航的最小两批闭环：**1 张初始实拍＋4 张第一批生成＋4 张第二批生成＝9 个保留历史 ID**。两批均保留原 576×576、T＝8、50 步与全组件数学，不用少步、低分辨率、占位 latent 或现有 CUT3R 档案替代主生成器。成功只说明本机透明适配后的原基线技术路径完成，不等于视频质量合格、新方法有效或创新成立。

原源码固定为 VMem `39291e4f272f6b4f270691d930926ab5930f942e`，原 checkout 只读。入口勘误及问题边界继承 `S17_BASELINE_ENTRY_CORRECTION_S19.md` 和 `S19_FEEDBACK_PATH_AUDIT.md`。所有本轮实际读取的小源码身份和时间保存在 `work/S20_protocol_review/`，未反复 hash GB 权重。

## 1. 建议冻结的输入与原入口

采用作者 `test_samples/changi.jpg`，仅作为初始已知实拍输入；本草案没有读取其文件字节或像素。将来正式 manifest 固定该文件 SHA、大小、来源版本与原预处理代码，再允许一次实际加载。无目标 RGB、传感器深度、GT 轨迹或真值相机输入。本轮导航相机是程序给定的共同输入，不是估计准确率答案。

沿原 app 的图像入口：`load_img_and_K(path, None, K=None, device='cpu')`，再 `transform_img_and_K(image, (576,576), mode='crop', K=None)`；实际 normalized tensor、PIL 输入和预处理形状均保存。初始 c2w 为 I4，K 为原 `get_default_intrinsics()` 的首项（54°、aspect ratio＝1、主点 0.5/0.5 的归一化 K）。不得混入 Bonn 光学标定 K，或把该 K 解释为 changi 的传感器标定。原 Pipeline `get_cond` 内部的列 1/2 取反和 camera centering/scale 保留；须分别记录输入相机和处理后相机，不能把被变换的临时张量重新作为历史相机。

headless 入口使用原 `Navigator` 和 `VMemPipeline`：

1. 新建一次 `VMemPipeline(config, device='cpu', dtype=torch.float32)`；构造器实际严格加载主生成器、指定 VAE、指定 CLIP、512 DPT，不能用桩替代。
2. `Navigator(pipeline, step_size=0.1, num_interpolation_frames=4)`，初始化一次。
3. `turn_left(5)`，成功提交第一批后 `turn_right(5)`，每次单独向 `generate_trajectory_frames` 传四个目标。不得改成一次传八个相机的长 trajectory。

这里的 5°是原 app “10° Turn”按钮实际值：按钮传 `y_angle=±10`，`navigate_video` 再取 `abs(y_angle // 2)`。Navigator 默认不显式给角度时为 3°，也不同于本草案。原 SLERP 分别取 t＝1/4、1/2、3/4、1；两批对应绝对 yaw 约 [1.25,2.5,3.75,5]° 和 [3.75,2.5,1.25,0]°，全部零平移。以原函数实际生成且冻结的 FP64 相机数组为准，不拿手写角度矩阵替换原插值。第二批回到已知方向有助于检查闭环是否发生，但本协议不据此定义或宣称质量收益。

正式执行从专用空 cwd 启动，配置三个输出目录均指向本次目录。原 `Navigator.initialize` 会删除相对路径 `visualization`；用隔离 cwd 避免接触旧成果，无需修改原删除函数。外层使用 `torch.no_grad()`，不包全局 `torch.inference_mode()`：原 geometry `prepare_output` 用 `torch.enable_grad()` 实际完成全局对齐。

## 2. 固定模型参数与最少设备/加载适配

默认 CPU、FP32、8 线程、seed＝42（原 YAML），一次种子初始化 Python/NumPy/Torch，第二批不重新播种。CUDA/MPS 不作为静默 fallback。保留 context4/target4/T8、H/W576、latent [8,4,72,72]、50 步、guider_types1、cfg2.0/cfg_min1.2、camera_scale2.0、surfel size512/niter400/lr0.01、原 NMS=true。只关闭会启动界面/覆盖文件的可视化副作用，用独立观察器保存完整结果；这不关闭几何、渲染、检索或条件编码。

| 最少改动或配置 | 为什么需要 | 不得扩大为 |
|---|---|---|
| 隔离 `utils/util.py::do_sample`，三个 `.to('cuda')` 改用显式 device；CPU 禁用 CUDA autocast | 原函数虽接收 CPU，仍硬搬相机/K/mask 到 CUDA | 修改步数、噪声、模型条件或精度为 BF16 |
| 复用 S17C 已核 signed RoPE CPU 分派与新纯函数 | 原 embedded fallback 没定义可用 RoPE2D；实际 blocks 中有 FP16 q/k 接口 | 从 S4 正位置公式照搬、宣称训练/任意设备等价 |
| 复用隔离 CUT3R `weights_only=True`＋已审 safe_globals；主 state_dict 显式安全加载并 strict=True | 固定公开权重的反序列化身份与实际参数装载 | 任意 allowlist、`strict=False`、随机初始化替代缺失权重 |
| 明确四组件的本地已验证路径，禁止构造器隐式联网或下新版本 | 原构造器内部 hf_hub_download、Diffusers/OpenCLIP 自动查缓存 | 使用未经证明的相似 VAE/CLIP checkpoint 冒称原指定模型 |
| 外置观察器/源码别名核对及专用 cwd | 持久记录原函数的真实输入输出，避免相对路径污染 | 改数学 core、NMS 或来源权重以便让实验通过 |

S17 已在本机 Torch2.7.0 小张量实测原 CPU FLASH 后端，故默认保留原 `Attention.forward`，**无需新增 dense attention 补丁**。全尺寸支持和峰值仍未知；遇失败留真实回执，若必须换 query 分块后端，另冻有差异的协议。原 `construct_and_store_scene` 此入口已显式传 `self.device`，因此把其默认 device 改为 None/self.device 不是原导航必需补丁。root 的 S20 隔离副本额外继承了 S17 已核的这一 helper 默认设备便利改动，须在 source manifest 明列，不能称为解决本导航设备错误所必需。headless 不导入 app，不需要修改 Gradio/Spaces 装饰器。

内存上可以在严格 `load_state_dict` 后显式释放局部 state_dict，若采用必须列入补丁并记录实际加载峰值；不偷偷顺序卸载模型/改变缓存或 offload。隔离副本、加载适配、观察器的逐文件 SHA/差异在正式运行前审完，原 checkout、S17C 源副本与旧环境均保持原样。

## 3. 两批槽位、缓存和计算账

| 阶段 | 调用前 history | 有序 context 槽 | 模型 target 槽 | padding | 真正追加 ID | 调用后 history |
|---|---:|---|---:|---:|---|---:|
| initialize | 0 | 无 | 无 | 无 | 0＝初始实拍 | 1 |
| batch 1 | 1 | 原返回 [0] | 7 | 最后相机重复三槽 | 1,2,3,4 | 5 |
| batch 2 | 5 | 原检索实际返回四槽，记录有序 ID/重复 | 4 | 0 | 5,6,7,8 | 9 |

第一批 T8 slot0 为 context0；slot1..4 保留为历史1..4，slot5..7 是 padding，无历史 ID。相机/K padding 与最后真实 target 相同，但仍有独立噪声和模型输出，不能假定像素、latent 相同。第二批 T8 前四槽为实际 context，后四槽为历史5..8。原第一批返回列表含初始图共5项，第二批返回4项；Navigator.frames 又 extend，可能包含重复初始项。**最终九帧以 `pipeline.pil_frames[0:9]` 和对应缓存 ID 为准**，不拼接返回列表或拿 Navigator.frames 长度作成功计数；不为此改原返回语义。

完整正常路径的预期观察计数，不是当前实测：主采样 2 次、每次 50 sampler steps；CFG 在模型输入维拼接为16槽，每步一次主模型调用，因此主模型前向预计100次（不是100个独立场景）。VAE 初始 encode 一张，decode 每批8槽、共16；CLIP 顶层输入依次 [1,7,4] 张，第一批 padding 也实际 encode。仅生成槽的 `samples_z` 缓存，不能重新 encode 生成 PIL 代替它。CUT3R 两次各实际读取当前5/9历史图，分别做原400步对齐，不把它算作复跑 S17C 的两张 Bonn 任务。

`cfg=2.0` 只是输入上限：原 MultiviewScaleRule 对角差<10°、平移差<1e-5、K一致的槽使用 cfg_min1.2。本建议小角度路径预计满足近距条件；正式记录实际 scale 或标为源码推断，不能称所有槽都使用CFG2。

固定 source 下每步 sampler 还调用 `randn_like`，即使 `s_churn=0`；`sigma_hat` 包含 `+1e-6`。观察器保存 sampler 收到的真实初始 noise 和前后 RNG 状态、实际步数与 sigma/模型调用信息，不修改全局随机函数、不少抽噪声、不为观察额外抽随机数。仅保存 seed 不足以描述此次实际随机状态；同批7/4目标是联合生成节点，不能按 append 顺序虚构帧间父关系。

## 4. 第二批 NMS、缓存与地图检查

第一批生成前 history1，原 `get_context_info` 直接选0，无已存在 Surfel。第一次生成提交四图后，原几何调用把5图和给定、已转换相机送入 `run_inference_from_pil`；depths=None。这不同于 S17C 的 poses=None 无先验路线。第一次地图为空则对所有5图构造候选；逐帧可合并、追加、增加来源，旧面片位置不更新。

第二批在 history恰为5时进入原 NMS=true路径，须记录 `is_second_step`、10个相机对距离、阈值排序索引 `int(10*0.5)=5`（代码注释“25th”不代表实际公式）、实际候选、排序/重复和选中ID。阈值初始化是源码保证的该分支行为，候选非空与最终选满4槽仍依赖真实结果。空地图、无候选、少于4 context 或不满足8槽形状时明确停止并保存；**不得补假历史/重复缓存来救场，不事后切NMS=false，不修改原len5条件**。实际原返回若本身包含重复ID则如实保留，重复与cache非法引用是两回事。

第二次几何输入9图、9个给定相机、首批5个旧深度图。原 `preset_depth` 的 zip 仅预设并冻结这5张深度，其余4张由原对齐求解；`preset_pose` 预设所有9相机且关闭其梯度。正常非空地图只把尾四帧5..8的面片候选送入累积合并。保存 depth cache 前后版本；旧 dense 缓存变化不等于旧 Surfel position 改写。

原 `surfel_Ks.extend` 每轮追加全部history焦距，因此正常长度0→5→14，第二轮不能强改成9。`surfel_depths` 则覆盖成当前5/9张。所有 latents/embeddings/Ks/c2ws/pil_frames 长度须为1→5→9，逐ID对齐；Surfel来源 ID 只能来自当时保留历史，padding绝不入图。原0.05缩小、confidence阈值、混合浮点 strict-z、first-write、首项票权双加和默认Octree不“顺手修复”。旧已核数学无需再跑整套回归。

## 5. 最小真实事件与档案

采用并行作者准备的 `TraceWriter`/batch观察接口；最终名字和 schema 以其正式审查合同为准，不把尚未完成的观察器写成已验证。只包实际原调用及其返回：

- 运行身份：源码/补丁、环境和模块实际路径、四组件权重版本/载入回执、配置/相机/输入身份、CPU/线程/种子、计时及内存。
- 初始化：原输入 normalized tensor、PIL身份，真实 VAE latent、CLIP embedding 及 cacheID0；记录 shape/dtype/finite，不用来自S17C或其他图的缓存。
- 每批 `get_context_info` 的有序 context IDs 与当时地图版本；缓存原值及转换后条件张量的身份；target/K、padding槽和保留映射。
- 实际 sampler 输入 noise、c/uc、camera/K/mask、RNG前后，所有 decoded samples/samples_z，包括未保留padding；主模型/采样真实调用计数。
- sampler结束、append事件、构图开始/结束分开落盘。保存新生成 PIL、其真实 embedding、进入历史的 latent，以及每次地图全量 position/normal/radius/color/source（color=None也保留）、dense depth/focal版本、候选/渲染出处和选图结果。日志 flush，异常后仍能知道最后真实完成的阶段。
- 依赖图标为**显式条件输入图**：batch→context真实缓存→保留新ID；同批共同父节点，无伪造逐帧祖先。第二批至少实际选入一个generated ID才报告“生成缓存实际回流”；只有map中含generated source或history已有五图不能证明它被消费。

不要求保存50次模型的全部中间激活，也不因此再次生成来抓日志。使用张量/数组 dtype、shape、字节摘要定义身份，避免 NumPy1.26/2.3文本repr差异。最终封存9个历史帧与两批完整输出、地图和事件；技术独立检查可以重算索引/缓存对应/相机变换/消费者证据，不默认重跑100次主模型。

## 6. 运行前真实条件及资源门

必须先具备：主 `liguang0115/vmem` 指定权重，原 `stabilityai/stable-diffusion-2-1-base/vae` 完整config＋权重，OpenCLIP `ViT-H-14/laion2b_s32b_b79k` 与实际loader匹配的模型身份，以及已经完成的公开512 DPT。读取当前合法可用缓存/下载回执确认；不将历史匿名401等同于今天永久不可用，也不替用户填写或提交联系信息。**不新增用户审批流程**；遇访问缺项保存 ACCESS_UNAVAILABLE 和具体缺失组件，继续其余已授权独立准备。替代镜像/权重只有经来源与实际参数身份核清才可进入同一基线，否则另称变体。

环境 root 当前候选是 diffusers0.32.2、open_clip_torch2.30.0、kornia0.8，overlay不改旧Torch/NumPy环境。它们目前是方案而非已通过组合；需完整 Pipeline/Navigator 导入成功、实际模块路径归属、禁止网络/实例化/权重读取守卫。正式模型加载另有阶段回执，导入PASS不能代替它。已有S17C overlay和CPU人工数值证据可复用，但不推断全尺寸生成能跑。

正式冻结表至少固定：原初图/精确9相机/K、各允许读取文件、四权重接入方式、源/补丁/观察器/外控脚本、运行解释器/overlay、原参数、输出空目录、失败条件、时间/内存界。大权重在获取完成时一次完整SHA，复用已验证收据并核路径、大小、device/inode、mtime等身份绑定；若身份变化再完整核验，不为每次文档审查反复读GB。不能把stat复核说成又做了全字节认证。

建议第一批（含首次模型加载、初始化、50步、首地图及trace保存）的外部上限：**1800秒墙钟、45GiB进程树RSS**，这是保护界而非预计耗时/峰值。外部父进程监测，达到上限终止整个子进程树，保存最后阶段、日志、部分文件、kill原因和真实清理结束时间；不能依赖模型内部自行报OOM。每批可设阶段计时且保留整进程累计时间，不能清零后漏计前期成本。

第二批的预算和自动继续条件必须在首次运行前同时冻结：建议同一存活worker、同样45GiB与额外1800秒，第一批完整提交且无非有限值/身份违规、缓存长度5、候选协议可满足后继续。最终 root 可按权重齐备后的实际资源状况另定该数值，但不能看视频好坏后增加步数、换seed或放宽停止门。若第一批资源已不足就记录部分完成并停止，不把两批目标降格为一批SUCCESS；续跑须另存合同，不无故重跑成功前缀。正式合同比本草案优先。

## 7. 成功、部分成功与失败判定

**SUCCESS_BASELINE_TECHNICAL** 必須同时满足：四个真实组件严格装载；两次原T8/50步完成；历史ID0..8唯一且缓存一致；首批真实构图＋第二批实际原render/process/NMS/cache条件选择＋第二次真实构图完成；第二批有实际generated cache被选入；有限性、条件形状及身份守卫通过；无资源界触发；封存与不同作者trace/索引复核完成。保存全部九帧的无补帧顺序预览，优先lossless PNG为规范载荷，MP4/GIF仅交付容器，需实际解码检查帧序/帧数；不能用原返回重复图把10帧展示称9个历史帧。播放速度只是展示参数，单独记录。

各失败如实分开：ACCESS_UNAVAILABLE、ENVIRONMENT_IMPORT_FAILURE、CHECKPOINT_LOAD_FAILURE、DEVICE_OPERATOR_FAILURE、CONTEXT_UNSUPPORTED、NONFINITE_OUTPUT、BUDGET_EXCEEDED、GENERATION_OR_ALIGNMENT_FAILURE、TRACE_OR_IDENTITY_FAILURE。一批已生成但地图失败、两批采样完成但trace不完整，都保留真实产物并标 PARTIAL，不能说完整baseline已完成；无可见候选也不能靠拿相机最近邻替代原路径。

几何正深度/焦距、有限值等按实际消费字段审；世界Z允许为负。退化纯旋转、PnP fallback、优化loss不单调、来源关联错误可能分别是几何局限或真实失败原因，记录原状态，不提前写成一律成功/一律失败。没有未来目标GT就不计算假PSNR/深度精度；已知起点方向重复也不等于高质量长程一致性。失败不是对S19新问题的效果反证，成功也不是它的证实。

## 8. 本草案的审查范围

应用 Supervisor `vibe-research-workflow` 的原代码理解、最小变更、先合同后执行，以及本地 Claude `sci-scientific-critical-thinking` 的构念效度/替代解释检查。没有调用Claude模型、进行新文献大综述或新增原gate的用户审批要求。已有S17/S18成功阶段不重跑。原来源主张只针对所读固定版本，详source hashes；本文件不认证当前完整依赖、权重访问或主模型实测。

下一实质准备是 root 完成禁止联网/模型实例化的完整导入，另一作者完成 trace 的人工接口核验，再审最少补丁与完整冻结表。以上实际条件尚未齐备，本协议不伪造可执行命令、权重路径、运行SHA或已生成结果。
