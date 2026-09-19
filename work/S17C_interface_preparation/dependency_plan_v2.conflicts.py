"""Read PyPI metadata and existing distribution metadata; no package installs.

This is a candidate dependency closure, not pip resolution or an import test.
Existing versions are retained and every active incoming version constraint is
checked. Missing dependencies select the currently published stable version.
Only core extras='' dependencies on this host are included.
"""
from pathlib import Path
import datetime, hashlib, importlib.metadata as md, json, subprocess, time
from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(ROOT.parent / 'S17C_environment/site-packages'))
ENV = {**default_environment(), 'extra': ''}
SEEDS = {'viser': '1.1.0', 'scikit-learn': '1.9.0'}
LOG = {'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'status': 'RUNNING_METADATA_ONLY', 'http_requests': [], 'packages': {},
       'conflicts': [], 'environment': ENV, 'package_installs': 0,
       'earlier_transport_failure': {'method': 'urllib.request', 'url': 'https://pypi.org/pypi/evo/1.37.1/json',
                                     'type': 'URLError wrapping SSLEOFError', 'downloaded_bytes': 0}}
pending = [(k, f'{k}=={v}', 'requested seed') for k, v in SEEDS.items()]

def remote(name):
    filename = f'{name}.pypi.json'
    output = ROOT / filename
    url = f'https://pypi.org/pypi/{name}/json'
    if not output.exists():
        assert len(LOG['http_requests']) < 35, 'metadata request budget'
        start = time.perf_counter()
        p = subprocess.run(['curl', '--max-time', '20', '--retry', '2', '--retry-delay', '1', '--retry-all-errors', '--max-filesize', '8388608', '--silent', '--show-error', '--fail', url, '-o', str(output)], capture_output=True, text=True)
        LOG['http_requests'].append({'url': url, 'exit_code': p.returncode, 'elapsed_seconds': time.perf_counter()-start, 'stderr': p.stderr})
        if p.returncode:
            raise RuntimeError('metadata HTTP failed: ' + name)
    data = output.read_bytes()
    obj = json.loads(data)
    return obj['info'], {'url': url, 'path': str(output), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

try:
    while pending:
        name, requirement_text, parent = pending.pop(0)
        name = canonicalize_name(name)
        req = Requirement(requirement_text)
        if name in LOG['packages']:
            info = LOG['packages'][name]
        else:
            if name not in SEEDS:
                try:
                    local = md.distribution(name)
                except md.PackageNotFoundError:
                    local = None
            else:
                local = None
            if local:
                info = {'name': name, 'version': local.version, 'source': 'existing distribution metadata',
                        'requires_dist': local.requires or [], 'metadata_path': str(local._path), 'incoming': []}
            else:
                obj, receipt = remote(name)
                info = {'name': name, 'version': obj['version'], 'source': 'PyPI metadata only',
                        'requires_dist': obj.get('requires_dist') or [], 'requires_python': obj.get('requires_python'),
                        'metadata_receipt': receipt, 'incoming': []}
            LOG['packages'][name] = info
            info['active_requirements'] = []
            for text in info['requires_dist']:
                child = Requirement(text)
                if child.marker is None or child.marker.evaluate(ENV):
                    assert not child.extras, 'explicit extras need additional closure: ' + text
                    info['active_requirements'].append(text)
                    pending.append((child.name, text, name))
        info['incoming'].append({'parent': parent, 'requirement': requirement_text})
        if req.specifier and not req.specifier.contains(info['version']):
            LOG['conflicts'].append({'name': name, 'selected': info['version'], 'requirement': requirement_text, 'parent': parent})
    LOG['status'] = 'CANDIDATE_CLOSURE_CONSTRAINTS_PASS' if not LOG['conflicts'] else 'CONSTRAINT_CONFLICT'
except Exception as exc:
    LOG['status'] = 'FAILED_METADATA_PLAN'
    LOG['failure'] = {'type': type(exc).__name__, 'message': str(exc)}
finally:
    LOG['ended_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    LOG['script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (ROOT / 'dependency_plan_v2.json').write_text(json.dumps(LOG, indent=2) + '\n')
    print(json.dumps({'status': LOG['status'], 'package_count': len(LOG['packages']),
                      'conflicts': LOG['conflicts'], 'failure': LOG.get('failure')}))
