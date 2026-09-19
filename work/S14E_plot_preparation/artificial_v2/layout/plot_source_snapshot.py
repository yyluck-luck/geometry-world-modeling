#!/usr/bin/env python3
"""Post-score S14E report: all four targets, RGB reference + GT + three depths.

Target RGB is opened only after an externally bound successful score and all
score payload hashes are verified. This is reporting, not a model/score rerun.
"""
from __future__ import annotations
import argparse
import csv
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import traceback
import numpy as np

METHODS=['ray','history_zbuffer','history_constant']
QUERIES=[20,21,22,23]


def utc():return datetime.now(timezone.utc).isoformat()
def require(ok,message):
    if not ok:raise ValueError(message)
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def canonical(path):
    p=Path(path);require(p.is_absolute() and str(p.resolve())==str(p),'Canonical absolute path required: '+str(p));return p

def validate_metrics(metrics):
    require(metrics['schema']=='s14e-depth-metrics-v1','Metrics schema')
    require(metrics['method_order']==METHODS and metrics['query_order']==QUERIES,'All ordered methods/queries')
    rows=metrics['rows'];require(len(rows)==12,'All twelve metric rows required')
    require([(r['query_index'],r['method']) for r in rows]==[(q,m) for q in QUERIES for m in METHODS],
            'Do not filter/reorder metric rows')
    require(all(set(r)==set(rows[0]) for r in rows),'Metrics row schema mismatch')
    return rows


def full_depth_range(gt,pred):
    require(gt.shape==(4,224,224) and pred.shape==(4,3,224,224),'All four GT and twelve prediction maps')
    require(gt.dtype==pred.dtype==np.float64,'Scorer depth dtype')
    values=np.r_[gt.reshape(-1),pred.reshape(-1)]
    valid=np.isfinite(values)&(values>0)
    require(valid.any(),'No finite positive depth values to display')
    lo=float(values[valid].min());hi=float(values[valid].max())
    # Colorbar needs nonzero width when all valid depths are exactly constant.
    # This only expands display bounds and never clips/removes observations.
    limits=[lo,hi]
    if lo==hi:limits=[0.,2*hi] if hi<=np.finfo(np.float64).max/2 else [hi/2,hi]
    stats=[]
    for q in range(4):
        for name,arr in [('gt',gt[q])]+[(m,pred[q,i]) for i,m in enumerate(METHODS)]:
            finite=np.isfinite(arr);positive=finite&(arr>0)
            stats.append(dict(query_index=QUERIES[q],map=name,all_pixels=arr.size,
                              positive_finite_pixels=int(positive.sum()),nan_pixels=int(np.isnan(arr).sum()),
                              infinite_pixels=int(np.isinf(arr).sum()),nonpositive_finite_pixels=int((finite&~positive).sum()),
                              minimum_positive=None if not positive.any() else float(arr[positive].min()),
                              maximum_positive=None if not positive.any() else float(arr[positive].max())))
    return dict(data_range_m=[lo,hi],display_range_m=limits,singular_range_expanded=lo==hi,
                valid_depth_values=int(valid.sum()),all_depth_values=len(values),per_map=stats)


