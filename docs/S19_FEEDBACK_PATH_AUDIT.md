# S19 反馈路径审查：拒绝“生成后代改写旧 Surfel 几何”版本

**Verdict：Reject and Pivot，限问题1的“生成后代覆盖已有 Surfel 几何字段”版本。** 原 VMem 的正常累积写入并不修改已存在 Surfel 的 position、normal、radius、color。这个版本触发了 [S19 问题筛选](S19_RESEARCH_QUESTION_TRIAGE.md) 自定的即时退出条件。原稿“旧几何被错误覆盖”若没有明确区分对象字段与渲染像素，就不能作为已成立的问题继续评分。

这是固定源码的反证与构念审查，**不是生成实验、效果负结果或文献新颖性证明**。不把它套称为 skill 中“数据已被基线击败”的情形；此处是核心事件在所指原写入函数中不存在。按 Supervisor idea-evaluator 的 CRITICAL 短路规则，停止原版本的五维打分与乐观防御。将“覆盖”改指屏幕占据或来源关联会改变研究对象，必须另立问题。

致命问题登记为 **F6 / CRITICAL：所计划原系统实验不能验证被定义为旧对象坐标覆盖的核心事件**。这是本次把 skill 的“何种实验能证明主张”规则应用到接口构念的判断；不是因为尚未跑模型就否定未测想法。原版本没有可补救的实验阈值，处置是退出该版本。

## 四种事件必须分开

固定来源为 VMem commit `39291e4f272f6b4f270691d930926ab5930f942e`；[pipeline.py](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py) SHA `90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`。下表行号均指该原文件。

| 构念 | 原路径与确切限制 | 本项目已实际证明什么 |
|---|---|---|
| 改写旧几何字段 | merge 第799–830行读取旧 position/normal，成功只在第820–821行追加来源ID；没有把新 position/normal/radius 写给旧对象。第1082行 extend 未匹配的新对象。 | S18 两实拍组件已核首写字段不变；它没有生成后代。正常增量原路径不支持本候选声称的旧对象坐标覆盖。 |
| 追加几何引起像素竞争 | 新候选未匹配时第825–826行保留，随后 extend。render 第334–405行依面片朝向、投影多边形、平均顶点深度及原严格比较写 z-buffer/ID。新对象可以成为某些像素的输出者，旧对象仍在地图中。 | S18 确有追加和渲染组件，但未测“生成错误压过真实观测”。像素占据改变不能叫旧 Surfel 坐标被重写，也不自动是真实遮挡或几何错误。 |
| 来源关联改变 | 匹配成功时，旧 Surfel 仍可获得新的 generated frame ID。process 第479–492行对每个可见 Surfel 的所有来源投票；get_context_info 第655–753行形成候选再经相机距离/NMS选择。 | 静态上存在来源改变消费者的路径；S18 只含真实照片来源0/1，不能当作生成祖先重复证据的实测。来源数量也没有在 merge 中变成旧几何的置信加权更新。 |
| 生成 latent/embedding 回流 | 第1288–1298行把生成图、sampler 输出的 target samples_z、生成图的 image embedding 存入历史；第517–522行按被选ID取缓存，get_cond 第1124、1145–1158行使用 embedding 均值及 latent replace；第1270行送入下一次 do_sample。 | 原代码有真实模型条件回流入口。当前没有原视频生成闭环、实际父依赖日志或该通路的质量干预；不能用占位缓存或 source IDs 代替。 |

`utils/util.py` 第1274–1285行的 Surfel 构造器写入四个字段；审查正常 generate/store/merge/render 路径未找到后续几何字段赋值。render 将 normal 转成新 float 数组再归一化，并非原对象 normal 的原地改写。reset 第135–145行清空记忆，undo 第1336–1404行删除部分对象、清除来源并重编号，是不同入口；它们也不是“生成后代把旧坐标融合成新坐标”。本结论不覆盖用户未来另改的算法。

## 静态反馈链确实存在，但不是原假设那条写入链

顺序为：get_context_info 选择历史缓存 → get_cond 形成 latent/embedding/camera 条件 → do_sample 同批采样 → 存生成缓存/PIL → construct_and_store_scene → 新几何追加或来源关联 → 下一次 get_context_info。`utils/util.py` 第697–732行显示 sampler 产出 samples_z，再由 VAE decode 得 samples；生成后的缓存 latent 来自这份 sampler 输出，并不是本轮重新 encode_vae_image 的结果。初始真实图则在 initialize 第173–177行经过 VAE/image encoder。

两处边界不能遗漏：

- **首份地图不等于已有旧 Surfel 被改写。** initialize 第162–185行只置初始实拍和缓存，并未建 Surfel。首次生成完成后，空地图从完整图序列第一次构造；生成图可能参与该次联合几何估计。若要研究“首次错误几何被共同生成输入诱导”，那是另一个初始化构念，不是旧对象覆盖。
- **非空地图处理尾窗，不保证每个候选都来自新照片。** construct 第979–996行把全部历史图及给定相机、已有 depth 送入重建并更新 dense depth/focal 缓存；第1026行取 `N-target_num_frames` 到 N。在默认满4帧新批次中它是新4帧；若实际只追加1–3帧，尾窗会包含旧帧的新候选。旧候选也可能被追加为新对象，仍未覆盖已有对象字段。dense depth 缓存被重新赋值不等于 Surfel position 被改写。

