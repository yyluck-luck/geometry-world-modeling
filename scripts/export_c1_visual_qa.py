"""Export all nine exact C1 RGB arrays after the sealed blind score.

The PNGs round-trip to the authoritative raw bytes. The contact sheet is only a
display artifact, never the input to a scientific measurement.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import stat
from PIL import Image, ImageDraw, ImageFont

R=Path(__file__).resolve().parents[1]
D=R/'work/S46_c1_blind_scoring_preparation'
OUT=R/'results/S44_C1_confirmation_generation/visual_qa_all9'
CONTRACT_SHA='07fb2e893c1e0072d72dd9e50b9ad1c5321c4da9fd9d25a61b4a1d322b92c3d9'
REPORT_SHA='0f222e861b4b29ec14c39ede253e136bf8e2412ce2234d433600b4b8b96b8ca7'
RECEIPT_SHA='b9a498206b81c88d31a2fc29407edb85e73fb6d13df285b063afd5e1d7b7a4bc'
YAWS=(0,1.25,2.5,3.75,5,3.75,2.5,1.25,0)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p,expected):
    assert sha(p)==expected,str(p)
    return json.loads(p.read_text())

def main():
    report=read(D/'C1_score_attempt_01/report.json',REPORT_SHA)
    receipt=read(D/'C1_score_attempt_01/receipt.json',RECEIPT_SHA)
    contract=read(D/'C1_SCORING_BOUND_CONTRACT.json',CONTRACT_SHA)
    orchestration=json.loads((R/'work/resumption_20260908/S46_C1_FORMAL_ORCHESTRATION.json').read_text())
    assert receipt['technically_valid'] is True and receipt['report_sha256']==REPORT_SHA
    assert orchestration['returncode']==0 and report['status']=='PASS_C1_BLIND_SCORE_TECHNICALLY_VALID'
    assert not OUT.exists()
    OUT.mkdir(mode=0o755)
    records=[];frames=[]
    for i,item in enumerate(contract['binding_slots']['authoritative_pixel_identities']):
        assert item['id']==i
        source=Path(item['blob'])
        fd=os.open(source,os.O_RDONLY|os.O_NOFOLLOW)
        with os.fdopen(fd,'rb') as h:
            before=os.fstat(h.fileno());raw=h.read();after=os.fstat(h.fileno())
        identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
        assert stat.S_ISREG(before.st_mode) and identity(before)==identity(after)==identity(source.lstat())
        assert len(raw)==576*576*3 and hashlib.sha256(raw).hexdigest()==item['tensor_body_sha256']
        frame=Image.frombytes('RGB',(576,576),raw)
        name=('frame_00_real_input.png' if i==0 else f'frame_{i:02d}_model_generated_requested_yaw_{YAWS[i]:.2f}.png')
        target=OUT/name;frame.save(target,format='PNG')
        with Image.open(target) as reloaded:
            assert reloaded.mode=='RGB' and reloaded.size==(576,576) and reloaded.tobytes()==raw
        records.append(dict(id=i,requested_yaw_degrees=YAWS[i],kind='real_input_fixed_crop_resize' if i==0 else 'model_generated',
            source_blob=str(source),source_body_sha256=item['tensor_body_sha256'],
            tensor_descriptor_sha256=item['tensor_descriptor_sha256'],png_path=str(target),png_sha256=sha(target),
            decoded_png_exactly_matches_raw_rgb=True))
        frames.append(frame)
    # Full-resolution panels; no crop, colour correction, or highlight inside data.
    tile=576;label=64;gap=18;header=115;footer=66
    width=3*tile+4*gap;height=header+3*(tile+label+gap)+footer
    sheet=Image.new('RGB',(width,height),'#f4f6f8');draw=ImageDraw.Draw(sheet)
    fontpath='/System/Library/Fonts/Supplemental/Arial.ttf'
    font=ImageFont.truetype(fontpath,24);titlefont=ImageFont.truetype(fontpath,32)
    draw.text((gap,18),'C1 baseline: all nine frames, in chronological order',font=titlefont,fill='#14212e')
    draw.text((gap,63),'VMem + ft-mse VAE variant | seed 43 | requested yaw: 0 -> +5 -> 0 degrees',font=font,fill='#334452')
    for i,frame in enumerate(frames):
        x=gap+(i%3)*(tile+gap);y=header+(i//3)*(tile+label+gap)
        kind='REAL INPUT (fixed preprocessing)' if i==0 else 'MODEL GENERATED'
        draw.text((x,y),f'ID {i} | {kind}',font=font,fill='#14212e')
        draw.text((x,y+29),f'Requested yaw: {YAWS[i]:+.2f} degrees',font=font,fill='#334452')
        sheet.paste(frame,(x,y+label))
    draw.text((gap,height-footer+5),'Post-score display only. Requested camera angles do not establish rendered camera obedience.',font=font,fill='#334452')
    contact=OUT/'C1_all9_contact_sheet.png';sheet.save(contact,format='PNG')
    manifest=dict(schema='c1-post-blind-score-all9-visual-export-v1',created_utc=datetime.now(timezone.utc).isoformat(),
        score_report_sha256=REPORT_SHA,score_receipt_sha256=RECEIPT_SHA,contract_sha256=CONTRACT_SHA,
        source=str(Path(__file__)),source_sha256=sha(Path(__file__)),frames=records,
        exact_raw_rgb_preserved_in_individual_pngs=True,images_human_viewed_by_exporter=0,
        contact_sheet_path=str(contact),contact_sheet_sha256=sha(contact),
        data_transformations='PNG encoding only for individual frames; full-resolution unaltered panels on a labelled contact sheet.',
        claim_boundary='ID0 is one preprocessed real observation; IDs1-8 are actual outputs of the recorded model run, not real scene photographs. Display does not prove visual quality, geometric correctness, camera obedience, method gain, or novelty.')
    with (OUT/'manifest.json').open('x') as f:json.dump(manifest,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'out':str(OUT),'contact':str(contact),'manifest_sha256':sha(OUT/'manifest.json')},ensure_ascii=False))

if __name__=='__main__':main()
