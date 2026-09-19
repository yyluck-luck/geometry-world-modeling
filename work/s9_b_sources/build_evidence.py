"""Archive a bounded primary-source review; does not run experiments."""
import hashlib
import json
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'work/s9_b_sources'
NOW = datetime.now(timezone.utc).isoformat()

class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1
    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(data.strip())

p = Text()
p.feed((BASE / 'covrag_arxiv_v1.html').read_text())
(BASE / 'covrag_arxiv_v1.txt').write_text('\n'.join(p.parts) + '\n')

def entry(path):
    b = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}

sources = [
  {
    'id': 'teller1993', 'title': 'Global Visibility Algorithms for Illumination Computations',
    'authors': ['Seth Teller', 'Pat Hanrahan'], 'year': 1993,
    'venue_status': 'SIGGRAPH 1993 / Computer Graphics, pp. 239–246; DOI 10.1145/166117.166148',
    'urls': ['https://graphics.stanford.edu/papers/visglob/', 'https://graphics.stanford.edu/papers/visglob/visglobillum.ps.Z', 'https://people.csail.mit.edu/teller/pubs/visglobillum.pdf', 'https://people.csail.mit.edu/teller/pubs/pubs.html', 'https://api.crossref.org/works/10.1145/166117.166148'],
    'raw_file': 'visglobillum.ps.Z', 'text_file': 'visglobillum_stanford.txt',
    'read_scope': '§1, §§3–6, especially §6.1–6.3; author PDF 8 pages opened; Stanford PS fully downloaded and converted locally. Not an independent verification of all geometric proofs.',
    'mechanism': '用空间单元/portal、区域对遮挡候选表与连接区域的 tube；层次 radiosity 把 patch 细分时，子对的遮挡候选从父表继承并再分类。已判完全可见/不可见必须正确；未决可保守返回 partial。',
    'object_granularity_setting': '光照传输的面片区域对；增量单位是层次细分，不是本轮 B 的 surfel 位置移动或固定相机离散最前像素身份。',
    'exactness_boundary': '保守分类的已确定标签正确；不是所有像素都取得精确可见 ID，也不直接提供动态点移动后的 z-buffer 更新算法。',
    'b_implication': '“能证明则跳过、不能证明则继续处理”的可见性思想已有；B 不能据此声称首创保守证书，也不能将该旧方法误称为已完整解决 B。',
  },
  {
    'id': 'yi2003', 'title': 'Efficient Maintenance of Materialized Top-k Views',
    'authors': ['Ke Yi', 'Hai Yu', 'Jun Yang', 'Gangqiang Xia', 'Yuguo Chen'], 'year': 2003,
    'venue_status': 'ICDE 2003, pp. 189–200; DOI 10.1109/ICDE.2003.1260792',
    'urls': ['https://www.cse.ust.hk/~yike/topk/icde03.pdf', 'https://api.crossref.org/works/10.1109/ICDE.2003.1260792', 'https://experts.illinois.edu/en/publications/efficient-maintenance-of-materialized-top-k-views/'],
    'raw_file': 'topk/icde03.pdf', 'text_file': 'topk/icde03.txt',
    'read_scope': '§3 pp. 2–3, §§4.1–4.6 pp. 4–6, §6.3/6.4, §7/Fig. 7 p. 10, introduction/related work/conclusion; page numbers are author-PDF pages, not proceedings pages. Independent teammate verification; proof appendices not fully checked.',
    'mechanism': '收到 (id,new value) 标量更新，维护不少于 k 的精确辅助 top-k′ 池；低于池底的池外项可忽略，池不足 k 才从基表 refill；可按观测成本调整池大小。',
    'object_granularity_setting': '元组身份和标量排序；新分数作为输入。未处理从几何移动计算像素可见性/来源票数，也未处理后续 NMS。',
    'exactness_boundary': '返回 top-k 的正确性是精确的；高概率/随机更新模型限定的是 refill 效率。不能把某些更新模型下的摊销界直接搬到相关的几何更新。',
    'b_implication': '缓存候选、阈值忽略、失败全查和精确结果均已有。B 若只维护票数 top-k，属于很强的普通移植风险。',
  },
  {
    'id': 'gkorgkas2015', 'title': 'Finding the Most Diverse Products using Preference Queries',
    'authors': ['Orestis Gkorgkas', 'Akrivi Vlachou', 'Christos Doulkeridis', 'Kjetil Nørvåg'], 'year': 2015,
    'venue_status': 'EDBT 2015; DOI 10.5441/002/edbt.2015.19',
    'urls': ['https://openproceedings.org/2015/conf/edbt/paper-176.pdf'],
    'raw_file': 'topk/edbt2015_diverse_products.pdf', 'text_file': 'topk/edbt2015_diverse_products.txt',
    'read_scope': '§6.2/Algorithm 3, printed p. 210 (PDF p. 6); §7, printed p. 211 (PDF p. 7). Teammate read and synthesis agent independently reread §7 text.',
    'mechanism': 'Stopk 以采样偏好查询形成近似 reverse-top-k 中心，再做多样性选择；保存已算查询的第 k 分数，新产品不越过任何阈值可安全忽略。',
    'object_granularity_setting': '产品/偏好插入与集合多样性；不是相机几何、可见性或 greedy NMS。',
    'exactness_boundary': '无影响门保证同重跑 Stopk；越过阈值后的局部中心更新明确不保证同重跑结果。底层多样性算法本身含近似。',
    'b_implication': '连“保守门通过就保证复杂检索结果同重跑”的叙事也已有。不能把论文的安全分支扩大成全程精确维护，也不能把它叫 NMS。',
  },
  {
    'id': 'vmem2025', 'title': 'VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory',
    'authors': ['Runjia Li', 'Philip Torr', 'Andrea Vedaldi', 'Tomas Jakab'], 'year': 2025,
    'venue_status': 'ICCV 2025; inspected author arXiv v3 dated 2025-08-14; final CVF full PDF not independently read in this bounded task',
    'urls': ['https://arxiv.org/html/2506.18903v3', 'https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py'],
    'raw_file': 'vmem_arxiv_v3.html', 'text_file': 'vmem_arxiv_v3.txt',
    'read_scope': '§3, especially §3.1 Reading from the memory and Fig. 2; official pinned code blob opened, local provenance checked. Full call-timing audit belongs to the root task.',
    'mechanism': '论文描述以平均目标相机渲染带来源 view ID 的 surfel，考虑深度遮挡；按可见像素中来源频次排序，再以相近姿态的 NMS 取参考。实际默认代码平均哪些目标位姿，需单独核源码，不能从论文推断为整段平均。',
    'object_granularity_setting': '交互视频历史帧检索；写入几何/来源后，下一目标相机可改变。是 B 所要严格保持的已有消费者组合。',
    'exactness_boundary': '所读方法段定义原选择器，未给位置更新后保持原有序 top-4 的增量证书。是否存在其他版本实现不由此排除。',
    'b_implication': '几何→来源票数→NMS 不是 B 新造的机制；B 必须绑定真实实现的取整、遮挡、并列和逐步抑制语义。固定查询重复调用的实际机会需调用时序证据。',
  },
  {
    'id': 'covrag2026', 'title': 'Retrieve What’s Missing: Coverage-Maximizing Retrieval for Consistent Long Video Generation',
    'authors': ['Minseok Joo', 'Dogyun Park', 'Taehoon Lee', 'Kyujin Lee', 'Hyunwoo J. Kim'], 'year': 2026,
    'venue_status': 'Original arXiv preprint 2606.02479v1, 2026-06-01; no conference acceptance verified',
    'urls': ['https://arxiv.org/html/2606.02479v1'],
    'raw_file': 'covrag_arxiv_v1.html', 'text_file': 'covrag_arxiv_v1.txt',
    'read_scope': '§4.1–4.3, Eq. 2–4 and Algorithm 1; not a code or experimental reproduction.',
    'mechanism': '用源深度与姿态 warp 为目标二值覆盖；逐次取对剩余未覆盖区域增益最大的历史帧。滑动窗口估计新帧几何并缓存深度，历史深度可用于后续目标 warp。',
    'object_granularity_setting': '同属视频世界模型的几何历史参考检索。缓存的是深度估计，目标覆盖及贪心准则仍随查询变化。',
    'exactness_boundary': '这在改变参考选择准则；不是维护原 VMem 的有序四帧。其有界窗口限制几何推理成本，不等于全部覆盖计算/检索成本恒定。Eq. 2 的二值投影也不能等同 VMem 最前 surfel 投票。',
    'b_implication': '“缓存几何以节省记忆检索”已经是直接同对象近邻。B 的可主张差异只能是相同完整消费者输出的精确计算维护，尚未证明其新颖性或价值。',
  },
]

