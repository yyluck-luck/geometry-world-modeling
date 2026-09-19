### **Independent Review of the Diagnostic Protocol**

#### **(1) Strongest Defensible Inference**
The protocol aims to test whether a *directionally appropriate change* in generated content occurs when the target camera's optical rotation is adjusted by +5 degrees. The inference space is constrained to this specific scene, fixed random realization, and predefined camera adjustments. 

- **Positive Outcome**: If the majority of matched points (via SIFT + mutual BF-L2) show a median paired difference > 0, this supports the hypothesis that the generator responds directionally to camera rotation changes.  
- **Negative Outcome**: If no systematic displacement is observed (median differences ≈ 0 or inconsistent across targets), the generator may lack geometric sensitivity to the prescribed camera adjustments.  
- **Missing Support**: If matches are sparse or unstable (e.g., high residuals, low spatial coverage), the diagnostic is inconclusive due to technical limitations (e.g., feature matching reliability, FOV overlap).  

Given the exploratory nature, a *positive* or *negative* outcome is defensible if supported by the match statistics. "Missing support" is the default if matches fail to meet analysis criteria.

---

#### **(2) Ranked Flaws**  
**Critical (Invalidating for This Diagnostic)**  
1. **Unverified RNG Equivalence**: The protocol assumes RNG states (post-intervention) match archived A0 states, but per-step epsilon tensors are unarchived. If sampler divergence occurs early, observed changes could stem from noise propagation, not camera rotation.  
   - *Mitigation*: Archive full RNG traces or validate per-step equivalence.  

**Limiting (For Broader Claims)**  
2. **Single-Scene Bias**: Results may not generalize due to fixed scene/realization.  
3. **Approximate Orthogonality Ignored**: FP32 rotation matrices may deviate from true orthogonality, introducing unquantified error in `H`.  
4. **No Physical Visibility Guarantee**: Common FOV is geometric, not a guarantee of shared scene content (e.g., occlusions).  
5. **Non-Independent Targets**: Four targets share the same scene; correlated errors inflate apparent consistency.  

---

#### **(3) Stopping vs. Follow-Up**  
- **No Stopping Justification**: Flaws (especially #2–5) limit generalizability but do not invalidate the diagnostic for its narrow goal.  
- **Prospective Follow-Up**:  
  - Replicate with multiple scenes/realizations.  
  - Quantify orthogonality error impact (e.g., via FP64 repro).  

---

#### **(4) Cheapest Decisive Control**  
**Control**: Repeat the diagnostic with *Ry(–5 degrees)* (inverse rotation).  
- **Rejection Criterion**: If the median paired differences do not invert (e.g., remain positive or vanish), the observed effect is not consistently directional.  
- **Cost**: Minimal (one additional generation + SIFT analysis).  

---

### **Summary**  
The protocol is methodologically sound for an *exploratory* test of directional response in a frozen generator. While flaws limit broader claims, none warrant halting the run. The proposed control (inverse rotation) is a low-cost validator. Avoid overinterpreting outcomes; label all findings as scene-specific and preliminary.
