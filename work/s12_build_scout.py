from pathlib import Path
from datetime import datetime, timezone, timedelta
import json, hashlib

ROOT=Path(__file__).resolve().parent.parent
S=ROOT/'work/S12_literature_sources'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
now=datetime.now(timezone.utc)
papers=[
 dict(id='VMem',title='VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory',authors=['Runjia Li','Philip Torr','Andrea Vedaldi','Tomas Jakab'],year=2025,status='ICCV 2025; methods read in author arXiv v3',version='2506.18903v3',version_date='2025-08-14',url='https://arxiv.org/html/2506.18903v3',file='vmem_arxiv_v3.html',locators=['§3.1 Reading from the memory / Fig. 4','§4.1 Implementation details','§4.4 / Table 4'],object='historical RGB frames',evidence='rendered surfel source-index frequency; pose NMS',budget='K=4 efficient model; K=17 also studied',relationship='existing actual consumer; already accounts for target visibility and pose diversity, without residual-union greedy in the read procedure'),
 dict(id='COVRAG',title="Retrieve What's Missing: Coverage-Maximizing Retrieval for Consistent Long Video Generation",authors=['Minseok Joo','Dogyun Park','Taehoon Lee','Kyujin Lee','Hyunwoo J. Kim'],year=2026,status='arXiv preprint; venue acceptance not verified',version='2606.02479v1',version_date='2026-06-01',url='https://arxiv.org/html/2606.02479v1',file='covrag_arxiv_v1.html',locators=['§4.1 Eq.(2–3)','§4.2 Eq.(4–6), Algorithm 1','§5 implementation; §5.3; Appendix C'],object='historical RGB frames',evidence='depth-warped binary target-pixel coverage; residual uncovered coverage greedy',budget='n=2 retrieved, plus temporal context δ=5 or 2',relationship='direct counterexample to novelty of independent scores → complementary coverage selection'),
 dict(id='I3DM',title='I3DM: Implicit 3D-aware Memory Retrieval and Injection for Consistent Video Scene Generation',authors=['Jia Li','Han Yan','Yihang Chen','Siqi Li','Xibin Song','Yifu Wang','Jianfei Cai','Tien-Tsin Wong','Pan Ji'],year=2026,status='arXiv preprint; venue acceptance not verified',version='2603.23413v2',version_date='2026-07-31',url='https://arxiv.org/html/2603.23413v2',file='i3dm_review/paper_v2.html',locators=['§3.2 Eq.(5–7)','§4.1 Implementation Details','Supplementary §2 Maximum Coverage Selection Algorithm / Algorithm 1'],object='historical whole RGB frames; score granularity is target patches',evidence='learned FF-NVS uncertainty → confidence; patch-wise maximum marginal gains',budget='K=3 additional + last frame = 4; 20 target views per 77-frame clip',relationship='very direct fixed-four and jointly complementary retrieval precedent; confidence is learned, not measured depth visibility'),
 dict(id='AnchorWeave',title='AnchorWeave: World-Consistent Video Generation with Retrieved Local Spatial Memories',authors=['Zun Wang','Han Lin','Jaehong Yoon','Jaemin Cho','Yue Zhang','Mohit Bansal'],year=2026,status='arXiv preprint; venue acceptance not verified',version='2602.14941v1',version_date='2026-02-16',url='https://arxiv.org/html/2602.14941v1',file='anchorweave_arxiv_v1.html',locators=['§3.2–3.4 / Fig. 2','§4.1 Implementation details','Appendix B / Algorithm 1'],object='per-frame local point clouds rendered into anchor clips',evidence='FoV filter, then greedy additional visibility coverage over target trajectory chunks',budget='at most K=4 per D=8-frame training chunk; invisible padding if fewer',relationship='direct local-geometry complementarity precedent; consumer receives rendered anchor clips and trained fusion, not merely four raw photos'),
 dict(id='BoostMVSNeRFs',title='BoostMVSNeRFs: Boosting MVS-based NeRFs to Generalizable View Synthesis in Large-scale Scenes',authors=['Chih-Hai Su','Chih-Yao Hu','Shr-Ruei Tsai','Jie-Ying Lee','Chin-Yang Lin','Yu-Lun Liu'],year=2024,status='SIGGRAPH 2024 Conference Papers, verified author project + arXiv metadata',version='2407.15848v1',version_date='2024-07-22',url='https://arxiv.org/html/2407.15848v1',file='boostmvsnerfs_arxiv_v1.html',locators=['§3.2 Eq.(3–4)','§3.4 Algorithm 1','§4.3 Table 3','Appendix C'],object='support cost volumes, each constructed from three input views',evidence='soft 2D visibility masks; residual coverage greedy and support-volume fusion',budget='K cost volumes; not K distinct RGB frames',relationship='earlier NVS maximum-coverage precedent; explicitly compares nearest-pose, independent-visibility and greedy coverage')
]
for p in papers:
 f=S/p['file'];p.update(source_path=str(f.relative_to(ROOT)),source_sha256=sha(f),source_bytes=f.stat().st_size)

