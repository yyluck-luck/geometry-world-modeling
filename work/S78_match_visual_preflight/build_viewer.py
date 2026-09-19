#!/usr/bin/env python3
"""Build a local, read-only image viewer; never modify or rematch source images.

Source preparation only: this script has not been run on the image inputs.
At a later reviewed run it reads four original PNG byte streams for identity
checks, creates anonymous symlinks, and writes HTML plus a separate mapping.
Opening the HTML is a distinct future image-viewing action. No rating UI exists.
"""

import argparse
import hashlib
import html
import json
import math
import os
from pathlib import Path
import struct
from datetime import datetime, timezone


SOURCE_IDS = (84, 210, 317, 536, 935, 1017)
# This fixed display permutation is not randomization or a scientific threshold.
DISPLAY_ARMS = (("C01", "B"), ("C02", "real"), ("C03", "A0"))
IMAGE_KEYS = {"B": "B_22", "real": "real22", "A0": "A0_22"}
FRAME_PX = 576
NEIGHBORHOOD_PX = 64
LOCAL_ZOOM = 2


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_new(path, data):
    with path.open("x", encoding="utf-8") as stream:
        stream.write(data)


def dump_new(path, value):
    write_new(path, json.dumps(value, ensure_ascii=False, indent=2,
                               allow_nan=False) + "\n")


def validate_index(index):
    require(index["schema"] == "s78-match-visual-preflight-input-index-v1",
            "Unexpected index schema")
    require(index["source_ids"] == list(SOURCE_IDS), "Source ID set changed")
    require(index["target_id"] == 22, "Target changed")
    require(index["arms"] == ["real", "A0", "B"], "Arm set changed")
    require(index["records_count"] == len(index["records"]) == 18,
            "Exactly 18 records required")
    records = {}
    for row in index["records"]:
        key = (row["source_id"], row["arm"])
        require(key not in records, "Duplicate source/arm record")
        require(row["source_id"] in SOURCE_IDS and row["arm"] in IMAGE_KEYS,
                "Unexpected source or arm")
        require(row["target_id"] == 22 and row["source_image_key"] == "source19",
                "Record identity changed")
        require(row["target_image_key"] == IMAGE_KEYS[row["arm"]],
                "Target image mapping changed")
        require(row["visual_rating"] is None, "Index must remain unrated")
        require(row["coordinate_identity_S73_S77_exact"] is True,
                "Coordinate provenance absent")
        for field in ("source_xy_px", "target_xy_px"):
            xy = row[field]
            require(len(xy) == 2 and all(
                isinstance(v, (int, float)) and not isinstance(v, bool)
                and math.isfinite(v) and 0 <= v < FRAME_PX for v in xy),
                "Invalid or out-of-domain saved coordinate")
        records[key] = row
    require(set(records) == {(i, arm) for i in SOURCE_IDS for arm in IMAGE_KEYS},
            "Incomplete source/arm product")
    for source_id in SOURCE_IDS:
        anchors = [records[source_id, arm]["source_xy_px"] for arm in IMAGE_KEYS]
        require(all(xy == anchors[0] for xy in anchors),
                "Source coordinate differs between arms")
    return records


def verify_images(index):
    """Future build only: read bytes for SHA and IHDR, without pixel decoding."""
    verified = {}
    for key in ("source19", "B_22", "real22", "A0_22"):
        entry = index["images"][key]
        path = Path(entry["path"])
        require(path.is_absolute() and path.is_file(), "Missing absolute PNG")
        body = path.read_bytes()
        observed = digest(body)
        require(observed == entry["historical_declared_sha256"],
                "PNG identity differs from historical contract: " + key)
        require(len(body) >= 33 and body[:8] == b"\x89PNG\r\n\x1a\n"
                and body[8:16] == b"\x00\x00\x00\x0dIHDR",
                "Expected PNG IHDR")
        width, height = struct.unpack(">II", body[16:24])
        require((width, height) == (FRAME_PX, FRAME_PX),
                "PNG dimensions differ from coordinate domain")
        verified[key] = {"path": str(path), "sha256": observed,
                         "bytes": len(body), "width": width, "height": height}
    return verified


