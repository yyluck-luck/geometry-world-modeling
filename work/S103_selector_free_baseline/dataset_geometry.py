#!/usr/bin/env python3
"""Per-dataset geometry conventions, declared explicitly rather than hardcoded.

Addendum A2: geom_eval_s110.py hardcoded depth/1000, which is the RGB-D Scenes
v2 convention.  TUM uses /5000, as this project's own src/tum_rgbd.py has always
recorded ("Registered PNG depth / 5000 is optical Z in metres; 0 is missing").
Running S113 on TUM with the wrong constant would have scaled every depth by 5x.

Nothing here may be inferred at runtime.  A dataset that is not listed must be
added deliberately, with its source of truth cited, before it can be scored.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetGeometry:
    dataset_id: str
    depth_divisor: float          # raw PNG value / divisor = metres
    invalid_depth_value: int      # raw value meaning "no measurement"
    native_wh: tuple              # (width, height) of the raw frames
    pose_convention: str          # what the stored pose maps
    source_of_truth: str


REGISTRY = {
    "rgbd-scenes-v2": DatasetGeometry(
        dataset_id="rgbd-scenes-v2",
        depth_divisor=1000.0,
        invalid_depth_value=0,
        native_wh=(640, 480),
        pose_convention="camera-to-world, 4x4 row-major in frame-XXXXXX.pose.txt",
        source_of_truth="dataset README; depth stored in millimetres"),
    "tum-rgbd": DatasetGeometry(
        dataset_id="tum-rgbd",
        depth_divisor=5000.0,
        invalid_depth_value=0,
        native_wh=(640, 480),
        pose_convention=("groundtruth.txt gives timestamp tx ty tz qx qy qz qw; "
                         "this project converts via src/tum_rgbd.optical_to_vmem_c2w"),
        source_of_truth=("TUM RGB-D file format documentation; mirrored in this "
                         "project's src/tum_rgbd.py line 5 and line 222")),
}


def get(dataset_id: str) -> DatasetGeometry:
    if dataset_id not in REGISTRY:
        raise KeyError(
            f"dataset '{dataset_id}' has no declared geometry convention. "
            f"Add it with a cited source before scoring; do not guess a divisor.")
    return REGISTRY[dataset_id]


def self_test():
    ok = []
    ok.append(("rgbd-scenes-v2 uses /1000", get("rgbd-scenes-v2").depth_divisor == 1000.0))
    ok.append(("tum-rgbd uses /5000", get("tum-rgbd").depth_divisor == 5000.0))
    try:
        get("unlisted-dataset"); refused = False
    except KeyError:
        refused = True
    ok.append(("unlisted dataset is refused, not guessed", refused))
    for name, passed in ok:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
    return 0 if all(p for _, p in ok) else 1


if __name__ == "__main__":
    raise SystemExit(self_test())
