"""Delivery-only check: hashes, original bytes, link-only prose rewriting."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
from urllib.parse import unquote

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
PACK = Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/S34_固定旧地图三条件与真实照片_2026-09-07')
DEST = ROOT / 'work/S34_root_preparation/snapshot_review.json'
assert not DEST.exists()
started = datetime.now(timezone.utc).isoformat()
sha = lambda b: hashlib.sha256(b).hexdigest()
manifest_bytes = (PACK / 'manifest.json').read_bytes()
manifest = json.loads(manifest_bytes)
assert sha(manifest_bytes) == 'f007ad26376a9a9d5551a12e5cc4fb2a47ccccc9d1e1c971cde1fe922804b104'
pattern = re.compile(r'(!?\[[^\]\n]*\]\()(<[^>\n]+>|[^)\n]+)(\))')
normalize = lambda s: pattern.sub(lambda m: m[1] + 'LINK_TARGET' + m[3], s)
links = []
rewritten = 0
photos = []
payload_bytes = 0
for item in manifest['payloads']:
    path = PACK / item['relative_path']
    content = path.read_bytes()
    assert sha(content) == item['destination_sha256'], str(path)
    assert len(content) == item['bytes'], str(path)
    payload_bytes += len(content)
    source = item.get('source_path')
    if source:
        source_bytes = Path(source).read_bytes()
        assert sha(source_bytes) == item['source_sha256'], source
        if item['kind'].startswith('source_exact_copy'):
            assert content == source_bytes, str(path)
        elif item['kind'] == 'markdown_absolute_links_with_original_preserved':
            assert normalize(content.decode()) == normalize(source_bytes.decode()), str(path)
            rewritten += 1
    if path.suffix == '.md':
        for match in pattern.finditer(content.decode()):
            raw = match[2].strip('<>')
            if re.match(r'^[a-zA-Z]+://', raw) or raw.startswith('#'):
                continue
            target = Path(unquote(raw.split('#')[0]))
            if not target.is_absolute():
                target = path.parent / target
            assert target.exists(), (str(path), str(target))
            links.append({'from': str(path), 'target': str(target)})
    if path.parent.name == '真实照片':
        assert item['kind'] == 'source_exact_copy'
        photos.append(item['relative_path'])
assert len(manifest['payloads']) == 219
assert len(photos) == 8
assert rewritten == 13
assert payload_bytes == manifest['payload_bytes']
assert (PACK/'证据/docs/S34_RESULTS.md.source.txt').read_bytes() == (ROOT/'docs/S34_RESULTS.md').read_bytes()
assert len([p for p in PACK.rglob('*') if p.is_file()]) == 220
result = dict(status='PASS_ROOT_DELIVERY_REVIEW', started_utc=started,
              completed_utc=datetime.now(timezone.utc).isoformat(),
              manifest_sha256=sha(manifest_bytes), payloads=219, total_files=220,
              payload_bytes=payload_bytes, original_photo_count=len(photos),
              link_only_markdown_rewrites=rewritten, local_link_count=len(links),
              links=links, photos=photos,
              scientific_array_decodes=0, RGB_pixel_decodes=0, sensor_GT_reads=0,
              new_models=0, new_GA=0, new_scoring=0,
              limits=['Large linked arrays are not copied or rehashed in this delivery audit.',
                      'PNG visual review and final claim review are separate ROOT receipts; immutable snapshot is not altered.'])
DEST.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('links','photos')}, ensure_ascii=False))
