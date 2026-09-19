# Event-memory nearest collision — bounded source check

**ReMind already occupies the broad claim that a video generator should recover a useful older event-state anchor when recent history becomes unreliable. NO_METHOD_SELECTED remains unchanged.**

The primary source is Xu et al., *Teaching Video Generators to Remember: Eliciting Dynamic Memory for Out-of-Sight State Evolution*, arXiv:2605.25333v2, 30 July 2026. The inspected record establishes a 2026 preprint; conference acceptance and released implementation were not verified. [Version record](https://arxiv.org/abs/2605.25333)

ReMind constructs event-informed frame graphs, protects historical anchors, corrupts interruption nodes, and trains nonlocal retrieval. Its reference-cache regime places clean historical chunks across explicit temporal gaps. Camera-conditioned rotary addressing preserves original time positions. Event-node examples include camera return, darkness, and occluder transitions. Its evidence includes recovery evaluations and attention diagnostics; its stated limits include restricted interruption types and camera/depth quality. This is learned memory use, not merely spatial coverage. [Method §§3.1–3.4, analysis §4.4, limitations §5, appendix F.2](https://arxiv.org/html/2605.25333v2)

| Question | Source-grounded boundary |
|---|---|
| Already event-bearing history? | Yes: protected anchors and event-derived training nodes. Calling these ideas new would collide directly. |
| Same as recent motion pair + coverage? | No: that ordinary baseline selects a fixed number of observations externally, without changing the consumer; ReMind trains its consumer and cache addressing. |
| Already the proposed equal-budget exchange? | No matched history-count, actual-noise, denoiser-budget event-versus-redundant-history exchange was identified in the inspected passages. This limited absence does not establish novelty. |

**Narrow remaining question, proposed only:** after preserving the recent motion pair and matching spatial support, does one older observation exposing a dynamics-changing event add predictive information beyond a plain latest-reliable-anchor baseline? Hold history count, actual randomness, consumer, denoiser calls, and available annotations equal. Compare an event-bearing slot against a redundant slot; keep future observations out of conditioning. This would test information allocation, not prove a new memory mechanism.

**Strongest falsifier:** if the motion pair plus coverage or latest reliable anchor already predicts the future equally well, the proposed event-memory benefit fails. If the alleged event is unobserved, unpredictable, or only labeled using future information, the comparison cannot establish recoverable historical information. Attention mass alone cannot replace this causal control. No experiment or protocol change is authorized by this note.
