# S34 评分器源码审查

全文读取 `score_s34.py`、`protocol.md`、当前 metadata candidate，并复读冻结 S26B `depth_metrics/aggregate/load_sensor_depths`。**评分数学和完整分母没有阻断；执行结论仍待真实 producer/consumer 合同与终态屏障绑定。** 没有运行评分、读取预测或 sensor 字节。

已确认：固定三端点的新4–7，共12行/3组，旧4不进入均值；原有效GT分母、严格δ1阈值、无效预测/空GT的NA和四帧全定义组均值保持。六字段shape/FP32门与共同old depth预定往返容差存在。四packet要求PASS，receipt和所有producer输出先字节封存，之后才decode；实际consumer终态须存在，consumer失败仍可评分合法geometry，但结果显式携带失败且不称整体S34通过。无k、重配对、mask、远距筛选、渲染GT准确率或生成质量主张。

冻结前只剩一项需与 consumer 作者实际接口衔接：**不仅核 consumer receipt 的 status，还要核它的 producer/consumer contract 身份与本次冻结合同一致。** 当前 candidate 的 `producer_contract` 和 `terminal_barrier` 均为null，不能执行。建议 root 在 terminal barrier 构造时核真实 consumer receipt 的合同字段并保存；scorer 对同一字段交叉核一次。不能将“同路径且status相同”单独当成本次合法consumer证据。此项不改指标或实验设计。

CPU1/120秒/2GiB、10GiB空盘是外部调用器责任；正式屏障还应只封本次实际所有产物、保留 consumer FAIL，并明确所有 GT PNG 字节尚未读。源/元数据审不代表这些未来执行条件已满足。

审查对象 SHA、时间、范围与本项待闭环条件见 `scorer_source_review.json`。无需重做原指标测试或增加臂。