screened = [
 {'id':'anchorweave2026', 'title':'AnchorWeave: World-Consistent Video Generation with Retrieved Local Spatial Memories', 'authors':['Zun Wang','Han Lin','Jaehong Yoon','Jaemin Cho','Yue Zhang','Mohit Bansal'], 'year':2026, 'date_version':'2026-02-16 / arXiv 2602.14941v1', 'url':'https://arxiv.org/html/2602.14941v1', 'raw_file':'anchorweave_arxiv_v1.html', 'sections':'§3.2–3.5; Appendix B/Algorithm 1', 'disposition':'第二个近期直接同对象近邻：各帧局部点云独立存储、只重建新帧；FoV 筛选后按新增可见覆盖贪心选 anchor。改变存储/选择机制，不证明原 VMem 有序结果保持。正文与附录对初始 anchor 的措辞不一致，本评估不据此推断具体初始 ID。未核会议接收。'},
 {'id':'i3dm2026', 'title':'I3DM: Implicit 3D-aware Memory Retrieval and Injection for Consistent Video Scene Generation', 'authors':['Jia Li','Han Yan','Yihang Chen','Siqi Li','Xibin Song','Yifu Wang','Jianfei Cai','Tien-Tsin Wong','Pan Ji'], 'year':2026, 'date_version':'2026-03-24 / arXiv 2603.23413v1', 'url':'https://arxiv.org/html/2603.23413v1', 'raw_file':'i3dm_arxiv_v1.html', 'sections':'§3.2 and maximum-coverage appendix', 'disposition':'读完机制后未列核心五篇：由前馈新视角模型特征预测 patch 不确定性，再贪心覆盖选历史；改变评分/注入，没有核到固定原选择器的精确维护证书。'},
 {'id':'freescale2026', 'title':'FreeScale: Scaling 3D Scenes via Certainty-Aware Free-View Generation', 'authors':['Chenhan Jiang','Yu Chen','Qingwen Zhang','Jifei Song','Songcen Xu','Dit-Yan Yeung','Jiankang Deng'], 'year':2026, 'date_version':'2026-04-12 / arXiv 2604.10512v1', 'url':'https://arxiv.org/html/2604.10512v1', 'raw_file':'freescale_arxiv_v1.html', 'sections':'§4.1.2 and §7.1 Virtual Viewpoints Selection', 'disposition':'几何可见性与 certainty 构成图分数，排序后按 WIoU 做 NMS；是组合先例，但选择对象是为扩充 3D 场景生成的虚拟视点，非精确维护历史参考帧。'},
 {'id':'gimworld2026', 'title':'Geometry-Aware Implicit Memory for Video World Models', 'authors':['Zhengxuan Wei','Xu Guo','Xinghui Li','Xunzhi Xiang','Min Wei','Yiran Zhu','Qiulin Wang','Xintao Wang','Pengfei Wan','Xiangwang Hou','Qi Fan'], 'year':2026, 'date_version':'2026-06-01 / arXiv 2606.02436v1', 'url':'https://arxiv.org/html/2606.02436v1', 'raw_file':'gim_world_arxiv_v1.html', 'sections':'§3.4–3.5', 'disposition':'姿态/时间核的互信息贪心 pruning 与隐式记忆；已核到不同检索准则，不据此声称解决原几何投票/NMS 的精确维护。'},
]

