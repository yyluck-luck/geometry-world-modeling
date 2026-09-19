"""Source-only snapshot and comparison; does not import source or read data/weights."""
import ast
import datetime
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
VMEM = Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem')
STANDALONE = VMEM.parent / 'cut3r-local'
PREFLIGHT = HERE.parent / 'S17_cpu_preflight'
DEST = HERE / 'isolated_vmem_source'
CODE_SUFFIXES = {'.py', '.cpp', '.cu', '.c', '.h', '.hpp', '.sh', '.yaml', '.yml'}

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def git(path, *args):
    return subprocess.check_output(['/usr/bin/git', '-C', str(path), *args], text=True).strip()

assert not DEST.exists()
assert git(VMEM, 'rev-parse', 'HEAD') == '39291e4f272f6b4f270691d930926ab5930f942e'
assert git(STANDALONE, 'rev-parse', 'HEAD') == '8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf'
assert not git(VMEM, 'status', '--porcelain', '--untracked-files=no')
assert not git(STANDALONE, 'status', '--porcelain', '--untracked-files=no')
report = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'vmem_root': str(VMEM), 'vmem_commit': git(VMEM, 'rev-parse', 'HEAD'),
          'standalone_root': str(STANDALONE), 'standalone_commit': git(STANDALONE, 'rev-parse', 'HEAD'),
          'selection': 'all tracked .py/.cpp/.cu/.c/.h/.hpp/.sh/.yaml/.yml plus LICENSE*, README.md and requirements*.txt',
          'source_files': {}, 'patches': [], 'embedded_src_comparison': [],
          'data_weight_image_reads': 0, 'full_model_imports': 0}
for name in git(VMEM, 'ls-files').splitlines():
    src = VMEM / name
    selected = src.suffix in CODE_SUFFIXES or src.name.startswith('LICENSE') or src.name == 'README.md' or (src.name.startswith('requirements') and src.suffix == '.txt')
    if not selected or not src.is_file():
        continue
    assert not src.is_symlink()
    dst = DEST / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
    report['source_files'][name] = {'bytes': src.stat().st_size, 'sha256': sha(src)}
for src in sorted((VMEM / 'extern/CUT3R/src').rglob('*.py')):
    name = str(src.relative_to(VMEM / 'extern/CUT3R'))
    other = STANDALONE / name
    report['embedded_src_comparison'].append({'path': name, 'embedded_sha256': sha(src),
        'standalone_sha256': sha(other) if other.exists() else None,
        'equal': other.exists() and src.read_bytes() == other.read_bytes()})
patch = []
for name in ['extern/CUT3R/src/croco/models/pos_embed.py', 'extern/CUT3R/src/croco/models/rope_cpu.py']:
    src = PREFLIGHT / 'patched' / name
    dst = DEST / name
    original = dst.read_text() if dst.exists() else ''
    if original:
        assert sha(dst) == sha(PREFLIGHT / 'original' / name)
    changed = src.read_text()
    dst.write_text(changed)
    patch.extend(difflib.unified_diff(original.splitlines(True), changed.splitlines(True),
                                     fromfile='a/' + name if original else '/dev/null', tofile='b/' + name))
    report['patches'].append({'path': name, 'sha256': sha(dst), 'source_preflight': str(src)})
(HERE / 'signed_rope_only.patch').write_text(''.join(patch))
report['signed_rope_patch_sha256'] = sha(HERE / 'signed_rope_only.patch')
name = 'extern/CUT3R/src/dust3r/model.py'
dst = DEST / name
original = dst.read_text()
assert original.count('map_location="cpu", weights_only=False') == 1
changed = original.replace('map_location="cpu", weights_only=False', 'map_location="cpu", weights_only=True', 1)
dst.write_text(changed)
patch.extend(difflib.unified_diff(original.splitlines(True), changed.splitlines(True), fromfile='a/' + name, tofile='b/' + name))
report['patches'].append({'path': name, 'sha256': sha(dst), 'reason': 'root-requested explicit weights_only=True; runner must use frozen approved S17B safe_globals'})
(HERE / 'cpu_geometry_candidate.patch').write_text(''.join(patch))
report['patch_sha256'] = sha(HERE / 'cpu_geometry_candidate.patch')
wrapper = DEST / 'extern/CUT3R/surfel_inference.py'
tree = ast.parse(wrapper.read_text())
report['original_entrypoints_unchanged'] = {}
for n in tree.body:
    if isinstance(n, ast.FunctionDef) and n.name in ['run_inference_from_pil', 'prepare_input_from_pil', 'prepare_output']:
        report['original_entrypoints_unchanged'][n.name] = hashlib.sha256(ast.dump(n, include_attributes=False).encode()).hexdigest()
for name in report['source_files']:
    assert sha(VMEM / name) == report['source_files'][name]['sha256']
assert not git(VMEM, 'status', '--porcelain', '--untracked-files=no')
report['source_count'] = len(report['source_files'])
report['source_bytes'] = sum(x['bytes'] for x in report['source_files'].values())
report['comparison_count'] = len(report['embedded_src_comparison'])
report['comparison_equal'] = sum(x['equal'] for x in report['embedded_src_comparison'])
(HERE / 'source_plan.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k:report[k] for k in ['source_count','source_bytes','comparison_count','comparison_equal','patch_sha256']}))
