"""S26 source-only preparation: saved predictions -> unchanged VMem GA.

No CLI or automatic execution. This draft has not loaded NPZ/RGB/GT, imported
torch, instantiated a model, or run GA. Parent must freeze the experiment first.
AST-derived original VMem functions retain their CC BY-NC-SA 4.0 license.
"""
from __future__ import annotations

import ast
import copy
from dataclasses import dataclass
import hashlib
import importlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SHAPES = {
    "pts3d_in_self_view": (1, 384, 512, 3),
    "pts3d_in_other_view": (1, 384, 512, 3),
    "conf_self": (1, 384, 512), "conf": (1, 384, 512),
    "camera_pose": (1, 7), "rgb": (1, 384, 512, 3),
}


def sha256(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def derive_original_functions(wrapper_source):
    """Extract original functions and the exact original star assembly body.

    The sole omitted statement from the assembly region is the model inference
    call: its `outputs` variable is now the already-saved, validated payload.
    This does not assert equivalence between different backbone implementations.
    """
    tree = ast.parse(wrapper_source)
    wanted = ("listify", "collate_with_cat", "prepare_input_from_pil", "prepare_output")
    original = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    functions = [copy.deepcopy(original[name]) for name in wanted]
    wrapper = original["run_inference_from_pil"]
    first = next(i for i, n in enumerate(wrapper.body)
                 if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "output" for t in n.targets))
    end = next(i for i, n in enumerate(wrapper.body)
               if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "total_time" for t in n.targets))
    region = wrapper.body[first:end]
    removed = [n for n in region if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call)
               and isinstance(n.value.func, ast.Name) and n.value.func.id == "inference"]
    if len(removed) != 1 or ast.unparse(removed[0]) != "outputs, state_args = inference(views, model, device)":
        raise RuntimeError("Original model-call anchor changed")
    assembly = [copy.deepcopy(n) for n in region if n is not removed[0]]
    function = ast.parse("def build_original_output(outputs):\n    return outputs\n").body[0]
    function.body = assembly + [ast.Return(ast.Name("output", ast.Load()))]
    functions.append(function)
    module = ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[]))
    compile(module, "<S26 original functions, compile only>", "exec")
    # Original non-model statements and full prepare_output preserved exactly.
    assert [ast.dump(n, include_attributes=False) for n in assembly] == [
        ast.dump(n, include_attributes=False) for n in region if n is not removed[0]]
    return module, {
        "assembly_source_lines": [region[0].lineno, region[-1].end_lineno],
        "assembly_statements_preserved": len(assembly),
        "model_calls_removed": 1,
        "original_ga_function_arithmetic_changes": 0,
        "original_functions_copied": list(wanted),
        "numerical_compatibility": "NOT_RUN",
    }


def configure_original_geometry(binding):
    """Future runtime only; no model imports/loaders are called explicitly."""
    for path, expected in binding["source_identities"].items():
        if sha256(path) != expected:
            raise RuntimeError(f"Source/config identity changed: {path}")
    embedded = Path(binding["embedded_root"]).resolve()
    overlay = Path(binding["overlay"]).resolve()
    prefixes = ("dust3r", "src.dust3r", "models", "cloud_opt", "croco")
    for name, module in list(sys.modules.items()):
        if name == prefixes[0] or name.startswith(tuple(p + "." for p in prefixes)) or name in prefixes:
            origin = getattr(module, "__file__", None)
            if origin and not Path(origin).resolve().is_relative_to(embedded):
                raise RuntimeError("Use a fresh process; geometry source namespace is occupied")
    sys.path[:0] = [str(overlay), str(embedded), str(embedded / "src"), str(embedded / "src/croco")]
    import numpy as np
    import torch
    import scipy
    if (np.__version__, torch.__version__, scipy.__version__) != ("1.26.4", "2.7.0", "1.16.2"):
        raise RuntimeError("Numerical package versions differ from S17C")
    if any(Path(m.__file__).resolve().is_relative_to(overlay) for m in (np, torch, scipy)):
        raise RuntimeError("Overlay cannot replace core numerical packages")
    wrapper = embedded / "surfel_inference.py"
    module, proof = derive_original_functions(wrapper.read_text())
    namespace = {"np": np, "torch": torch, "os": importlib.import_module("os")}
    exec(compile(module, str(wrapper), "exec"), namespace)
    return namespace, proof


def load_saved_predictions(records):
    """Future runtime only. Read the complete six heads, without pose conversion."""
    import numpy as np
    import torch
    predictions = []
    for i, record in enumerate(records):
        if record["index"] != i or sha256(record["path"]) != record["sha256"]:
            raise RuntimeError("Saved head identity/index mismatch")
        with np.load(record["path"], allow_pickle=False) as archive:
            if set(archive.files) != set(SHAPES):
                raise RuntimeError("Missing or unexpected prediction head")
            values = {}
            for name, shape in SHAPES.items():
                value = archive[name]
                if value.shape != shape or value.dtype != np.float32 or not np.isfinite(value).all():
                    raise RuntimeError(f"Invalid saved head schema: frame={i}, head={name}")
                if name in ("conf", "conf_self") and not (value > 0).all():
                    raise RuntimeError("Original GA log-conf weight requires positive confidence")
                values[name] = torch.from_numpy(np.array(value, copy=True))
            predictions.append(values)
    return predictions


