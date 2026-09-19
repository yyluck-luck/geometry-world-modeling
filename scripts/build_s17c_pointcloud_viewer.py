#!/usr/bin/env python3
"""Offline supplementary viewer from sealed, independently verified S17C outputs.

No model, original-image, GT or extra NPZ reads. Fixed grid stride=4, origin=(0,0),
both 384x512 images retained; the confidence control affects display only.
The native Canvas view is interactive supplementary material, not a paper figure.
"""
from __future__ import annotations
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import traceback
import zipfile

SCHEMA = 's17c-offline-pointcloud-viewer-v1'
SOURCE_COMMIT = '39291e4f272f6b4f270691d930926ab5930f942e'
STRIDE, HEIGHT, WIDTH, FRAMES = 4, 384, 512, 2
SHAPES = {'point_clouds': (2,384,512,3), 'colors': (2,384,512,3),
          'depths': (2,384,512), 'confidences': (2,384,512), 'focal': (2,1),
          'pp': (2,2), 'R': (2,3,3), 't': (2,3)}
SELECTED_ARRAYS = ('point_clouds', 'colors', 'confidences', 'R', 't')

def utc():
    return datetime.now(timezone.utc).isoformat()

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def aid(array):
    import numpy as np
    a = np.ascontiguousarray(array)
    return {'shape': list(a.shape), 'dtype': str(a.dtype),
            'sha256': hashlib.sha256(a.tobytes()).hexdigest()}

def json_for_html(value):
    # Names/metadata are data, never executable script or HTML.
    return (json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
            .replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
            .replace('\u2028', '\\u2028').replace('\u2029', '\\u2029'))

def float_payload(array):
    import numpy as np
    # Little-endian FP32 bytes, with no coordinate rescaling/rounding/clipping.
    return base64.b64encode(np.ascontiguousarray(array, dtype='<f4').tobytes()).decode('ascii')

def bind_inputs(args, report):
    """Read only the four control JSONs and hash the one allowed archive."""
    paths = {key: Path(getattr(args, key)).resolve() for key in ('manifest', 'seal', 'verification')}
    run = Path(args.run_dir).resolve()
    paths.update(metadata=run/'run_metadata.json', result=run/'final_result.npz')
    for key in ('manifest', 'seal', 'verification'):
        expected = getattr(args, key + '_sha256')
        require(len(expected) == 64 and all(c in '0123456789abcdef' for c in expected), 'Explicit SHA required: ' + key)
        actual = sha(paths[key])
        require(actual == expected, 'Binding changed: ' + key)
        report['input_hashes'][key] = {'path': str(paths[key]), 'sha256': actual}
    manifest, seal, verification = [json.loads(paths[k].read_text()) for k in ('manifest', 'seal', 'verification')]
    require(manifest['schema'] == 's17c-embedded-two-frame-geometry-manifest-v1'
            and manifest['source_commit'] == SOURCE_COMMIT, 'Expected S17C source/schema')
    require(verification['schema'] == 's17c-embedded-independent-verification-v1'
            and verification['status'] == 'PASS' and verification.get('inputs_unchanged') is True,
            'Independent PASS with unchanged inputs required before archive access')
    require(verification['checks'] and all(x['passed'] is True for x in verification['checks']),
            'Independent verifier contains a failed/missing check')
    verifier_sources = [h for p,h in manifest['identities'].items() if Path(p).name == 'verify_s17c_embedded_geometry.py']
    require(verifier_sources == [verification['source_sha256']], 'Independent verifier source bound by manifest')
    observed = {(item['path'], item['sha256']) for item in verification['file_hashes']}
    for key in ('manifest', 'seal'):
        require((str(paths[key]), report['input_hashes'][key]['sha256']) in observed,
                'Independent verifier used these exact bindings: ' + key)
    ids = seal['identities']
    require(ids.get(str(paths['manifest'])) == args.manifest_sha256, 'Seal binds manifest')
    for key in ('metadata', 'result'):
        actual = sha(paths[key])
        require(ids.get(str(paths[key])) == actual, 'Selected file must match output seal: ' + key)
        require((str(paths[key]), actual) in observed, 'Selected file was independently verified: ' + key)
        report['input_hashes'][key] = {'path': str(paths[key]), 'sha256': actual}
    metadata = json.loads(paths['metadata'].read_text())
    require(metadata['schema'] == 's17c-embedded-two-frame-geometry-run-v1'
            and metadata['status'] == 'SUCCESS' and metadata['manifest_sha256'] == args.manifest_sha256,
            'Successful producer and same manifest required')
    for key in ('video_generated', 'new_model_trained', 'accuracy_evaluated',
                'supplied_pose_prior', 'supplied_depth_prior', 'surfel_objects_created'):
        require(metadata[key] is False, 'S17C component interpretation changed: ' + key)
    require(manifest['contract']['niter'] == 400 and manifest['contract']['poses'] is None
            and manifest['contract']['depths'] is None, 'Expected no-prior 400-step component')
    require([x['index'] for x in manifest['history_images']] == [0,1], 'Both frozen source images in original order')
    require(metadata['output_files']['final_result.npz']['sha256'] == report['input_hashes']['result']['sha256'],
            'Producer file identity matches seal')
    report['gates_passed_before_array_read'] = True
    return paths, manifest, metadata, verification

