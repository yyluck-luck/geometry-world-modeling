# S30：两种初始化尺度的完整优化对照（候选，未运行）

沿 Supervisor 2.2 的基线失败／根因对照，检验“保留模型点图的名义尺度作为起点，能否在原目标下保持更好的消费者深度”。本轮是普通工程控制，不是新方法。原提案仍是 Geometry-aware World Modeling；该已见 common4 深度组件不代表视频或长期记忆结果。

依据 root 转交的 S29 实测：2026-09-06 17:52:48.654534–17:53:10.901356 UTC，2 MST／6 PnP／2 无梯度 objective，0 优化／GT／模型；23 个身份与数学门通过，所有原 pre-log z 正且有限。C2t 为原 s0≈0.17318、原 R0、中心均值匹配 T；C2a 为 s=1、同 R0、同一均值匹配公式。两个控制的共享前缀通过；初始化深度按理论缩放，C2t/B 初态深度接近。以上由 root 报告，本作者本轮只读相关 JSON 身份／源码，未读取真实数组。S28 的仅梯度修复使指标更坏，不能将其 loss 下降当精度提高。

**唯一待比较因素仍是中心均值对齐这一变换族中的初始化 s。** 两臂都用已验证的修复 getter，原消费的 anchor self／其余 other pointmap+conf、原 star、原给定 optical GT camera control、`depths=None`、固定 image pose/pp、相同 focal/pairwise/depth 可训练配置。相似变换返回分别为 `(s0,R0,ḡ−s0R0c̄)` 和 `(1,R0,ḡ−R0c̄)`；R0 不动。整个优化过程中 edge scale 仍按原代码可训练，不能称“全程固定尺度”。不加 sensor-depth prior／GT 比例／额外 self 头、旋转修复、正则或调参。

## 新运行与复用边界

| 臂 | 初态门 | 本轮新增计算 |
|---|---|---|
| C2t | 新原路径初始化必须与已封存 S29/C2t 全 33 个 parameter/buffer 名称、shape、dtype、flags、raw bytes 及原 objective 逐字相同 | 原 MST/PnP 新建状态与 optimizer，然后原 Adam 400 步／linear／lr=.01 |
| C2a | 同上，对其自己的 S29/C2a 封存初态；不要求它与 C2t 的 depth/pair geometry 相同 | 同上 |

需要新初始化的理由是沿原函数正常新建 optimizer，并以完整原参数逐字核验避免 decoded 值逆编码或假装恢复历史对象。它服务本轮新的 400 步延续，不重跑 S28 已成功 A/B；S29 的已封存零步数组直接作为初点评分，绝不为其评分再跑 MST。

两臂顺序全新子进程，CPU8／FP32／seed0，每臂 120 秒／4 GiB RSS。预算总 2 MST／6 PnP／800 Adam／800 backward／0 网络。沿用 S28 两次 getter 边界无更新目标求值 + 原 400 次优化 forward + 原 clean 前一次 postfinal 求值，各臂 403 次 objective forward。后续独立公式复算不冒称网络或 optimizer forward。评分额外 120 秒／2 GiB。任何资源／源身份／初态门／梯度／原数学门失败均保留产物，不自动延长预算或重跑。

## 实现范围

复用原 S26B 保存与独立 objective／backprojection／clean 门、S28 逐步 observer 和单表达式 getter；只派生臂名、共同初始化返回、各自 S29 初态参考门与本轮回执名字。保留清楚 diff／AST 派生清单，不复制原 GA 数学。每步原 Adam 前核 depth 梯度非 None、有限（允许为零），原冻结参数不动，参数／buffer对象和 optimizer 成员保持；400 行 loss/lr/深度变化/focal/edge-scale trace、完整首末 raw 状态与原 clean 产物全部保存。

两臂原始预测、全部数值门与输出文件封存后，才进入独立评分子进程。先绑定两份 S29 零步档案与两份 S30 终点，再统一解码原 4 张 sensor GT，使用原 `nearest_grid`／`depth_metrics`／`aggregate`，不重写数学。共同原分母，raw-scale AbsRel/RMSE/delta1/无效预测，严格原阈值，无 confidence mask、无远点剔除、无尺度拟合。固定输出 2 臂×2 端点×4 帧=16 行，四个均值组；同一 GT 数据只加载一次。每臂“终点−起点”指标差只描述预定 400 步代价，不能选择中间最好步。

## 可反证与停止

- 新初态若不能逐字复现其 S29 全 33 项和 objective，第一步 Adam 前停止；不把看似接近的起点当同一条件。
- 若 C2a 零步更准，但原 400 步使它缩小／误差变大，普通初始化修正不足以解决原目标后续问题；保留负结果，不临时固定 scale 或加 prior。
- 若 C2a 终点更准，只支持这个已见 common4 的普通起点控制收益；需要后续更多场景／真实消费者／生成才能提出范围更广的结论。C2t 才是本轮匹配尺度对照，不把它相对原 B 的平移差混入因果归因。
- 若两臂轨迹没有预想区别，同样完整报告；loss、深度缩放和 sensor 精度是不同量。两个条件都跑预定完整 400 步，不根据答案提前结束／挑步／选超参。

本候选仅用于 root 全文审、另一作者前审与单独冻结；尚未执行新 MST、优化、真实数组或 GT 读取，原冻结文件与主账未改。实际准备时刻记录在本目录 preparation_receipt.json。
