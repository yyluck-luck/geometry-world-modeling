"""S25 preparation only: source-derived, single-event FILT3R branch adapter.

No model is imported or run at import/build time. Numerical compatibility is
UNTESTED. This file does not authorize an experiment or select an event/horizon.
The generated FILT3R method retains the upstream CC BY-NC-SA 4.0 license.
"""
from __future__ import annotations

import ast
import copy
from dataclasses import dataclass
import hashlib
import inspect
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
STATE_FIELDS = (
    "state_feat", "state_pos", "init_state_feat", "mem", "init_mem",
    "prev_reset", "prev_candidate_state_feat", "prev_feat_i", "state_cov",
    "kalman_stats", "device",
)
S_FIELDS = ("state_feat", "state_cov", "kalman_stats",
            "prev_candidate_state_feat", "prev_feat_i")
ACTIONS = ("normal", "freeze_s_aux", "freeze_m", "freeze_all")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_source_binding():
    binding = json.loads((HERE / "source_binding.json").read_text())
    for path, expected in binding["identities"].items():
        if sha256(path) != expected:
            raise RuntimeError(f"Frozen source changed: {path}")
    return binding


def _original_function(source):
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == "ARCroco3DStereo")
    fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
              and n.name == "forward_recurrent_lighter")
    if any(isinstance(n, ast.Name) and n.id.startswith("_s25") for n in ast.walk(fn)):
        raise RuntimeError("Unexpected pre-existing instrumentation")
    return fn


def derive_function(source):
    """Return instrumented AST and a machine-checked erasure proof.

    Only three guarded observation/restore sites, one per-frame guard, the
    loop's starting index, the function name and the extra kwarg are added.
    No upstream update/head/helper expression is rewritten.
    """
    original = _original_function(source)
    derived = copy.deepcopy(original)
    derived.name = "_s25_forward_recurrent_lighter"
    derived.args.kwonlyargs.append(ast.arg(arg="_s25"))
    derived.args.kw_defaults.append(ast.Constant(None))
    loop = next(n for n in derived.body if isinstance(n, ast.For))
    if ast.unparse(loop.iter) != "enumerate(views)":
        raise RuntimeError("Unsupported source loop")
    fields_literal = "{" + ", ".join(f"{f!r}: {f}" for f in STATE_FIELDS) + "}"
    start_code = (
        "if _s25 is not None:\n"
        "    _s25.start(self, views, device, update_type, need_attn_for_update)\n"
        "    if _s25.resume is not None:\n"
        f"        {', '.join(STATE_FIELDS)} = _s25.restore_values()\n"
    )
    derived.body.insert(derived.body.index(loop), ast.parse(start_code).body[0])
    loop.iter = ast.parse(
        "enumerate(views, start=(_s25.start_index if _s25 is not None else 0))",
        mode="eval").body
    view_assign = next(n for n in loop.body if isinstance(n, ast.Assign)
                       and ast.unparse(n.targets[0]) == "view")
    loop.body.insert(loop.body.index(view_assign) + 1, ast.parse(
        "if _s25 is not None:\n    _s25.before_frame(i, view)\n").body[0])
    emit = [n for n in loop.body if isinstance(n, ast.Expr)
            and ast.unparse(n) == "ress.append(res_cpu)"]
    if len(emit) != 1:
        raise RuntimeError("Current-head emission anchor changed")
    loop.body.insert(loop.body.index(emit[0]) + 1, ast.parse(
        "if _s25 is not None and i == _s25.fork_index:\n"
        f"    _s25.before_write(i, {fields_literal})\n").body[0])
    loop.body.append(ast.parse(
        "if _s25 is not None and i == _s25.final_index:\n"
        f"    _s25.after_write(i, {fields_literal})\n").body[0])
    ast.fix_missing_locations(derived)

    # Erase only the four instrumentation guards, then restore signature/index.
    # This is structural equivalence, NOT numerical equivalence under execution.
    erased = copy.deepcopy(derived)
    erased.name = original.name
    erased.args = copy.deepcopy(original.args)
    removed = []

    class Erase(ast.NodeTransformer):
        def visit_If(self, node):
            if any(isinstance(n, ast.Name) and n.id == "_s25"
                   for n in ast.walk(node.test)):
                removed.append(ast.unparse(node.test))
                return None
            return self.generic_visit(node)

        def visit_For(self, node):
            node = self.generic_visit(node)
            node.iter = copy.deepcopy(next(n for n in original.body
                                           if isinstance(n, ast.For)).iter)
            return node

    erased = Erase().visit(erased)
    exact = ast.dump(erased, include_attributes=False) == ast.dump(original, include_attributes=False)
    if not exact or len(removed) != 4:
        raise RuntimeError("AST erasure proof failed")
    module = ast.fix_missing_locations(ast.Module(body=[derived], type_ignores=[]))
    compile(module, "<S25 source-derived FILT3R>", "exec")
    return module, {
        "upstream_ast_restored_exactly": exact,
        "guard_sites_removed": len(removed),
        "original_statement_count": sum(isinstance(n, ast.stmt) for n in ast.walk(original)),
        "original_arithmetic_or_helper_calls_rewritten": 0,
        "source_start_line": original.lineno,
        "source_end_line": original.end_lineno,
        "numerical_compatibility": "NOT_RUN",
    }


