#!/usr/bin/env python3
"""Reuse a verified cached ZIP header and one HTTPS connection for final RGBs."""
import argparse
import http.client
import json
from pathlib import Path
import traceback
from urllib.parse import urlsplit
from fetch_s15_zip_members import now,sha,save,require,parse_header,unpack_member


def main():
    p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--contract-sha256',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    out=Path(a.output);require(not out.exists(),'fresh output');out.mkdir(parents=True)
    r=dict(schema='s15-range-member-receipt-v1',started_utc=now(),status='RUNNING',requests=[],members=[],body_bytes=0,image_array_decodes=0,model_calls=0,transport='single standard-library HTTPSConnection; cached first header; no automatic retries')
    conn=None
    try:
        raw=Path(a.contract).read_bytes();require(sha(raw)==a.contract_sha256,'contract SHA');c=json.loads(raw)
        require(sha(Path(__file__).read_bytes())==c['fetcher_sha256'],'fetcher SHA')
        require(sha(Path(__file__).with_name('fetch_s15_zip_members.py').read_bytes())==c['zip_parser_sha256'],'parser SHA')
        require(len(c['members'])==len(set(c['members']))==2 and c['max_requests']==3,'exact bounded remainder')
        iv=Path(c['inventory_path']).read_bytes();require(sha(iv)==c['inventory_sha256'],'inventory SHA');inv={e['name']:e for e in json.loads(iv)['entries']}
        cached=Path(c['cached_header_path']).read_bytes();require(sha(cached)==c['cached_header_sha256'],'cached header SHA')
        fr=Path(c['cached_header_receipt']).read_bytes();require(sha(fr)==c['cached_header_receipt_sha256'],'cached response receipt')
        old=json.loads(fr)['requests'][0];entry0=inv[c['members'][0]]
        require(old['status']==206 and old['bytes']==30 and old['sha256']==sha(cached) and old['requested_range']==f"bytes={entry0['local_header_offset']}-{entry0['local_header_offset']+29}",'cached requested header identity')
        require(old['headers']['ETag']==c['etag'] and old['headers']['Last-Modified']==c['last_modified'],'cached same source')
        u=urlsplit(c['url']);require(u.scheme=='https' and not u.query and not u.fragment,'exact HTTPS source')
        conn=http.client.HTTPSConnection(u.hostname,port=u.port or 443,timeout=25)
        r.update(contract_path=str(Path(a.contract).resolve()),contract_sha256=a.contract_sha256,url=c['url'],archive_total_bytes=c['archive_total_bytes'],cached_header_sha256=sha(cached))
        def fetch(start,length):
            require(len(r['requests'])<3 and r['body_bytes']+length+1<=c['max_response_bytes'],'budget')
            end=start+length-1;require(0<=start<=end<c['central_directory_offset'],'range')
            item=dict(started_utc=now(),requested_range=f'bytes={start}-{end}');r['requests'].append(item);save(out/'receipt.json',r)
            conn.request('GET',u.path,headers={'Range':item['requested_range'],'Accept-Encoding':'identity','If-Match':c['etag'],'If-Range':c['etag'],'Connection':'keep-alive'})
            with conn.getresponse() as response:
                item.update(status=response.status,final_url=c['url'],headers={k:response.getheader(k) for k in ('Content-Range','Content-Length','Content-Encoding','ETag','Last-Modified')})
                require(response.status==206,'exact206; no redirect/body read')
                require(response.getheader('Content-Range')==f"bytes {start}-{end}/{c['archive_total_bytes']}" and response.getheader('ETag')==c['etag'] and response.getheader('Last-Modified')==c['last_modified'],'source/range identity')
                require(response.getheader('Content-Encoding') in (None,'identity') and response.getheader('Content-Length') in (None,str(length)),'encoding/length')
                data=response.read(length+1);r['body_bytes']+=len(data);item.update(ended_utc=now(),bytes=len(data),sha256=sha(data));require(len(data)==length,'body length')
            save(out/'receipt.json',r);return data
        for i,name in enumerate(c['members']):
            e=inv[name];require(e['uncompressed_bytes']<=c['max_member_uncompressed_bytes'],'member budget')
            header=cached if i==0 else fetch(e['local_header_offset'],30)
            _,nlen,xlen=parse_header(header,e);rest=fetch(e['local_header_offset']+30,nlen+xlen+e['compressed_bytes'])
            data=unpack_member(header,rest,e,c['max_member_uncompressed_bytes']);path=out/'members'/name;path.parent.mkdir(parents=True,exist_ok=True);require(not path.exists(),'fresh member');path.write_bytes(data)
            r['members'].append(dict(**e,path=str(path.resolve()),bytes=len(data),sha256=sha(data),zip_crc32_verified=True));save(out/'receipt.json',r)
        r['status']='PASS'
    except Exception as e:r.update(status='FAIL',error=repr(e),traceback=traceback.format_exc())
    finally:
        if conn:conn.close()
        r['ended_utc']=now();save(out/'receipt.json',r)
    print(json.dumps(dict(status=r['status'],members=len(r['members']),body_bytes=r['body_bytes'])));return int(r['status']!='PASS')

if __name__=='__main__':raise SystemExit(main())