groups = [
 {'id':'visibility', 'goal':'保守/精确可见性与增量粒度，主动查旧缓存反例', 'queries':[
  'incremental exact visibility computation dynamic scene conservative Teller Hanrahan visibility global illumination',
  '"incremental" "visibility" "top-k" surfel memory retrieval',
  '"Temporally Coherent Conservative Visibility" paper author pdf',
  '"Global Visibility Algorithms for Illumination Computations" Teller Hanrahan 1993',
  '"surfel" "incremental" "visibility" exact cache']},
 {'id':'ranking_diversity_nms', 'goal':'标量 top-k 与下游多样性/NMS 的精确维护先例', 'queries':[
  'materialized top k maintenance updates exact result diversity non maximum suppression',
  '"exact" "incremental" "non-maximum suppression" cache',
  '"continuous" "diversified top-k" "exact"',
  '"incremental" "non maximum suppression" "exact"',
  '"top-k" "diversity" "maintenance" dynamic queries']},
 {'id':'geometry_memory', 'goal':'近期直接同对象的几何记忆检索、缓存及 NMS', 'queries':[
  'geometry memory video generation reference frame retrieval visibility cache incremental VMem FreeScale GIM World',
  '"VMem" "cache" "retrieval" "exact"',
  '"geometry" "memory retrieval" "cache" "NMS"',
  '"incremental" "exact" "reference" "retrieval" "video" geometry memory',
  '"cache" "visibility" "reference frame" "selection" video generation',
  'COVRAG residual coverage memory retrieval video generation arxiv']},
]

