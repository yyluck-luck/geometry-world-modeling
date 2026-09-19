# DynaBench 数据可行性：目前不能据此启动分原因验证

实际核验：2026-09-10 22:08:04–22:09:33 UTC（北京时间次日 06:08–06:09）。本批仅查官方论文、项目入口、README、目录与许可说明；未下载数据集、读取拟用图像/标签或运行模型。S86 四臂验收优先，不新增动态实验。

**结论：DynaBench 是相关的真实采集动态定位基准，但“是否足以初步区分真实变化与共同位姿误差”仍为 UNKNOWN。** 当前没有核到可取用的数据 manifest/schema，更未核到独立相机参考和变化/遮挡事件标注。不能把论文的定位标签与 posed RGB-D 自动升级为这些条件；也不能因入口没找到就声称作者没有发布数据。

## 已确认与缺项

以下论文事实定位于 [DynaMem v2 §4.1、§4.3](https://arxiv.org/html/2411.04999v2)（v2：2025-05-29；本轮复核浏览器行 151–170）。

| 必要信息 | 本轮可确认 | 仍不能确认 |
|---|---|---|
| 真实 RGB-D 或模拟 | §4.3 描述三个机器人场景的运行传感数据，另六场景用 iPhone Pro 拍摄 posed RGB-D；三轮人工移动物体/障碍。这里“simulate this process”指用手机模仿采集过程，不是已证明使用渲染图。§4.1 机器人相机为 RealSense D435。 | 各文件的传感器型号/深度生成方式、单位、RGB-depth 对齐、同步误差、有效深度标志及每场景文件身份；未核实际包。 |
| 时间戳与严格前缀 | §4.3 的查询 t 明确只使用 timestamp <t 的输入；查询标签包含时间。 | schema 字段、时基/单位、同时间戳顺序、全局或分轮时钟、缺帧；尚不能写真实 loader。还要核提供的 pose 是否由未来帧或离线全程 SLAM 优化得到；仅筛 RGB 时间戳不自动避免未来几何信息。 |
| 相机来源与独立真值 | 方法使用 posed RGB-D。当前官方运行文档要求在机器人启动 SLAM，足以说明运行系统依赖估计过程。 | DynaBench 打包 pose 的确切来源、坐标约定、尺度、精度及是否逐时可用；手机是否 ARKit、机器人数据是否另有外部定位均 UNKNOWN。SLAM 输出不是外部真值。 |
| 对象位置或“不存在” | 论文说明人工标注 q、三维位置 X、成功半径 ε、时间 t；负查询包含从未观察到和先见后移除，两者都应返回 not found。 | 字段编码与缺失约定；X 如何获得、是否借用了同一估计相机；两种负查询是否有可区分类型字段。查询时的位置/缺失标签不等于真实变化时刻或对象连续身份轨迹。 |
| 遮挡与重访事件 | 论文描述分轮移动及多场景。 | 未见遮挡、可见性、最后可见/首次重见、事件 ID、运动区间或独立 episode 划分的 schema 说明。不能把 not found 当“被遮挡”，也不能把一轮或每个 query 直接算独立重访样本。 |
| 下载体量与许可 | 当前官方项目/作者 Code 链接均落到 stretch_ai 的 DynaMem 运行文档。 | 本轮未定位 DynaBench 专用下载 URL、总字节/分片/校验和或数据许可。代码 Apache/MIT 与网站内容许可不等于数据集许可。不能把代码文档的 KB 数或 Docker 体积当数据体量。 |

其中前两行的“真实采集”和严格 <t 是论文层证据；并未做文件级核验。对于完整原 proposal，RGB-D 作为模型输入是另一种模态设定；若继续仅用 RGB 预测几何，真实深度只能按新设计作为共同评分参考，不能单独给候选。

## 官方入口实际查到了什么

1. [官方项目页](https://dynamem.github.io/) 与 [作者发表页](https://www.lerrelpinto.com/publication/dynamem/) 的 Code 均指向 [stretch_ai/docs/dynamem.md](https://github.com/hello-robot/stretch_ai/blob/main/docs/dynamem.md)。实读导航/SLAM/保存读取记忆等段；其中语义记忆保存为 pickle，可加载旧运行状态，但没有 DynaBench schema 或下载说明。不能把该机器人运行接口当作论文离线基准 loader。
2. [仓库 README](https://github.com/hello-robot/stretch_ai/blob/main/README.md) 实读正文及链接；[docs 目录](https://github.com/hello-robot/stretch_ai/tree/main/docs) 查看文件名；[data/scenes 目录](https://github.com/hello-robot/stretch_ai/tree/main/data/scenes) 当次仅列 default_scene.xml、empty_scene.xml、stretch.xml，未打开其内容。它们不能证明是 DynaBench 的真实序列。README 的通用使用示例文字已随正文读取；没有读取拟用测试图像/对象查询标签、原始 pickle 或标注文件。
3. README 说明代码主体 Apache 2.0、部分 Meta 来源 MIT；[LICENSE](https://github.com/hello-robot/stretch_ai/blob/main/LICENSE) 仅核标题为 Apache 2.0 及版权归属。这只确认代码说明，数据许可仍 UNKNOWN。
4. 为查文件名而发起一次官方 GitHub recursive tree 元数据请求，22:09:01.363743–22:09:01.789379 UTC 返回 curl 35 / TLS 失败、0 字节，回执保存在 dynamic_data_source_01/TREE_RECEIPT.json。随后 web 对同一 API 地址的读取返回 non-retryable safe-open 错误，未继续请求该端点。只查到了上述普通网页目录，**没有完成全仓库递归核查**。这些失败只限制审读范围，不是否证数据存在。

仓库页面为访问时 main 展示，完整 commit 未取得；不冒充版本锁定。实际浏览范围：项目页文本 0–62；作者页 4–18；DynaMem 文档正文 196–505（重点 268–288、366–376）；README 194–323；docs 最后一次解析的文件名 187–215；data/scenes 224–247；LICENSE 标题 594–600、版权 891–899。行号依浏览器解析变化，路径/章节为主定位。没有为了获取 commit 再次拉仓库。

英文查询仅用于定位官方入口：“DynaBench DynaMem dataset download github peiqi official”、“site:github.com/hello-robot/stretch_ai DynaBench dataset”、“site:dynamem.github.io DynaBench data”。结果中的 PDE 动力系统、NLP 等同名 DynaBench 全部排除，未采用第三方教程；一个初始 web click 因引用格式无效，随后使用已返回页面引用成功取得官方链接。

## 最小缺项与下一决策

只需一份作者维护的非答案说明/manifest 能回答以下三组问题，才值得下一次文件级可行性检查，不必先搬整个数据集：

- **可取用与可前缀化：** 数据 URL、分场景字节/许可；RGB、depth、K、pose、采集时间的字段/单位/匹配规则，以及 pose 的生成时间和是否用了未来观测。
- **可区分两种原因：** 独立于待评几何系统的相机参考来源；对象真实变化及遮挡/可见状态是否单独标注。若只有查询位置标签，只能先评“动态定位表现”，不能归因于相机误差或真实变化。
- **可独立划分：** 场景/对象身份/轮次或事件 ID 与时间区间，能否留出未见场景的完整重访事件；不把同场景多个查询或像素当独立场景。

若没有外部相机参考但有合法前缀，可在未来另立“对已知人工位姿扰动的稳健性”测试；它衡量人工扰动反应，不能证明辨出了自然相机误差。当前也未达到文件级执行准备，不启动此替代实验。本批停止在明确 UNKNOWN；由 root 在现有四臂验收后按用户既有授权与新的官方证据决定后续，不增加用户审批关卡。

同时已按 root 指示修正 LONG_HORIZON_MEMORY_CANDIDATE.md 的范围句为“本批仅作设计，不启动；未来由 root 按已有用户授权和证据决定”，没有改变科学候选、近邻判断或本轮实验。
