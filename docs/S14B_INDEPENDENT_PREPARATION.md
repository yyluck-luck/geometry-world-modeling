# S14B独立核验准备

本文件记录不同作者的执行前准备。代码准备完成且人工检查通过；尚未运行真实S14B数值核验，不能据此声称真实连接或测量通过。最终源码SHA与实际准备时间见 `work/S14B_independent_preparation/preparation_receipt.json`，后续真实核验输出另存新目录。

独立核验器为 `scripts/verify_s14b_disagreement_independent.py`。生产作者只提供文件字段合同；本作者没有阅读或导入生产测量函数。推导依据为本项目设计、原 `src/s7_event_replay.py` 的观测标识/事件/首写回放、`scripts/run_s7_replay.py` 的保存结构，以及 `src/s6_memory_bridge.py` 的像素行优先顺序。准备时只解读S7 block0的一份事件JSON及一份来源JSON以了解结构；12个NPZ结构来自既有header记录，未解码真实预测数组，没有读GT、评分、查询或S14A/S13数值结果。

已阅读并应用 `/Users/rocket/.claude/skills/sci-scientific-critical-thinking/SKILL.md` 的测量效度、独立方法交叉核对、预定分析和结论比例原则；没有调用Claude模型或CLI。具体落实为：不把同帧像素当成独立帧；保留单来源点；测量含义限定为固定已筛选关联的预测分散；冻结相同容差并保留失败；不把代数恒等式误说成算法优势。该脚本说明不需要另造科研示意图。

核验时首先读取结果目录的 `execution_manifest.json`，它必须是冻结manifest原文拷贝。要求schema为 `s14b-observation-disagreement-v1`、精确24路径及SHA、生产快照SHA `source_sha256`、核验器SHA `independent_verifier_sha256`。输入路径集合在核验器中固定为S7/S8各3块的stride8四份文件，先检查路径集合再读任何数组。生产 `source_snapshot.py` 只读取字节核SHA，不作为代码读取或执行。运行后再次核输入、结果文件与自身源码身份，输出目录存在即拒绝覆盖。

连接使用独立Python字典重建，每个扁平观测索引恰好一次；核20帧边界、frame/u/v唯一性、步幅与行优先顺序、targets/matches出生编号和既存约束、每点来源集合与counts、原图每点首写points和radii精确一致。NumPy只用于反序列化和dtype/shape/finite检查，没有使用NumPy均值或分位数重算指标。

先把每个观测减去固定首写位置，在局部坐标中用 `math.fsum` 求和；每帧质心和帧内平方差分别计算，跨帧等权。W为帧内方差的平均，B为帧质心围绕其均值的平方差平均，A为该均值到首写锚点的平方距离，D直接从各质心到锚点的平方距离求平均，随后才核 `D=B+A`。四项再分别除以该点原地图半径平方，不加epsilon。零、负、非有限半径及其平方溢出/下溢均拒绝。

精确核身份和整数。浮点门固定为 `abs(actual-reference) <= 1e-12 + 1e-10*abs(reference)`，reference为独立重算值；不采用观察结果后放宽的门。m=1的独立B必须精确为0。输出比较覆盖逐点CSV的全部23字段、逐帧CSV的10字段、全连接索引JSON和6块摘要。摘要仅对每块exact m分层核点数和8量的均值/中位数/p90；分位数由排序后 `(n-1)*q` 的相邻位置线性插值独立实现。

人工检查保存在 `work/S14B_independent_preparation/synthetic_checks.json`。同帧不等像素例：第一帧横坐标0和2，第二帧7，锚点0、半径2；手算W=0.5、B=9、A=16、D=25。另有单来源、零分散、整体平移1e12、六种非法半径、4种linear分位数。该回执中single_source(W=1,A=1)仅为通用measure公式的单组例；它不可能作为本项目合法A0P0单来源事件，因为合法m=1点只含一条出生观测，W/B/A/D都为0。连接人工例另外检查该项目规则。全部属于软件检查，不是新场景或实测效果。详细连接人工检查另见该目录的connection_checks.json；原初回执不随代码小改覆盖，最终源码人工复核另存v2。

真实结果产生且冻结审读通过后，由根执行：

```sh
python3 scripts/verify_s14b_disagreement_independent.py --result results/S14B_observation_disagreement --output results/S14B_independent_verification
```

结果目录名由根最终合同确定，CLI本身不假定固定结果名。失败时新目录保留 `verification.json` 的UTC、环境、检查数、首次详细错误和traceback、自身源码快照；不改生产结果。本阶段没有GT联结、拟合、候选排序、训练或视频验证。