for s in sources + screened:
    s['raw_archive'] = entry(BASE / s['raw_file'])

manifest = {'created_utc': NOW, 'scope':'All primary bytes, derivatives, HTTP receipts and review support in this new source directory, excluding manifest self; build script included. Root maintains project memory.', 'files':[entry(x) for x in sorted(BASE.rglob('*')) if x.is_file() and x.name != 'source_manifest.json']}
(BASE / 'source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')

review = {
 'status':'BOUNDED_PRIMARY_SOURCE_REVIEW_COMPLETE',
 'session_started_utc':'2026-09-05T20:19:08+00:00', 'completed_utc':NOW,
 'timezone':'Asia/Shanghai',
 'search_timestamp_scope':'Search queries occurred within this session; individual web-query wall times were not separately captured. HTTP receipt timestamps bind actual successful/failed fetches. No invented per-query exact times.',
 'candidate_scope':'B: fixed query camera and fixed point groups/source identities; geometry updates; preserve the unmodified implementation\'s final ordered top-4 frame IDs by conservative dependency/visibility/vote/NMS checks with full fallback.',
 'verdict':'GENERIC_CACHING_AND_EXACT_INCREMENTAL_RETRIEVAL_HAVE_STRONG_PRIOR_ART; NARROW_FULL_CHAIN_NOVELTY_AND_RUNTIME_VALUE_UNESTABLISHED',
 'not_an_idea_evaluator_score':True, 'experiments_run':False,
 'keyword_groups':groups, 'core_sources':sources, 'additional_screened_sources':screened,
 'primary_archive_manifest':entry(BASE/'source_manifest.json'),
 'local_original_source':{
  'repository':'https://github.com/runjiali-rl/vmem','commit':'39291e4f272f6b4f270691d930926ab5930f942e',
  'pipeline':entry(ROOT/'vendor/vmem_snapshot/modeling/pipeline.py'),
  'provenance':entry(ROOT/'vendor/provenance.json'),
  'origin':'Existing pinned local official snapshot, not a successful new raw HTTP download. GitHub blob was opened; raw HTTP fetch failed SSL EOF.'},
 'source_corrections':[
  'Stanford web-page title differs from actual paper title. Downloaded author paper header says SIGGRAPH 94 pp.443–450, inconsistent with author bibliography and publisher-deposited Crossref DOI (1993 pp.239–246); bibliography here follows the latter, while preserving the conflicting original bytes.',
  'ICDE Crossref fetched record has null issued year; institutional author bibliography supplies 2003. DBLP XML HTTP 503 is preserved, not claimed successful.',
  'COVRAG/AnchorWeave and other 2026 items are original preprints; keyword or manuscript template is not treated as conference acceptance.'
 ],
 'access_limits':[
  'Stanford initial guessed visglob.ps.Z failed; actual linked visglobillum.ps.Z succeeded.',
  'ACM DOI web endpoint errored and Crossref web open was blocked; direct Crossref HTTP JSON succeeded and was archived.',
  'VMem CVF endpoint returned 403; inspected arXiv v3 full method and official local pinned source instead.',
  'VMem new raw GitHub request SSL EOF; preserved failed receipt and use explicitly identified prior local source.',
  'AnchorWeave guessed project URL returned 404; arXiv full text succeeded.',
  'EDBT web PDF endpoint timed out; direct full PDF HTTP download and text extraction succeeded.',
  'No full-paper proof/experiment reproduction; only specified full-text method sections support the reported mechanisms. No paper performance metric is imported.'
 ],
 'required_falsifiers_and_baselines':[
  'Verify genuine repeated fixed-query consumers between writes, rather than imposing extra queries merely to make cache useful.',
  'Compare to unchanged-input cache, ordinary conservative dirty-pixel/tile rerendering plus full original selector, and incremental votes plus full original NMS.',
  'Require exact final ordered IDs under baseline floating-point, tie and NMS semantics; fourth/fifth raw-vote margin alone is insufficient.',
  'Measure entire cost including dependency maintenance, invalidations, fallbacks, memory and all query changes; do not count only skipped calls.',
  'If position updates cross pixel/depth/tie thresholds or point/source/camera identities change, handle or invalidate explicitly.',
  'S7/S8 already seen data are regressions, not unseen confirmation. Finite zero discrepancies do not replace a correctness argument.'
 ],
 'unknowns':[
  'This bounded search did not verify an exact full geometry→votes→ordered greedy-NMS maintenance algorithm under the precise B setting; it does not establish absence or novelty.',
  'Usefulness of fixed-camera/fixed-group setting in real VMem call timing is under separate root source audit.',
  'No acceleration, cache pass rate, consumer time share or video outcome has been measured for B.'
 ]
}

