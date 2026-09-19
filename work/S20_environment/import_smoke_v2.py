"""Import actual complete generator and Navigator, prohibiting model/data/network use."""
from pathlib import Path
import ast,datetime,hashlib,importlib,importlib.metadata as md,json,os,socket,sys,time,traceback,resource
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent;SOURCE=HERE/'isolated_vmem_source';OLD=ROOT/'work/S17C_environment/site-packages';CUT3R=SOURCE/'extern/CUT3R'
START=time.perf_counter();utc=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
OUT=HERE/'import_smoke_v2.json';assert not OUT.exists()
report={'started_utc':utc(),'status':'RUNNING_IMPORT_ONLY','checks':[],'blocked_events':[],'modules':{},'distributions':{},'model_constructor_attempts':0,'torch_weight_load_attempts':0,'PIL_image_open_attempts':0,'network_attempts':0}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(name,ok):
 report['checks'].append({'name':name,'pass':bool(ok)});assert ok,name
os.environ.update(PYTHONDONTWRITEBYTECODE='1',MPLBACKEND='Agg',MPLCONFIGDIR=str(HERE/'matplotlib-config'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HOME=str(HERE/'huggingface-cache'),HF_HUB_DISABLE_IMPLICIT_TOKEN='1',KORNIA_CHECK_VERSION='0')
def no_network(*a,**kw):
 report['network_attempts']+=1;raise RuntimeError('S20 import: no network')
socket.socket.connect=no_network;socket.create_connection=no_network
DENIED_SUFFIX={'.pth','.pt','.ckpt','.safetensors','.npz','.npy','.bin'}
def audit(event,args):
 if event in ['socket.connect','socket.sendto','subprocess.Popen','os.system','os.posix_spawn']:
  report['blocked_events'].append({'event':event});raise RuntimeError('S20 prohibits network/subprocess during import')
 if event=='open':
  p=args[0]
  if isinstance(p,(str,bytes,os.PathLike)):
   path=Path(os.fsdecode(p)).resolve()
   protected=[ROOT/'data', ROOT/'results', SOURCE/'test_samples', Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/test_samples')]
   if path.suffix.lower() in DENIED_SUFFIX or any(path.is_relative_to(q) for q in protected):
    report['blocked_events'].append({'event':event,'path':str(path)});raise RuntimeError('S20 prohibits weight/data opens')
sys.addaudithook(audit)
def profile(frame,event,arg):
 if event=='call' and frame.f_code.co_name=='__init__' and 'self' in frame.f_locals:
  obj=frame.f_locals['self']; name=type(obj).__name__
  if name in ['VMemPipeline','VMemModel','AutoEncoder','CLIPConditioner','ARCroco3DStereo']:
   report['model_constructor_attempts']+=1;raise RuntimeError('S20 import prohibits model construction: '+name)
try:
 install=json.loads((HERE/'install_receipt.json').read_text());check('wheels installed',install['status']=='PASS_INSTALLED_PENDING_IMPORT')
 report['guard_revision']='v2: resolve paths and protect data/results/test_samples/bin; audit socket/subprocess';report['earlier_import_receipt_sha256']=sha(HERE/'import_smoke.json')
 report['install_receipt_sha256']=sha(HERE/'install_receipt.json');report['source_manifest_sha256']=sha(HERE/'source_manifest.json')
 manifest=json.loads((HERE/'source_manifest.json').read_text())
 for r in manifest['source_files']:check('source identity '+r['path'],sha(SOURCE/r['path'])==r['final_sha256'])
 sys.path[:0]=[str(HERE/'site-packages'),str(OLD),str(SOURCE),str(CUT3R),str(CUT3R/'src')]
 os.chdir(SOURCE)
 import torch
 def no_load(*a,**kw):
  report['torch_weight_load_attempts']+=1;raise RuntimeError('S20 import: no weight load')
 torch.load=no_load
 import PIL.Image
 def no_image(*a,**kw):
  report['PIL_image_open_attempts']+=1;raise RuntimeError('S20 import: no image open')
 PIL.Image.open=no_image
 sys.setprofile(profile)
 from modeling.pipeline import VMemPipeline
 from navigation import Navigator
 from modeling.modules.autoencoder import AutoEncoder
 from modeling.modules.conditioner import CLIPConditioner
 from modeling.sampling import create_samplers
 from utils import do_sample
 from extern.CUT3R.cloud_opt.dust3r_opt import global_aligner
 from diffusers.models import AutoencoderKL
 import open_clip,kornia,av,imageio_ffmpeg
 from torchvision.io import write_video,read_video
 sys.setprofile(None)
 for name,obj in [('VMemPipeline',VMemPipeline),('Navigator',Navigator),('AutoEncoder',AutoEncoder),('CLIPConditioner',CLIPConditioner),('create_samplers',create_samplers),('do_sample',do_sample),('global_aligner',global_aligner),('AutoencoderKL',AutoencoderKL),('write_video',write_video),('read_video',read_video)]:check('callable '+name,callable(obj))
 cfg=open_clip.get_pretrained_cfg('ViT-H-14','laion2b_s32b_b79k');report['clip_pretrained_config']=cfg
 check('OpenCLIP exact upstream model tag',cfg['hf_hub']=='laion/CLIP-ViT-H-14-laion2B-s32B-b79K/')
 report['clip_architecture']=open_clip.get_model_config('ViT-H-14')
 check('CLIP architecture embed1024',report['clip_architecture']['embed_dim']==1024)
 for w in json.loads((HERE/'wheel_plan_v2.json').read_text())['wheels']:
  d=md.distribution(w['name']);check('distribution version '+w['name'],d.version==w['version']);check('distribution source '+w['name'],Path(d._path).is_relative_to(HERE/'site-packages'));report['distributions'][w['name']]={'version':d.version,'path':str(d._path)}
 for n in ['torch','torchvision','numpy','huggingface-hub','transformers','accelerate','safetensors']:
  d=md.distribution(n);report['distributions'][n]={'version':d.version,'path':str(d._path)};check('retained base '+n,Path(d._path).is_relative_to(ROOT/'.venv-cut3r'))
 for n,m in sorted(sys.modules.items()):
  f=getattr(m,'__file__',None)
  selected=n in ['navigation','surfel_inference','utils','utils.util'] or n.startswith(('modeling.','extern.CUT3R.','cloud_opt.','dust3r.','src.dust3r.','models.','croco.'))
  if selected and f:
   p=Path(f).resolve();check('isolated source module '+n,p.is_relative_to(SOURCE));report['modules'][n]={'path':str(p),'sha256':sha(p)}
 check('no model construction',report['model_constructor_attempts']==0);check('no torch weight load',report['torch_weight_load_attempts']==0);check('no PIL image opens',report['PIL_image_open_attempts']==0);check('no network',report['network_attempts']==0);check('no denied data attempts',not report['blocked_events'])
 ns=dict(Path=Path,hashlib=hashlib,os=os,json=json);tree=ast.parse((ROOT/'work/S17C_interface_preparation/install_overlay.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['sha','tree_state']],type_ignores=[]),'<existing read-only filesystem helper>','exec'),ns)
 before=json.loads((HERE/'existing_environment_before.json').read_text());after={str(p):ns['tree_state'](p) for p in [ROOT/'.venv-cut3r',ROOT/'.venv',OLD]};check('existing environments unchanged except bytecode',before==after)
 report['status']='PASS_FULL_PIPELINE_IMPORT_ONLY'
except BaseException as exc:
 sys.setprofile(None);report['status']='FAILED_IMPORT_ONLY';report['failure']=traceback.format_exc()
finally:
 report['ended_utc']=utc();report['elapsed_seconds']=time.perf_counter()-START;report['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;report['script_sha256']=sha(__file__);report['pass_checks']=sum(c['pass'] for c in report['checks']);OUT.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','pass_checks','elapsed_seconds','peak_rss_bytes']}));print(report.get('failure',''))
