# Brief R261 — REJECTION of S143 Amendment 1 (fresh-seed confirmation) before any S143 result exists (2026-10-10)

Read work/S143_context_ranking/PROTOCOL.md (Amendment 1 at the end), analyze_s143_confirm.py, s143_confirm_chain.sh,
analyze_s143.py, and your R260 (work/agents/CODEX_R260_S143_DRAFT_REJECTION.md §3.4). Discovery generation (seeds 3-6) is
running; nothing has been scored. The confirmation uses fresh seeds 42,7,1,2 on the same RTX 3090s, selections frozen
from discovery (c_W from warps; c_G_disc = argmax of the 4-seed discovery mean; r_disc = best discovery rule).

Attack it, briefly and concretely: (1) is C = mean_w[Q_G_fresh(c_G_disc) - Q_G_fresh(c_W)] the right confirmatory
estimand, and is "C >= 0.20, window-bootstrap lower > 0, >= 3/4 fresh seed panels positive, no negative pair mean in 2/3"
a sensible rule given that the unit of seed replication is the seed panel and the windows are shared? (2) Does using
all four discovery seeds for c_G_disc (rather than the 2-seed folds of the discovery primary) create any inconsistency?
(3) Any bug in analyze_s143_confirm.py (ties, aliases between rules 4/5, key parsing of "<window>__<set_id>__s<seed>"
files by score_s140.py's rsplit('__s', 1), seeds 1/2 vs set ids "s1"/"s2")? Verify by reading code and, where useful,
running it on synthetic CPU inputs. (4) Anything that must change before discovery results are opened.

Output: write exactly one file, work/agents/CODEX_R261_S143_AMENDMENT_REJECTION.md: findings table (issue | severity |
evidence | concrete change), then verdict. I prefer a correct negative to an encouraging answer.
