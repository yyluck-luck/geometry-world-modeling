# S33：普通尺度约束超过零步与事后恢复的局部基线结果

**三个可评分片段上，普通的训练内共同配对尺度约束在AbsRel、RMSE、δ1三项上均好于自己的零步和已有事后公共尺度恢复。主实验与评分已完成，独立数值复核尚在准备。** 这是一项基线加固结果；尺度约束已有DUSt3R机制，不能将其改名宣称创新方法。

本轮新增1200次真实Adam/反向传播、3MST/9PnP/3clean，0新模型调用；复用S32同窗真实RGB推理保存的头。旧48行分数和CSV逐字导入，仅给新候选追加16行，其中12行评分、4行缺相机NA。没有重跑旧三对照、没有为新终点再算k或用GT调尺度。

## 完整对照与结果

四个窗口与S32完全一致：fr2_desk原987–990、1974–1977；fr1_xyz原264–267、529–532。每窗4帧约0.10秒。原strict20ms一对一相机配对使第一窗缺相机，继续保留NA，不重选窗口。相机均为显式允许的GT optical c2w；这是已见场景、已评分开发窗口，先封输出不让它变回盲测。

| 固定窗口 | 零步 | 原400步 | 原400步+事后k | 新400步训练内尺度约束 |
|---|---:|---:|---:|---:|
| fr2_desk_j1 | NA | NA | NA | NA |
| fr2_desk_j2 | 11.49439% | 40.00581% | 12.33071% | 10.82468% |
| fr1_xyz_j1 | 13.20508% | 17.45834% | 13.19783% | 12.63547% |
| fr1_xyz_j2 | 10.16412% | 19.30582% | 10.20706% | 9.05079% |
| **全部四个预定窗均值** | **NA** | **NA** | **NA** | **NA** |
| 三个预定相机完整窗的描述均值 | 11.62120% | 25.58999% | 11.91187% | 10.83698% |

表中为AbsRel（越低越好），每窗四帧等权，最后一行是固定三个相机完整窗的描述汇总。全部四窗均值仍为NA；完整设计为64行、16窗条件组，48可评分/16NA，其中旧48行原值不变。没有将帧/像素当独立样本，没有显著性或跨场景泛化结论。

相对零步，新条件AbsRel改善分别为0.66971、0.56961、1.11333个百分点；固定三窗描述均值改善约0.78422个百分点。对所有主指标同时检查如下，不能仅对比变差的自由尺度400步。

| 窗口与强对照 | RMSE↓（米） | δ1↑ |
|---|---:|---:|
| fr2_desk_j2 零步 | 0.241984014 | 89.331684% |
| fr2_desk_j2 事后k | 0.271504644 | 88.876527% |
| fr2_desk_j2 训练内尺度约束 | 0.233422320 | 90.013584% |
| fr1_xyz_j1 零步 | 0.193070394 | 95.396782% |
| fr1_xyz_j1 事后k | 0.194183513 | 95.155460% |
| fr1_xyz_j1 训练内尺度约束 | 0.187024319 | 96.178268% |
| fr1_xyz_j2 零步 | 0.115626028 | 98.029715% |
| fr1_xyz_j2 事后k | 0.115930355 | 98.205503% |
| fr1_xyz_j2 训练内尺度约束 | 0.105649489 | 98.471245% |

全部GT有效像素与旧同窗对照完全相同，三窗分别642877/625608/594549；对应缺失像素143555/160824/191883；候选预测无效像素均0。未加confidence mask、far-cut、逐帧归一化或GT拟合。

## 只改变哪一处

S32的给定相机路径关闭`norm_pw_scale`。本轮在每窗原MST后、第一次Adam前，以实际初始化的三个raw log尺度均值m0为固定常量：

```python
m0 = scene.pw_poses[:, -1].detach().mean().clone()
factor = (m0 - scene.pw_poses[:, -1].mean()).exp()
```

只覆盖实例`get_pw_norm_scale_factor`；当前mean保持可微，只有m0 detach。原`get_pw_scale`与`get_pw_poses`不改，整个3×4变换的旋转和平移共同乘有效尺度；原`norm_pw_scale=False`不翻转，避免连带改变adaptors，也不引入默认0.5或强写1.0。

三个实际m0为1.1920928244535389e-7、1.6689286894688848e-6、-8.344653110725631e-7。初态factor均恰为1。每窗原33参数/buffer的名字、dtype、shape、训练flag、raw bytes，以及全部decoded、objective、C2a alignment逐字匹配S32自身初态后才安装。插入仍位于原两个无更新loss之间：无多一次优化，无额外scene objective。

固定共同有效尺度保留相对边尺度、depth、focal、pair旋转和平移训练；相机/pp及原冻结参数保持。全400步前后有效尺度log均值门atol1e-5、相对比值门atol/rtol1e-5及完整3×4门通过。raw log尺度均值本身可随Adam漂移，不能误要求其不变。

这改变了允许的优化集合。非共心给定相机下，不能称无损纯坐标规范变换；也不能把公共pair尺度固定等同于每个深度都正确或全部自由度不再退化。

## 实际时间、资源与原路径核验

