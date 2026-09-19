#!/usr/bin/env python3
"""Independent manuscript/CSV arithmetic check, without scoring arrays or enumeration."""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal, ROUND_HALF_UP, localcontext
from datetime import datetime,timezone
from collections import Counter
import csv,json,hashlib,re,sys
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
START=now()
source_rel=["docs/S13_RESULTS.md","docs/S13_INDEPENDENT_AUDIT.md","reports/S13/all_24_queries_two_pools.csv","reports/S13/three_strata_two_pools.csv","reports/S13/report_provenance.json","reports/S13/oracle_gap_decomposition.png","reports/S13/oracle_gap_decomposition.svg","reports/S13/oracle_gap_decomposition.pdf","results/S13_independent_audit/verification.json","results/S13_independent_audit/independent_records.json","results/S13_independent_audit/independent_summary.json"]
source_hash={x:sha(ROOT/x) for x in source_rel}
output=OUT/"numeric_check.json"
assert not output.exists()
(OUT/"reviewed_report_snapshot.md").write_bytes((ROOT/"docs/S13_RESULTS.md").read_bytes())
md=(ROOT/"docs/S13_RESULTS.md").read_text()
records=json.loads((ROOT/"results/S13_independent_audit/independent_records.json").read_text())
summary=json.loads((ROOT/"results/S13_independent_audit/independent_summary.json").read_text())
v=json.loads((ROOT/"results/S13_independent_audit/verification.json").read_text())
prov=json.loads((ROOT/"reports/S13/report_provenance.json").read_text())
stats=Counter();errors=[];max_diff=0.0
def check(ok,kind,message):
    stats[kind]+=1
    if not ok: errors.append({"kind":kind,"message":message})
def equal(x,y,kind,loc):
    check(x==y,kind,f"{loc}: {x!r} != {y!r}")
def near(x,y,kind,loc):
    global max_diff
    diff=abs(float(x)-float(y));max_diff=max(max_diff,diff)
    check(diff<=1e-12,kind,f"{loc}: {x!r} != {y!r}, diff {diff}")
def mean(v): return sum(v,Fraction(0))/len(v)
def rounded(f,n=4):
    with localcontext() as c:
        c.prec=90
        return str((Decimal(f.numerator)/Decimal(f.denominator)).quantize(Decimal(10)**-n, rounding=ROUND_HALF_UP))
def strata(r): return "S7_development_4" if r["stage"]=="S7" and r["split"]=="development" else ("S7_test_8" if r["stage"]=="S7" else "S8_test_12")
def ids(a): return " ".join(map(str,a))
def csvread(path):
    with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
expected={};groups={}
for r in records:
    for pool in ["geometry14","pose14"]:
        cur=r["current"][pool]; o=r["oracle"][pool]; all20=r["oracle"]["all20"]
        d=cur["valid_pixels"];c=Fraction(cur["supported_pixels"],d);b=Fraction(o["supported_pixels"],d);a=Fraction(all20["supported_pixels"],d)
        stratum=strata(r)
        e=dict(stratum=stratum,stage=r["stage"],block=r["block"],query=r["query"],pool=pool,
               valid_pixels=d,current_pixels=cur["supported_pixels"],pool_oracle_pixels=o["supported_pixels"],all20_oracle_pixels=all20["supported_pixels"],
               current_support_percent=c*100,pool_oracle_support_percent=b*100,all20_oracle_support_percent=a*100,
               within_pool_hindsight_gap_pp=(b-c)*100,candidate_exclusion_gap_pp=(a-b)*100,total_hindsight_gap_pp=(a-c)*100,
               exact_within_pool_gap_pp=str((b-c)*100),exact_candidate_exclusion_gap_pp=str((a-b)*100),exact_total_gap_pp=str((a-c)*100),
               current_ids=ids(cur["selected"]),pool_oracle_ids=ids(o["selected"]),all20_oracle_ids=ids(all20["selected"]),
               pool_oracle_ties=o["optimal_combination_count"],all20_oracle_ties=all20["optimal_combination_count"],
               current_oracle_intersection=len(set(cur["selected"])&set(o["selected"])),oracle_enforces_nms="False")
        key=(stratum,r["stage"],r["block"],r["query"],pool)
        check(key not in expected,"query_domain","duplicate audit key")
        expected[key]=e;groups.setdefault((stratum,pool),[]).append(e)
        equal((a-c)*100,(b-c)*100+(a-b)*100,"fraction_identity",str(key))
        check(c<b<=a,"strict_headroom",str(key))
        equal(all20["optimal_combination_count"],1,"all20_tie_claim",str(key))
