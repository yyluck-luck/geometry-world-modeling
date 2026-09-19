from pathlib import Path
from datetime import datetime, timezone
import base64, hashlib, html, io, json
from PIL import Image, ImageDraw, ImageFont
D=Path(__file__).resolve().parent
r=json.loads((D/'execution_01/receipt.json').read_text())
c=json.loads((D/'CONTRACT_v2.json').read_text())
assert r['status']=='COMPLETE_REAL_CONTROL_DIAGNOSTIC'
out=D/'visuals_01';out.mkdir(exist_ok=False)
W,H=1220,830
im=Image.new('RGB',(W,H),'white');draw=ImageDraw.Draw(im)
fontpath='/System/Library/Fonts/Supplemental/Arial.ttf'
font=ImageFont.truetype(fontpath,15);title=ImageFont.truetype(fontpath,22)
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="white"/>']
def text(x,y,s,size=15):
 draw.text((x,y),s,font=title if size==22 else font,fill='#17202A')
 svg.append(f'<text x="{x}" y="{y+size}" font-family="Arial" font-size="{size}" fill="#17202A">{html.escape(s)}</text>')
def photo(path,x,y,expected):
 b=path.read_bytes();assert hashlib.sha256(b).hexdigest()==expected
 with Image.open(io.BytesIO(b)) as src:im.paste(src.resize((280,280),Image.Resampling.LANCZOS),(x,y))
 svg.append(f'<image x="{x}" y="{y}" width="280" height="280" href="data:image/png;base64,{base64.b64encode(b).decode()}"/>')
def mark(x,y,color,solid):
 if solid:draw.ellipse((x-3,y-3,x+3,y+3),outline=color,width=2);svg.append(f'<circle cx="{x}" cy="{y}" r="3" stroke="{color}" fill="none"/>')
 else:
  draw.line((x-3,y-3,x+3,y+3),fill=color,width=2);draw.line((x-3,y+3,x+3,y-3),fill=color,width=2)
  svg.append(f'<path d="M{x-3},{y-3}L{x+3},{y+3}M{x-3},{y+3}L{x+3},{y-3}" stroke="{color}"/>')
text(20,14,'S72 | Real-photo controls: most matches near requested epipolar lines',22)
text(20,45,'Blue circles: <=5 px. Orange crosses: >5 px or invalid. Display threshold only; not proof of correct cameras.')
text(20,67,'All four targets retained. Up to 12 matches shown at evenly spaced indices; every match is saved in the receipt.')
selected={}
for k,row in enumerate(r['pairs']):
 ox=20+(k%2)*605;oy=107+(k//2)*354;j=row['target_id'];n=row['match_count']
 text(ox,oy,f"Real 19 -> real {j} | n={n} | median={row['residual_quantiles_px'][1]:.2f} px")
 text(ox,oy+21,'History 19                                      Target '+str(j))
 y0=oy+45
 photo(D/'execution_01/real_anchor_19.png',ox,y0,r['anchor_export_sha256'])
 p=Path(c['targets'][str(j)]['path']);photo(p,ox+295,y0,c['targets'][str(j)]['sha256'])
 ix=sorted(set(round(i*(n-1)/(min(12,n)-1)) for i in range(min(12,n)))) if n>1 else list(range(n))
 selected[str(j)]=ix
 for i in ix:
  a=row['source_xy'][i];b=row['target_xy'][i];v=row['residuals'][i]
  solid=v is not None and v[2]<=5;col='#0072B2' if solid else '#D55E00'
  x1,y1=ox+a[0]*280/576,y0+a[1]*280/576;x2,y2=ox+295+b[0]*280/576,y0+b[1]*280/576
  draw.line((x1,y1,x2,y2),fill=col,width=1)
  svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="1"'+('' if solid else ' stroke-dasharray="4 3"')+'/>')
  mark(x1,y1,col,solid);mark(x2,y2,col,solid)
text(20,794,'576 x 576 native images; preview resized without warping. Approximate K; target 23 retains a large outlier tail.')
svg.append('</svg>')
im.save(out/'S72_all4_real_controls.png');(out/'S72_all4_real_controls.svg').write_text(''.join(svg))
receipt={'completed_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'input_receipt_sha256':hashlib.sha256((D/'execution_01/receipt.json').read_bytes()).hexdigest(),'selected_indices':selected,'scope':'supporting diagnostic figure; actual photos, no AI image generation, only display resizing and match overlays','output_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}}
(out/'EXPORT_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
for p in out.iterdir():p.chmod(0o444)
print(json.dumps(receipt))
