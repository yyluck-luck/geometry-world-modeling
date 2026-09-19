"""Transport-only continuation after frozen v1 per-wheel timeouts. No model/data."""
from pathlib import Path
import ast, datetime, hashlib, json, os, shutil, subprocess, sys, time, traceback
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
ENV = ROOT / 'work/S17C_environment'
WHEELS = ENV / 'wheelhouse'
OVERLAY = ENV / 'site-packages'
UTC = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
# Reuse only pure filesystem snapshot functions from the frozen installer source.
tree = ast.parse((HERE / 'install_overlay.py').read_text())
ns = dict(Path=Path, hashlib=hashlib, os=os, json=json)
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ['sha','tree_state']], type_ignores=[]), '<frozen filesystem helpers>', 'exec'), ns)
sha, tree_state = ns['sha'], ns['tree_state']
prior = json.loads((ENV / 'install_receipt.json').read_text())
assert prior['status'] == 'FAILED' and not OVERLAY.exists()
assert not (ENV / 'continuation_receipt.json').exists()
base = json.loads((ENV / 'access_contract.json').read_text())
assert sha(HERE / 'install_overlay.py') == base['script_sha256']
plan = base['plan']
report = {'status': 'RUNNING', 'started_utc': UTC(), 'previous_receipt_sha256': sha(ENV / 'install_receipt.json'),
          'previous_attempts': len(prior['requests']), 'prior_response_bytes': prior['network_response_bytes'],
          'new_requests': [], 'wheels': [], 'package_installs': 0, 'model_instantiations': 0,
          'real_image_reads': 0, 'weight_reads': 0}
contract = {'schema': 's17c-overlay-transport-continuation-v2', 'created_utc': UTC(),
            'reason': 'original 25-second full-wheel limit caused transport timeouts; preserve partial bytes and SHA-verifiable fixed artifacts',
            'script_sha256': sha(__file__), 'previous_contract_sha256': sha(ENV / 'access_contract.json'),
            'previous_receipt_sha256': report['previous_receipt_sha256'],
            'max_total_response_bytes': 104857600, 'max_total_attempts': 60,
            'max_new_attempts_per_wheel': 3, 'max_total_seconds_from_first_stage': 600,
            'single_request_seconds': 150, 'require_http_206_on_resume': True,
            'versions_urls_hashes_unchanged': True}
(ENV / 'continuation_contract.json').write_text(json.dumps(contract, indent=2)+'\n')
first_start = datetime.datetime.fromisoformat(prior['started_utc'])
def elapsed():
    return (datetime.datetime.now(datetime.timezone.utc) - first_start).total_seconds()
def save(name, obj):
    (ENV / name).write_text(json.dumps(obj, indent=2)+'\n')
try:
    for w in plan['wheels']:
        dest = WHEELS / w['filename']
        if dest.exists():
            assert dest.stat().st_size == w['bytes'] and sha(dest) == w['sha256']
            report['wheels'].append({'filename': w['filename'], 'reused_completed': True, 'sha256': w['sha256']})
            continue
        part = WHEELS / (w['filename'] + '.resume.part')
        candidates = list(WHEELS.glob(w['filename'] + '.attempt*.part'))
        if candidates:
            longest = max(candidates, key=lambda p:p.stat().st_size)
            shutil.copyfile(longest, part)
        for attempt in range(1,4):
            assert elapsed() < 600
            assert report['previous_attempts'] + len(report['new_requests']) < 60
            offset = part.stat().st_size if part.exists() else 0
            if offset == w['bytes']:
                assert sha(part) == w['sha256']
                part.rename(dest)
                break
            timeout = min(150, max(1,int(600-elapsed())))
            args=['curl','--max-time',str(timeout),'--connect-timeout','12','--max-filesize',str(w['bytes']),
                  '--silent','--show-error','--output',str(part),'--write-out','%{http_code}|%{size_download}|%{time_total}']
            if offset:
                args += ['--continue-at',str(offset)]
            args += [w['url']]
            start=time.perf_counter()
            p=subprocess.run(args,capture_output=True,text=True)
            fields=p.stdout.strip().split('|')
            count=int(float(fields[1])) if len(fields)==3 else 0
            r={'filename':w['filename'],'attempt':attempt,'offset':offset,'ended_utc':UTC(),
               'curl_exit_code':p.returncode,'http_code':fields[0],'response_bytes':count,
               'elapsed_seconds':time.perf_counter()-start,'stderr':p.stderr}
            report['new_requests'].append(r)
            report['total_response_bytes']=report['prior_response_bytes']+sum(x['response_bytes'] for x in report['new_requests'])
            save('continuation_progress.json',report)
            assert report['total_response_bytes']<=104857600 and elapsed()<600
            if p.returncode:
                if p.returncode in (18,28,35,52,55,56) and attempt<3:continue
                raise RuntimeError('Transport failed: '+w['filename'])
            assert fields[0]==('206' if offset else '200'), 'Unexpected HTTP code'
            assert part.stat().st_size==w['bytes'] and sha(part)==w['sha256'], 'Artifact size/hash failure'
            part.rename(dest)
            break
        assert dest.exists()
        report['wheels'].append({'filename':w['filename'],'reused_completed':False,'sha256':sha(dest),'bytes':dest.stat().st_size})
    assert len(report['wheels'])==22
    install_env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PIP_DISABLE_PIP_VERSION_CHECK='1',PIP_NO_INDEX='1')
    args=[sys.executable,'-m','pip','install','--no-index','--no-deps','--no-compile','--require-hashes',
          '--only-binary=:all:','--find-links',str(WHEELS),'--target',str(OVERLAY),'-r',str(HERE/'overlay_requirements.txt')]
    p=subprocess.run(args,env=install_env,capture_output=True,text=True,timeout=max(1,int(600-elapsed())))
    (ENV/'pip_install.stdout.txt').write_text(p.stdout)
    (ENV/'pip_install.stderr.txt').write_text(p.stderr)
    report['install']={'command':args,'exit_code':p.returncode,'ended_utc':UTC()}
    assert p.returncode==0,'Overlay pip install failed'
    report['package_installs']=22
    before=json.loads((ENV/'original_environment_before.json').read_text())
    after={str(p):tree_state(p) for p in [ROOT/'.venv-cut3r',ROOT/'.venv']}
    save('original_environment_after.json',after)
    assert before==after,'Original non-bytecode venv content/metadata changed'
    report['original_environments_unchanged']=True
    report['status']='OVERLAY_INSTALLED_PENDING_IMPORT_SMOKE'
except BaseException as exc:
    report['status']='FAILED'
    report['failure']={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
finally:
    report['ended_utc']=UTC()
    report['elapsed_seconds_from_first_stage']=elapsed()
    save('continuation_receipt.json',report)
    print(json.dumps({'status':report['status'],'wheel_count':len(report['wheels']),
                      'total_response_bytes':report.get('total_response_bytes'),
                      'elapsed_seconds_from_first_stage':elapsed(),'failure':report.get('failure')}))
