"""Supporting diagnostic figure: fixed even-index samples, not selected good matches."""
from pathlib import Path
from datetime import datetime, timezone
import base64
import hashlib
import html
import json
import math
from PIL import Image, ImageDraw, ImageFont

D=Path(__file__).resolve().parent
S=D.parent/'S70_fixed_context_generation/visuals_01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
now=lambda:datetime.now(timezone.utc).isoformat()
out=D/'visuals_01';out.mkdir(exist_ok=False)
rec={'started_utc':now(),'inputs':{},'panels':[],'new_method_validated':False}
r=json.loads((D/'execution_01/receipt.json').read_text())
c=json.loads((D/'CONTRACT.json').read_text())
assert r['status']=='COMPLETE_SAVED_IMAGE_EXPLORATION'
assert (D/'ROOT_RESULT_ACCEPTANCE.json').is_file()
rec['inputs']['result']=sha(D/'execution_01/receipt.json')
im=Image.new('RGB',(1200,1485),'white');draw=ImageDraw.Draw(im)
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',17)
title=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',23)
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1485"><rect width="100%" height="100%" fill="white"/>']
def text(x,y,value,big=False):
    draw.text((x,y),value,fill='#17202a',font=title if big else font)
    svg.append(f'<text x="{x}" y="{y+(22 if big else 16)}" font-family="Arial,sans-serif" font-size="{23 if big else 17}">{html.escape(value)}</text>')
text(15,10,'S71: matched-feature displacements; sparse matches do not establish a camera pose',True)
text(15,42,'Each panel: real reference (left), generated (right). Circles/solid: fit consensus; crosses/dashed: other.')
text(15,64,'At most 12 evenly spaced match indices shown per panel; all matches remain in the numerical report.')
for p in r['pairs']:
    if p['pair']=='A0_A1_repeat_control':continue
    row=p['target_id']-20;col=0 if p['pair']=='reference_A0' else 1;x0=15+col*595;y0=115+row*337
    arm='A0' if col==0 else 'B';n=p['mutual_match_count']
    text(x0,y0-24,f'Target {p["target_id"]}: {arm}; matches {n}, fit consensus {p.get("inlier_count","N/A")}')
    for j,name in enumerate(['reference',arm]):
        path=S/f'{name}_target_{p["target_id"]}.png';h=sha(path);assert h==c['source_images'][str(path)]
        rec['inputs'][str(path)]=h
        with Image.open(path) as src:im.paste(src.resize((288,288),Image.Resampling.LANCZOS),(x0+j*290,y0))
        svg.append(f'<image x="{x0+j*290}" y="{y0}" width="288" height="288" href="data:image/png;base64,{base64.b64encode(path.read_bytes()).decode()}"/>')
    idx=sorted(set(round(i*(n-1)/(min(n,12)-1)) for i in range(min(n,12)))) if n>1 else list(range(n))
    rec['panels'].append({'target':p['target_id'],'pair':p['pair'],'displayed_indices':idx,'total_matches':n})
    for i in idx:
        ax,ay=p['source_xy'][i];bx,by=p['destination_xy'][i]
        a=(x0+ax/2,y0+ay/2);b=(x0+290+bx/2,y0+by/2)
        good=p.get('ransac_inlier_mask',[False]*n)[i];color='#0072b2' if good else '#d55e00'
        if good:draw.line([a,b],fill=color,width=2)
        else:
            steps=max(1,int(math.dist(a,b)/7))
            for k in range(0,steps,2):
                z=[(a[0]+(b[0]-a[0])*min(t/steps,1),a[1]+(b[1]-a[1])*min(t/steps,1)) for t in [k,k+1]]
                draw.line(z,fill=color,width=1)
        dash='' if good else ' stroke-dasharray="5 4"'
        svg.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{color}"{dash}/>')
        for x,y in [a,b]:
            if good:
                draw.ellipse((x-3,y-3,x+3,y+3),outline=color,width=2)
                svg.append(f'<circle cx="{x}" cy="{y}" r="3" fill="none" stroke="{color}"/>')
            else:
                draw.line((x-3,y-3,x+3,y+3),fill=color,width=2);draw.line((x-3,y+3,x+3,y-3),fill=color,width=2)
                svg.append(f'<path d="M{x-3},{y-3}L{x+3},{y+3}M{x-3},{y+3}L{x+3},{y-3}" stroke="{color}"/>')
text(15,1460,'Known-image exploration; no image warp, score replacement, true correspondence or recovered-camera claim.')
svg.append('</svg>');(out/'S71_all8_feature_pairs.svg').write_text('\n'.join(svg));im.save(out/'S71_all8_feature_pairs.png')
rec.update(completed_utc=now(),source_sha256=sha(Path(__file__)),scope='Supporting figure; original photos retained as embedded raster, labels/lines vector in SVG; PNG preview only',outputs={p.name:sha(p) for p in out.iterdir() if p.is_file()})
(out/'EXPORT_RECEIPT.json').write_text(json.dumps(rec,indent=2)+'\n')
for p in out.iterdir():p.chmod(0o444)
print(json.dumps({'completed_utc':rec['completed_utc'],'out':str(out)}))
