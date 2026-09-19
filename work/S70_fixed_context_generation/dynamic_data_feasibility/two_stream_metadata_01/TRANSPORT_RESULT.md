# Two-stream preparation stopped at transport

Recorded UTC: 2026-09-09T03:36:12.227638+00:00. **BLOCKED_TLS_BEFORE_ANY_ARCHIVE_BODY**.

The fixed pair remains **cam00 + cam06**, chosen from calibration before any video read. Across three preserved worker executions, all six30-byte local-header GET attempts failed during TLS handshake. Total archive response bodies: **0 B /157,286,400 B cap**. The auxiliary curl HEAD also failed TLS with exit35 and0 body. No local member header completed, no MP4 member was downloaded/decompressed, and **ffprobe was never invoked**. There are no frame PTS, codec/dimension observations, or camera-sync results from this stage.

| Route | Actual external UTC window | Return | Archive body |
|---|---|---:|---:|
| . | 2026-09-09T03:31:10.283764+00:00 – 2026-09-09T03:31:11.432433+00:00 | 1 | 0 B |
| retry_01/ | 2026-09-09T03:32:38.655321+00:00 – 2026-09-09T03:32:40.174949+00:00 | 1 | 0 B |
| retry_02/ | 2026-09-09T03:34:23.245718+00:00 – 2026-09-09T03:34:23.700122+00:00 | 1 | 0 B |

The first route used project Python3.12.14; the second used installed system Python3.13.0; the third reused the already-recorded anonymous official release-assets redirect directly. All preserved exact member/range rules, default TLS certificate verification, and the original external deadline03:41:10.283764Z (600 seconds from first start). Runtime/endpoint changes did not establish the underlying network cause. Curl's precise wall-clock interval was not separately instrumented; its actual exit35 and zero-body HEAD outputs are retained, with the later observation timestamp in ASSET_TRANSPORT_RETRY.json.

A final read-only system check shows HTTP, HTTPS, SOCKS and PAC proxy enable flags0; this does not rule out TUN routing or upstream interception. No network configuration was changed. Stop further retries in this bounded task as instructed. This is a current transport blocker, not evidence the dataset or proposed diagnostic is invalid.

All failure receipts, request logs, exact sources, external process records and the proxy observation are frozen. The intended reader remains compile-checked only beyond the failed network entry: decompression and ffprobe paths were not exercised. No claim of tested download/probe implementation is made.

Root's separately frozen PAST_PREFIX_INSPECTION_PLAN.md remains unexecuted: eventual cam06 inspection only at0,.5,...4.5 seconds; cam00 RGB and time≥5s RGB remain unexposed. No substitute camera, synthetic example, dynamic-event selection, model call, S70 payload read, or S70 source change occurred. A future transport recovery must retain the existing pair and input/answer boundaries and receive its own actual bounded execution record.
