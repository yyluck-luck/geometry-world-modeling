from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib,json
from datetime import datetime,timezone
root=Path(__file__).parent
r=json.loads((root/'execution_01/receipt.json').read_text())
out=root/'visuals_01';out.mkdir(exist_ok=False)
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',22)
items=[]; combined=Image.new('RGB',(1152,614*5),'white')
for i,row in enumerate(r['rows']):
    canvas=Image.new('RGB',(1152,614),'white');draw=ImageDraw.Draw(canvas)
    for col,key in enumerate(['reference','reconstruction']):
        rec=row['pngs'][key];p=Path(rec['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==rec['file_sha256']
        im=Image.open(p).convert('RGB');assert im.size==(576,576)
        canvas.paste(im,(col*576,38));draw.text((col*576+12,8),f"History {row['history_id']} | {key}",fill='black',font=font)
    dst=out/f"history_{row['history_id']}_pair.png";canvas.save(dst);combined.paste(canvas,(0,614*i));items.append({'path':str(dst),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'source_pngs':row['pngs']})
combined.save(out/'ALL_FIVE_PAIRS.png')
(out/'manifest.json').write_text(json.dumps({'created_utc':datetime.now(timezone.utc).isoformat(),'source_receipt_sha256':hashlib.sha256((root/'execution_01/receipt.json').read_bytes()).hexdigest(),'scope':'Fixed display only. Original PNG pixels pasted at native size; no image edits, selection, alignment or AI synthesis. All five histories retained. Human inspection tracked separately.','pairs':items,'combined_sha256':hashlib.sha256((out/'ALL_FIVE_PAIRS.png').read_bytes()).hexdigest()},indent=2))
print(out)
