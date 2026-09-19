# Gate0 future-answer isolation protocol (candidate revision)

The formal selector sees only history RGB-D observations, their timestamps/frame IDs, frozen camera/depth contract, and any calibration outputs produced without future files. The future query files are mounted read-only to a separate scorer process and are inaccessible to the predictor process.

## Frozen windows

- Development/formal calibration source: TUM Freiburg3 long office, paired rows from the deterministic 20 ms one-to-one matcher.
- Independent held-out source: Microsoft 7-Scenes Chess, test sequences 3 and 5. The scene archive and train/test split hashes are recorded in `work/S102_gate0_7scenes/HELDOUT_ARCHIVE_EVIDENCE.json`.
- Predictor history: the first `N=20` paired observations in a declared sequence window; no future frame bytes or pose values are read by the selector.
- Calibration: a disjoint prefix of declared training sequences only; calibration code receives history-only residuals and frozen metadata.
- Future query: the next `M=20` observations after the history window, or the declared test sequence windows. Future RGB/depth/pose are scorer-only inputs.

## Seal order

1. Freeze the candidate pool, budget, seed, checkpoints, source snapshot, and this protocol hash.
2. Run the predictor in a process with no future-file paths.
3. Hash the prediction artifact and write the output seal.
4. Terminate the predictor and preserve its logs/exit status.
5. Start the independent scorer with future RGB/depth/pose paths; recompute metrics from the sealed prediction.
6. Independent verifier recomputes the manifest and metric summaries.

A future file read before step 3 invalidates the run. The pre-run Gate0 contract therefore remains blocked until a real predictor run supplies the required prediction hash and the independent readback is completed; a protocol declaration alone is not evidence of those post-run facts.