out = ROOT / 'docs/S9_B_NOVELTY_EVIDENCE.json'
out.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')

lines = [
 '# S9 候选 B：有界原始来源新颖性反证', '',
 f'检索始于 2026-09-05 20:19:08 UTC（北京时间 2026-09-06 04:19:08）；本归档完成时间 {NOW}。HTTP 获取的实际起止时间、失败记录和完整来源 SHA 见同名 JSON 与 `work/s9_b_sources/`。没有运行新实验，也没有进行完整 idea-evaluator 评分。', '',
 '结论：**“缓存 + 保守跳过 + 精确 top-k”已有强前例。** 近期同类视频记忆也已缓存历史几何。B 不能凭换成几何记忆应用就声称创新。尚待验证的是：对真实消费者有用的查询序列，能否低成本维护“几何→来源票数→逐步 NMS”的完整依赖，并严格保留原实现最终四个 ID 的顺序。此次检索没有核到完全同设定的方案；这不证明文献空白，更不证明 B 值得立项。', '',
 '范围固定为查询相机、点组和来源身份不变后的坐标更新；任何未被覆盖的增删点、来源或相机变化应失效/回退。原候选审查保留为历史版本；本文纠正其将 Stanford “增量可见性”泛化为动态移动维护的风险。', '',
 '## 五篇核心近邻', '',
 '覆盖分工：Teller 为保守增量可见性；Yi 为精确 top-k；Gkorgkas 为复杂多样性检索的同结果安全门；VMem 为实际几何/票数/NMS 消费者；COVRAG 为近期同对象缓存检索。', ''
]
for i,s in enumerate(sources,1):
    lines += [f'### {i}. {s["title"]}', '',
      f'{", ".join(s["authors"])}，{s["year"]}。{s["venue_status"]}。[原始全文]({s["urls"][2] if s["id"] == "teller1993" else s["urls"][0]})。', '',
      f'**实读位置：** {s["read_scope"]}', '',
      f'**原机制：** {s["mechanism"]}', '',
      f'**对象、粒度与设定：** {s["object_granularity_setting"]}', '',
      f'**精确性边界：** {s["exactness_boundary"]}', '',
      f'**对 B 的推论：** {s["b_implication"]}', '',
      f'原文件 `{s["raw_archive"]["path"]}`，SHA-256 `{s["raw_archive"]["sha256"]}`。', '']

lines += ['## 第二个近期同对象近邻与有界筛查', '',
 'COVRAG 与下列 AnchorWeave 是本轮补充的两个近期直接同对象近邻。其余三项为已打开相关全文段后记录的筛查去向，不用搜索摘要推断机制，也不把它们都称为最接近的精确维护方法。', '',
 '| 工作与原文 | 作者、年份/版本 | 实读位置 | 处理结果 |', '|---|---|---|---|']
for s in screened:
    lines.append(f'| [{s["title"]}]({s["url"]}) | {", ".join(s["authors"])}；{s["date_version"]} | {s["sections"]} | {s["disposition"]} |')

