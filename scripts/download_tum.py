#!/usr/bin/env python3
"""Resumable bounded-concurrency download from the official TUM server."""
import concurrent.futures
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tarfile
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'data/tum'
URL='https://webshare.cvg.cit.tum.de/g/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_xyz.tgz'
SIZE=448204271
CHUNK=4*1024*1024
ARCHIVE=DEST/'rgbd_dataset_freiburg1_xyz.tgz'

def now(): return datetime.now(timezone.utc).isoformat()
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''): h.update(b)
    return h.hexdigest()

def main():
    DEST.mkdir(parents=True,exist_ok=True)
    chunks=DEST/'chunks'
    chunks.mkdir(exist_ok=True)
    meta=dict(started_utc=now(),source_url=URL,expected_size=SIZE,chunk_bytes=CHUNK,workers=6)
    # Reuse only fully received prefix chunks from the failed initial transfer.
    prefix=DEST/'rgbd_dataset_freiburg1_xyz.tgz.part'
    if prefix.exists():
        with prefix.open('rb') as f:
            for i in range(prefix.stat().st_size//CHUNK):
                payload=f.read(CHUNK)
                p=chunks/f'{i:04}.part'
                if not p.exists(): p.write_bytes(payload)
    def get(i):
        start,end=i*CHUNK,min(SIZE,(i+1)*CHUNK)-1
        p=chunks/f'{i:04}.part'
        if p.exists() and p.stat().st_size==end-start+1:
            return dict(index=i,bytes=p.stat().st_size,sha256=sha(p),reused=True)
        for attempt in range(6):
            try:
                req=urllib.request.Request(URL,headers={'Range':f'bytes={start}-{end}','Accept-Encoding':'identity'})
                with urllib.request.urlopen(req,timeout=45) as r:
                    expected=f'bytes {start}-{end}/{SIZE}'
                    if r.status!=206 or r.headers.get('Content-Range')!=expected:
                        raise ValueError(f'Unexpected range response {r.status} {r.headers.get("Content-Range")}')
                    payload=r.read(end-start+2)
                    if len(payload)!=end-start+1: raise ValueError('Incorrect payload length')
                    headers=dict(r.headers)
                temp=p.with_suffix('.tmp')
                temp.write_bytes(payload)
                temp.replace(p)
                return dict(index=i,bytes=len(payload),sha256=sha(p),reused=False,headers=headers)
            except Exception as e:
                print(json.dumps(dict(event='retry',chunk=i,attempt=attempt,error=str(e),utc=now())),flush=True)
                if attempt==5: raise
                time.sleep(min(2**attempt,10))
    records=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        futures=[ex.submit(get,i) for i in range((SIZE+CHUNK-1)//CHUNK)]
        for future in concurrent.futures.as_completed(futures):
            records.append(future.result())
            if len(records)%10==0:
                print(json.dumps(dict(event='progress',chunks_complete=len(records),chunks_total=len(futures),utc=now())),flush=True)
    assembled=DEST/'assembled.tmp'
    with assembled.open('wb') as f:
        for i in range((SIZE+CHUNK-1)//CHUNK):
            f.write((chunks/f'{i:04}.part').read_bytes())
    assert assembled.stat().st_size==SIZE
    meta.update(download_completed_utc=now(),sha256=sha(assembled),chunks=sorted(records,key=lambda x:x['index']))
    # Reading the entire gzip/tar validates its stream; extraction excludes unsafe members.
    with tarfile.open(assembled,'r:gz') as tar:
        members=tar.getmembers()
        meta['tar_members']=len(members)
        tar.extractall(DEST,filter='data')
    assembled.replace(ARCHIVE)
    meta['extraction_completed_utc']=now()
    (DEST/'download_manifest.json').write_text(json.dumps(meta,indent=2))
    print(json.dumps({k:v for k,v in meta.items() if k!='chunks'}),flush=True)

if __name__=='__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    main()
