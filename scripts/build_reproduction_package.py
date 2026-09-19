#!/usr/bin/env python3
"""Create a content-hashed snapshot of this research project without bulky inputs."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
KEEP_ROOT={'README.md','AGENTS.md','RESEARCH_MEMORY.md','RESEARCH_LOG.md','research_events.jsonl','.gitignore'}
KEEP_DIRS={'src','scripts','tests','configs','docs','vendor','results','reports'}
DROP_PARTS={'__pycache__','.pytest_cache','.DS_Store','.git','node_modules'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise ValueError('Use a fresh package filename; previous packages are preserved')
    payloads={}
    rewritten=[]
    for path in sorted(ROOT.rglob('*')):
        rel=path.relative_to(ROOT)
        if not path.is_file() or any(part in DROP_PARTS or part.startswith('.venv') for part in rel.parts):continue
        if path.suffix in ('.pyc','.part','.pth','.tgz'):continue
        keep=(len(rel.parts)==1 and (rel.name in KEEP_ROOT or rel.name.startswith('requirements')))
        keep |= rel.parts[0] in KEEP_DIRS
        # Only provenance/identity documents from raw data directories.
        keep |= rel.parts[0]=='data' and len(rel.parts)==3 and path.suffix=='.json' and rel.parts[1] in ('tum','cut3r')
        if not keep:continue
        data=path.read_bytes()
        if path.suffix=='.md':
            content=data.decode('utf-8')
            relative_root=os.path.relpath(ROOT,path.parent).replace(os.sep,'/')
            portable=content.replace(str(ROOT)+'/',relative_root+'/')
            if portable!=content:
                rewritten.append(str(rel))
                data=portable.encode('utf-8')
        if path.suffix=='.json':json.loads(data)
        payloads[str(rel)]=data
    manifest=dict(created_utc=datetime.now(timezone.utc).isoformat(),
        root_name='geometry-world-modeling',
        portable_markdown_files=rewritten,
        portability_note='Only Markdown copies normalize project-local absolute paths. Historical JSON provenance is retained verbatim. External models and raw data need separate setup.',
        excluded='Raw TUM archive/images, model checkpoint/chunks, virtual environments, official full clone and caches. Download manifests and source snapshots are retained.',
        evidence_note='Synthetic tests, measured RGB-D tests, learned-model inference and generated video are separate evidence levels. Consult completed metadata and the research memory.',
        files={name:dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest()) for name,data in payloads.items()})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    temporary=args.output.with_suffix(args.output.suffix+'.building')
    with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,data in payloads.items():z.writestr('geometry-world-modeling/'+name,data)
        z.writestr('geometry-world-modeling/PACKAGE_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    with zipfile.ZipFile(temporary) as z:
        if z.testzip() is not None:raise ValueError('ZIP integrity check failed')
        for name,entry in manifest['files'].items():
            if hashlib.sha256(z.read('geometry-world-modeling/'+name)).hexdigest()!=entry['sha256']:
                raise ValueError('Archived content hash mismatch')
    temporary.rename(args.output)
    receipt=dict(completed_utc=datetime.now(timezone.utc).isoformat(),archive=str(args.output.resolve()),
                 files=len(payloads),bytes=args.output.stat().st_size,sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),
                 zip_crc_and_all_file_hashes_verified=True)
    args.output.with_suffix('.verification.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt))


if __name__=='__main__':main()
