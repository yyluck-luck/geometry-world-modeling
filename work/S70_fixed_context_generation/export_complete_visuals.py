"""Export all accepted S70 pixels unchanged, with a labelled full-grid preview."""
from pathlib import Path
from datetime import datetime, timezone
import base64
import hashlib
import html
import io
import json

import numpy as np
from PIL import Image, ImageDraw, ImageFont

D = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    score = json.loads((D/'scoring_01/receipt.json').read_text())
    verify = json.loads((D/'rgb_verification_01/receipt.json').read_text())
    binding = json.loads((D/'ROOT_SCORING_BINDING.json').read_text())
    assert score['status'] == 'COMPLETE_FIXED_RGB_SCORE_PENDING_INDEPENDENT_RECOMPUTE'
    assert verify['status'] == 'PASS_INDEPENDENT_INTEGER_RGB_SCORE'
    assert score['target_ids'] == verify['target_ids'] == [20,21,22,23]
    assert verify['new_method_validated'] is False
    out = D/'visuals_01'
    out.mkdir(exist_ok=False)
    receipt = {'started_utc':datetime.now(timezone.utc).isoformat(), 'inputs':[],
               'native_pngs':[], 'scope':'all4 targets x reference/A0/A1/B; no pixel correction',
               'new_method_validated':False}
    rows = []
    for arm in ('reference','A0','A1','B'):
        path = D/'scoring_01/transformed_targets_uint8.npy' if arm == 'reference' else D/'execution_01'/arm/'targets_uint8.npy'
        expected = score['outputs_before_receipt'][path.name]['sha256'] if arm == 'reference' else binding['result_files_sha256'][str(path)]
        raw = path.read_bytes()
        assert sha(raw) == expected
        a = np.load(io.BytesIO(raw), allow_pickle=False)
        assert a.shape == (4,576,576,3) and a.dtype == np.uint8
        receipt['inputs'].append({'path':str(path),'sha256':sha(raw),'bytes':len(raw)})
        row = []
        for i,t in enumerate(score['target_ids']):
            p = out/f'{arm}_target_{t}.png'
            Image.fromarray(a[i]).save(p)
            with Image.open(p) as im:
                assert im.mode == 'RGB' and np.array(im).tobytes() == a[i].tobytes()
            receipt['native_pngs'].append({'path':str(p),'sha256':sha(p.read_bytes()),
                'decoded_pixels_sha256':sha(a[i].tobytes()),'exact_pixel_readback':True})
            row.append((p,Image.fromarray(a[i])))
        rows.append(row)
    # Labels and preview resampling affect only the overview, never individual PNGs.
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',22)
    small = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
    cell, left, top, gap, rowgap = 288, 155, 82, 12, 48
    width = left + 4*(cell+gap)+12
    height = top + 4*(cell+rowgap)+105
    canvas = Image.new('RGB',(width,height),'white')
    draw = ImageDraw.Draw(canvas)
    draw.text((18,14),'S70: all four fixed targets, all three generation runs',fill='#17202a',font=font)
    labels = ['Real reference','A0: context A','A1: repeat A','B: context B']
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
           '<rect width="100%" height="100%" fill="white"/>',
           '<g fill="#17202a" font-family="Arial,sans-serif" font-size="22">',
           '<text x="18" y="38">S70: all four fixed targets, all three generation runs</text>']
    for i,t in enumerate(score['target_ids']):
        x=left+i*(cell+gap)
        draw.text((x,52),f'Target {t}',fill='#17202a',font=font)
        svg.append(f'<text x="{x}" y="74">Target {t}</text>')
    for j,row in enumerate(rows):
        y=top+j*(cell+rowgap)
        draw.text((12,y+120),labels[j],fill='#17202a',font=small)
        svg.append(f'<text x="12" y="{y+142}" font-size="16">{labels[j]}</text>')
        for i,(p,im) in enumerate(row):
            x=left+i*(cell+gap)
            canvas.paste(im.resize((cell,cell),Image.Resampling.LANCZOS),(x,y))
            src=base64.b64encode(p.read_bytes()).decode('ascii')
            svg.append(f'<image x="{x}" y="{y}" width="{cell}" height="{cell}" href="data:image/png;base64,{src}"/>')
            if j:
                label=f'MSE {score["frames"][i]["mse"][("A0","A1","B")[j-1]]:.7f}'
                draw.text((x,y+cell+5),label,fill='#17202a',font=small)
                svg.append(f'<text x="{x}" y="{y+cell+22}" font-size="16">{label}</text>')
    foot=[f'Exact A/A latent + raw RGB replay: {score["replay"]["all_passed"]}. Delta MSE (B - A0): {score["delta_B_minus_A0"]:+.9f}.',
          'One known short sequence; GT cameras; declared ft-mse VAE variant. No validated new method.',
          'Original 576 x 576 PNGs preserve output pixels. Preview is resized; no alignment or enhancement.']
    for k,line in enumerate(foot):
        y=height-80+k*25
        draw.text((18,y),line,fill='#17202a',font=small)
        svg.append(f'<text x="18" y="{y+18}" font-size="16">{html.escape(line)}</text>')
    canvas.save(out/'S70_all_targets_contact_sheet.png')
    svg.append('</g></svg>')
    (out/'S70_all_targets_contact_sheet.svg').write_text('\n'.join(svg))
    receipt.update(completed_utc=datetime.now(timezone.utc).isoformat(),status='COMPLETE_ALL16_NATIVE_PNGS_EXACT_READBACK',
                   preview_resampling='288px LANCZOS, original native PNGs unchanged',
                   source_sha256=sha(Path(__file__).read_bytes()),
                   outputs={p.name:sha(p.read_bytes()) for p in out.iterdir() if p.is_file()})
    (out/'EXPORT_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    for p in out.iterdir():
        if p.is_file():p.chmod(0o444)
    print(json.dumps({'status':receipt['status'],'out':str(out)}))


if __name__ == '__main__':
    main()
