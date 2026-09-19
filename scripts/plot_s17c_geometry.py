#!/usr/bin/env python3
"""S17C sealed-result plots: two processed real RGB tensors, all pixels, all 400 steps.
No PNG input, model, GT, metric calibration or generated-video claim.
"""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import hashlib
import json
import shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

DEPTH_DISPLAY_MAX = 5.0  # predetermined model units; never fitted from results
FRAMES = [0, 1]


def utc(): return datetime.now(timezone.utc).isoformat()
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def require(ok, text):
    if not ok: raise ValueError(text)
def write(p, value): Path(p).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def plot_scene(rgb, depths, before, after, stats, out):
    fig, axes = plt.subplots(2, 3, figsize=(7.6, 5.65))
    fig.subplots_adjust(left=.04, right=.985, top=.825, bottom=.215, wspace=.055, hspace=.15)
    cmap = plt.get_cmap('viridis').copy();cmap.set_bad('#d5d8dd')
    maskmap = ListedColormap(['#e7ebef', '#d55e00'])
    norm = BoundaryNorm([-.5, .5, 1.5], 2)
    for i in FRAMES:
        axes[i,0].imshow(rgb[i])
        valid = np.isfinite(depths[i]) & (depths[i]>0)
        heat = axes[i,1].imshow(np.ma.array(depths[i],mask=~valid), cmap=cmap, vmin=0,vmax=DEPTH_DISPLAY_MAX)
        axes[i,2].imshow(before[i]!=after[i], cmap=maskmap, norm=norm)
        axes[i,0].text(.025,.055,f'Frame {i}', transform=axes[i,0].transAxes,fontsize=9,color='white',
            bbox=dict(facecolor='black',alpha=.65,edgecolor='none',pad=2))
        axes[i,2].text(.02,.04,f"Changed: {stats[i]['confidence_changed']:,} / 196,608",transform=axes[i,2].transAxes,
            fontsize=9,bbox=dict(facecolor='white',alpha=.88,edgecolor='none',pad=2))
        for ax in axes[i]:
            ax.set_xticks([]);ax.set_yticks([])
            for sp in ax.spines.values(): sp.set_visible(False)
    for ax,title in zip(axes[0],['Processed real RGB | 512 × 384','Aligned camera depth | model units','Confidence changed | every pixel']):
        ax.set_title(title, pad=6)
    cbax=fig.add_axes([.36,.165,.285,.016])
    cb=fig.colorbar(heat,cax=cbax,orientation='horizontal',extend='max',ticks=[0,1,2,3,4,5]);cb.ax.tick_params(labelsize=9,length=2)
    fig.legend(handles=[Patch(color='#e7ebef',label='Unchanged'),Patch(color='#d55e00',label='Changed')],
        loc='lower right',bbox_to_anchor=(.99,.138),frameon=False,ncol=2,fontsize=9,handlelength=1)
    fig.suptitle('S17C | Embedded geometry and confidence cleaning',x=.04,y=.965,ha='left',fontsize=11,fontweight='bold')
    fig.text(.04,.909,'Fixed Bonn frames 0 / 1; original wrapper, no pose or depth priors.',fontsize=9)
    fig.text(.04,.083,'Both depth maps share the predeclared 0–5 display range; units are not metres.',fontsize=9)
    fig.text(.04,.045,'Cleaning changes confidence only. No GT, metric accuracy, Surfel objects or video here.',fontsize=9)
    for ext in ['png','pdf','svg']: fig.savefig(out/f's17c_two_frame_geometry.{ext}',dpi=220,facecolor='white')
    plt.close(fig)


