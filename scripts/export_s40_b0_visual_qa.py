#!/usr/bin/env python3
"""Export human-readable names and a contact sheet after the sealed B0 blind score."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "results/S40_declared_variant_generation/archive"
SCORE = ROOT / "work/S42_baseline_failure_preregistration/B0_score_attempt_01"
OUT = ROOT / "results/S40_declared_variant_generation/visual_qa_all9"
INPUT = Path("/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/test_samples/changi.jpg")
INPUT_SHA256 = "12fc2c4ddfccee952d5390b147b813a8f062209832ec675013f82283e796e54a"
SCORE_RECEIPT_SHA256 = "93c90e24e404aa1f87e111ed3a7c79d51de9d9bf35babd060ac807af9d99f2ad"
SCORE_REPORT_SHA256 = "13b190b126e925ae18f43728781c323d5cece8d9a591b73e6e9bf3a865aa8a8e"
FRAMES = [
    (0, 0.00, "2569b50b56f715859497aaaa24a7b12642bfa8507347f29f63a897ad0db2c13f.png", 664039),
    (1, 1.25, "37736461037400e58199ac47972576c3ffd038c4eda6bf1bce915eea7ad69485.png", 626191),
    (2, 2.50, "430a829031b5e9ffda02b5f214b0f8117391ed26e6c01008dbd663ce3e436b29.png", 624118),
    (3, 3.75, "f96ded0cc45d1fd200a620aff169bde630c3294012db432e8c6f553af23ff3eb.png", 623484),
    (4, 5.00, "02e058acd5a45db3eef05a15d5b09fbdfcd0d1c5b7766a48699480d48339fb32.png", 627101),
    (5, 3.75, "42da5a7b0df3856ac58bef41dc075f089363e311ea6d9c1abe19327729e5314a.png", 631726),
    (6, 2.50, "9ea136fe456c7a1c5095f965a36a7b5ced18a58a38bf394ffc89658c1fd4974c.png", 630721),
    (7, 1.25, "5fca09e965dd9b75f42572423c2680b1484ad11afe18d104db02c3e851564bce.png", 631174),
    (8, 0.00, "cce60092c6c84555cfe7c4d1eda59c581bf08aa0b6684555a63c0e7334698b08.png", 640200),
]


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def main() -> None:
    receipt = SCORE / "receipt.json"
    report = SCORE / "report.json"
    require(sha256(receipt) == SCORE_RECEIPT_SHA256, "Sealed B0 receipt identity changed")
    require(sha256(report) == SCORE_REPORT_SHA256, "Sealed B0 report identity changed")
    score = json.loads(receipt.read_text(encoding="utf-8"))
    require(score.get("technically_valid") is True and score.get("human_viewing_now_allowed") is True,
            "B0 receipt does not permit post-score human viewing")
    require(sha256(INPUT) == INPUT_SHA256, "Input image identity changed")
    require(not OUT.exists(), "Visual QA export already exists; refusing to replace it")
    OUT.mkdir(parents=False, mode=0o755)

    input_copy = OUT / "input_reference_changi.jpg"
    shutil.copyfile(INPUT, input_copy)
    require(sha256(input_copy) == INPUT_SHA256, "Input copy is not byte-identical")

    exported = []
    contact_items = [("Input reference", input_copy)]
    for frame_id, yaw, source_name, expected_bytes in FRAMES:
        source = ARCHIVE / "images" / source_name
        expected_sha = source_name.removesuffix(".png")
        require(source.is_file() and source.stat().st_size == expected_bytes, "Archived frame size differs")
        require(sha256(source) == expected_sha, "Archived frame SHA-256 differs")
        destination = OUT / ("frame_%02d_requested_yaw_%0.2f.png" % (frame_id, yaw))
        shutil.copyfile(source, destination)
        require(sha256(destination) == expected_sha, "Named frame copy is not byte-identical")
        with Image.open(destination) as image:
            require(image.mode == "RGB" and image.size == (576, 576), "Named frame image metadata differs")
        exported.append({
            "id": frame_id,
            "requested_yaw_degrees": yaw,
            "source_path": str(source),
            "source_sha256": expected_sha,
            "source_bytes": expected_bytes,
            "named_copy_path": str(destination),
            "named_copy_sha256": expected_sha,
        })
        contact_items.append(("Frame %02d | requested yaw %.2f°" % (frame_id, yaw), destination))

    cell_width, image_height, label_height = 288, 288, 32
    cols, rows = 5, 2
    sheet = Image.new("RGB", (cols * cell_width, rows * (image_height + label_height)), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, (label, path) in enumerate(contact_items):
        col, row = index % cols, index // cols
        x, y = col * cell_width, row * (image_height + label_height)
        with Image.open(path) as image:
            tile = image.convert("RGB").resize((cell_width, image_height), Image.Resampling.LANCZOS)
        sheet.paste(tile, (x, y + label_height))
        draw.text((x + 7, y + 10), label, fill="black", font=font)
    contact = OUT / "S40_input_plus_all9_contact_sheet.png"
    sheet.save(contact, format="PNG", optimize=False)

    manifest = {
        "schema": "s40-post-b0-visual-qa-export-v1",
        "status": "EXPORTED_FOR_POST_BLIND_SCORE_HUMAN_QA",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "score_receipt_path": str(receipt),
        "score_receipt_sha256": SCORE_RECEIPT_SHA256,
        "score_report_path": str(report),
        "score_report_sha256": SCORE_REPORT_SHA256,
        "input_reference": {"source_path": str(INPUT), "sha256": INPUT_SHA256, "named_copy_path": str(input_copy)},
        "generated_frames": exported,
        "generated_frames_are_byte_identical_named_copies": True,
        "contact_sheet_path": str(contact),
        "contact_sheet_sha256": sha256(contact),
        "contact_sheet_scope": "Derived display artifact only; authoritative machine scores use raw archived tensor bodies, not this PNG.",
        "claim_boundary": "Export does not establish visual quality, camera obedience, repeatability, baseline failure, method gain, or novelty.",
    }
    manifest_path = OUT / "manifest.json"
    with manifest_path.open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"out": str(OUT), "contact_sheet": str(contact), "manifest_sha256": sha256(manifest_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
