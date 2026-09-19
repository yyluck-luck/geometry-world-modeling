"""Plot completed S24 scores; never run against partial method outputs."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / 'results/S24_baseline_expansion/scoring'
OUT = ROOT / 'work/S24_reporting_v2'


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    metrics = json.loads((B / 'metrics.json').read_text())
    receipt = json.loads((B / 'receipt.json').read_text())
    assert receipt['status'] == 'PASS' and metrics['passed']
    assert sha(B / 'metrics.json') == receipt['metrics_sha256']
    manifest_path = ROOT / 'work/S24_baseline_expansion/run_manifest.json'
    assert sha(manifest_path) == metrics['manifest_sha256']
    manifest = json.loads(manifest_path.read_text())
    n = len(manifest['frames'])
    assert metrics['frame_count'] == n
    assert not OUT.exists()

    sys.path.append(str(ROOT / 'work/S17C_environment/site-packages'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from PIL import Image

    OUT.mkdir()
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'pdf.fonttype': 42,
                         'svg.fonttype': 'none'})
    style = {'cut3r': ('#0072B2', '-', 'CUT3R'),
             'ttt3r': ('#D55E00', '--', 'TTT3R'),
             'filt3r': ('#009E73', '-.', 'FILT3R')}
    data = {}
    for name in style:
        with np.load(B / (name + '_aligned.npz'), allow_pickle=False) as archive:
            data[name] = {k: archive[k].copy() for k in archive.files}
        assert len(data[name]['ate_m']) == n
        assert len(data[name]['rpe_translation_m']) == n-1
    fields = [('ate_m', 'Position error (m)'),
              ('rpe_translation_m', 'Local translation error (m)'),
              ('rpe_rotation_deg', 'Local rotation error (deg)')]
    fig, axes = plt.subplots(3, 1, figsize=(9.2, 8.1), sharex=True,
                             layout='constrained')
    for name, (color, linestyle, label) in style.items():
        for ax, (field, ylabel) in zip(axes, fields):
            v = data[name][field]
            ax.plot(np.arange(len(v)), v, color=color, ls=linestyle,
                    lw=1.1, label=label)
            ax.set_ylabel(ylabel)
            ax.grid(alpha=.15)
    axis_audit = {}
    for ax, (field, _) in zip(axes, fields):
        maximum = max(float(np.max(data[name][field])) for name in style)
        ax.set_ylim(0, 1.05*maximum if maximum > 0 else 1)
        limits = ax.get_ylim()
        clipped = sum(int(np.count_nonzero((data[name][field] < limits[0]) | (data[name][field] > limits[1]))) for name in style)
        assert clipped == 0, 'All method values must remain visible'
        axis_audit[field] = dict(limits=list(limits), data_max=maximum, clipped_points=clipped)
    axes[0].legend(frameon=False, ncol=3)
    axes[-1].set_xlabel(f'Frame index (all {n} associated frames; {n-1} adjacent pairs)')
    values = ' | '.join(f"{style[name][2]} {metrics['methods'][name]['official'][0]*100:.2f} cm"
                        for name in style)
    fig.suptitle('Position RMSE: ' + values + '\n'
                 'TUM fr1_xyz; existing methods; previously exposed scene\n'
                 'Shared 512 DPT weights / crop; outer FP32, encoder RoPE q/k FP16',
                 fontsize=11)
    for extension in ['png', 'pdf', 'svg']:
        fig.savefig(OUT / ('s24_all_frame_errors.' + extension), dpi=180)
    plt.close(fig)

    selected = []
    fig, axes = plt.subplots(3, 3, figsize=(10.5, 8.5), layout='constrained')
    for row, name in enumerate(style):
        worst = int(metrics['methods'][name]['worst_indices_descending'][0])
        indices = [max(0, min(n-1, worst + offset)) for offset in [-1, 0, 1]]
        selected.append(dict(method=name, worst_index=worst, photo_indices=indices))
        for ax, index in zip(axes[row], indices):
            frame = manifest['frames'][index]
            assert sha(frame['path']) == frame['sha256']
            with Image.open(frame['path']) as photo:
                ax.imshow(photo)
            ax.set_title(f"{style[name][2]}: RGB {index}\n"
                         f"Position error {data[name]['ate_m'][index]*100:.2f} cm", fontsize=10)
            ax.axis('off')
    fig.suptitle('Real photos at each method\'s largest position error and adjacent frames\n'
                 'Selected after scoring; these photos do not establish the error cause',
                 fontsize=11)
    fig.savefig(OUT / 's24_real_residual_photos.png', dpi=160)
    plt.close(fig)
    recipe = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                  metrics_sha256=sha(B / 'metrics.json'), manifest_sha256=sha(manifest_path),
                  plotting_script_sha256=sha(__file__), all_frames=n, all_adjacent_pairs=n-1,
                  photo_selection=selected, post_score_descriptive=True,
                  method_claim='existing baselines only, no new method or generated video',
                  skill='figure-designer: all-time curves, dual color/line encoding, vector exports',
                  visual_qa='PENDING: inspect both PNGs before delivery', font_min_pt=10, axis_audit=axis_audit,
                  correction='v1 set_ylim inside first method loop disabled later y autoscale; v2 sets full union limits after all methods; raw data unchanged')
    (OUT / 'figure_recipe.json').write_text(json.dumps(recipe, indent=2) + '\n')
    print(OUT)


if __name__ == '__main__':
    main()
