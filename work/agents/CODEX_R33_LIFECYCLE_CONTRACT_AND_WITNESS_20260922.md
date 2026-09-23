# Round 33: VMem lifecycle contract and an initial-threshold witness

## Scope and evidence

This report follows the requested CPU-only, read-only investigation. I did not use a GPU, train, download weights or data, submit a job, contact anyone, or modify an existing repository file. The three pinned VMem source copies were checked and have the stated SHA-256:

90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e.

The line references below use the first pinned copy,
work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py; the other two copies are byte-identical.

The literature check is the VMem paper, arXiv:2506.18903 (DOI: 10.48550/arXiv.2506.18903). The paper describes memory as past views and surfels, retrieval by surfel visibility, and NMS for reducing redundant references (arXiv:2506.18903, §3.1). The generator consumes the selected reference views together with target camera poses (arXiv:2506.18903, §3.2). The paper does not define initial_threshold, a percentile rule, a persistent threshold lifecycle, or a reset/call-order contract (arXiv:2506.18903, §§3.1–3.2).

## 1. Contract argument

### 1.1 State that retrieval is allowed to use

The intended retrieval state is the current VMem state plus the current query and fixed configuration.

| State | How it enters retrieval | Evidence and intended role |
|---|---|---|
| The view bank | self.c2ws (camera poses), self.latents, self.encoder_embeddings, self.Ks, self.pil_frames, and their lengths | The constructor owns these banks [pipeline.py:47-135]. prepare_context_data uses the selected frame IDs to gather poses, latents, embeddings, intrinsics, and the returned IDs [pipeline.py:505-522]. The bank is the code-level version of the paper's past-view set V (arXiv:2506.18903, §3.1). |
| The surfel memory | self.surfels, self.surfel_Ks, self.surfel_depths, and self.surfel_to_timestep | Retrieval renders the surfel memory and processes the resulting index/cosine/depth maps [pipeline.py:635-647]. Timestep counts are converted into candidate frame counts [pipeline.py:462-502]. This is the code-level version of the paper's surfel map S and its past-view IDs (arXiv:2506.18903, §3.1). |
| Current query geometry | target_c2ws and target_Ks passed to get_context_info | The query pose is averaged and used for pose distances; the target intrinsics are used for the surfel render [pipeline.py:635-647]. |
| Fixed retrieval controls | context_num_frames, translation_distance_weight, and the configured use_non_maximum_suppression | These are configuration values [configs/inference/inference.yaml:9-17]. The pipeline resolves a missing per-call NMS flag to the configured value [pipeline.py:677-680]. |
| The render result | The surfel index/cosine/depth maps returned by the renderer | These maps determine the frame-count distribution before candidate expansion [pipeline.py:639-647, pipeline.py:462-502]. This is an output of the current surfel state and current query, rather than an independent historical memory. |
| Frame count and list alignment | len(self.pil_frames), len(self.latents), and len(self.c2ws) | Candidate multiplicity, the five-frame threshold branch, max_frames, and the most-recent-frame expression all depend on list lengths [pipeline.py:631-632, pipeline.py:655-674, pipeline.py:681-713]. |

Some other fields exist in the object, but they are not retrieval inputs on this path. For example, global_step, all_pil_frames, and the RGB-specific temporary lists are initialized or maintained elsewhere [pipeline.py:118-132] and are not read by the selection code in get_context_info [pipeline.py:631-765]. They therefore should not silently become retrieval history under the stated contract.

The paper supports history dependence through V, S, and the stored view IDs: writing adds views and updates the surfel map, while reading ranks stored frame IDs and applies NMS (arXiv:2506.18903, §3.1). It does not support a hidden scalar that remembers whether an earlier call used NMS.

### 1.2 What self.initial_threshold is

The precise semantic object is an NMS pose-distance threshold. In the five-frame branch, the code computes pairwise camera geodesic distances, chooses a percentile-like order statistic, and writes that scalar to self.initial_threshold [pipeline.py:681-700]. The NMS loop reads the scalar as the minimum pose distance from every already-selected frame [pipeline.py:707-742]. The code comment calls this an adaptive initial threshold based on camera-pose distribution [pipeline.py:681-682].

That makes it a per-call control variable under the experimental contract, not scene memory:

