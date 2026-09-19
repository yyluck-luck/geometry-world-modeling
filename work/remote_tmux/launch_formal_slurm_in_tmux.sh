#!/usr/bin/env bash
# Formal guard: Gate0 PASS and contract/script hash bindings are mandatory.
set -euo pipefail
SESSION="${1:?tmux session name required}"
CONTRACT="${2:?remote Gate0 contract JSON required}"
MANIFEST="${3:?remote frozen pre-run manifest required}"
SBATCH_SCRIPT="${4:?remote sbatch script required}"
REMOTE_LOG="${5:-$HOME/gwm_formal_${SESSION}.log}"
LAUNCH_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATOR="${GWM_GATE0_VALIDATOR:-$LAUNCH_ROOT/validate_gate0_contract.py}"
[[ -f "$VALIDATOR" ]] || { echo "missing Gate0 validator: $VALIDATOR" >&2; exit 2; }
command -v python3 >/dev/null || { echo 'python3 is required for validation' >&2; exit 2; }
if ! python3 "$VALIDATOR" "$CONTRACT"; then
  echo 'formal submission refused: Gate0 validator did not pass' >&2
  exit 4
fi
python3 - "$CONTRACT" "$MANIFEST" "$SBATCH_SCRIPT" <<'PY'
import hashlib, json, pathlib, sys
contract, manifest, script = map(pathlib.Path, sys.argv[1:])
for p in (contract, manifest, script):
    if not p.is_absolute() or not p.is_file():
        raise SystemExit(f'missing absolute artifact: {p}')
obj = json.loads(manifest.read_text())
if obj.get('status') != 'FROZEN':
    raise SystemExit('formal manifest must declare status=FROZEN')
for key, path in [('gate0_contract_sha256', contract), ('sbatch_script_sha256', script)]:
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if obj.get(key) != actual:
        raise SystemExit(f'{key} mismatch; formal submission refused')
    print(f'{key}:{actual}')
print('manifest_sha256:' + hashlib.sha256(manifest.read_bytes()).hexdigest())
PY
exec bash "$LAUNCH_ROOT/launch_slurm_in_tmux.sh" "$SESSION" "$SBATCH_SCRIPT" "$REMOTE_LOG"
