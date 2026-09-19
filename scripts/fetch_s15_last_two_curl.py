#!/usr/bin/env python3
"""Final two original RGB members via bounded macOS curl, after urllib TLS EOF."""
import argparse
import json
from pathlib import Path
import subprocess
import traceback
from fetch_s15_zip_members import now,sha,save,require,parse_header,unpack_member


def main():
    p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--contract-sha256',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    out=Path(a.output);require(not out.exists(),'preserve prior results');out.mkdir(parents=True)
    r=dict(schema='s15-range-member-receipt-v1',started_utc=now(),status='RUNNING',requests=[],members=[],body_bytes=0,image_array_decodes=0,model_calls=0,transport='macOS curl 8.7.1 SecureTransport, no automatic retry')
    try:
        raw=Path(a.contract).read_bytes();require(sha(raw)==a.contract_sha256,'contract identity');c=json.loads(raw)
        require(sha(Path(__file__).read_bytes())==c['fetcher_sha256'],'curl adapter identity')
        require(sha(Path(__file__).with_name('fetch_s15_zip_members.py').read_bytes())==c['zip_parser_sha256'],'audited ZIP parser identity')
        require(len(c['members'])==len(set(c['members']))==2 and c['max_requests']==4,'final two original members only')
        invbytes=Path(c['inventory_path']).read_bytes();require(sha(invbytes)==c['inventory_sha256'],'inventory identity');inv={e['name']:e for e in json.loads(invbytes)['entries']}
        version=subprocess.check_output(['/usr/bin/curl','--version'],text=True);require(version.startswith('curl 8.7.1 '),'audited curl version supporting streaming max-filesize');r['curl_version']=version
        r.update(contract_path=str(Path(a.contract).resolve()),contract_sha256=a.contract_sha256,url=c['url'],archive_total_bytes=c['archive_total_bytes'])
        def fetch(start,length):
            require(len(r['requests'])<4 and r['body_bytes']+length+1<=c['max_response_bytes'],'budget')
            end=start+length-1;require(0<=start<=end<c['central_directory_offset'],'member range')
            i=len(r['requests']);head=out/f'range{i}_headers.txt';body=out/f'range{i}_body.bin'
            item=dict(started_utc=now(),requested_range=f'bytes={start}-{end}');r['requests'].append(item)
            command=['/usr/bin/curl','--disable','--silent','--show-error','--retry','0','--max-redirs','0','--proto','=https','--connect-timeout','10','--max-time','25','--max-filesize',str(length+1),'--range',f'{start}-{end}','--header','Accept-Encoding: identity','--header','If-Match: '+c['etag'],'--header','If-Range: '+c['etag'],'--dump-header',str(head),'--output',str(body),'--write-out','%{http_code} %{url_effective}',c['url']]
            result=subprocess.run(command,capture_output=True,text=True,timeout=30)
            size=body.stat().st_size if body.exists() else 0;r['body_bytes']+=size
            item.update(ended_utc=now(),returncode=result.returncode,bytes=size,stderr=result.stderr,write_out=result.stdout)
            save(out/'receipt.json',r)
            require(result.returncode==0 and size<=length+1,'curl transfer limit or transport error')
            blocks=[b for b in head.read_text().split('\n\n') if b.startswith('HTTP/')];require(blocks,'response headers')
            lines=blocks[-1].splitlines();status=int(lines[0].split()[1]);headers={k.lower():v.strip() for line in lines[1:] if ':' in line for k,v in [line.split(':',1)]}
            item.update(status=status,final_url=result.stdout.split(' ',1)[1],headers={k:headers.get(k.lower()) for k in ('Content-Range','Content-Length','Content-Encoding','ETag','Last-Modified')})
            require(status==206 and result.stdout=='206 '+c['url'],'precise range without redirect')
            require(headers.get('content-range')==f"bytes {start}-{end}/{c['archive_total_bytes']}" and headers.get('etag')==c['etag'] and headers.get('last-modified')==c['last_modified'],'same archive and exact range')
            require(headers.get('content-encoding') in (None,'identity'),'no response encoding')
            require(size==length and headers.get('content-length') in (None,str(length)),'exact body size')
            data=body.read_bytes();item['sha256']=sha(data);save(out/'receipt.json',r);return data
        for name in c['members']:
            entry=inv[name];require(entry['uncompressed_bytes']<=c['max_member_uncompressed_bytes'],'member budget')
            header=fetch(entry['local_header_offset'],30);_,nlen,xlen=parse_header(header,entry)
            rest=fetch(entry['local_header_offset']+30,nlen+xlen+entry['compressed_bytes'])
            data=unpack_member(header,rest,entry,c['max_member_uncompressed_bytes'])
            path=out/'members'/name;path.parent.mkdir(parents=True,exist_ok=True);require(not path.exists(),'fresh member');path.write_bytes(data)
            r['members'].append(dict(**entry,path=str(path.resolve()),bytes=len(data),sha256=sha(data),zip_crc32_verified=True));save(out/'receipt.json',r)
        r['status']='PASS'
    except Exception as e:r.update(status='FAIL',error=repr(e),traceback=traceback.format_exc())
    r['ended_utc']=now();save(out/'receipt.json',r);print(json.dumps(dict(status=r['status'],members=len(r['members']),body_bytes=r['body_bytes'])));return int(r['status']!='PASS')


if __name__=='__main__':raise SystemExit(main())