qr=csvread(ROOT/"reports/S13/all_24_queries_two_pools.csv")
equal(len(qr),48,"row_count","per query rows")
keys=[]
for row in qr:
    key=(row["stratum"],row["stage"],int(row["block"]),int(row["query"]),row["pool"]);keys.append(key)
    check(key in expected,"query_domain",str(key))
    if key not in expected:continue
    e=expected[key]
    equal(set(row),set(e),"query_csv_columns",str(key))
    for col,value in e.items():
        if isinstance(value,Fraction):near(row[col],value,"query_csv_numeric",f"{key}/{col}")
        else:equal(row[col],str(value),"query_csv_exact",f"{key}/{col}")
equal(len(set(keys)),48,"query_domain","unique output rows")
equal(set(keys),set(expected),"query_domain","complete output keys")
gr=csvread(ROOT/"reports/S13/three_strata_two_pools.csv")
equal(len(gr),6,"row_count","strata rows")
expected_groups={}
floatcols=["current_support_percent","pool_oracle_support_percent","all20_oracle_support_percent","within_pool_hindsight_gap_pp","candidate_exclusion_gap_pp","total_hindsight_gap_pp"]
for (s,pool),rows in groups.items():
    e={col:mean([r[col] for r in rows]) for col in floatcols}
    e.update(stratum=s,n_queries=len(rows),pool=pool,zero_within_pool_gap_queries=sum(r["within_pool_hindsight_gap_pp"]==0 for r in rows),oracle_ties_min=min(r["pool_oracle_ties"] for r in rows),oracle_ties_max=max(r["pool_oracle_ties"] for r in rows),aggregation="equal query mean; no pooling across strata")
    expected_groups[s,pool]=e
for row in gr:
    key=(row["stratum"],row["pool"]);e=expected_groups[key]
    equal(set(row),set(e),"strata_csv_columns",str(key))
    for col,value in e.items():
        if isinstance(value,Fraction):near(row[col],value,"strata_csv_numeric",f"{key}/{col}")
        else:equal(row[col],str(value),"strata_csv_exact",f"{key}/{col}")
equal({(r["stratum"],r["pool"]) for r in gr},set(expected_groups),"strata_domain","all6")
for s in summary["strata"]:
    sid=s["stratum"]
    equal(s["n_queries"],len(groups[sid,"geometry14"]),"independent_summary","N")
    for pool in ["geometry14","pose14"]:
        e=expected_groups[sid,pool]
        for name,col,mult in [("current_mean","current_support_percent",100),("oracle_mean","pool_oracle_support_percent",100),("headroom_mean_pp","within_pool_hindsight_gap_pp",1)]:
            k=pool+"_"+name
            equal(Fraction(s["exact_fraction_means"][k]),e[col]/mult,"independent_summary_exact",k)
            near(s[k],e[col]/mult,"independent_summary_float",k)
    equal(Fraction(s["exact_fraction_means"]["all20_oracle_mean"]),expected_groups[sid,"geometry14"]["all20_oracle_support_percent"]/100,"independent_summary_exact","all20")
# Parse real printed tables: 21 main numbers and 18 decomposition numbers.
table_lines=[l for l in md.splitlines() if l.startswith("| S")]
main=[l for l in table_lines if "查询 |" in l]
decomp=[l for l in table_lines if "| 来源14 |" in l or "| 姿态14 |" in l]
equal(len(main),3,"printed_table_shape","main")
equal(len(decomp),6,"printed_table_shape","decomposition")
stratum_order=["S7_development_4","S7_test_8","S8_test_12"]
for line,sid in zip(main,stratum_order):
    cells=[x.strip() for x in line.strip("|").split("|")]
    g=expected_groups[sid,"geometry14"];p=expected_groups[sid,"pose14"]
    vals=[g["current_support_percent"],g["pool_oracle_support_percent"],g["within_pool_hindsight_gap_pp"],p["current_support_percent"],p["pool_oracle_support_percent"],p["within_pool_hindsight_gap_pp"],g["all20_oracle_support_percent"]]
    equal(int(re.search(r"(\d+)查询",cells[0]).group(1)),g["n_queries"],"printed_query_count",sid)
    for i,(cell,val) in enumerate(zip(cells[1:],vals)):
        equal(re.sub(r"[% p]","",cell),rounded(val),"printed_main_number",f"{sid}/{i}")
    equal(len(cells[1:]),7,"printed_table_shape",sid)
