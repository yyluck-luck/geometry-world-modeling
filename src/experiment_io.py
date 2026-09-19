"""Small shared utilities for immutable, timestamped local experiments."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import platform
from importlib.metadata import version
import zipfile
ROOT=Path(__file__).resolve().parents[1]

def utc_now(): return datetime.now(timezone.utc).isoformat()
def sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_json(path,value): Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False))

def begin_run(directory,protocol,config):
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=False)
    files=[p for folder in ('src','scripts','tests','configs') for p in (ROOT/folder).rglob('*')
           if p.is_file() and '__pycache__' not in p.parts]
    files += [ROOT/protocol,ROOT/'vendor/provenance.json',ROOT/'requirements-rgbd.txt',ROOT/'requirements-retrieval.txt']
    files += list((ROOT/'vendor/vmem_snapshot').rglob('*.py'))
    files += [ROOT/'vendor/VMEM_LICENSE']
    # Capture bytes once so an independent task cannot change a file between
    # hashing and archiving it. Imported experiment modules must stay frozen.
    snapshot={str(p.relative_to(ROOT)):p.read_bytes() for p in files}
    hashes={name:hashlib.sha256(payload).hexdigest() for name,payload in snapshot.items()}
    with zipfile.ZipFile(directory/'reproduction_source.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name,payload in snapshot.items(): z.writestr(name,payload)
    meta=dict(started_utc=utc_now(),protocol=protocol,config=config,source_sha256=hashes,
              python=platform.python_version(),machine=platform.machine(),system=platform.platform(),
              packages={name:version(name) for name in ('numpy','scipy','torch','Pillow','matplotlib')},
              numerical_precision='geometry float64; official renderer depth float32; official distance sort float32; CPU')
    write_json(directory/'run_metadata.json',meta)
    return meta

def complete_run(directory,meta,**extra):
    meta.update(completed_utc=utc_now(),**extra)
    write_json(Path(directory)/'run_metadata.json',meta)

def append_jsonl(path,record):
    with Path(path).open('a') as f: f.write(json.dumps(record,ensure_ascii=False,allow_nan=False)+'\n')
