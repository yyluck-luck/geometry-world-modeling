Here is an evaluation of the candidate mechanism.

**1. Probability Example**
Let the future target query $Y \in \{0, 1\}$ be uniformly distributed. We have access to a pool of three past variables $X_1, X_2, X_3 \in \{0, 1\}$. Let $X_1$ and $X_2$ be independent fair coin flips, and let the future state be determined by their parity: $Y = X_1 \oplus X_2$. Let $X_3$ be a noisy indicator of $Y$ driven by an independent noise channel, matching $Y$ with probability 0.8 and flipping with probability 0.2.

The observation budget is $k=2$. The loss is the zero-one risk (exact prediction error).

If we score each observation independently using Mutual Information $I(X_i; Y)$:

* $I(X_1; Y) = 0$ bits.
* $I(X_2; Y) = 0$ bits.
* $I(X_3; Y) = 1 - H(0.2) \approx 0.278$ bits.

An independent per-observation scoring method will select $X_3$ and arbitrarily choose $X_1$ (or $X_2$) to fill the $k=2$ budget. The optimal predictor using $\{X_1, X_3\}$ relies entirely on $X_3$, yielding a zero-one risk of 0.2. However, the jointly selected pair $\{X_1, X_2\}$ contains complete information about the target, yielding $I(X_1, X_2; Y) = 1$ bit and a zero-one risk of 0. This is a mathematical demonstration of information synergy, not evidence of real video model behavior.

**2. Prior Art**
A standard joint mutual-information maximization design, defined as $\arg\max_{S, \vert{}S\vert{}=k} I(X_S; Y)$, explicitly evaluates the combinatorial synergy and solves this example by directly selecting $\{X_1, X_2\}$. Consequently, the basic mechanism is prior art. Repackaging this established joint-information criterion by attaching camera-ray metadata or describing it as "preserving clues about a nonlinear dynamic mode" does not constitute algorithmic novelty.

**3. Necessary Empirical Fact**
Before designing a new bounded-memory mechanism, you must establish one single empirical fact on real past-only video: that evaluating the frozen world model on a specific synergistic $k$-frame subset yields strictly lower prediction error on real future targets than evaluating it on the $k$ most individually predictive frames.

To prove this, you must conduct an allowed-input probe where your offline selection algorithm is granted access to the whole history to optimally search for this synergistic subset, but the frozen model inference is strictly constrained to the $k$-frame budget. Demonstrating this error gap proves that exploitable synergistic signals actually exist in the model's latent processing of real video, which marginal selection misses.

**4. Decision and Residual Question**
**Reason to stop:** You should stop pursuing this candidate as a core theoretical contribution because recognizing that joint selection outperforms marginal selection is merely a restatement of classic Bayesian experimental design. Without a computationally novel approximation specific to the world model's architecture, the observation itself is mathematically trivial and functionally identical to established subset selection.

**Precise residual question:** Can a scalable selection heuristic identify these synergistic frame tuples causally (strictly blind to future outcomes) using only the frozen world model's past latents, without requiring privileged extra-view camera metadata or dense semantic annotations during the selection phase, while adhering to the identical $k$-frame input budget and fixed decoder for evaluation?