def plot_trace(trace, final_loss, stats, out):
    fig, axes=plt.subplots(3,1,figsize=(7.6,7.0),gridspec_kw={'height_ratios':[1.3,1,1.1]})
    fig.subplots_adjust(left=.13,right=.965,top=.86,bottom=.19,hspace=.60)
    iterations=np.array([x['iteration'] for x in trace])
    losses=np.array([x['loss_before_step'] for x in trace]);lrs=np.array([x['lr'] for x in trace])
    axes[0].plot(iterations,losses,color='#0072b2',linewidth=1.5,label='All 400 native pre-step losses')
    axes[0].scatter([400],[final_loss],s=28,facecolors='none',edgecolors='#d55e00',marker='o',label='One read-only postfinal objective')
    axes[0].set(xlabel='Native iteration (0–399); final read-only value at 400',ylabel='Alignment objective')
    axes[0].legend(frameon=False,fontsize=9,loc='best')
    axes[1].plot(iterations,lrs,color='#009e73',linewidth=1.5)
    axes[1].set(xlabel='Native iteration (0–399)',ylabel='Learning rate',xlim=(0,399))
    labels=[];zero=[];positive=[]
    for i in FRAMES:
        for label,stage in [('Before','before'),('After','after')]:
            labels.append(f'Frame {i}\n{label}')
            zero.append(stats[i][f'confidence_{stage}_zero']);positive.append(stats[i][f'confidence_{stage}_positive'])
    x=np.arange(4)
    axes[2].bar(x,positive,color='#0072b2',width=.65,label='Positive confidence')
    axes[2].bar(x,zero,bottom=positive,color='#d55e00',width=.65,label='Zero confidence')
    axes[2].set(xticks=x,xticklabels=labels,ylabel='Pixel count',ylim=(0,225000))
    axes[2].set_yticks([0,100000,196608]);axes[2].set_yticklabels(['0','100,000','196,608'])
    for j in x: axes[2].text(j,199000,f'0: {zero[j]:,}',ha='center',fontsize=9)
    handles, legend_labels=axes[2].get_legend_handles_labels()
    fig.legend(handles,legend_labels,frameon=False,fontsize=9,loc='lower center',bbox_to_anchor=(.5,.07),ncol=2)
    for ax in axes:
        ax.grid(axis='y',color='#d6dbe0',linewidth=.5,alpha=.8);ax.set_axisbelow(True)
        ax.spines[['top','right']].set_visible(False)
    fig.suptitle('S17C | Complete optimization trace and confidence counts',x=.04,y=.968,ha='left',fontsize=11,fontweight='bold')
    fig.text(.04,.921,'400 native Adam steps; one additional objective read, with no extra optimizer step.',fontsize=9)
    fig.text(.04,.023,'No subsampling, confidence threshold or error bar. Counts cover every pixel in both frames.',fontsize=9)
    for ext in ['png','pdf','svg']:fig.savefig(out/f's17c_full_trace_and_confidence.{ext}',dpi=220,facecolor='white')
    plt.close(fig)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['manifest','seal','verification','run-dir','output']:p.add_argument('--'+name,type=Path,required=True)
    for name in ['manifest-sha256','seal-sha256','verification-sha256','verifier-source-sha256']:p.add_argument('--'+name,required=True)
    a=p.parse_args();require(not a.output.exists(),'Preserve earlier reporting directory');a.output.mkdir(parents=True)
    r=dict(schema='s17c-reporting-v1',status='RUNNING',started_utc=utc(),native_rgb_png_decodes=0,
        saved_rgb_tensor_decodes=0,numerical_array_decodes=0,model_calls=0,sensor_depth_decodes=0,
        video_generated=False,metric_scale_fit=False,fixed_frames=FRAMES,depth_display_range=[0,DEPTH_DISPLAY_MAX],input_ids=[])
    try:
        for path,h in [(a.manifest,a.manifest_sha256),(a.seal,a.seal_sha256),(a.verification,a.verification_sha256)]:
            require(sha(path)==h,'Externally bound reporting input '+str(path))
            r['input_ids'].append(dict(path=str(path.resolve()),sha256=h))
        manifest=json.loads(a.manifest.read_text());seal=json.loads(a.seal.read_text());verification=json.loads(a.verification.read_text())
        require(manifest['schema']=='s17c-embedded-two-frame-geometry-manifest-v1','Correct input manifest')
        require(verification['schema']=='s17c-embedded-independent-verification-v1' and verification['status']=='PASS','Completed independent numerical verification')
        require(verification['source_sha256']==a.verifier_source_sha256,'Externally bound independent verifier source')
        for role,path,h in [('bound manifest',a.manifest,a.manifest_sha256),('bound output seal',a.seal,a.seal_sha256)]:
            require(any(x.get('role')==role and x.get('path')==str(path.resolve()) and x.get('sha256')==h for x in verification['file_hashes']), 'Independent verifier binding: '+role)
        def bound_file(relative):
            f=a.run_dir/relative;digest=sha(f)
            require(seal['identities'].get(str(f.resolve()))==digest,'Sealed file identity: '+relative)
            r['input_ids'].append(dict(path=str(f.resolve()),sha256=digest));return f
        meta=json.loads(bound_file('run_metadata.json').read_text())
        require(meta['schema']=='s17c-embedded-two-frame-geometry-run-v1' and meta['status']=='SUCCESS','Completed native run')
        require(meta['manifest_sha256']==a.manifest_sha256,'Native manifest binding')
        require([x['index']for x in manifest['history_images']]==FRAMES,'All two predetermined images')
        require(meta['counters']['optimization_iterations']==400 and meta['counters']['optimizer_steps']==400 and meta['counters']['postfinal_objective_evaluations']==1,'Native call counts')
        trace=meta['optimization_trace']
        require(len(trace)==400 and [x['iteration']for x in trace]==list(range(400)),'Every native iteration exactly once')
        require(all(np.isfinite(x['loss_before_step'])and np.isfinite(x['lr'])for x in trace),'Finite trace')
        final_loss=meta['postfinal_objective'];require(np.isfinite(final_loss),'Finite postfinal objective')
        def load(relative,keys):
            f=bound_file(relative);require(meta['output_files'][relative]['sha256']==sha(f),'Metadata output identity')
            with np.load(f,allow_pickle=False)as store:
                values={k:store[k].copy()for k in keys};r['numerical_array_decodes']+=len(keys)
            for k,v in values.items():
                desc=meta['array_files'][relative][k]
                require(list(v.shape)==desc['shape'] and str(v.dtype)==desc['dtype'],'Sealed array shape/dtype')
                require(hashlib.sha256(np.ascontiguousarray(v).tobytes()).hexdigest()==desc['sha256'],'Sealed array bytes')
            return values
        inputs=load('processed_inputs.npz',['frame0_img','frame1_img']);r['saved_rgb_tensor_decodes']=2
        before=load('scene_before_clean.npz',['depths','confidence']);after=load('scene_after_clean.npz',['depths','confidence'])
        require(np.array_equal(before['depths'],after['depths']),'Depth unchanged by cleaning')
        rgb=[];stats=[]
        for i in FRAMES:
            im=inputs[f'frame{i}_img'];require(im.shape==(1,3,384,512),'Saved RGB tensor dimensions')
            require(np.isfinite(im).all()and(im>=-1).all()and(im<=1).all(),'Normalized real RGB tensor range')
            rgb.append((im[0].transpose(1,2,0)+1)/2)
            z=after['depths'][i];cb=before['confidence'][i];ca=after['confidence'][i]
            require(z.shape==cb.shape==ca.shape==(384,512),'All pixels and native geometry dimensions')
            require(np.isfinite(z).all()and(z>0).all()and np.isfinite(cb).all()and np.isfinite(ca).all(),'Finite full maps')
            require((cb>=0).all()and(ca>=0).all(),'No negative confidence')
            stats.append(dict(index=i,total_pixels=int(z.size),camera_depth_positive=int((z>0).sum()),
                camera_depth_min_model_units=float(z.min()),camera_depth_max_model_units=float(z.max()),
                depth_above_fixed_display_max=int((z>DEPTH_DISPLAY_MAX).sum()),confidence_changed=int((cb!=ca).sum()),
                confidence_before_zero=int((cb==0).sum()),confidence_before_positive=int((cb>0).sum()),
                confidence_after_zero=int((ca==0).sum()),confidence_after_positive=int((ca>0).sum()),
                confidence_before_min=float(cb.min()),confidence_before_max=float(cb.max()),
                confidence_after_min=float(ca.min()),confidence_after_max=float(ca.max())))
        r.update(pixel_statistics=stats,native_trace_count=len(trace),loss_first=trace[0]['loss_before_step'],
            loss_before_last_step=trace[-1]['loss_before_step'],postfinal_objective=final_loss,
            interpretation='Component behavior only; objective is not GT accuracy; arbitrary reconstruction units are not metres.')
        plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':9,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none'})
        plot_scene(rgb,after['depths'],before['confidence'],after['confidence'],stats,a.output)
        plot_trace(trace,final_loss,stats,a.output)
        shutil.copy2(__file__,a.output/'plot_source_snapshot.py')
        r.update(status='SUCCESS_PLOTS_AWAIT_VISUAL_QA',completed_utc=utc(),matplotlib_version=matplotlib.__version__)
        r['output_sha256']={f.name:sha(f)for f in a.output.iterdir()if f.is_file()}
    except BaseException as error:
        r.update(status='FAILED',completed_utc=utc(),error=repr(error));write(a.output/'plot_receipt.json',r);raise
    write(a.output/'plot_receipt.json',r)


if __name__=='__main__':main()
