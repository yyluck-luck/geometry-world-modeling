# S14 新真实场景身份与评价接口核查

状态：**候选核查完成；没有新增合格的独立校准/测试组，没有执行新数据实验。** 本文接续 S14 场景计划，保留原计划。实际访问时间、成功和失败、源码身份见 [receipt.json](../work/S14_new_scene_identity/receipt.json)。

本轮得到一个明确的排除和一个具体后备：原版 **7-Scenes 不能直接进入现有 RGB 像素支持评分**，因为官方确认 RGB 与深度未联合标定；**Bonn 的 `rgbd_bonn_static_close_far`** 提供已配准深度、相机参数与外部动捕，是下一项更合适的接口核查对象。TUM fr3 的格式可适配，但“fr3 是新物理房间”仍没有核实。不得把这些结论升级为新方法有效。

## 本轮怎样应用技能

实际读了 Supervisor 的 [benchmark-paper-template](</Users/rocket/.codex/skills/benchmark-paper-template/SKILL.md>) 及 [construction-pipeline](</Users/rocket/.codex/skills/benchmark-paper-template/references/construction-pipeline.md>)，应用的是来源选择、许可、质量门与划分的明确输入输出要求；本文不是完整 benchmark 论文，不机械套用论文图表模板。实际读了本地 Claude [scientific-critical-thinking](</Users/rocket/.claude/skills/sci-scientific-critical-thinking/SKILL.md>)，应用独立统计单位、测量可靠性、证据与推断分级。不调用 Claude 模型或 CLI，不联系作者。

本轮输入只有公开说明、原论文文本、许可、官方训练配置和本地评价源码。没有查看新照片/预览，没有读取新 RGB/depth/GT 数组，没有预测或评分。保存 HTML/PDF/RTF 属于文献取证。网页工具曾请求一个 Bonn ZIP 链接并返回“不支持 application/zip”，没有保存或解码数据包；这次多余的内容请求保留在 `web_bonn2.json`，后续只从 HTML 取 URL，不点击数据链接。

## 1. TUM `freiburg3_long_office_household`

