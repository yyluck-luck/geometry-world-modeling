# S35：原生成循环的记录接线与人工检查

**已补齐五个准备模块，并实际通过新人工接线检查。没有加载真实模型，没有生成真实视频，也没有新增算法精度结果。** 本轮把 S20 的“记录工具已写、尚未接入循环”推进为“原控制流程已接入观察器，并用人工替身实际验证”。S34 的真实几何实验结果保持原样。

本轮由 root 与三名 agent 分工实现、审查与验证。主实现目录：[S35代码及证据](../work/S35_generation_integration/)；[运行前准备规则](../work/S35_generation_integration/preparation_protocol.md)。全部实际时间追加至[研究主账](../RESEARCH_LOG.md)。

## 为什么现在做这一步

上一轮 S34 表明，普通优化已带来大部分局部深度改善，额外尺度约束只有小幅收益，而且候选参考图未改变。因此没有把它包装成新方法，也没有继续对同一短窗调参。

下一项重要证据是：第一批真正生成的图片，是否作为参考进入第二批生成。S20 的旧回执明确为 `PASS_PREPARATION_MODULE_REVIEW_NOT_INTEGRATED`，且仅保存部分条件的指纹，缺少完整条件与返回值。这个待办无需先拿到模型权重，故本轮先补齐。[旧缺项回执](../work/S20_protocol_review/trace_completion_review.json)；[S34结论](S34_RESULTS.md)。

## 实际交付

| 模块 | 完成的功能 | 验证程度 |
|---|---|---|
| [resource_gate.py](../work/S35_generation_integration/resource_gate.py) | 所有组件、原配置、源码和审查绑定齐备后才允许加载；先检查全体文件，再读大权重 | 源审；当前草稿由外层启动器提前拒绝 |
| [runtime_factory.py](../work/S35_generation_integration/runtime_factory.py) | 离线调用原加载器，精确原文件路径映射，保留原数学和加载返回检查 | 仅源审，尚未实际加载四模型 |
| [integrate_original.py](../work/S35_generation_integration/integrate_original.py) | 原循环前后同步记录，保留原函数调用一次、输入原地变化与缓存关系 | 源 AST 还原检查及人工接线实际通过 |
| [archive_outputs.py](../work/S35_generation_integration/archive_outputs.py) | 保存完整噪声、条件、图像、latent、embedding、地图和原始返回，失败也保留前缀 | 新人工归档完整读回通过 |
| [launch_original.py](../work/S35_generation_integration/launch_original.py) | 单进程两批、分阶段计时、进程树内存与磁盘外控，禁止自动重试 | 源审、DRAFT拒绝实际通过；正向真实分支未执行 |

原始 VMem、CUT3R、S20 记录器及已冻结实验未修改。两处原 pipeline 方法删除新增观察节点后，与原 AST 完全一致；这验证原计算语句的保留，不能单独证明所有真实运行行为一致。

源码审查实际发现并修正了资源门的绑定缺口，以及启动器的计时缺口。第二批起点改用上次 trace 读取开始时刻，采样间隔改为连续内存/磁盘采样完成时点之差。旧源码和 `REVISION_REQUIRED` 回执保留，未把原版追认为通过。

## 实际人工检查结果

冻结时间 UTC **2026-09-06 23:09:46.032190**，精确合同 SHA `e206b03c0843c9dacba4f7ba0f194b6e49346488d5b0e12a8423ae5f987b9200`。CPU 1、120秒、采样 RSS 2 GiB 上限，现有 Python 与既有外控，无安装和网络请求。[冻结合同](../work/S35_generation_integration/artificial_wiring_frozen_v1.json)；[源码前审](../work/S35_generation_integration/artificial_wiring_pre_review.json)。

实际外控开始 UTC **23:09:57.553586**，结束 **23:10:00.664674**，即北京时间 **07:09:57–07:10:00**。耗时 **3.110794秒**，采样峰值 **443.33 MiB**，退出码 **0**。峰值为离散采样结果，不是对瞬时峰值的保证。[外控原回执](../work/S35_generation_integration/synthetic_execution_v1/receipt.json)；[人工检查原结果](../work/S35_generation_integration/synthetic_wiring_checks_v1/receipt.json)。

一次检查程序包含三类用途，成功和注入异常分别运行无观察与有观察对照。模型、几何和渲染为脚本内明确的人工替身；没有读取真实照片、GT、权重或旧预测数组。