* It is derived from self.c2ws only in the special len(self.pil_frames)==5 branch [pipeline.py:674-700].
* It is not a surfel, a stored view, a frame ID, a latent, an embedding, or an entry in the paper's V/S memory (arXiv:2506.18903, §3.1).
* The NMS-off branch overwrites it with the sentinel 1e8 even though the NMS loop is then bypassed [pipeline.py:704-705, pipeline.py:715-742].
* A later call reads it unconditionally [pipeline.py:707-708]. A clean full-bank NMS-on call that has not first executed either threshold-writing branch can therefore fail with an absent attribute.
* The constructor does not initialize it [pipeline.py:47-135]. reset() clears the listed view/surfel and bookkeeping arrays but does not clear or recreate initial_threshold [pipeline.py:135-147]. initialize() calls reset() and then rebinds the initial bank [pipeline.py:149-185], again without assigning the threshold.
* Undo removes the latest latent, embedding, pose, intrinsics, and image entries, but does not restore the threshold [pipeline.py:1348-1362]. The three pose-list mutation sites are the initial bind [pipeline.py:174-181], append [pipeline.py:1288-1309], and pop [pipeline.py:1348-1362].

Thus the defensible classification is (b), a per-call control value that should be derived afresh from the current call's arguments and current bank, with one qualification: the current implementation accidentally stores it as persistent object state. It is not (a) accumulated scene memory. It is not documented by the paper or exposed as a configuration field. Calling it a trajectory-level calibration would be a possible future design, but it is not the contract documented by this source and paper.

### 1.3 The strongest legitimate-history-dependence argument

The strongest defense is real: VMem is deliberately history-dependent. A later query is supposed to see the accumulated view bank and surfel map, and the paper's read operation explicitly ranks stored past views and removes redundant ones (arXiv:2506.18903, §3.1). The source comment could be read as saying that the camera-pose distribution observed at an earlier trajectory stage should calibrate later NMS. Navigation also deliberately uses different NMS modes: backward and forward movement pass False [navigation.py:185-187, navigation.py:234-236], while turning leaves the flag unspecified and therefore uses the configured default [navigation.py:321, pipeline.py:677-680]. One could argue that the mode sequence is part of the intended trajectory state.

That defense does not survive the declared contract. The contract treats two executions as equivalent when their current V/S memory, current bank and frame count, current query poses/intrinsics, fixed configuration, and per-call NMS flag are identical; their prior calls may differ only in a control value that should have been recomputed. initial_threshold is not in V, S, the view bank, or the query. Its value can be 1e8 solely because an earlier call used the NMS-off mode, and it survives both reset() and undo. It is therefore an unadvertised dependency on call history, rather than legitimate dependence on scene memory. The application-level “Choose New Image” operation only replaces the navigator list [app.py:688-697]; the shared global pipeline is created at module scope [app.py:19-23] and is not recreated there. The evidence establishes a contract violation under this declared forensic contract; it does not claim that every form of history dependence in VMem is a bug.

## 2. Selection trace and threshold behavior

### 2.1 Exact construction of the ordered context list

The selection path is:

1. A one-frame bank returns [0] immediately [pipeline.py:631-632].
2. Otherwise, the code averages the last quarter of target poses, averages target intrinsics, renders the surfels, and converts the render maps into frame-count weights [pipeline.py:635-647]. With the default context_num_frames=4, the target-pose slice is the last one [configs/inference/inference.yaml:9-17; pipeline.py:635-637].
3. For each (frame,count), it extends the candidate list by repeating that frame count times; indices_to_frame maps each occurrence back to the frame ID [pipeline.py:655-662]. Candidate multiplicity therefore comes from the surfel-derived count, not from independently sampled frames.
4. It computes one geodesic distance from the averaged target pose to every candidate frame pose, sorts only by that distance, and obtains sorted_frames [pipeline.py:664-670]. The distance is translation norm times translation_distance_weight plus rotational angle [pipeline.py:191-226].
5. It sets max_frames = min(context_num_frames, len(candidates), len(latents)) [pipeline.py:671]. It records is_second_step = (len(pil_frames)==5) [pipeline.py:674].
6. If NMS is enabled and the bank has exactly five images, it computes all pairwise bank-pose distances, selects an order statistic, and writes self.initial_threshold [pipeline.py:681-700]. If the pairwise list is empty, it writes 1; otherwise the index is int(len(pairwise_distances)*0.5) [pipeline.py:693-700]. The comment says “25th percentile,” but the code uses the upper-middle index for the ten pairs in a five-frame bank; the code, not the comment, is the operative behavior.
7. It initializes selected_indices=[] and reads current_threshold=self.initial_threshold [pipeline.py:707-708]. It unconditionally appends sorted_frames[0] [pipeline.py:710-711].
8. On NMS-off, it then appends len(self.c2ws)-1, the most recent bank frame, without checking whether it equals the first item [pipeline.py:704-713].
9. On NMS-on, the loop scans sorted_frames[1:]. A candidate is accepted only if its geodesic distance from every selected frame is at least current_threshold [pipeline.py:715-730]. If the target count is not reached, the threshold is divided by 1.2 and the scan repeats [pipeline.py:731-742]. The selected list is not reset between relaxations.
10. If the target count is still not reached, fallback builds an available list by testing membership against the selected list and extends the result [pipeline.py:744-750]. The membership list is not updated during that extension, so duplicate candidate occurrences can pass the same test. Finally, the selected order is converted to a tensor and passed through prepare_context_data; that order is returned as context_time_indices [pipeline.py:752-765].
11. The generator calls this method and receives the ordered context tensors before concatenating context and target camera poses [pipeline.py:1249-1267]. Therefore the order is observable by the generator, not merely an internal set.

