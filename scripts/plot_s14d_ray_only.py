#!/usr/bin/env python3
"""Supporting diagnostic: all five raw predicted z maps, one global color scale."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'results/S14D_ray_only_probe/query_outputs.npz'
out=ROOT/'work/S14D_reporting';out.mkdir(parents=True,exist_ok=True)
with np.load(source,allow_pickle=False) as data:
    maps=[data[f'call{i}_pts3d_in_self_view'][0,:,:,2].copy() for i in range(5)]
assert all(m.shape==(224,224) and np.isfinite(m).all() for m in maps)
lo=min(float(m.min()) for m in maps);hi=max(float(m.max()) for m in maps)
plt.rcParams.update({'font.size':10,'svg.fonttype':'none'})
fig,axes=plt.subplots(1,5,figsize=(12.6,3.35),layout='constrained')
titles=['Q0 / NaN dummy','Q0 / zero dummy','Q1 / +local x','Q2 / -local x','Q3 / +local z']
for ax,data,title in zip(axes,maps,titles):
    img=ax.imshow(data,cmap='viridis',vmin=lo,vmax=hi,origin='upper',interpolation='nearest')
    ax.set_title(title,fontsize=10);ax.set_xticks([0,112,223]);ax.set_yticks([0,112,223]);ax.set_xlabel('pixel u')
axes[0].set_ylabel('pixel v')
fig.colorbar(img,ax=axes,shrink=.77,label='Predicted z (model units)')
fig.suptitle('CUT3R direct ray queries: target RGB absent\nReal history + synthetic cameras; no accuracy evaluation',fontsize=12)
paths=[]
for ext in ['png','svg']:
    p=out/f's14d_all_five_depth_maps.{ext}';fig.savefig(p,dpi=180);paths.append(p)
plt.close(fig)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
(out/'figure_receipt.json').write_text(json.dumps(dict(created_utc=datetime.now(timezone.utc).isoformat(),
    source_path=str(source),source_sha256=sha(source),plot_source_sha256=sha(Path(__file__)),
    calls_shown=list(range(5)),pixels_per_call=224*224,global_min=lo,global_max=hi,
    crop=False,clipping=False,smoothing=False,metric_recomputation=False,
    svg_contains_native_axes_and_raster_measurement_maps=True,
    outputs={p.name:sha(p) for p in paths}),indent=2)+'\n')
print(json.dumps({'plot_paths':[str(p) for p in paths],'global_range':[lo,hi]}))