CSS = """
:root { color-scheme: light; font-family: system-ui, sans-serif; color: #182630; }
* { box-sizing: border-box; }
body { margin: 0; background: #eef2f4; }
header, main { max-width: 1280px; margin: auto; padding: 22px; }
header p { line-height: 1.6; max-width: 88ch; }
h1 { margin: 0 0 12px; font-size: 25px; } h2 { font-size: 19px; }
.notice { border-left: 4px solid #a76716; padding: 8px 12px; background: #fff3db; }
.pair { background: white; padding: 20px; border: 1px solid #ccd6dd;
  border-radius: 10px; margin-bottom: 24px; break-inside: avoid; }
.sides { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 24px; }
.side { min-width: 0; overflow-x: auto; }
.side h3 { font-size: 15px; margin: 0 0 8px; }
.full { position: relative; width: 576px; height: 576px;
  overflow: hidden; background: #d9e0e5; }
.full img { display: block; width: 100%; height: 100%; }
.context { display: flex; align-items: start; gap: 15px; margin-top: 14px; }
.local { position: relative; flex: 0 0 128px; width: 128px; height: 128px;
  overflow: hidden; background: #d9e0e5; }
.local img { position: absolute; display: block; width: 1152px;
  height: 1152px; max-width: none; image-rendering: pixelated; }
.marker { position: absolute; width: 18px; height: 18px;
  transform: translate(-50%, -50%); border: 2px solid #ffcc00;
  border-radius: 50%; box-shadow: 0 0 0 1px #172126;
  pointer-events: none; }
.coords { margin: 8px 0 0; font-variant-numeric: tabular-nums; font-size: 13px; }
.legend { font-size: 12px; line-height: 1.55; color: #3d505e; }
img { image-rendering: auto; }
footer { max-width: 1280px; margin: auto; padding: 0 22px 25px; line-height: 1.6; }
@media (max-width: 1220px) { .sides { grid-template-columns: 1fr; } }
"""


def side_html(label, image_alias, xy):
    x, y = xy
    # Half-up center rule for these nonnegative coordinates, not banker rounding.
    # Exactly 64 pixels: [cx-32,cx+32) x [cy-32,cy+32), not radius 64.
    # Never move the rounded center at an edge: outside padding is constant gray.
    cx, cy = (math.floor(v + 0.5) for v in xy)
    local_left = NEIGHBORHOOD_PX - LOCAL_ZOOM * cx
    local_top = NEIGHBORHOOD_PX - LOCAL_ZOOM * cy
    marker_left = NEIGHBORHOOD_PX + LOCAL_ZOOM * (x - cx)
    marker_top = NEIGHBORHOOD_PX + LOCAL_ZOOM * (y - cy)
    image_uri = "assets/" + image_alias + ".png"
    return f"""<div class="side"><h3>{html.escape(label)}</h3>
<div class="full"><img src="{image_uri}" alt="{html.escape(label)} 全图">
<span class="marker" style="left:{x / FRAME_PX * 100:.15g}%;top:{y / FRAME_PX * 100:.15g}%"></span></div>
<p class="coords">坐标 x={x:.6f}, y={y:.6f} px</p>
<div class="context"><div class="local"><img src="{image_uri}"
alt="{html.escape(label)} 局部邻域"
style="left:{local_left:.15g}px;top:{local_top:.15g}px">
<span class="marker" style="left:{marker_left:.15g}px;top:{marker_top:.15g}px"></span></div>
<p class="legend">邻域总边长 64 原图像素，半宽 32；中心 ({cx}, {cy})。
统一以最近邻放大 2 倍；灰色为边界 padding，不拉伸或移窗。
圆环仍标原小数坐标，中心透明。</p></div></div>"""


def build(index, records, verified, output, index_sha, script_sha):
    require(not output.exists() and not output.is_symlink(),
            "Output must be a new directory; previous attempts are preserved")
    output.mkdir(parents=False)
    viewer = output / "viewer"
    private = output / "preparer_mapping"
    viewer.mkdir()
    private.mkdir(mode=0o700)
    assets = viewer / "assets"
    assets.mkdir()
    aliases = {"source19": "S00"}
    aliases.update({IMAGE_KEYS[arm]: code for code, arm in DISPLAY_ARMS})
    for key, alias in aliases.items():
        # Symlinks point at the existing PNGs. No image copy or rewrite occurs.
        os.symlink(verified[key]["path"], assets / (alias + ".png"))
    cards, mapping = [], []
    for group_index, source_id in enumerate(SOURCE_IDS, start=1):
        for code, arm in DISPLAY_ARMS:
            row = records[source_id, arm]
            item = "P" + str(len(cards) + 1).zfill(3)
            group = "G" + str(group_index).zfill(2)
            cards.append(f'<section class="pair" id="{item}"><h2>{item} · {group} · {code}</h2>'
                         '<div class="sides">'
                         + side_html("S00", "S00", row["source_xy_px"])
                         + side_html(code, code, row["target_xy_px"])
                         + '</div></section>')
            mapping.append({"item_code": item, "group_code": group,
                            "target_code": code, "source_id": source_id,
                            "arm": arm, "input_record": row,
                            "source_window_center_xy": [math.floor(v + 0.5) for v in row["source_xy_px"]],
                            "target_window_center_xy": [math.floor(v + 0.5) for v in row["target_xy_px"]]})
    require(len(cards) == 18, "All 18 items must be rendered")
    document = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self' file:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>已有对应点的视觉检查</title><style>""" + CSS + """</style></head><body>
