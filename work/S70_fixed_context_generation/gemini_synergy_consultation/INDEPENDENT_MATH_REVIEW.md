# Independent review of the finite synergy examples

**PASS for the stated probability examples and the root's restricted interpretation; no mathematical blocker found.** This is a different-author team review of `ROOT_MATH_REVIEW.md` SHA256 `f87d2e91d0bd2b736605025ebd9ead7b74c06c2ee9a4852a41659664e7d1f365` and its actual Fraction receipt. Review began at the observed clock 2026-09-09 03:52:41 UTC. Exact arithmetic time, input identities and numerical comparisons are in `INDEPENDENT_MATH_REVIEW_RECEIPT.json`.

I derived the conditional distributions directly and ran one tiny standard-library closed-form check. I did not read, import or execute the author's enumeration source. No model, media, weight, scientific array, simulation or S70 result was used.

## XOR: the exact conditional distributions

Write `Z=A xor B`, where A and B are independent fair bits, and let E be independent with P(E=1)=1/5. Then Y=Z and X3=Z xor E. For either value of A, B remains fair, so A is independent of Z. Since E is independent too, A is independent of the pair (Y,X3), and likewise B. Thus observing A or B in addition to X3 leaves the posterior error probability exactly 1/5. Observing both A and B determines Y.

| Observed subset | Bayes 0–1 risk | Mutual information with Y |
|---|---:|---:|
| Empty, {1}, or {2} | 1/2 | 0 bits |
| {3}, {1,3}, or {2,3} | 1/5 | `1−h2(1/5)` = 0.2780719051126377 bits |
| {1,2} or {1,2,3} | 0 | 1 bit |

All eight original receipt rows match these independently derived risks exactly and information values within 1e−15. The binary-entropy logarithms are floating approximations, not exact rational information values.

The greedy trap needs a precise algorithm: one-at-a-time **forward** maximization of marginal MI, or reduction in Bayes 0–1 risk, with cardinality two. X3 is the unique best first choice; both remaining one-item gains are zero. The second-choice tie cannot repair that decision. Joint search finds {1,2}. This does not claim failure of look-ahead, swaps, backtracking, every greedy heuristic, or budget three. The MI set function is not submodular here: the gain from X1 is zero at the empty set and one bit after X2. Its increasing marginal gain already explains why an ordinary diminishing-returns guarantee does not apply. This is a known mathematical construction, not a discovered video selector.

## MI and 0–1 loss are different objectives

Agreement on the best XOR subset is local to this example. A small explicit counterexample uses the same fair binary target: an erasure channel reveals Y with independent probability 1/2 and otherwise outputs an erasure symbol. It has MI=1/2 bit and Bayes risk=1/4. A binary symmetric channel with crossover probability 1/5 has MI≈0.278072 bits and risk=1/5. The higher-MI observation has worse 0–1 risk. Both calculations were checked analytically in the small receipt. No universal substitution of joint MI for the task loss is justified.

## Gaussian duplication: ordinary precision is sufficient

Make the intended Gaussian assumptions explicit: Y~N(0,1), e1~N(0,1), e3~N(0,2), mutually independent; X1=X2=Y+e1 and X3=Y+e3. Merely specifying noise variances without Gaussianity/independence would not establish these exact Bayes formulas.

X1 and X2 repeat the **same noisy measurement**. Their posterior precision is prior precision 1 plus measurement precision 1, so risk is 1/2. X1 and X3 instead have precision `1+1+1/2=5/2`, giving risk 2/5. Counting X2 as a second independent unit of precision would be wrong.

The independently checked information values are I(X1;Y)=0.5, I(X3;Y)=0.2924812503605781 and I(X1,X3;Y)=0.6609640474436812 bits. Joint minus summed individual information is −0.1315172029168969 bits. A better pair therefore follows from ordinary duplication avoidance/noise precision. This signed information difference is not a complete partial-information decomposition and does not prove every possible definition of synergy is zero. It does establish the root's intended objection: a subset error gap alone cannot identify a particular higher-order interaction or an interaction inside a model's latent computation.

## Access and causal interpretation

X3 need not leak the future. A consistent causal interpretation samples a persistent hidden parity Z before the observations, measures it noisily in the past, and observes the same Z as the later target. It is prior task-relevant information, not future-label access. That interpretation would fail if X3 were actually calculated from a withheld future outcome or if later dynamics changed the target without a corresponding observation model. The example supplies no physical camera/dynamics witness.

The table concerns **fixed subsets** chosen under a known distribution. A selector that scans the whole history, uses annotations, or searches candidate losses has a larger access/computation budget than the retained count k. A future-label-based subset search is an oracle. For an adaptive past-only selector, the consumer's observation is generally `(selected IDs/timestamps, selected values)`; the selection pattern can itself transmit information. It is not enough to compute MI for each fixed subset and assume the same result covers an instance-dependent policy. Candidate scanning and any retained summaries must be counted explicitly.

The root appropriately rejects “a better tuple proves latent synergy.” Model estimation error, redundant measurements, a weak/misspecified decoder, different conditioning and oracle selection can all yield that gap. Recent/uniform and ordinary redundancy-aware or joint-design controls should be tested before proposing a new mechanism. The present evidence is finite mathematical correctness only: no natural failure, empirical selector benefit, dynamic-state sufficiency, new S70 arm, or new method has been established.
