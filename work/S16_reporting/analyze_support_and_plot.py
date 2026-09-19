#!/usr/bin/env python3
"""Explicitly post-answer support audit and full-policy figure, no model/RGB reads."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import csv
import hashlib
import json
import sys
import time
import traceback
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

POLICIES = ['all_new', 'half_blend', 'pool_new', 'split_new',
            'matched_absolute_new', 'model_confidence']
DISPLAY = ['All new', 'Half blend', 'Photo pool', 'Time split',
           'Matched absolute', 'Model confidence']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def masked_counts(mask, interaction):
    fields = dict(count=mask, j_positive=mask & (interaction > 0),
                  j_negative=mask & (interaction < 0), j_nonzero=mask & (interaction != 0))
    result = {name: {'per_target': x.sum(axis=(1, 2)).tolist(), 'total_pixel_visits': int(x.sum())}
              for name, x in fields.items()}
    integer_sum = (interaction * mask).sum(axis=(1, 2))
    result['j_integer_sum'] = dict(per_target=integer_sum.tolist(), total=int(integer_sum.sum()))
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    root, out = Path(args.root), Path(args.output)
    out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    paths = dict(scores=root/'results/S16_source_interference/interference.json',
                 layers=root/'results/S16_source_interference/source_layers.npz',
                 maps=root/'results/S16_source_interference/interaction_maps.npz',
                 gt=root/'results/S15B_consumer_scores/evaluation_gt.npz',
                 producer=root/'results/S16_source_interference/run_metadata.json',
                 independent=root/'results/S16_interference_independent/verification.json')
    receipt = dict(started_utc=datetime.now(timezone.utc).isoformat(),
                   scope='Post-answer, post-S16 support audit; no new protocol or method',
                   python=sys.executable, numpy=np.__version__, matplotlib=matplotlib.__version__,
                   source_sha256=sha(__file__), input_identities={str(p): sha(p) for p in paths.values()},
                   rgb_decodes=0, sensor_png_decodes=0, model_calls=0, npz_files_opened=3)
    try:
        producer = json.loads(paths['producer'].read_text())
        independent = json.loads(paths['independent'].read_text())
        assert producer['status'] == 'PASS' and independent['status'] == 'PASS'
        data = json.loads(paths['scores'].read_text())
        assert list(data['policies']) == POLICIES
        with np.load(paths['gt'], allow_pickle=False) as archive:
            gt = archive['depth_m']
        gv = np.isfinite(gt) & (gt > 0)
        den = gv.sum(axis=(1, 2))
        audit, rows = {}, []
        array_decodes = 1
        with np.load(paths['layers'], allow_pickle=False) as layers, np.load(paths['maps'], allow_pickle=False) as maps:
            old = layers['never_z_model']; old_ids = layers['never_source_pixel']; array_decodes += 2
            for name in POLICIES:
                new = layers[name+'_z_model']; new_ids = layers[name+'_source_pixel']
                fixed_saved = maps[name+'_fixed_candidates_depth_competition']
                interaction = maps[name+'_interaction']; array_decodes += 4
                old_valid, new_valid = old > 0, new > 0
                fixed = np.all(old_valid == new_valid, axis=0) & np.all(old_ids == new_ids, axis=0)
                assert np.array_equal(fixed, fixed_saved)
                assert np.array_equal(den, data['policies'][name]['denominators'])
                fixed_gt = fixed & gv
                changed = np.any(old != new, axis=0)
                at_least_two = old_valid.sum(axis=0) >= 2
                subsets = dict(fixed_gt=fixed_gt,
                               fixed_gt_any_z_changed=fixed_gt & changed,
                               fixed_gt_at_least_two_valid_sources=fixed_gt & at_least_two,
                               fixed_gt_changed_and_2valid=fixed_gt & changed & at_least_two,
                               fixed_gt_all_sources_missing=fixed_gt & ~np.any(old_valid, axis=0),
                               fixed_gt_no_z_changed=fixed_gt & ~changed)
                audit[name] = {key: masked_counts(mask, interaction) for key, mask in subsets.items()}
                assert audit[name]['fixed_gt']['count']['per_target'] == data['policies'][name]['components'][0]['gt_pixel_counts']
                for key, statistics in audit[name].items():
                    for ti, target in enumerate([20, 21, 22, 23]):
                        rows.append(dict(policy=name, target=target, subset=key,
                                         gt_denominator=int(den[ti]),
                                         **{field: value['per_target'][ti] for field, value in statistics.items()}))
        audit_payload = dict(schema='s16-post-answer-fixed-support-audit-v1',
                             target_indices=[20, 21, 22, 23], gt_denominators=den.tolist(),
                             count_unit='target-pixel visits; not independent samples',
                             changed_definition='Exact model-unit layer z inequality in any source; not a significance threshold',
                             two_valid_definition='At least two old source layers valid; validity is unchanged in fixed class',
                             evidence_scope='Post-answer support accounting, does not replace the frozen S16 outcomes', policies=audit)
        save(out/'fixed_support_audit.json', audit_payload)
        with (out/'fixed_support_audit.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)

        plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':9, 'axes.titlesize':10,
                             'axes.labelsize':9, 'xtick.labelsize':8, 'ytick.labelsize':8,
                             'pdf.fonttype':42, 'svg.fonttype':'none'})
        fig = plt.figure(figsize=(10.4, 9.2))
        gs = fig.add_gridspec(3, 3, height_ratios=[1.28, 1, 1], hspace=.67, wspace=.27)
        ax = fig.add_subplot(gs[0, :])
        matrix = np.array([[p['interaction_mean_delta1'],
                            *[c['interaction_mean_delta1'] for c in p['components']]]
                           for p in data['policies'].values()]) * 100
        im = ax.imshow(matrix, cmap='RdBu', norm=TwoSlopeNorm(vmin=-2.1, vcenter=0, vmax=2.1), aspect='auto')
        ax.set_yticks(range(6), DISPLAY)
        ax.set_xticks(range(4), ['Total interaction I', 'Fixed candidate IDs', 'Source-pixel routing', 'Source coverage'])
        ax.tick_params(top=False, bottom=False, left=False)
        ax.set_title('(a) Interaction and its three additive spatial contributions', loc='left', pad=10)
        for row in range(6):
            for col in range(4):
                text = f'{matrix[row,col]:+.3f}' if matrix[row,col] else '0.000'
                ax.text(col, row, text, ha='center', va='center', fontsize=9,
                        color='white' if abs(matrix[row,col]) > 1.2 else '#202020')
        colorbar = fig.colorbar(im, ax=ax, fraction=.025, pad=.025)
        colorbar.set_label('Delta1 percentage points')
        all_marginal = []
        for p in data['policies'].values():
            all_marginal.extend([100*m['single_mean_delta1'] for m in p['marginals']])
            all_marginal.extend([100*m['joint_marginal_mean_delta1'] for m in p['marginals']])
        limit = max(abs(x) for x in all_marginal) * 1.18
        bars = []
        for index, (name, label) in enumerate(zip(POLICIES, DISPLAY)):
            current = fig.add_subplot(gs[1 + index // 3, index % 3])
            marginal = data['policies'][name]['marginals']
            single = np.array([m['single_mean_delta1'] for m in marginal])*100
            joint = np.array([m['joint_marginal_mean_delta1'] for m in marginal])*100
            x = np.arange(4)
            a = current.bar(x-.19, single, width=.36, color='#0072B2', edgecolor='#003A5E', label='Single: others stay old')
            b = current.bar(x+.19, joint, width=.36, color='#E69F00', edgecolor='#764D00', label='Joint marginal: others updated')
            current.axhline(0, color='#333333', lw=.8)
            current.set_ylim(-limit, limit)
            current.set_yticks([-1, -.5, 0, .5, 1])
            current.set_xticks(x, ['0', '3', '6', '9'])
            current.set_xlabel('Source frame')
            if index % 3 == 0: current.set_ylabel('Delta1 gain (pp)')
            current.set_title(f'({chr(98+index)}) {label}', loc='left')
            current.grid(axis='y', color='#DADADA', linewidth=.5)
            current.set_axisbelow(True)
            current.spines[['top','right']].set_visible(False)
            for xi, si, ji in zip(x, single, joint):
                # Shape distinguishes series even in monochrome.
                current.plot(xi-.19, si, 'o', color='#003A5E', ms=3)
                current.plot(xi+.19, ji, 's', color='#764D00', ms=3)
            bars = [a,b]
        fig.legend(bars, ['Single: others stay old (circle)', 'Joint marginal: others updated (square)'],
                   loc='lower center', bbox_to_anchor=(.5,.05), ncol=2, frameon=False, fontsize=9)
        fig.text(.5,.025, 'Saved-data diagnosis | Four target frames, equal weight | Aggregate gains, not pixel-level sign reversals',
                 ha='center', fontsize=9)
        fig.subplots_adjust(left=.16, right=.95, top=.95, bottom=.15)
        for suffix in ['pdf','svg','png']:
            fig.savefig(out/f's16_interaction_summary.{suffix}', dpi=180, facecolor='white')
        plt.close(fig)
        save(out/'figure_values.json', dict(policies=POLICIES, matrix_columns=['total_I','fixed','routing','coverage'],
                                          matrix_percentage_points=matrix.tolist(),
                                          marginals={name:data['policies'][name]['marginals'] for name in POLICIES}))
        assert all(sha(p) == receipt['input_identities'][str(p)] for p in paths.values())
        receipt.update(status='PASS', actual_array_decodes=array_decodes,
                       independent_status=independent['status'], independent_completed_utc=independent['completed_utc'],
                       unchanged_input_identities=True,
                       outputs={p.name:sha(p) for p in out.iterdir() if p.is_file()})
    except BaseException as exc:
        receipt.update(status='FAIL', error=repr(exc), traceback=traceback.format_exc())
    receipt.update(completed_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic()-start)
    save(out/'receipt.json', receipt)
    print(json.dumps(receipt))
    return int(receipt['status']!='PASS')


if __name__ == '__main__':
    raise SystemExit(main())