def load_selected_result(path, metadata, report):
    import numpy as np
    recorded = metadata['array_files']['final_result.npz']
    require(set(recorded) == set(SHAPES), 'Complete original final-result schema')
    with zipfile.ZipFile(path) as archive:
        names = [m.filename for m in archive.infolist()]
        require(len(names) == len(SHAPES) and set(names) == {k+'.npy' for k in SHAPES}, 'Exact NPZ member domain')
        for member in archive.infolist():
            expected_bytes = int(np.prod(SHAPES[member.filename[:-4]])) * 4
            require(expected_bytes <= member.file_size <= expected_bytes + 4096, 'Bounded numeric NPZ member')
    result = {}
    with np.load(path, allow_pickle=False) as archive:
        for name in SELECTED_ARRAYS:
            a = archive[name]
            report['array_decodes'] += 1
            require(a.shape == SHAPES[name] and a.dtype == np.dtype('float32'), 'Array shape/dtype: ' + name)
            require(np.isfinite(a).all(), 'Finite values required; do not silently delete points: ' + name)
            require(aid(a) == recorded[name], 'Saved array identity: ' + name)
            result[name] = a
    require(((result['colors'] >= 0) & (result['colors'] <= 1)).all(), 'Input RGB colors in 0..1')
    require((result['confidences'] >= 0).all(), 'Nonnegative cleaned confidence; zeros retained')
    return result

