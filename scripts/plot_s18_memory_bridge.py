#!/usr/bin/env python3
"""Plot sealed S18 component outputs after independent verification; no models/RGB."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch


def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser()
    for key in ('run','seal','verification','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists();a.output.mkdir(parents=True)
    start=datetime.now(timezone.utc).isoformat();seal=json.loads(a.seal.read_text());verification=json.loads(a.verification.read_text())
    assert verification['status']=='PASS'
    assert any(r.get('role')=='bound output seal' and r.get('sha256')==sha(a.seal) for r in verification['file_hashes'])
    reads=[]
    def bound(name):
        path=(a.run/name).resolve();digest=sha(path);assert seal['identities'][str(path)]==digest
        reads.append(dict(path=str(path),sha256=digest));return path
    meta=json.loads(bound('run_metadata.json').read_text())
    assert meta['status'] in ('SUCCESS','NO_VISIBLE_SOURCE')
    sources=json.loads(bound('map_after_frame1_sources.json').read_text())['sources']
    member=np.asarray([sum(1<<j for j in sources[str(i)]) for i in range(len(sources))],dtype=np.uint8)
    data=[];vote=[]
    for q in range(2):
        with np.load(bound(f'render_query{q}.npz'),allow_pickle=False) as z:
            d=z['depth'].copy();ids=z['surfel_index_map'].copy()
        cats=np.zeros_like(ids,dtype=np.uint8);valid=ids>=0;cats[valid]=member[ids[valid]]
        data.append((d,ids,cats));vote.append(json.loads(bound(f'votes_query{q}.json').read_text()))
    finite=np.concatenate([d[ids>=0] for d,ids,cats in data]);vmax=float(finite.max()) if finite.size else 1.
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':11,'axes.labelsize':10,'svg.fonttype':'none','pdf.fonttype':42})
    fig,axs=plt.subplots(2,2,figsize=(10,6.6),layout='constrained')
    colors=['#f0f0f0','#0072b2','#e69f00','#5d3a9b'];cmap=ListedColormap(colors);norm=BoundaryNorm([-.5,.5,1.5,2.5,3.5],4)
    summaries=[]
    for q,((d,ids,cats),v) in enumerate(zip(data,vote)):
        ax=axs[q,0];heat=ax.imshow(np.ma.masked_where(ids<0,d),cmap='viridis',vmin=0,vmax=vmax,interpolation='nearest')
        ax.set_facecolor(colors[0]);ax.set_title(f'Known camera {q}: original disk depth')
        axs[q,1].imshow(cats,cmap=cmap,norm=norm,interpolation='nearest')
        counts=[int((cats==j).sum()) for j in range(4)]
        axs[q,1].set_title(f'Known camera {q}: photo-source membership')
        text=f'Visible {v["visible_pixels"]:,} / {d.size:,} pixels; candidates {v["candidate_source_ids"]}'
        axs[q,1].set_xlabel(text,fontsize=9)
        summaries.append(dict(query=q,category_pixel_counts=dict(zip(['empty','source0_only','source1_only','both_sources'],counts)),visible_pixels=v['visible_pixels'],candidate_source_ids=v['candidate_source_ids']))
        for axis in axs[q]:
            axis.set_xticks([0,128,256,384,511]);axis.set_yticks([0,96,192,287]);axis.set_ylabel('Render row (pixel)')
        ax.set_xlabel('Render column (pixel)')
    cb=fig.colorbar(heat,ax=axs[:,0],shrink=.83,pad=.02);cb.set_label('Mean disk-vertex depth (model units)')
    # Text IDs and explicit counts supplement categorical colors.
    fig.legend(handles=[Patch(facecolor=c,label=l) for c,l in zip(colors,['Empty','Photo 0 only','Photo 1 only','Photos 0 + 1'])],loc='outside lower center',ncol=4,frameon=False)
    fig.suptitle('S18 | saved real geometry enters the original memory consumer',fontsize=13)
    outputs=[]
    for suffix in ('png','pdf','svg'):
        target=a.output/('s18_memory_visibility.'+suffix);fig.savefig(target,dpi=170);outputs.append(dict(path=target.name,sha256=sha(target),bytes=target.stat().st_size))
    plt.close(fig)
    receipt=dict(status='GENERATED_NOT_YET_VISUALLY_REVIEWED',started_utc=start,completed_utc=datetime.now(timezone.utc).isoformat(),script_sha256=sha(__file__),seal_sha256=sha(a.seal),verification_sha256=sha(a.verification),reads=reads,array_decodes=4,model_calls=0,RGB_reads=0,GT_reads=0,outputs=outputs,queries=summaries,depth_color_range=[0,vmax],caption='Both queries use the same estimated cameras that built this map. Color labels show source membership of the visible first-write surfel; they do not validate association accuracy. Empty pixels remain empty. Original 512x288 widened-FoV disk rendering uses mean vertex depth in model units, not calibrated sensor depth or generated video.',format_scope='Scientific raster fields remain raster; labels, axes and legends are vector in PDF/SVG. No artificial photographs or interpolated display smoothing.')
    (a.output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(status=receipt['status'],queries=summaries,outputs=outputs)))

if __name__=='__main__':main()
