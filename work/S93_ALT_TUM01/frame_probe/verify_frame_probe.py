from pathlib import Path
import hashlib,json,subprocess
from PIL import Image
root=Path(__file__).parent
files=[root/'rgb_movie_full_unintended.bin',root/'depth_movie_prefix_1MiB.bin',root/'decode/rgb0.png',root/'decode/depth0.png']
def sha(p):
 h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def probe(p):
 r=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)],text=True,capture_output=True)
 return r.returncode, json.loads(r.stdout) if r.stdout else {'stderr':r.stderr}
out={'checks':{},'files':{}}
for p in files:
 out['files'][str(p.relative_to(root))]={'bytes':p.stat().st_size,'sha256':sha(p)}
for key,p in [('rgb_movie',files[0]),('depth_prefix',files[1])]:
 rc,d=probe(p); s=d.get('streams',[{}])[0]; out['checks'][key]={'ffprobe_rc':rc,'codec':s.get('codec_name'),'codec_tag':s.get('codec_tag_string'),'size':[s.get('width'),s.get('height')],'pix_fmt':s.get('pix_fmt'),'time_base':s.get('time_base'),'r_frame_rate':s.get('r_frame_rate')}
for key,p in [('rgb_png',files[2]),('depth_png',files[3])]:
 im=Image.open(p); out['checks'][key]={'mode':im.mode,'size':list(im.size),'bits':im.bits if hasattr(im,'bits') else None}
out['checks']['media_total_bytes']=files[0].stat().st_size+files[1].stat().st_size
out['checks']['under_10mb']=out['checks']['media_total_bytes']<10_000_000
out['checks']['gate0']=False
(root/'VERIFY_FRAME_PROBE.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
