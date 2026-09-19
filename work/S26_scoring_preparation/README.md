# S26 评分器准备交接

2026-09-06 15:19 UTC 后整理。本目录是评分器作者的独立准备区域，不修改主账或已冻结 S24/S26 producer 文件。

- 入口：`scripts/score_s26_consumer.py`；正式协议：`docs/S26_CONSUMER_SCORING_PROTOCOL.md`。
- `candidate_scoring_inputs.json` 已通过 metadata-only 入口生成。父任务把整个 JSON 放入正式 manifest 的 `scoring` 字段，再绑定正式 manifest SHA。它引用的 8 个 sensor PNG SHA 来自 S23 既存 receipt，本轮未读取这些 PNG 字节。
- `check_artificial.py` 58 项作者检查在 15:18:56 UTC 通过，结果 `artificial_checks_v1.json`。固定 NumPy 向量公式与标准库标量 fsum 路径核数；完整 640×480→512×384 nearest 与 PIL/标量路径一致。小 FP32 NPZ 是现场构造的人工文件字节，未使用真实预测。
- 现有目录拒绝、四模式 PASS/input seal/NPZ hash 门、无效值不删分母、严格 δ1 边界、旧 depth 1e-6+1e-6 容差、四帧完整均值均有人工检查。门控只是程序顺序及身份检查，不能证明没有其他进程读取 GT。
- 真实数组读取 0、真实 PNG 字节读取 0、GA 0、模型 0、score 0。父任务后续静态审查、冻结、运行和不同作者真实复算尚未由本准备报告宣称完成。

调用合同与 PASS 的含义见正式协议。评分器需要四个 `receipt.json` 绑定父 SHA、模式、frame_count、`inputs_seal_sha256` 和字符串 `outputs["output.npz"]`；input seal 声明 `sensor_depth_used:false` 并绑定同一父 SHA。输入身份不足或旧深度超预定容差就在 GT 前停止。

最终主结果是 cut3r / ttt3r / filt3r 的索引 4–7 raw-meter depth 等帧均值；old4 与 all8 单列诊断。所有新帧的有效 GT 像素保留，无 conf/远点/尺度筛选。任何有效 GT 处的无效预测使该帧 AbsRel/RMSE=null，同时在 δ1 分母中算失败。共同相机为 GT control、8 张 GT 已看过、片段仅约 0.236 秒，不能解释为新机制或生成提升。

`preparation_receipt.json` 记录精确源/协议/检查器/候选身份与实际时点。主研究日志由父任务统一追加，避免多作者同时改主账。