def build_payload(result, manifest, metadata, verification, report):
    import numpy as np
    points = result['point_clouds'][:, ::STRIDE, ::STRIDE, :].copy()
    colors = result['colors'][:, ::STRIDE, ::STRIDE, :].copy()
    confidence = result['confidences'][:, ::STRIDE, ::STRIDE].copy()
    per_frame = (HEIGHT//STRIDE) * (WIDTH//STRIDE)
    require(points.shape == (2,96,128,3), 'Frozen stride-four sample grid')
    full_points = result['point_clouds'].reshape(-1,3)
    lo, hi = full_points.min(0).astype(float), full_points.max(0).astype(float)
    # A single fit includes every archived point and both estimated camera centers.
    fit_lo = np.minimum(lo, result['t'].min(0).astype(float))
    fit_hi = np.maximum(hi, result['t'].max(0).astype(float))
    center = (fit_lo + fit_hi) / 2
    radius = float(np.linalg.norm((fit_hi-fit_lo)/2))
    require(np.isfinite(radius) and radius > 0, 'Nonzero finite scene extent required')
    summary = {'title': '两张照片推断出的三维点云', 'schema': SCHEMA,
        'interpretation': '模型推断；任意尺度；不是传感器真值、完整Surfel记忆或视频生成。',
        'created_utc': utc(), 'producer_started_utc': metadata['started_utc'],
        'producer_finished_utc': metadata['finished_utc'], 'independent_completed_utc': verification['completed_utc'],
        'source_commit': manifest['source_commit'], 'images': [dict(index=x['index'], name=Path(x['path']).name,
            sha256=x['sha256']) for x in manifest['history_images']],
        'stride': STRIDE, 'sampling_origin_uv': [0,0], 'processed_size_hw': [HEIGHT,WIDTH],
        'sampled_size_hw': [HEIGHT//STRIDE,WIDTH//STRIDE], 'points_per_image': per_frame,
        'display_sample_points': FRAMES*per_frame, 'archived_dense_points': FRAMES*HEIGHT*WIDTH,
        'sampling_rule': '两图都从(行0,列0)起，每4行、每4列取一个；没有按区域、置信度或几何挑选。',
        'confidence_min': float(confidence.min()), 'confidence_max': float(confidence.max()),
        'sample_zero_confidence_count': int((confidence==0).sum()),
        'world_bbox_min': lo.tolist(), 'world_bbox_max': hi.tolist(),
        'display_center': center.tolist(), 'display_fit_radius': radius,
        'display_fit_includes': '全部档案点和两个估计相机中心；不按置信度或区域计算范围。',
        'display_transform': '只进行整体视图旋转、平移、统一缩放；坐标存储保持原FP32字节，不修正几何或裁掉离群点。',
        'coordinate_units': 'model units / 任意尺度，非米', 'projection': 'orthographic / 正交投影',
        'rgb_source': 'wrapper实际输入照片的缩放裁切后颜色；不是模型rgb预测头。',
        'camera_source': 'MST/PnP及全局对齐后的估计c2w，非传感器位姿或raw camera_pose head。',
        'niter': metadata['counters']['optimization_iterations'],
        'bindings': report['input_hashes'], 'generator_sha256': sha(__file__),
        'sample_array_identities': {k: aid(v) for k,v in [('points',points),('colors',colors),('confidence',confidence)]}}
    report['sampling'] = {k:summary[k] for k in ('stride','sampling_origin_uv','points_per_image',
                           'display_sample_points','archived_dense_points','sample_zero_confidence_count')}
    report['sample_array_identities'] = summary['sample_array_identities']
    return {'meta': summary, 'data': {'points': float_payload(points), 'colors': float_payload(colors),
        'confidence': float_payload(confidence), 'camera_R': float_payload(result['R']),
        'camera_t': float_payload(result['t'])}}

HTML = r'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; base-uri 'none'">
<title>S17C · 两图三维点云</title><style>
:root{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#18242d;background:#edf1f3;font-size:15px}
*{box-sizing:border-box}body{margin:0}header,main,footer{max-width:1500px;margin:auto;padding:22px 26px}header{padding-bottom:14px}
h1{font-size:28px;line-height:1.25;margin:0 0 8px}p{line-height:1.65;margin:7px 0}.muted{color:#50636e}.boundary{font-weight:600;color:#713d09}
.stats{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0 0}.stat{background:#fff;border:1px solid #cad5dc;padding:9px 13px;border-radius:5px}
.stat strong{font-size:20px;display:block}.stat span{font-size:12px;color:#50636e}main{padding-top:0;display:grid;grid-template-columns:minmax(0,1fr) 290px;gap:18px}
.view{background:#fff;border:1px solid #c4d0d8;border-radius:7px;overflow:hidden;min-width:0}.canvaswrap{height:64vh;min-height:380px;position:relative;background:#f8fafb}
#cloud{width:100%;height:100%;display:block;touch-action:none;outline-offset:-3px}.viewnote{padding:12px 16px;border-top:1px solid #dbe3e8;font-size:13px;line-height:1.6}
aside{background:#fff;border:1px solid #c4d0d8;border-radius:7px;padding:17px}label{display:block;font-weight:600;line-height:1.4;margin:0 0 8px}
input[type=range]{width:100%;accent-color:#006a93}input[type=checkbox]{accent-color:#006a93}select,button{font:inherit;background:#fff;color:inherit;border:1px solid #839ca9;padding:8px;border-radius:4px}
select{width:100%}button{cursor:pointer;touch-action:manipulation}button:hover{background:#edf4f8}button:focus-visible,select:focus-visible{outline:2px solid #006a93}.control{margin-bottom:22px}
.readout{font-size:13px;color:#475d68;line-height:1.5;font-variant-numeric:tabular-nums}.buttonrow{display:flex;gap:8px;flex-wrap:wrap}.legend{font-size:13px;line-height:1.8}.source0{color:#0072b2}.source1{color:#b24b00}
.previews{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:14px 16px;border-top:1px solid #dbe3e8}.preview canvas{width:100%;max-width:240px;image-rendering:pixelated;border:1px solid #cad5dc;display:block}.preview{font-size:12px;line-height:1.6}
footer{padding-top:0;font-size:13px}details{background:white;border:1px solid #cad5dc;border-radius:5px;padding:13px 16px;margin:10px 0}summary{font-weight:600;cursor:pointer}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:11px;line-height:1.5}
.error{padding:18px;background:#fff0ed;color:#8d220f}.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}
@media(max-width:880px){main{grid-template-columns:1fr}aside{display:grid;grid-template-columns:1fr 1fr;gap:15px}.control{margin:0}.canvaswrap{height:58vh;min-height:340px}header,main,footer{padding-left:14px;padding-right:14px}h1{font-size:23px}}
@media(max-width:470px){aside{grid-template-columns:1fr}.canvaswrap{min-height:300px}}
</style></head><body>
<header><h1>两张照片推断出的三维点云</h1><p class="muted">VMem 内嵌 CUT3R · 两图无先验建图与全局对齐 · 离线交互辅助材料</p>
<p class="boundary">模型推断 · 任意尺度 · 不是传感器真值、完整 Surfel 记忆或视频生成</p>
<div class="stats"><div class="stat"><strong>2 张</strong><span>已见输入照片，全部保留</span></div><div class="stat"><strong id="samplecount"></strong><span>固定网格展示点</span></div><div class="stat"><strong id="densecount"></strong><span>完整档案中的稠密点</span></div><div class="stat"><strong>独立核验 PASS</strong><span>核验数值与身份，不代表几何准确率</span></div></div></header>
<main><section class="view"><div class="canvaswrap"><canvas id="cloud" tabindex="0" role="img" aria-label="模型推断的两图三维点云，可拖动旋转和滚轮缩放"></canvas><span class="sr" id="accessibleStatus" aria-live="polite"></span></div>
<div class="viewnote"><strong>拖动旋转 · 滚轮/双指缩放 · Shift＋拖动平移</strong><br>键盘：方向键旋转，＋/－缩放，Home 恢复。采用正交投影与统一坐标比例；没有去掉离群点或拉直表面。几何误差、重影和不完整区域会原样呈现。</div>
<div class="previews"><div class="preview"><canvas id="rgb0" width="128" height="96" aria-label="图0处理后输入颜色"></canvas><strong>图 0：处理后输入颜色</strong><div id="name0"></div></div><div class="preview"><canvas id="rgb1" width="128" height="96" aria-label="图1处理后输入颜色"></canvas><strong>图 1：处理后输入颜色</strong><div id="name1"></div></div></div>
<div class="viewnote">颜色预览与点云同样每 4 像素采样，来自照片经缩放裁切后的真实颜色。它们不是原始分辨率照片，也不是模型 RGB 预测头；预览始终保留全部颜色，不随置信筛选改变。</div></section>
<aside><div class="control"><label for="confidence">仅改变显示：置信度下限</label><input id="confidence" type="range" min="0" max="1000" value="0" step="1"><div class="readout" id="threshold"></div><div class="readout" id="shown"></div><p class="readout">默认显示全部，包括清理后置信度为 0 的点。置信度是模型分数，不是准确率或概率；筛选不会改动档案或指标。</p></div>
<div class="control"><label for="colorMode">点的颜色</label><select id="colorMode"><option value="rgb">输入照片颜色</option><option value="source">来源编号（颜色＋形状）</option></select><div class="legend">来源模式：<span class="source0">● 图 0</span> · <span class="source1">■ 图 1</span></div></div>
<div class="control"><label for="size">显示点大小</label><input id="size" type="range" min="1" max="4" step="0.5" value="2"><div class="readout">只改变屏幕标记大小，不表示物理半径。</div></div>
<div class="control"><label><input id="cameras" type="checkbox" checked> 显示估计相机 C0 / C1</label><div class="readout">相机标记覆盖绘制；短线指向估计光轴。相机位置和点云均不是传感器真值。</div></div>
<div class="control"><div class="buttonrow"><button id="reset">恢复全部与初始视角</button><button id="fit">适配完整范围</button></div></div>
<div class="control readout" id="extent"></div></aside></main>
<footer><p>固定规则：两图都从行 0、列 0 起，每 4 行、每 4 列取一个点；每图 12,288 点。没有挑选好区域，也没有置信度预筛选。点数是采样量，不是独立实验数。所有原始稠密数组仍在封存档案中。</p>
<details><summary>来源、实际运行时间与完整参数</summary><p>这是一份单文件离线查看器，无外部 JavaScript、网络请求或模型推理。来源身份在生成前已绑定 root 提供的 manifest、输出 seal 和独立核验回执 SHA。</p><pre id="provenance"></pre></details>
<p class="muted">Canvas 是交互辅助材料，不是可直接投稿的矢量论文图。此页面不声称新方法优越性、米制精度或完整视频系统成功。</p><noscript><p class="error">此离线查看器需要启用 JavaScript；完整数组仍保存在原档案中。</p></noscript></footer>
<script id="payload" type="application/json">__S17C_PAYLOAD__</script>
<script>
"use strict";
(() => {
 const payload=JSON.parse(document.getElementById('payload').textContent), m=payload.meta;
 const $=id=>document.getElementById(id), format=n=>n.toLocaleString('zh-CN');
 function floats(encoded){const binary=atob(encoded), bytes=new Uint8Array(binary.length);for(let i=0;i<binary.length;i++)bytes[i]=binary.charCodeAt(i);const view=new DataView(bytes.buffer),answer=new Float32Array(binary.length/4);for(let i=0;i<answer.length;i++)answer[i]=view.getFloat32(i*4,true);return answer;}
 const xyz=floats(payload.data.points), rgb=floats(payload.data.colors), conf=floats(payload.data.confidence), camR=floats(payload.data.camera_R), camT=floats(payload.data.camera_t);
 const count=m.display_sample_points, per=m.points_per_image;
 if(xyz.length!==count*3||rgb.length!==count*3||conf.length!==count||camR.length!==18||camT.length!==6)throw Error('嵌入数组长度不符，停止显示。');
 $('samplecount').textContent=format(count);$('densecount').textContent=format(m.archived_dense_points);$('provenance').textContent=JSON.stringify(m,null,2);
 $('extent').textContent='完整坐标范围（模型单位，非米）：'+['X','Y','Z'].map((axis,i)=>axis+' '+m.world_bbox_min[i].toPrecision(5)+' … '+m.world_bbox_max[i].toPrecision(5)).join('；');
 const colors=new Array(count);for(let i=0;i<count;i++)colors[i]='rgb('+Math.round(rgb[i*3]*255)+','+Math.round(rgb[i*3+1]*255)+','+Math.round(rgb[i*3+2]*255)+')';
 for(let f=0;f<2;f++){const ctx=$('rgb'+f).getContext('2d'),im=ctx.createImageData(128,96);for(let i=0;i<per;i++){const p=(f*per+i)*3;im.data[i*4]=Math.round(rgb[p]*255);im.data[i*4+1]=Math.round(rgb[p+1]*255);im.data[i*4+2]=Math.round(rgb[p+2]*255);im.data[i*4+3]=255;}ctx.putImageData(im,0,0);$('name'+f).textContent=m.images[f].name;}
 const canvas=$('cloud'),ctx=canvas.getContext('2d'),pos=new Float64Array(count*3),active=[];
 let yaw=0,pitch=0,zoom=1,panX=0,panY=0,frame=0,W=0,H=0,scale=1,dpr=1;
 const center=m.display_center,fitRadius=m.display_fit_radius;
 function rotate(x,y,z){const cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch),a=cy*x+sy*z,c=-sy*x+cy*z;return[a,cp*y-sp*c,sp*y+cp*c];}
 function projected(p){const r=rotate(p[0]-center[0],p[1]-center[1],p[2]-center[2]);return[W/2+panX+r[0]*scale,H/2+panY-r[1]*scale,r[2]];}
 function schedule(){if(!frame)frame=requestAnimationFrame(draw);}
 function updateFilter(){const amount=Number($('confidence').value)/1000,threshold=m.confidence_min+(m.confidence_max-m.confidence_min)*amount;active.length=0;let by=[0,0];for(let i=0;i<count;i++)if(conf[i]>=threshold){active.push(i);by[i<per?0:1]++;}$('threshold').textContent='下限 '+threshold.toPrecision(6)+(amount===0?' · 全部显示':' · 显示筛选已启用');$('shown').textContent='筛选保留 '+format(active.length)+' / '+format(count)+' 点；图0 '+format(by[0])+'，图1 '+format(by[1])+'。视角遮挡与缩放可能使部分点不在屏幕内。';$('accessibleStatus').textContent=$('shown').textContent;schedule();}
 function line(a,b,color,width=1){ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(a[0],a[1]);ctx.lineTo(b[0],b[1]);ctx.stroke();}
 function axes(){const origin=[46,H-47];ctx.font='12px -apple-system,sans-serif';[[1,0,0,'X','#8a3a22'],[0,1,0,'Y','#327147'],[0,0,1,'Z','#005d91']].forEach(v=>{const r=rotate(v[0],v[1],v[2]),end=[origin[0]+r[0]*29,origin[1]-r[1]*29];line(origin,end,v[4],2);ctx.fillStyle=v[4];ctx.fillText(v[3],end[0]+4,end[1]-4);});ctx.fillStyle='#344e5c';ctx.fillText('统一坐标比例 · 任意尺度',12,H-12);}
 function cameras(){for(let f=0;f<2;f++){const p=[camT[f*3],camT[f*3+1],camT[f*3+2]],a=projected(p),length=fitRadius*.08,b=projected([p[0]+camR[f*9+2]*length,p[1]+camR[f*9+5]*length,p[2]+camR[f*9+8]*length]),color=f===0?'#0072b2':'#b24b00';line(a,b,color,2);ctx.fillStyle=color;ctx.beginPath();ctx.moveTo(a[0],a[1]-6);ctx.lineTo(a[0]+6,a[1]+5);ctx.lineTo(a[0]-6,a[1]+5);ctx.closePath();ctx.fill();ctx.font='bold 13px -apple-system,sans-serif';ctx.fillText('C'+f,a[0]+8,a[1]-7);}}
 function draw(){frame=0;const rect=canvas.getBoundingClientRect();W=rect.width;H=rect.height;dpr=Math.min(2,window.devicePixelRatio||1);if(canvas.width!==Math.round(W*dpr)||canvas.height!==Math.round(H*dpr)){canvas.width=Math.round(W*dpr);canvas.height=Math.round(H*dpr);}ctx.setTransform(dpr,0,0,dpr,0,0);ctx.fillStyle='#f8fafb';ctx.fillRect(0,0,W,H);scale=.82*Math.min(W,H)/(2*fitRadius)*zoom;const cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);for(let n=0;n<active.length;n++){const i=active[n],o=i*3,x=xyz[o]-center[0],y=xyz[o+1]-center[1],z=xyz[o+2]-center[2],a=cy*x+sy*z,c=-sy*x+cy*z;pos[o]=W/2+panX+a*scale;pos[o+1]=H/2+panY-(cp*y-sp*c)*scale;pos[o+2]=sp*y+cp*c;}const order=active.slice().sort((a,b)=>pos[a*3+2]-pos[b*3+2]||a-b),size=Number($('size').value),source=$('colorMode').value==='source';for(const i of order){const x=pos[i*3],y=pos[i*3+1];if(x< -size||x>W+size||y< -size||y>H+size)continue;ctx.fillStyle=source?(i<per?'#0072b2':'#b24b00'):colors[i];if(source&&i<per){ctx.beginPath();ctx.arc(x,y,size*.65,0,Math.PI*2);ctx.fill();}else ctx.fillRect(x-size/2,y-size/2,size,size);}if($('cameras').checked)cameras();axes();}
 function reset(){yaw=0;pitch=0;zoom=1;panX=panY=0;$('confidence').value=0;$('colorMode').value='rgb';$('size').value=2;$('cameras').checked=true;updateFilter();}
 const pointers=new Map();let gesture=null;
 function gestureNow(){const p=[...pointers.values()];return p.length>=2?{distance:Math.max(1,Math.hypot(p[1].x-p[0].x,p[1].y-p[0].y)),x:(p[0].x+p[1].x)/2,y:(p[0].y+p[1].y)/2}:null;}
 canvas.addEventListener('pointerdown',e=>{canvas.focus();canvas.setPointerCapture(e.pointerId);pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});gesture=gestureNow();});
 canvas.addEventListener('pointermove',e=>{if(!pointers.has(e.pointerId))return;const old=pointers.get(e.pointerId);pointers.set(e.pointerId,{x:e.clientX,y:e.clientY});if(pointers.size>=2){const next=gestureNow();if(gesture){zoom=Math.max(.05,Math.min(40,zoom*next.distance/gesture.distance));panX+=next.x-gesture.x;panY+=next.y-gesture.y;}gesture=next;}else if(e.shiftKey){panX+=e.clientX-old.x;panY+=e.clientY-old.y;}else{yaw+=(e.clientX-old.x)*.007;pitch=Math.max(-Math.PI/2,Math.min(Math.PI/2,pitch+(e.clientY-old.y)*.007));}schedule();});
 for(const event of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(event,e=>{pointers.delete(e.pointerId);gesture=gestureNow();});
 canvas.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(.05,Math.min(40,zoom*Math.exp(-e.deltaY*.001)));schedule();},{passive:false});
 canvas.addEventListener('keydown',e=>{let handled=true;if(e.key==='ArrowLeft')yaw-=.07;else if(e.key==='ArrowRight')yaw+=.07;else if(e.key==='ArrowUp')pitch=Math.max(-Math.PI/2,pitch-.07);else if(e.key==='ArrowDown')pitch=Math.min(Math.PI/2,pitch+.07);else if(e.key==='+'||e.key==='=')zoom=Math.min(40,zoom*1.15);else if(e.key==='-')zoom=Math.max(.05,zoom/1.15);else if(e.key==='Home')reset();else handled=false;if(handled){e.preventDefault();schedule();}});
 $('confidence').addEventListener('input',updateFilter);for(const id of ['size','colorMode','cameras'])$(id).addEventListener('input',schedule);$('reset').addEventListener('click',reset);$('fit').addEventListener('click',()=>{zoom=1;panX=panY=0;schedule();});new ResizeObserver(schedule).observe(canvas);updateFilter();
})();
</script></body></html>'''

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','manifest-sha256','seal','seal-sha256','verification','verification-sha256','run-dir','output-dir'):
        parser.add_argument('--'+name, required=True)
    args = parser.parse_args()
    output, run = Path(args.output_dir).resolve(), Path(args.run_dir).resolve()
    require(not output.exists() and not output.is_relative_to(run), 'Fresh output outside sealed run required')
    output.mkdir(parents=True)
    report = {'schema': SCHEMA, 'status': 'RUNNING', 'started_utc': utc(), 'input_hashes': {},
              'array_decodes': 0, 'original_rgb_decodes': 0, 'gt_reads': 0, 'model_calls': 0,
              'browser_qa': 'NOT_PERFORMED_BY_GENERATOR', 'script_sha256': sha(__file__)}
    try:
        paths, manifest, metadata, verification = bind_inputs(args, report)
        result = load_selected_result(paths['result'], metadata, report)
        payload = build_payload(result, manifest, metadata, verification, report)
        html = HTML.replace('__S17C_PAYLOAD__', json_for_html(payload))
        require('__S17C_PAYLOAD__' not in html, 'Payload placeholder removed')
        (output/'viewer.html').write_text(html, encoding='utf-8')
        for value in report['input_hashes'].values():
            require(sha(value['path']) == value['sha256'], 'Input changed during rendering')
        report.update(status='GENERATED_FROM_VERIFIED_ARCHIVE_BROWSER_QA_PENDING',
                      output_html_sha256=sha(output/'viewer.html'), output_html_bytes=(output/'viewer.html').stat().st_size)
    except BaseException as exc:
        report.update(status='FAILED', error=repr(exc), traceback=traceback.format_exc())
    finally:
        report['completed_utc'] = utc()
        (output/'viewer_receipt.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
        print(json.dumps({'status': report['status'], 'array_decodes': report['array_decodes'],
                          'original_rgb_decodes': report['original_rgb_decodes'], 'model_calls': report['model_calls']}, ensure_ascii=False))
    return 1 if report['status']=='FAILED' else 0

if __name__ == '__main__':
    raise SystemExit(main())
