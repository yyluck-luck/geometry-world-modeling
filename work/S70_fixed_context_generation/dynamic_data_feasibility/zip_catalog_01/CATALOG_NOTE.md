# coffee_martini ZIP: actual metadata-only range catalog

Actual UTC2026-09-09T03:14:39.107679–03:14:40.546894Z,1.439222s, return0. Two anonymous HTTP206 requests to the official asset returned exactly **1900 archive-metadata bytes**, below the2MiB/120s limits. No archive member was extracted, decompressed, decoded or viewed. No dataset/media/model scientific result follows.

- EOCD range `1186324662–1186324683`:22B, SHA `2468e48f6dd0884f885c102a986c8ff3567f0d512e7cca6789feed9456f6bab7`.
- Central-directory range `1186322784–1186324661`:1878B, SHA `746038284f5f5d84f8913f73315149963731941eb2416f6eb4f3f00f3756457d`.

Both Content-Range values give total archive1,186,324,684B. Zero-comment, single-disk ordinary ZIP;20 central entries comprise one directory,18 MP4s and one `poses_bounds.npy`. No README, per-frame timestamp sidecar, explicit visibility mask or other calibration file appears in the actual directory. Original official README remains the source for the heldout-camera/sorted-pose mapping.

| Exact member | Compressed bytes | Uncompressed bytes | Method | Local header offset | CRC32 from directory |
|---|---:|---:|---|---:|---|
| `coffee_martini/cam00.mp4` |66,447,398|66,440,149|8: deflate|474,686,633|8eadec32|
| `coffee_martini/cam04.mp4` |58,417,253|58,411,275|8: deflate|1,068,171,437|d7313db5|
| `coffee_martini/poses_bounds.npy` |2,157|2,576|8: deflate|1,186,320,538|52c2222a|

No listed member is encrypted. cam04 is the smallest compressed **eligible training** MP4 among the17 non-heldout streams; selected solely from byte counts, before media access. cam00+cam04+poses compressed content totals **124,866,808B** (about119.08MiB), excluding local ZIP headers. Their uncompressed file bytes total124,854,000B. This is the minimum byte pair under the fixed cam00-heldout plus one valid training-camera requirement, **not** a scientifically certified view pair. Actual overlap, camera baseline, motion interval and occlusions remain unknown.

Sorted video IDs are `[0,1,2,4,5,6,7,8,9,10,11,12,13,14,16,18,19,20]`. Thus under the official sorted-existing-video convention, the candidate cam00 is pose row0 and cam04 is pose row3, not row4. The pose NPY body itself has not been read; its dtype/shape/values/camera convention are not inferred from byte size. Original exclusions explain missing03/15/17; this metadata does not diagnose each excluded stream.

Next bounded data read, only if root chooses it: inspect the three local headers to locate their exact compressed starts (central-extra lengths do not determine local-extra lengths), then retrieve only the three member ranges under an explicit roughly125MB payload budget. Validate actual decompressed sizes, CRCs and SHA before using anything. Directory CRCs above are expected metadata, **not already verified content integrity**. Deflate members are compressed streams, so the catalog does not establish direct random-frame access inside each MP4; a full-member retrieval/decompression is the simple honest route to later small-clip decoding. Verify actual video codec/PTS/30FPS/frame count and pose array, then freeze a past/future interval with separate heldout frames. No future frame or future-derived visibility becomes conditioning.

The tiny catalog closes public byte-range access and minimum-member-size questions. It leaves physical synchronization tolerance, continuous/contact-free segment selection, true visibility, camera conventions and actual decode unresolved. The parent feasibility note/receipt remains a valid earlier metadata snapshot and is not rewritten.
