# S76 单 yaw 实际保存量独立核验

通过：`PASS_S76_INDEPENDENT_SAVED_GENERATION`，308/308 核项通过，0 discrepancy / blocker。这是不同作者的团队内保存量核验，不是再运行生成模型或独立外部模型复现。

已按 root 真实 SHA，使用词法绝对 `.venv-cut3r/bin/python -B` 执行冻结 verifier 一次，执行前复核 source 与 root source acceptance。外部 2026-09-09T09:42:41.323239+00:00 至 2026-09-09T09:42:41.666316+00:00，0.343101583 秒，return 0，120 秒限时未触发，stderr 空。内部 0.245825875 秒，采样 self peak 146,325,504 B。44 次记录读取、41 个独立文件、38,520,165 B；未读取权重正文、RGB 文件，未导入模型/Torch/OpenCV，也没有重做生成、get_cond、renderer 或 SIFT。授权的保存 FP32/uint8 数组已作数值读取，未作为图像查看。

实际保存的 50 步与 trace/progress 一致，每步 RNG 前后、初始噪声全部字节、sampler-entry/common/terminal RNG 与旧 A0 对应。模型完整值/模式及本次进程对象身份由实际 source/receipt/snapshot 元数据相互绑定；不把它表述为审查者现场观察每个模型参数。全部新增 NPY/NPZ 的文件 SHA、字段、shape/dtype、finite、body SHA 均通过；完整 8 latent 与 4 raw/uint8 目标被保留。原非干预条件、历史 ray、K/masks/中心及 appearance 字节核通过。

独立局部 yaw 列展开、原 lower-median/0.97 中心与自然尺度、相机代数光线/叉积及 576×576 正反 FOV 全掩码核通过。独立 FP64 尺度为 27.3220544137032，对应保存 FP32 27.322040557861328，符合结果前固定容差。全部八 slot 独立光线最大绝对差为 4.733852588145737e-6。固定 H 与 true inverse 变体的投影差仅作近似误差诊断：

| 目标 | 固定 H 对 inverse 的最大像素差 | 共同正深度且图内像素 |
|---|---:|---:|
| 20 | 4.65225120873e-05 | 291593 |
| 21 | 6.98523042631e-05 | 291592 |
| 22 | 4.57333044001e-05 | 291593 |
| 23 | 4.75236333413e-05 | 291593 |

这些差异未替换冻结 H，没有改变评分合同。四帧原 NumPy 量化分支均使用 `(x+1)/2` 后 clip/truncate，保存 uint8 全字节一致；原 FP32 超出 [-1,1] 的数值保留在 raw 数组，未隐藏。Torch advisory branch 本次与实际 NumPy 分支一致，仍不当作通用权威量化判定。

本票只确认已执行生成的保存量与既定单 yaw 干预/随机流一致。尚未核未来 score 或评价视觉质量；没有证明全图相机符合、匹配真值、校准精度、H-noise 严格等变性或新方法成立。全部负结果/UNKNOWN 的后续解释边界保持。

实际内部回执 `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S76_relative_camera_response/independent_review_01/generation_01/receipt.json` SHA256 `37a6d249209918fbfb7b96836d2ac05fe437d9c48dc6503a8fc4d92799a4aad1`。

实际外部回执 `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S76_relative_camera_response/independent_review_01/generation_external_01/receipt.json` SHA256 `460e0a08cfc90401793ec5ffcc926172c45f6bb2859f7125c48cdee6a51b70e4`。

冻结 verifier SHA256 `d7bf57ef8d90b94719cdcbf5e8688e0accaa0d056ad9b4d16a309d6c34c84b50`；root source acceptance SHA256 `7d124741751cf404370cdc9f4a84de66a9141ead65fca0e9ad6accba9b18f24e`。
