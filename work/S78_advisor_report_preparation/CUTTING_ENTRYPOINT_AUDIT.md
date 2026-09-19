# 裁剪入口审查与动态消费者取舍

记录日期：2026-09-10。本批公开材料获取时间为15:03:25–15:04:39 UTC（北京时间23:03:25–23:04:39），随后作静态阅读与整理；精确时刻见同目录 `cutting_entrypoint_audit/` 下三份获取回执。

**结果：固定版本仓库没有独立的裁剪源码文件；在本批检查的3个小notebook以及前批已经排除的QA/跟踪演示中，未找到cut-frame映射的消费入口。** 不能据此声称所有官方资源都没有实现：两个其他notebook和外部资源未在本批阅读。仍没有足够证据确认QA cutoff的端点约定，因此没有建立已核实的真实样例前缀。

本批新增的一条精确事实是：官方可视化的动作/声音绘制循环使用 `range(start_frame, end_frame)`，排除结束帧；这只约束该绘制函数，**不能据此认定QA的cutoff也排除端点**。不修改主实验，不启动模型。

## 1. 固定仓库树与3个小文件

统一版本：`3938d2f1ba3a6b502025741cea4cd73c7b3bdfaf`。读取对象限官方仓库；QA notebook本批未重读。新获取的树元数据3,866字节，`truncated=false`，列出11个普通文件、无额外gitlink。源码/演示共7个notebook；其余是README、LICENSE、CONTRIBUTING和.gitignore，没有 `.py`、`.sh` 或名为cut/preprocess的独立脚本。[固定树API](https://api.github.com/repos/google-deepmind/perception_test/git/trees/3938d2f1ba3a6b502025741cea4cd73c7b3bdfaf?recursive=1)

| 官方文件 | 实际获取与身份 | 读取范围及结论 |
|---|---|---|
| [data_visualisation.ipynb](https://github.com/google-deepmind/perception_test/blob/3938d2f1ba3a6b502025741cea4cd73c7b3bdfaf/data_visualisation.ipynb) | 32,230字节；SHA256 `4707275b12bace37c4cfc718125792b9236f30f9e78de9f7c3277c70a643c8fe`；官方Contents API于15:04:37.804592–15:04:39.266432 UTC返回。 | 提取13个代码单元。`load_mp4_to_frames/get_video_frames`读取完整视频；`paint_sound/paint_action`按各标注区间绘字；没有cutoff映射或QA裁剪调用。 |
| [baselines/grounded_vqa.ipynb](https://github.com/google-deepmind/perception_test/blob/3938d2f1ba3a6b502025741cea4cd73c7b3bdfaf/baselines/grounded_vqa.ipynb) | 56,716字节；SHA256 `da4108b183bd46da6c67191ad7c840e2342b28dda21566e97ade084d1e12d148`；官方Contents API于15:04:37.805840–15:04:39.403252 UTC返回。 | 提取14个代码单元。Dataset用总帧数的中点读一帧，再配合静态跟踪；没有cutoff映射。这个中点必须另外证明位于合法前缀，不能直接视为合法。 |
| [baselines/temporal_action_localisation.ipynb](https://github.com/google-deepmind/perception_test/blob/3938d2f1ba3a6b502025741cea4cd73c7b3bdfaf/baselines/temporal_action_localisation.ipynb) | 10,887字节；SHA256 `091bcba2fe2648adeede02ee74bd986479b03cea487a4d83d5e2f99b0212d68b`；raw于15:04:06.096616–15:04:07.104292 UTC返回。 | 提取6个代码单元。链接官方适配ActionFormer，下载预计算特征和动作标签，再调用评测；该notebook没有QA映射或视频裁剪逻辑。外部ActionFormer仓库本批未进入。 |

前两个raw请求发生TLS失败，均保留returncode 35；每个仅改用一次**官方GitHub Contents API**成功获取，没有循环重试。API响应是notebook源码文件的base64传输封装，解开该传输层后仅提取code source；未读取/渲染作者已有输出、未解码内嵌媒体、未读取真实样例答案、未执行任何notebook下载或模型命令。

本批未读：`single_point_tracking.ipynb`、`temporal_sound_localisation.ipynb`，外部ActionFormer、Dataset Explorer、挑战页面及云端切帧文件正文。前批QA和single_object_tracking的结论只引用既有审查，不冒充这批新阅读。原README已核链接包括train/valid切帧映射，但链接存在不等于裁剪实现已核。

## 2. 精确源码逻辑与范围

行号指 `cutting_entrypoint_audit/*.ipynb.code.txt` 中的一基行号，不是原notebook的JSON行号。

- **可视化读帧：** `data_visualisation` 第98–145行从VideoCapture逐帧读至结束，再返回总长度视频；第218行末轴反转是颜色通道变换，时间轴仍为完整 `:`，不能误认成时间裁剪。
- **动作/声音端点：** 同文件第345–346、378–379行，以二元素 `frame_ids` 解出start/end，再使用排除end的range绘制。它证明该函数如何画标注，不证明标注任务的全部规范，更不证明不同用途的QA cutoff。
- **grounded QA取帧：** `grounded_vqa` 第181–202行用 `CAP_PROP_POS_FRAMES` 定位一帧；第289–300行传入 `round(num_frames/2)`。没有使用cut-frame映射，所以不能独立建立过去限定的输入。其余显示辅助函数仍可读取全视频，不能在有答案隔离要求时直接执行展示单元。
- **动作定位：** `temporal_action_localisation` 121行代码均已读，仅涉及依赖、现有特征/标签、模型与评测入口；没有原RGB切帧参数。它处理的是视频动作段定位，不是本项目的QA预测截止条件。

三个文件全部代码单元中，对 `cut_frame/cut_frames/cutoff/cut_frame_mapping/ffmpeg/subclip/trim` 的定点搜索均无命中。搜索与函数级阅读共同支持上述有限结论；“某字符串未命中”单独不是对所有潜在实现的证明。

## 3. 不看答案能否独立建立前缀

**原则上可以，但当前仍缺官方语义绑定。** 若明确c对应的保留区间及原视频编号，裁剪器只需video_id、匹配split的映射、视频帧索引与总长度；不需要问题、选项、答案、未来对象状态或动作语义。这是待实现接口设计，不是已运行结果。

当前不能确定c是最后保留帧还是第一排除帧，也未核实实际样例的映射/视频版本一致性。因此现在只能保存切帧值，不能认证已生成的前缀。不能根据答案或尾段内容反向决定截止时刻。即使下一步找到官方切帧代码，样例的初始化时间、时间轴、split关联和下游实际可见输入仍须分别核查。

如果需要作者公开说明，最小问题可压缩为以下两项（**尚未发送，不代表有发送授权**）：

1. In `cut_frame_mapping_train/valid.json`, is the mapped frame the last included frame or the first excluded frame, and which frame-index origin does it use?
2. Which released script or exact command applies this mapping to the original videos, including missing entries and video-version alignment, without consulting question answers?

这两项直接解决端点和可复现入口；不需要请作者替我们挑选成功案例。

## 4. 复用已有证据：哪些消费者真的推进物理时间

以下仅复用2026-09-09已保存的原文/源码审查，未重新联网核权重与运行状态；不能当作今天的成功加载记录。目的是分清任务接口，避免把相机变化当成时间变化。

| 消费者 | 允许输入与输出 | 与“实拍小球/杯子＋k帧选择”的差别 | 当前合理用途 |
|---|---|---|---|
| **FloWM 3D Dynamic Blockworld** | 已观察RGB序列、历史动作、未来观察者动作；按目标动作序列长度输出后续RGB。既有源码审查中target RGB可缺省、teacher forcing为0，标准评测为70历史帧后预测70或210帧。[已核固定源码](https://github.com/hlillemark/flowm/blob/c909c54a3d58ae240de03f5ebbec222d3e6b1264/algorithms/mem_wm/backbones/flowm/flowm_models_3d.py#L526) | 是模拟方块与已知相机动作，不是未知人手操纵的实拍杯子。它按离散步骤推进；删除帧再当相邻步骤会改变时间和训练合同。 | 既有证据支持优先做原任务的本机可行性验证；若后续执行，先复现原动态基线，不直接塞入稀疏k帧或改成杯子任务。 |
| **WorldMem** | Minecraft动作、姿态/时间条件和历史视觉记忆，逐步生成；选择器含视场、时间与去冗余。[已核作者论文](https://arxiv.org/html/2504.12369v2) | 接近固定历史帧生成问题，但不等于已具备实拍杯子状态推断。历史审查的app硬编码CUDA；本机代价未实测。 | 作为强近邻与后续有条件基线；不从论文时间嵌入推断它支持任意物理时距或未见人手动作。 |
| **ReMind公开5B DMD推理** | 一张图或视频前缀，文本/控制preset，随后按时间块生成并累积cache。已存官方说明的V2V例子使用21帧前缀；代码建立known-prefix mask。[已核固定入口](https://github.com/Applied-Intuition-Open-Source/ReMind/blob/bf316a30b10f444e15adf5ddf710fa9f97e34ee9/pipeline/remind_inference.py#L710) | 有真实时间展开，但公开路径读取累积cache，不是已部署的自动固定k事件选择器。文本中给出的动作/状态若是未来答案，会改变信息合同；必须另行审查。 | 作为前缀续生成和事件记忆近邻；不直接宣称是零额外训练、等计算、实拍动态预测基线。 |
| **现有VMem/SEVA路径（参照项）** | 历史图像集合与目标相机条件，产生目标视角图像。 | 相机槽位不等于物理时刻；相机响应分析不证明物体动态推断。 | 保留已有静态多视角基线结论，不将它当上述动态候选已经运行。 |

上述接口信息的本地证据：`work/S70_fixed_context_generation/innovation_round_10/PROBLEM_DECISION.md`、`innovation_round_11/PROBLEM_DECISION.md`；`work/S77_generated_wrong_pose_control/innovation_sources/fixed_budget_collision_01/NOTE.md`；`work/S76_relative_camera_response/innovation_sources/event_memory_nearest/code_followup/NOTE.md` 与 `docs_inference.md`。FloWM与WorldMem更详细的身份和资源边界以这些已保存审查为准；本批不新增GPU耗时、模型精度或加载成功主张。

**下一科学判断没有改变：** 实拍杯子线先解决合法前缀和简单身份/状态对照；动态生成线先核消费者自身的原任务与时间接口。当前没有证据允许用一个尚未合格的数据窗口、一个静态视角模型和一个未匹配的k帧改动组合出“新动态记忆方法”。本批有实际源码取证，零模型运行，零新科学结果，`NO_METHOD_SELECTED`保持。
