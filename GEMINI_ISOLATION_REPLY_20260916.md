# Gemini isolation advisory: actual visible reply and disposition

Captured from the user-authorized in-app Browser via `mcp__cua_repl.js`, `tab.playwright.getByRole('main').innerText()` on 2026-09-16. Conversation: https://gemini.google.com/app/98591b89d8bb18fc . The visible model picker says **Pro Extended**; no numeric model version was shown. This file is advisory evidence, not an execution receipt.

## Exact submitted prompt

Give a concise independent engineering review in English. What is the minimal reproducible input-isolation demonstration for a DEVELOPMENT-ONLY VMem run with 4 history RGB frames and 4 predeclared command-camera inputs? Target RGB/depth outcomes must remain scorer-only until prediction sealing. Linux unprivileged user+mount namespaces are available; H800 runs via Slurm. We need actual allowed-read and denied-read probes, not substring guards or a declaration. Recommend an enforceable namespace/mount boundary and receipt fields binding input manifests, wrapper/source/config hashes and execution-boundary ID. Address archived copies, symlinks, inherited file descriptors and network downloads. Keep this bounded; no new framework, no demand for cross-hardware bit-exactness, no science PASS from a sandbox probe.

## Visible reply (verbatim text; code formatting restored)

Here is an independent engineering review and minimal reproducible protocol for enforcing and demonstrating input isolation for your VMem development run.

1. Enforceable Namespace Boundary (The Sandbox)

To physically prevent future-data leakage without introducing new frameworks, utilize Bubblewrap (bwrap) (standard on HPC/Slurm, running Apptainer underneath) or raw Linux unshare to create an ephemeral, unprivileged sandbox.

The boundary must enforce:

Mount Namespace: Only explicit inputs are mounted.

Network Namespace: Severed entirely to prevent fetching targets via API/WandB.

PID/IPC Namespaces: Isolated to prevent memory scraping of sibling Slurm tasks.

Minimal Sandbox Execution:

```bash
# Parent process (outside sandbox) resolves absolute, canonical paths
bwrap \
  --unshare-user --unshare-ipc --unshare-pid --unshare-net \
  --ro-bind /usr /usr \
  --ro-bind /lib /lib \
  --dir /workspace \
  --ro-bind $(realpath ./staged_history_rgb) /workspace/history_rgb \
  --ro-bind $(realpath ./staged_commands) /workspace/commands \
  --bind $(realpath ./empty_output_dir) /workspace/output \
  --symlink usr/lib /lib64 \
  --symlink usr/bin /bin \
  --setenv PATH /bin:/usr/bin \
  --new-session \
  python run_vmem_dev.py
```

Note: The target RGB/Depth directories are simply not bound into the container. They physically do not exist in the sandbox's VFS.

2. Required Isolation Probes (The Demonstration)

A valid development demonstration must run two explicit pre-flight probes inside the namespace before launching the model:

Allowed-Read Probe (PASS expected):
`python -c "open('/workspace/history_rgb/frame_3.png', 'rb'); open('/workspace/commands/cmd_3.json', 'r')"`
Must exit 0.

Denied-Read Probe (Hard FAIL expected):
`python -c "open('/absolute/path/to/host/targets/depth_0.png', 'rb')"`
Must throw FileNotFoundError (ENOENT). A permission error (EACCES) is insufficient as it implies the file path is still visible.

3. Mitigating Leakage Vectors (Edge Cases)

To satisfy rigorous isolation, the wrapper script launching the namespace must guarantee the following:

Inherited File Descriptors: The parent Slurm job might inadvertently leave target files open. The sandbox launcher must close all FDs except 0, 1, 2 (stdin/out/err) before exec. In Python, use os.set_inheritable(fd, False) or close_fds=True in subprocess.

Symlink Escape: Bind mounts must be executed on canonical paths. The parent wrapper must run realpath on all input directories to prevent a malicious symlink in the history folder pointing to ../targets.

Archived Copies: The staging mechanism must assert that input directories contain only flat image/tensor files. No .tar, .zip, or .npz archives that might secretly bundle targets alongside history frames are permitted in the mounted volumes.

Network Downloads: Addressed natively by --unshare-net. The model cannot wget or requests.get targets.

4. Cryptographic Receipt Binding

Upon successful exit (Prediction Sealing), the parent process (which has network and target access) generates an immutable receipt. The sandbox cannot generate this receipt because it lacks the execution boundary ID and target context.

Post-Flight Receipt Schema:

```json
{
  "execution_boundary_id": "uuid-v4-generated-by-slurm-parent-before-run",
  "isolation_probes": {
    "history_read": "EXIT_0",
    "target_read": "EXIT_ENOENT"
  },
  "hashes": {
    "wrapper_code_sha256": "",
    "source_tree_commit": "",
    "config_sha256": "",
    "input_manifest_sha256": "",
    "output_prediction_sha256": ""
  },
  "scorer_trigger": "READY"
}
```

Only after this receipt is written to disk does the independent Scorer Process spin up. The Scorer reads the output_prediction_sha256 and the previously hidden targets, computes the metrics, and logs them.

5. Final Guardrail

As requested, this protocol validates pipeline security and data isolation only. Passing these probes and successfully generating a receipt using dummy/synthetic inputs is an engineering milestone (DEV-ONLY). It does not constitute a scientific PASS regarding the model's actual predictive geometry or VMem capability.

## Root review: accepted and corrected

- Adopt the mount whitelist, closed network, clean inherited descriptors, actual allowed/denied reads, archive exclusion, and hashes bound to the tested execution boundary. Source, conda runtime, weights, needed CUDA device/library access, and an empty writable output must also be made explicitly available; the illustrative command above omits them and was not executed.
- Do not rely on the claim that bwrap is standard on this cluster or runs Apptainer. Our real probe found unshare/singularity/enroot, but not bwrap. Use verified capabilities.
- EACCES is a valid denial under an enforced ACL; ENOENT is expected when a path is absent in the mount namespace. The frozen method and actual error should be recorded, rather than treating every EACCES as failure.
- Canonicalizing directory roots alone does not inspect nested symlinks. Stage only enumerated regular files, reject links, and test attempted symlink/alias access. Do not give the predictor a mount of a directory that also contains scorer data or archives.
- A typed, schema-checked NPZ containing only declared allowed inputs is not intrinsically leakage. Whole-dataset containers or unreviewed bundles remain excluded; allowlist contents and bytes are what matter.
- The pre-run isolation receipt must exist before prediction. The post-run prediction seal is separate, avoiding the old Gate0 cycle. An execution-boundary ID can be passed into the sandbox; it is an identity binding, not a secret or permission mechanism.
- Output hashes plus recorded logs provide traceability; the JSON is not automatically cryptographically signed or physically immutable. Do not call advisory text an executed security proof.
