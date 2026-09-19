"""Pure arithmetic checks for the proposed ICL camera/depth contract.
No dataset, GT, model, or generated image is read.  Passing is only an
implementation sanity check, never Gate 0 or method validation.
"""
import math, json

fx, fy, cx, cy = 525.0, 525.0, 319.5, 239.5
u, v, d = 100.0, 200.0, 5000.0
z = d / 5000.0
x, y = (u-cx)*z/fx, (v-cy)*z/fy
assert abs(z-1.0) < 1e-12
assert abs(x - (u-cx)/fx) < 1e-12
assert abs(y - (v-cy)/fy) < 1e-12

# MATLAB 1-index centre 320.5/240.5 corresponds exactly to 0-index 319.5/239.5.
assert (320.5 - 1.0) == cx
assert (240.5 - 1.0) == cy

# Native radial-to-z conversion round trip for one non-central ray.
radial = 2.0
native_fy = -480.0
native_u0, native_v0 = 320.5, 240.5  # MATLAB 1-index
uu, vv = 400.0, 300.0
den = math.sqrt(((uu-native_u0)/fx)**2 + ((vv-native_v0)/native_fy)**2 + 1.0)
z_native = radial / den
radial_back = z_native * den
assert abs(radial_back-radial) < 1e-12

out = {
    "kind": "arithmetic_contract_check",
    "dataset_read": False,
    "gt_read": False,
    "model_run": False,
    "checks": ["tum_depth_factor", "matlab_to_zero_index_center", "native_radial_z_roundtrip"],
    "status": "PASS_ARITHMETIC_ONLY",
}
print(json.dumps(out, indent=2))
