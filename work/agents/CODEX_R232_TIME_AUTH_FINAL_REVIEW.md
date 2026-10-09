# R232 Authenticated-time final review of R231

## Concrete remaining gap

R231 binds time to an authority and monotonic epoch/counter but does not require freshness/non-replay of the time attestation itself or define rotation/revocation for the time authority key. A stale signed timestamp could therefore pass monotonic checks after verifier state reset or key compromise.

## Fail-closed repair

Add attestation freshness and authority-key lifecycle gates:

```yaml
time_attestation_policy:
  attestation_id: "MISSING_EVIDENCE"
  attestation_signature: "MISSING_EVIDENCE"
  attestation_freshness_check: "pending"
  attestation_nonce_or_sequence: "MISSING_EVIDENCE"
  replay_check: "pending"
  time_authority_key_version: "MISSING_EVIDENCE"
  key_revocation_status: "pending"
  key_rotation_status: "pending"
time_policy:
  stale_or_replayed_attestation: "reject_and_remain_B_STATIC_ONLY"
  revoked_or_untrusted_time_key: "reject_and_remain_B_STATIC_ONLY"
```

Acceptance requires a fresh, non-replayed attestation signed by a current, non-revoked authority key.

## Status and stop condition

Remain `B_STATIC_ONLY`; `allowed_next_branch_state=explicit_null`; `allowed_next_branch_value=null`; `transition_policy=prohibited`. Stop on missing attestation/freshness/replay/key lifecycle evidence, pending checks, divergent time, key mismatch, or any execution/transition attempt.
