#!/usr/bin/env python3
"""Post-hoc error-tail inspection of all eight frozen primary test queries.

Only reads saved depths. Does not alter primary masks or recalculate results
after filtering residuals. Thresholds are descriptive bins, not validity rules.
"""
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'results/S3_rgbd_memory'
OUT = SOURCE / 'posthoc_residuals'
METHODS = ('first_write', 'frame_mean')


def main():
    verification = json.loads((SOURCE / 'verification.json').read_text())
    if verification['status'] != 'passed':
        raise ValueError('Requires passed primary verification')
    OUT.mkdir(exist_ok=True)
    rows, hashes, pooled = [], {}, {m: [] for m in METHODS}
    plt.rcParams.update({'font.size': 10, 'svg.fonttype': 'none'})
    fig, axes = plt.subplots(2, 4, figsize=(13, 7), sharex=True, sharey=True)
    colors = ('#0072B2', '#D55E00')
    depth_cmap = plt.get_cmap('viridis').copy(); depth_cmap.set_bad('#dddddd')
    residual_cmap = plt.get_cmap('RdBu_r').copy(); residual_cmap.set_bad('#dddddd')
    for bi, block in enumerate((1, 2)):
        maps, axmaps = plt.subplots(4, 3, figsize=(10.5, 10))
        for query in range(4):
            path = SOURCE / f'block{block}_stride16_bias00/query_{query}_depths.npz'
            hashes[str(path.relative_to(SOURCE))] = hashlib.sha256(path.read_bytes()).hexdigest()
            with np.load(path) as z:
                common, target, valid = z['common'], z['target'], z['target_valid']
                n = int(common.sum())
                target_image = np.where(valid, target, np.nan)
                imdepth = axmaps[query, 0].imshow(target_image, cmap=depth_cmap, vmin=0, vmax=5)
                axmaps[query, 0].set_ylabel(f'Query {query}', fontsize=11)
                for mi, method in enumerate(METHODS):
                    diff = (z[method][common] - target[common]) * 1000
                    if not np.all(np.isfinite(diff)) or n == 0:
                        raise ValueError('Invalid primary residual support')
                    pooled[method].append(diff)
                    row = dict(block=block, query=query, method=method, common_pixels=n,
                               target_valid_pixels=int(valid.sum()), common_coverage_fraction=n/int(valid.sum()),
                               median_abs_mm=float(np.median(np.abs(diff))), mae_mm=float(np.mean(np.abs(diff))),
                               p90_abs_mm=float(np.percentile(np.abs(diff), 90)), max_abs_mm=float(np.max(np.abs(diff))),
                               signed_mean_mm=float(diff.mean()),
                               abs_ge100mm_fraction=float(np.mean(np.abs(diff)>=100)),
                               abs_ge500mm_fraction=float(np.mean(np.abs(diff)>=500)),
                               positive_ge100mm_fraction=float(np.mean(diff>=100)),
                               negative_le_minus100mm_fraction=float(np.mean(diff<=-100)))
                    rows.append(row)
                    ordered = np.sort(np.abs(diff))
                    axes[bi, query].step(ordered, np.arange(1, n+1)/n, where='post', color=colors[mi],
                                        linestyle=('-', '--')[mi], label=('First write', 'Frame mean')[mi])
                    residual_image = np.full_like(target, np.nan)
                    residual_image[common] = diff
                    imerr = axmaps[query, mi+1].imshow(residual_image, cmap=residual_cmap, vmin=-1000, vmax=1000)
                axes[bi, query].set_title(f'Block {block}, query {query}\nn = {n}, target coverage {100*n/valid.sum():.2f}%')
                axes[bi, query].set_xscale('symlog', linthresh=10)
                axes[bi, query].set_xlim(0, max(float(np.max(np.abs(v))) for v in pooled[METHODS[0]]+pooled[METHODS[1]])*1.05)
                axes[bi, query].grid(alpha=.2)
                for ax in axmaps[query]:
                    ax.set_xticks([]); ax.set_yticks([])
        axmaps[0, 0].set_title('Held-out measured depth (m)')
        axmaps[0, 1].set_title('First write residual (mm)')
        axmaps[0, 2].set_title('Frame mean residual (mm)')
        maps.suptitle(f'Post-hoc inspection: all primary queries in test block {block}', fontsize=13)
        maps.subplots_adjust(top=.91, bottom=.11, wspace=.1, hspace=.1, right=.86)
        cax = maps.add_axes([.89, .54, .017, .32])
        maps.colorbar(imdepth, cax=cax, label='Measured depth (m)')
        cax = maps.add_axes([.89, .15, .017, .32])
        maps.colorbar(imerr, cax=cax, label='Prediction minus measurement (mm)', extend='both')
        maps.text(.5, .036, 'Grey: outside the evaluated mask. Residual colours saturate at ±1000 mm; numerical statistics retain every value.\nSparse point-centre projection, original measurements, stride 16. No learned geometry or generated video.', ha='center', fontsize=9)
        maps.savefig(OUT / f'block{block}_residual_atlas.png', dpi=170)
        maps.savefig(OUT / f'block{block}_residual_atlas.svg')
        plt.close(maps)
    for ax in axes[1]: ax.set_xlabel('Absolute depth difference (mm)')
    for ax in axes[:, 0]: ax.set_ylabel('Fraction of common pixels')
    axes[0, 0].legend(loc='lower right', fontsize=8)
    fig.suptitle('Post-hoc residual distributions: all eight original-measurement test queries', fontsize=13)
    fig.text(.5, .015, 'Same common pixels for both rules. Complete tails retained; linear x-axis from 0–10 mm, logarithmic beyond.\nThese empirical pixel distributions do not provide independent-scene confidence intervals.', ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .08, 1, .94))
    fig.savefig(OUT / 'all_primary_query_ecdf.png', dpi=170)
    fig.savefig(OUT / 'all_primary_query_ecdf.svg')
    plt.close(fig)
    with (OUT / 'per_query_tail_statistics.csv').open('w') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    totals = {}
    for method in METHODS:
        d = np.concatenate(pooled[method])
        totals[method] = dict(n=int(d.size), pooled_mae_mm=float(np.mean(np.abs(d))),
                             pooled_median_abs_mm=float(np.median(np.abs(d))),
                             pooled_p90_abs_mm=float(np.percentile(np.abs(d), 90)),
                             abs_ge100mm_pixels=int(np.sum(np.abs(d)>=100)),
                             abs_ge500mm_pixels=int(np.sum(np.abs(d)>=500)),
                             positive_ge100mm_pixels=int(np.sum(d>=100)),
                             negative_le_minus100mm_pixels=int(np.sum(d<=-100)))
    summary = dict(completed_utc=datetime.now(timezone.utc).isoformat(), label='Post-hoc diagnostic, not a new primary metric',
                   condition='Test blocks 1 and 2, stride 16, original measurements', distinct_queries=8,
                   note='Pooled values weight pixels; they differ from the predeclared unweighted mean of query metrics. No residuals excluded.',
                   script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   source_sha256=hashes, pooled=totals, query_statistics=rows)
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps({'completed': True, 'pooled': totals, 'output': str(OUT)}))


if __name__ == '__main__':
    main()