因此不能从“没有旧字段覆盖”推出“所有生成反馈风险均不存在”；也不能反过来拿任意缓存变化替原假设辩护。

## 现在没有可用于祖先实验的实际依赖日志

源码的 `context_time_indices` 在第753–764行形成/返回，第1249–1260行被生成调用取得，又在第1306行作为 `time_indices` 传给 construct。**AST核对显示 construct 的函数体对该参数零次读取**；真实写入来源使用第1044/1056行的 frame_idx。这个实参名字不能当作已经保存的父依赖图。

固定 pipeline 的可选保存是图片/GIF；未找到 generation-call→selected-context IDs/latents/embeddings→retained-target IDs 的持久事件记录。现有 S17C/S18 JSON 也没有实际生成父依赖：S18 记录 model_calls=0、full_context_calls=0、video_generated=false。S18 source lists、candidate provenance、查询 votes 是地图来源与消费者记录，不能替代生成因果依赖。此判断限定已核原路径与本项目控制回执，不宣称所有外部系统都没有此日志。

若未来另立生成依赖问题，至少先实际记录每次生成的调用ID、当时 map 版本、按顺序选中的 context IDs 与真实 latent/embedding 身份、全部 target camera/保留及 padding 标记、输入噪声或 RNG 状态和输出 frame 身份。还需把“显式条件输入关系”和“实测因果效应”分开。单次 do_sample 同时生成多个目标，不能依据第1293行保存循环的顺序，虚构同批图 j 是图 j−1 的后代；共同批次与跨批次父依赖应分别表示。当前只提出日志必要条件，没有实现或宣称采集完成。

## 入口勘误：首次7个模型目标不一定实际追加7帧

默认 YAML 第9–11行是 context4 / target4 / num_frames8。必须同时检查**调用入口、请求相机数量、padding、保存数量及下一次检索时机**：

| 入口条件 | 首轮实际路径 | 下一次 context 的条件 |
|---|---|---|
| 原 app/Navigator 默认每步4个新相机 | navigation.py 第25、131–133行及 app.py 第181行给出4个插值 target。初始仅1帧时 pipeline 第1218–1243行补至7个模型 target；第1293行减去3个 padding，只追加4帧，history变5。 | 第一次 get_context_info 在生成前看到history1，直接选0；下一次调用才看到5，满足第674行的 NMS 初始化条件。前/后移动还在 navigation.py 第185–187、234–236行显式关闭NMS；转向第321行使用默认配置。 |
| 直接长 generate_trajectory_frames，或 __call__ 提供足够长路径 | 初始仅1帧且首批有至少7个真实 target 时，不需首批padding，实际追加7，history变8。__call__ 第1427–1429行先用首图 initialize，再传其余相机；不是同一个4-target导航入口。 | 若后来进入非空历史检索、有效候选路径并启用NMS，history8不触发len5初始化。源码未见其他默认 initial_threshold 初始化，下一次第708行读取存在未初始化风险。这里只是条件化源码发现，未运行模型、未观测到 AttributeError。 |
| 调用前已存在多帧历史 | 第1221行通常取最多4 target；第1249行先检索再生成。 | 取决于当前history是否5、此前阈值是否已初始化、NMS是否关闭，以及候选是否可用。没有公开“任意多实拍初始化后自动正确”的保证；initialize 接口本身是一张图。 |

`generate_trajectory_frames` 的公开形参是相机列表、K列表和可选NMS，没有单独的 num_frames 参数。修改 config.num_frames 会改变第1219行首批计划，且调用 do_sample 仍显式 T=8（第1279行）；本审查没有测这种配置兼容性。若短请求导致 generation_steps 不进入循环，也不能套用上表“完成首轮后的history”结论。

本节给 [S18旧草案](S18_MEMORY_BRIDGE_PREPARATION.md) 中“原视频通常初始1图加生成4图到5图”的泛化表述补上入口限定：它适用于已核4-target导航保存路径，不能覆盖所有 trajectory 调用。**原 `len==5` 初始化事实仍真，S18未调用完整get_context_info的结论也不变。** 不修改冻结的 S18 文档、代码和实验结果；不据此宣称原系统所有场景都不能运行。

## 处置与唯一另行登记的问题

原版本停止：不实现“阻止 generated descendants 改写旧 Surfel 坐标”的新方法，不把三维坐标不变的 S18 结果当作后代误差实验。该核心构念在所指原写入路径中不成立，更多模型运行不能补上不存在的写语句。

可以另行登记一个更窄、**未验证且未确证新颖**的问题：**固定旧 Surfel 几何和查询像素出处后，生成图新增的来源关联，是否会改变后续选中的真实缓存条件，并在已观测区域造成普通质量/去重/数量控制无法解释的约束损失？** 它的干预对象是 source association 与 conditioning，不是旧几何坐标覆盖；追加几何的遮挡是需分离的另一因素。原源码仅支持“存在可能的传递接口”，不支持效应存在、相关祖先是原因或新方法优于基线。

该新问题不继承原问题的7分或 Accept。真实短生成闭环、可靠依赖事件、同信息/成本控制和独立约束评价未具备前，保持未立项状态；不使用无生成的 S18 再做代理消融。本轮仅静态源码/已有JSON审查，0模型、0真实图片、0NPZ解码、0算法实现；主账由 root 更新。完整范围、原文件SHA、AST观察与实际记录时间见 [审查回执](../work/S19_feedback_path/receipt.json)。
