# Synchronization scope

This is an additive research snapshot on branch `codex/research-reset-20261010`, based on committed primary source `52bdb866`. It contains the existing tracked repository, a single current experiment map, verified literature metadata/synthesis, the next-study decision plan and task-owned compact source/evidence imports. Uncommitted changes owned by other agents are excluded.

Synchronization targets are an isolated local worktree, GitHub branch, a new versioned checkout on SuperPOD, and new versioned checkouts on TACC gpu13/gpu14. Every successful target must report the same Git commit and a clean tracked tree. Existing active experiment directories are not overwritten, reset, merged, restarted or cancelled. The primary local checkout remains untouched. No force push or destructive mirror is used.

This is source/protocol/summary synchronization, not full compute-environment replication. Large raw datasets, model weights and generated arrays are excluded from new transfer. Original input hashes and absolute historical paths remain in receipts; executing on a new host still requires checking that those exact bytes are available and the environment is compatible. See the user-facing SYNC_RECEIPT.json for verified destinations and failures.
