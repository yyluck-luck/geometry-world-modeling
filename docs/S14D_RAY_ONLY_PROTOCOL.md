# S14D-I：无目标照片的 CUT3R 接口探针（运行前协议）

本阶段只回答：本地预训练 CUT3R 的官方 direct ray-only 接口能否消费历史状态和给定相机射线，并在不读取目标照片、不写回历史状态的情况下输出有限的几何预测？这是新输入条件的接口实验，不是新方法、几何准确率或视频质量实验。目标相机为虚拟设置，输入历史图像来自真实 TUM 数据。

S14C已完成的负结果不重跑。普通目标像素覆盖设计见 S14D_TARGET_VIEW_DESIGN_DRAFT.md；本轮不执行其旧24查询测量或再关联旧评分。近邻报告已说明普通覆盖与传统MVS并非新机制。先修复当前研究的输入域缺口，再讨论新方法。

## 固定输入和实际调用

- 使用原S8 block0前20张历史RGB，顺序和字节身份取其保存metadata并核SHA；不读取该块4张query RGB，不读取深度、GT位姿、旧NPZ预测或评分。
- 复用已有224 linear CUT3R权重，官方commit 8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf。CPU 8线程、FP32，原内部RoPE精度语义不改；仅沿用既有signed RoPE兼容层，不改上游源码。
- 历史照片执行一次官方 `inference`，全部update=True；旧实验没有保存可直接复用的latent state，因此重建这次新条件需要的历史状态。不是重复原RGB-query效果实验。
- 新history输出的20个预测c2w中，设距离为 `||t_i-t_0||`，只保留大于1e-6的距离；若为空技术停止。步长d为其median乘0.05，单位为模型预测尺度，不是米。使用最后历史c2w，沿其局部相机轴给四目标偏移 `(0,0,0),(d,0,0),(-d,0,0),(0,0,d)`；不依据结果挑位姿。
- 图像尺寸224×224；K严格使用官方viewer pseudo intrinsics：f=sqrt(224²+224²)、主点(112,112)。目标不是TUM真实相机轨迹，不能配旧GT评价。
- `viser_utils.py`的两个纯方法通过AST原样提取，ro=t，rd=normalize(R K^-1[u,v,1]+t)。该官方约定含平移项，不是标准的纯方向射线；本次只验证此官方接口。不得暗改为物理方向或对效果作解释。
- 按Q0/NaN、Q0/zero、Q1/NaN、Q2/NaN、Q3/NaN共5次官方 `inference_step`。query的img只是(1,3,224,224)人工占位，ray为(1,224,224,6)，img_mask=False、ray_mask=True、update=False、reset=False。直接路径与mixed路径不默认等价。

## 验证和解释

技术完成条件：所有5调用返回所需FP32几何/置信度/pose schema且全部tensor有限；Q0占位NaN与zero的所有输出逐值/字节相同；五个历史state张量每次前后shape、dtype、SHA和数值相同；query图像encoder实际处理batch数0、ray encoder调用5；四组输入rays不同，20历史图的打开/解码来源和partial失败留痕；冻结输入/代码和manifest身份前后相同。

另报告每个移位目标相对Q0在两个pts3d输出中的最大绝对差，`>1e-6`仅记为“检测到接口条件响应”。不超过该阈值不是模型调用失败，也不意味着视角没有物理意义；不调整阈值，不据响应大小论准确率或创新。

独立核验从保存数组重算历史encoding→pose、局部位姿偏移和逐像素ray，使用不同公式实现，预定atol1e-6/rtol1e-5；整数/域/原始字节/状态/dummy输出精确。独立核验不重新运行神经网络，不是不同模型对结果真实性的验证。

资源由独立外部caller执行：墙钟上限600秒，监测RSS上限32GiB，不在循环中重试。进程/输出失败立即保留metadata、stdout/stderr、已返回每call数组。源码改动仅在真实执行前完成；若真实执行失败，要另记录后续修复的范围，不能覆盖失败文件。

## 预期产物和未完成项

保留运行metadata、20历史相机编码/位姿、4目标位姿/K/rays、5query全部tensor、before/after latent state、每call状态hash/flags/schema/时间、实际源码和冻结manifest、独立核验报告。数据规模是1段已见真实历史+4人工相机条件，不是4个真实独立场景。

通过此探针仍不能证明：参考图选择更优、ray几何准确、历史记忆改进有效、生成视频更好或达到论文贡献。后续需要在合法目标输入域明确可用信息，再制定真实评价协议与普通覆盖/一致性/相机基线。