def draw_panel(rgb,gt,pred,rows,range_info,out,scope):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    require(len(rgb)==4 and all(x.shape==(224,224,3) and x.dtype==np.uint8 for x in rgb),'Four cropped RGB arrays')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,
                         'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,'svg.fonttype':'none'})
    fig,axes=plt.subplots(4,5,figsize=(13.2,11.7),layout='constrained')
    cmap=plt.get_cmap('viridis').copy();cmap.set_bad('#a5a5a5')
    norm=Normalize(*range_info['display_range_m'],clip=False)
    headings=['Real RGB: post-score reference','Sensor GT depth','CUT3R ray-only depth',
              'History z-buffer depth','History constant depth']
    for q in range(4):
        for col,ax in enumerate(axes[q]):
            if col==0:ax.imshow(rgb[q],origin='upper',interpolation='nearest')
            else:
                depth=gt[q] if col==1 else pred[q,col-2]
                shown=np.ma.masked_where(~np.isfinite(depth)|(depth<=0),depth)
                im=ax.imshow(shown,cmap=cmap,norm=norm,origin='upper',interpolation='nearest')
            if q==0:ax.set_title(headings[col],pad=10)
            ax.set_xticks([0,112,223]);ax.set_yticks([0,112,223])
            if q!=3:ax.set_xticklabels([])
            if col!=0:ax.set_yticklabels([])
            else:ax.set_ylabel(f'Query {QUERIES[q]}\npixel v')
            ax.tick_params(length=2)
            if col>=2:
                row=rows[q*3+col-2]
                d='undefined' if row['delta1_all_gt'] is None else f"{100*row['delta1_all_gt']:.1f}%"
                c='undefined' if row['coverage'] is None else f"{100*row['coverage']:.1f}%"
                ax.set_xlabel(f'Delta1: {d}  |  coverage: {c}',fontsize=8)
            elif col==0:ax.set_xlabel('Not provided to the model',fontsize=8)
            else:ax.set_xlabel('Measured after prediction seal',fontsize=8)
    colorbar=fig.colorbar(im,ax=axes[:,1:],shrink=.78,pad=.015)
    colorbar.set_label('Optical-axis depth (m): one full range for all 16 maps',fontsize=9)
    title='S14E: four known-camera targets, all methods and all queries retained'
    if scope=='artificial_layout_only':title='ARTIFICIAL LAYOUT CHECK: no real photos or research scores\n'+title
    fig.suptitle(title,fontsize=12)
    footer=('Gray = missing / nonfinite / nonpositive depth. No depth clipping, smoothing or per-panel color scaling.\n'
            'RGB is a post-score reference at its paired RGB time; GT/model target camera uses depth time.\n'
            'Delta1: ratio error < 1.25 over all valid GT pixels; missing predictions fail. Displayed pixel u: 0-223.')
    fig.supxlabel(footer,fontsize=9)
    for ext in ['png','svg']:fig.savefig(out/f's14e_all_four_targets.{ext}',dpi=180)
    plt.close(fig)
    return dict(matplotlib_version=matplotlib.__version__,canvas_inches=[13.2,11.7],
                native_font_points=[8,9,10,12],colormap='viridis',invalid_color='#a5a5a5',
                svg_contains_vector_labels_and_raster_sensor_photo_arrays=True,
                visual_verification_after_execution_required=True,publication_scaled_font_size_verified=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--score-dir',type=Path,required=True)
    parser.add_argument('--score-manifest',type=Path,required=True)
    parser.add_argument('--score-metadata-sha256',required=True)
    parser.add_argument('--rgb-manifest',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();require(not args.output.exists(),'Fresh reporting directory required');args.output.mkdir(parents=True)
    report=dict(schema='s14e-depth-figure-run-v1',status='RUNNING',started_utc=utc(),reads=[],hashes=[],
                model_calls=0,metrics_recomputed=False,depth_png_decoded=0,
                counters=dict(json_attempts=0,json_decoded=0,npz_open_attempts=0,npz_opened=0,
                              npz_array_attempts=0,npz_arrays_decoded=0,rgb_open_attempts=0,rgb_opened=0,
                              rgb_decode_attempts=0,rgb_decoded=0,hash_attempts=0,hash_successes=0))
    def phase(name):
        report.update(phase=name,updated_utc=utc());write(args.output/'figure_receipt.json',report)
        print(json.dumps(dict(utc=utc(),phase=name)),flush=True)
    def read_json(path,role):
        row=dict(path=str(path),role=role,attempted_utc=utc(),completed=False);report['reads'].append(row)
        report['counters']['json_attempts']+=1;value=json.loads(Path(path).read_text())
        report['counters']['json_decoded']+=1;row.update(completed=True,completed_utc=utc());return value
    def hash_check(path,expected,role):
        row=dict(path=str(path),role=role,attempted_utc=utc(),completed=False);report['hashes'].append(row)
        report['counters']['hash_attempts']+=1;digest=sha(path);row.update(completed=True,sha256=digest,completed_utc=utc())
        require(digest==expected,'Hash mismatch: '+str(path));report['counters']['hash_successes']+=1
    try:
        score_dir=canonical(args.score_dir);score_manifest_path=canonical(args.score_manifest)
        rgb_manifest_path=canonical(args.rgb_manifest)
        phase('verify_successful_score_before_any_target_rgb_access')
        meta_path=score_dir/'run_metadata.json';hash_check(meta_path,args.score_metadata_sha256,'externally bound score metadata')
        meta=read_json(meta_path,'score status gate')
        require(meta['schema']=='s14e-depth-score-run-v1' and meta['status']=='SUCCESS','Successful score required')
        require(meta['result_rows']==12 and meta['counters']['depths_decoded']==4 and meta['counters']['target_rgb_decoded']==0,
                'Score domain / target RGB boundary')
        require(meta['before_after_identity_pass'] is True,'Score identity gate did not pass')
        require(datetime.fromisoformat(meta['completed_utc'])<datetime.fromisoformat(report['started_utc']),'Score must complete before reporting')
        for name,digest in meta['output_sha256'].items():
            path=(score_dir/name).resolve();require(path.is_relative_to(score_dir),'Score payload path traversal')
            hash_check(path,digest,'sealed successful scoring payload')
        require({'arrays.npz','metrics.json','frozen_manifest.json'}<=set(meta['output_sha256']),'Missing required scoring payload')
        hash_check(score_manifest_path,meta['manifest_sha256'],'original scoring manifest')
        require(meta['output_sha256']['frozen_manifest.json']==meta['manifest_sha256'],'Copied scoring manifest identity')
        sm=read_json(score_manifest_path,'score query contract')
        require(sm['schema']=='s14e-score-manifest-v1' and [t['query_index'] for t in sm['targets']]==QUERIES,'Score manifest queries')
        report['score_payload_verified_utc']=utc();report['score_completed_utc']=meta['completed_utc']
        report['score_metadata_sha256']=args.score_metadata_sha256
        phase('bind_post_score_reference_photo_manifest')
        rgb_manifest_sha=sha(rgb_manifest_path);rm=read_json(rgb_manifest_path,'post-score reference RGB contract')
        require(rm['schema']=='s14e-report-rgb-manifest-v1','RGB report manifest schema')
        scope=rm.get('scope','real_research_report');require(scope in ['real_research_report','artificial_layout_only'],'Figure scope')
        require([x['query_index'] for x in rm['targets']]==QUERIES,'Four ordered RGB targets')
        frozen_path=canonical(rm['frozen_inputs']);hash_check(frozen_path,rm['frozen_inputs_sha256'],'original RGB/depth pairing ledger')
        frozen=read_json(frozen_path,'block0 original frame mapping')
        require(frozen['schema']=='s8-inputs-v1' and frozen['blocks'][0]['block']==0,'Original block0 inputs')
        frames=frozen['blocks'][0]['frames'];require(len(frames)==24,'Original block0 24 frame records')
        dataset=canonical(rm['dataset_root']);rgb_paths=[]
        for i,(q,target) in enumerate(zip(QUERIES,rm['targets'])):
            frame=frames[q];require(frame['frame']==q,'Frame index')
            path=canonical(target['rgb_path']);depth=canonical(sm['targets'][i]['depth_path'])
            require(path==dataset/frame['rgb']['path'] and target['rgb_sha256']==frame['rgb_sha256'],'Original RGB mapping/SHA')
            require(depth==dataset/frame['depth']['path'] and sm['targets'][i]['depth_sha256']==frame['depth_sha256'],'Same scored depth target')
            rgb_paths.append(path)
        require(len(set(rgb_paths))==4,'Distinct four RGB files')
        metrics=read_json(score_dir/'metrics.json','all twelve completed score rows');rows=validate_metrics(metrics)
        require(metrics['source_seal_sha256']==meta['prediction_seal_sha256'],'Metrics use completed score prediction seal')
        phase('read_two_scored_depth_arrays')
        row=dict(path=str(score_dir/'arrays.npz'),role='four GT and twelve scored prediction maps',arrays=[])
        report['reads'].append(row);report['counters']['npz_open_attempts']+=1
        with np.load(score_dir/'arrays.npz',allow_pickle=False) as values:
            report['counters']['npz_opened']+=1;arrays={}
            for key in ['gt_depth_m','prediction_depth_m']:
                entry=dict(key=key,completed=False,attempted_utc=utc());row['arrays'].append(entry)
                report['counters']['npz_array_attempts']+=1;arrays[key]=values[key].copy()
                report['counters']['npz_arrays_decoded']+=1;entry.update(completed=True,completed_utc=utc())
        gt=arrays['gt_depth_m'];pred=arrays['prediction_depth_m'];range_info=full_depth_range(gt,pred)
        report.update(depth_range=range_info,scope=scope,queries_shown=QUERIES,methods_shown=METHODS,
                      gt_panels=4,prediction_panels=12,rgb_panels=4)
        phase('open_reference_rgb_only_after_verified_score')
        from PIL import Image
        rgb=[]
        for i,target in enumerate(rm['targets']):
            path=rgb_paths[i];hash_check(path,target['rgb_sha256'],'post-score reference RGB')
            read=dict(path=str(path),role='reference photo, absent from model/score inputs',query_index=QUERIES[i],
                      attempted_utc=utc(),opened=False,decoded=False);report['reads'].append(read)
            report['counters']['rgb_open_attempts']+=1
            require(datetime.fromisoformat(read['attempted_utc'])>datetime.fromisoformat(report['score_payload_verified_utc']),
                    'RGB access before score verification')
            phase('reference_photo_'+str(QUERIES[i])+'_started')
            with Image.open(path) as im:
                report['counters']['rgb_opened']+=1;read.update(opened=True,opened_utc=utc(),format=im.format,mode=im.mode,size=list(im.size))
                require(im.format=='PNG' and im.size==(640,480),'Original RGB PNG geometry')
                report['counters']['rgb_decode_attempts']+=1;im.load();report['counters']['rgb_decoded']+=1
                read.update(decoded=True,decoded_utc=utc())
                # Standard fixed photo resize/crop for comparable pixel coordinates;
                # depth maps are already scored and are never resampled here.
                image=im.convert('RGB').resize((299,224),Image.Resampling.LANCZOS).crop((37,0,261,224))
                rgb.append(np.asarray(image,dtype=np.uint8).copy())
            phase('reference_photo_'+str(QUERIES[i])+'_complete')
        phase('draw_all_twenty_panels')
        report['figure_design']=draw_panel(rgb,gt,pred,rows,range_info,args.output,scope)
        with (args.output/'all_12_scores.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        shutil.copy2(__file__,args.output/'plot_source_snapshot.py')
        shutil.copy2(rgb_manifest_path,args.output/'rgb_reference_manifest.json')
        # Caption derives only setup and exact unfiltered displayed range; no novelty
        # or winner claim is invented before the result is read and reviewed.
        caption=('全部4个预定目标、3种方法及其传感器深度均完整展示。第一列是真实目标RGB的事后参照；这些照片没有提供给模型或评分，且与深度采集时刻有原配对时间差。'
                 '第二列为传感器测量的光轴深度，其余依次是CUT3R ray-only、20历史预测深度重投影、历史常数深度；全部16张深度图共用完整有限正深度色域。'
                 '灰色表示无值、非有限或非正深度；图中不作深度裁剪、平滑、补洞或逐图色域。RGB仅按既定299×224后裁[37,0,261,224]对齐显示，未重新评分。')
        if scope=='artificial_layout_only':caption='本文件仅是人工布局测试，没有真实照片或科研分数。\n\n'+caption
        (args.output/'图注.md').write_text(caption+'\n\n数据完整正深度范围（米）：'+repr(range_info['data_range_m'])+'。\n')
        phase('post_report_identity')
        for name,digest in meta['output_sha256'].items():hash_check(score_dir/name,digest,'post-report scoring payload')
        hash_check(meta_path,args.score_metadata_sha256,'post-report score metadata')
        hash_check(score_manifest_path,meta['manifest_sha256'],'post-report score manifest')
        hash_check(rgb_manifest_path,rgb_manifest_sha,'post-report RGB contract')
        hash_check(frozen_path,rm['frozen_inputs_sha256'],'post-report original frame ledger')
        for target in rm['targets']:hash_check(target['rgb_path'],target['rgb_sha256'],'post-report RGB')
        require(report['counters']['rgb_decoded']==4 and report['counters']['npz_arrays_decoded']==2,'Exact reporting read budget')
        report.update(status='SUCCESS',phase='complete',completed_utc=utc(),before_after_identity_pass=True,
                      rgb_appearance_transform='LANCZOS 640x480 to299x224 then crop[37,0,261,224], no depth resizing',
                      depth_interpolation='nearest display only',depth_clipping=False,depth_smoothing=False,
                      depth_per_panel_scaling=False,all_12_metric_rows_preserved=True,
                      output_sha256={p.name:sha(p) for p in sorted(args.output.iterdir()) if p.is_file() and p.name!='figure_receipt.json'})
        write(args.output/'figure_receipt.json',report)
        print(json.dumps(dict(status='SUCCESS',rgb_decoded=4,depth_panels=16,metric_rows=12)),flush=True)
    except BaseException as e:
        report.update(status='FAILED',completed_utc=utc(),error=repr(e),traceback=traceback.format_exc())
        write(args.output/'figure_receipt.json',report);print(report['traceback'],file=sys.stderr);return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
