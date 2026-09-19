# Root review: useful probability example, overstated empirical diagnosis

The response was actually obtained through Gemini 3.1 Pro / Extended thinking. It is external AI advice, not primary literature or experimental evidence. No citations were offered. The finite arithmetic below is a deliberately artificial probability calculation, never real video or model generation.

## Accepted exact example

Let A,B be independent Bernoulli(1/2) and E independent Bernoulli(1/5). Define past observations X1=A, X2=B, X3=A xor B xor E and the later target Y=A xor B. This causal interpretation makes X3 a noisy *past measurement* of a persistent hidden parity; it does not grant literal future-label access. Nothing here implies a physical camera interpretation.

There are eight elementary states. With a two-observation budget, individual I(Xi;Y) scores rank X3 first: I(X1;Y)=I(X2;Y)=0, I(X3;Y)=1-h2(1/5)=0.27807190511263774 bits. X1 adds no information conditional on X3, and conversely for X2. The optimal zero-one risks are R({1,3})=R({2,3})=1/5 and R({1,2})=0. Full joint search selects {1,2}. An ordinary greedy marginal-gain search beginning with X3 also fails at budget two; this is a standard non-submodular example, not a new selector. Mutual information and zero-one risk agree on the optimum *here*, not universally across tasks/losses.

Root used independent exact Fraction enumeration of all eight states and all eight subsets on 2026-09-09T03:51:19Z. Risks are exact rationals; reported logarithms are floating approximations. The source and actual receipt are local. This verifies this finite probability construction only.

## Rejected empirical inference

Gemini claims that a selected tuple outperforming the individually top-ranked tuple proves exploitable synergy in the model's latent processing. That does not follow. Estimation error, redundancy, model misspecification, nuisance/context changes, and subset-dependent conditioning all remain explanations. A fixed decoder and equal final frame count do not equate selection cost or total accessed information. Searching with the heldout future is an oracle, even if the final decoder receives only past images. Training/validation estimates or a genuinely past-only rule need their own finite protocol.

An ordinary Gaussian redundancy example makes the insufficiency concrete. Let Y~N(0,1), X1=X2=Y+e1 with Var(e1)=1, and X3=Y+e3 with independent Var(e3)=2. Individual information ranks the duplicate X1/X2 first (0.5 bits each versus 0.29248125). Their Bayes squared risk is 1/2; choosing X1/X3 gives 1/(1+1+1/2)=2/5. Ordinary independent measurement precision explains the improvement. Joint I(X1,X3;Y)=0.66096405 is less than the sum of individual information by0.13151720 bits. This is not an assertion that every possible partial-information-decomposition synergy component is zero; it shows that a subset error gap does not uniquely establish the intended higher-order mechanism. No Gaussian data were simulated or fitted.

## Decision

Keep the textbook counterexample and the need to count full-history selection access separately from retained k. Reject treating one favorable subset/model score as an automatic interaction proof, or demanding a novel computational approximation as the only possible research contribution. A substantive new empirical problem or diagnostic can also matter, but neither a renamed criterion nor one known probability example establishes it.

The residual question remains conditional: is there a reproducible failure beyond matched recent/uniform and ordinary joint/redundancy-aware controls, under a consumer whose task actually supports the requested dynamic prediction? Verify that task and an affordable natural witness first. Raw-frame, annotation, extra-view, future-action and training advantages must remain explicit. NO_METHOD_SELECTED; new_method_validated=false. No new S70 arm, threshold or data outcome was introduced.
