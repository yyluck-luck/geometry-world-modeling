from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,re
ROOT=Path(__file__).resolve().parent.parent
P=ROOT/'docs/S12_COVERAGE_IDEA_EVALUATION.md'
s=P.read_text();d=json.loads((ROOT/'docs/S12_COVERAGE_NOVELTY_SCOUT.json').read_text());checks=[]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def check(name,v):
 checks.append({'name':name,'passed':bool(v)})
 if not v: raise AssertionError(name)
for p in d['core_papers']:
 check(p['id']+': title',p['title'] in s)
 row=next(line for line in s.splitlines() if line.startswith('| *'+p['title']+'*'))
 for a in p['authors']:check(p['id']+': author '+a,a in row)
 check(p['id']+': year',str(p['year']) in row)
 check(p['id']+': primary link',p['url'] in row)
 check(p['id']+': source SHA',sha(ROOT/p['source_path'])==p['source_sha256'])
for name,condition in [
 ('only sections 1,2,7',re.findall(r'^## (\d+)\.',s,re.M)==['1','2','7']),
 ('assistant-origin C0', '由研究助手提出的候选C0，用户没有声称已经发明它' in s),
 ('untested acknowledged','尚未运行C0' in s),
 ('not literal implementation duplication','不是“实现逐字相同”' in s),
 ('representation and consumer differences retained','消费者差异' in s),
 ('rejection limited to novelty positioning','只否定本版本的创新定位' in s),
 ('pose14 separate','不作为C0的辩护或胜出证据' in s),
 ('GT oracle boundary','知道答案后的上限分析' in s),
 ('video benefit unknown','完整VMem／视频质量尚未验证' in s),
 ('correct review then freeze sequence','独立设计/实现审查，再冻结并运行' in s and '已冻结前设计' not in s),
 ('CRITICAL narrow research judgment explicit','CRITICAL是对当前唯一贡献的研究判断' in s),
 ('untested/resource automatic rejection excluded','不因“尚未测试”自动触发' in s and '不来自对用户工期或资源期限的臆测' in s),
 ('new mechanism is new version','加入新的机制则应视为另一个版本重新评价' in s)
 ]:check(name,condition)
