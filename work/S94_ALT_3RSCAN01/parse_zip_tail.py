from pathlib import Path
import struct, json, hashlib, collections
p=Path(__file__).parent/'downloads/3RScan.v2.tail64k.bin'
b=p.read_bytes(); idx=b.rfind(b'PK\x05\x06')
if idx<0: raise SystemExit('EOCD_NOT_FOUND')
_,_,_,n1,n2,cdsz,cdo,comment=struct.unpack('<4s4H2LH',b[idx:idx+22]); pos=idx-cdsz; names=[]; entries=[]
while pos<idx:
    f=struct.unpack('<4s6H3L5H2L',b[pos:pos+46]); fn,extra,com=f[10:13]
    name=b[pos+46:pos+46+fn].decode('utf8','replace')
    crc,csz,usz,lh=f[7],f[8],f[9],f[16]
    names.append(name); entries.append({'name':name,'compressed_size':csz,'uncompressed_size':usz,'local_header_offset':lh})
    pos += 46+fn+extra+com
roots=sorted({x.split('/')[0] for x in names})
def category(x):
    return ('color' if '.color.' in x else 'depth' if '.depth.' in x else 'pose' if '.pose.' in x else 'info' if x.endswith('_info.txt') else 'mesh' if x.endswith('mesh.refined.v2.obj') else 'other')
out={'eocd_offset_in_tail':idx,'entry_count':n2,'central_directory_size':cdsz,'central_directory_offset':cdo,'roots':roots,'entries_per_root':{r:len([x for x in names if x.startswith(r+'/')]) for r in roots},'categories_per_root':{r:dict(collections.Counter(category(x) for x in names if x.startswith(r+'/'))) for r in roots},'info_entries':[e for e in entries if e['name'].endswith('_info.txt')],'sample_frame_entries':[e for e in entries if 'frame-000000.' in e['name']], 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(Path(__file__).parent/'receipts/zip_central_directory_summary.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