### 2.2 Does 1e8 change the output?

It can. The sentinel is not an infinite barrier: each unsuccessful pass divides it by 1.2, and the loop stops only when enough items have been selected, the threshold falls below 10^-5, or the NMS condition is false [pipeline.py:715-742]. Because selections persist across passes, the threshold schedule changes which candidate is accepted first and which later candidates remain eligible.

A difference is possible when:

* max_frames >= 2;
* at least two candidates survive the surfel-count expansion;
* the fresh threshold accepts an earlier sorted candidate that is still too close to the first seed under 1e8, while the inherited-threshold relaxation eventually accepts another candidate in a different scan pass; and
* the changed accepted items or their acceptance order are not erased by the fallback.

The residue is observationally inert in several cases: NMS-off bypasses the loop after still reading the attribute; max_frames<=1 leaves only the first seed; candidate geometry can make both thresholds produce the same greedy sequence; and fallback can make the final list coincide. The local census contains two NULL cases, so the residue does not change every output. It is nevertheless consumed in a way that changes outputs in the non-NULL cases.

The strongest direct artifact evidence is docs/report/bundle/LEAK_REGIME_CENSUS.json. In scene 13, width 50, the clean record has context IDs [105,100,95,90] and threshold 0.007324910257011652 [LEAK_REGIME_CENSUS.json:86-219]. The leaked same-build record has [105,55,95,90] and threshold 100000000.0 [LEAK_REGIME_CENSUS.json:222-490]. The census reports 8 CONTENT, 4 PERMUTATION, and 2 NULL outcomes, with slot 0 invariant [LEAK_REGIME_CENSUS.json:1-42]. This is exactly the expected pattern: the unconditional first seed is stable, while later selections can change set or order.

### 2.3 CPU witness

A full end-to-end replay of the sealed render is not possible from the saved files. The repository search found no saved complete bank of c2ws, target c2ws, frame counts, or surfel index maps for jobs 594957, 595887, or S111. The receipts do contain selected context poses/IDs and thresholds:

* docs/report/bundle/NMS_RECEIPT.json, job 594957/S111, contains bank and selected-ID summaries, thresholds, and hashes, but not the complete pose bank or surfel render [NMS_RECEIPT.json:103-157].
* docs/report/bundle/NMS_ON_CLEAN_RECEIPT.json, job 595887/S113, contains clean selected IDs and thresholds, but not the complete candidate inputs [NMS_ON_CLEAN_RECEIPT.json:914-1009].
* LEAK_REGIME_CENSUS.json contains selected context pose snippets, multiplicities, raw/retrieved IDs, and thresholds, but not the full inputs needed to reproduce the renderer [LEAK_REGIME_CENSUS.json:1-42, 86-219, 222-490, 5351-5376, 5486-5511].

The following CPU run uses saved scene-13 width-50 context poses and the saved clean threshold. The only artificial boundary is the surfel-render boundary: because the real frame-count map was not saved, the code supplies one count per frame in the union of the saved clean/leaked candidate IDs. The pose-distance formula, sorting, threshold relaxation, persistent selected list, and fallback are source-faithful translations of [pipeline.py:191-226, 664-750]. This is a mechanism witness, not a claim that the missing surfel render was reconstructed.

~~~python
# Executed on CPU; the marked candidate counts are the only stub.
import json, math, numpy as np
p = "docs/report/bundle/LEAK_REGIME_CENSUS.json"
d = json.load(open(p))
r = next(x for x in d["records"]
         if x.get("scene") == "scene_13" and x.get("width") == 50
         and x.get("regime") == "clean")
leak = next(x for x in d["records"]
            if x.get("scene") == "scene_13" and x.get("width") == 50
            and x.get("regime") in ("leaked", "same_build_leaked"))

# Saved context poses; field names are the receipt's context_c2ws snippets.
poses = {}
for rec in (r, leak):
    for frame_id, pose in zip(rec["context_time_indices"], rec["context_c2ws"]):
        poses[int(frame_id)] = np.asarray(pose, dtype=float)
frame_ids = sorted(poses)
frame_count = {i: 1 for i in frame_ids}       # STUB for missing surfel counts

def geo(a, b, w=0.1):
    R1, t1 = a[:3,:3], a[:3,3]
    R2, t2 = b[:3,:3], b[:3,3]
    q = (np.trace(R1.T @ R2) - 1.0) / 2.0
    return w*np.linalg.norm(t1-t2) + math.acos(np.clip(q, -1.0, 1.0))