- 正式生产合同SHA `44a817a74afe10a16b758cc8fa6f7a17781d34d41ac575dd24e73b1ac1101400`，runner `bd2711d50da6200453a40f73074e4b11d60a67d1e25d0a8ae22ad66f0fb9f392`。不同作者源审和根全文审先完成，47来源身份绑定。
- 实际UTC20:21:37.068277–20:23:02.862184，85.793940秒。三个可用窗外控28.037553/28.549757/28.603975秒，峰值1024868352/1024933888/1021673472字节，均低于CPU8/120秒/4GiB每窗预算。第一缺窗为科学UNAVAILABLE，外控正常退出不是有科学分数。PID36281/session39485已exit0，不重复运行。
- 各窗实际400Adam/400backward、1MST/3PnP/1clean，403原objective（400+既有边界2+末端1）。原getter梯度修复及所有实际深度梯度记录、冻结/优化器成员门保留；clean独立参考失配0，world重投影最大差各7.5805e-7/5.3381e-7/3.5658e-7，原目标独立式检查通过。
- 原初始objective为5.4427943/1.6599680/2.5770812，新末端为0.015193712/0.010242216/0.010412384。有限步非凸优化各有轨迹，不能用某个末端loss的高低替代深度评分或最优值证明。
- 根核全部四窗终态及83项新产物/终态/dispatch文件字节后封存，见`work/S33_scoring_freeze/endpoint_barrier.json`。评分正式manifest SHA `83be08e12d3102487cf31f902c396db49567cfdbc63cbfeba12b02d3ab1665ab`。评分UTC20:24:46.482439–46.990395，首次GT字节20:24:46.720067；外控1.032831秒/RSS95846400字节，CPU1/120秒/2GiB。12传感器GT仅用于新端点评分；旧JSON/CSV按SHA导入，CSV保留旧48行字节前缀。session62695已exit0。

<!-- INDEPENDENT_REVIEW_BEGIN -->
独立数值复核正在准备，尚未PASS。主执行内部门与source前审不替代不同作者对完整新端点、64行表、400步scale与梯度保存记录的实际重算。
<!-- INDEPENDENT_REVIEW_END -->

## 机制解释及创新边界

S32已经显示事后一个k能恢复大量误差，S33进一步在这三个短窗中取得对零步和k的净收益。这支持把共同pair尺度约束纳入一个更强的开发基线；仍不能证明它是唯一原因、普遍收益或新机制。

<!-- DEPTH_DRIFT_BEGIN -->
协议要求比较共同depth log偏移的幅度是否减小。当前已确认有效pair尺度执行门通过；完整预测像素的mu独立分析尚待完成，不以pair尺度门代替深度漂移结果。
<!-- DEPTH_DRIFT_END -->

根另从原欧氏残差目标构造条件性缩小路径，得到`J(a)<=aJ(1)+(1-a)C`；C由给定相机基线和固定权重组成。**必须假设固定权重非负**；原log(conf)变换需要conf>=1，本轮未核每个实际输入或计算实例C。另一作者代数审通过并要求明确该前提，修改前稿与审阅均保留。该推导没有证明Adam实际走了此路径，也没有改变本轮预定设置。见[条件推导与范围](../work/S33_mechanism_analysis/conditional_scale_path.md)、[独立审](../work/S33_mechanism_analysis/review/review.md)、[权重假设修订闭环](../work/S33_mechanism_analysis/review/revision_closure.json)。

按Supervisor第2章、idea-evaluator和本地Claude科学批判要求：普通强对照有效就接受，并放弃把这一修补包装成新算法。DUSt3R已有公共配对尺度约束；Scal3R/LASER也覆盖几何保持与尺度相关的相邻思路，见[原文机制排查](../work/S32_next_decision/review.md)。本轮没有复现这些论文或证明独立新颖性。

## 接手入口与下一步

- [生产协议](../work/S33_preparation/PROTOCOL_CANDIDATE.md)、[冻结合同](../work/S33_preparation/contract.json)、[源前审](../work/S33_independent_review/final_pre_review.json)、[实际运行回执](../work/S33_launch/receipt.json)。候选文档的“未执行”指其起草时间，当前状态以实际合同/回执为准。
- [主评分协议](../work/S33_scoring_preparation/protocol.md)、[冻结manifest](../work/S33_scoring_preparation/manifest.json)、[完整64行JSON](../results/S33_pair_scale_scoring/metrics.json)、[CSV](../results/S33_pair_scale_scoring/per_frame.csv)、[实际评分回执](../results/S33_pair_scale_scoring/receipt.json)。
- [S32前一轮完整对照](S32_RESULTS.md)、[16张真实照片与历史交付](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/S32_新片段三对照与真实照片_2026-09-07/先读我.md>)。

停止在这三个已见短窗继续调m0、焦距冻结、先验权重或步数。下一决策是回到真实old4→new4消费者：旧depth冻结与本轮全depth训练条件不同，不能直接声称同样有效；应沿原接口检验地图/可见性/选图的实际影响。下一项具体设计正在独立审阅，未启动新实验；完整VMem生成视频仍未执行，PhD深度/CCF A投稿质量尚未验收。
