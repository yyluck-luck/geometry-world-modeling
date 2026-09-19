# CVaR and DLV Development Pilots

This directory contains two pre-Gate development pilots:

* `CVaR-Tail-Risk-Selector`: a deterministic candidate-pool experiment that
  compares mean-risk greedy selection with tail-risk (CVaR) greedy selection
  under the same candidate pool and cardinality budget.
* `DLV-Invalidation-Protocol`: a deterministic state-machine experiment that
  checks whether contradictory observations invalidate a landmark while a
  consistent re-observation preserves it.

The fixture is synthetic and intentionally small. It is not a VMem forward,
not an RGB-D benchmark, not a held-out evaluation, and not evidence that either
candidate method works. It only verifies that the proposed objectives,
tie-breaking, state transitions, and kill criteria are executable before the
data contract is frozen.

Run:

```bash
python3 run_pre_gate_pilots.py
python3 verify_pre_gate_pilots.py
```

The output is `results.json` and `RECEIPT.json`.
