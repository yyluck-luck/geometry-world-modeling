# 顶会近邻刷新回执：来源绑定、相机门与全局状态

- 检索时间：`2026-09-08T08:13:14Z`（北京时间 `2026-09-08T16:13:14+08:00`）
- 目的：主动寻找能否否定PC-DPM新颖性的等价设计，而不是用关键词未命中证明首创
- 证据边界：两篇CVF正式论文PDF完成本地文本核读；一篇NeurIPS正式会议页完成摘要核读。没有运行模型、没有读取C1/C2图片正文、没有产生方法结果
- 当前裁决：`NOVELTY_AUTHORIZATION_NONE`

## 一手来源核对

### Movie Weaver，CVPR 2025

- 正式PDF：<https://openaccess.thecvf.com/content/CVPR2025/papers/Liang_Movie_Weaver_Tuning-Free_Multi-Concept_Video_Personalization_with_Anchored_Prompts_CVPR_2025_paper.pdf>
- 本次下载PDF SHA-256：`eb6c6d346235ee681e45c0661973a4431937a0be6505c4f4bc7e31b18d2f24c7`
- 核到的方法事实：论文明确指出普通cross-attention对参考顺序不敏感并可能产生identity blending；其anchored prompts用`[R1]/[R2]`将概念描述连到对应参考图，concept embeddings编码参考图顺序。
- 对本项目的排重：source tag、reference order和concept-image linkage不是新贡献。PC-DPM必须比较这一类强基线，并证明ordinary-retrieved memory里的跨consumer共享provenance提供额外因果与样本外收益。

### Geometry-as-context，CVPR 2026

- 正式PDF：<https://openaccess.thecvf.com/content/CVPR2026/papers/Hu_Geometry-as-context_Modulating_Explicit_3D_in_Scene-consistent_Video_Generation_to_Geometry_CVPR_2026_paper.pdf>
- 本次下载PDF SHA-256：`b2817bb1c656909fbb8ed927b9a3edda07b7c9c8be0d07d0a982ad7404a464d4`
- 核到的方法事实：模型交替处理RGB与geometry context；camera-gated attention把Plucker-ray相机特征用于调制self-attention，并用geometry dropout支持RGB-only推理。
- 对本项目的排重：camera-conditioned gate、显式geometry context和geometry dropout均已被占据。PC-DPM的几何分支必须将camera gate作为强对照。

### Learning World Models for Interactive Video Generation / VRAG，NeurIPS 2025

- 正式会议页：<https://proceedings.neurips.cc/paper_files/paper/2025/hash/e32310c3acb058d563a6a9e54d0e9000-Abstract-Conference.html>
- 本次核对范围：正式摘要；本轮PDF网络获取失败，因此没有把摘要外细节写成已核事实。
- 核到的方法事实：论文区分自回归累积误差和memory不足，并用video retrieval augmented generation加显式global-state conditioning改善长期一致性。
- 对本项目的排重：不能把全部长期漂移默认归因于source provenance；未来强对照必须包括no-memory、普通retrieval和global-state conditioning。

## 对创新候选的实际影响

新增近邻没有杀死“跨consumer共享provenance”这个窄假设，但显著提高了门槛：

1. M1必须覆盖参考顺序/source token容量强基线；
2. M2必须覆盖source mask、per-source geometry attention与camera-gated geometry；
3. 失败归因必须区分普通自回归误差、memory不足、已选但未消费、消费位置错误和selected source负收益；
4. 只有M3共享provenance在容量与计算匹配下胜过上述强基线，且P0–P3跨scene成立，才保留方法贡献；
5. 任一决定门失败就停止或降级，不通过改名字保存故事。

## Supervisor-Skills 2.3 对应关系

- 第一性原理：把目标固定为“历史证据是否在正确位置真正且有益地约束未来生成”。
- 房间里的大象：存储/检索成功并不证明被消费，也不证明有益。
- 技术周期：source ID、camera gate、geometry attention和global state已成为常规部件，不能靠组件叠加制造新颖性。
- Hamming问题：保留“世界模型如何知道自己的某条记忆何时、何地值得信任”；是否足够重要由跨模型/跨scene失败率和收益决定。
