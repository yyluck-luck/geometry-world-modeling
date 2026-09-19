# Correction: the released demo reaches both NMS settings (2026-09-18, second correction)

Status: `CORRECTION`. `new_method_validated=false`, `novelty_authorization=NONE`.
This is the second correction of the day to my own claims. Both stand recorded.

## 1. What I claimed, and why it was wrong

Earlier today I wrote, in `docs/LEAK_ATTRIBUTION_AND_ENTRY_PATH_20260918.md` and in two register
files, that the released interface disables retrieval NMS at **every** call site, that the config
default is therefore unreachable, that NMS-on "is not the method as shipped", and that the
cross-arm threshold leak is a property of **comparative harnesses only**.

**All four statements are false.** They came from a defective source trace.

I grepped for `use_non_maximum_suppression` and for `MODEL\.`. That finds the call sites which
**override** the parameter. It does not enumerate the call sites of the **function**. There are
three:

| line | method | NMS argument |
|---|---|---|
| `navigation.py:185` | `move_backward` | explicit `use_non_maximum_suppression=False` |
| `navigation.py:234` | `move_forward` | explicit `use_non_maximum_suppression=False` |
| **`navigation.py:321`** | **`_turn`**, reached by `turn_left` / `turn_right` | **no argument passed** |

`generate_trajectory_frames` defaults the parameter to `None`; `get_context_info` resolves `None`
to `self.use_non_maximum_suppression`, set in `pipeline.py:103` from
`configs/inference/inference.yaml:16`, which is `true`.

`app.py:208` and `app.py:210` route turning commands to `navigator.turn_left` and
`navigator.turn_right`. The turn path is part of the interface, not dead code.

## 2. What is therefore established

**In the released demo, turning uses NMS enabled and forward/backward movement uses NMS
disabled, on the same pipeline object.**

Combined with the selector's own semantics — the disabled branch writes
`self.initial_threshold = 1e8` unconditionally, the enabled branch assigns only when the pipeline
holds exactly five frames, and `reset()` does not clear the attribute — a native interaction of the
form

    initialize -> move_forward -> move_forward -> turn_left

leaves the bank at a size other than five when the turn executes, so the NMS-enabled turn consumes
the `1e8` written by the preceding forward move.

**The threshold a turn uses depends on whether the user moved before turning.** That is a property
of the released demo, not of my evaluation harness.

## 3. What is NOT established, and must not be written

- **Not measured on the demo.** This is static reachability plus the selector's code semantics. I
  have not run `app.py` and have no generated evidence from the demo itself.
- **Nothing about the published results.** The release contains only the demo and no evaluation or
  benchmark entry point, so the configuration behind the paper's tables cannot be determined from
  it. The paper's results are not challenged, contradicted, or implied to be contaminated.
- **Not an accusation.** Per-action retrieval settings may be deliberate. The correct posture is a
  question to the authors, not a claim about their intent.
- **Contamination is demonstrated in my comparative execution.** It is *reachable* natively. Those
  are different statements and the report keeps them apart.

## 4. What this does to my arms

The correspondence is structural, not exact: in the demo the bank grows as generated frames are
written back, while my diagnostic holds a fixed 12-frame bank.

| my arm | corresponding released behaviour |
|---|---|
| `memory_nms_off` | forward / backward movement |
| `memory_nms_on_clean` | turning, with a threshold assigned at the five-frame state |
| `memory_nms_on` (leaked) | turning **after** a movement, i.e. the mixed sequence |

So the arm I labelled "contaminated" corresponds to a reachable released behaviour rather than
being purely an artefact of my harness. Its earlier withdrawal as an estimate of the
*independently initialised* NMS-on effect stands — that is what it was withdrawn for, and
`memory_nms_on_clean` remains the correct estimate of that quantity.

## 5. Consequent retractions

Retracted from `docs/LEAK_ATTRIBUTION_AND_ENTRY_PATH_20260918.md` sections 3 and 5, and from the
corresponding rows of both register files:

- "both of its call sites pass the flag explicitly" — there is a third that does not
- "the leak is not a defect of native inference" — a native path reaches it
- "NMS on is not VMem as shipped" — it is shipped, for turning
- "the config default is unreachable through the released interface" — turning reaches it
- "the leak requires evaluating two settings on one pipeline object — my comparative harness" —
  the released demo also evaluates two settings on one pipeline object

Retained unchanged: the selector source semantics, the 28/28 byte-identical historical
reproduction, the census, the order-invariance gate, the threshold-independence of the disabled
branch, and every measured contrast.

## 6. Principle consequence

`RESEARCH_PRINCIPLES.md` v2.14 item (3) already required tracing from the released entry script to
the called function and recording call-site file and line. It did not say how to enumerate call
sites, and I searched for the **parameter** rather than for the **function**. That is added as an
explicit procedure: grepping a parameter name finds only the sites that override it, and the count
of overrides is never the count of call sites.
