"""Resume after supplement copy, without repeating ledger/workflow mutations."""
from finalize_report_delivery import R,S,B,P,C,sha,writej
from pathlib import Path
from datetime import datetime, timezone
import json,shutil,re,sys

assert not (S/'FINAL_DELIVERY_INDEX.json').exists()
initial=json.loads((P/'COPY_READBACK.json').read_text())
for row in initial['files']:
    p=Path(row['target'])
    assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
sys.path.insert(0,str(R))
from scripts.research_log import append_event
append_event('S87最终资料索引记录脚本修复','补充资料已复制后，在174初始文件复核处因缺Path导入停止；未生成最终索引。原脚本和失败已封存，现复核初始174哈希/字节全部一致，恢复补充清单与最终索引生成，不重复科研或七项检查。',evidence=[str(S/'DELIVERY_COPY_RECOVERY.json'),str(S/'delivery_attempt_01/close_delivery_packet.py')],next_step='保存修复后的主账快照与最终交付索引。',event_id='S87-delivery-index-recovery')
records=[]
def copy_final(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists() and sha(src)!=sha(dst):
        backup=S/'delivery_attempt_01/copied_before_recovery'/dst.relative_to(P)
        backup.parent.mkdir(parents=True,exist_ok=True)
        assert not backup.exists()
        shutil.copy2(dst,backup)
    shutil.copy2(src,dst)
    assert sha(src)==sha(dst)
    records.append(dict(source=str(src),destination=str(dst),sha256=sha(dst),bytes=dst.stat().st_size))
names=['NEXT_SCIENTIFIC_DECISION.md','NEXT_DATA_ACCESS_CHECK.md','NEXT_DATA_ACCESS_CHECK_02.md','BEGINNER_READING_MAP_168.md','FINAL_DELIVERY_SCIENCE_REVIEW.json','FINAL_DELIVERY_SCIENCE_REVIEW.md','WORKFLOW_CHECK_DELIVERY.json','MERGED_PDF_COPY_READBACK.json','finalize_report_delivery.py','close_delivery_packet.py','resume_delivery_index.py','DELIVERY_COPY_RECOVERY.json']
for name in names: copy_final(S/name,P/'完成后交接'/name)
copy_final(S/'delivery_attempt_01/close_delivery_packet.py',P/'完成后交接/首次索引脚本失败/close_delivery_packet.py')
for name in ['pointodyssey_access_01','pointodyssey_access_02']:
    for source in sorted((S/name).rglob('*')):
        if source.is_file():copy_final(source,P/'完成后交接'/name/source.relative_to(S/name))
sources=[R/'RESEARCH_MEMORY.md',R/'docs/RESEARCH_HANDOFF_CURRENT.md',R/'docs/PROPOSAL_PROGRESS_CURRENT.md',R/'docs/PROJECT_DELIVERY_TRACKER.md',S/'CONTINUE_HERE.md',R/'docs/RESEARCH_ACCURACY_CURRENT.md',R/'RESEARCH_LOG.md',R/'research_events.jsonl',R/'workflow_checks.jsonl',R/'AGENTS.md',R/'RESEARCH_PRINCIPLES.md']
for source in sources:copy_final(source,P/'完成后交接/当前主账快照'/source.name)
for p in [P/'00_从这里开始.md',B/'00_从这里开始.md',B/'最新连续阅读版/00_先读这里.md']:
    records.append(dict(source='generated navigation during delivery',destination=str(p),sha256=sha(p),bytes=p.stat().st_size))
patterns=[re.compile(rb'sk-or-v1-[A-Za-z0-9]{20,}'),re.compile(rb'hf_[A-Za-z0-9]{25,}')]
for row in records:
    p=Path(row['destination'])
    if p.suffix.lower() in ['.md','.json','.jsonl','.py','.txt','.html','.headers','.body']:
        assert not any(rx.search(p.read_bytes()) for rx in patterns),str(p)
    assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
supplement=dict(status='COPIED_READ_BACK_AND_INITIAL_MANIFEST_RECHECKED',completed_utc=datetime.now(timezone.utc).isoformat(),file_count=len(records),files=records,initial_file_count=len(initial['files']),initial_mismatches=[],supplement_mismatches=[],credential_format_hits=0,credential_scan_limit='Narrow known OpenRouter/HF credential patterns only, not exhaustive security audit.',recovery_record_sha256=sha(S/'DELIVERY_COPY_RECOVERY.json'))
writej(P/'SUPPLEMENT_READBACK.json',supplement)
merged=B/'最新连续阅读版/完整汇报_含S87实际结果_168页.pdf';report=P/'S87_有限末端对照_实际结果与零基础讲解.pdf'
final=dict(status='DELIVERED',completed_utc=datetime.now(timezone.utc).isoformat(),packet=str(P),pdfs=[dict(path=str(p),pages=n,bytes=p.stat().st_size,sha256=sha(p)) for p,n in [(merged,168),(report,12)]],initial_manifest=dict(path=str(P/'COPY_READBACK.json'),sha256=sha(P/'COPY_READBACK.json'),files=174),supplement_manifest=dict(path=str(P/'SUPPLEMENT_READBACK.json'),sha256=sha(P/'SUPPLEMENT_READBACK.json'),files=len(records)),acceptances={str(p):sha(p) for p in [S/'ROOT_RESULT_ACCEPTANCE.json',S/'ROOT_VISUAL_ACCEPTANCE.json',S/'result_report/ROOT_REPORT_ACCEPTANCE.json',C/'ROOT_MERGE_ACCEPTANCE.json',S/'FINAL_DELIVERY_SCIENCE_REVIEW.json']},research_status='S87 complete; no method selected or validated; independent data feasibility unverified',new_science_in_delivery=0,navigation=str(P/'完成后交接/BEGINNER_READING_MAP_168.md'),scope='Initial174 files plus supplements and separately copied168PDF; all original history/weights kept in canonical project. Current ledger snapshots include delivery recovery event. Not wholeproposal completion.')
writej(S/'FINAL_DELIVERY_INDEX.json',final)
shutil.copy2(S/'FINAL_DELIVERY_INDEX.json',P/'FINAL_DELIVERY_INDEX.json')
assert sha(S/'FINAL_DELIVERY_INDEX.json')==sha(P/'FINAL_DELIVERY_INDEX.json')
print(json.dumps(dict(completed_utc=final['completed_utc'],supplement_files=len(records),initial_rechecked=174,mismatches=0,pdf_pages=[168,12],final_index_sha256=sha(S/'FINAL_DELIVERY_INDEX.json')),ensure_ascii=False))