now=datetime.now(timezone.utc).isoformat()
skill=Path('/Users/rocket/.codex/skills/idea-evaluator/SKILL.md')
fatal=skill.parent/'references/fatal-flaws.md'
result={'status':'PASS','reviewed_utc':now,'manuscript':{'path':str(P.relative_to(ROOT)),'sha256':sha(P),'bytes':P.stat().st_size},'checks':checks,'check_count':len(checks),'findings_resolved':[{'issue':'pose14 planning stage described with malformed freeze wording','resolution':'final says independent design/implementation review, then freeze/run'},{'issue':'make narrow CRITICAL rationale explicit, rather than infer it automatically from untested status or resource lifecycle','resolution':'final explicitly scopes unique claimed contribution and requires new-version evaluation for a new mechanism'}],'remaining_required_changes':[],'skill_sources':[{'path':str(q),'sha256':sha(q)} for q in [skill,fatal]],'primary_literature_sources':[{'id':p['id'],'path':p['source_path'],'sha256':p['source_sha256'],'url':p['url']} for p in d['core_papers']],'supporting_evidence':[{'path':n,'sha256':sha(ROOT/n)} for n in ['docs/S12_COVERAGE_NOVELTY_SCOUT.md','docs/S12_COVERAGE_NOVELTY_SCOUT.json','docs/S12_EXISTING_EVIDENCE_AUDIT.md','docs/S12_MATCHED_BUDGET_PROTOCOL.md','work/S12_IDEA_INITIAL_TEXT_CHECK.json']],'scope':['Read-only review of the idea-evaluator application, novelty evidence and wording; no modification to reviewed manuscript.','F1 CRITICAL is supportable only for C0 with ordinary greedy coverage as the sole alleged method contribution; it is not an exhaustive duplication proof.','No experimental defeat or generator utility conclusion is made; C0 is untested and proposed by assistant, not an invention claim attributed to user.','Five titles/authors/years and object/mechanism/granularity/setting checked against the current archived primary-source scout; I3DM current v2 retained.','Teammate independently reread the skill early gate and current C0 scope; no additional mandatory rule-misuse finding.','No new literature search, model, renderer, selector, experiment, ledger edit, or pose14 execution/protocol implementation approval.']}
(ROOT/'docs/S12_COVERAGE_IDEA_REVIEW.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
md=f'''# S12 C0 想法评估的独立审查

**PASS：当前终稿没有剩余必修项。** 审查于 {now}，绑定 `docs/S12_COVERAGE_IDEA_EVALUATION.md`，SHA-256 `{sha(P)}`。本回执只审查 C0 的论证与文献范围，不批准 pose14 实现或运行。

## F1 与 CRITICAL 短路

实际读取 [idea-evaluator 主文件](/Users/rocket/.codex/skills/idea-evaluator/SKILL.md) 的 Step 2 及 [fatal-flaws](/Users/rocket/.codex/skills/idea-evaluator/references/fatal-flaws.md) 的 F1、检测规则、严重性与 data-refuted 边界。F1 问的是 “what does this idea add over the single closest prior work?”；主文件规定 CRITICAL 后仅输出第 1、2、7 节。终稿满足该结构，没有继续五维评分或推算学生能力与周期。

这里可支持的判断是：**严格固定 C0 唯一贡献为普通新增覆盖贪心，补实验、换标题或润色不能使已知规则本身成为新方法。** 需要新增的覆盖估计器、可靠性机制或消费者适配时，应成为另一版想法重新评价。CRITICAL 是这个窄范围内的研究判断；技能并未要求把一切尚未测试、存在相似工作或存在设置差异的想法自动判死。

终稿明确保留表示、anchor、评分粒度、查询单位与消费者差异，不宣称各工作逐字或全流程重复。COVRAG 提供联合残余覆盖的直接先例，I3DM 提供总四帧的直接先例；这些足以反驳“普通规则及四帧本身就是新贡献”，但不证明任何未来改进都无价值。也未借 S7/S8 结果触发 data-refuted 自动否决：C0 尚未执行，旧条件差异不是它失败的实验数据。

## 文献和研究范围

五篇完整题名、作者顺序、年份与原文链接已核。BoostMVSNeRFs 全题与官方 arXiv 一致；其选择单位是代价体，不误称四张原图。VMem 已有目标可见性与姿态 NMS，不被描写成完全不处理遮挡/冗余。COVRAG 的二值投影、I3DM 的学习 patch 置信与 AnchorWeave 的局部点云/anchor 片段也未混为相同覆盖真值。

I3DM 采用当前 v2，补充章节为 §2；三张检索加最后帧与自由选四张的约束不同。未核会议接收的三篇只称预印本。15 条查询和 44 份文件是检索与归档数量，不是论文数量、实验样本数或系统性穷尽证明。原文机制及版本证据见 [定点核查](S12_COVERAGE_NOVELTY_SCOUT.md)。

终稿正确说明 C0 由研究助手提出，不把用户写成发明宣称者；pose14 同候选数量诊断独立于 C0，不被用作 C0 的辩护或胜出证据。实测支持、GT 最优上限、真实视频消费者收益也保持分离。

## 已修问题和审查边界

初审提出的一处必修状态措辞和一处必要理由澄清均已处理：第 7.2 项改为先独立设计/实现审查、再冻结运行；第 2 节明确 CRITICAL 针对当前唯一贡献，不从未测试或臆测资源工期自动触发。

此次完成 {len(checks)} 项文本/元数据/来源身份核对，加上逐段论证审读；次数不代表独立科研样本。另有队友只读核对 skill 早期门与 C0 逻辑，同样未发现必修规则误用。没有修改根稿、运行实验或选择器、进行新泛搜、批准新实验实现，亦没有写入主账。若根稿内容改变，应重新绑定 SHA；若提出新机制，不能沿用当前 CRITICAL 结论。
'''
(ROOT/'docs/S12_COVERAGE_IDEA_REVIEW.md').write_text(md)
print(json.dumps({'status':'PASS','checks':len(checks),'manuscript_sha256':sha(P),'review_md_sha256':sha(ROOT/'docs/S12_COVERAGE_IDEA_REVIEW.md'),'review_json_sha256':sha(ROOT/'docs/S12_COVERAGE_IDEA_REVIEW.json')},indent=2))
