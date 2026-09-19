"""Small ICL archive qualification sample; not a model or GRC experiment."""
import io, json, tarfile, hashlib, sys
from PIL import Image

archive = sys.argv[1]
ids = [1, 2, 3, 750, 1508]
out = {
    "archive": archive,
    "sample_ids": ids,
    "data_access": True,
    "future_gt_used_for_selection": False,
    "model_execution": False,
    "samples": [],
    "errors": [],
}
with tarfile.open(archive, "r:gz") as tf:
    names = set(tf.getnames())
    for i in ids:
        row = {"id": i}
        for kind in ("rgb", "depth"):
            name = f"{kind}/{i}.png"
            if name not in names:
                row[kind] = {"status": "MISSING"}
                continue
            raw = tf.extractfile(name).read()
            im = Image.open(io.BytesIO(raw))
            im.load()
            row[kind] = {
                "status": "OK",
                "format": im.format,
                "size": list(im.size),
                "mode": im.mode,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
            if kind == "depth":
                px = list(im.getdata())
                row[kind].update({
                    "min": int(min(px)),
                    "max": int(max(px)),
                    "zero_count": int(sum(v == 0 for v in px)),
                    "nonzero_count": int(sum(v != 0 for v in px)),
                })
        out["samples"].append(row)
print(json.dumps(out, ensure_ascii=False, indent=2))
