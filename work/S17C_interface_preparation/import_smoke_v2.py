"""Import embedded geometry stack with fixed overlay, no model/data/network."""
from pathlib import Path
import ast, datetime, hashlib, importlib, importlib.metadata as md, json, os, socket, sys, time, traceback
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
ENV=ROOT/'work/S17C_environment'
OVERLAY=ENV/'site-packages'
SOURCE=HERE/'isolated_vmem_source'
CUT3R=SOURCE/'extern/CUT3R'
START=time.perf_counter()
report={'status':'RUNNING_IMPORT_ONLY','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'model_instantiations':0,'weight_load_attempts':0,'image_open_attempts':0,'network_attempts':0,
        'modules':{},'distributions':{},'checks':[]}
assert not (ENV/'import_smoke_v2.json').exists()
os.environ.update(PYTHONDONTWRITEBYTECODE='1',MPLCONFIGDIR=str(ENV/'matplotlib-config'),
                  MPLBACKEND='Agg',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
                  HF_HOME=str(ENV/'huggingface-cache'))
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def reject_network(*a,**k):
    report['network_attempts']+=1
    raise RuntimeError('S17C import smoke prohibits network')
socket.socket.connect=reject_network
socket.create_connection=reject_network
def check(name,ok):
    report['checks'].append({'name':name,'pass':bool(ok)})
    assert ok,name
try:
    prior=json.loads((ENV/'addendum_receipt.json').read_text())
    check('overlay installation completed',prior['status']=='OVERLAY_INSTALLED_PENDING_IMPORT_SMOKE')
    check('overlay exists',OVERLAY.is_dir())
    sys.path[:0]=[str(OVERLAY),str(CUT3R),str(CUT3R/'src')]
    import torch
    def reject_load(*a,**k):
        report['weight_load_attempts']+=1
        raise RuntimeError('S17C import smoke prohibits weight loads')
    torch.load=reject_load
    import PIL.Image
    def reject_image(*a,**k):
        report['image_open_attempts']+=1
        raise RuntimeError('S17C import smoke prohibits image opens')
    PIL.Image.open=reject_image
    # These imports only define classes/functions, no constructor or inference call.
    from dust3r.model import ARCroco3DStereo
    wrapper=importlib.import_module('surfel_inference')
    infer=importlib.import_module('src.dust3r.inference')
    align=importlib.import_module('cloud_opt.dust3r_opt')
    base=importlib.import_module('cloud_opt.dust3r_opt.base_opt')
    init=importlib.import_module('cloud_opt.dust3r_opt.init_im_poses')
    imageutils=importlib.import_module('src.dust3r.utils.image')
    for name,obj in [('ARCroco3DStereo',ARCroco3DStereo),('run_inference_from_pil',wrapper.run_inference_from_pil),
        ('prepare_input_from_pil',wrapper.prepare_input_from_pil),('prepare_output',wrapper.prepare_output),
        ('inference',infer.inference),('global_aligner',align.global_aligner),
        ('global_alignment_iter',base.global_alignment_iter),('clean_pointcloud',base.clean_pointcloud),
        ('fast_pnp',init.fast_pnp)]:
        check('callable '+name,callable(obj))
    for name,m in sorted(sys.modules.items()):
        f=getattr(m,'__file__',None)
        selected=(name in ['surfel_inference','add_ckpt_path','dust3r','src.dust3r','models','croco','cloud_opt'] or name.startswith(('dust3r.','src.dust3r.','models.','croco.','cloud_opt.')))
        if selected and f:
            p=Path(f).resolve()
            check('isolated module origin '+name,p.is_relative_to(CUT3R))
            report['modules'][name]={'path':str(p),'sha256':sha(p)}
    check('original wrapper byte identity',sha(wrapper.__file__)==sha(Path(json.loads((HERE/'source_plan.json').read_text())['vmem_root'])/'extern/CUT3R/surfel_inference.py'))
    check('CPU RoPE candidate imported', 'models.rope_cpu' in sys.modules)
    check('no main VMem pipeline loaded','modeling.pipeline' not in sys.modules)
    check('no diffusers loaded',not any(n=='diffusers' or n.startswith('diffusers.') for n in sys.modules))
    check('no open_clip loaded',not any(n=='open_clip' or n.startswith('open_clip.') for n in sys.modules))
    plan=json.loads((HERE/'overlay_wheel_plan.json').read_text())
    extra=json.loads((HERE/'overlay_wheel_addendum.json').read_text())
    plan['wheels'] += extra['wheels']
    plan['baseline_retained'].update(extra['baseline_retained'])
    expected={x['name']:x['version'] for x in plan['wheels']}
    expected.update(plan['baseline_retained'])
    expected.update({'torch':'2.7.0','torchvision':'0.22.0','transformers':'4.48.3','accelerate':'1.4.0'})
    for name,version in expected.items():
        d=md.distribution(name)
        check('distribution version '+name,d.version==version)
        location=Path(d._path).resolve()
        should_overlay=name in {x['name'] for x in plan['wheels']}
        expected_base=OVERLAY if should_overlay else ROOT/'.venv-cut3r'
        check('distribution origin '+name,location.is_relative_to(expected_base))
        report['distributions'][name]={'version':d.version,'metadata_path':str(location),'source':'overlay' if should_overlay else 'existing .venv-cut3r'}
    check('no weight load',report['weight_load_attempts']==0)
    check('no image open',report['image_open_attempts']==0)
    check('no network',report['network_attempts']==0)
    # Compare old environments again after imported modules have initialized.
    tree=ast.parse((HERE/'install_overlay.py').read_text())
    ns=dict(Path=Path,hashlib=hashlib,os=os,json=json)
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['sha','tree_state']],type_ignores=[]),'<frozen filesystem helpers>','exec'),ns)
    before=json.loads((ENV/'original_environment_before.json').read_text())
    after={str(p):ns['tree_state'](p) for p in [ROOT/'.venv-cut3r',ROOT/'.venv']}
    check('old venvs still unchanged excluding bytecode',before==after)
    report['status']='PASS_IMPORT_ONLY_NO_MODEL'
except BaseException as exc:
    report['status']='FAILED_IMPORT_ONLY'
    report['failure']={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
finally:
    report['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    report['elapsed_seconds']=time.perf_counter()-START
    report['script_sha256']=sha(__file__)
    report['pass_checks']=sum(x['pass'] for x in report['checks'])
    (ENV/'import_smoke_v2.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'pass_checks':report['pass_checks'],'module_count':len(report['modules']),
                      'elapsed_seconds':report['elapsed_seconds'],'failure':report.get('failure')}))