for line,(sid,pool) in zip(decomp,[(s,p) for s in stratum_order for p in ["geometry14","pose14"]]):
    cells=[x.strip() for x in line.strip("|").split("|")]
    e=expected_groups[sid,pool]
    equal(cells[1],"来源14" if pool=="geometry14" else "姿态14","printed_pool_label",str((sid,pool)))
    for cell,col in zip(cells[2:],["within_pool_hindsight_gap_pp","candidate_exclusion_gap_pp","total_hindsight_gap_pp"]):
        equal(re.sub(r"[% p]","",cell),rounded(e[col]),"printed_decomposition_number",f"{sid}/{pool}/{col}")
    equal(len(cells[2:]),3,"printed_table_shape",str((sid,pool)))
for rel,h in prov["inputs_sha256"].items():equal(sha(ROOT/rel),h,"provenance_hash",rel)
for rel,h in prov["outputs_sha256"].items():equal(sha(ROOT/"reports/S13"/rel),h,"provenance_hash",rel)
equal(sha(ROOT/"scripts/report_s13_oracle_headroom.py"),prov["script_sha256"],"provenance_hash","plot script")
equal(v["verdict"],"PASS_NUMERICAL_WITH_PROTOCOL_DEVIATION_AND_SCOPE_LIMITATIONS","audit_status","verdict")
equal(v["actual_combinations_enumerated"],164328,"audit_status","enumeration count reused")
# SVG text is emitted as text, so rendered labels can be checked directly.
svg=(ROOT/"reports/S13/oracle_gap_decomposition.svg").read_text()
for (sid,pool),e in expected_groups.items():
    label=rounded(e["within_pool_hindsight_gap_pp"],2)+" + "+rounded(e["candidate_exclusion_gap_pp"],2)
    check(label in svg,"figure_numeric_labels",label)
required=["上限没有 NMS","不是已经实现的算法提升","同样选四张不代表相同候选预算或相同计算成本","没有把所有像素拼在一起加权","分解是本轮结果之后追加","不是事前预定的因果实验","未直接绑定","事后复核","原执行只有每池最优摘要","不能用现在的环境补作历史证明","不能成为新方法的未见测试"]
for phrase in required:check(phrase in md,"scope_statement",phrase)
terms=["innovative","pioneering","revolutionary paradigm","transformative framework","superior","surpass","excel","remarkable","unprecedented","achieves sota","breakthrough performance","general-purpose","is capable of","notably","yet","yielding","at its essence","encompass","differentiate","reveal","underscore","exhibit superior capability","exceed","pave the way for","highlight the potential of","profound challenges","stems from","rigid","impede"]
vocab={t:[i for i,l in enumerate(md.splitlines(),1) if t in l.lower()] for t in terms}
vocab={t:lines for t,lines in vocab.items() if lines}
em=[i for i,l in enumerate(md.splitlines(),1) if "—" in l]
post={x:sha(ROOT/x) for x in source_rel}
equal(source_hash,post,"input_unchanged","all manuscript inputs")
result={"schema":"s13-manuscript-numeric-review-v1","status":"PASS" if not errors else "FAIL","started_utc":START,"completed_utc":now(),
"reviewer":"research_novelty_routes, different from report author and S13 independent array auditor",
"scope":"Checks manuscript/CSV arithmetic from saved audited integers only; no NPZ, enumeration, model, renderer, NMS, raw image or GT access.",
"inputs_sha256":source_hash,"post_inputs_sha256":post,"script_sha256":sha(Path(__file__)),"counts":dict(stats),"check_count":sum(stats.values()),"errors":errors,"max_numeric_difference_percent_or_pp":max_diff,"fixed_csv_float_atol":1e-12,
"comparison_rules":"IDs, integers, exact fractions, column domains and hashes exact. CSV floats abs1e-12. Printed numbers Decimal rounded half-up from integer ratios.",
"printed_values":{"main_table":21,"decomposition_table":18,"decomposition_table_note":"Actual manuscript has six rows and three numeric columns, not 24 printed values; all six query counts also checked in CSV."},
"vocabulary_scan":{"scope":"entire reviewed S13_RESULTS.md","hits":vocab,"em_dash_lines":em},"figure_text_labels_checked":6,
"role_limit":"This is independently authored manuscript review. The scientific scoring evidence reuses another auditor's saved records; it is not another bottom-level experiment audit."}
output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"status":result["status"],"checks":result["check_count"],"counts":dict(stats),"errors":errors,"max_difference":max_diff},ensure_ascii=False,indent=2))
sys.exit(bool(errors))