limitations=[
 'Bounded scout, not a systematic review or proof of novelty absence/presence.',
 'Only methods/definitions and specified experimental design passages were checked; no model, renderer, selector, timing or new data experiment ran.',
 'No paper performance number is adopted as a local expected gain; different backbones, context budgets, geometry and datasets remain separate.',
 'COVRAG Eq.(2) is projected-pixel occupancy. The inspected definition does not specify target-depth agreement or a complete cross-source nearest-surface visibility check; do not equate it to TUM measured co-visibility.',
 'AnchorWeave Appendix B prose says first rendered frame, while Algorithm 1 starts P_latest. Initialization identity is unresolved without code audit; no exact policy implementation claim.',
 'BoostMVSNeRFs §3.4 has overly broad polynomial-optimal wording. This review does not adopt it as an exact-optimality or approximation theorem; Algorithm 1 also uses ambiguous P subscripts.',
 'I3DM confidence is negative predicted uncertainty, not a calibrated binary visibility probability. Its global confidence canvas starts at zero; last frame is the anchor/input and mandatory context, not a claimed initial coverage canvas.',
 'Aalto Ji thesis was only accessible as institutional metadata/abstract: no public full-text link found in the opened item; Nam et al. 2022 was only verified bibliographically. Neither is core method evidence.',
 'S7/S8 are already-seen local conditions. New coverage evaluation on them would be exploratory diagnosis, not unseen-scene method confirmation.'
]
local_inputs=['AGENTS.md','RESEARCH_MEMORY.md','RESEARCH_LOG.md','docs/S9_B_NOVELTY_EVIDENCE.md','docs/LITERATURE_SYNTHESIS_V2.md','docs/S7_RESULTS.md','docs/S8_RESULTS.md']
inputs=[{'path':x,'sha256':sha(ROOT/x)} for x in local_inputs]
data={'recorded_utc':now.isoformat(),'recorded_beijing':now.astimezone(timezone(timedelta(hours=8))).isoformat(),'search_started_utc':'2026-09-05T22:37:30+00:00','scope':'S12 coverage-complementary fixed-budget frame selection; separate from closed fixed-output caching candidate B','verdict':'PLAIN_GREEDY_COVERAGE_IS_DIRECT_PRIOR_ART_AND_REQUIRED_BASELINE_NOT_ESTABLISHED_NOVELTY','core_papers':papers,'limits':limitations,'query_log':'work/S12_literature_sources/query_log.json','primary_download_manifests':['work/S12_literature_sources/download_manifest.json','work/S12_literature_sources/download_manifest_second.json','work/S12_literature_sources/i3dm_review/download_receipt.json','work/S12_literature_sources/i3dm_review/download_v2_receipt.json'],'local_context_read':inputs,'claim_status':{'fixed_four_novel':False,'joint_residual_coverage_novel':False,'new_generator_improvement_established':False,'global_novelty_claim_supported':False,'ordinary_greedy_is_appropriate_baseline':True,'candidate_B_reopened':False},'no_experiment':True,'no_ledger_edit':True}
(ROOT/'docs/S12_COVERAGE_NOVELTY_SCOUT.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

md='''# S12：覆盖互补选四张参考图的定点文献核查

**结论：普通的“按新增覆盖贪心选四张”已有直接先例，应作为强基线，不能仅凭这句话立为新方法。** COVRAG 已显式替换逐帧独立评分，I3DM 已采用三张检索帧加最后一帧；AnchorWeave 与 BoostMVSNeRFs 也以新增覆盖联合选择。是否还存在有价值的具体改进，需要新的机制和消费者证据。本审查不恢复旧候选 B 的固定输出缓存方案，也不替完整 idea-evaluator 评分。

检索始于 **2026-09-05 22:37:30 UTC / 北京时间 2026-09-06 06:37:30**；本报告生成时间：RECORDED。先宽搜，再按直接近邻窄搜，共五篇核心原文。完整查询串、访问起止时间、失败和文件哈希在同名 JSON 与 `work/S12_literature_sources/`。只核正文指定段落，未运行模型、选图或实验，未改主账。

## 先把问题说清楚

令 Cᵢ(q) 是历史图 i 能支持的目标相机 q 区域。互补性通常希望扩大所选四图的**并集**，每次优先选新增覆盖最多的一图。它不同于要求四张图都看到同一区域的交集；也不同于 S7/S8 为公平比较几何残差而取的“四张反事实地图共同有效 mask”。“共同可见”必须明确是源图与目标视角的共同可见，不能把这三个集合混用。

已有 S7/S8 只支持组件层动机：选图效果依赖关联、位置和读出规则；去掉 NMS 或放开候选并非总有益。S8 主设置旧 A0 负/A1 正组合及预定抵消未重现。它们没有试验本候选的联合覆盖算法，也没有证明覆盖提高会让视频更好。[S7 结果](S7_RESULTS.md)；[S8 结果](S8_RESULTS.md)。本轮延续已核综述中“几何证据、参考检索、条件注入和生成评价分开”的定位。[综述](LITERATURE_SYNTHESIS_V2.md)

## 五篇核心原文

| 工作、作者与版本 | 实读正文与机制 | 对当前想法最直接的约束 |
|---|---|---|
| **VMem**；Runjia Li、Philip Torr、Andrea Vedaldi、Tomas Jakab；ICCV 2025；arXiv v3，2025-08-14 | §3.1/Fig.4：目标相机渲染带来源 ID 的 surfel，按像素频次排参考，再做姿态 NMS。§4.1 有 K=4 的生成器配置。[原文](https://arxiv.org/html/2506.18903v3#S3.SS1) | 已使用目标可见性和姿态多样性；不能写成“完全不考虑遮挡或冗余”。所读选择流程没有逐次扣除已选覆盖。本项目固定选择器来自它的检索代码。 |
| **COVRAG / Retrieve What's Missing**；Minseok Joo、Dogyun Park、Taehoon Lee、Kyujin Lee、Hyunwoo J. Kim；2026-06-01，v1 预印本 | §4.1 Eq.(2–3)：源深度/姿态投影为二值目标像素图；§4.2 Eq.(4–6)/Algorithm1：从当前上下文覆盖开始，每次最大化尚未覆盖区域并更新 OR。§5 使用 n=2 检索帧，另有 δ=5/2 时间上下文。[原文](https://arxiv.org/html/2606.02479v1#S4.SS2) | 与“独立评分改为互补联合选帧”直接重叠。其覆盖是估计深度的投影占据；不是本项目实测深度一致支持，也不是最前 surfel 身份。不能直接移植其视频收益或称已复现。 |
| **I3DM**；Jia Li、Han Yan、Yihang Chen、Siqi Li、Xibin Song、Yifu Wang、Jianfei Cai、Tien-Tsin Wong、Pan Ji；v1 2026-03-24，当前 v2 2026-07-31 | §3.2 Eq.(5–7)、补充§2/Algorithm1：用前馈新视角网络特征估计 patch 置信，按逐 patch 最大值的边际收益贪心选整张历史图。§4.1：每段77帧取20个目标视角，K=3 再加最后一帧，共4张。[v2 原文](https://arxiv.org/html/2603.23413v2#S3.SS2) | 固定四张、目标条件和覆盖互补均有直接先例。区别在学习的隐式置信和后续注入，不能靠改成显式 surfel 就推定新颖。置信画布初值是零；最后帧为强制上下文/输入，不能误称其覆盖已作为画布初值。 |
| **AnchorWeave**；Zun Wang、Han Lin、Jaehong Yoon、Jaemin Cho、Yue Zhang、Mohit Bansal；2026-02-16，v1 预印本 | §3.2–3.4、Fig.2、附录B：每帧保留局部点云，FoV 筛候选，再按目标轨迹块的新增可见覆盖贪心挑选；渲染成 anchor clips 输入控制器。§4.1 训练用 D=8、至多 K=4。[原文](https://arxiv.org/html/2602.14941v1#S3.SS3) | 是显式几何互补检索的直接近邻；消费的是渲染片段和学习融合，非仅四张原照片。附录文字说 first rendered frame，伪代码却从 P_latest 开始；初始身份有歧义，不据此声称已核 exact 实现。 |
| **BoostMVSNeRFs**；Chih-Hai Su、Chih-Yao Hu、Shr-Ruei Tsai、Jie-Ying Lee、Chin-Yang Lin、Yu-Lun Liu；SIGGRAPH 2024，arXiv v1 2024-07-22 | §3.2 生成软二维可见性 mask；§3.4/Algorithm1 把选择写为 maximum coverage，贪心降低残余未覆盖权重；§4.3/Table3 比较近姿态、独立可见性与联合覆盖。[原文](https://arxiv.org/html/2407.15848v1#S3.SS4)；[作者项目](https://su-terry.github.io/BoostMVSNeRFs/) | 较早的新视角合成先例；所选单位是各由三张输入图形成的代价体，K 个代价体不等于 K 张不同照片。普通贪心覆盖已有；不将原文过宽的 polynomial-optimal 措辞当作全局最优证明。 |

COVRAG、I3DM、AnchorWeave 的会议接收状态未在本轮独立核定，按预印本记录。VMem、BoostMVSNeRFs 的已发表身份与原文方法证据分开保存。这里不采用论文性能数值推算本机收益。

## 对新颖性与下一步判据的含义

这不是从“没搜到”推出空白：已找到多篇明确的正面重叠。把独立 top-4 换为贪心剩余覆盖、加固定四张预算、改用另一种几何表示，这三个描述都不足以独立构成贡献。仍需说明究竟修复哪个已识别的失效条件，以及为何普通二值/软覆盖贪心做不到。

若根任务以后立最小诊断，公平比较至少要固定候选历史、总参考数、相机输入、是否强制最后帧和输出排序规则；分别比较同一覆盖证据的独立打分与贪心边际增益，才能拆出“联合选择”的作用。姿态 NMS 若保留，必须同等说明约束；不能把换目标与去 NMS 混算。本轮只建议对照，不执行或选最好结果。

选择分数应来自实际可用的预测证据；查询实测深度/GT 只能用于选择封存后的独立评价。若用实测支持并集找最优四张，只能标作知道答案后的上限诊断，不能称可部署方法或方法胜出。有限20候选、4张预算的集合枚举与普通贪心，也不产生新的优化算法贡献。

覆盖只能表示区域是否有支持。遮挡判断错误、参考图模糊、视角差异及跨图矛盾仍可能影响消费；本项目尚未证明同等预算下的生成收益。S7/S8 已见结果可用于探索或基线诊断，不能重新称未见新场景。具体限制也不能因为论文没有写而自动升级为创新点。

## 检索边界与证据保存

三个关键词组为：(G1) reference view / novel view synthesis / greedy coverage / set cover；(G2) BoostMVSNeRFs、reference subset、visibility-guided fixed budget；(G3) VMem、COVRAG、I3DM、AnchorWeave 的几何历史检索。先三条宽搜，再窄搜原文入口与同对象机制；实际全部字符串见 `query_log.json`，搜索片段只用于找入口。

另外遇到 Xu Ji 的 Aalto 2025 硕士论文 *3D Gaussian visibility-guided view selection for novel view synthesis*，其[院校条目](https://aaltodoc.aalto.fi/items/eb4782f5-85c1-42ea-9774-0e100894887a)仅取得摘要/元数据，页面指向 Thesis Database，没有取得公开全文；故不推断它如何实现联合覆盖。Nam、Jung、Han、Han 的2022年 *An Efficient Algorithm to Select Reference Views for Virtual View Synthesis* 仅核[院校书目](https://sejong.elsevierpure.com/en/publications/an-efficient-algorithm-to-select-reference-views-for-virtual-view/)和 DOI 10.1109/ACCESS.2022.3182401，DOI web 打开失败，也不当作核心方法证据。OpenReview 的 BoostMVSNeRFs PDF 入口遇浏览器验证，改读同作者 arXiv 全文。没有登录绕过或外部联系。

所有核心已下载的原始 HTML、元数据、派生文字与检索回执有 SHA-256 清单；HTML 是权威本地副本，文字提取不等于作者排版 PDF。I3DM v1/v2 独立核对另见 `work/S12_literature_sources/i3dm_review/`。本轮不是全领域综述，不声称穷尽全部论文或排除其他更近工作。

原文 SHA-256：

HASH_TABLE
'''
md=md.replace('RECORDED',data['recorded_utc']).replace('HASH_TABLE','\n'.join(f"- {p['id']} ({p['version']}): `{p['source_sha256']}`" for p in papers))
(ROOT/'docs/S12_COVERAGE_NOVELTY_SCOUT.md').write_text(md)
files=[]
for p in sorted(S.rglob('*')):
 if p.is_file() and p.name!='fixed_source_hashes.json':files.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)})
(S/'fixed_source_hashes.json').write_text(json.dumps({'recorded_utc':datetime.now(timezone.utc).isoformat(),'files':files,'scope':'all current S12 literature archive files; later independent review additions require a new manifest'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'files':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in [ROOT/'docs/S12_COVERAGE_NOVELTY_SCOUT.md',ROOT/'docs/S12_COVERAGE_NOVELTY_SCOUT.json',S/'fixed_source_hashes.json']]},indent=2))
