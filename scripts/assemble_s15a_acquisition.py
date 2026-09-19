#!/usr/bin/env python3
"""Validate and join 11 + 4 + 3 + 0 + 2 members across preserved TLS failures."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    paths=[ROOT/p for p in ['data/bonn_s15a_history/receipt.json','data/bonn_s15a_history_resume1/receipt.json','data/bonn_s15a_history_resume2/receipt.json','data/bonn_s15a_history_curl/receipt.json','data/bonn_s15a_history_persistent/receipt.json']]
    receipts=[json.loads(p.read_text()) for p in paths]
    first,middle,third,curl,last=receipts
    assert first['status']=='FAIL' and 'SSLEOFError' in first['error'] and len(first['members'])==11
    assert middle['status']=='FAIL' and 'SSLEOFError' in middle['error'] and len(middle['members'])==4
    assert third['status']=='FAIL' and 'SSLEOFError' in third['error'] and len(third['members'])==3
    assert curl['status']=='FAIL' and len(curl['members'])==0 and 'SSL_ERROR_SYSCALL' in curl['requests'][-1]['stderr']
    assert last['status']=='PASS' and len(last['members'])==2
    original=json.loads((ROOT/'work/S15A_access/history_contract.json').read_text())
    recovery=json.loads((ROOT/'work/S15A_access/history_resume_contract.json').read_text())
    assert recovery['recovery_receipt_sha256']==sha(paths[0])
    assert original['members'][:11]==[x['name'] for x in first['members']]
    recovery2=json.loads((ROOT/'work/S15A_access/history_resume2_contract.json').read_text())
    assert recovery['members'][:4]==original['members'][11:15]==[x['name'] for x in middle['members']]
    assert recovery2['members'][:3]==original['members'][15:18]==[x['name'] for x in third['members']]
    assert all(recovery2['prior_receipt_sha256'][str(p)]==sha(p) for p in paths[:2])
    recovery3=json.loads((ROOT/'work/S15A_access/history_curl_contract_v2.json').read_text())
    assert recovery3['members']==original['members'][18:]==[x['name'] for x in last['members']]
    assert all(recovery3['prior_receipt_sha256'][str(p)]==sha(p) for p in paths[:3])
    recovery4=json.loads((ROOT/'work/S15A_access/history_persistent_contract.json').read_text())
    assert recovery4['members']==recovery3['members']
    assert recovery4['cached_header_receipt_sha256']==sha(paths[3]) and recovery4['cached_header_sha256']==sha(recovery4['cached_header_path'])
    expected_contracts=['history_contract.json','history_resume_contract.json','history_resume2_contract.json','history_curl_contract_v2.json','history_persistent_contract.json']
    for rec,contract,contract_name in zip(receipts,(original,recovery,recovery2,recovery3,recovery4),expected_contracts):
        assert Path(rec['contract_path']).resolve()==ROOT/'work/S15A_access'/contract_name
        assert rec['contract_sha256']==sha(rec['contract_path'])
        assert rec['url']==original['url'] and rec['archive_total_bytes']==original['archive_total_bytes']
        assert rec['image_array_decodes']==0 and rec['model_calls']==0
        for item in rec['requests']:
            if 'status' not in item:
                assert rec is not last and item is rec['requests'][-1]
                continue
            assert item['status']==206 and item['headers']['ETag']==original['etag'] and item['headers']['Last-Modified']==original['last_modified']
            assert item['final_url']==original['url']
    members=first['members']+middle['members']+third['members']+curl['members']+last['members']
    assert len({m['name'] for m in members})==len(members)==20
    for m in members:
        assert sha(m['path'])==m['sha256'] and Path(m['path']).stat().st_size==m['bytes'] and m['zip_crc32_verified']
    requests=sum((x['requests'] for x in receipts),[])
    body=sum(x['body_bytes'] for x in receipts)
    assert len(requests)<=46 and body<=20*1024**2
    out=ROOT/'data/bonn_s15a_history_combined';assert not out.exists();out.mkdir()
    result=dict(schema='s15-range-member-combined-receipt-v1',status='PASS',started_utc=first['started_utc'],ended_utc=last['ended_utc'],assembled_utc=datetime.now(timezone.utc).isoformat(),url=original['url'],archive_total_bytes=original['archive_total_bytes'],source_receipt_sha256={str(p):sha(p) for p in paths},source_sha256=sha(__file__),requests=requests,members=members,body_bytes=body,image_array_decodes=0,model_calls=0,interpretation='20 original frozen RGB files assembled after bounded TLS recovery; original failure remains immutable; no sample was changed')
    (out/'receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status='PASS',members=20,requests=len(requests),body_bytes=body,receipt_sha256=sha(out/'receipt.json'))))

if __name__=='__main__':main()
