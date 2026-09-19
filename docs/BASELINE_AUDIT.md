# VMem 基线审查与旧稿修正

审查日期：2026-09-05。基线固定于 `runjiali-rl/vmem@39291e4f272f6b4f270691d930926ab5930f942e`。此文中的实现结论针对该提交；没有验证模型权重的实际运行配置。

## 关键纠正

| 旧稿中的概括 | 源码证据 | 研究上应如何表述 |
|---|---|---|
| VMem 是 original always-write / 无条件累积估计几何 | `pointmap_to_surfels` 同时比较 confidence 阈值与深度 0.999 分位数；上游先运行 point-cloud cleaning | 比较对象必须写成“原版完整清理、过滤与合并策略”。另设关闭过滤的 always-write 作为消融，不能用它冒充原版 |
| 加入 provenance 是本研究独有贡献 | `surfel_to_timestep` 已存储并更新观测来源帧编号 | 需要证明的是额外的每来源可靠性、冲突判断或失效检测的价值；不能把来源 ID 本身称为新颖 |
| 读取只是均匀的 top-K 统计 | 实现按法向与视线夹角及深度加权，再分配帧数并按位姿距离选择 | 对照保留原版完整选择路径；额外 gate 不能通过改变上下文数量取得不公平优势 |
| merge 会融合/修正新旧几何 | 匹配时追加 timestep，既有 position / normal / radius 没有被该函数更新 | 将“已写入几何能否被纠正”作为可测试问题，但先确认其是否影响检索 |

相关固定源码：[写入过滤](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py#L832)、[合并](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py#L770)、[来源与构建流程](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py#L1019)、[读取打分](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py#L462)。

细节：代码实际使用深度 **0.999 分位数**，旁边注释写“95 percentile”，应以执行语句为准。默认 `conf_thresh: 1` 的存在不代表已完成可靠性校准：CUT3R 默认置信度模式为 `1 + exp(x)`，而后续清理又会降低部分点的置信度。必须实测完整路径后的分布，才能判断过滤力度。[默认配置](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/configs/inference/inference.yaml#L28)、[置信度变换](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/extern/CUT3R/src/dust3r/heads/postprocess.py#L142)、[默认模式](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/extern/CUT3R/src/dust3r/model.py#L100)。

上游 `prepare_output` 在返回点图和置信度前执行 `scene.clean_pointcloud()`；其实现会把位于其他视图观测表面前方且相对更低置信的点降权。因而“新增重投影一致性检查”也必须对照已有检查，不能只与完全没有清理的版本比较。[调用](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/extern/CUT3R/surfel_inference.py#L196)、[实现](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/extern/CUT3R/cloud_opt/dust3r_opt/base_opt.py#L581)。

## 本机可运行与尚未运行的部分

实际设备为 Apple M3 Max、64 GB 统一内存；用户已确认暂无远程 GPU。原版生成路径含显式 CUDA 调用，README 要求申请 Hugging Face 权重访问。64 GB 统一内存不等价于 64 GB CUDA 显存，构造函数允许 CPU 也不等于整个流程支持 CPU/MPS。[生成路径](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/utils/util.py#L698)、[权重说明](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/README.md)。

本轮仅从官方源文件抽取 Surfel、Octree、merge 和 renderer。AST 对比通过；原许可保留。**没有宣称 VMem 在本机端到端运行成功，也没有实测其所需显存。**

## 创新性边界：至少补上这些对照

| 工作 | 作者与年份 | 已验证的相关内容 | 对当前课题的约束 |
|---|---|---|---|
| VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory | Runjia Li, Philip Torr, Andrea Vedaldi, Tomas Jakab，2025 | 几何索引历史视图并检索生成上下文；源码含过滤和来源关联 | 研究增量不能只是 surfel、来源 ID 或 confidence threshold |
| ElasticFusion: Dense SLAM Without A Pose Graph | Thomas Whelan, Stefan Leutenegger, Renato F. Salas-Moreno, Ben Glocker, Andrew J. Davison，2015 | RGB-D surfel 建图并持续细化模型 | “可更新的 surfel memory”本身早已存在；区别应落在生成模型的检索与闭环后果 |
| Probabilistic Surfel Fusion for Dense LiDAR Mapping | Chanoh Park, Soohwan Kim, Peyman Moghadam, Clinton Fookes, Sridha Sridharan，2017 | 按测量不确定性关联与融合 surfel，使用贝叶斯过滤抑制地图噪声 | 不确定性融合不是新机制；它与生成世界模型的接口、误差传播及评测才可能形成差异 |

文献依据：[VMem 论文](https://arxiv.org/abs/2506.18903)、[ElasticFusion 官方项目](https://www.imperial.ac.uk/dyson-robotics-lab/projects/elasticfusion/)、[Probabilistic Surfel Fusion 会议页面（ICCV Workshops）](https://openaccess.thecvf.com/content_ICCV_2017_workshops/w35/html/Park_Probabilistic_Surfel_Fusion_ICCV_2017_paper.html)。本表用于检查机制是否已有，不是最新视频世界模型领域的完整综述。本轮没有重新核验旧调研中的全部引用，不继承其“全部已核验”的结论。

下一阶段建议保留的简单对照：原版完整策略、仅调 confidence 阈值、匹配写入数量的随机拒绝、简单均值/稳健位置更新、近期帧检索，以及待研究的来源可靠性策略。调阈值或融合的任何收益都不能先算成新方法贡献。
