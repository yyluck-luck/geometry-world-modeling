#!/usr/bin/env bash
# Gate0 v2 formal dispatch guard. No tmux/Slurm action occurs before all checks pass.
set -euo pipefail
SESSION="${1:?tmux session name required}"
CONTRACT="${2:?absolute bundled contract JSON required}"
MANIFEST="${3:?absolute bundled dispatch manifest required}"
SBATCH_SCRIPT="${4:?absolute bundled sbatch script required}"
REMOTE_LOG="${5:-$HOME/gwm_formal_${SESSION}.log}"
FORMAL_GUARD_RECEIPT="${6:-${REMOTE_LOG}.formal_launch_guard_receipt.json}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SELF="$ROOT/$(basename "${BASH_SOURCE[0]}")"
PYTHON_BIN="${GWM_GATE0_PYTHON:-python3}"
VALIDATOR="${GWM_GATE0_V2_VALIDATOR:-$ROOT/../S102_gate0_tum/validate_gate0_v2.py}"
GENERIC_LAUNCHER="$ROOT/launch_slurm_in_tmux.sh"
[[ "$SESSION" =~ ^[A-Za-z0-9_-]+$ ]] || { echo 'invalid session name' >&2; exit 2; }
for p in "$CONTRACT" "$MANIFEST" "$SBATCH_SCRIPT" "$SELF" "$VALIDATOR" "$GENERIC_LAUNCHER"; do
  [[ "$p" == /* && -f "$p" ]] || { echo "absolute existing artifact required: $p" >&2; exit 2; }
done
command -v "$PYTHON_BIN" >/dev/null || { echo "python unavailable: $PYTHON_BIN" >&2; exit 2; }
[[ "$FORMAL_GUARD_RECEIPT" == /* ]] || { echo 'formal guard receipt path must be absolute' >&2; exit 2; }
[[ ! -e "$FORMAL_GUARD_RECEIPT" ]] || { echo "formal guard receipt already exists: $FORMAL_GUARD_RECEIPT" >&2; exit 3; }
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/gate0-v2-dispatch.XXXXXX")"
trap 'rm -rf "$TMP_ROOT"' EXIT
RECEIPT="$TMP_ROOT/validator.json"
PREFLIGHT="$TMP_ROOT/preflight.json"
"$PYTHON_BIN" - "$CONTRACT" "$MANIFEST" "$SBATCH_SCRIPT" "$SELF" "$VALIDATOR" "$GENERIC_LAUNCHER" "$PREFLIGHT" <<'PY'
import hashlib, json, pathlib, sys
contract, manifest, sbatch, guard, validator, generic, out = map(pathlib.Path, sys.argv[1:])
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()
def canonical(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def need(value,message):
    if not value: raise SystemExit(message)
def checked_ref(ref,label):
    need(isinstance(ref,dict), f'{label}: descriptor missing')
    p=pathlib.Path(ref.get('path','')).resolve()
    need(p.is_file(), f'{label}: source artifact missing')
    need(p.stat().st_size==ref.get('bytes') and sha(p)==ref.get('sha256'), f'{label}: descriptor mismatch')
    return p
c=json.loads(contract.read_text()); p=c.get('protocol',{}); formal=p.get('formal_execution',{})
m=json.loads(manifest.read_text())
need(c.get('schema')=='gwm-gate0-staged-v2' and p.get('status')=='FROZEN','contract schema/status invalid')
need(m.get('schema')=='gwm-gate0-v2-dispatch-manifest-v1' and m.get('status')=='FROZEN' and m.get('stage')=='pre-run','dispatch schema/status/stage invalid')
bundle=pathlib.Path(formal.get('bundle_root','')).resolve()
need(contract.parent.resolve()==bundle and manifest.parent.resolve()==bundle and sbatch.parent.resolve()==bundle,'cross-bundle dispatch refused')
need(contract.name=='contract.json' and manifest.name=='dispatch_manifest.json' and sbatch.name=='run_s103_vmem_base.slurm','unexpected bundle filenames')
refs={k:checked_ref(formal.get(k),k) for k in ('bundle_preparer_ref','validator_ref','predictor_ref','sealer_ref','sbatch_ref','launch_guard_ref','generic_launcher_ref','formal_chain_regression_receipt_ref')}
need(guard.resolve()==refs['launch_guard_ref'] and validator.resolve()==refs['validator_ref'] and generic.resolve()==refs['generic_launcher_ref'],'caller-selected guard/validator/launcher differs from protocol')
copies={'predictor_ref':bundle/'predictor_s103.py','sealer_ref':bundle/'seal_predictions_s103.py','sbatch_ref':sbatch,'validator_ref':bundle/'validate_gate0_v2.py'}
for key,path in copies.items(): need(path.is_file() and sha(path)==formal[key]['sha256'],f'bundled {key} mismatch')
actual={'contract_sha256':sha(contract),'manifest_sha256':sha(manifest),'sbatch_script_sha256':sha(sbatch),'validator_sha256':sha(validator),'predictor_wrapper_sha256':sha(copies['predictor_ref']),'prediction_sealer_sha256':sha(copies['sealer_ref']),'formal_bundle_preparer_sha256':formal['bundle_preparer_ref']['sha256'],'launch_guard_sha256':sha(guard),'generic_launcher_sha256':sha(generic),'formal_chain_regression_receipt_sha256':formal['formal_chain_regression_receipt_ref']['sha256']}
for key,value in actual.items():
    if key!='manifest_sha256': need(m.get(key)==value,f'dispatch binding mismatch: {key}')
need(m.get('bundle_root')==str(bundle),'dispatch bundle root mismatch')
need(m.get('run_id')==p.get('run_id') and m.get('scope')==p.get('scope'),'dispatch identity mismatch')
need(m.get('protocol_sha256')==canonical(p),'dispatch protocol SHA mismatch')
need(m.get('execution_boundary_id')==(p.get('isolation') or {}).get('execution_boundary_id'),'dispatch boundary mismatch')
embedded=m.get('validator_receipt',{})
need(m.get('validator_receipt_sha256')==canonical(embedded),'embedded validator receipt SHA mismatch')
need(embedded.get('schema')=='gwm-gate0-staged-v2' and embedded.get('stage')=='pre-run' and embedded.get('status')=='PRE_RUN_READY' and embedded.get('pre_run_ready') is True and embedded.get('errors')==[] and embedded.get('opens_future_outcome_files') is False,'embedded validator receipt is not ready')
need(embedded.get('protocol_sha256')==m.get('protocol_sha256'),'embedded validator receipt protocol mismatch')
out.write_text(json.dumps({**actual,'bundle_root':str(bundle),'run_id':m['run_id'],'scope':m['scope'],'protocol_sha256':m['protocol_sha256'],'execution_boundary_id':m['execution_boundary_id']},sort_keys=True))
PY
"$PYTHON_BIN" "$VALIDATOR" "$CONTRACT" --stage pre-run >"$RECEIPT"
"$PYTHON_BIN" - "$RECEIPT" "$PREFLIGHT" "$CONTRACT" "$MANIFEST" "$SBATCH_SCRIPT" "$SELF" "$VALIDATOR" "$GENERIC_LAUNCHER" <<'PY'
import hashlib,json,pathlib,sys
receipt, frozen, contract, manifest, sbatch, guard, validator, generic=map(pathlib.Path,sys.argv[1:])
def sha(path):
 h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()
def need(v,m):
  if not v: raise SystemExit(m)
r=json.loads(receipt.read_text()); f=json.loads(frozen.read_text())
need(r.get('schema')=='gwm-gate0-staged-v2' and r.get('stage')=='pre-run' and r.get('status')=='PRE_RUN_READY' and r.get('pre_run_ready') is True and r.get('errors')==[] and r.get('opens_future_outcome_files') is False,'fresh validator did not return zero-error PRE_RUN_READY')
need(r.get('run_id')==f['run_id'] and r.get('scope')==f['scope'] and r.get('protocol_sha256')==f['protocol_sha256'],'fresh validator identity mismatch')
for path,key in ((contract,'contract_sha256'),(manifest,'manifest_sha256'),(sbatch,'sbatch_script_sha256'),(guard,'launch_guard_sha256'),(validator,'validator_sha256'),(generic,'generic_launcher_sha256')): need(sha(path)==f[key],f'artifact changed after preflight: {key}')
PY
# Only now may the generic launcher create a tmux session and submit Slurm.
LAUNCH_OUTPUT="$(bash "$GENERIC_LAUNCHER" "$SESSION" "$SBATCH_SCRIPT" "$REMOTE_LOG")" || { printf '%s\n' "$LAUNCH_OUTPUT" >&2; exit 4; }
STATE_DIR="$(printf '%s\n' "$LAUNCH_OUTPUT" | sed -n 's/^receipt_directory://p' | tail -n 1)"
[[ -n "$STATE_DIR" ]] || { echo 'generic launcher did not return receipt directory' >&2; exit 4; }
mkdir -p "$(dirname "$FORMAL_GUARD_RECEIPT")"
TMP_GUARD="${FORMAL_GUARD_RECEIPT}.tmp.$$"
"$PYTHON_BIN" - "$TMP_GUARD" "$RECEIPT" "$PREFLIGHT" "$CONTRACT" "$MANIFEST" "$SESSION" "$REMOTE_LOG" "$STATE_DIR" <<'PY'
import datetime as dt,hashlib,json,pathlib,sys
out,receipt,preflight,contract,manifest=map(pathlib.Path,sys.argv[1:6]); session,remote_log,state_dir=sys.argv[6:9]
def sha(p): h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
r=json.loads(receipt.read_text()); f=json.loads(preflight.read_text()); m=json.loads(manifest.read_text())
obj={"schema":"gwm-formal-launch-guard-receipt-v1","status":"PASS","recorded_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"session":session,"remote_log":remote_log,"state_dir":state_dir,"bundle_root":f['bundle_root'],"validator_receipt_sha256":sha(receipt),"validator_receipt":r,"manifest_sha256":sha(manifest),"contract_sha256":sha(contract),"protocol_sha256":m['protocol_sha256'],"run_id":m['run_id'],"scope":m['scope'],"execution_boundary_id":m['execution_boundary_id']}
for key in ('validator_sha256','predictor_wrapper_sha256','prediction_sealer_sha256','sbatch_script_sha256','formal_bundle_preparer_sha256','launch_guard_sha256','generic_launcher_sha256','formal_chain_regression_receipt_sha256'): obj[key]=f[key]
out.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
PY
mv "$TMP_GUARD" "$FORMAL_GUARD_RECEIPT"
printf '%s\n' "$LAUNCH_OUTPUT"
printf 'formal_launch_guard_receipt:%s\n' "$FORMAL_GUARD_RECEIPT"
