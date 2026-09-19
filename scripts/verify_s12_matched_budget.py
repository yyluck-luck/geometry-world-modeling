#!/usr/bin/env python3
"""Independent read-only S12 audit. Run only after the parent confirms completion.

No production imports, dynamic execution, selector, renderer, model, or raw
measurement decoding. Saved predicted poses and support/valid arrays only.
Integer counts, IDs, FP32 ranks and independently evaluated FP64 distances are
exact gates. Derived percentage-point/mean floats use a fixed 1e-12 tolerance.
Every failed attempt requires a fresh output directory and is retained.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
from importlib.metadata import version
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import platform
import re
import sys
import traceback
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
STAGES = ('S7', 'S8')
STRIDES = (8, 12)
ARMS = ('A0P0', 'A0P1', 'A1P0', 'A1P1')
READOUTS = ('official', 'candidate_no_nms', 'all20_nms', 'all20_no_nms')
OLD = {'S7': ROOT/'results/S7_event_replay', 'S8': ROOT/'results/S8_event_replay_v2'}
PINS = {
    'src/vmem_retrieval_kernel.py': '35825a3989f368906cba08808616f0c6922ff08d0a92c7205fddb4822652e2b3',
    'src/s7_event_replay.py': '3f4028366d1cf1fdcca8744a0cb14690075b9b146bd71af88360afa74bc5e20d',
    'src/rgbd_retrieval.py': '6f5188f7f72b66e93af27ab5a368cd09fcea2166715f1bf4cd0545a686ec3cd6',
    'scripts/run_s12_matched_budget.py': 'ccc36d5a7a0efcce82c7354818b878e91464e3822b680259e6dd03d504e7f6d5',
}
PROTOCOL_PIN = '60eebbfe82a4661917d3d4a887c847e39bfb23245b48452bea737a9adda78e60'
FLOAT_TOLERANCE = 1e-12

def utc(): return datetime.now(timezone.utc).isoformat()
def read(p): return json.loads(Path(p).read_text())
def save(p, x): Path(p).write_text(json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
def digest_bytes(b): return hashlib.sha256(b).hexdigest()
def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()
def stamp(s): return datetime.fromisoformat(s)
def split(stage, block): return 'development' if stage == 'S7' and block == 0 else 'test'
def label(stage, block, query): return f'{stage}_block{block}_query{query}'
def array_id(a):
    return {'dtype': str(a.dtype), 'shape': list(a.shape), 'c_bytes_sha256': digest_bytes(a.tobytes(order='C'))}

class Audit:
    def __init__(self, output):
        self.output = output
        self.counts = Counter()
        self.max_float_difference = 0.0

    def ok(self, condition, name, group='integrity'):
        if not condition: raise AssertionError(name)
        self.counts[group] += 1

    def exact(self, actual, expected, name, group='identity'):
        self.ok(actual == expected, name, group)

    def close(self, actual, expected, name):
        difference = abs(actual-expected)
        self.ok(math.isfinite(actual) and math.isfinite(expected) and difference <= FLOAT_TOLERANCE,
                f'{name}: {actual!r} != {expected!r}', 'derived_float')
        self.max_float_difference = max(self.max_float_difference, difference)

    def file_set(self, identities):
        for name, expected in identities.items():
            p = ROOT/name
            self.ok(p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(ROOT), f'unsafe input {name}')
            self.exact(sha(p), expected, f'file SHA {name}', 'file_sha')

    def archive(self, base, info, expected):
        path = base/info['path']
        self.exact(sha(path), info['sha256'], 'archive SHA')
        self.exact(path.stat().st_size, info['bytes'], 'archive size')
        manifest_path = path.with_suffix('.manifest.json')
        self.exact(sha(manifest_path), info['manifest_sha256'], 'archive manifest SHA')
        manifest = read(manifest_path)
        self.exact(set(manifest), set(expected), 'archive manifest domain')
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            self.exact(names, list(expected), 'archive ordered domain')
            self.exact(len(names), info['members'], 'archive member count')
            self.ok(len(names) == len(set(names)), 'duplicate ZIP names')
            for entry in z.infolist():
                name = entry.filename
                self.ok(not entry.is_dir() and not PurePosixPath(name).is_absolute()
                        and '..' not in PurePosixPath(name).parts, 'unsafe archive member')
                data = z.read(entry)  # zipfile checks CRC; also independently compare CRC below.
                self.exact(zlib.crc32(data) & 0xffffffff, entry.CRC, 'member CRC', 'zip_member')
                self.exact(digest_bytes(data), expected[name], 'member SHA', 'zip_member')
                self.exact({'sha256': expected[name], 'bytes': len(data)}, manifest[name], 'member manifest', 'zip_member')
                self.exact(len(data), entry.file_size, 'member size', 'zip_member')

    def extraction(self, run):
        receipt = read(run/'extraction_identity.json')
        extracted = ast.parse((run/'extracted_original_functions.py').read_text())
        targets = [('src/vmem_retrieval_kernel.py', None, 'average_camera_pose'),
                   ('src/vmem_retrieval_kernel.py', 'RetrievalKernel', 'geodesic_distance'),
                   ('src/rgbd_retrieval.py', None, 'optical_to_vmem'),
                   ('src/rgbd_retrieval.py', None, 'initial_nms_threshold'),
                   ('src/s7_event_replay.py', None, 'decision_trace')]
        self.exact(len(extracted.body), 5, 'extraction function count')
        self.exact(receipt['extracted_file_sha256'], sha(run/'extracted_original_functions.py'), 'extraction SHA')
        self.exact(receipt['original_modules_imported'], False, 'original import attestation')
        self.exact(len(receipt['functions']), 5, 'extraction receipt count')
        for copied, item, (path, owner, name) in zip(extracted.body, receipt['functions'], targets):
            source = (ROOT/path).read_text()
            body = ast.parse(source).body
            if owner: body = next(n for n in body if isinstance(n, ast.ClassDef) and n.name == owner).body
            original = next(n for n in body if isinstance(n, ast.FunctionDef) and n.name == name)
            original_dump = ast.dump(original, include_attributes=False)
            self.exact(ast.dump(copied, include_attributes=False), original_dump, 'unmodified AST '+name, 'source_ast')
            expected = {'path': path, 'owner': owner, 'name': name, 'first_line': original.lineno,
                        'last_line': original.end_lineno, 'source_sha256': sha(ROOT/path),
                        'original_span_sha256': digest_bytes(''.join(source.splitlines(keepends=True)[original.lineno-1:original.end_lineno]).encode()),
                        'extracted_source_sha256': digest_bytes((ast.unparse(original)+'\n').encode()),
                        'original_ast_sha256': digest_bytes(original_dump.encode())}
            self.exact(item, expected, 'extraction original identity '+name, 'source_ast')
        tree = ast.parse((ROOT/'scripts/run_s12_matched_budget.py').read_text())
        execution = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'execute')
        calls = [(n.lineno, n.func.id) for n in ast.walk(execution) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        line_select = [l for l, n in calls if n == 'make_selections']
        line_score = [l for l, n in calls if n == 'score_after_seal']
        self.ok(len(line_select) == len(line_score) == 1 and line_select[0] < line_score[0], 'selection before scoring source order', 'source_ast')

def expected_inputs():
    names = []
    for run in OLD.values():
        names.extend(str((run/n).relative_to(ROOT)) for n in ('run_metadata.json', 'records.json'))
        for b in range(3):
            for d in STRIDES:
                case = run/f'block{b}_stride{d}'
                names.extend(str((case/n).relative_to(ROOT)) for n in ('predicted_poses.npz', 'prediction_only_selection.json'))
                names.extend(str((case/f'query{q}_scoring.npz').relative_to(ROOT)) for q in range(20,24))
    return names

def evaluate(run, output):
    a = Audit(output)
    metadata = read(run/'run_metadata.json')
    a.exact(metadata['status'], 'completed', 'runner must be completed before audit')
    initial_result_hashes = {str(p.relative_to(run)): sha(p) for p in run.rglob('*') if p.is_file()}
    identities = read(run/'input_sha256.json')
    a.exact(list(identities), expected_inputs(), 'all 76 original inputs, ordered')
    a.exact(len(identities), 76, 'input count')
    a.exact(identities, metadata['input_sha256'], 'metadata input identities')
    a.file_set(identities)
    sources = read(run/'execution_source_sha256.json')
    a.exact(sources, PINS, 'four pinned execution sources')
    a.exact(sources, metadata['execution_source_sha256'], 'metadata source identities')
    a.file_set(sources)
    auxiliary = read(run/'protocol_and_review_sha256.json')
    a.file_set(auxiliary)
    protocol_name = 'docs/S12_MATCHED_BUDGET_PROTOCOL.md'
    a.exact(auxiliary[protocol_name], PROTOCOL_PIN, 'protocol predeclared SHA')
    freeze_names = []
    for name in auxiliary:
        if name.endswith('.json'):
            candidate = read(ROOT/name)
            if isinstance(candidate, dict) and candidate.get('schema') == 's12-matched-budget-freeze-v1':
                freeze_names.append(name)
    a.exact(len(freeze_names), 1, 'one actual execution freeze')
    freeze_name = freeze_names[0]
    freeze = read(ROOT/freeze_name)
    a.exact(freeze['status'], 'approved_for_execution', 'freeze approval status')
    a.exact(freeze['input_sha256'], identities, 'freeze input set')
    a.exact(freeze['execution_source_sha256'], sources, 'freeze source set')
    a.exact(freeze['protocol_sha256'], PROTOCOL_PIN, 'freeze protocol')
    a.exact(metadata['freeze_sha256'], auxiliary[freeze_name], 'metadata freeze SHA')
    a.exact(auxiliary, {**freeze['review_evidence_sha256'], protocol_name: PROTOCOL_PIN, freeze_name: sha(ROOT/freeze_name)}, 'review/freeze source union')
    a.ok(bool(freeze['review_evidence_sha256']), 'review evidence present')
    contract = json.loads(re.search(r'```s12-matched-budget-json\s*\n(.*?)\n```', (ROOT/protocol_name).read_text(), re.S).group(1))
    a.exact(metadata['contract'], contract, 'contract equals protocol')
    a.exact(metadata['protocol_sha256'], PROTOCOL_PIN, 'metadata protocol identity')
    a.exact(metadata['schema'], 's12-matched-budget-run-v1', 'run schema')
    combined = {**sources, **auxiliary}
    a.archive(run, metadata['archives']['inputs'], identities)
    a.archive(run, metadata['archives']['sources'], combined)
    a.extraction(run)
    post = read(run/'post_run_integrity.json')
    a.exact(post['input_sha256'], identities, 'post-run input set')
    a.exact(post['combined_source_sha256'], combined, 'post-run source set')
    for name in ('all_input_and_source_hashes_unchanged', 'selections_unchanged'): a.exact(post[name], True, 'post-run '+name)
    a.exact((post['input_files'], post['execution_sources']), (76, 4), 'post-run domain counts')

    import numpy as np
    import torch
    from scipy.spatial.transform import Rotation
    versions = {'python': platform.python_version(), **{n: version(n) for n in ('numpy','torch','scipy')}}
    a.exact(versions, contract['versions'], 'audit numerical environment')
    a.exact(metadata['environment']['versions'], versions, 'runner numerical environment')
    torch.set_num_threads(8)
    torch.set_num_interop_threads(8)
    flip = np.diag([1.,-1.,-1.,1.])

    def normalized_query(optical):
        flipped = optical @ flip
        quaternion = Rotation.from_matrix(flipped[:3,:3]).as_quat()
        quaternion = quaternion / np.linalg.norm(quaternion)
        result = np.eye(4)
        result[:3,:3] = Rotation.from_quat(quaternion).as_matrix()
        result[:3,3] = flipped[:3,3]
        return result

    def distance(left, right):
        # Independent equation, no original function or original module execution.
        p, q = torch.as_tensor(left, dtype=torch.float64), torch.as_tensor(right, dtype=torch.float64)
        rotation_trace = (p[:3,:3].mT @ q[:3,:3]).trace().clamp(min=-1., max=3.)
        angle = torch.arccos((rotation_trace-1.)*.5)
        translation = torch.linalg.vector_norm(p[:3,3]-q[:3,3], ord=2)
        return float(angle + .1*translation)

    poses, old_choices, old_records = {}, {}, {}
    for stage, old in OLD.items():
        prior_metadata = read(old/'run_metadata.json')
        a.exact(prior_metadata['status'], 'completed', 'old run complete')
        seals = {(c['block'],c['stride']): c for c in prior_metadata['cases']}
        a.exact(set(seals), {(b,d) for b in range(3) for d in STRIDES}, 'old case coverage')
        records = read(old/'records.json')
        a.exact(len(records), 24, 'old record count')
        old_records[stage] = {(r['block'],r['stride'],r['frame']):r for r in records}
        a.exact(len(old_records[stage]), 24, 'unique old records')
        for b in range(3):
            for stride in STRIDES:
                case = old/f'block{b}_stride{stride}'
                for n in ('predicted_poses.npz','prediction_only_selection.json'):
                    a.exact(sha(case/n), seals[b,stride]['sealed_files'][n], 'original prediction seal')
                with np.load(case/'predicted_poses.npz', allow_pickle=False) as f:
                    a.exact(f.files,['poses'],'old pose fields')
                    values = f['poses']
                a.ok(values.shape==(24,4,4) and values.dtype==np.float64 and np.isfinite(values).all(), 'pose domain')
                if stride==8: poses[stage,b]=values
                else: a.exact(array_id(values), array_id(poses[stage,b]), 'pose stride equality')
                choices=read(case/'prediction_only_selection.json')
                a.exact((choices['block'],choices['stride'],choices['split']), (b,stride,split(stage,b)), 'old choice identity')
                a.exact([r['frame'] for r in choices['queries']],list(range(20,24)),'old query order')
                for r in choices['queries']:
                    a.exact(set(r['maps']),set(ARMS),'old choice arm domain')
                    for arm in ARMS:
                        a.exact(set(r['maps'][arm]['readouts']),set(READOUTS),'old choice readout domain')
                    old_choices[stage,b,stride,r['frame']]=r['maps']

    calls = [json.loads(line) for line in (run/'distance_calls.jsonl').read_text().splitlines()]
    a.ok(0 < len(calls) < 100000, 'bounded actual distance log')
    cursor=0
    def consume(left, right, expected_label, phase):
        nonlocal cursor
        a.ok(cursor<len(calls),'distance log exhausted')
        item=calls[cursor]
        a.exact((item['call_index'],item['label'],item['phase'],item['weight_translation']),
                (cursor,expected_label,phase,.1),'distance call routing','distance_call')
        a.exact(item['left'],left.tolist(),'actual left matrix','distance_call')
        a.exact(item['right'],right.tolist(),'actual right matrix','distance_call')
        a.exact(item['left_identity'],array_id(left),'left matrix bytes','distance_call')
        a.exact(item['right_identity'],array_id(right),'right matrix bytes','distance_call')
        value=distance(left,right)
        a.ok(math.isfinite(value),'independent distance finite','distance_call')
        a.exact(item['result_float64'],value,'independent FP64 equation','distance_equation')
        cursor+=1
        return value

    thresholds=read(run/'initial_thresholds.json')
    a.exact(len(thresholds),6,'threshold row count')
    selected, independent_traces, created_times = {}, {}, []
    for stage in STAGES:
        for b in range(3):
            optical=poses[stage,b]
            history=[p@flip for p in optical[:20]]
            start=cursor
            values=[consume(history[i],history[j],f'{stage}_block{b}','initial_threshold_first5')
                    for i in range(5) for j in range(i+1,5)]
            threshold=sorted(values)[5]
            a.exact(thresholds[len(independent_traces)//4], {'stage':stage,'block':b,'initial_threshold':threshold,
                    'distance_call_range':[start,cursor]}, 'threshold construction')
            for q in range(20,24):
                ident=label(stage,b,q)
                record=read(run/'selections'/f'{ident}.json')
                a.exact((record['stage'],record['block'],record['query'],record['split'],record['label']),
                        (stage,b,q,split(stage,b),ident),'new selection identity')
                created_times.append(stamp(record['created_utc']))
                a.exact(record['predicted_pose_identity'],array_id(optical),'new prediction bytes')
                target=normalized_query(optical[q])
                begin=cursor
                values=[consume(target,h,ident,'all20_query_distance_identity_gate') for h in history]
                d32=torch.tensor(values,dtype=torch.float32)
                rank=torch.argsort(d32).tolist()
                a.ok(len(set(d32.tolist()))==20,'no FP32 full-distance ties','selection')
                a.exact(record['full20_frame_order'],list(range(20)),'full20 source order')
                a.exact(record['full20_distances_float64'],values,'stored full20 FP64')
                a.exact(record['full20_distances_float32'],d32.tolist(),'stored full20 FP32')
                a.exact(record['full20_sorted_frames'],rank,'stored full20 rank')
                pool=rank[:14]
                candidate_ids=sorted(pool)
                a.exact(record['pose14_ranked_candidates'],pool,'nearest14 definition','selection')
                a.exact(record['pose14_counts'],[[i,1] for i in candidate_ids],'ID-order unit counts','selection')
                a.exact(record['full20_distance_call_range'],[begin,cursor],'full20 actual calls')
                for stride in STRIDES:
                    for arm in ARMS:
                        old=old_choices[stage,b,stride,q][arm]['readouts']
                        for name in ('all20_nms','all20_no_nms'):
                            a.exact(old[name]['distances_float32'],d32.tolist(),'old full20 FP32')
                            a.exact(old[name]['sorted_frames'],rank,'old full20 order')
                            a.exact(old[name]['initial_threshold'],threshold,'old initial threshold')
                begin=cursor
                candidate_d=[consume(target,history[i],ident,'new_pose14_decision_trace') for i in candidate_ids]
                candidate32=torch.tensor(candidate_d,dtype=torch.float32)
                ranked=[candidate_ids[i] for i in torch.argsort(candidate32).tolist()]
                a.exact(ranked,pool,'pose14 rank preserves full20 prefix','selection')
                chosen=[ranked[0]]
                steps=[]
                current=threshold
                rounds=0
                while len(chosen)<4 and current>=1e-5:
                    rounds+=1
                    a.ok(rounds<1000,'finite NMS rounds','nms')
                    for frame in ranked[1:]:
                        if len(chosen)==4: break
                        comparisons=[]
                        accept=True
                        for other in chosen:
                            value=consume(history[frame],history[other],ident,'new_pose14_decision_trace')
                            comparisons.append([other,value])
                            if value<current:
                                accept=False
                                break
                        steps.append({'frame':frame,'threshold':current,'comparisons':comparisons,'accepted':accept})
                        if accept: chosen.append(frame)
                    if len(chosen)<4:
                        reduced=current/1.2
                        steps.append({'relax_from':current,'relax_to':reduced})
                        current=reduced
                if len(chosen)<4:
                    extra=[i for i in ranked if i not in chosen][:4-len(chosen)]
                    chosen.extend(extra)
                    steps.append({'fallback_added':extra})
                trace={'selected':chosen,'expanded_candidates':candidate_ids,'sorted_frames':ranked,
                       'distances_float32':candidate32.tolist(),'nms':True,'expanded_adjacent_pose_ties':0,
                       'initial_threshold':threshold,'steps':steps}
                a.exact(record['trace'],trace,'entire independently replayed new NMS trace','nms')
                a.ok(len(chosen)==len(set(chosen))==4 and set(chosen)<=set(pool),'four legal candidate IDs','selection')
                a.exact(record['pose14_distance_call_range'],[begin,cursor],'NMS actual call range')
                selected[stage,b,q]={'ids':chosen,'pool':pool}
                independent_traces[ident]=trace
    a.exact(cursor,len(calls),'all actual distance calls consumed')
    a.exact(set(p.name for p in (run/'selections').glob('*.json')),
            {name+'.json' for name in independent_traces},'exact 24 selection files')
    seal=read(run/'selection_seal.json')
    a.exact(seal['schema'],'s12-selection-seal-v1','selection seal schema')
    a.exact(seal['distance_calls'],cursor,'sealed distance count')
    a.exact(seal['selection_count'],24,'sealed selection count')
    a.exact(seal['new_decision_trace_calls'],24,'sealed new calls')
    a.exact(seal['old_decision_trace_calls'],0,'sealed old calls')
    a.exact(seal['scoring_fields_decoded'],0,'sealed scoring attestation')
    sealed_names={f'selections/{name}.json' for name in independent_traces}|{'initial_thresholds.json','distance_calls.jsonl'}
    a.exact(set(seal['files']),sealed_names,'sealed artifact domain')
    for n,h in seal['files'].items():a.exact(sha(run/n),h,'selection artifact SHA','file_sha')
    a.exact(sha(run/'selection_seal.json'),metadata['selection_seal_sha256'],'selection seal SHA')
    a.exact(metadata['selections_sealed_utc'],seal['sealed_utc'],'seal timestamp identity')
    a.ok(stamp(freeze['frozen_utc']) < stamp(metadata['started_utc']) <= min(created_times)
         <= max(created_times) < stamp(seal['sealed_utc']) < stamp(metadata['first_scoring_field_decode_utc'])
         < stamp(metadata['completed_utc']),'declared phase chronology','chronology')
    a.ok(created_times==sorted(created_times),'selection created timestamps follow fixed order','chronology')

    support_cache, scoring_ids={},[]
    for stage in STAGES:
        for b in range(3):
            for stride in STRIDES:
                for q in range(20,24):
                    path=OLD[stage]/f'block{b}_stride{stride}'/f'query{q}_scoring.npz'
                    with np.load(path,allow_pickle=False) as f:
                        support,valid=f['support'],f['valid']
                    a.ok(support.dtype==valid.dtype==np.bool_ and support.shape==(20,112,112)
                         and valid.shape==(112,112) and bool(valid.any()),'saved boolean scoring arrays','scoring_array')
                    ident={'stage':stage,'block':b,'stride':stride,'query':q,'path':str(path.relative_to(ROOT)),
                           'support':array_id(support),'valid':array_id(valid)}
                    scoring_ids.append(ident)
                    if stride==8:support_cache[stage,b,q]=(support,valid)
                    else:
                        old_s,old_v=support_cache[stage,b,q]
                        a.exact((array_id(support),array_id(valid)),(array_id(old_s),array_id(old_v)),'scoring stride bytes','scoring_array')
    a.exact(read(run/'scoring_array_identities.json'),scoring_ids,'all 48 scoring-array identities','scoring_array')
    def score(key,ids):
        support,valid=support_cache[key]
        combined=np.zeros(valid.shape,dtype=bool)
        for frame in ids:combined |= support[frame]
        n=int(np.count_nonzero(combined & valid));den=int(np.count_nonzero(valid))
        return {'selected':list(ids),'supported_pixels':n,'valid_pixels':den,'support':n/den}
    old_scores=[];bounds=[];lookup={}
    for stage in STAGES:
        for b in range(3):
            for stride in STRIDES:
                for q in range(20,24):
                    key=stage,b,q
                    original=old_records[stage][b,stride,q]
                    a.exact(original['split'],split(stage,b),'old split')
                    upper=score(key,list(range(20)))
                    a.exact((upper['support'],upper['valid_pixels']),(original['all20_support'],original['valid_pixels']),'old upper bound')
                    if stage=='S8':a.exact(upper['supported_pixels'],original['all20_supported_pixels'],'S8 old upper integer')
                    bounds.append({'stage':stage,'block':b,'stride':stride,'query':q,**upper})
                    for arm in ARMS:
                        scores={}
                        choice=old_choices[stage,b,stride,q][arm]
                        counts=choice['official_trace']['candidate_counts']
                        geom_pool=[i for i,c in counts if c]
                        a.ok([i for i,c in counts]==list(range(20)) and all(c in (0,1) for i,c in counts)
                             and len(geom_pool)==14,'old geometry14 counts','old_score')
                        a.exact(geom_pool,choice['readouts']['official']['expanded_candidates'],'old geometry14 pool')
                        for readout in READOUTS:
                            ids=choice['readouts'][readout]['selected']
                            a.ok(len(ids)==len(set(ids))==4 and all(type(i)==int and 0<=i<20 for i in ids),'old four IDs','old_score')
                            value=score(key,ids);saved=original['readouts'][arm][readout]
                            a.exact((value['selected'],value['support']),(saved['selected'],saved['support']),'old exact score','old_score')
                            if stage=='S8':a.exact(value['supported_pixels'],saved['supported_pixels'],'S8 old integer numerator','old_score')
                            scores[readout]=value
                            old_scores.append({'stage':stage,'block':b,'stride':stride,'query':q,'arm':arm,'readout':readout,**value})
                        lookup[stage,b,stride,q,arm]=scores
    reproduction=read(run/'old_scoring_reproduction.json')
    a.exact(reproduction['readouts'],old_scores,'all 768 reconstructed old score rows','old_score')
    a.exact(reproduction['all20_upper_bounds'],bounds,'all 48 old upper-bound rows','old_score')
    a.exact((reproduction['old_readout_count'],reproduction['all20_upper_bound_count'],reproduction['exact_match']),(768,48,True),'old reproduction counts')
    a.ok(stamp(metadata['first_scoring_field_decode_utc']) <= stamp(reproduction['completed_utc'])
         <= stamp(post['verified_utc']) <= stamp(metadata['completed_utc']),'score reproduction chronology','chronology')
    new_scores={key:score(key,value['ids']) for key,value in selected.items()}
    rows=[]
    for stage in STAGES:
        for b in range(3):
            for q in range(20,24):
                key=stage,b,q;new=new_scores[key];pool=selected[key]['pool']
                for stride in STRIDES:
                    for arm in ARMS:
                        old=lookup[stage,b,stride,q,arm]
                        geometry=old['official'];gp=old_choices[stage,b,stride,q][arm]['readouts']['official']['expanded_candidates']
                        n,den=geometry['supported_pixels']-new['supported_pixels'],new['valid_pixels']
                        rows.append({'stage':stage,'block':b,'query':q,'split':split(stage,b),'label':label(stage,b,q),
                            'stride':stride,'arm':arm,'main_comparison':stride==8 and arm=='A0P0',
                            'old_readouts':old,'pose14':new,'geometry14_candidates':gp,'pose14_ranked_candidates':pool,
                            'geometry14_minus_pose14_pp':100*n/den,
                            'candidate_intersection_ids':sorted(set(gp)&set(pool)),
                            'candidate_intersection_count':len(set(gp)&set(pool)),'same_candidate_set':set(gp)==set(pool),
                            'selected_intersection_count':len(set(geometry['selected'])&set(new['selected'])),
                            'selected_set_changed':set(geometry['selected'])!=set(new['selected']),
                            'selected_order_changed':geometry['selected']!=new['selected'],
                            'pose14_same_order_as_all20_nms':new['selected']==old['all20_nms']['selected']})
    actual=read(run/'records.json')
    a.exact(len(actual),192,'all new pair rows')
    for expected,record in zip(rows,actual):
        a.close(record['geometry14_minus_pose14_pp'],expected['geometry14_minus_pose14_pp'],'integer-derived pair pp')
        a.exact({k:v for k,v in record.items() if k!='geometry14_minus_pose14_pp'},
                {k:v for k,v in expected.items() if k!='geometry14_minus_pose14_pp'},'entire pair fields','pair_record')

    def stats(subset,identity):
        n=len(subset)
        signs=[r['old_readouts']['official']['supported_pixels']-r['pose14']['supported_pixels'] for r in subset]
        return {**identity,'n_queries':n,
                'geometry14_mean_support':math.fsum(r['old_readouts']['official']['support'] for r in subset)/n,
                'pose14_mean_support':math.fsum(r['pose14']['support'] for r in subset)/n,
                'geometry14_minus_pose14_mean_pp':math.fsum(r['geometry14_minus_pose14_pp'] for r in subset)/n,
                'geometry_higher':sum(s>0 for s in signs),'pose_higher':sum(s<0 for s in signs),'equal':sum(s==0 for s in signs),
                'selected_set_changed':sum(r['selected_set_changed'] for r in subset),
                'selected_order_changed':sum(r['selected_order_changed'] for r in subset),
                'candidate_set_equal':sum(r['same_candidate_set'] for r in subset),
                'pose14_same_order_as_all20_nms':sum(r['pose14_same_order_as_all20_nms'] for r in subset),
                'old_readout_mean_support':{name:math.fsum(r['old_readouts'][name]['support'] for r in subset)/n for name in READOUTS}}
    strata=[];blocks=[]
    for stage,part,n in [('S7','development',4),('S7','test',8),('S8','test',12)]:
        for stride in STRIDES:
            for arm in ARMS:
                subset=[r for r in rows if (r['stage'],r['split'],r['stride'],r['arm'])==(stage,part,stride,arm)]
                a.exact(len(subset),n,'planned strata size','summary')
                strata.append(stats(subset,{'stage':stage,'split':part,'stride':stride,'arm':arm,'main_comparison':stride==8 and arm=='A0P0'}))
    for stage in STAGES:
        for b in range(3):
            for stride in STRIDES:
                for arm in ARMS:
                    subset=[r for r in rows if (r['stage'],r['block'],r['stride'],r['arm'])==(stage,b,stride,arm)]
                    a.exact(len(subset),4,'planned block size','summary')
                    blocks.append(stats(subset,{'stage':stage,'block':b,'split':split(stage,b),'stride':stride,'arm':arm,'main_comparison':stride==8 and arm=='A0P0'}))
    summary=read(run/'summary.json')
    a.exact(summary['schema'],'s12-matched-budget-summary-v1','summary schema')
    for group,expected in [('strata',strata),('blocks',blocks)]:
        a.exact(len(summary[group]),len(expected),'summary '+group+' domain')
        for recorded,calculated in zip(summary[group],expected):
            a.exact(set(recorded),set(calculated),'summary fields')
            for key,value in calculated.items():
                if type(value)==float:a.close(recorded[key],value,'summary '+key)
                elif isinstance(value,dict):
                    a.exact(set(recorded[key]),set(value),'readout summary domain')
                    for k,v in value.items():a.close(recorded[key][k],v,'summary old '+k)
                else:a.exact(recorded[key],value,'summary integer/identity','summary')
    a.exact((summary['unique_seen_queries'],summary['related_map_conditions'],summary['difference']),
            (24,192,'geometry14_minus_pose14_percentage_points'),'summary scope')
    for k,v in {'new_decision_trace_calls':24,'original_selection_calls':0,'renderer_calls':0,'model_calls':0,
                'raw_pixels_decoded':False,'gt_pose_values_parsed':False,'checked_scoring_files':48,
                'reproduced_old_readout_scores':768,'reproduced_all20_upper_bounds':48,'unique_queries':24,
                'paired_map_conditions':192,'distance_calls':cursor}.items():a.exact(metadata[k],v,'metadata '+k)
    for n,k in [('summary.json','summary_sha256'),('records.json','records_sha256')]:a.exact(sha(run/n),metadata[k],'output SHA')
    a.file_set(identities);a.file_set(combined)
    a.exact({str(p.relative_to(run)):sha(p) for p in run.rglob('*') if p.is_file()},initial_result_hashes,'all original result files unchanged')
    save(output/'independent_traces.json',independent_traces)
    save(output/'independent_records.json',rows)
    save(output/'independent_summary.json',{'strata':strata,'blocks':blocks})
    save(output/'audited_result_sha256.json',initial_result_hashes)
    return {'counts':dict(a.counts),'check_count':sum(a.counts.values()),'max_derived_float_difference':a.max_float_difference,
            'distance_calls_independently_evaluated':cursor,'new_traces':24,'old_readout_scores':768,'all20_upper_bounds':48,
            'paired_rows':192,'scoring_npz_files':48,'original_inputs':76,'main_strata':[r for r in strata if r['main_comparison']],
            'all_pose14_equals_all20_nms':all(r['pose14_same_order_as_all20_nms'] for r in rows),
            'run_started_utc':metadata['started_utc'],'run_completed_utc':metadata['completed_utc'],
            'selection_sealed_utc':seal['sealed_utc'],'scoring_decode_marker_utc':metadata['first_scoring_field_decode_utc'],
            'freeze_path':freeze_name,'freeze_sha256':sha(ROOT/freeze_name),'protocol_sha256':PROTOCOL_PIN,
            'execution_source_sha256':sources,'run_metadata_sha256':sha(run/'run_metadata.json'),
            'numerical_versions':versions}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results',type=Path,default=ROOT/'results/S12_matched_budget')
    p.add_argument('--output',type=Path,default=ROOT/'results/S12_matched_budget_independent_audit')
    args=p.parse_args()
    run=args.results.resolve();output=args.output.resolve()
    if run!=ROOT/'results/S12_matched_budget' or output==run or output.exists():
        raise ValueError('Use the fixed completed run and a fresh, distinct audit directory')
    output.mkdir(parents=True,exist_ok=False)
    started=utc()
    (output/'auditor_snapshot.py').write_bytes(Path(__file__).read_bytes())
    result={'status':'running','started_utc':started,'auditor_sha256':sha(Path(__file__)),
            'fixed_derived_float_tolerance':FLOAT_TOLERANCE,'input_directory':str(run),'output_directory':str(output)}
    save(output/'verification.json',result)
    try:
        result.update(evaluate(run,output),status='PASS',completed_utc=utc())
        save(output/'verification.json',result)
    except BaseException as error:
        result.update(status='FAIL',failed_utc=utc(),error_type=type(error).__name__,error=str(error))
        save(output/'verification.json',result)
        (output/'failure_traceback.txt').write_text(traceback.format_exc())
        raise
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
