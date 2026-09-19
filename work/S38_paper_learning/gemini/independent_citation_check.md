# Gemini 首答的三项引用核验

审阅记录 UTC：2026-09-07T03:29:47.559Z；北京时间为 UTC+8。作者 `/root/s14_feature_extractor`。范围仅为根任务指出的三处文献身份错误；没有全文审查 Gemini 原答，也没有复核其全部实验、消融或建议。

**结论：SceneScape 的 venue 应为 NeurIPS 2023；StreamingT2V 应为 CVPR 2025；两篇 LucidDreamer 的完整题名、作者和方法不同，不能互套引用。** 前两项由本 agent 直接核正式来源返回内容，第三项复核根任务本轮已取得的作者页/CVF 正文，并明确保留这一区别。

## 1. SceneScape

- 完整题名：**SceneScape: Text-Driven Consistent Scene Generation**
- 作者：**Rafail Fridman, Amit Abecasis, Yoni Kasten, Tali Dekel**
- 正式 venue：**Advances in Neural Information Processing Systems 36 (NeurIPS 2023), Main Conference Track**
- Gemini 待核说法：CVPR 2023。
- 核验：**错误；应改为 NeurIPS 2023。** [NeurIPS 正式论文集条目](https://proceedings.neurips.cc/paper_files/paper/2023/hash/7d62a85ebfed2f680eb5544beae93191-Abstract-Conference.html) 的题名、作者及会议字段直接支持该结论。本轮使用检索工具返回的该正式页面正文，没有下载 PDF。

## 2. StreamingT2V

- 完整题名：**StreamingT2V: Consistent, Dynamic, and Extendable Long Video Generation from Text**
- 作者：**Roberto Henschel, Levon Khachatryan, Hayk Poghosyan, Daniil Hayrapetyan, Vahram Tadevosyan, Zhangyang Wang, Shant Navasardyan, Humphrey Shi**
- 正式 venue：**Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2025, pp. 2568–2577**
- Gemini 待核说法：CVPR 2024。
- 核验：**错误；应改为 CVPR 2025。** [CVF 正式条目](https://openaccess.thecvf.com/content/CVPR2025/html/Henschel_StreamingT2V_Consistent_Dynamic_and_Extendable_Long_Video_Generation_from_Text_CVPR_2025_paper.html) 的作者行和 BibTeX 同时列明 2025。本 agent 还读取 agent A 已保存 HTML 的相应字段，二者一致；未重新下载、读取其 PDF。

本轮仅修正正式发表年份，没有据此推断预印本年份、方法强弱或实验是否可迁移。

## 3. 两篇 LucidDreamer 必须分别引用

| 字段 | 场景生成论文 | Interval Score Matching 论文 |
|---|---|---|
| 完整题名 | **LucidDreamer: Domain-free Generation of 3D Gaussian Splatting Scenes** | **LucidDreamer: Towards High-Fidelity Text-to-3D Generation via Interval Score Matching** |
| 作者 | **Jaeyoung Chung, Suyoung Lee, Hyeongjin Nam, Jaerin Lee, Kyoung Mu Lee** | **Yixun Liang, Xin Yang, Jiantao Lin, Haodong Li, Xiaogang Xu, Yingcong Chen** |
| venue | 作者页报告 **IEEE Transactions on Visualization and Computer Graphics (TVCG), 2025** | CVF 正式条目 **CVPR 2024, pp. 6517–6526** |
| 用于区分的机制名 | 作者页的 **Dreaming + Alignment** | CVF 摘要中的 **Interval Score Matching (ISM)** |
| 来源 | [作者页](https://luciddreamer-cvlab.github.io/)；[arXiv 2311.13384](https://arxiv.org/abs/2311.13384) | [CVF 正式条目](https://openaccess.thecvf.com/content/CVPR2024/html/Liang_LucidDreamer_Towards_High-Fidelity_Text-to-3D_Generation_via_Interval_Score_Matching_CVPR_2024_paper.html) |

Gemini 将 arXiv 2311.13384 的 Domain-free 论文标成 CVPR 2024，并将 ISM 归入该论文，混合了两组作者的不同工作。**应拆为两条引用；不能借同一个 LucidDreamer 名字互套 venue、方法或实验。**

本 agent 对 arXiv 的一次 open 只得到完整题名和页面元信息；对上述 Liang CVF URL 的一次 open 返回工具 `Internal Error`，未取得正文或 HTTP 状态。因此没有把这次失败冒称读取成功。之后根任务提供了其本轮实际取得的两份公开正文供本 agent 审阅：作者页 L0/L2/L5/L20–21/L59 分别给出题名、TVCG 2025、五位作者、Dreaming/Alignment、arXiv 2311.13384；CVF 正文给出另一完整题名、六位作者、CVPR 2024/页码及 ISM。上表第三项的完整身份核对基于这份团队内来源交接，**不是本 agent 再次独立联网取得**。TVCG 字段目前由论文作者页支持；本轮未另查 IEEE Xplore 正式期刊条目或 DOI。

## 范围、请求和科研决策边界

本轮保守计数 **4 个网页工具操作：2 个限定正式来源的检索查询 + 2 次小页面 open**，没有在失败后新增来源请求。检索自动返回的其他论文和 PDF 索引未继续打开或用于本文结论。网页工具未暴露各请求 HTTP 状态及精确请求开始/结束时点，故不编造 HTTP 200 或秒级访问时间；本报告时间是实际审阅落盘时间。

新增 PDF 下载、权重下载、模型/科学实验均为 0。已保存的 agent A HTML 只读；Gemini prompt/preparation、原答和科研协议没有修改。前两项是本 agent 对正式来源的直接核对，第三项是本 agent 对 root 已获取原始正文的独立审阅；都不是外部独立复现。

这三处修正足以说明 Gemini 引用需要逐条检查，**不证明其未检查项正确，也不等于其全部内容错误**。Gemini 对话是待核 AI 意见；本核验不采纳其终止研究、替换基线或更改实验的命令。实验因果判断与原答保存由根任务单独处理。完整出处、来源交接和失败记录见 [receipt.json](receipt.json)。
