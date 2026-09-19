# S15A sampling different-author review plan

Scope: synthetic index text and synthetic frozen central-directory metadata only. No actual `rgb.txt`, `depth.txt`, PNG, GT, model weight, or old real arrays will be read. This is an engineering check, not a new-scene sample or experiment. Do not edit the root author's selector or this agent's history runner during this review.

Pre-run protocol under review: `docs/S15A_NATIVE_HISTORY_PROTOCOL.md`.

Independent mathematical reference: retain timestamp lexemes as decimal values; ideal query times are t0 + 1 + 0.4 i, i=0..23. Among finite strictly increasing candidate timestamps, minimize the tuple (absolute decimal distance, timestamp). For depth, target the chosen RGB timestamp, not the ideal target. The inclusive bound is 0.025 seconds. Store all 24 pairs; each stream must have 24 distinct members and chosen RGB times must increase. A failed case is a failure of the frozen sampling contract, not permission to shift the window.

Planned cases:

1. Normal exact ideal matches with matching depth: all 24 ordered, first20 history/last4 future.
2. RGB closest-neighbor selection is global over the series rather than always preceding/following.
3. Exact RGB and depth ties choose the earlier timestamp.
4. Exactly 0.025 seconds is admitted; a decimal increment beyond it is rejected, including large Unix-like timestamp offsets.
5. Required RGB frame near an endpoint absent: reject rather than clipping or extrapolating.
6. Empty series, one missing sample, duplicate timestamps, descending rows, NaN/Inf, extra/missing columns are rejected.
7. Path traversal, absolute path, absent frozen member, wrong image stream/extension are rejected.
8. Selected member and source timestamps are not silently deduplicated; fewer than24 unique RGB or depth paths is rejected.
9. Depth association follows chosen RGB instead of nominal target and is at most0.025 away.
10. Source reads and side effects remain restricted to the explicit selector inputs; failure metadata is retained by the caller.

The exact synthetic adapter will be written after the author announces the selector interface. Source hashes and actual test start/completion times will be recorded; this plan does not claim checks have already run.
