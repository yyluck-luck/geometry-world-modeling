#!/usr/bin/env python3
"""Show both frozen images and all held-out residuals, without cherry-picking."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

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
    p.add_argument('--result',type=Path,default=ROOT/'results/S4_cut3r_pair_verified')
    p.add_argument('--data',type=Path,default=ROOT/'data/tum/rgbd_dataset_freiburg1_xyz')
    args=p.parse_args()
    result=json.loads((args.result/'summary.json').read_text())
    if result['status']!='completed':raise ValueError('Completed evaluation required')
    out=args.result/'figures'
    out.mkdir(exist_ok=False)
    a=np.load(args.result/'measurement_comparison.npz',allow_pickle=False)
    plt.rcParams.update({'font.size':10,'axes.titlesize':11,'svg.fonttype':'none'})
    depth_cmap=plt.get_cmap('viridis').copy();depth_cmap.set_bad('#dedede')
    error_cmap=plt.get_cmap('magma').copy();error_cmap.set_bad('#dedede')
    allz=np.concatenate([a[f'target{i}'][a[f'valid{i}']] for i in range(2)]+[a[f'cpu_depth{i}_scaled'].ravel() for i in range(2)])
    zmax=float(allz.max())
    errors=[np.where(a[f'valid{i}'],np.abs(a[f'cpu_depth{i}_scaled']-a[f'target{i}'])*1000,np.nan) for i in range(2)]
    emax=float(max(np.nanmax(e) for e in errors))
    fig,axs=plt.subplots(2,4,figsize=(12,6.8),layout='constrained')
    for i in range(2):
        rgb,_=resize_crop(Image.open(args.data/result['frames'][i]['rgb']).convert('RGB'),Image.Resampling.LANCZOS)
        imgs=[np.asarray(rgb),np.where(a[f'valid{i}'],a[f'target{i}'],np.nan),a[f'cpu_depth{i}_scaled'],errors[i]]
        for j,x in enumerate(imgs):
            ax=axs[i,j]
            if j==0: ax.imshow(x)
            else:
                im=ax.imshow(x,cmap=error_cmap if j==3 else depth_cmap,vmin=0,vmax=emax if j==3 else zmax)
                fig.colorbar(im,ax=ax,shrink=.62,pad=.02,label='Absolute difference (mm)' if j==3 else 'Depth (m)')
            ax.set_xticks([]);ax.set_yticks([])
            if i==0:ax.set_title(['RGB crop','Measured depth (valid mask)','CPU predicted depth','All valid residuals'][j])
        s=result['runs']['cpu']['depth'][i]['calibrated']
        axs[i,0].set_ylabel(('Frame 0: scale fit','Frame 1: held out')[i])
        axs[i,3].set_xlabel(f"MAE {s['mae_mm']:.1f} mm; n={s['n']:,}")
    fig.suptitle('Two real images: scale fitted on frame 0 only',fontsize=14)
    fig.savefig(out/'depth_and_residuals.png',dpi=180)
    fig.savefig(out/'depth_and_residuals.svg')
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(6.7,4.1),layout='constrained')
    for device,color,style in [('cpu','#0072B2','-'),('mps','#D55E00','--')]:
        x=np.sort(np.abs(a[f'{device}_depth1_scaled'][a['valid1']]-a['target1'][a['valid1']])*1000)
        ax.plot(x,np.arange(1,len(x)+1)/len(x),label=device.upper(),color=color,linestyle=style,lw=1.7)
    ax.axvline(30,color='#555555',ls=':',label='30 mm reference')
    ax.set(xlabel='Absolute difference from measured depth (mm)',ylabel='Fraction of valid held-out pixels',
           xlim=(0,float(x.max())*1.02),ylim=(0,1),title='Frame 1 residual distribution (37,325 pixels)')
    ax.spines[['top','right']].set_visible(False);ax.legend(loc='lower right');ax.grid(alpha=.18)
    fig.savefig(out/'heldout_error_distribution.png',dpi=180);fig.savefig(out/'heldout_error_distribution.svg')
    plt.close(fig)
    captions='''# S4 figure captions and audit

Figure 1. The frozen held-out image has CPU mean absolute depth difference 32.324 mm after one scalar is fitted only on frame 0. Both selected images are shown, with shared depth and error scales. Grey pixels are excluded by the prespecified measured-depth mask; predicted depth is shown across the whole crop. The error scale covers the actual maximum without clipping. These are one calibrated image and one held-out image from one environment, not independent scenes. All images use the official 224 crop.

Figure 2. CPU and MPS yield nearly overlapping held-out error distributions, using the identical CPU-fitted scalar and all 37,325 prespecified valid pixels. The horizontal axis extends to the actual maximum, with a 30 mm reference. Pixel errors are spatially dependent; no confidence interval or population significance is claimed.

Design: 2-by-4 evidence grid plus ECDF; numerical depth uses Viridis and error uses Magma with labelled color bars. Missing measurements are grey. ECDF uses color and line style, not color alone. SVG has editable text; raster image panels retain original spatial data. Titles, units, complete ranges and denominators are explicit. All output images require visual inspection before delivery.

Source photographs and depth: TUM RGB-D freiburg1_xyz, CC BY 4.0; https://cvg.cit.tum.de/data/datasets/rgbd-dataset . Geometry: official CUT3R 224 intermediate checkpoint with documented signed-RoPE/blocking-transfer compatibility, not VMem video generation.
'''
    (out/'captions.md').write_text(captions)
    (out/'manifest.json').write_text(json.dumps({'created_utc':datetime.now(timezone.utc).isoformat(),
        'summary_sha256':hashlib.sha256((args.result/'summary.json').read_bytes()).hexdigest(),
        'figure_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'color_max_depth_m':zmax,'color_max_error_mm':emax,'pixel_counts':[int(a[f'valid{i}'].sum()) for i in range(2)]},indent=2))
    print(out)


if __name__=='__main__':main()
