"""Write report from completed independent receipt; no selector/renderer imports."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'results/S12_matched_budget'
AUDIT=ROOT/'results/S12_matched_budget_independent_audit'
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
v=read(AUDIT/'verification.json')
assert v['status']=='PASS'
m=read(RUN/'run_metadata.json')
f=read(ROOT/v['freeze_path'])
now=datetime.now(timezone.utc).isoformat()
source=ROOT/'scripts/run_s12_matched_budget.py'
tree=ast.parse(source.read_text())
source_spans={n.name:[n.lineno,n.end_lineno] for n in tree.body if isinstance(n,ast.FunctionDef)
              and n.name in ('archive','load_prediction_inputs','make_selections','score_after_seal','execute')}
artifacts={str(p.relative_to(ROOT)):sha(p) for p in sorted(AUDIT.iterdir()) if p.is_file()}
actual_metadata={str(RUN.joinpath(n).relative_to(ROOT)):sha(RUN/n) for n in (
    'run_metadata.json','summary.json','records.json','selection_seal.json','distance_calls.jsonl',
    'initial_thresholds.json','old_scoring_reproduction.json','scoring_array_identities.json',
    'extraction_identity.json','post_run_integrity.json')}
names={('S7','development'):'S7 开发',('S7','test'):'S7 测试',('S8','test'):'S8 测试'}
table=[]
for r in v['main_strata']:
    table.append(f"| {names[r['stage'],r['split']]} | {r['n_queries']} | {100*r['geometry14_mean_support']:.6f}% | {100*r['pose14_mean_support']:.6f}% | {r['geometry14_minus_pose14_mean_pp']:+.9f} | {r['geometry_higher']}/{r['pose_higher']}/{r['equal']} | {r['selected_set_changed']}/{r['n_queries']} | {r['pose14_same_order_as_all20_nms']}/{r['n_queries']} |")
text=f'''# S12 同候选数量诊断：不同作者独立结果审计

结论：**PASS，首轮执行通过，无失败或事后放宽检查门。** 本审计验证实际保存结果及其可重算性，未调用生产 runner、validator、选择器、renderer 或模型。准备阶段仅解析审计器语法；根任务明确通知实际实验完成之后才读取 S12 新结果并运行独立审计。

报告记录时间 UTC `{now}`。实际独立审计 UTC `{v['started_utc']}` 至 `{v['completed_utc']}`。审计器为 `scripts/verify_s12_matched_budget.py`，SHA-256 `{v['auditor_sha256']}`；同一首版源码在读取新结果前已报根任务，并原样复制为审计目录的 `auditor_snapshot.py`。本次没有修改原实验、冻结协议、既有输入或实际结果。

## 核查覆盖

共 **{v['check_count']} 个显式检查门**通过；计数是本审计器的字段/整数组/身份检查门数，不是独立样本数，也不与此前按不同粒度计数的审计比较。

| 对象 | 独立处理与结果 |
|---|---|
| 原始输入 | 76 文件逐 SHA 对冻结表、运行表及当前原文件，运行前后不变；包含 12 份位姿 NPZ、12 份原选择 JSON、48 份支持/有效掩码 NPZ 与 4 份旧元数据/记录 |
| 源码与前审 | 4 个执行源码、9 个前审/来源证据、协议和执行冻结全部 SHA 一致；5 个实际抽取函数逐 AST、源码区间及哈希与固定原源码一致，仅解析而未执行这些函数 |
| 两个 ZIP | 输入 ZIP 76 成员；源码/证据 ZIP 15 成员（4+9+协议+冻结），共 91 成员独立重开，逐成员校验 CRC、SHA、字节数、名单/顺序、安全相对路径及 manifest，两个整包 SHA 一致 |
| 位姿与初阈值 | 6 块独立位姿，双 stride 的 12 份保存位姿逐 bytes 相同；逐块前 5 帧 10 对距离的第 6 小值重建，6 个阈值一致 |
| 新选择 | 24 查询从原位姿独立重建全 20 距离、FP32 排序及前 14 候选；按 ID 升序各配额 1。全部无 FP32 距离并列，候选与保存值一致 |
| 实际距离日志 | 共 {v['distance_calls_independently_evaluated']} 条。逐调用编号、阶段、标签、平移权重、两端实际矩阵列表及 bytes 身份核对；以独立 FP64 方程计算全部返回值，精确一致 |
| 新 NMS | 根据独立方程逐次访问及短路回放所有距离比较、严格阈值、放宽步骤和后备顺序；24 份完整 trace（含全部 steps、距离、顺序、最终 ID）一致，均为 4 个不同且合法候选 ID |
| 支持整数 | 重开 48 份原 support/valid 数组，逐份身份一致；同查询两档 stride 的数组 bytes 相同。独立逐帧 OR 后与 valid 相交，复算全部 768 旧读出、48 全 20 张支持上界及 24 个新选择的整数分子/分母 |
| 配对与统计 | 192 配对所有字段、24 个分层汇总行、48 个块汇总行一致；检查正负/不变、候选交集、集合/有序 ID 变化及与原 all20 NMS 是否同序 |
| 时序及只读性 | 24 选择和阈值/距离日志共 26 文件的 seal 全部哈希一致；冻结→运行→24 选择→seal→评分标记→完成符合保存记录，整个审计前后实际结果及输入/源码哈希未变 |

支持计算采用 `count((OR selected support) AND valid) / count(valid)`；先为每个查询计算，再以固定查询数取算术均值，未拼接各查询像素分母。原 S7 记录未保存逐读出整数分子，因此先从原掩码重建整数，再精确核其旧比例；S8 同时精确核旧比例和已存整数分子。新记录均逐整数和比例核验。

24 新选择被 8 个地图/stride 组合复用为 192 配对条件；不是 192 次新选择或独立查询。旧 768 分对应 48 个案例查询条件（含 stride）×4 种地图×4 读出；48 个全 20 张支持上界另列，不能当成只取 4 张的原 `all20_nms`。

## 独立算术与预定门限

审计仅使用 NumPy、SciPy 的旋转转换及 Torch 的标量矩阵/距离、FP32 `argsort` 运算。环境核为 Python {v['numerical_versions']['python']}、NumPy {v['numerical_versions']['numpy']}、Torch {v['numerical_versions']['torch']}、SciPy {v['numerical_versions']['scipy']}，CPU。没有执行模型。

对每个查询独立构造固定 Y/Z 轴翻转、单相机四元数归一化路径。距离按下式独立计算，而非调用原 `geodesic_distance`：

`d(P,Q) = acos((clip(trace(RpᵀRq), −1, 3) − 1) / 2) + 0.1 × ||tp − tq||₂`。

所有实际距离返回值、输入 bytes、FP32 排序、完整 NMS 轨迹、整数、ID 与旧比例均为精确比较。仅独立采用整数差算百分点、`math.fsum` 算均值时，因运算顺序不同，用结果前已固定的绝对容差 `1e-12`；实际最大差 `{v['max_derived_float_difference']:.17g}`，未修改容差。

## 主设置结果的独立复算

主设置保持 **A0P0、stride 8**。差值为“几何来源投票筛 14 − 预测姿态近邻筛 14”，单位为百分点；正数表示几何来源方案的支持代理更高。两者候选数量同为 14、输出同为 4，并使用同一 NMS 规则。

| 分层 | 查询数 | 几何14 | 姿态14 | 差值（pp） | 几何高/姿态高/相同 | 集合变化 | 姿态14与原all20 NMS同序 |
|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(table)}

S7 测试差值 −2.338960684 pp，而 S8 测试 +4.382919665 pp。S7 主测试中，4 个支持发生变化的查询均为姿态14更高，另 4 查询同分且同选图；S8 11 查询几何14更高、1 查询姿态14更高。主设置的集合变化数与有序列表变化数相同，没有只换顺序而集合不变的主例。不能将跨查询正负平均解释为同一查询的机制抵消。

全部预定分层与块统计保存在 `results/S12_matched_budget_independent_audit/independent_summary.json`，192 行完整字段在 `independent_records.json`。其余地图和 stride 12 为预定敏感性条件，不替换上述主设置。两个数据阶段分别报告，未混成一个总均值或作显著性检验。

## 封存与时序证据边界

| 事件 | 保存的 UTC |
|---|---|
| 执行冻结 | {f['frozen_utc']} |
| 实际运行开始 | {v['run_started_utc']} |
| 全部选择封存 | {v['selection_sealed_utc']} |
| 首次 support/valid 字段解码前标记 | {v['scoring_decode_marker_utc']} |
| 实际运行完成 | {v['run_completed_utc']} |

源码 `execute` 在 `make_selections` 返回且更新 seal 后才调用 `score_after_seal`；`make_selections` 不解码评分数组，`score_after_seal` 写下首次解码前标记后才取出 support/valid。此前归档会读取/复制 NPZ **原始文件 bytes**，因此“封存后评分”不等于此前未读取任何该文件字节。这里的依据是已绑定源码的控制流、实际日志/时间与封存内容，**不是 OS 文件访问追踪或从头重放系统调用**。

逐函数静态位置见配套 JSON 的 `runner_source_spans`；该源码身份为 `{v['execution_source_sha256']['scripts/run_s12_matched_budget.py']}`。实际流程从固定原源码抽取并执行记录型 `decision_trace` 24 次；不是调用 24 次完整原 VMem `get_context_info`。本独立审计连该抽取函数也未执行，只独立复算保存行为。

## 能支持与不能支持的结论

可支持：这次已见查询诊断中，固定候选数量、输出数量和 NMS 后，候选形成策略仍改变了最终选择及支持代理；效果在 S7 与 S8 主测试分层方向不同。该结果可用于约束候选筛选的作用判断。

不能支持：几何信息普遍有益/有害、姿态14是“无几何”控制、新场景泛化、新独立样本、训练未见保证、真实生成视频质量、更快性能或新的算法贡献。S7/S8 均为本研究已查看的既有查询，本审计没有重做原 RGB/depth/GT 测量、地图构建、渲染、历史全实验或完整视频。原封存支持掩码沿用既有证据，本轮只对其保存 bytes 与整数计算负责。C0 普通覆盖贪心没有在本轮运行；该诊断与 C0 的新颖性拒绝判断、已停止的缓存候选 B 分开。

## 固定身份与产物

- 执行冻结 SHA-256：`{v['freeze_sha256']}`。
- 协议 SHA-256：`{v['protocol_sha256']}`。
- 实际 summary SHA-256：`{actual_metadata['results/S12_matched_budget/summary.json']}`。
- 输入 ZIP SHA-256：`{m['archives']['inputs']['sha256']}`；2,953,961 bytes、76 成员。
- 源码 ZIP SHA-256：`{m['archives']['sources']['sha256']}`；68,130 bytes、15 成员。
- 审计目录：`results/S12_matched_budget_independent_audit/`；回执 `verification.json`，独立重建 `independent_traces.json`、`independent_records.json`、`independent_summary.json`，实际结果全文件 SHA 表 `audited_result_sha256.json`。
- 配套 `docs/S12_MATCHED_BUDGET_INDEPENDENT_AUDIT.json` 绑定本文与全部审计产物 SHA。检查门分类数、实际时点、冻结源码身份均保留原回执，不与数据样本量混同。
'''
md=ROOT/'docs/S12_MATCHED_BUDGET_INDEPENDENT_AUDIT.md'
assert not md.exists()
md.write_text(text)
report={
 'schema':'s12-matched-budget-independent-audit-report-v1','status':'PASS',
 'recorded_utc':now,'first_attempt_pass':True,'auditor_prepared_before_new_result_access':True,
 'no_production_function_import_or_execution':True,'no_renderer_or_model':True,'no_original_result_mutation':True,
 'audit_receipt':v,'archives':m['archives'],'archive_total_members':91,
 'review_evidence_sha256':f['review_evidence_sha256'],'runner_source_spans':source_spans,
 'chronology_basis':'Pinned source order and saved metadata/seal; not OS file-access tracing or syscall replay. Raw NPZ file bytes were copied before seal; named scoring arrays decoded afterward.',
 'inference_scope':'Existing seen-query exploratory support proxy. Same candidate/output counts and NMS; effects are stage-specific. No video, speed, training-unseen, independent-query or novelty claim.',
 'audit_artifact_sha256':artifacts,'actual_result_core_sha256':actual_metadata,
 'report_md_sha256':sha(md),
}
js=ROOT/'docs/S12_MATCHED_BUDGET_INDEPENDENT_AUDIT.json'
assert not js.exists()
js.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps({'recorded_utc':now,'md_sha256':sha(md),'json_sha256':sha(js),'verification_sha256':sha(AUDIT/'verification.json')},indent=2))