<header><h1>已有对应点的视觉检查</h1>
<p>共有 18 项，按固定组编号与匿名目标编号排列，全部保留。S00 是共同来源图。
圆环标示保存坐标，局部窗口按同一规则显示；图像沿用原文件。</p>
<p class="notice">本团队已经见过旧全图、标签与数值结果。本页隐藏当次标签提示，
不能称为从未见结果的盲审。图像内容可能让人识别条件，文件系统也能追踪原路径。
本页只用于检查对应点是否容易解释，不提供相机或方法验收结论。</p>
<p>本页没有评级、保存、统计或自动判定功能。不能凭一个圆环认定真实三维对应。
若图像缺失或尺寸异常，应停止使用并记录问题。</p></header><main>""" + "\n".join(cards) + """</main>
<footer>显示参数：全图保持 576×576 CSS 像素，窄屏横向滚动，不缩小。
局部中心按 floor(坐标+0.5) 四舍五入，边长 64 原图像素、半宽 32，
统一最近邻放大 2 倍。越界为常量灰 padding，不移动中心、不拉伸。
显示不修改原图像。无新增匹配或几何拟合。</footer>
</body></html>"""
    write_new(viewer / "index.html", document)
    dump_new(private / "ANON_MAPPING.json", {
        "scope": "Preparation mapping; do not include in reviewer-facing materials",
        "not_prospectively_blinded": True, "index_sha256": index_sha,
        "anonymous_arm_mapping": dict(DISPLAY_ARMS), "images": verified,
        "records": mapping})
    (private / "ANON_MAPPING.json").chmod(0o600)
    dump_new(output / "BUILD_RECEIPT.json", {
        "status": "VIEWER_PREPARED_NOT_VISUALLY_REVIEWED",
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "index_sha256": index_sha, "builder_sha256": script_sha,
        "image_files_read_for_SHA_and_IHDR": 4, "pixel_decodes": 0,
        "source_images_modified": 0, "features_computed": 0, "model_calls": 0,
        "visual_ratings": 0, "cards": 18, "source_ids": list(SOURCE_IDS),
        "neighborhood_source_px": NEIGHBORHOOD_PX,
        "local_zoom": LOCAL_ZOOM, "local_interpolation": "nearest at exact 2x via CSS pixelated",
        "window_center_rule": "floor(nonnegative_coordinate + 0.5), ties round up",
        "window_interval": "[cx-32,cx+32) x [cy-32,cy+32)",
        "marker_rule": "original fractional coordinate; not rounded with window center",
        "boundary": "fixed rounded center; constant gray #d9e0e5 outside-image padding; no stretch",
        "full_image_display_css_px": [576, 576],
        "order": "ascending source ID, then C01/C02/C03",
        "html_sha256": digest(document.encode("utf-8")),
        "images_verified_at_build_not_continuously": True,
        "browser_opened_by_builder": False, "new_method_validated": False})
    return viewer / "index.html"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--index-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(args.index.is_absolute() and args.output.is_absolute(),
            "Use explicit absolute index/output paths")
    require(not args.output.exists() and not args.output.is_symlink(),
            "Output already exists; stop before reading image inputs")
    index_bytes = args.index.read_bytes()
    index_sha = digest(index_bytes)
    require(index_sha == args.index_sha, "Index differs from reviewed SHA")
    index = json.loads(index_bytes)
    records = validate_index(index)
    verified = verify_images(index)
    destination = build(index, records, verified, args.output, index_sha,
                        digest(Path(__file__).read_bytes()))
    # Deliberately do not open a browser or load images into a UI.
    print(json.dumps({"status": "PREPARED_ONLY", "viewer": str(destination)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
