from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import collections, hashlib, json, subprocess

out = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S23_supervisor_readthrough')
repo = Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/Supervisor-Skills')
root = out.parent.parent
stamp = datetime.now(timezone.utc)
commit = '207bc6f7a1aa107e544099c2c7cc86816fba9628'
reference_reads = {
    'idea-evaluator': ['fatal-flaws', 'lifecycle-capability-matching', 'five-dimensions', 'paradigm-shift-probe', 'paradigm-first-principles', 'paradigm-elephant', 'paradigm-technology-cycle', 'paradigm-hamming'],
    'tech-paper-template': ['thinking-template', 'consistency-checks', 'paper-types'],
    'benchmark-paper-template': ['experiments', 'gap-analysis', 'benchmark-design'],
    'deep-research': ['search-strategy', 'citation-protocol', 'quality-gates', 'self-adversarial', 'synthesis-framework', 'hedge-calibration'],
    'vibe-research-workflow': ['behavior-guidelines', 'vibe-coding', 'tool-selection'],
    'figure-designer': ['experimental-results', 'motivated-example', 'design-rules'],
    'paper-writer': ['evidence-discipline', 'verification-ladder'],
}
ref_paths = {f'skills/{skill}/references/{name}.md' for skill, names in reference_reads.items() for name in names}
skill_paths = {str(p.relative_to(repo)) for p in (repo/'skills').glob('*/SKILL.md')}
handbook_paths = {str(p.relative_to(repo)) for p in (repo/'handbook').rglob('*.md')}
full_text_paths = ref_paths | skill_paths | handbook_paths | {'README.md'}
pdf_path = 'handbook/01_Preliminary/博士生科研入门辅导.pdf'
assert len(ref_paths) == 28, len(ref_paths)
assert len(skill_paths) == 12, len(skill_paths)
assert len(handbook_paths) == 18, len(handbook_paths)
assert len(full_text_paths) == 59, len(full_text_paths)

def sha(data): return hashlib.sha256(data).hexdigest()
def digest(path): return sha(Path(path).read_bytes())

tracked = subprocess.run(['git', '-C', str(repo), 'ls-tree', '-r', '-z', commit], check=True, capture_output=True).stdout.split(b'\0')
entries = []
for item in tracked:
    if not item: continue
    meta, raw_path = item.split(b'\t', 1)
    mode, typ, object_id = meta.decode().split(' ')
    rel = raw_path.decode()
    local = repo/rel
    entry = {'path': rel, 'git_mode': mode, 'git_type': typ, 'git_object_id': object_id, 'inventory_seen': True,
             'content_read': False, 'status': 'index_only_content_not_read', 'source_attribution': f'https://github.com/HKUSTDial/Supervisor-Skills/blob/{commit}/{rel}'}
    if rel in full_text_paths or rel == pdf_path:
        content = local.read_bytes()
        computed_blob = hashlib.sha1(f'blob {len(content)}\0'.encode()+content).hexdigest()
        assert computed_blob == object_id, rel
        entry.update({'content_read': True, 'byte_size': len(content), 'sha256': sha(content), 'local_matches_pinned_git_blob': True,
                      'reading_timestamp': None, 'reading_timestamp_note': 'Exact per-file read times were not separately logged. All declared reads occurred before this manifest was written.'})
        if rel == pdf_path:
            entry.update({'status': 'full_body_text_and_all_pages_visual_review', 'category': 'chinese_handbook_pdf', 'pages': 70,
                          'visual_scope': 'All 70 full slides viewed at original rendered size in 18 contact sheets; embedded original-paper screenshots are illustrative, not independent full-paper reviews.'})
        else:
            category = 'skill_entry' if rel in skill_paths else 'chinese_handbook_markdown' if rel in handbook_paths else 'selected_reference' if rel in ref_paths else 'root_readme'
            entry.update({'status': 'full_text_read', 'category': category, 'line_count': len(content.decode().splitlines())})
    else:
        entry['category'] = 'unread_english_handbook' if rel.startswith('handbook-en/') else 'unread_reference' if '/references/' in rel else 'unread_image_asset' if local.suffix.lower() in {'.png','.jpg','.jpeg','.webp'} else 'unread_other'
        entry['unread_reason'] = 'Outside the bounded readthrough of every SKILL.md, Chinese handbook body, and selected project-relevant references; filename inventory only.'
    entries.append(entry)