| 项目 | 已核内容与判断 |
|---|---|
| 物理组 | `TUM-FR3-UNRESOLVED`。下载页描述办公布置、手持 Asus Xtion 及轨迹；未给建筑/房间 ID，也未声明和 fr1 或 fr2 所在房间不同。搜索 `freiburg3 + industrial hall/room/recorded` 没有解决这一点。不同传感器、年份或布置不足以证明独立。 |
| 与已有两个组的关系 | **UNKNOWN**，不声称相同，也不声称不同。继续隔离，不能给校准/测试新增一个独立 n。 |
| RGB/depth | 官方格式说明深度已预配准到 RGB；PNG 深度除以 5000 得米，0 无效。fr3 的 RGB/IR 已去畸变，RGB 内参为 `(535.4,539.2,320.1,247.6)`，畸变为零，深度缩放已处理。 |
| GT | 官方基准说明为外部动捕轨迹；实际文件的时间同步、有效范围、姿态方向尚未解码核验。 |
| 公开入口 | [序列说明及下载](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/download#freiburg3_long_office_household)；具体包 URL 在所保存 HTML 中，未请求包。 |
| 使用条件 | 官方当前声明数据默认 CC BY 4.0，包内例外须保留核查；未取得具体包，不能替包内许可作保证。 |
| 当前决定 | 适合另立“未知房间关系的新轨迹诊断”；不满足本任务的新物理场景留出标准。 |

以上接口依据为[官方格式](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats)，许可与动捕依据为[官方基准页](https://cvg.cit.tum.de/data/datasets/rgbd-dataset)。本轮不因 fr3 K 与原 ROS 默认 K 不同而回改旧 TUM 实验；新传感器要在新合同固定 K。

## 2. Microsoft 7-Scenes：以 `Chess` 为具体候选

| 项目 | 已核内容与判断 |
|---|---|
| 物理组 | `7SCENES-CHESS-ROOM-UNKNOWN`；原论文 §4.1/Fig.3 说明七个命名场景、每场景多序列，但没有建筑地址/房间 ID 或空间共享映射。保守整套隔离；不能把七个名字认证成七个房间。 |
| 与 TUM 的关系 | 论文作者机构为 Microsoft Research Cambridge，**机构地址不是采集地点证明**。跨数据集大概率不同也不是已核实房间映射；本轮保持未证实。 |
| 评价接口 | 原始 RGB/depth 未标定且无校准参数；默认深度内参不能替代 RGB 内参和跨相机外参。因此不能直接沿用现有同像素对应。 |
| 深度/位姿 | 深度单位毫米，无效 65535；位姿文件为 camera-to-world 4×4，来自 KinectFusion/ICP 的 frame-to-model 对齐。不是 TUM 动捕，也不是独立于 RGB-D 重建的物理真值。 |
| 公开入口 | [Microsoft 官方页面](https://www.microsoft.com/en-us/research/project/rgb-d-dataset-7-scenes/)列出 Chess 等直接下载，无个人信息表单。没有请求 7-Scenes 数据 ZIP。 |
| 使用条件 | 官方 [MSR-LA 许可全文](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/7-scenes-msr-la-dataset-7-scenes.rtf) 已读取，允许非商业学术/教学/个人试验；分发须沿原条件并保留声明。 |
| 当前决定 | **排除原版数据直接接入当前像素支持评分**。如改做姿态重定位或使用另有可验证标定的版本，须另立测量合同。 |

原论文从 [CVF 官方 PDF](https://openaccess.thecvf.com/content_cvpr_2013/papers/Shotton_Scene_Coordinate_Regression_2013_CVPR_paper.pdf) 成功取得，重点读 §4.1–4.2；不冒称全文科学审读。许可 RTF 85355 字节，经 macOS `textutil` 转文后全文读完；其中同时存在允许衍生、限制修改数据的表述。本文只记录原条款，不把“允许学术使用”扩写为任意改写或公开重分发数据的授权；即使许可处理完，配准缺口仍独立存在。

## 3. 下一项具体候选：Bonn `rgbd_bonn_static_close_far`

选择原因是原始数据发布者明确提供两条静态序列，且此包标称 1.0 GB，比 `rgbd_bonn_static` 的 5.8 GB 更接近原 2 GB 下载预算。这是**根据元数据与预算选择**，没有看新模型分数或照片。[官方页面](https://www.ipb.uni-bonn.de/data/rgbd-dynamic-dataset/)

| 项目 | 已核内容与剩余缺口 |
|---|---|
| 物理归组 | 暂记 `BONN-DYNAMIC-ENVIRONMENT-UNRESOLVED`，两条静态和 24 条动态序列保守合组，不能算 26 个房间。原论文使用同一静态环境的激光真值模型；没有房间地址。 |
| 与 TUM 是否不同 | 作者明确区分 TUM 与自行新采集数据，Bonn 机构和采集设备也有不同；这是支持不同来源的证据，仍**不是直接房间 ID 证据**。若研究合同只要求不同采集数据集，可合格；若坚持已证实不同物理房间，尚未完全过门。 |
| RGB/depth | 官方明确深度已配准至对应 RGB；TUM 文件格式；K=`(542.822841,542.576870,315.593520,237.756098)`，畸变=`(0.039903,-0.099343,-0.000730,-0.000144,0)`。 |
| 传感器/GT | 原论文 §IV-B：ASUS Xtion Pro LIVE 与 Optitrack Prime 13；另有 Leica BLK360 静态激光点云。网页说明 RGB-D 与激光模型坐标对齐涉及 `T_m`、`T_ROS` 和首帧 pose；不能把这个激光转换链直接当 RGB-D 光学 c2w。 |
| 入口/包大小 | [官方候选下载地址](https://www.ipb.uni-bonn.de/html/projects/rgbd_dynamic2019/rgbd_bonn_static_close_far.zip)，标称 1.0 GB；没有测得完整包实际字节或哈希。 |
| 公开使用条件 | 发布页邀请科研使用并给引用要求，但当前保存页没有独立数据许可文本。ReFusion 代码仓库有 CC BY-NC-SA 3.0，**代码许可不能自动认证外链数据许可**；二手论文把它写成数据许可，本轮不采用该推断。 |
| 当前决定 | 保留为唯一下一项具体候选；先做不读照片/评分的包清单/许可/标定元数据核查合同，由根任务决定是否允许有界元数据获取。没有在本轮下载整包。 |

本轮成功读 [ReFusion 原论文 arXiv PDF](https://arxiv.org/pdf/1905.02082) 的采集与评价部分；不是仅从摘要推断。Bonn 站 PDF 直取第一次 SSL EOF 失败，保留失败，然后从官方页面链接的 arXiv 成功获取。没有把 arXiv 版本和会议 PDF 当作字节相同。

接口剩余工作很具体：本地 `src/tum_rgbd.py` 和 `src/rgbd_metrics.py` 使用针孔投影，原像素规则且不做额外去畸变。Bonn 有非零畸变，因此仅改 K 还不能称“严格沿用经验证评价”。须先冻结畸变感知射线/投影或明确近似误差的接口协议，再用与算法调参分离的适配数据检查。两条静态序列必须共同占一个组，不拆成独立校准/测试。激光点云不是当前必要输入，不下载数 GB 点云来凑工具使用。

## 4. CUT3R 训练接触核查

本轮从 CUT3R 官方 GitHub 的项目固定 commit `8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf` 重新获取 `stage1.yaml` 至 `stage4.yaml` 和 `docs/train.md`，与已有 S8 快照逐字节比较：四个配置均相同。解析训练数据别名、类名，并搜索 TUM/7scenes/SevenScenes/Bonn；四份都没有这些名称。[官方训练说明](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/docs/train.md)

这个阴性检索不能认证权重未见这些照片。官方训练说明明确配置只是代表性流程，不能完整复原迭代训练历史；已存原论文 §3.4 还说明编码器继承 DUSt3R 权重。官方 README 把 TUM-dynamics 和 7scenes 列为评价集，已存论文称 Bonn 等深度评价集排除于训练；应逐项引用该范围，不能泛化为所有继承预训练、具体发布权重与图像重叠均已彻查。[官方 README](https://github.com/CUT3R/CUT3R)

因此三项候选登记为：`listed_in_examined_cut3r_training_configs=false`、`complete_checkpoint_training_exposure=UNKNOWN`。新的本项目留出组、公开基准的训练/测试序列、模型预训练未接触，是三个不同字段。机器检查在 [cut3r_config_check.json](../work/S14_new_scene_identity/cut3r_config_check.json)。

## 5. 接手动作与停止条件

1. 根任务可先将 Bonn 候选列入**待适配来源**，而非已合格新测试房间；要获取元数据，先冻结 URL、范围、字节预算、只取清单/README/许可/标定/pose格式描述而不解码图像和GT的边界。整包若不支持有界元数据提取，不在本合同悄悄下载。
2. 房间直接证据或可验证采集位置仍缺。如果只能确认不同来源，则把将来结果命名为“新来源诊断”，不要改写成已证实房间独立的风险校准。坚持房间标准时继续保留未通过状态。
3. 7-Scenes 原版接口排除已充分；不再重复查同一页面期待获得不存在的标定。TUM fr3 身份如无新原始证据，也不重复无产出的搜索。
4. 任何未来运行都要独立冻结、记录失败、预测与GT隔离并独立复核。当前新增合格独立校准/测试组数仍为 **0**；当前候选表不是数据采购或实验完成。

本轮没有改变算法，没有宣称创新成立，没有新真实实验。它完成了来源筛选的具体接口排除、原始许可核查、训练身份核查，并把下一项候选缩到明确的文件与缺口。
