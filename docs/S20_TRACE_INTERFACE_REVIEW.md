# S20 生成记录工具的不同作者接口审查

**结论：记录模块的接口准备可继续；它尚未接入原 VMem 生成循环，不能据此声称真实生成、缓存回流或视频质量验证完成。** 审查者完整阅读模块、原源码接入点和作者人工程序，只读核对回执，没有重跑作者测试，没有加载模型、权重、图片、GT 或 NPZ。

正式文件身份、实际审查结束时间和已关闭问题见 `work/S20_protocol_review/trace_completion_review.json`。本审查是团队内不同作者代码审查；作者执行了人工样本，不能称外部独立模型复现。

## 发现并关闭的实际接口问题

原 `get_context_info` 首次返回 Python `[0]`，后续返回一维 Torch 整型 `context_time_indices`。本项目修复前的记录器用 `numbers.Integral` 检查迭代项，会把后续的零维 Torch Tensor 当成非法 ID。因此人工列表例通过，不能保证第二批真实接口可用；问题属于本项目新记录器，不是原 VMem 作者代码错误。

作者已补显式的一维 Torch 整数转换，拒绝浮点、布尔和二维索引；转为 CPU 整数列表后保留顺序与重复。旧版模块和人工回执未覆盖。新增 `original_interface_checks.py` 从 S20 隔离源抽取实际 CPU `do_sample` 函数，原样保留参数、`inference_mode` 和设备分派，只将 sampler、denoiser、AE 换成人工小函数。

新增实测回执 `original_cpu_interface_v1/receipt.json` 为 **15 项 PASS**，UTC 2026-09-06 12:50:50.863692 至 12:50:51.471973，0.608285 秒。该人工检查覆盖真实函数委托、原始噪声、返回样本/latent与CPU随机状态不受观察改变、作用域还原、Torch索引顺序/重复，以及float/bool/rank2拒绝。它实际调用了两次抽取的 CPU `do_sample`，没有调用主生成模型、原50步采样器、VAE、CLIP或几何模型；不能把“原函数入口”扩大成“原完整生成集成”。

原29项、后续32项小fixture回执保留；本次不同作者审查没有重复执行这些成功测试。32项属于此前模块版本，新增15项才精确绑定本次Torch-ID修复后的代码。

## 与原生成语义的契合

| 环节 | 已审契合点 | 尚须真实 producer 承担 |
|---|---|---|
| context | 按原有序ID核 live cache 与dtype/device转换后latent、embedding、camera/K；保留重复 | 实际调用原NMS/get_context_info并记录其候选/阈值/选中结果 |
| get_cond | 记录原传入 do_sample 及 sampler 的条件身份 | 保持原embedding均值、latent replace、相机中心化/尺度/取反；模块没有独立重算这些公式 |
| sampler | 只替换第4实参 sampler 为委托包装；直接接收原do_sample创建的noise；不全局patch随机函数 | 原50步、CFG模型、解码和各组件真实计数；callback计数不能冒称主model forward次数 |
| padding/cache | T与context＋target槽数一致；first 3 padding无历史ID；保留latent对应samples_z；embedding对应完整target CLIP行；旧cache身份不变 | 保留原1→5→9流程、所有原返回与图像数据、原输入有效性及有限性检查 |
| map | 构图前后完整Surfel字段及来源有序列表、内容版本；记录原surfel_Ks长度 | 实际原construct返回、原dense depth/focal缓存值、几何/渲染/查询证据，不以空人工map代替 |
| dependencies | 同批统一父节点，有序context是显式条件关系 | 第二批真的选中generated ID后才能报告回流；因果干预与质量评价另立协议 |

`sampler_enter.scale` 是原传入的cfg标量，不是 `MultiviewScaleRule` 之后逐帧生效的引导值。当前模块没有挂接guider输出，不能凭记录的2.0声称所有槽实际使用CFG2。

模块不修改grad模式。原app外层`no_grad`与geometry内部`enable_grad`可共同工作；禁止全局`inference_mode`包住需要梯度的对齐。原CPU `do_sample` 局部`inference_mode`保持不变。这个区别已经核对原 `surfel_inference.prepare_output`，不需要为观察器再改原数学。

## 持久化及成功判定边界

保存原字节的范围目前是初始noise、受支持RNG状态、每个Surfel的字段。context、c/uc、采样输出、cache latent/embedding默认只存dtype/shape/字节摘要；PIL只核历史长度，没有读取像素；dense depth/focal值不在当前map快照中。正式producer需另外封存这些真实数组/图像，才能满足 `S20_MINIMAL_VIDEO_PROTOCOL_DRAFT.md` 的完整输出档案，不能只交付本日志。

`recorded_execution` 与manifest SHA是调用者提供的身份合同，不是模块自动证明“真实模型已跑”。未来须绑定实际加载器、原函数调用、外caller及完整输出。观察器把异常与已完成前缀保留；硬kill/磁盘故障不保证有结尾事件。

`verify_trace` 检查事件链、顺序、blob和来源/槽位结构；**VALID_CLOSED_TRACE 可以包含失败batch**。只有日志结构有效不能上升为生成成功。它也不验证未保存张量原值、原get_cond数学、CPU与CUDA数值等价、物理来源正确性或模型因果效应。

本次审查未发现Torch-ID问题修复后仍阻断预定接口的确定缺陷。这里的通过仅限可审查的观察模块准备。下一阶段仍需实际接线的原两批producer、四权重/环境/输入合同、资源外控、真实执行和独立结果检查；不会用新的人工例子代替这些工作。