assert full_text_paths | {pdf_path} <= {e['path'] for e in entries}

page_pngs = sorted((out/'pdf').glob('page-*.png'))
contact_sheets = sorted((out/'pdf').glob('contact_*.png'))
assert len(page_pngs) == 70, len(page_pngs)
assert len(contact_sheets) == 18, len(contact_sheets)

required_fields = [
    {'id': 'important_failure', 'question_zh': '强基线在哪个必要条件下失败，该失败为何影响原 proposal？', 'evidence': ['real input identity and timestamps', 'complete relevant curves', 'failure definition', 'downstream consequence or explicitly untested consequence']},
    {'id': 'falsifiable_hypothesis', 'question_zh': '修改何对象、用何允许信息、通过何机制改善何输出，何时应无效？', 'evidence': ['one-sentence mechanism hypothesis', 'predicted positive and null conditions']},
    {'id': 'nearest_prior_art', 'question_zh': '最近 3–5 个近邻工作的机制与本候选有何差别？', 'evidence': ['primary paper or official code', 'location and retrieval receipt', 'object/mechanism/input-granularity/setting comparison'], 'warning': 'Search not finding a duplicate does not establish firstness; never invent 3-5 citations to satisfy a count.'},
    {'id': 'mechanism_difference', 'question_zh': '去掉新部件退化成什么，何种简单替代解释可能同样有效？', 'evidence': ['state/action/formula/interface difference', 'simple competing explanation or matched null control']},
    {'id': 'legal_inputs', 'question_zh': '推理信息在当时是否可得，是否使用 GT、未来帧或测试标签？', 'evidence': ['input allowlist', 'causal timing', 'GT scoring boundary', 'oracle label where applicable']},
    {'id': 'minimal_discriminating_test', 'question_zh': '哪个最低成本干预可以区分本机制与替代解释？', 'evidence': ['hypothesis', 'comparison', 'variables', 'controls', 'metrics', 'pre-run selection rule', 'stop conditions']},
    {'id': 'fairness_and_completeness', 'question_zh': '基线、预算和精度适配是否公平，是否保留所有冻结条件及失败？', 'evidence': ['source version', 'manifest', 'patch', 'compatibility receipt', 'runtime and memory', 'all frozen outcomes including failures and nulls']},
    {'id': 'decision', 'question_zh': '结果支持、否定或尚不能判定什么，下一步为何值得做？', 'evidence': ['continue/revise/reject/defer', 'reason tied to evidence', 'preserved rejected versions']},
    {'id': 'local_feasibility_and_downstream', 'question_zh': '本地先执行什么，如何接回几何相关指标和生成消费者？', 'evidence': ['local command or experiment interface', 'resource limit', 'integration path', 'unresolved generation dependency']},
    {'id': 'independent_confirmation', 'question_zh': '如何避免在已见场景上选条件并把它当盲测？', 'evidence': ['exploration/confirmation split', 'frozen rule', 'independent-condition plan or actual receipt']},
]
gates = {
    'schema_version': '1.0', 'recorded_at_utc': stamp.isoformat(), 'recorded_at_asia_shanghai': stamp.astimezone(ZoneInfo('Asia/Shanghai')).isoformat(),
    'source_commit': commit, 'applies_to': 'Each of five logical innovation routes; actual concurrent execution remains resource-limited.',
    'route_template': {'route_id': None, 'author_agent': None, 'created_at_utc': None, 'hypothesis_version': None, 'status': 'proposed_unvalidated',
                       'required_fields': {item['id']: None for item in required_fields}},
    'field_definitions': required_fields,
    'gate_order': [
        {'id':'G0', 'name':'Observed problem and hypothesis', 'advance_if':'Real condition and important failure are identified, or an explicit plan will test whether the hypothesized failure exists.', 'cannot_claim':'A residual by itself proves memory failure or generated-video degradation.'},
        {'id':'G1', 'name':'Prior-art and fatal-flaw audit', 'advance_if':'Mechanism difference is precise and no unrepairable flaw, known direct duplicate, or current data-refuted premise invalidates this version.', 'cannot_claim':'A favorable self-score proves novelty or top-venue quality.'},
        {'id':'G2', 'name':'Frozen minimal discriminating experiment', 'advance_if':'Inputs, comparison, control, metric, decision and stop conditions are committed before new test execution.', 'cannot_claim':'Previously inspected TUM results are blinded confirmation.'},
        {'id':'G3', 'name':'Real mechanism evidence', 'advance_if':'Actual runs distinguish the proposed mechanism from key simpler explanations with transparent costs, nulls, and scope.', 'cannot_claim':'A local geometry gain equals full generative-system improvement.'},
        {'id':'G4', 'name':'Generalization and proposal integration', 'advance_if':'Claim-matched independent conditions and the relevant generation consumer confirm utility, with strongest nearby baselines and complete evidence.', 'cannot_claim':'Internal gate passage guarantees external acceptance or an advisor response.'},
    ],
    'decision_enum': ['continue', 'revise', 'reject', 'defer'],
    'decision_rules': {
        'fatal_flaw_rule':'Use evidence and repairability, not the contradictory upstream automatic MAJOR-count rule.',
        'untested_rule':'An untested but coherent candidate may proceed to a low-cost falsifier; untested does not mean disproven.',
        'rejected_rule':'Do not revive a rejected mechanism by renaming it. A materially changed premise requires an explicit version and new test.',
        'replication_rule':'Repeat where randomness, sampling, or relevant noise can affect conclusions; do not mechanically repeat deterministic runs.',
        'failure_rule':'Preserve failed runs and missing/null data; never relabel synthetic or oracle results as real deployable improvement.',
        'permissions_rule':'The user authorized local research. Do not add approval gates inferred from vague skill wording; do not claim personal user comprehension, hours, or endorsement.',
    },
    'project_state_cutoff_utc':'2026-09-06T13:45:05.014983+00:00',
    'shared_baseline_context':{'existing_methods':['CUT3R','TTT3R','FILT3R'], 'data':'Previously seen TUM fr2_desk 300-frame segment', 'generation_completed':False, 'project_new_method_established':False, 'independent_author_metric_audit_completed':False},
}
(out/'five_route_acceptance.json').write_text(json.dumps(gates, ensure_ascii=False, indent=2)+'\n')

