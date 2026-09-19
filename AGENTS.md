# Research continuity

At the start of a research session, after compaction/resumption, or when the project state may have changed, read `RESEARCH_PRINCIPLES.md`, `RESEARCH_MEMORY.md`, and the latest entries of `RESEARCH_LOG.md`. For a narrow follow-up within the same session, use the current ledger and only the relevant supporting document; a 20-minute heartbeat still performs the full workflow checklist. The principles document records the user's continuing requirements; maintain it when the user revises those requirements.

The user is a beginner. Explain the question, action, finding, and next step in simple Chinese. Use concrete examples; define technical terms only when needed. User prefers autonomous progress on this local machine and has an authorized HKUST SuperPOD H800 path; remote jobs must still use the recorded SSH/Slurm contract and evidence gates.

Maintain local research memory during every work session:

- Keep `RESEARCH_MEMORY.md` as the short current-state summary, including constraints, verified findings, uncertainty, and next action.
- Append dated events through `scripts/research_log.py`. The canonical append-only record is `research_events.jsonl`; `RESEARCH_LOG.md` is its readable view. Include time in Asia/Shanghai, action, outcome, evidence paths, and next step.
- Log session starts, completed experiments, material failures/corrections, changes of direction, and session completion. Do not fabricate time spent or exact historical event times. Backfilled events must state their timestamp source and actual recording time.
- Preserve old results and protocols. Record exploratory follow-ups separately from pre-run plans. Record negative results as clearly as positive results.
- Every experimental conclusion must link to actual outputs. Keep synthetic, source-code, real-data, and end-to-end evidence distinct. Changed retrieval does not by itself mean worse retrieval or worse generated video.

The project uses HKUSTDial/Supervisor-Skills. Relevant skills and pinned upstream code are documented in `docs/RESEARCH_STATUS.md` and `vendor/provenance.json`. Do not overwrite original proposal/drafts while doing experiments. No messages to the advisor or others are authorized.

For the user-requested OpenAI harness reference and local DeepSeek installation, see `docs/HARNESS_GUIDE.md`. Tool installation is not model access or scientific validation.

## Codex / GPT-6 Astra 是本项目的强制外部复核层(2026-09-19 起)

**每一轮决策与创新探索都必须经过 codex,且用最高档。** 不是可选的辅助。

```bash
codex exec -m gpt-6-astra \
  -c model_reasoning_effort="ultra" \
  -c service_tier="priority" \
  -s workspace-write \
  -c sandbox_workspace_write.network_access=true \
  --skip-git-repo-check \
  - < <(cat PREAMBLE.md PROMPT.md)
```

规则:

1. **在仓库内运行(`cwd` = 仓库根),并开启网络。** 这是关键——它能自己读 pinned 源码、算哈希、
   `git ls-remote` 公开仓库、打 arXiv API,**不必信我的转述**。前置 preamble 必须写明
   "verify, do not trust",并给出可核查的文件路径。
2. **每轮只允许新建一个输出文件**,禁止修改既有文件;禁止 GPU、训练、微调、下载权重。
3. **每一条引用我都要独立核验**(arXiv ID + 精确标题),每一条代码断言都要独立复核
   (repo + commit SHA + 路径 + 行号)。**已多次抓到需要更正的细节。**
4. **长任务用 `run_in_background`,并行开多条流。** 单轮 ultra 可跑 15–40 分钟、
   消耗 18–31 万 tokens。遇到 `Selected model is at capacity` 是容量错误不是逻辑失败,**直接重跑**。
5. **prompt 必须允许对方否定本方。** 明写 "I prefer a correct negative to an encouraging answer",
   并禁止它把我导向已被 owner 排除的贡献类型。
6. **codex 的裁定不构成人类授权。** `new_method_validated` 与 `novelty_authorization` 只能由 owner 改。

**为什么强制:** 它在仓库内自查后,已经推翻过本方多条结论(占据性、oracle 提案、
`self.c2ws` mutation 完备性、"任意 move 后 turn 即泄漏"的夸大),也发现过本方漏掉的真实系统与引用。
让它只读摘要或只读我的转述,这些更正一条都不会出现。
