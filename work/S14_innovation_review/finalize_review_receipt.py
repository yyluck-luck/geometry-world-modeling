from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,re
ROOT=Path("/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling")
BASE=ROOT/"work/S14_innovation_review"
report=ROOT/"docs/S14_INNOVATION_CANDIDATES_REVIEW.md"
skills=[Path("/Users/rocket/.claude/skills/sci-scientific-brainstorming/SKILL.md"),Path("/Users/rocket/.codex/skills/idea-evaluator/SKILL.md")]
skills += [Path("/Users/rocket/.codex/skills/idea-evaluator/references")/f for f in ["fatal-flaws.md","lifecycle-capability-matching.md","five-dimensions.md","paradigm-shift-probe.md"]]
def item(p): return {"path":str(p),"resolved":str(p.resolve()),"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
downloads=json.loads((BASE/"source_download_receipt.json").read_text())
assert len(downloads["records"])==7
for r in downloads["records"]:
    assert r["status"]=="saved"
    assert hashlib.sha256((BASE/r["name"]).read_bytes()).hexdigest()==r["sha256"]
text=report.read_text()
for marker in ["S13数值","Accept with Revisions","同14候选信息预算","独立同分布","查询RGB","循环论证","未执行"]:
    assert marker in text,marker
local_targets=re.findall(r"\]\((\.\.?/[^)#]+)(?:#[^)]*)?\)",text)
missing=[t for t in local_targets if not (report.parent/t).exists() and not t.endswith("review_receipt.json")]
assert not missing, missing
receipt={"schema":"s14-innovation-review-receipt-v1","status":"COMPLETED_CANDIDATE_REVIEW_NO_EXPERIMENT",
"completed_utc":datetime.now(timezone.utc).isoformat(),
"first_clock_observed_utc":"2026-09-06 03:16:26 UTC",
"timing_note":"First clock is before the first search and after initial reading, not the task start. Download times are actual receipt timestamps. No experiment time or student hours inferred.",
"candidate_verdicts":{"C1":"Accept with Revisions; prerequisite diagnostics only","C2":"Accept with Revisions; backup prerequisite diagnostic"},
"search_queries":12,"keyword_groups":3,"direct_neighbor_papers":5,"background_papers":2,"primary_snapshots":7,
"experiments_run":0,"models_called":0,"claude_model_or_cli_calls":0,"new_selection_decisions":0,
"s13_scoring_array_reads":0,"independent_review_status":"NOT_YET_REVIEWED_BY_ANOTHER_AUTHOR",
"skill_files_read":[item(p) for p in skills],
"report":item(report),"evidence_files":[item(p) for p in sorted(BASE.iterdir()) if p.is_file()],
"source_identity_note":"Hashes are current output identities at receipt time, not a claim of OS access history.",
"known_corrections":["MVS author order corrected from search bibliography to agreement of author PDF and official COLMAP citation.","DOI, author-PDF, LTT-PDF and CVF browser failures preserved; successful alternate primary-source reads documented."],
"boundary":"No general novelty proof, no fresh held-out evidence, no safe deployment or video improvement claim. Parent must record completion in canonical research_events ledger."}
out=BASE/"review_receipt.json"
assert not out.exists()
out.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"report_sha256":receipt["report"]["sha256"],"report_bytes":receipt["report"]["bytes"],"evidence_files":len(receipt["evidence_files"]),"completed_utc":receipt["completed_utc"],"status":receipt["status"]},ensure_ascii=False,indent=2))