context_files = [root/'AGENTS.md', root/'RESEARCH_PRINCIPLES.md', root/'RESEARCH_MEMORY.md', root/'RESEARCH_LOG.md', root/'docs/S21_RESULTS.md', root/'docs/S22_RESULTS.md', root/'docs/PAPER_LOGIC_CURRENT.md', root/'vendor/provenance.json', repo.parent/'Yiyang_LIU_Proposal.txt']
context = []
for path in context_files:
    assert path.exists(), str(path)
    context.append({'path': str(path), 'scope': 'newest approximately 100 lines read' if path.name=='RESEARCH_LOG.md' else 'full text read', 'sha256_at_manifest_time': digest(path), 'note':'Context may be updated concurrently by root; status conclusions in audit use the explicit S22 reporting cutoff.'})
external_skill = Path('/Users/rocket/.codex/plugins/cache/openai-primary-runtime/pdf/26.904.11930/skills/pdf/SKILL.md')
manifest = {
    'schema_version':'1.0', 'agent':'/root/supervisor_full_readthrough',
    'recorded_at_utc':stamp.isoformat(), 'recorded_at_asia_shanghai':stamp.astimezone(ZoneInfo('Asia/Shanghai')).isoformat(),
    'source':{'repository':'https://github.com/HKUSTDial/Supervisor-Skills', 'requested_branch_url':'https://github.com/HKUSTDial/Supervisor-Skills/tree/main', 'local_clone':str(repo), 'pinned_commit':commit, 'remote_verification_receipt':'remote_verification.json', 'local_installed_skill_comparison':'installed_skill_parity.json', 'online_github_page_opened':True},
    'scope':{'all_skill_entries_read':True, 'all_chinese_handbook_markdown_read':True, 'all_chinese_handbook_pdf_body_read':True, 'all_chinese_handbook_pdf_pages_visually_reviewed':True, 'all_repository_files_read':False, 'all_references_read':False, 'english_handbook_read':False, 'standalone_image_assets_visually_reviewed':False, 'original_papers_embedded_or_linked_in_handbook_independently_read':False},
    'counts':{'tracked_files':len(entries), 'full_text_markdown':len(full_text_paths), 'skill_entries':len(skill_paths), 'chinese_handbook_markdown':len(handbook_paths), 'selected_references':len(ref_paths), 'root_readme':1, 'pdf_full_text_and_visual':1, 'pdf_pages':70, 'full_text_or_pdf_content_read':60, 'index_only_content_not_read':sum(not e['content_read'] for e in entries)},
    'status_definitions':{'full_text_read':'Complete local text read by agent; file content verified against pinned Git blob.', 'full_body_text_and_all_pages_visual_review':'All extracted body text and every full slide visually reviewed; not an independent review of original papers in embedded screenshots.', 'index_only_content_not_read':'Filename observed in repository inventory. No claim of content reading, image inspection, code audit, or execution.'},
    'pdf_review':{'source_path':pdf_path, 'source_page_count':70, 'extracted_text':'pdf/handbook_lecture.txt', 'text_line_count':len((out/'pdf/handbook_lecture.txt').read_text().splitlines()), 'text_sha256':digest(out/'pdf/handbook_lecture.txt'), 'render_command_description':'pdftoppm -r 72 -png SOURCE OUTPUT_PREFIX', 'individual_pages':70, 'page_pixels':[960,540], 'contact_sheet_pixels':[1920,1120], 'contact_sheets':[str(p.relative_to(out)) for p in contact_sheets], 'visually_reviewed_pages':list(range(1,71)), 'viewing_tool':'view_image with original detail', 'external_pdf_skill':{'path':str(external_skill),'status':'full_text_read','sha256':digest(external_skill)}, 'limitation':'Images embedded in slides were viewed as slide examples. Tiny or cropped original-paper text was not independently reconstructed or verified.'},
    'project_context':context,
    'read_time_precision':'Exact per-file read timestamps were not recorded; manifest timestamps are artifact-recording times, and all declared reads finished before them. Remote verification timestamps are separately captured in the receipt.',
    'execution_boundary':{'reading_is_not_execution':True, 'models_launched_by_this_agent':False, 'claude_model_called':False, 'automations_created_or_verified_by_this_agent':False, 'main_ledger_modified_by_this_agent':False, 'new_research_method_established_by_this_audit':False, 'new_metric_computation_or_independent_author_audit':False},
    'outputs':{'audit':'audit.md','common_five_route_gates':'five_route_acceptance.json','remote_receipt':'remote_verification.json','installed_parity':'installed_skill_parity.json'},
    'files':entries,
}
(out/'read_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'recorded_at_utc':stamp.isoformat(),'counts':manifest['counts'],'status_counts':dict(collections.Counter(e['status'] for e in entries))}, ensure_ascii=False, indent=2))
