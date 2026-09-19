# S8：CUT3R检查点训练数据重叠审查

结论：**不能声称当前CUT3R 224 linear中间检查点确定没有在训练中见过TUM、freiburg1_xyz或freiburg2_desk。** 本次没有发现这两条序列被用于训练的直接证据；同样没有找到足以证明它们被完整排除的检查点级训练清单。S8仍可按冻结协议作为本研究未使用过的新场景验证，但“对本研究是新场景”不能写成“对预训练模型也是未见场景”。

首次检索批次实际时钟：2026-09-06 03:14:12（Asia/Shanghai）。来源文本归档完成于03:16:46；最终记录时点见同名JSON和研究日志。仅检查原始论文文字、官方代码及本地检查点的小型元数据；没有读取S8图片或实验输出，没有加载模型、重新下载权重/数据或修改主记忆。

## 四层证据应分别理解

| 证据层 | 已核实 | 不能据此推出 |
|---|---|---|
| 论文总体训练数据 | 作者写使用32个数据集；附录A表6没有TUM RGB-D条目 | 具体公开224检查点和全部继承预训练都无TUM重叠 |
| 论文和仓库评估 | TUM-dynamics被列为相机姿态评估数据；官方评估脚本默认使用512最终检查点 | fr1_xyz/fr2_desk必然是训练排除集，或224检查点沿用完全相同的评估/训练划分 |
| 固定提交公开配置 | 六份配置都没有TUM/freiburg训练条目；部分数据集写`split='train'`，另一些写`split=None` | 配置列出了这个权重实际看过的全部文件；`split='train'`也不等于已拿到场景名单 |
| 我们实际使用的224权重 | 官方明确标为中间检查点；本地小型元数据只找到模型结构，没有训练数据集/划分或祖先权重身份 | 文件名、内部stage名称或推理代码提交能够重建实际训练历史 |

论文依据是作者原始[arXiv v1 §3.4、§4.2、附录A](https://arxiv.org/html/2501.12387v1)。本次未把512最终模型的总体实验设置直接赋给224中间检查点。官网[项目页](https://cut3r.github.io/)指向该论文及官方仓库。

## 公开配置为什么不足以证明无重叠

固定提交的[官方训练说明](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/docs/train.md)明确解释：实际训练在不同配置间迭代，完整过程难以发布，公开配置是有代表性的方案。这是作者对来源完整性的直接限定，而非本审查自行猜测。

[linear_224_fixed_16.yaml](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/config/linear_224_fixed_16.yaml)把`cut3r_224_linear_4.pth`作为`pretrained`输入，是从已发布权重继续微调的起点，不是生成这份权重的原始训练回执。其活动混合项为26个加载器条目，不能当作实际权重历史的完整训练集。其他stage配置也只是该文档限定下的代表方案；例如公开stage1写`pretrained: null`，而论文总体描述使用DUSt3R编码器初始化，不能自行补齐两者的历史对应关系。

官方[README检查点表](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/README.md#download-checkpoints)将224 linear标为中间检查点，表内训练视图数为16。因此文件名末尾`_4`也不能单独被用来认定实际训练长度。固定提交[姿态评估脚本](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/eval/relpose/run.sh)指向512最终权重；[评估元数据](https://github.com/CUT3R/CUT3R/blob/8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf/eval/relpose/metadata.py)的TUM部分没有列出完整序列名单。

也需避免关键词误判：ScanNet++网址中的`in.tum.de`表示机构域名；SmartPortraits预处理中的`convert_to_TUM`及轨迹读写函数表示位姿文件格式。它们都不是TUM RGB-D被用作训练数据的证据。

## 继承预训练还存在明确来源缺口

CUT3R论文§3.4说明图像编码器用DUSt3R预训练权重初始化，但本次未找到将当前224权重唯一对应到某份祖先权重哈希的记录。[CUT3R原论文](https://arxiv.org/html/2501.12387v1#S3.SS4)

向上只追查了一层：DUSt3R官方[Our Hyperparameters](https://github.com/naver/dust3r#our-hyperparameters)给出的实际训练命令含`InternalUnreleasedDataset`，并引用CroCo V2初始化；其数据准备说明还限定，发布的配对列表并不严格等同实际训练配对。本次没有该未公开数据的场景名单，也没有完成当前CUT3R检查点到每个祖先检查点的对应核实。这些是**无法证明无重叠的原因**，不是“已经证明含有TUM”的证据。

## 当前检查点自身能提供什么

本地实际文件为`data/cut3r/cut3r_224_linear_4.pth`，2,994,205,002字节。完整SHA256沿用此前已验证记录：`7a7d83e47f822e040980c8f5aff4c15aa94366d469d3ceae51fa30cc2f62327d`，本次未重算整份权重哈希。

本次只通过ZIP读取`checkpoint-stage3_latest_latest/data.pkl`，并用`pickletools.genops`做静态操作码检查，未反序列化pickle或读取张量存储。该成员203,481字节，当前重新计算SHA256为`acfc763f4d5a83d3bfe1e0451305266cf0e5f3014dfd19d7ca4e59856efede12`。共检查3377个字符串操作码；未发现`train_dataset`、`test_dataset`、`pretrained`、`resume`、`num_views`、`TUM`或两条序列名。模型配置字符串含224/linear及`freeze='encoder_and_head'`，但没有训练场景名单。

该结果严格表示“检查过的元数据没有提供这些信息”，不能从字符串缺失反推无训练接触。ZIP内部`stage3`名称也不能直接对应当前仓库的stage3配置，因为该公开配置是512 DPT。完整静态检查记录见[元数据证据](s8_model_overlap_sources/checkpoint_static_metadata.json)。

## 建议使用的结论措辞

“我们在本研究此前未使用的TUM fr2/desk场景上，按运行前冻结的协议检验记忆机制。CUT3R论文及所核对的公开代表性训练配置未列出TUM RGB-D，但具体224中间检查点及其继承预训练缺少完整场景级来源，因此其对本序列的训练接触状态未知。”

不应写“确定训练未见”“零训练污染”“严格跨训练分布泛化”，也不应反过来写“已发现训练泄漏”。要升级为检查点级未见结论，需要作者针对该权重和这两条序列的明确来源声明，或可核对的完整训练/预训练场景名单及祖先检查点标识。

## 审查范围与复核入口

固定代码提交经本机`/usr/bin/git`核实为`8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf`，已跟踪文件没有修改；仅存在原有未跟踪的`local_readiness/`。13份官方源码/说明、原始arXiv HTML和DUSt3R README文字快照已归档到`docs/s8_model_overlap_sources/`，每份来源链接、字节数和SHA256在[S8_MODEL_DATA_OVERLAP_REVIEW.json](S8_MODEL_DATA_OVERLAP_REVIEW.json)。缺少于稀疏工作树的说明通过固定提交的Git对象读取，不改变工作树文件。

检索遇到的限制也已保留：系统默认旧Git不支持worktreeconfig，改用已安装的新Git；误探arXiv v3返回404后以实际存在的v1为准；CVF页面及PDF访问返回403。因此本报告声称读过的是作者arXiv v1和固定官方代码，不冒称核对了不可访问的CVF最终版本。未向作者或其他人发送消息。
