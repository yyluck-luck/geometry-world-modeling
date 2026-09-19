# S87 报告源码内容审查（真实结果前）

记录UTC：2026-09-10T23:40:27.786544+00:00。角色：不同于报告作者的内容审核；本人是S87生成实现作者，不把本稿称为独立生成或VAE前向验收。

实际全文读取 `build_result_report.py`，19,156B，SHA `9b9de7dd18959e478c47bb548b361b85e47801ba3d0de5942308501b116ffc99`。对照最新S87协议bdd5…370d、冻结生成合同337982…2538、评分源码的schema/输出写入段、已冻结exporter0a7c5d…ac928，以及既有S86导出元数据。本轮没有编译/渲染、运行评分、读取S87真实数组或修改root文件；实际分数与最终页数/版面均待接受后核。

## 必须对齐的一处运行阻断

报告第40行及文内图片名用 `target_<id>_comparison.png`；已交exporter实际输出 `overview_target_<id>_2x5.png`。最小修复：builder读后者，并在报告images目录复制成前者，保留文内图片引用即可。不需改已交exporter或生成源。

报告预期root未来视觉回执至少包含 `accepted: true`、`target_observations` 字典，键为字符串20/21/22/23，各值为真实非盲观察文字。建议同时绑定实际 `export_receipt_sha256` 及查看文件/SHA；不能在未观察时填默认通过或预报重影。

## 必要的精确措辞和身份核验

- 第11节“六策略子集内”容易被理解成每族都有六个。分别明写Gpaste三策略族内、Gterminal三策略族内、合并六策略；平局全部保留、旧0.25不入新包络已正确。
- 第12节 `vae_load_seconds` 从绑定权重字节读完后起算，实际是构造/反序列化计时；请明示不包含此前文件读取和SHA核验。科学总elapsed包含全程，不需要改数字或重计时。
- 第30–33行直接读ARM_SUMMARY/FRAME_SCORES/DECISION/HISTORICAL_S86_ARM_SUMMARY。已接受scoring RECEIPT有artifacts描述符，可用其SHA直接核这四JSON；独立score review按root接受中的SHA核。该轻量绑定使“报告基于封存文件身份”具体成立，无需新增执行或框架。

## 内容、手算和枚举通过范围

完整六策略/24新行，旧16仅历史引用，G0不是新lambda0重演；共同四目标、统一lambda、三次全8解码=24chunk、无新encoder/denoiser均与合同相符。图版预定上排reference/G0/三档Gpaste，下排warp/Gguide/三档Gterminal，与exporter GRID完全对应，保持576全图后在PDF整体缩小，不构成裁剪。

每帧331776像素/995328颜色标量，四帧3981312，支持312396/292217/267572/263594、洞19380/39559/64204/68182均与旧固定mask元数据一致；区域等帧/合并权重解释正确。主差新策略减Gguide，阈值SSE≤13571317266和完整策略反例范围正确；没有把6策略未胜过当作多步必要性证明。

Gpaste映射→clamp→FP32where→uint8顺序、Gterminal分数mask融合→原sigma_hat/Euler→全8解码说明正确。lambda1不保证分数mask位置完全替换，也不保证RGB局部不变。人工A=(1,0)/B=(0,1)例中软均值风险0.25、独立随机选端点期望0.5，以及平方展开恒等式正确；明确是教学、不直接适用于非线性VAE/50步反馈/量化。文献段对应创新岗位已存原文范围，本轮未另做全文论文验证。

已见静态单场景、四相关目标、事后有限包络、VAE全局作用/累计剂量、重影非盲观察与RGB分数不能替代几何/感知/长期/动态效果均保留。proposal定位是阶段解释，不宣称新方法或完成百分比。

当前结论：方法讲解与表格设计可用；上述路径阻断及精确项已直接交root修正。真实数字、实际观察和最终交付状态不在本次PASS范围。

## 定点修订回读与初评分表结构核查（2026-09-10T23:43:18.503068+00:00）

当前builder为19,865B，SHA `d0deccfdd59416c0a3e83baa570db5c06fd461ca44c6380f5d7eb4c69e6d23f6`。仅定点回读修改区；原审查保留。原4项现为 **CLOSED，限此SHA**：读取实际overview文件并复制为文内名；族内三/合并六；VAE计时排除前置字节读取核验；四JSON沿scoring.artifacts及score review沿root接受SHA绑定。新增N、L、alpha范围与随机选择概率定义、把“排除解释”收窄为“检查解释”正确。没有重新编译、跑科学程序或读原数组。

已读初评分保存JSON的全24新行与全16旧行，并检查完整笛卡尔积顺序、各族12行、每目标固定分母、区域之和与RGB×3通道数；新行均COMPLETE，全部相符。新完整行SHA `9d06494fbd357eb9adc1c2afa8ee501cced18bcce27b4d953c4dddcf5c87907f`；旧16行SHA `332340880c2374ec26e32e3f3fde7d8dc939c7a5af2b553f1ad436bfe872efba`；summary `0965f614fdeb1810c420ca02f11d28949157ed5dd1c495cf2aea4fea9eecc3d4`；decision `03d2aaed778ea1f7983c6cb992161e4dc7d55e285356d30f97bbd9485add377f`；scoring receipt `be2dbedd9be3d434bd552674461bf54760f07888473ffca11b6e27a527ba7514`。四表身份与receipt artifacts相符。旧schema没有status/strength字段，按历史臂身份读取；首次打印器请求旧status产生KeyError，随后仅纠正打印读取，不修改记录或重跑评分。

此时独立统计核器PASS和root结果接受尚未落盘，**本段只接受填表结构/记录身份，不提前接受分数复算**。初评分显示唯一完整四帧反例为Gterminal .75；它的四帧均值较低，但目标22的.0748324332高于旧Gguide的.0682643877，20/21/23较低。已提醒root最终只说“四帧均值”，不说“四目标全部改善”。小数尚待独立统计闭合，未作感知/几何/速度/跨场景结论。最终TeX实际数字、完整PDF和真实观察仍待root通知后核。
