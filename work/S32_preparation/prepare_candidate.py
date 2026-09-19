"""Prepare S32 A from sealed selection metadata and existing source identities only."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
HERE = Path(__file__).resolve().parent
SELECTION = ROOT / 'work/S32_input_freeze/selected_windows_rgb_sealed.json'
SELECTION_SHA = 'ac2c04437afa62fbaa5f03e5159ba06960131d9a2405afd5f94eef0c2f9ed318'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())
def write(p, x): p.write_text(json.dumps(x, indent=2, ensure_ascii=False, allow_nan=False)+'\n')


def main():
    assert not (HERE/'contract_candidate.json').exists(), 'Candidate is written once; preserve prior versions before revision'
    assert sha(SELECTION) == SELECTION_SHA
    selection = read(SELECTION)
    original_selection = ROOT/'work/S32_selection/selected_windows.json'
    assert sha(original_selection) == selection['parent_selection_sha256'] == '4574c2635851e83f5389da0d099819e7cbfd2ad9b8fe543ddf163e0fbf7e6cc6'
    parent = ROOT/'work/S26B_preparation/run_manifest.json'
    assert sha(parent) == '147357aa1b24caeb813c01fd822cb96f754c2573437d0db6ac8a05b7cbd4d90c'
    baseline = ROOT/'work/S21_baseline_preparation/run_manifest.json'
    old = read(baseline); binding = read(parent)['binding']; embedded = Path(binding['embedded_root'])
    # Hash the existing 203-file binding; no recursive dependency/tree discovery.
    for path, identity in binding['source_identities'].items(): assert sha(Path(path)) == identity, path
    windows = []
    for selected in selection['windows']:
        window = {k:selected[k] for k in ('id','scene','j','start_index','total_original_RGB')}
        window['frames'] = [{k:f[k] for k in ('index','source_rgb_index','path','rgb_time','sha256')} for f in selected['frames']]
        window['B_metadata_status'] = selected['status']
        window['B_missing_pose_indices'] = [f['index'] for f in selected['frames'] if f['gt_time'] is None]
        assert len(window['frames']) == 4 and all(isinstance(f['sha256'],str) and len(f['sha256'])==64 for f in window['frames'])
        windows.append(window)
    assert [w['id'] for w in windows] == ['fr2_desk_j1','fr2_desk_j2','fr1_xyz_j1','fr1_xyz_j2']
    runner = HERE/'run_inference.py'
    compile(ast.parse(runner.read_text()),str(runner),'exec')  # No imports or execution of model code.
    wrapper = embedded/'surfel_inference.py'; model = embedded/'src/dust3r/model.py'; inference = embedded/'src/dust3r/inference.py'
    for source, function in [(wrapper,'prepare_input_from_pil'),(wrapper,'run_inference_from_pil'),(inference,'inference'),(model,'_forward_impl')]:
        nodes = [n for n in ast.walk(ast.parse(source.read_text())) if isinstance(n,ast.FunctionDef) and n.name==function]
        assert len(nodes) == 1
    wrapper_node = next(n for n in ast.parse(wrapper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='run_inference_from_pil')
    assert sum(ast.unparse(n)=='outputs, state_args = inference(views, model, device)' for n in wrapper_node.body) == 1
    source_reads = {
        'scripts/s21_baseline.py':'Full original4 worker and dispatch read; recurrent path only a prior feasibility reference',
        'scripts/s24_baseline_expansion.py':'Read original policy source routing, schema/hook, and resource supervision',
        'scripts/s26b_consumer_baseline.py':'Read original_context, numeric_setup, ga_worker, original observer and supervision',
        'work/S28_gradient_scale_control/run_candidate.py':'Read getter, MST clone boundary, all400 gradient trace and inherited worker for future B only',
        'work/S30_scale_optimization_preparation/run_s30.py':'Read original C2a alignment/observer and historical S29 gate; B must replace history gate',
        'work/S26_consumer_baseline_preparation/saved_heads_adapter.py':'Full source read: original PIL/assembly AST extraction, six-head schema, GA contract',
        'work/S31_next_decision/review.md':'Full decision read; complete three controls, exposure/NA discipline',
    }
    read_entries = [{'path':str(ROOT/p),'sha256':sha(ROOT/p),'scope':scope} for p,scope in source_reads.items()]
    for source,scope in [(wrapper,'PIL 446-539; inference/star 290-443; original GA 174-236'),(model,'load_model 68-89; from_pretrained 300-315; forward reset/state flow 813-899'),(inference,'loss_of_one_batch 55-92; original inference 225-247; recurrent 266-296'),(embedded/'src/croco/models/pos_embed.py','Actual isolated CPU RoPE wrapper 117-138'),(embedded/'src/croco/models/rope_cpu.py','Full existing CPU signed FP32/FP16 source read')]:
        read_entries.append(dict(path=str(source),sha256=sha(source),scope=scope))
    write(HERE/'source_read_manifest.json',dict(recorded_utc=datetime.now(timezone.utc).isoformat(),source_reads=read_entries,
        binding_only_files=len(binding['source_identities']),binding_scope='203 inherited source SHA identities checked; not a claim every file was newly read line by line',
        actual_access=dict(RGB_bytes=0,GT_depth_bytes=0,GT_pose_file_bytes=0,NPZ_bytes=0,checkpoint_bytes=0,torch_imports=0,models=0,GA=0),
        compatibility_limit='A actual original inference and checkpoint load compatibility not yet executed; source evidence does not assert numerical equality with S21 recurrent path'))
    sources = [runner,HERE/'prepare_candidate.py',HERE/'plan_candidate.md',HERE/'source_read_manifest.json',SELECTION,original_selection,parent,baseline,
               ROOT/'scripts/s26b_consumer_baseline.py',ROOT/'work/S26_consumer_baseline_preparation/saved_heads_adapter.py']
    contract = dict(schema='s32-original-consumer-fresh4-inference-v1',status='CANDIDATE_NOT_FROZEN',phase='A_inference_only',
        prepared_utc=datetime.now(timezone.utc).isoformat(),runner=str(runner),selection=str(SELECTION),selection_sha256=SELECTION_SHA,
        original_metadata_selection=str(original_selection),original_metadata_selection_sha256=sha(original_selection),
        output_root=str(ROOT/'results/S32_fresh_window_inference'),execution_root=str(ROOT/'work/S32_A_execution'),
        windows=windows,total_frames=16,limits=dict(threads=8,seconds_per_window=180,rss_bytes_per_window=16*1024**3),
        inference_entry='src.dust3r.inference.inference',training=False,seed=0,dtype='float32',device='cpu',
        adapter=str(ROOT/'work/S26_consumer_baseline_preparation/saved_heads_adapter.py'),binding=binding,
        cpu_rope_source=str(embedded/'src/croco/models/rope_cpu.py'),supervisor_source=str(ROOT/'scripts/s26b_consumer_baseline.py'),
        identities={str(p):sha(p) for p in sources},
        phase_B='NOT_IMPLEMENTED_OR_FROZEN; one missing-camera window retained NA, other three require future separate GA contract',
        scientific_scope='Four predetermined RGB windows, fresh state and complete six heads; no GT/model-derived selection or accuracy outcome')
    for key in ('checkpoint','checkpoint_sha256','checkpoint_stat','checkpoint_identity_basis'): contract[key]=old[key]
    write(HERE/'contract_candidate.json',contract)
    receipt=dict(status='PASS_SOURCE_AND_METADATA_PREPARATION_ONLY',completed_utc=datetime.now(timezone.utc).isoformat(),
        candidate_sha256=sha(HERE/'contract_candidate.json'),runner_sha256=sha(runner),selection_sha256=SELECTION_SHA,
        source_file_count=len(binding['source_identities']),RGB_reads=0,GT_reads=0,NPZ_reads=0,model_loads=0,GA_calls=0,
        next='Different-author code review and root freeze before A dispatch; do not change old files')
    write(HERE/'preparation_receipt.json',receipt);print(json.dumps(receipt,indent=2))


if __name__=='__main__': main()
