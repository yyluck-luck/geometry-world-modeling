# Pre-Gate Protocol: CVaR Tail Risk and DLV Invalidation

## Scope

The two pilots use only a synthetic development fixture generated inside the
runner. No project prediction, future depth, held-out manifest, or external
ground truth is read.

## Pilot A: CVaR-Tail-Risk-Selector

Each candidate has a fixed cost, coverage gain, and a vector of scenario losses.
The budget is `k=3` candidates. The baseline greedily maximizes mean gain minus
mean loss. The CVaR rule greedily maximizes the same gain minus the empirical
upper-tail loss at `alpha=0.80`. Both rules use the same candidate pool,
cardinality, tie-breaking, and scenario vectors.

The pilot records:

* selected IDs and total cost;
* mean loss, CVaR loss, and worst loss of each selected set;
* whether the selected sets differ;
* whether the tail rule improves CVaR on this fixture.

The pre-registered kill condition is: if the tail rule does not improve CVaR
on a fixture with a deliberately heavy tail, the implementation is rejected
for repair. A pass only means the implementation distinguishes the objectives;
it does not support a paper claim.

## Pilot B: DLV-Invalidation-Protocol

Each landmark maintains a state (`active` or `invalidated`) and a history of
observations. A new observation is consistent when its absolute depth residual
is at most `tau=0.05`. Two consecutive contradictory observations invalidate
an active landmark. A single later consistent observation is recorded but does
not immediately reactivate an invalidated landmark; reactivation requires two
consecutive consistent observations. This hysteresis prevents one noisy frame
from flipping state.

The pilot records the full event trace, residuals, states, and false-revival
guard. The pre-registered kill condition is: if one contradictory observation
invalidates the landmark, or one noisy consistent observation reactivates it,
the state machine is rejected.

## Evidence boundary

These are code and protocol pilots only. They do not measure future geometry,
long-horizon generation, RGB quality, or cross-scene generalization. Formal
experiments require a frozen eligible RGB-D/pose/timestamp manifest, a
held-out future answer seal, and equal-budget strong baselines.