def load_original_views(namespace, frames):
    """Future runtime: real RGB preprocessing, 0 model calls, no GT images."""
    from PIL import Image
    images = []
    for i, frame in enumerate(frames):
        if frame["index"] != i or sha256(frame["path"]) != frame["sha256"]:
            raise RuntimeError("RGB identity/index mismatch")
        with Image.open(frame["path"]) as image:
            images.append(image.copy())
    return namespace["prepare_input_from_pil"](images, size=512, revisit=1, update=True)


def assemble_saved_output(namespace, views, predictions):
    if len(views) != len(predictions) or len(views) not in (4, 8):
        raise RuntimeError("This pilot uses an intact four- or eight-frame prefix")
    for i, view in enumerate(views):
        if view["idx"] != i or tuple(view["img"].shape) != (1, 3, 384, 512):
            raise RuntimeError("Original view ordering/shape mismatch")
    output = namespace["build_original_output"]({"views": views, "pred": predictions})
    if output["view1"]["idx"] != [0] * (len(views) - 1):
        raise RuntimeError("Anchor must stay historical frame zero")
    if output["view2"]["idx"] != list(range(1, len(views))):
        raise RuntimeError("Original directed star edge order changed")
    return output


@dataclass(frozen=True)
class CommonOldDepth:
    """Caller must bind the sealed original4 GA output, never sensor depth."""
    values: object
    original4_ga_seal_sha256: str
    expected_depth_tensor_sha256: str
    control_pose_prefix_tensor_sha256: str
    provenance_kind: str = "original_cut3r_saved4_given_pose_no_depth_ga400"


def tensor_sha256(value):
    """Future runtime: schema checked separately; hash contiguous FP32 bytes."""
    return hashlib.sha256(value.detach().cpu().contiguous().numpy().tobytes()).hexdigest()


def run_original_ga(namespace, output, *, control_c2ws, old_depth=None, output_dir):
    """Future runtime: unchanged prepare_output, with explicit given-pose control.

    This is an adapter, not a finished supervised runner. Caller owns fresh
    process, seeded RNG, deadline/RSS monitor, identities, observer trace,
    complete output sealing and the separate depth scorer. No GT file is read
    by this function; control_c2ws is a pre-sealed common condition tensor.
    """
    import torch
    n = len(output["view2"]["idx"]) + 1
    if n not in (4, 8) or tuple(control_c2ws.shape) != (n, 4, 4):
        raise RuntimeError("Given camera tensor must cover the complete prefix")
    if control_c2ws.device.type != "cpu" or control_c2ws.dtype != torch.float32:
        raise RuntimeError("Given cameras must be CPU FP32")
    if not torch.isfinite(control_c2ws).all():
        raise RuntimeError("Nonfinite control cameras")
    if torch.get_num_threads() != 8 or torch.is_autocast_enabled("cpu") or torch.is_autocast_enabled("cuda"):
        raise RuntimeError("Require CPU8 and disabled outer autocast")
    if n == 4 and old_depth is not None:
        raise RuntimeError("Shared old-depth construction must have no depth prior")
    if n == 8 and old_depth is None:
        raise RuntimeError("Eight-frame comparison requires the common old four-depth packet")
    depth = None
    if old_depth is not None:
        if (not isinstance(old_depth, CommonOldDepth)
                or old_depth.provenance_kind != "original_cut3r_saved4_given_pose_no_depth_ga400"
                or len(old_depth.original4_ga_seal_sha256) != 64):
            raise RuntimeError("Shared old depth must identify the sealed original CUT four-frame GA")
        depth = old_depth.values.detach().clone()
        if (tuple(depth.shape) != (4, 384, 512) or depth.dtype != torch.float32
                or depth.device.type != "cpu" or not torch.isfinite(depth).all() or not (depth > 0).all()):
            raise RuntimeError("Invalid common old-depth tensor")
        if tensor_sha256(depth) != old_depth.expected_depth_tensor_sha256:
            raise RuntimeError("Common old-depth content differs from the sealed tensor")
        if tensor_sha256(control_c2ws[:4]) != old_depth.control_pose_prefix_tensor_sha256:
            raise RuntimeError("Old-depth construction and this run used different prefix camera conditions")
    # Original function internally enable_grad's the scene optimizer. Do not
    # wrap this in torch.inference_mode(); do not form pose*self pointmaps.
    return namespace["prepare_output"](
        output, control_c2ws.detach().clone(), depth, lr=0.01, niter=400,
        outdir=str(output_dir), device="cpu", save_flag=False,
    )