| 检查 | 实际结果 | 能说明什么 |
|---|---|---|
| 无观察 vs 有观察 | 图像逐像素、完整缓存、相机、选中ID、调用次数、Python/NumPy/Torch随机数状态逐值一致；梯度和inference模式恢复 | 在这条人工路径中，记录器没有改变这些值 |
| 原两批控制流程 | 人工历史1→5→9；第二批实际选ID `[0,2,4,1]`；首批7行目标编码、第二批4行，8个输出槽均完整保留 | 原槽位、填充、缓存及选图接线被执行；不是原模型效果 |
| 默认NMS状态 | 原len5分支产生10个距离，索引5对应阈值0.04363296926021576；持久阈值与选中ID保存一致 | 阈值与选择记录来自实际人工路径，未补造默认状态 |
| 成功归档 | 39条trace事件；296份归档载荷完成检查；两批均完成 | 此人工归档完整；不能据此判视频质量 |
| 第二批人工采样异常 | 原异常对象保留、两套钩子恢复；26条trace事件，204份归档载荷；首批历史5仍保留、第二批标失败 | 失败前缀可追查，不把“关闭记录”误当两批成功 |
| 工厂调用前资源拒绝 | gate调用1次，trace/archive/runtime三个factory均0次 | 人工资源回调先于构造；不是正向资源验收 |

每条成功路径（plain与observed分别）的实际调用：人工采样2次、人工采样步4次、人工主模型4次、人工VAE编码1次/解码2次、人工CLIP3次、人工几何2次、人工渲染1次。每条失败路径在第二次人工采样进入后抛错，故解码和几何均只完成1次。这些次数不是四条路径合计。**这里不是原50步采样、400步几何优化或原渲染器测试。** 原 AST 的 `do_sample`、控制流程、相机条件处理、NMS和导航在替身环境中执行；解码输出只有4×4，不能当作576×576生成图。

另外实际核到一个原行为：首批返回的是历史列表本身，当时5张，第二批追加后同一对象变成9张。同步归档正确保留当时5张；最终规范帧应取 `pipeline.pil_frames` 的9张，而 `Navigator.frames` 含重复初图，共10张。这是源码及人工路径证据，未为此改动原算法。

## 实际启动保护与未完成的部分

UTC **23:06:58.264751–23:06:58.265133** 实际调用启动器，输入当前明确为 DRAFT 的资源文件。它按预期退出码2，状态 `NOT_READY_BEFORE_SCIENTIFIC_IMPORT`，worker未创建，科学模块导入0次。错误原因是“必须使用冻结的真实运行文件”，**只覆盖草稿拒绝路径，未执行完整资源门或正向真实运行**。[启动拒绝回执](../work/S35_generation_integration/draft_refusal_execution/receipt.json)；[当前不可执行资源草稿](../work/S35_generation_integration/real_run_draft_not_ready.json)。

原 VMem 主权重、原指定 VAE、完整原 CLIP 尚未在项目中验收，VAE的实际revision/config/weight身份仍未知；已验证的 CUT3R 保留。资源判断来自 S34 的有界官方查询及本轮限定文件元数据检查，不声称搜遍全电脑，也不把TLS失败当新的HTTP拒绝。[资源来源与时点](../work/S34_resource_refresh/report.md)。

真实运行仍需先补齐原组件与来源，冻结实际输入图和完整文件身份，然后在新目录执行既定原1→5→9两批协议。建议CPU8/FP32、每批1800秒、总3600秒、45GiB采样RSS是未验证预算；没有在缺权重时偷偷换模型、缩减配置或造缓存。正向资源门、四模型加载、原50步生成、原400步几何、真实第二批缓存消费、视频评分及跨场景机制验证均尚未完成。

## 独立核验与科研流程

源码前审分别保存于[集成审查](../work/S35_generation_integration/integration_source_pre_review.json)、[启动器审查](../work/S35_generation_integration/launcher_source_pre_review.json)、[人工检查前审](../work/S35_generation_integration/artificial_wiring_pre_review.json)。另一作者已于 UTC **23:14:44.039792–23:14:44.467441** 独立读回新落盘证据，通过完整两条事件链、500份归档载荷字节、133次trace原始载荷引用、时间及源码绑定、两批/失败前缀、保存NMS数值和实际计数检查。[独立读回回执](../work/S35_generation_integration/executed_results_review.json)。

这次独立核查没有重跑测试或模型。运行时的原对象身份、plain/observed全部数组与随机数相等、钩子和计算模式恢复，以及PNG解码像素相等，由原检查程序的实际断言支持；另一作者没有再次执行这些内存断言。文件哈希与保存事件复核也不是独立数学复现或视频质量评分。

Supervisor handbook 2.2 用于基线优先及反证后转向；idea-evaluator维持普通尺度机制的新颖性否决；Claude本地科学批判用于混杂、失败保存和证据分层，未调用Claude模型或CLI。本轮使用现有Python、rg、AST、完整文件归档与多agent审查；没有新文献事实需要时不重复网络检索。最近实际流程检查UTC23:04:20.656538，间隔26.799135分钟；定时任务原误配20分钟，本轮已经在应用内改为30分钟并回读确认。

**S35完成的是基线准备和接口验证；新方法、完整生成和PhD／CCF A质量目标仍未完成。** 下一位AI先读主记忆与最新主账，不重跑本轮已成功的人工检查，不将目录中的人工PNG标为真实照片。
