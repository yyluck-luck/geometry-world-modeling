# S40 保存量读回：独立初审 v1

时间：2026-09-07T05:02:33.248010+00:00 UTC。已全文审读 315 行，绑定源码 `3e3d1b6a9e41aa4be6268088501ed555520282e8d652466d92d8cd5a8424f3ef`。结论：**需要补齐两个验收合同缺口；不是实际结果失败或 PASS**。本轮没有 import/执行脚本，没有打开预测数组、权重、GT、旧人工 case 或新空 case。

1. **Trace 状态链未完整核验（196–211、270–279 行）。** Hashchain 可以证明封存记录内部一致，但当前仅按出现顺序提取两次 begin/end/cache_commit，没有逐批核唯一 ID、完整 sample/sampler/cache/map 状态转换、关闭后不得追加以及回调归属。协议声称“两链顺序与闭合”，需要补一个只读状态机，并将 archive 已有的 metadata.batch_id 对到 trace 同批。
2. **上游保存值桥接尚缺（207–258 行）。** 现有检查从 commit 的 target_encoder_embeddings 开始，没有接上同批已归档 encode_image_output，也没有核 samples 的全部目标行→encode_image_input；sampler_output→samples_z 同样缺失。目标相机/K虽已与cache比较，但进入 translation/get_cond 的后缀未与原 batch_input 逐值核对。补这些已存值比较及 translation 标量对应即可，无需重算任何神经网络或相机数学。

已通过的静态部分包括完整动态 archive 文件清单/字节哈希/descriptor/sidecar、trace 真 blob 的字节核验、第一批cache→第二批所选context→get_cond→sampler replace 的实际值检查，以及小相机 FP64→FP32 的单独标签。不能将本次源码评价替代真实 S40 输出验收。

CPU1、RSS2GiB 当前是外控建议；300秒只是协作 tick，并非阻断所有慢操作的硬时限。NumPy memmap 降低数组额外内存，但 JSON/事件列表仍会驻留。实际执行必须由父任务外控线程/RSS/总时限并记录实测，当前预算未验证。

详细字段、源码来源身份、缺口与修改建议见 source_review_v1.json。初始问题回执保留；后续仅对稳定新 SHA 增量复审。