lines += ['', '## 必须排除的普通工程解释', '',
 '以下是本任务根据已核机制提出的检验要求，不是文献已证明 B 成功。若 B 只是把缓存、脏区域检测和原排序器串在一起，当前证据应将它视作工程候选；形成方法贡献还需证明具体证书超出这些直接基线的能力或成本。', '',
 '1. **真实重复消费机会。** 先核实际调用时序：同一查询究竟是否在多次位置更新之间被消费。不能为了提高缓存命中率主动增加原流程没有的查询。相机改变若总使证书失效，固定相机实验只证明人工受限问题。',
 '2. **普通缓存基线。** 至少比较输入完全未变的直接缓存、保守脏像素/区域重渲染后仍完整调用原选择器、增量票数后仍完整 NMS。只胜过每次全渲染不足以区分一般缓存移植。',
 '3. **完整输出语义。** 固定历史姿态可以固定两帧间的抑制关系，但票数顺序仍可能变化。NMS 会跳过候选，原始第 4/5 名分差不能保证最终四张。取整、视锥、前后遮挡、浮点并列和逐步接受/拒绝都需与原实现一致。',
 '4. **总成本。** 将依赖维护、证书、失效、回退、查询相机变化与内存计入；不能只报告省掉多少次渲染。几何输入分数的代价不在 Yi 的“收到新分数”假设里。',
 '5. **证据界限。** 尚无 B 的速度、通过率或视频结果；有限回归零错选不等于形式证明。S7/S8 已看过，只能是现有软件回归材料，不能改称新方法未见场景验证。', '',
 '## 检索范围、时间及未决项', '',
 '以下三组检索均发生于本次记录区间；未逐条记录 web 查询秒级时点，因此只报告真实区间。精确 HTTP 时点以请求回执为准。随后沿论文/作者/官方项目链接打开全文与指定算法段。没有做全领域穷尽检索，未确认接受状态的 2026 工作均按原始预印本标注。', '']
for g in groups:
    lines += [f'**{g["id"]}：{g["goal"]}**', ''] + ['- `'+q+'`' for q in g['queries']] + ['']
lines += [
 '重要来源纠正：Stanford 网页用题名 *Visibility Computations for Global Illumination Algorithms*，实际原稿题名为本报告所列；下载作者稿页眉写 SIGGRAPH ’94/443–450，却与[作者书目](https://people.csail.mit.edu/teller/pubs/pubs.html)及[出版方 Crossref DOI 元数据](https://api.crossref.org/works/10.1145/166117.166148)的 1993/239–246 不符。本报告保留原字节并采用后两者的一致书目信息，不悄悄修改原稿。该文的增量是细分中的遮挡关系继承，不能用“精确”一词把未决 partial 判定变成全像素精确答案。', '',
 '访问异常已保留：Stanford 最初猜测旧文件名失败，随后实际链接成功；VMem CVF 403，采用 arXiv v3 方法全文；新 raw GitHub 请求 SSL EOF，采用明确标注的旧官方固定快照（commit `39291e4f272f6b4f270691d930926ab5930f942e`），没有冒称重新获取成功；EDBT web PDF 超时但直接 HTTP 原 PDF 成功；ICDE DBLP XML 503；AnchorWeave 猜测项目页 404；Crossref 浏览器端未打开但直接 HTTP JSON 成功。', '',
 '未知项：本轮没有核到在 B 精确设定下保证完整有序 greedy-NMS 输出一致的已发表算法；不能据此断言不存在。固定查询假设的真实适用范围由根任务另做调用时序核查。没有复现论文实验或导入论文速度/质量指标，没有独立通检全部证明附录。', '',
 '## 可复核归档', '',
 f'- 结构化事实与检索范围：`docs/S9_B_NOVELTY_EVIDENCE.json`。',
 f'- 原始字节、文本衍生、回执和辅助审查：`work/s9_b_sources/source_manifest.json`；SHA-256 `{review["primary_archive_manifest"]["sha256"]}`。',
 '- top-k 独立原文核查：`work/s9_b_sources/topk/VERIFICATION_REPORT.md` 与 `verification.json`。',
 f'- 旧官方本地 pipeline SHA-256 `{review["local_original_source"]["pipeline"]["sha256"]}`；它只是消费者语义证据，实际时序结论由根任务独立归档。',
 '- 所有来源 SHA 在 JSON 中固定。下载原稿与转换出的 PDF/text 分别列出，不把本地转换 PDF 当作服务器返回的原 PDF。本文不修改候选旧稿、实验源码、协议、结果或主记忆。', ''
]
(ROOT/'docs/S9_B_NOVELTY_EVIDENCE.md').write_text('\n'.join(lines))
print(json.dumps({'completed_utc':NOW,'manifest':entry(BASE/'source_manifest.json'),'md':entry(ROOT/'docs/S9_B_NOVELTY_EVIDENCE.md'),'json':entry(out)},ensure_ascii=False,indent=2))
