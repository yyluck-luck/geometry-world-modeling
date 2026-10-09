# R239 Side-channel final review of R238

## Concrete remaining confound

R238 equalizes envelope length/order/metadata but does not control processing-time, compression, encryption-randomness, or error-path differences. A consumer could infer the hidden trace from timing, retry count, ciphertext randomness, or rejection behavior without evaluating membership/version/order semantics.

## Fail-closed repair / rejection rule

```yaml
side_channel_controls:
  timing_equalization: "MISSING_EVIDENCE"
  compression_policy: "MISSING_EVIDENCE"
  encryption_randomness_policy: "MISSING_EVIDENCE"
  retry_error_path_equalization: "MISSING_EVIDENCE"
  access_count_equalization: "MISSING_EVIDENCE"
  side_channel_audit: "MISSING_EVIDENCE"
  hidden_label_predictor_accuracy: "pending"
side_channel_policy:
  uncontrolled_side_channel: "reject_and_remain_B_STATIC_ONLY"
  predictor_above_chance_margin: "reject_and_remain_B_STATIC_ONLY"
```

Reject the paired-trace hypothesis as non-identifiable if timing/encoding/error channels cannot be equalized and independently audited. Envelope equality alone is insufficient.

## Branch and status

Remain `B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. No parser, consumer, external artifact, data/model access, evaluation, commitment resolution, or result mutation is authorized.
