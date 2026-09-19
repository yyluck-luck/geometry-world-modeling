#!/usr/bin/env python3
"""Save primary-source snapshots for a bounded literature review, not experiments."""
from pathlib import Path
from datetime import datetime, timezone
import urllib.request, hashlib, json, concurrent.futures
BASE = Path(__file__).resolve().parent
SOURCES = {
    "vmem_v3.html": "https://arxiv.org/html/2506.18903v3",
    "covrag_v1.html": "https://arxiv.org/html/2606.02479v1",
    "i3dm_v2.html": "https://arxiv.org/html/2603.23413v2",
    "nerf_director_v1.html": "https://arxiv.org/html/2406.08839v1",
    "ltt_v4.html": "https://arxiv.org/html/2110.01052v4",
    "layerrecall_v1.html": "https://arxiv.org/html/2608.28460v1",
    "pixelwise_view_selection_author.pdf": "https://demuc.de/papers/schoenberger2016mvs.pdf"
}
def now(): return datetime.now(timezone.utc).isoformat()
def fetch(item):
    name, url = item
    record = {"name": name, "url": url, "started_utc": now()}
    path = BASE / name
    try:
        if path.exists(): raise FileExistsError(str(path))
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Research source archival"}), timeout=25) as response:
            blob = response.read()
            record.update(final_url=response.url, status_code=response.status, content_type=response.headers.get("Content-Type"))
        path.write_bytes(blob)
        record.update(status="saved", bytes=len(blob), sha256=hashlib.sha256(blob).hexdigest())
    except Exception as exc:
        record.update(status="failed", error=repr(exc))
    record["completed_utc"] = now()
    return record
if __name__ == "__main__":
    receipt_path = BASE / "source_download_receipt.json"
    if receipt_path.exists(): raise FileExistsError(str(receipt_path))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(fetch, SOURCES.items()))
    receipt_path.write_text(json.dumps({"schema": "s14-primary-source-downloads-v1", "records": records}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(records, ensure_ascii=False, indent=2))

