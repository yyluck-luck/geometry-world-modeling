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

## Codex / GPT-6 Astra 外部复核层(2026-09-19 起;2026-10-10 调整两次)

**Owner 2026-10-10(晚):"From now on, use the 'GPT-6 Astra Ultra' model in Codex for your research (ideation, rejection, retrieval)."**
即 `codex exec -m gpt-6-astra -c model_reasoning_effort="ultra"`(命令见下)。**构想(ideation)、否定/挑刺(rejection)、
文献与代码检索(retrieval)三类研究工作必须经过它**;每个新实验的设计在冻结协议前要过一轮 rejection,
结果出来后的下一步要过一轮 ideation。输出写 `work/agents/CODEX_R###_*.md`,prompt 存 `work/agents/prompts/`。
遇到 capacity 错误直接重跑;持续不可用时按下文 fallback,并在账本标注。

**Owner 2026-10-10(早):"u can do by yourself not codex"** —— 仍适用于对本方运行结果的**核查/复核**(独立重算、
逐行核对源码、对照预注册):可由 agent 自审,写 `work/agents/SELF_AUDIT_*.md`,结论注明 "self-audit"。
codex 可用时也可以用于复核,但复核不是它的必经步骤;研究三类工作(构想/否定/检索)才是。


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

## GPT-6 Pro(本机 ChatGPT.app)是决策/思想类问题的指定渠道(2026-09-21 起,owner 指定)

**凡是关于研究决策、方法思想、取舍判断的问题,都要问 GPT-6 Pro。** codex/astra 负责
仓库内可核查的事实(读源码、算哈希、查行号);Pro 负责判断与取舍。两者不互相替代。

调用方式:本机 `ChatGPT.app`,经 AppleScript + System Events 驱动(需辅助功能权限)。
档位必须是 **Pro, 5 of 5**。

硬性规则:

1. **绝对不要用 Temporary Chat。** 它在页面切走时**立即销毁**,已经因此丢失过一轮
   十几分钟的深度检索结果。必须用普通对话。
2. **每次操作前先按标题点回自己的对话,再读。** 不得假设"当前显示的就是我的"。
   读取后必须用一个只可能出现在本方 prompt 里的字符串做验证(例如
   `hostile prior-art examiner`);**验证不通过立刻中止,绝不读取或记录内容。**
   —— 本规则源于一次真实事故:在未定位的情况下读取,读到了 owner 自己的私人对话。
3. **读取脚本里不得出现 `activate`。** 只有发送和按 owner 指定的间隔检查时才允许激活。
   曾经因为轮询脚本每 20 秒 `activate` 一次,持续抢占 owner 的前台焦点。
4. **后台读取看不到回答区**(web view 懒渲染:后台约 1k 字符,前台约 6.5k)。
   因此"不激活就检测完成"不可行;检查间隔由 owner 指定。
5. **完成判据不能只看文本长度稳定。** 检索中途会长时间不变。必须同时要求出现
   足够数量的实质性裁定标记。
6. **Pro 的裁定同样不构成人类授权**,且**不能替代 codex 的仓库内核查** ——
   它读不到仓库,所有事实都由我转述,因此它无法履行 "verify, do not trust"。
   经由 Pro 得出的结论,必须在账本中标注"无 codex 外部复核",并在额度恢复后补做。
7. **剪贴板是共享资源。** 借用前先 `pbpaste` 备份,用完归还。
8. **夜间科研必须用 ChatGPT.app 协同**(owner 2026-09-21 指定),且按本节方法驱动。
   夜间是 codex 额度最容易见底的时段,也是无人值守时段;Pro 渠道是此时的主力外部大脑。
   仍适用第 6 条:Pro 读不到仓库,其结论必须标注"无 codex 外部复核"并择期补做。

## Language rule for external models (owner, 2026-09-22)

**All tasks sent to codex, and all prompts written for the owner to send to GPT, must be entirely in English.**
- Codex prompts and the shared preamble contain no Chinese, and the preamble explicitly requires the output file to be written in English, because codex otherwise follows the Chinese in the ledger.
- Prompts handed to the owner for the ChatGPT app are written in English, including the request section. Do not add "Answer in Chinese".
- Explanations to the owner in this conversation stay in Chinese; only the prompts themselves are English.

## Fallback when codex is unavailable (owner, 2026-09-22)

If codex cannot run (quota, capacity that does not clear, region block, CLI failure), ask the question in the owner's
desktop ChatGPT app, in a GPT-6 astra conversation, driven by the AppleScript bridge described above.
All GPT-6 Pro/app rules still apply: regular (not temporary) chat, navigate by title before reading, verify a
marker before reading, no `activate` in read loops, prompts in English. Conclusions obtained this way cannot
read the repository and must be marked "no codex repository-level review".

Codex on the SuperPOD login node is blocked by region (HTTP 403 from HKUST egress). It works only through the
reverse SSH tunnel to the Mac's Clash proxy: `source ~/.codex_proxy_env && codex` on slogin-01, while the tunnel is up.

## SSH connection budget for SuperPOD (2026-09-23, after an incident)

Polling Slurm by opening a fresh SSH connection every 30-45 s, plus a tunnel that reconnected every 15 s, ended with
SuperPOD closing connections before the SSH handshake (`kex_exchange_identification: Connection closed by remote
host`) from the Mac's egress IP. TACC previously banned an IP for too many attempts. Rules:
- Reuse one connection: poll through the existing `claude-ssh` session or an SSH ControlMaster
  (`-o ControlMaster=auto -o ControlPath=~/.ssh/cm-%r@%h -o ControlPersist=10m`), never a new connection per poll.
- Poll no more often than every 2 minutes; prefer one wait loop *on the cluster* (inside tmux) over remote polling.
- Never auto-reconnect a tunnel in a tight loop; back off exponentially and stop after 3 failures.
- If connections are refused, stop all automated SSH and wait; do not keep testing.

## Owner authorization rule (owner, 2026-10-09) — supersedes the R112–R249 packet requirements

The owner (the user) authorizes a new experiment by **one dated protocol file** in the stage directory
(e.g. `work/S133_scale_debug/PROTOCOL.md`) containing: question, inputs, source/weight hashes, primary
metric, controls, leakage boundary, stopping rule, output directory. The owner's approval in conversation,
recorded in that file, is sufficient.

- Not required, and must not be re-introduced as gates: signed owner/reviewer packets, quorum or membership
  proofs, key rotation/status, trusted-time attestation, replay stores, external audit identities. The
  R112–R249 memos are kept as history only; their "NOT_READY_OWNER_PACKET / END-LINE / NO_REOPEN" states
  are retired.
- Anti-loop stop rule: if two consecutive rounds (agent or codex) produce no new code, data, or result, stop
  and report to the owner instead of opening another audit round. Process documents never count as progress.
- Owner standing authorization (2026-10-09): "You don't need to ask me anything from here on out". Agents proceed
  autonomously through successive protocols, propose and test new methods, and still write each protocol file before
  running it. This covers compute on SuperPOD/TACC. It does not cover messages to others.
- `new_method_validated` and `novelty_authorization` still change only by explicit owner decision.
- Compute: SuperPOD H800 (see SSH budget above) and TACC `gpu13`/`gpu14` (owner-approved 2026-10-09;
  per-node storage rules in the TACC notes) may be used for authorized protocols. Prefer local CPU when a
  diagnostic fits there.
