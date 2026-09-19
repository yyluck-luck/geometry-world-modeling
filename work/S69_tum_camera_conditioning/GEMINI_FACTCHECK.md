# S69：Gemini可见答复的定点反查

完成UTC：2026-09-09T02:16:02.911714+00:00；审查者`/root/negative_result_question_triage`。本补充不改已冻结输入审查，不增加生成臂。实际只读公开原文、项目文字与源码，0 RGB/深度/GT数值/权重正文，0模型或科学数值执行。继续应用本地scientific-critical-thinking的证据、混杂与统计边界，不调用Claude。

**结论：接受“输入尺度可能影响网络、自然重算中介有助于比较原条件”的有限提醒；拒绝错误出处、不存在的depth/warp通路、单次重放方差、已孤立内容效应，以及未经结果证明的灾难/bug判断。**

## 原答身份与出处核对

已全文读root保存的`GEMINI_VISIBLE_RESPONSE.txt`，SHA `0005bde657af92ab91f3831a0123c6bbfcbfc4bbfc983432388c3d1ec848db00`；其`GEMINI_OBSERVATION.json` SHA `2082122f0d1068b5d9b1a7791158e73aea1446aa161ee296ea1807c0fa6a3600`记录完成观察上界02:12:54.963040Z、3.1 Pro Advanced reasoning/Extended thinking。AX遗漏行内公式，本文没有填补遗漏，不能称核过完整公式转录。

| 可见答复的主张 | 原始来源与裁决 |
|---|---|
| CameraCtrl是CVPR2024 | **错误。** 正式[ICLR proceedings](https://proceedings.iclr.cc/paper_files/paper/2025/hash/f98fd73d59d8494489ea970747b91fe4-Abstract-Conference.html)列ICLR2025，正式标题为CameraCtrl: Enabling Camera Control for Video Diffusion Models。 |
| arXiv:2404.02101 | **正确。** [arXiv版本记录](https://arxiv.org/abs/2404.02101)为v1 2024-04-02、v2 2025-03-13；早期标题含Text-to-Video Generation。不可因会议错误把编号也否掉。 |
| §4.1明确证明Plücker尺度脆弱 | **所引段落不支持。** 作者[v1 §4.1](https://arxiv.org/html/2404.02101v1#S4.SS1)及[v2 §4.1](https://arxiv.org/html/2404.02101v2#S4.SS1)都讲基础模型、训练与评估设置。v2 §3.2讨论直接使用原始外参的幅度和像素对应困难，并以Plücker作替代；这不是VMem尺度干预的证据。 |
| 文中尺度问题可直接证明本接口不鲁棒 | **越界。** [v2附录D.5](https://arxiv.org/html/2404.02101v2#A4.SS5)处理COLMAP恢复轨迹的尺度对齐，还报告失败轨迹被过滤；这是评估端的不确定性，不能改写成输入尺度干预已导致生成失真。 |

“网络未被本接口显式约束为尺度不变”是可由模型设计提出的待测解释；不能推导每次改幅值必有伪影、色偏或拓扑断裂，更不能预先认定为实现bug。本次也不从§3.2的文字论证替代当前VMem源码的射线公式。

## 当前接口没有Gemini虚构的depth/warp消费

已完整核原`pipeline.py:1123–1195`的`get_cond`：参数仅为context latents、全部相机、K、scale、encoder embeddings、mask。实际执行是CLIP均值；相机轴翻号/求逆/平移缩放；由相机和K构建Plücker；latent补一个有效性通道并按mask放入`replace`；mask与Plücker组成`concat`，另以`dense_vector`传递Plücker。**它没有输入深度，也没有按深度重投影或warp latent。** latent的第五通道是填1/0的标记，不是深度。

因此不存在“这里还必须把源深度或latent几何网格同比缩放”的源码依据。上游surfel检索使用几何，不能据此虚构本次已选集合的额外depth消费。下游仍收到相机/K；若将来做scale干预，应从输入scale一致重算本接口的全部受影响相机和c/uc，而不是只篡改一份moment后称路径一致。此处只说明范围，不授权干预。

源码身份：`work/S20_environment/isolated_vmem_source/modeling/pipeline.py` SHA `680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255`，已读1089–1195；`utils/util.py` SHA `30a97451f7a895e99ab881e97249f564e6b97eca2b5ea4d8f83953c26c4cf65e`，已读57–150。没有导入或执行这些函数。

## 一次重放及第三臂到底识别什么

A与一次相同输入重放，只提供**本次一对输出的重放差异**。不能把它叫作已经识别的非确定性方差、一般噪声分布或稳定显著性界限。即使两次字节相等，也只证实这两次一致；若不同，还要区分未绑定RNG/状态与算子行为。当前CPU执行，cuDNN例子不适用；这也不等于已证明CPU必然确定。此纠正不要求现在追加重复运行。

为避免符号误导，令`G(A,s)`表示固定A的有序参考内容、相机、K及共同外生状态，尺度取s且全部相关后代自然重算。若以后另行声明并实际执行A_with_sB：

- `G(A,sB)−G(A,sA)`：固定A上的尺度干预效应。
- `G(B,sB)−G(A,sB)`：固定sB下其余**整套**输入差异；含12/14替换、13换槽位、相应参考相机与外观条件，不能叫纯内容或纯顺序效应。
- 二者可沿这条顺序相加为原B−A；这样的分解不证明交互为零，也不唯一分离两条机制。没有`G(B,sA)`就不能对称估计两因素交互。本轮不因此添加第四臂或更大的消融矩阵。

主A/B保持各自原算法自然重算，可以作为**条件于固定两套有序参考的消费者比较**；它既不是上游在线检索全流程总效应，也不是某一来源或尺度的孤立价值。真实收益还需冻结参考误差，影响本身不能定收益符号。

原答指定“必须自然长轨迹scale剧跳并严重崩坏”、永久锁首帧scale或对Plücker加InstanceNorm，都只是尚未验证的具体猜测/基线候选。不能成为现在的新强制门，也不能因简单就假定语义正确或有效。保持当前最小完整生成路径，尚无新方法或已成立架构缺陷。

## 实际检索范围与失败保留

本轮检索开始上界2026-09-09 02:11:51Z（首批搜索调用前未独立打点），公开读取结束上界02:14:37Z。成功读：ICLR官方条目行0–6；arXiv版本记录行19–28；作者v1 HTML的§3.2–3.3、§4.1；作者v2 HTML的§3.2–3.3、§4.1、附录D.5（web行118–141、161–167、375–378），并定点find“4.1”“scale”。作者GitHub用于身份交叉核，不据其他论文引用反推会议。

[OpenReview正式PDF入口](https://openreview.net/pdf?id=Z4evOUYrk7)实际转浏览器验证页；ICLR条目的Paper/Supplemental点击各返回Internal Error。随后直接尝试同proceedings的`f98fd73d59d8494489ea970747b91fe4-Paper-Conference.pdf`及更远§4.3读取未返回，在有界范围内终止该工具单元；不记为成功或全文阅读。结论依据上述实际可访问官方会议信息与作者v1/v2原文，不声称读完正式PDF或全部消融。本轮未新下载论文/数据，不修改既有两件套、生产入口、协议或主账。
