#!/usr/bin/env python3
"""S5 full sequence plots and six atlases covering every fixed image."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from learned_pair_metrics import resize_crop


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--result',type=Path,default=ROOT/'results/S5_cut3r_sequence')
    p.add_argument('--data',type=Path,default=ROOT/'data/tum/rgbd_dataset_freiburg1_xyz')
    args=p.parse_args()
    result=json.loads((args.result/'summary.json').read_text());rows=json.loads((args.result/'records.json').read_text())
    if result['status']!='completed':raise ValueError('Completed evaluation required')
    frozen=json.loads((ROOT/'data/cut3r/S5_inputs.json').read_text())
    a=np.load(args.result/'measurement_comparison.npz',allow_pickle=False)
    out=args.result/'figures';out.mkdir(exist_ok=False)
    plt.rcParams.update({'font.size':10,'svg.fonttype':'none'})
    fig,axs=plt.subplots(3,3,figsize=(12,9),layout='constrained')
    for b in range(3):
        block=[r for r in rows if r['block']==b];t=np.array([r['seconds_from_first'] for r in block]);cut=(t[19]+t[20])/2
        axes=axs[:,b]
        axes[0].plot(t,[r['calibrated']['mae_mm'] for r in block],'-o',ms=3,lw=1.3,c='#0072B2',label='MAE')
        axes[0].plot(t,[r['calibrated']['median_abs_mm'] for r in block],'--s',ms=3,lw=1.3,c='#D55E00',label='Median absolute')
        axes[1].plot(t,[r['relative_pose']['translation_vector_error_mm'] for r in block],'-o',ms=3,c='#0072B2')
        axes[2].plot(t,[r['relative_pose']['rotation_error_deg'] for r in block],'-s',ms=3,c='#D55E00')
        for ax in axes:
            ax.axvspan(cut,t[-1],color='#999999',alpha=.14)
            ax.set_xlim(0,t[-1]);ax.set_ylim(bottom=0);ax.spines[['top','right']].set_visible(False);ax.grid(alpha=.17)
        axes[0].set_title(f'Block {b}: '+('development' if b==0 else 'test'));axes[0].legend(fontsize=8)
        axes[2].set_xlabel('Seconds from block start')
    for i,label in enumerate(['Depth difference (mm)','Translation vector difference (mm)','Relative rotation difference (degrees)']):axs[i,0].set_ylabel(label)
    fig.suptitle('One depth scale at each block start; last four frames shaded',fontsize=13)
    fig.savefig(out/'sequence_errors.png',dpi=180);fig.savefig(out/'sequence_errors.svg');plt.close(fig)
    cmap=plt.get_cmap('viridis').copy();cmap.set_bad('#dedede')
    zmax=max(float(np.max(a[f'block{b}_depth_scaled'])) for b in range(3))
    zmax=max(zmax,max(float(np.max(a[f'block{b}_target'][a[f'block{b}_valid']])) for b in range(3)))
    for b in range(3):
        for page in range(2):
            fig,axs=plt.subplots(4,3,figsize=(16,9),layout='constrained')
            for index,ax in enumerate(axs.ravel()):
                i=page*12+index;f=frozen['blocks'][b]['frames'][i]
                rgb,_=resize_crop(Image.open(args.data/f['rgb']['path']).convert('RGB'),Image.Resampling.LANCZOS)
                depth=a[f'block{b}_depth_scaled'][i];target=np.where(a[f'block{b}_valid'][i],a[f'block{b}_target'][i],np.nan)
                pred_color=cmap(np.clip(depth/zmax,0,1))[:,:,:3];meas_color=cmap(np.ma.masked_invalid(target/zmax))[:,:,:3]
                tile=np.concatenate([np.asarray(rgb)/255,meas_color,pred_color],axis=1)
                ax.imshow(tile);ax.set_xticks([]);ax.set_yticks([])
                r=rows[b*24+i];ax.set_title(f"Frame {i:02d} | MAE {r['calibrated']['mae_mm']:.1f} mm"+(' | SCALE FIT' if i==0 else ''),fontsize=10)
            sm=plt.cm.ScalarMappable(norm=plt.Normalize(0,zmax),cmap=cmap)
            fig.colorbar(sm,ax=axs.ravel().tolist(),location='right',shrink=.7,label='Depth (m); shared across all six atlases',pad=.015)
            fig.suptitle(f'Block {b}, frames {page*12}–{page*12+11} | each tile: RGB / measured valid depth / scaled CPU prediction',fontsize=13)
            stem=f'block{b}_frames{page*12:02d}_{page*12+11:02d}'
            fig.savefig(out/f'{stem}.png',dpi=160);plt.close(fig)
    (out/'captions.md').write_text('''# S5 figures

Sequence plot: One first-frame measured scale per block is held fixed for subsequent images. Depth mean/median differences and relative-to-start pose differences are shown for every frame in each of three temporal blocks from the same environment. Shading identifies the last four frames; only the shaded images in blocks 1 and 2 form the eight-image primary test. The first point is calibration description. All axes begin at zero and include all observed values, with separate panel ranges. Trends are descriptive, not a fitted drift model or independent-scene benchmark.

Six atlases: All 72 fixed RGB images are shown in time order, alongside measured depth restricted to the prespecified mask and the CPU prediction using the block's first-frame scalar. Each tile's label gives that frame's MAE. Grey means excluded measured pixels. The depth color scale is shared across all six atlases and includes the actual maximum; no image or residual was selected by performance. Source images: TUM RGB-D freiburg1_xyz, CC BY 4.0, https://cvg.cit.tum.de/data/datasets/rgbd-dataset . No novel video frames were generated.

Design audit: time-series line/marker encoding with units, independent data panels, full axis ranges, separate development/test labels, explicit eight-image denominator. Depth color uses Viridis and missing data grey. Main chart exports SVG text; atlases retain image data. Visual inspection is required before delivery.
''')
    (out/'manifest.json').write_text(json.dumps(dict(created_utc=datetime.now(timezone.utc).isoformat(),
        summary_sha256=hashlib.sha256((args.result/'summary.json').read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rgb_images_shown=72,shared_depth_max_m=zmax),indent=2))
    print(out)


if __name__=='__main__':main()