target = poses[105]
candidates = [i for i in frame_ids for _ in range(frame_count[i])]
sorted_frames = sorted(candidates, key=lambda i: geo(target, poses[i]))
max_frames = min(4, len(candidates), len(candidates))

def select(threshold, use_nms=True):
    selected = [sorted_frames[0]]
    selected_indices = list(selected)
    cur, passes = threshold, 0
    while len(selected) < max_frames and cur >= 1e-5 and use_nms:
        for idx in sorted_frames[1:]:
            if len(selected) >= max_frames:
                break
            if all(geo(poses[idx], poses[s]) >= cur for s in selected_indices):
                selected.append(idx); selected_indices.append(idx)
        if len(selected) < max_frames:
            cur /= 1.2
        passes += 1
    if len(selected) < max_frames:
        available = [i for i in sorted_frames if i not in selected_indices]
        selected.extend(available[:max_frames-len(selected)])
    return selected, passes, cur

fresh = float(r["threshold"])
print("artifact=LEAK_REGIME_CENSUS.json scene_13 w050")
print("stub_candidate_frame_count=", sorted(frame_count.items()))
print("sorted_frames=", sorted_frames)
print("dists=", [round(geo(target, poses[i]), 9) for i in sorted_frames])
print("fresh=", select(fresh))
print("inherited=", select(1e8))
print("different=", select(fresh)[0] != select(1e8)[0])
~~~

The output was:

~~~text
artifact=LEAK_REGIME_CENSUS.json scene_13 w050
stub_candidate_frame_count= [(55, 1), (90, 1), (95, 1), (100, 1), (105, 1)]
sorted_frames= [105, 100, 95, 90, 55]
dists= [0.168582264, 0.097163467, 0.079956858, 0.053170151, 0.0]
fresh= ([105, 100, 95, 90], 1, 0.007324910257011652)
inherited= ([105, 55, 95, 100], 122, 0.02624636887416205)
different= True
~~~

This establishes a concrete CPU witness for the source-level mechanism: two legal method-level executions can have the same current bank/query/candidate snapshot and the same NMS-on call, while one has first reached that call through the five-frame threshold-writing branch and the other has first reached it through the legal NMS-off branch. The current snapshot and call arguments are then identical, but the ordered context list differs. The generator receives that list at [pipeline.py:1249-1267]. The missing full surfel render prevents an exact end-to-end replay of a sealed job, so the evidence level must be stated as “source-faithful CPU mechanism witness plus sealed-record corroboration,” not as a new GPU result.

## 3. The duplicate-seeding observation

The observation about lines 711 and 713 is correct for the NMS-off movement path. Line 711 seeds the closest-pose candidate, sorted_frames[0]; line 713 independently appends the most recent bank frame, len(self.c2ws)-1, with no identity check [pipeline.py:710-713]. Forward and backward navigation explicitly select NMS-off [navigation.py:185-187, navigation.py:234-236]. When the closest candidate is also the latest bank frame, the same ID occupies two slots. The sealed retrieval report records this nearest-plus-latest mechanism and reports 10 of 14 duplicate cases [docs/RETRIEVAL_ARMS_RESULT_20260918.md:118-128; docs/report/TECHNICAL_REPORT_20260918.md:287-296]. The exact examples in the sealed lists include repeated leading IDs such as [355,355,350,345] and [405,405,400,395].

Therefore, the technical report's phrase “two independently seeded selections return the same frame” is directionally correct only if “independently seeded” means the two independent seed expressions. They are not two independent algorithms or two random selections. The code has one nearest-pose seed and one latest-frame seed, and it does not test equality.

There is a second, distinct duplication mechanism on an NMS-on path. In the clean scene-14 width-150 record, the candidate multiplicity contains frame 150 twice and the final context list is [170,160,150,150] [LEAK_REGIME_CENSUS.json:5351-5376]. Because fallback tests membership against a stale selected_indices list while extending [pipeline.py:744-750], repeated candidate occurrences can both be admitted. That duplicate cannot be attributed to line 713, because line 713 is guarded by NMS-off. Consequently, the owner's nearest/latest explanation is the right explanation for the movement-path duplicates; the report's one-sentence explanation is incomplete if it is intended to cover the NMS-on multiplicity/fallback duplicate as well.

## Verdict

**CONTRACT VIOLATION ESTABLISHED** under the declared current-state/per-call contract. This is a statement about the implementation's hidden lifecycle dependency, not a claim that VMem's intended surfel/view memory may not be history-dependent.

**WITNESS EXHIBITED** as a source-faithful CPU mechanism witness, corroborated by the sealed clean/leaked context records. An exact replay of the sealed surfel-render inputs is **not feasible with the saved artifacts** because the complete pose bank, target poses, frame-count map, and surfel render maps were not saved.


