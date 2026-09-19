"""Export all nine exact S64 RGB arrays after fixed scoring and independent confirmation.

The PNGs round-trip to the authoritative raw bytes. The contact sheet is only a
display artifact, never the input to a scientific measurement.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import stat
import sys
from PIL import Image, ImageDraw, ImageFont

R=Path(__file__).resolve().parents[2]
OUT=R/'results/S64_unit_repaired_generation/visual_qa_all9'
PARENT_SOURCE_SHA='f0f3e792b6fe5f2f702b7f0e87df337745aad6b62cceef61852c64dec45a1aa5'
YAWS=(0,1.25,2.5,3.75,5,3.75,2.5,1.25,0)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p,expected):
    assert sha(p)==expected,str(p)
    return json.loads(p.read_text())

def main():
    assert len(sys.argv)==3, 'Actual post-score binding path and SHA required'
    binding_path=Path(sys.argv[1]).resolve()
    assert binding_path.parent==Path(__file__).resolve().parent
    binding=read(binding_path,sys.argv[2])
    assert binding['row']=='C2_UNIT_REPAIRED_S64'
    assert binding['stage']=='SCORE_AND_INDEPENDENT_RECOMPUTATION_ACCEPTED'
    assert binding['eligible_for_original_cohort'] is False
    for item in binding['evidence'].values():
        assert sha(Path(item['path']))==item['sha256']
    identities=binding['authoritative_pixel_identities']
    assert len(identities)==9
    assert not OUT.exists()
    OUT.mkdir(mode=0o755)
    records=[];frames=[]
    for i,item in enumerate(identities):
        assert item['id']==i
        source=Path(item['blob']).resolve()
        assert source.is_relative_to(R/'results/S64_unit_repaired_generation/archive')
        fd=os.open(source,os.O_RDONLY|os.O_NOFOLLOW)
        with os.fdopen(fd,'rb') as h:
            before=os.fstat(h.fileno());raw=h.read();after=os.fstat(h.fileno())
        identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
        assert stat.S_ISREG(before.st_mode) and identity(before)==identity(after)==identity(source.lstat())
        assert len(raw)==576*576*3 and hashlib.sha256(raw).hexdigest()==item['tensor_body_sha256']
        frame=Image.frombytes('RGB',(576,576),raw)
        name=('frame_00_input.png' if i==0 else f'frame_{i:02d}_model_generated_requested_yaw_{YAWS[i]:.2f}.png')
        target=OUT/name;frame.save(target,format='PNG')
        with Image.open(target) as reloaded:
            assert reloaded.mode=='RGB' and reloaded.size==(576,576) and reloaded.tobytes()==raw
        records.append(dict(id=i,requested_yaw_degrees=YAWS[i],kind='input_fixed_crop_resize' if i==0 else 'model_generated',
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
    draw.text((gap,18),'S64 unit-repaired variant: all nine frames in order',font=titlefont,fill='#14212e')
    draw.text((gap,63),'VMem + ft-mse VAE variant | seed 44 | requested yaw: 0 -> +5 -> 0 degrees',font=font,fill='#334452')
    for i,frame in enumerate(frames):
        x=gap+(i%3)*(tile+gap);y=header+(i//3)*(tile+label+gap)
        kind='INPUT (fixed preprocessing)' if i==0 else 'MODEL GENERATED'
        draw.text((x,y),f'ID {i} | {kind}',font=font,fill='#14212e')
        draw.text((x,y+29),f'Requested yaw: {YAWS[i]:+.2f} degrees',font=font,fill='#334452')
        sheet.paste(frame,(x,y+label))
    draw.text((gap,height-footer+5),'Post-score display only. Requested camera angles do not establish rendered camera obedience.',font=font,fill='#334452')
    contact=OUT/'S64_all9_contact_sheet.png';sheet.save(contact,format='PNG')
    manifest=dict(schema='s66-postscore-s64-all9-visual-export-v1',created_utc=datetime.now(timezone.utc).isoformat(),
        binding_path=str(binding_path),binding_sha256=sys.argv[2],evidence=binding['evidence'],parent_source_sha256=PARENT_SOURCE_SHA,
        source=str(Path(__file__)),source_sha256=sha(Path(__file__)),frames=records,
        exact_raw_rgb_preserved_in_individual_pngs=True,images_human_viewed_by_exporter=0,
        contact_sheet_path=str(contact),contact_sheet_sha256=sha(contact),
        data_transformations='PNG encoding only for individual frames; full-resolution unaltered panels on a labelled contact sheet.',
        claim_boundary='ID0 is the fixed preprocessed input; IDs1-8 are actual outputs of the recorded model run, not real scene photographs. Display does not prove visual quality, geometric correctness, camera obedience, method gain, or novelty.')
    with (OUT/'manifest.json').open('x') as f:json.dump(manifest,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'out':str(OUT),'contact':str(contact),'manifest_sha256':sha(OUT/'manifest.json')},ensure_ascii=False))

if __name__=='__main__':main()
