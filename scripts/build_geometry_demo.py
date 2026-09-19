#!/usr/bin/env python3
"""An annotated replay of all S5 observations, never a generated novel-view video."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from learned_pair_metrics import resize_crop


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--preview-dir',type=Path,required=True)
    p.add_argument('--font',type=Path,default=Path('/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
    p.add_argument('--data',type=Path,default=ROOT/'data/tum/rgbd_dataset_freiburg1_xyz')
    args=p.parse_args()
    if args.output.exists():raise ValueError('Preserve previous output')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.preview_dir.mkdir(parents=True,exist_ok=True)
    result=ROOT/'results/S5_cut3r_sequence'
    summary=json.loads((result/'summary.json').read_text());assert summary['status']=='completed'
    rows=json.loads((result/'records.json').read_text());frozen=json.loads((ROOT/'data/cut3r/S5_inputs.json').read_text())
    a=np.load(result/'measurement_comparison.npz',allow_pickle=False)
    zmax=max(max(float(a[f'block{b}_depth_scaled'].max()),float(a[f'block{b}_target'][a[f'block{b}_valid']].max())) for b in range(3))
    cmap=plt.get_cmap('viridis').copy();cmap.set_bad('#dddddd')
    fonts={s:ImageFont.truetype(str(args.font),s) for s in (16,20,24,32)}
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','2','-i','-',
         '-an','-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(args.output)]
    process=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for b in range(3):
            for i in range(24):
                f=frozen['blocks'][b]['frames'][i];r=rows[b*24+i]
                canvas=Image.new('RGB',(1280,720),'#F7FAFC');d=ImageDraw.Draw(canvas)
                d.text((40,27),'模型怎样理解这个房间',font=fonts[32],fill='#153648')
                d.text((915,37),f'第 {b+1}/3 段  ·  第 {i+1}/24 张',font=fonts[24],fill='#153648')
                role='校准距离比例' if i==0 else ('末尾评分画面' if i>=20 else '连续观察')
                d.text((40,82),f'真实观测的对照回放  |  {role}  |  每段只在第一张校准一次',font=fonts[20],fill='#536978')
                rgb,_=resize_crop(Image.open(args.data/f['rgb']['path']).convert('RGB'),Image.Resampling.LANCZOS)
                measured=np.where(a[f'block{b}_valid'][i],a[f'block{b}_target'][i],np.nan)
                depth=a[f'block{b}_depth_scaled'][i]
                tiles=[rgb,Image.fromarray((cmap(np.ma.masked_invalid(measured/zmax))[:,:,:3]*255).astype('uint8')),
                       Image.fromarray((cmap(depth/zmax)[:,:,:3]*255).astype('uint8'))]
                for x,t,label in zip((40,450,860),tiles,('原始照片','相机测量的距离','模型估计的距离')):
                    d.text((x,127),label,font=fonts[24],fill='#153648');canvas.paste(t.resize((380,380),Image.Resampling.NEAREST),(x,165))
                d.text((40,567),'灰色：预定测量掩码之外',font=fonts[20],fill='#536978')
                grad=np.tile(np.linspace(0,1,570),(18,1));bar=Image.fromarray((cmap(grad)[:,:,:3]*255).astype('uint8'))
                canvas.paste(bar,(585,566));d.text((450,563),'距离颜色',font=fonts[20],fill='#536978')
                d.text((585,591),'0 米',font=fonts[16],fill='#536978');d.text((1125,591),f'{zmax:.1f} 米',font=fonts[16],fill='#536978')
                d.text((40,629),f"这一张的平均深度差：{r['calibrated']['mae_mm']/10:.1f} 厘米  |  比较像素：{r['calibrated']['n']:,}",font=fonts[24],fill='#153648')
                d.text((40,683),'TUM RGB-D · CC BY 4.0  |  72张取样以每秒2张回放；不是原始帧率，也不是新视角生成视频',font=fonts[16],fill='#536978')
                if (b,i) in ((0,0),(1,20),(2,23)):canvas.save(args.preview_dir/f'block{b}_frame{i}.png')
                process.stdin.write(canvas.tobytes())
    finally:
        process.stdin.close()
    if process.wait()!=0:raise RuntimeError('Video encoding failed')
    metadata=dict(created_utc=datetime.now(timezone.utc).isoformat(),evidence_level='annotated_replay_of_72_real_observations',
        frames=72,playback_fps=2,duration_seconds=36,new_views_generated=False,
        source='TUM RGB-D freiburg1_xyz, CC BY 4.0, https://cvg.cit.tum.de/data/datasets/rgbd-dataset',
        summary_sha256=hashlib.sha256((result/'summary.json').read_bytes()).hexdigest(),
        sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),bytes=args.output.stat().st_size)
    args.output.with_suffix('.json').write_text(json.dumps(metadata,indent=2));print(json.dumps(metadata))


if __name__=='__main__':main()
