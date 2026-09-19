# S75：五张真实历史照片，经已有 VAE 缓存能还原到什么程度？

**五张已保存历史的 VAE 解码均完成，保存结果的独立数值复核通过。** root 实际看过全部五组照片：桌边、显示器、玩偶等粗结构大致对应，小纹理有所平滑。但只有 **31.52%–51.83%** 的原图特征找到接受匹配，且存在很大的坐标偏差。因此本轮不能证明“VAE 完全没问题”，更不能据此认定或排除 S70 取景偏差的原因。

VAE 在这里负责把图像压缩表示（latent）还原成图片。此次使用 S68 已编码的历史 **12、13、14、18、19**，沿原包装函数用 **latent÷0.18215** 解码；没有重新编码、运行 CLIP、VMem 视频采样或读取新目标答案。每张参考图是原照片按既有处理得到的 576×576 输入；五个参考 FP32 数据体均逐字节匹配 S68 身份。这是**五次真实神经网络解码**，后面的独立复核只读取其保存数组、PNG 和匹配坐标，未再次运行模型。

| 历史 ID | 原始 MSE | 原始 MAE | 匹配 M / 原图特征 N | 匹配可用率 | 匹配位移中位数 px | p95 px | 最大值 px | >10 px 点数 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 12 | 0.0030294796 | 0.0351155172 | 331 / 864 | 38.31% | 0.538384 | 2.246750 | 50.308 | 2 / 331 |
| 13 | 0.0023554933 | 0.0315610440 | 368 / 710 | 51.83% | 0.473497 | 2.185670 | 174.481 | 4 / 368 |
| 14 | 0.0040734555 | 0.0386592239 | 487 / 1447 | 33.66% | 0.538518 | 2.279993 | 453.504 | 7 / 487 |
| 18 | 0.0044893037 | 0.0400692812 | 463 / 1468 | 31.54% | 0.523430 | 2.256433 | 454.078 | 4 / 463 |
| 19 | 0.0040323075 | 0.0380160334 | 389 / 1234 | 31.52% | 0.498168 | 2.435359 | 480.846 | 8 / 389 |

MSE 是逐通道误差平方的平均，MAE 是绝对误差的平均；每张都纳入完整 **995,328 个通道数值**。两者在输入约定的 **[-1,1] 数值尺度**上计算，解码值即使越界也不裁剪、不配准、不遮罩。MSE 的量纲是该数值尺度的平方，MAE 是该尺度本身。解码范围实际达到约 **−1.0795 至 1.2121**，所有越界值都保留在原始评分中。

显示 PNG 单独采用固定映射：先 `(x+1)/2`、裁剪到 [0,1]，乘 255 后就近量化；参考与还原图使用同一规则。独立标量实现核对了全部十张 PNG 的每个像素字节，完全一致。**S70 的主评分是按原 `tensor_to_pil` 分支/截断得到的 uint8 图再除以 255；本表既不是这个分数，也不能直接与 S70 数值比较。** 同样，S75 的特征数不能直接当作使用另一量化规则的 S72/S73 的同一分母。

匹配位移只描述接受的互惠 SIFT 特征对——程序在两张图片都认为对应的一小组点。低中位数没有包含未匹配的 48.17%–68.48% 原图特征，也不证明匹配本身正确。五组的 p95 约 2.19–2.44 px，但最大值依次为 **50.308、174.481、453.504、454.078、480.846 px**；不能删除这些大值，亦不能直接当作真实物体移动。匹配在 4×4 网格分别占据 14、16、16、16、16 格，这只表示分布跨度，不是整图重建正确率。全部五张、完整分位数、阈值计数、未匹配分母和越界数值均保留。

全部五组配对图（左为处理后的实拍参考，右为 VAE 还原；不是新视频帧）：[历史 12](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S75_vae_history_roundtrip/visuals_01/history_12_pair.png>)；[历史 13](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S75_vae_history_roundtrip/visuals_01/history_13_pair.png>)；[历史 14](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S75_vae_history_roundtrip/visuals_01/history_14_pair.png>)；[历史 18](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S75_vae_history_roundtrip/visuals_01/history_18_pair.png>)；[历史 19](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S75_vae_history_roundtrip/visuals_01/history_19_pair.png>)。[五组总览](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S75_vae_history_roundtrip/visuals_01/ALL_FIVE_PAIRS.png>)。