def select_branch_states(pre, post, *, clone=copy.deepcopy):
    """Pure selection of whole write groups; callable without torch/model.

    Each result is a deep independent tree. Structural/reset controls use the
    post-event value: a frame was consumed even when both writes are frozen.
    """
    if set(pre) != set(STATE_FIELDS) or set(post) != set(STATE_FIELDS):
        raise ValueError("State-field contract mismatch")
    if pre["prev_reset"] or post["prev_reset"]:
        raise ValueError("Reset/intervention collisions are out of scope")
    result = {}
    for action in ACTIONS:
        selected = dict(post)
        if action in ("freeze_s_aux", "freeze_all"):
            selected.update({key: pre[key] for key in S_FIELDS})
        if action in ("freeze_m", "freeze_all"):
            selected["mem"] = pre["mem"]
        result[action] = clone(selected)
    return result


def _clone_tree(value):
    import torch
    if torch.is_tensor(value):
        return value.detach().clone()
    if isinstance(value, dict):
        return {copy.deepcopy(k): _clone_tree(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_clone_tree(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_clone_tree(v) for v in value)
    return copy.deepcopy(value)


def _cache_objects(model):
    """The two audited inference cache types; preserve shared-object identity."""
    found, seen = {}, set()
    for path, module in model.named_modules():
        candidates = [(path, module)]
        if hasattr(module, "position_getter"):
            candidates.append((path + ".position_getter", module.position_getter))
        for obj_path, obj in candidates:
            if id(obj) in seen:
                continue
            seen.add(id(obj))
            for attr in ("cache", "cache_positions"):
                if hasattr(obj, attr):
                    if not isinstance(getattr(obj, attr), dict):
                        raise RuntimeError("Unexpected cache representation")
                    found[(obj_path, attr)] = (obj, attr)
    return found


@dataclass(frozen=True)
class Checkpoint:
    next_index: int
    frame_ids: tuple[str, ...]
    action: str
    state: dict
    runtime: dict
    model_token: int


def validate_checkpoint(checkpoint):
    """Reject malformed absolute indices before any model/frame operation."""
    if not isinstance(checkpoint, Checkpoint):
        raise TypeError("Need an adapter Checkpoint")
    if type(checkpoint.next_index) is not int or checkpoint.next_index < 1:
        raise ValueError("next_index must be an integer >= 1; bool is not an index")
    if (type(checkpoint.frame_ids) is not tuple
            or any(type(x) is not str or not x for x in checkpoint.frame_ids)
            or checkpoint.next_index != len(checkpoint.frame_ids)
            or len(set(checkpoint.frame_ids)) != len(checkpoint.frame_ids)):
        raise ValueError("next_index must equal the complete unique prefix ID count")
    if checkpoint.action not in ACTIONS or set(checkpoint.state) != set(STATE_FIELDS):
        raise ValueError("Checkpoint action/state schema mismatch")
    if checkpoint.state["prev_reset"] is not False:
        raise ValueError("Reset-state checkpoints are unsupported")


@dataclass
class RunResult:
    original_return: tuple
    checkpoint: Checkpoint
    branches: dict[str, Checkpoint]
    first_index: int
    final_index: int


class _Controller:
    def __init__(self, adapter, views, frame_ids, resume, fork_last):
        self.adapter, self.resume = adapter, resume
        self.frame_ids = tuple(frame_ids)
        if any(type(x) is not str or not x for x in self.frame_ids):
            raise ValueError("Frame IDs must be nonempty strings")
        if resume is not None:
            validate_checkpoint(resume)
        self.start_index = 0 if resume is None else resume.next_index
        self.final_index = self.start_index + len(views) - 1
        self.fork_index = self.final_index if fork_last else -1
        self.pre = None
        self.checkpoint = None
        self.branches = {}
        if len(views) == 0 or len(views) != len(frame_ids):
            raise ValueError("Need nonempty views with one caller-provided ID per frame")
        if fork_last and self.fork_index < 1:
            raise ValueError("A real prefix of at least one frame is required")
        prefix_ids = () if resume is None else resume.frame_ids
        self.all_ids = prefix_ids + self.frame_ids
        if len(set(self.all_ids)) != len(self.all_ids):
            raise ValueError("Repeated frame IDs are outside this one-pass contract")

    def start(self, model, views, device, update_type, need_attn):
        if model is not self.adapter.model or update_type != "filt3r" or need_attn:
            raise RuntimeError("Only bound FILT3R lighter is supported")
        if str(device) != "cpu":
            raise RuntimeError("CPU only")
        self.adapter._assert_runtime()
        if self.resume is not None:
            if self.resume.model_token != id(model):
                raise RuntimeError("Checkpoint is in-process and tied to this model")
            self.adapter._restore_runtime(self.resume.runtime)

    def restore_values(self):
        state = _clone_tree(self.resume.state)
        if set(state) != set(STATE_FIELDS):
            raise RuntimeError("Incomplete checkpoint")
        return tuple(state[f] for f in STATE_FIELDS)

    def before_frame(self, i, view):
        import torch
        if view["img"].device.type != "cpu" or tuple(view["img"].shape) != (1, 3, 384, 512):
            raise RuntimeError("Contract requires CPU B=1, RGB 384x512")
        if view["img"].dtype != torch.float32:
            raise RuntimeError("Contract requires FP32 input")
        if not bool(view["img_mask"].all()) or bool(view["ray_mask"].any()):
            raise RuntimeError("Only RGB-only, valid-frame inputs are supported")
        reset = view["reset"]
        if reset is not None and bool((reset > 0.5).any()):
            raise RuntimeError("Reset frames are not supported by this causal fork")
        update = view.get("update")
        if update is not None and not bool(update.all()):
            raise RuntimeError("Update-suppressed inputs are outside this contract")
        if i < self.start_index or i > self.final_index:
            raise RuntimeError("Absolute frame index mismatch")

    def before_write(self, i, state):
        # Executed only after res_cpu has been appended, before Kalman dictionary
        # mutation. Do NOT capture references and call them snapshots.
        self.pre = _clone_tree(state)

    def after_write(self, i, state):
        # Executed after reset handling AND _advance_prev_buffers.
        runtime = self.adapter._capture_runtime()
        post = _clone_tree(state)
        self.checkpoint = Checkpoint(i + 1, self.all_ids, "normal", post, runtime, id(self.adapter.model))
        if self.fork_index == i:
            if self.pre is None:
                raise RuntimeError("Pre-write state was not captured")
            states = select_branch_states(self.pre, post, clone=_clone_tree)
            self.branches = {
                action: Checkpoint(i + 1, self.all_ids, action, values,
                                   _clone_tree(runtime), id(self.adapter.model))
                for action, values in states.items()
            }


class StateInterventionAdapter:
    """Executable draft, in-process only. Caller owns input SHA/budget protocol.

    Call only after a later parent decision approves a numerical compatibility
    pilot. No method of this class is called by the static preparation script.
    """
    def __init__(self, model):
        binding = verify_source_binding()
        self.model = model
        self.source_path = Path(binding["model_source"]).resolve()
        original = model.forward_recurrent_lighter
        if Path(inspect.getsourcefile(original)).resolve() != self.source_path:
            raise RuntimeError("Loaded method is not from the bound FILT source")
        if "forward_recurrent_lighter" in vars(model):
            raise RuntimeError("Instance method replacement is unsupported")
        self._original_code = original.__func__.__code__
        self._training_identity = tuple((n, m.training) for n, m in model.named_modules())
        self._method_identity = self._methods()
        self._rope_identity = self._ropes()
        self._parameter_identity = self._parameters()
        self._config_identity = self._configuration()
        self._caches = _cache_objects(model)
        module, self.structural_proof = derive_function(self.source_path.read_text())
        namespace = dict(original.__func__.__globals__)
        exec(compile(module, str(HERE / "derived_forward.py"), "exec"), namespace)
        self._forward = namespace["_s25_forward_recurrent_lighter"]

    def _methods(self):
        audited = {
            "model": (self.model, (
                "forward_recurrent_lighter", "_encode_image", "_encode_ray_map",
                "_get_img_level_feat", "_init_state", "_encode_state", "_decoder",
                "_recurrent_rollout", "_downstream_head", "_apply_stream_reset",
                "_advance_prev_buffers", "_compute_kalman_ema_gain_and_cov",
                "_ema_update", "_get_hparam", "_resolve_model_update_type",
                "_requires_attn_for_update")),
            "pose_retriever": (self.model.pose_retriever, ("inquire", "update_mem")),
        }
        result = []
        for group, (obj, names) in audited.items():
            for name in names:
                method = getattr(obj, name)
                if name in vars(obj) or Path(inspect.getsourcefile(method)).resolve() != self.source_path:
                    raise RuntimeError(f"Unsupported replacement of {group}.{name}")
                result.append((group, name, method.__func__.__code__))
        return tuple(result)

    def _ropes(self):
        expected_path = Path(verify_source_binding()["signed_rope_helper"]).resolve()
        result = []
        for name, module in self.model.named_modules():
            if type(module).__module__ != "models.pos_embed":
                continue
            if type(module).__name__ != "RoPE2D":
                raise RuntimeError("Unexpected positional-embedding implementation")
            forward = type(module).forward
            owner = sys.modules.get(forward.__module__)
            if (forward is not getattr(owner, "signed_forward", None)
                    or Path(inspect.getsourcefile(forward)).resolve() != expected_path
                    or module.base != 100.0 or module.F0 != 1.0):
                raise RuntimeError("Require the bound signed RoPE helper, base=100, F0=1")
            result.append((name, id(module), forward.__code__,
                           module.get_cos_sin.__func__.__code__, module.rotate_half.__code__,
                           module.base, module.F0))
        if not result:
            raise RuntimeError("No audited CPU RoPE module found")
        return tuple(result)

    def _parameters(self):
        return tuple((n, id(p), p.data_ptr(), p._version, tuple(p.shape), str(p.dtype), str(p.device))
                     for n, p in self.model.named_parameters())

    def _configuration(self):
        # Freeze all effective keys called via _get_hparam in this source.
        tree = ast.parse(self.source_path.read_text())
        values = {}
        for n in ast.walk(tree):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "_get_hparam" and n.args
                    and isinstance(n.args[0], ast.Constant)):
                key = n.args[0].value
                default = ast.literal_eval(n.args[1]) if len(n.args) > 1 else None
                values[(key, repr(default))] = repr(self.model._get_hparam(key, default))
        for key in ("pose_head_flag", "dec_depth", "state_pe", "state_size", "fixed_input_length", "gradient_checkpointing"):
            values[(key, "attribute")] = repr(getattr(self.model, key))
        return values

    def _assert_runtime(self):
        import torch
        verify_source_binding()
        if tuple((n, m.training) for n, m in self.model.named_modules()) != self._training_identity:
            raise RuntimeError("Preserve the baseline's per-module training flags")
        # S21/S22/S24 retain training=True. Do not silently switch to eval.
        # The audited source uses zero dropout; reject actually stochastic or
        # batch-stat-updating modules instead of changing their execution mode.
        for m in self.model.modules():
            if m.training and isinstance(m, torch.nn.modules.batchnorm._BatchNorm):
                raise RuntimeError("Active BatchNorm is outside the branch contract")
            if m.training and isinstance(m, torch.nn.modules.dropout._DropoutNd) and m.p > 0:
                raise RuntimeError("Active dropout is outside the branch contract")
            if m.training and getattr(m, "drop_prob", 0) > 0:
                raise RuntimeError("Active stochastic depth is outside the branch contract")
        if torch.is_grad_enabled() or torch.is_autocast_enabled("cpu") or torch.is_autocast_enabled("cuda"):
            raise RuntimeError("Use torch.no_grad and disabled outer autocast")
        if torch.get_num_threads() != 8:
            raise RuntimeError("Keep the frozen CPU-8 execution setting")
        if (self._parameters() != self._parameter_identity
                or self._configuration() != self._config_identity
                or self._methods() != self._method_identity
                or self._ropes() != self._rope_identity):
            raise RuntimeError("Model/configuration changed since adapter binding")
        if any(str(p.device) != "cpu" or (p.is_floating_point() and p.dtype != torch.float32)
               for p in self.model.parameters()):
            raise RuntimeError("Keep model weights CPU FP32; bound RoPE cast stays FP16")
        if self.model.forward_recurrent_lighter.__func__.__code__ is not self._original_code:
            raise RuntimeError("Model method changed")
        for m in self.model.modules():
            if "forward" in vars(m) or m._forward_hooks or m._forward_pre_hooks or m._backward_hooks:
                raise RuntimeError("Remove observation hooks; adapter owns checkpoints")
        global_module = torch.nn.modules.module
        if global_module._global_forward_hooks or global_module._global_forward_pre_hooks:
            raise RuntimeError("Global model hooks are unsupported")

    def _capture_runtime(self):
        import torch
        self._assert_runtime()
        result = {
            "buffers": {n: _clone_tree(v) for n, v in self.model.named_buffers()},
            "caches": {key: _clone_tree(getattr(obj, attr)) for key, (obj, attr) in self._caches.items()},
            "torch_cpu_rng": torch.get_rng_state().clone(),
            "python_rng": random.getstate(),
            "numpy_rng": None,
        }
        if "numpy" in sys.modules:
            result["numpy_rng"] = _clone_tree(sys.modules["numpy"].random.get_state())
        return result

    def _restore_runtime(self, runtime):
        import torch
        current = dict(self.model.named_buffers())
        if set(current) != set(runtime["buffers"]) or set(self._caches) != set(runtime["caches"]):
            raise RuntimeError("Runtime buffer/cache structure changed")
        for name, value in runtime["buffers"].items():
            current[name].copy_(value)
        for key, value in runtime["caches"].items():
            obj, attr = self._caches[key]
            setattr(obj, attr, _clone_tree(value))
        torch.set_rng_state(runtime["torch_cpu_rng"].clone())
        random.setstate(copy.deepcopy(runtime["python_rng"]))
        if runtime["numpy_rng"] is not None:
            if "numpy" not in sys.modules:
                raise RuntimeError("Numpy runtime disappeared")
            sys.modules["numpy"].random.set_state(_clone_tree(runtime["numpy_rng"]))

    def run(self, views, *, frame_ids, resume=None, fork_last=False):
        """Run complete normal statements, optionally fork the final write.

        `original_return` contains only this call's frames. Checkpoint indices
        and frame_ids are absolute. `fork_last` is one event, never a policy.
        Branches all share the final current head from this call. For H>=1 next
        frames, call run on the identical suffix with each branch as `resume`.
        """
        controller = _Controller(self, views, frame_ids, resume, fork_last)
        result = self._forward(self.model, views, device="cpu", ret_state=True, _s25=controller)
        if controller.checkpoint is None:
            raise RuntimeError("No complete end-of-frame checkpoint")
        return RunResult(result, controller.checkpoint, controller.branches,
                         controller.start_index, controller.final_index)
