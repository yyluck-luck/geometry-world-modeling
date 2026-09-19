"""Expose only ten predeclared past frames; real data qualification, not prediction."""
from pathlib import Path
from datetime import datetime,timezone
from fractions import Fraction
import hashlib,json,re,shutil,subprocess,time,traceback
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent
source=D/'two_stream_mirror_01'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
assert sha(D/'PAST_PREFIX_INSPECTION_PLAN.md')=='e26ba65b78ace9aec61ea4d26d8b3eac2e7797771cfa07fca8cd8750d0385fab'
assert sha(source/'FINAL_DELIVERY.json')=='66953084ddd9cb59ee753a659542fad10aa76f64071b274e1b278f8b15f66c1f'
assert sha(source/'receipt.json')=='06641f36e9195168a1797d33d6189fc852e733533b0b2cf4e5a0da7cd7826b2e'
media=source/'cam06.mp4'
assert media.stat().st_size==64468940 and sha(media)=='3a5cb2acd5266d23c83d7dbd16c10b69da10eac73b689011e275b0da33695f0d'
streams=json.loads((source/'cam06.streams.json').read_text())['streams']
assert len(streams)==1 and streams[0]['width']==2704 and streams[0]['height']==2028
frames=json.loads((source/'cam06.frames.json').read_text())['frames']
tb=Fraction(streams[0]['time_base']); times=[f['pts']*tb for f in frames]
mapping=[]
for j in range(10):
    target=Fraction(j,2)
    idx=min(range(len(times)),key=lambda i:(abs(times[i]-target),times[i]))
    assert abs(times[idx]-target)<=Fraction(1,60) and times[idx]<5
    mapping.append({'output_index':j,'source_frame_index':idx,'pts':frames[idx]['pts'],'exact_seconds':str(times[idx])})
assert [x['source_frame_index'] for x in mapping]==list(range(0,136,15))
out=D/'past_prefix_01';out.mkdir(exist_ok=False)
rec={'started_utc':now(),'status':'RUNNING','plan_sha256':sha(D/'PAST_PREFIX_INSPECTION_PLAN.md'),
 'source_sha256':sha(Path(__file__)),'cam06_file_sha256':sha(media),'metadata_inputs':{p.name:sha(p) for p in (source/'cam06.streams.json',source/'cam06.frames.json')},
 'media_hash_read_bytes_before_decode':2*64468940,'mapping':mapping,'future_exported_or_viewed':False,'new_method_validated':False}
tick=time.monotonic()
try:
    filt='select='+ '+'.join('eq(n\\,%d)'%x['source_frame_index'] for x in mapping)+',scale=676:507:flags=area,showinfo'
    argv=[shutil.which('ffmpeg'),'-nostdin','-hide_banner','-loglevel','info','-threads','1','-filter_threads','1','-i',str(media),'-map','0:v:0','-vf',filt,'-an','-sn','-dn','-frames:v','10','-fps_mode','passthrough','-threads','1','-start_number','0',str(out/'cam06_past_%02d.png')]
    rec['argv']=argv; rec['decode_started_utc']=now()
    with (out/'ffmpeg.stdout.txt').open('x') as fo,(out/'ffmpeg.stderr.txt').open('x') as fe:
        p=subprocess.run(argv,stdout=fo,stderr=fe,timeout=120)
    rec['decode_completed_utc']=now();rec['returncode']=p.returncode
    assert p.returncode==0
    log=(out/'ffmpeg.stderr.txt').read_text()
    observed=[int(x) for x in re.findall(r'\bn:\s*\d+\s+pts:\s*(-?\d+)\s+pts_time:',log)]
    assert observed==[x['pts'] for x in mapping],observed
    imgs=sorted(out.glob('cam06_past_*.png'));assert len(imgs)==10
    rec['pngs']=[]
    for m,p in zip(mapping,imgs):
        with Image.open(p) as im:
            assert im.size==(676,507)
            rec['pngs'].append({'path':str(p),'file_sha256':sha(p),'wh':list(im.size),'mode':im.mode,**m})
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',20)
    small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
    canvas=Image.new('RGB',(724,1490),'white');draw=ImageDraw.Draw(canvas)
    draw.text((18,14),'Real video: cam06, all 10 predeclared past observations',font=font,fill='#18222b')
    draw.text((18,43),'Coffee Martini / Neural 3D Video. No model generation.',font=small,fill='#18222b')
    for j,(m,p) in enumerate(zip(mapping,imgs)):
        x=18+(j%2)*354;y=77+(j//2)*275
        with Image.open(p) as im:canvas.paste(im.convert('RGB').resize((338,254),Image.Resampling.LANCZOS),(x,y))
        draw.text((x,y+255),f't={float(Fraction(m["exact_seconds"])):.1f}s | source frame {m["source_frame_index"]}',font=small,fill='#18222b')
    draw.text((18,1460),'Past-only sampling; no future outcome or motion prediction inspected.',font=small,fill='#18222b')
    canvas.save(out/'REAL_cam06_past10_contact_sheet.png')
    assert sum(p.stat().st_size for p in out.iterdir())<20*1024**2
    rec['status']='COMPLETE_TEN_PREDECLARED_PAST_FRAMES_PENDING_VISUAL_INSPECTION'
    rec['showinfo_pts']=observed
    rec['exposure_scope']='Only cam06 t=0,.5,...4.5 exported. Codec may internally decode dependency frames; byte-level reads are not future-semantic access. No cam00 pixel export, no audio.'
except BaseException as exc:
    rec['status']='FAILED_PRESERVED';rec['error']=repr(exc);rec['traceback']=traceback.format_exc()
rec['completed_utc']=now();rec['elapsed_seconds']=time.monotonic()-tick
rec['outputs']={p.name:sha(p) for p in out.iterdir() if p.is_file()}
with (out/'EXPORT_RECEIPT.json').open('x') as f:json.dump(rec,f,indent=2);f.write('\n')
for p in out.iterdir():p.chmod(0o444)
print(json.dumps({k:rec[k] for k in ('status','started_utc','completed_utc','elapsed_seconds')}))
raise SystemExit(0 if rec['status'].startswith('COMPLETE') else 1)
