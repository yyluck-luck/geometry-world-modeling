# Candidate B: bounded original-paper verification

Recorded UTC: 2026-09-05T20:23:10.497357+00:00. This is literature verification and conditional novelty analysis, not an experiment or a full idea-evaluator assessment.

## Identity and original-source access

Ke Yi, Hai Yu, Jun Yang, Gangqiang Xia, Yuguo Chen, *Efficient Maintenance of Materialized Top-k Views*, ICDE 2003, pp. 189–200, DOI 10.1109/ICDE.2003.1260792. Author PDF, publisher-deposited Crossref metadata and the author's institutional bibliography agree on identity and pages. The institutional record supplies 2003; the fetched Crossref `issued` year is null. The attempted DBLP XML request returned HTTP 503; no successful DBLP full-record retrieval is claimed.

Sources: [author PDF](https://www.cse.ust.hk/~yike/topk/icde03.pdf), [Crossref](https://api.crossref.org/works/10.1109/ICDE.2003.1260792), [institutional bibliography](https://experts.illinois.edu/en/publications/efficient-maintenance-of-materialized-top-k-views/).

## Strictly supported mechanism and limits

Locations use printed author-PDF pages, also PDF pages 1–12; they are not the proceedings pagination.

- **§3, pp. 2–3:** fixed tuple identities with changing scalar scores; an update supplies `(id,new val)`. Maintain an exact top-k′ auxiliary view, k≤k′≤kmax. Ignore an outsider below the view's bottom score; update/insert/remove affected tuples. Refill from the base table when fewer than k remain. Distinct values are assumed; identifiers may break ties.
- **§3.1, p. 3:** maintenance is O(log kmax); expected practical refill-query cost is O(N). Total cost includes maintenance and refill frequency. Supplied score evaluation is not the paper's geometry computation problem.
- **§§4.3–4.6, pp. 4–6:** let n=kmax−k+1. With bad/good probabilities p=q, n=N^(1/2+ε) gives constant expected amortized refill-query cost; p<q permits c log N. When p>q, a linear-size buffer is needed for the analyzed Θ(N) refill interval. History dependence requires the stated conditional drift restrictions. These are efficiency conditions, not probabilistic correctness.
- **§7/Fig. 7, p. 10:** observed refill/update costs adapt buffer size.
- **§2, p. 2:** the authors acknowledge an earlier MIN/MAX work-area idea; that earlier source was not independently inspected here.

## Comparison to candidate B — our inference, not a claim from Yi et al.

B fixes query cameras and point grouping, updates positions, and seeks a conservative certificate that the final **ordered four frame identifiers** match an unmodified VMem voting-plus-NMS execution.

The strong prior-art mapping is: cached candidate frames ↔ materialized tuples, frame votes ↔ ranking scores, extra candidates ↔ auxiliary pool, safe rejection ↔ ignored update, certificate failure ↔ recomputation/refill. Fixed identities and exact answers already occur in the 2003 setting. Renaming this pattern for frame retrieval does not establish algorithmic novelty.

The potentially substantive gap precedes the supplied scalar score and extends beyond scalar ranking: geometric motion can change projection, visibility and aggregated votes; greedy NMS can propagate ranking changes through later accepted frames. Fixed query/history camera poses can freeze pairwise suppression predicates but do not freeze the traversal order. A top-four score boundary alone does not certify four accepted NMS outputs. Equality must also follow the baseline's floating-point operations and tie order. These points follow from B's stated target, not from an inspection of B implementation in this task.

Therefore B needs a specifically justified dependency certificate over the full computation, fallback on uncertified cases, and measured total costs including certificate maintenance. A generic buffer, threshold test, exact-output slogan or a new application domain is insufficient evidence of novelty. The 2003 cost bounds cannot be transferred to correlated geometric updates without verifying their assumptions. This bounded check does not establish that the full B certificate is new or already solved elsewhere.

## One inspected diversity-maintenance neighbor

Orestis Gkorgkas, Akrivi Vlachou, Christos Doulkeridis, Kjetil Nørvåg, *Finding the Most Diverse Products using Preference Queries*, EDBT 2015, DOI 10.5441/002/edbt.2015.19. [Original proceedings PDF](https://openproceedings.org/2015/conf/edbt/paper-176.pdf).

**§6.2/Algorithm 3, printed p. 210 (PDF p. 6):** Stopk samples preference queries and approximates product reverse-top-k centroids before greedy diversity selection. **§7, printed p. 211 (PDF p. 7):** retain each evaluated query's kth score. An inserted product failing every threshold can be ignored with the same result as rerunning Stopk. If it crosses a threshold, affected centroids are updated and diversity selection reruns, but the paper explicitly says equality with a fresh Stopk run is not guaranteed. New-preference maintenance also lacks that equality guarantee. Thus it supplies an exact no-effect gate inside approximate diverse retrieval, not exact NMS maintenance or globally optimal diverse selection.

The bounded search did not verify a method guaranteeing full ordered greedy-NMS identity after arbitrary position updates. This is an unresolved search result, not evidence of absence. Queries included `"continuous" "diversified top-k" "exact"`, `"incremental" "non maximum suppression" "exact"`, and `"top-k" "diversity" "maintenance" dynamic queries`.

## Evidence archive and read scope

The complete two PDF byte streams and layout-preserving text extractions are preserved beside this note. `retrieval_receipt.json` records each original request's actual start/completion UTC, response details, byte count and SHA; `extraction_receipt.json` binds the 2003 PDF/text; `edbt2015_retrieval_receipt.json` binds the neighbor PDF/text. The neighbor receipt's completion time is after extraction. The web PDF endpoint timed out for the neighbor, but direct HTTP retrieval succeeded and the saved full text was actually inspected.

Read in the 2003 original: introduction/related work, all §3 algorithm/cost description, §§4.1–4.6 including conditional bounds, §6.3 data structures, §6.4 tradeoff discussion, all §7 adaptive algorithm, and conclusion. Proof appendices were not independently checked; statistical models/experiments are not claimed fully reproduced. Read in the 2015 original: identity, §6.2/Algorithm 3 and all §7. No claim of full-paper exhaustive reading or model/experiment execution.
