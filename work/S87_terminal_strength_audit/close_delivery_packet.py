"""Append actual workflow status and publish immutable supplemental readback."""
from finalize_report_delivery import R, S, B, P, C, sha, writej, copy_checked
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json, shutil, re, sys, fcntl

if __name__=='__main__':
    assert not (S/'FINAL_DELIVERY_INDEX.json').exists()
    for name in ['FINAL_DELIVERY_SCIENCE_REVIEW.json','NEXT_DATA_ACCESS_CHECK_02.md','BEGINNER_READING_MAP_168.md']:
        assert (S/name).is_file(),name
    final_review=json.loads((S/'FINAL_DELIVERY_SCIENCE_REVIEW.json').read_text())
    assert final_review['accepted_reviewed_scope'] and not final_review['blocking_findings']
    now=datetime.now(timezone.utc);stamp=now.isoformat()
    old=json.loads((R/'workflow_checks.jsonl').read_text().splitlines()[-1])
    gap=(now-datetime.fromisoformat(old['checked_utc'])).total_seconds()/60
    findings={
      'skills':'Supervisor科研流程、本地Claude科学批判和PDF技能按实际任务应用；本轮接续未因工具数量而重复模型咨询。',
      'innovation':'S87末步.75构成本例MSE必要性反例；不包装普通融合为创新。原文/数学边界保留；新批独立多视角数据访问仍未落实。',
      'experiment':'24新目标行与16旧引用分开；科学输出、独立算术核、视觉审查均完成。报告封版与网页核查未新增模型或科学评分。',
      'tools_retrieval':'本机VAE/Python/LaTeX/Poppler已用；额外官方Drive及repo元数据3请求含1次TLS失败，0数据包/图像下载。PDF打开请求返回queued，不称屏幕已打开。',
      'agents':'三子岗完成阅读导航、独立交付审查、数据访问，均为明确有界任务；完成后不冒称仍在运行。',
      'records':'实际科学时间、53.74秒缓存派生边界、首次排版失败、历史超时及HTTP失败保留；时间不换算成学生工时。',
      'handoff':'12页新PDF与168页合并已接受和回读，当前交接/入口同步；本脚本随后保存完成后快照与补充manifest。'}
    check=dict(schema='research-workflow-check-v1',checked_utc=stamp,checked_local=now.astimezone(timezone(timedelta(hours=8))).isoformat(),previous_checked_utc=old['checked_utc'],interval_minutes=gap,cadence_compliance='ON_TIME' if gap<=30 else 'OVERDUE',checks=[dict(item=k,status='PASS',finding=v) for k,v in findings.items()],next_step='停止同例强度扫参；优先有明确同步/相机/位置参考的独立小片段。PointOdyssey具体访问和划分仍未落实，不启动新生成。')
    with (R/'workflow_checks.jsonl').open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX);f.write(json.dumps(check,ensure_ascii=False)+'\n');f.flush();fcntl.flock(f,fcntl.LOCK_UN)
    writej(S/'WORKFLOW_CHECK_DELIVERY.json',check)
    tail=f'''最新七项检查UTC {stamp}，实际间隔{gap:.6f}分钟，{check['cadence_compliance']}；前两次OVERDUE记录不改。报告与科研本批已闭合，下一按独立数据入口推进；不重跑已成功的S86/S87。'''
    secondary='第二批实际3请求已核Drive目的页只见整包和官方repo问题元数据，另1请求TLS失败；共6请求/2批，仍未定位具体同步序列。未取得新图像/NPZ/数据包，许可冲突与划分独立性保留。见NEXT_DATA_ACCESS_CHECK_02.md；用户问题不是作者数据声明。'
    canonical=[R/'RESEARCH_MEMORY.md',R/'docs/RESEARCH_HANDOFF_CURRENT.md',R/'docs/PROPOSAL_PROGRESS_CURRENT.md',R/'docs/PROJECT_DELIVERY_TRACKER.md',S/'CONTINUE_HERE.md']
    for p in canonical:
        text=p.read_text();a=text.index('<!-- S87_CURRENT_BEGIN -->');z=text.index('<!-- S87_CURRENT_END -->',a)
        block=text[a:z]
        block=re.sub(r'（UTC [^\n]+?）',f'（交付记录UTC {stamp}）',block,count=1)
        pos=block.index('最新七项检查UTC ')
        block=block[:pos]+secondary+'\n\n'+tail+'\n'
        p.write_text(text[:a]+block+text[z:])
    accuracy=R/'docs/RESEARCH_ACCURACY_CURRENT.md'
    shutil.copy2(accuracy,S/'before_final_delivery_sync/RESEARCH_ACCURACY_CURRENT.before_final.md')
    accuracy.write_text(f'''## S87当前准确性更新（UTC {stamp}）

以下S80段落是旧截点，本段与RESEARCH_HANDOFF_CURRENT.md优先。S81–S87的实际执行、失败、逐项复核均见各批ROOT_RESULT_ACCEPTANCE与完整主账；没有重新执行全历史。

本批S87六种固定末端处理真实完成24新目标记录，旧S86 16行仅引用；保存量不同作者精确核验通过，全部新图及12页新PDF已实看。末步.75均值0.05116758低于旧多步0.05242222，只否证该单例分数的多步必要性；目标22/孔洞/重影失败保留，NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false。

168页合并逐页等源，4关键页渲染像素等源，没有重新视觉检查全部历史156页。{secondary}

{tail}

---

'''+accuracy.read_text())
    sys.path.insert(0,str(R))
    from scripts.research_log import append_event
    append_event('S87三岗补充完成及最终资料快照封版','独立交付审查、168页零基础阅读地图、PointOdyssey两批有限访问完成；官方入口仍未落实同步小片段。更新七项流程和准确性入口；本次无新增模型/评分。',evidence=[str(S/'FINAL_DELIVERY_SCIENCE_REVIEW.json'),str(S/'NEXT_DATA_ACCESS_CHECK_02.md'),str(S/'WORKFLOW_CHECK_DELIVERY.json')],next_step=check['next_step'],occurred_at=stamp,event_id='S87-packet-final-closure')

    records=[]
    for name in ['NEXT_SCIENTIFIC_DECISION.md','NEXT_DATA_ACCESS_CHECK.md','NEXT_DATA_ACCESS_CHECK_02.md','BEGINNER_READING_MAP_168.md','FINAL_DELIVERY_SCIENCE_REVIEW.json','FINAL_DELIVERY_SCIENCE_REVIEW.md','WORKFLOW_CHECK_DELIVERY.json','MERGED_PDF_COPY_READBACK.json','finalize_report_delivery.py','close_delivery_packet.py']:
        records.append(copy_checked(S/name,P/'完成后交接'/name))
    # Keep initial174-source manifest and old snapshot files unchanged.
    for name in ['pointodyssey_access_01','pointodyssey_access_02']:
        for source in sorted((S/name).rglob('*')):
            if source.is_file(): records.append(copy_checked(source,P/'完成后交接'/name/source.relative_to(S/name)))
    for source in canonical+[accuracy,R/'RESEARCH_LOG.md',R/'research_events.jsonl',R/'workflow_checks.jsonl',R/'AGENTS.md']:
        records.append(copy_checked(source,P/'完成后交接/当前主账快照'/source.name))
    for source in [R/'docs/RESEARCH_PRINCIPLES.md',R/'RESEARCH_PRINCIPLES.md']:
        if source.exists():records.append(copy_checked(source,P/'完成后交接/当前主账快照'/source.name))
    readme=P/'00_从这里开始.md'
    readme.write_text(readme.read_text()+'\n\n完成后补充：请先读[168页零基础阅读地图](完成后交接/BEGINNER_READING_MAP_168.md)。最新主账快照和数据访问失败见`完成后交接/`。初始174份来源COPY_READBACK保持不变，新增及更新入口由SUPPLEMENT_READBACK和FINAL_DELIVERY_INDEX另行登记。\n')
    for path in [readme,B/'00_从这里开始.md',B/'最新连续阅读版/00_先读这里.md']:
        records.append(dict(source='generated navigation at final delivery',destination=str(path),sha256=sha(path),bytes=path.stat().st_size))
    initial=json.loads((P/'COPY_READBACK.json').read_text())
    initial_errors=[]
    for row in initial['files']:
        target=Path(row['target'])
        if sha(target)!=row['sha256'] or target.stat().st_size!=row['bytes']: initial_errors.append(str(target))
    assert not initial_errors,initial_errors
    # Narrow credential-format check; do not claim a complete secret audit.
    patterns=[re.compile(rb'sk-or-v1-[A-Za-z0-9]{20,}'),re.compile(rb'hf_[A-Za-z0-9]{25,}')]
    hits=[]
    for row in records:
        p=Path(row['destination'])
        if p.suffix.lower() in ['.md','.json','.jsonl','.py','.txt','.html','.headers','.body']:
            data=p.read_bytes()
            if any(rx.search(data) for rx in patterns):hits.append(str(p))
    assert not hits,hits
    supplement=dict(status='COPIED_READ_BACK_AND_INITIAL_MANIFEST_RECHECKED',completed_utc=datetime.now(timezone.utc).isoformat(),file_count=len(records),files=records,initial_file_count=len(initial['files']),initial_mismatches=initial_errors,supplement_mismatches=[],credential_format_hits=len(hits),credential_scan_limit='Narrow known OpenRouter/HF credential patterns only, not exhaustive security audit.')
    writej(P/'SUPPLEMENT_READBACK.json',supplement)
    merged=B/'最新连续阅读版/完整汇报_含S87实际结果_168页.pdf'
    report=P/'S87_有限末端对照_实际结果与零基础讲解.pdf'
    final=dict(status='DELIVERED',completed_utc=datetime.now(timezone.utc).isoformat(),packet=str(P),pdfs=[dict(path=str(p),pages=n,bytes=p.stat().st_size,sha256=sha(p)) for p,n in [(merged,168),(report,12)]],initial_manifest=dict(path=str(P/'COPY_READBACK.json'),sha256=sha(P/'COPY_READBACK.json'),files=174),supplement_manifest=dict(path=str(P/'SUPPLEMENT_READBACK.json'),sha256=sha(P/'SUPPLEMENT_READBACK.json'),files=len(records)),acceptances={str(p):sha(p) for p in [S/'ROOT_RESULT_ACCEPTANCE.json',S/'ROOT_VISUAL_ACCEPTANCE.json',S/'result_report/ROOT_REPORT_ACCEPTANCE.json',C/'ROOT_MERGE_ACCEPTANCE.json',S/'FINAL_DELIVERY_SCIENCE_REVIEW.json']},research_status='S87 complete; no method selected or validated; next independent data feasibility unverified',new_science_in_delivery=0,navigation=str(P/'完成后交接/BEGINNER_READING_MAP_168.md'),scope='Initial174 files plus immutable supplements and separately copied168PDF; original history/weights kept in canonical project. This delivery is not wholeproposal completion.')
    writej(S/'FINAL_DELIVERY_INDEX.json',final)
    shutil.copy2(S/'FINAL_DELIVERY_INDEX.json',P/'FINAL_DELIVERY_INDEX.json')
    assert sha(S/'FINAL_DELIVERY_INDEX.json')==sha(P/'FINAL_DELIVERY_INDEX.json')
    print(json.dumps(dict(completed_utc=final['completed_utc'],supplement_files=len(records),initial_rechecked=174,mismatches=0,pdf_pages=[168,12],workflow_gap_minutes=gap,final_index_sha256=sha(S/'FINAL_DELIVERY_INDEX.json')),ensure_ascii=False))