root 的全五组查看时间为 **2026-09-09 08:31:43.118090 UTC**（北京时间 16:31:43），见 [实际视觉观察记录](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S75_vae_history_roundtrip/visuals_01/ROOT_VISUAL_QA.json>)。上述“粗结构大致对应、纹理平滑”来自该记录；本报告作者独立核了保存像素字节和数值，没有另作图像主观评分。视觉观察不能替代误差统计，也不证明这些特征对是真实对应。

实际模型运行的外部时间为 **2026-09-09 08:17:14.953014–08:17:32.452432 UTC**（北京时间 16:17:14–16:17:32），**17.499437 秒**，return 0、未触发停止。不同作者复核发生在 **08:31:05.734361–08:31:08.630294 UTC**，**2.895733 秒**，一次执行，**202/202 项通过**。原始 MSE/MAE 采用 Python 标量与 `math.fsum` 复算，最大差 **6.94×10⁻¹⁸**；坐标统计最大差 **4.44×10⁻¹⁶ px**。容差在复核前已固定：原始误差绝对 10⁻¹² / 相对 10⁻¹⁰，坐标统计绝对 10⁻⁹ / 相对 10⁻¹²。身份、像素字节和计数要求精确一致。

复核共读 **44 个唯一文件、45,430,184 字节**，其中解码十份 FP32 数组和十张 PNG 的数据体合计 **49,766,400 字节**；没有读权重、原照片或 latent 正文，没有重跑 VAE/SIFT。源码、工作进程与进度记录共同支持“**五次 decode、一次权重字节消费**”；这是对已存证据的核对，不能写成独立现场观察了五次模型调用。实际组件声明为 **ft-mse VAE**，其与原 SD2.1 VAE 的精确来源身份仍为 **UNKNOWN**。

该结果只覆盖一个场景的五份已有图像均值 latent；视频模型生成的 latent 可能有不同分布。因此仍不能证明完整消费者兼容、相机服从、生成画质收益或 VAE 因果归因。**S73 的 UNKNOWN 不变，NO_METHOD / 新方法未验证不变。** 后续 [S76 相机相对响应草案](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S76_relative_camera_response/PROTOCOL_DRAFT.md>) 拟保持历史和原随机流，施加固定 +5° 目标相机转动，观察相对响应；这是 DRAFT，单臂连接与评分尚待实现和核验，本报告没有执行新生成，也不把固定图像网格噪声当成严格几何等变条件。

root 于 **2026-09-09T08:47:33.416749+00:00** 完成最终接收：逐一核验独立回执、202 项检查、实际五行与输出文件身份，并确认全五组照片已实际查看。接收仅限上述五历史解码及保存量算术；[最终接收记录](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S75_vae_history_roundtrip/ROOT_RESULT_ACCEPTANCE.json>)。本报告初版整理时该接收尚未完成，初版已保存在本阶段目录，未倒填接收时间。

证据：[冻结合同](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S75_vae_history_roundtrip/CONTRACT.json>)；[实际模型回执](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S75_vae_history_roundtrip/execution_01/receipt.json>)；[外部进程回执](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S75_vae_history_roundtrip/external_01/receipt.json>)；[不同作者源与结果审查](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S75_vae_history_roundtrip/independent_review_01/RESULT_REVIEW.md>)；[完整复算记录](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S75_vae_history_roundtrip/independent_review_01/receipt.json>)。

本文由 `/root/c2_v9_source_primary` 于 **2026-09-09T08:45:40.748123+00:00** 根据已存结果整理。独立结果审查 SHA256：`da1fa65336f2a50dfde9034ffdb06b89dadbd3f434684944b7a83fabca211aff`；完整复算回执 SHA256：`3ca87db455613ea0a87c3420055f6add467ceb513b9065c9ad64e90e83f2aa16`。
