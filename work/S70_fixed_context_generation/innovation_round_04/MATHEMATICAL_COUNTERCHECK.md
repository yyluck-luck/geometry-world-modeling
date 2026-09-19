# Different-author mathematical countercheck

UTC: 2026-09-09T03:12:51.344479+00:00. Author: `/root/negative_result_question_triage`.
Read root `gemini_math_consultation/ROOT_MATH_REVIEW.md`, SHA `ce8dc11bedb6097e921b9a477864475c094de7057f713b513f38b64178e321f0`, and the untrusted original Gemini prompt/answer. This is a symbolic review, with no numerical experiment, model call or scientific payload.

**PASS within the stated scope.** Let `Z=M(H,q)` be measurable from `(H,q)` and let vector Y have finite second moment. With `mu_H=E[Y|H,q]` and `mu_Z=E[Y|Z,q]`, expand `Y−mu_Z=(Y−mu_H)+(mu_H−mu_Z)`. The second term is measurable given `(H,q)` and the first has zero conditional mean. The cross term therefore vanishes. Taking expectations yields `R*_Z−R*_H=E||mu_H−mu_Z||²`. The stars require unrestricted squared-loss Bayes predictors. For restricted fitted models, their estimation/approximation errors remain; their observed risk difference need not equal this expression.

Independently checking the supplied symmetric example: equiprobable H=0/1, constant Z, Y conditionally equiprobable ±1 or ±2. Both conditional means are zero. Both optimal squared risks equal `(1+4)/2=5/2`; nevertheless `abs(Y)` identifies H. Thus distributional information is lost while the ideal point-prediction risks coincide. This refutes the Gemini inference more strongly than a weak-probe example does. No finite empirical equality can establish the ideal equality, let alone full sufficiency.

For the deterministic compression just defined, the appropriate distribution question is `P(Y|H,q)=P(Y|Z,q)` almost surely (equivalently conditional mutual information zero under the usual well-defined distribution conditions). It is not a theorem that every history suffers loss when this equality fails. Unobserved forces, incomplete observation, measurement noise and stochastic dynamics are different reasons for uncertainty. A finite-state POMDP/PSR existence result neither solves unknown-state learning nor establishes a constant-memory implementation at fixed numerical precision.

The root note correctly preserves all these boundaries and does not authorize an added S70 arm. No correction to its formula or counterexample is needed.
