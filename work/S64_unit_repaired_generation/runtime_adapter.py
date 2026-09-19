"""Exact S35 constructor routed through the C2 gate, with S40 invariants."""
from __future__ import annotations

import ast
import builtins
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import stat

import generation_gate as gate_api


require, sha = gate_api.require, gate_api.sha
FACTORY = gate_api.ROOT / "work/S35_generation_integration/runtime_factory.py"
FACTORY_SHA256 = "a7f812717c053b401433bac423ba0a63028a9dc1874b1cba3c4fbca6c276e3d0"
LABELS = {
    "LOADING_REAL_COMPONENTS": "LOADING_C2_DECLARED_COMPONENT_VARIANT",
    "PASS_ORIGINAL_COMPONENT_LOADING_ONLY": "LOADED_C2_PENDING_VARIANT_INVARIANTS",
    "original_vae_local_directory": "declared_official_ft_mse_local_directory",
    "recorded_execution": "recorded_c2_component_variant_loading",
}
_RUNTIME_JOURNAL = {"count": 0, "last": None, "terminal": False}


def manifest_from_verified_gate(gate):
    manifest = gate.get("manifest_snapshot")
    require(
        isinstance(manifest, dict)
        and manifest.get("output_root") == gate.get("output_root") == str(gate_api.C2_OUTPUT)
        and gate.get("manifest_path") == str(gate_api.PUBLISHED_MANIFEST),
        "C2 runtime requires the full gate's detached canonical manifest snapshot",
    )
    return copy.deepcopy(manifest)


def _write_create_only_at(directory_fd, name, payload):
    flags = (
        os.O_WRONLY | os.O_CREAT | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor = os.open(name, flags, 0o600, dir_fd=directory_fd)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            require(written > 0, "Short C2 runtime journal write")
            view = view[written:]
        os.fchmod(descriptor, 0o444)
        os.fsync(descriptor)
        opened = os.fstat(descriptor)
        named = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        require(
            stat.S_ISREG(opened.st_mode)
            and (opened.st_dev, opened.st_ino) == (named.st_dev, named.st_ino)
            and opened.st_size == len(payload),
            "C2 runtime journal inode changed while its descriptor remained open",
        )
    finally:
        os.close(descriptor)
    os.fsync(directory_fd)
    return hashlib.sha256(payload).hexdigest()


def atomic_save_runtime_receipt(receipt, record, output, gate):
    """Append immutable evidence; create the terminal receipt directly with O_EXCL."""
    output = Path(output)
    receipt = Path(receipt)
    require(
        output == gate_api.C2_OUTPUT
        and receipt == output / "runtime_loading.json",
        "C2 runtime receipt path is not the frozen output-root record",
    )
    require(not _RUNTIME_JOURNAL["terminal"],
            "C2 runtime receipt was already terminally sealed")
    directory_fd = gate_api.duplicate_output_dirfd(gate)
    record = copy.deepcopy(record)
    record["row"] = gate_api.RUN_ROW
    record["retrieval_variant"] = gate_api.exact_retrieval_variant()
    payload = (
        json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")
    try:
        gate_api.validate_gate(gate)
        _RUNTIME_JOURNAL["count"] += 1
        event_name = "runtime_loading.event_%04d.json" % _RUNTIME_JOURNAL["count"]
        event_sha = _write_create_only_at(directory_fd, event_name, payload)
        terminal = (
            str(record.get("status", "")).startswith("FAILED_")
            or record.get("status") == "PASS_S47_C2_DECLARED_VARIANT_COMPONENT_LOADING_ONLY"
        )
        if terminal:
            terminal_sha = _write_create_only_at(
                directory_fd, "runtime_loading.json", payload
            )
            require(terminal_sha == event_sha,
                    "C2 terminal runtime receipt differs from its immutable event")
            _RUNTIME_JOURNAL["terminal"] = True
        _RUNTIME_JOURNAL["last"] = copy.deepcopy(record)
        gate_api.validate_gate(gate)
    finally:
        os.close(directory_fd)


def last_runtime_record():
    require(isinstance(_RUNTIME_JOURNAL["last"], dict),
            "C2 runtime factory did not append a loading record")
    return copy.deepcopy(_RUNTIME_JOURNAL["last"])


def _fd_file(gate, name, mode="rb"):
    descriptor = gate_api.duplicate_resource_fd(gate, name)
    if "b" in mode:
        return os.fdopen(descriptor, mode)
    return os.fdopen(descriptor, mode, encoding="utf-8")


def load_verified_config(omega_conf, gate):
    with _fd_file(gate, "config", "r") as handle:
        return omega_conf.load(handle)


def load_verified_input(loader, gate, *args, **kwargs):
    with _fd_file(gate, "input_image", "rb") as handle:
        return loader(handle, *args, **kwargs)


def safe_torch_load_from_fd(old_loader, gate, requested, args, kwargs):
    name = gate_api.resource_name_for_path(gate, Path(requested))
    require(name in {"vmem", "cut3r", "clip", "vae_weight"},
            "Torch loader requested a non-weight descriptor")
    with _fd_file(gate, name, "rb") as handle:
        return old_loader(handle, *args, **kwargs)


def install_verified_loader_patches(stack, gate, patch):
    """Route every component payload read to a duplicate of the verified FD."""
    import safetensors.torch as safetensors_torch

    old_open = builtins.open
    old_io_open = io.open
    old_isfile = os.path.isfile
    old_exists = os.path.exists
    old_isdir = os.path.isdir
    old_listdir = os.listdir
    old_path_is_file = Path.is_file
    old_path_exists = Path.exists
    old_safetensors_load_file = safetensors_torch.load_file
    resource_paths = {
        os.path.normpath(os.path.abspath(str(item["path"]))): name
        for name, item in gate["components"].items()
    }
    vae_directory = os.path.normpath(os.path.abspath(
        str(Path(gate["components"]["vae_config"]["path"]).parent)
    ))
    vae_children = {
        os.path.normpath(os.path.abspath(str(gate["components"][name]["path"])))
        for name in ("vae_config", "vae_weight")
    }

    def key_for(value):
        if not isinstance(value, (str, bytes, os.PathLike)):
            return None
        return os.path.normpath(os.path.abspath(os.fsdecode(value)))

    def under_vae(key):
        return key == vae_directory or (
            isinstance(key, str) and key.startswith(vae_directory + os.sep)
        )

    def bound_open(file, mode="r", *args, **kwargs):
        key = key_for(file)
        if key in resource_paths:
            require("r" in mode and not any(flag in mode for flag in "wax+"),
                    "Scientific resource descriptors are read-only")
            descriptor = gate_api.duplicate_resource_fd(gate, resource_paths[key])
            return os.fdopen(descriptor, mode, *args, **kwargs)
        require(not under_vae(key),
                "VAE directory loader requested an unbound child path")
        return old_open(file, mode, *args, **kwargs)

    def bound_io_open(file, mode="r", *args, **kwargs):
        key = key_for(file)
        if key in resource_paths:
            require("r" in mode and not any(flag in mode for flag in "wax+"),
                    "Scientific resource descriptors are read-only")
            descriptor = gate_api.duplicate_resource_fd(gate, resource_paths[key])
            return os.fdopen(descriptor, mode, *args, **kwargs)
        require(not under_vae(key),
                "VAE directory loader requested an unbound pathlib child path")
        return old_io_open(file, mode, *args, **kwargs)

    def bound_safetensors_load_file(filename, device="cpu"):
        name = gate_api.resource_name_for_path(gate, Path(filename))
        require(name in {"clip", "vae_weight"},
                "Safetensors loader requested an unbound component")
        descriptor = gate_api.duplicate_resource_fd(gate, name)
        try:
            return old_safetensors_load_file("/dev/fd/%d" % descriptor, device=device)
        finally:
            os.close(descriptor)

    def bound_isfile(path):
        key = key_for(path)
        return key in vae_children if under_vae(key) else old_isfile(path)

    def bound_exists(path):
        key = key_for(path)
        return (key == vae_directory or key in vae_children) if under_vae(key) else old_exists(path)

    def bound_isdir(path):
        key = key_for(path)
        return key == vae_directory if under_vae(key) else old_isdir(path)

    def bound_listdir(path="."):
        key = key_for(path)
        if key == vae_directory:
            return sorted(Path(item).name for item in vae_children)
        require(not under_vae(key), "VAE loader attempted to enumerate an unbound path")
        return old_listdir(path)

    def bound_path_is_file(path):
        key = key_for(path)
        return key in vae_children if under_vae(key) else old_path_is_file(path)

    def bound_path_exists(path):
        key = key_for(path)
        return (key == vae_directory or key in vae_children) if under_vae(key) else old_path_exists(path)

    stack.enter_context(patch.object(builtins, "open", bound_open))
    stack.enter_context(patch.object(io, "open", bound_io_open))
    stack.enter_context(patch.object(os.path, "isfile", bound_isfile))
    stack.enter_context(patch.object(os.path, "exists", bound_exists))
    stack.enter_context(patch.object(os.path, "isdir", bound_isdir))
    stack.enter_context(patch.object(os, "listdir", bound_listdir))
    stack.enter_context(patch.object(Path, "is_file", bound_path_is_file))
    stack.enter_context(patch.object(Path, "exists", bound_path_exists))
    stack.enter_context(patch.object(safetensors_torch, "load_file", bound_safetensors_load_file))


def derive_factory(*, compile_only=False):
    factory_bytes, _ = gate_api.verified_bytes(
        FACTORY, FACTORY_SHA256, "Original S35 runtime factory"
    )
    original = ast.parse(factory_bytes, filename=str(FACTORY))
    derived = copy.deepcopy(original)
    counts = {label: 0 for label in LABELS}
    imports = 0
    expected_seed_sites = {(74, 20), (74, 39), (74, 61), (78, 29)}
    seed_sites = set()
    manifest_snapshot_sites = 0
    receipt_writer_sites = 0
    config_loader_sites = 0
    torch_loader_sites = 0
    loader_patch_sites = 0
    input_loader_sites = 0
    hardening_originals = {}
    for node in ast.walk(derived):
        if isinstance(node, ast.ImportFrom) and node.module == "resource_gate":
            require(
                [(item.name, item.asname) for item in node.names]
                == [("validate_gate", None), ("require", None)],
                "Unexpected S35 resource-gate import",
            )
            node.module = "generation_gate"
            imports += 1
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in LABELS:
            counts[node.value] += 1
            node.value = LABELS[node.value]
        if (
            isinstance(node, ast.Constant)
            and type(node.value) is int
            and node.value == 42
            and (node.lineno, node.col_offset) in expected_seed_sites
        ):
            seed_sites.add((node.lineno, node.col_offset))
            node.value = 44
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "m"
            and node.lineno == 26
        ):
            manifest_snapshot_sites += 1
            hardening_originals["manifest"] = copy.deepcopy(node.value)
            node.value = ast.copy_location(
                ast.Call(
                    func=ast.Name(id="_manifest_from_verified_gate", ctx=ast.Load()),
                    args=[ast.Name(id="gate", ctx=ast.Load())],
                    keywords=[],
                ),
                node.value,
            )
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "config"
            and node.lineno == 75
        ):
            config_loader_sites += 1
            hardening_originals["config_loader"] = copy.deepcopy(node.value)
            node.value = ast.copy_location(
                ast.Call(
                    func=ast.Name(id="_load_verified_config", ctx=ast.Load()),
                    args=[ast.Name(id="OmegaConf", ctx=ast.Load()), ast.Name(id="gate", ctx=ast.Load())],
                    keywords=[],
                ),
                node.value,
            )
        if (
            isinstance(node, ast.Return)
            and node.lineno == 103
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "old_torch_load"
        ):
            torch_loader_sites += 1
            hardening_originals["torch_loader"] = copy.deepcopy(node.value)
            node.value = ast.copy_location(
                ast.Call(
                    func=ast.Name(id="_safe_torch_load_from_fd", ctx=ast.Load()),
                    args=[
                        ast.Name(id="old_torch_load", ctx=ast.Load()),
                        ast.Name(id="gate", ctx=ast.Load()),
                        ast.Name(id="f", ctx=ast.Load()),
                        ast.Name(id="args", ctx=ast.Load()),
                        ast.Name(id="kwargs", ctx=ast.Load()),
                    ],
                    keywords=[],
                ),
                node.value,
            )
        if isinstance(node, ast.With) and node.lineno == 126:
            loader_patch_sites += 1
            hardening_originals["with_body"] = copy.deepcopy(node.body)
            install = ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="_install_verified_loader_patches", ctx=ast.Load()),
                    args=[
                        ast.Name(id="stack", ctx=ast.Load()),
                        ast.Name(id="gate", ctx=ast.Load()),
                        ast.Name(id="patch", ctx=ast.Load()),
                    ],
                    keywords=[],
                )
            )
            node.body.insert(0, ast.copy_location(install, node.body[0]))
        if (
            isinstance(node, ast.Assign)
            and node.lineno == 138
            and len(node.targets) == 1
            and isinstance(node.targets[0], (ast.Tuple, ast.List))
            and isinstance(node.value, ast.Call)
        ):
            input_loader_sites += 1
            hardening_originals["input_loader"] = copy.deepcopy(node.value)
            original_call = node.value
            node.value = ast.copy_location(
                ast.Call(
                    func=ast.Name(id="_load_verified_input", ctx=ast.Load()),
                    args=[
                        ast.Name(id="load_img_and_K", ctx=ast.Load()),
                        ast.Name(id="gate", ctx=ast.Load()),
                        *copy.deepcopy(original_call.args[1:]),
                    ],
                    keywords=copy.deepcopy(original_call.keywords),
                ),
                original_call,
            )
        if isinstance(node, ast.FunctionDef) and node.name == "save" and node.lineno == 37:
            receipt_writer_sites += 1
            hardening_originals["save_body"] = copy.deepcopy(node.body)
            replacement = ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="_atomic_save_runtime_receipt", ctx=ast.Load()),
                    args=[
                        ast.Name(id="receipt", ctx=ast.Load()),
                        ast.Name(id="record", ctx=ast.Load()),
                        ast.Name(id="out", ctx=ast.Load()),
                        ast.Name(id="gate", ctx=ast.Load()),
                    ],
                    keywords=[],
                )
            )
            node.body = [ast.copy_location(replacement, node.body[0])]
    ast.fix_missing_locations(derived)
    require(
        imports == 1
        and all(count == 1 for count in counts.values())
        and seed_sites == expected_seed_sites
        and manifest_snapshot_sites == 1
        and receipt_writer_sites == 1
        and config_loader_sites == 1
        and torch_loader_sites == 1
        and loader_patch_sites == 1
        and input_loader_sites == 1,
        "Unexpected C2 runtime derivation edit count",
    )
    inverse = {value: key for key, value in LABELS.items()}
    restored = copy.deepcopy(derived)
    for node in ast.walk(restored):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "m"
            and node.lineno == 26
        ):
            node.value = copy.deepcopy(hardening_originals["manifest"])
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "config"
            and node.lineno == 75
        ):
            node.value = copy.deepcopy(hardening_originals["config_loader"])
        if isinstance(node, ast.Return) and node.lineno == 103:
            node.value = copy.deepcopy(hardening_originals["torch_loader"])
        if isinstance(node, ast.With) and node.lineno == 126:
            node.body = copy.deepcopy(hardening_originals["with_body"])
        if (
            isinstance(node, ast.Assign)
            and node.lineno == 138
            and len(node.targets) == 1
            and isinstance(node.targets[0], (ast.Tuple, ast.List))
        ):
            node.value = copy.deepcopy(hardening_originals["input_loader"])
        if isinstance(node, ast.FunctionDef) and node.name == "save" and node.lineno == 37:
            node.body = copy.deepcopy(hardening_originals["save_body"])
        if isinstance(node, ast.ImportFrom) and node.module == "generation_gate":
            node.module = "resource_gate"
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in inverse:
            node.value = inverse[node.value]
        if (
            isinstance(node, ast.Constant)
            and type(node.value) is int
            and node.value == 44
            and (node.lineno, node.col_offset) in expected_seed_sites
        ):
            node.value = 42
    require(
        ast.dump(restored, include_attributes=False) == ast.dump(original, include_attributes=False),
        "C2 runtime derivation changed the S35 factory beyond the declared reversible edits",
    )
    proof = {
        "parent_sha256": FACTORY_SHA256,
        "gate_import_routes": imports,
        "label_counts": counts,
        "seed_sites": sorted(seed_sites),
        "manifest_snapshot_sites": manifest_snapshot_sites,
        "stable_atomic_receipt_writer_sites": receipt_writer_sites,
        "same_fd_config_loader_sites": config_loader_sites,
        "same_fd_torch_loader_sites": torch_loader_sites,
        "same_fd_loader_patch_sites": loader_patch_sites,
        "same_fd_input_loader_sites": input_loader_sites,
        "reversible_full_AST_equal": True,
    }
    if compile_only:
        compile(derived, str(FACTORY) + "[S47 C2 gate/labels/security]", "exec")
        return proof
    namespace = {
        "__file__": str(FACTORY),
        "__name__": "_s47_c2_declared_factory",
        "_manifest_from_verified_gate": manifest_from_verified_gate,
        "_atomic_save_runtime_receipt": atomic_save_runtime_receipt,
        "_load_verified_config": load_verified_config,
        "_safe_torch_load_from_fd": safe_torch_load_from_fd,
        "_install_verified_loader_patches": install_verified_loader_patches,
        "_load_verified_input": load_verified_input,
    }
    exec(compile(derived, str(FACTORY) + "[S47 C2 gate/labels]", "exec"), namespace)
    return namespace["create_runtime"]


def install_verified_unit_hook(pipeline, gate, manifest):
    identities = manifest["source_identities"]
    variant = gate_api.exact_retrieval_variant()
    require(manifest.get("retrieval_variant") == variant, "S64 retrieval variant changed")
    hook = gate_api.execute_verified_module(
        "_s64_unit_renderer_hook", gate_api.UNIT_HOOK, identities[str(gate_api.UNIT_HOOK)]
    )
    adapter = gate_api.execute_verified_module(
        "_s64_canonical_unit_adapter", gate_api.UNIT_ADAPTER, identities[str(gate_api.UNIT_ADAPTER)]
    )
    original_path = gate_api.ROOT / "work/S20_environment/isolated_vmem_source/modeling/pipeline.py"
    original_sha = identities[str(original_path)]
    gate_api.verified_bytes(original_path, original_sha, "Original renderer source")
    bindings = dict(hook=copy.deepcopy(variant["hook"]), adapter=copy.deepcopy(variant["adapter"]),
                    original_renderer={"path": str(original_path), "sha256": original_sha})

    def save_unit_call(sequence, record):
        gate_api.validate_gate(gate)
        descriptor = gate_api.duplicate_output_dirfd(gate)
        try:
            record = copy.deepcopy(record)
            record.update(row=gate_api.RUN_ROW, manifest_sha256=gate["manifest_sha256"])
            payload = (json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
            _write_create_only_at(descriptor, "retrieval_unit_call_%04d.json" % sequence, payload)
        finally:
            os.close(descriptor)

    return hook.install_unit_renderer(pipeline, adapter.render_in_canonical_units,
                                      save_unit_call, variant, bindings)


def create_runtime(gate):
    gate_api.validate_gate(gate)
    runtime = derive_factory()(gate)
    manifest = manifest_from_verified_gate(gate)
    path = Path(manifest["output_root"]) / "runtime_loading.json"
    loading = last_runtime_record()
    try:
        import diffusers

        vae = runtime["pipeline"].vae
        module = vae.module
        checks = {
            "diffusers_version": diffusers.__version__,
            "use_tiling": module.use_tiling,
            "use_slicing": module.use_slicing,
            "sample_size": module.config.sample_size,
            "latent_channels": module.config.latent_channels,
            "wrapper_chunk_size": vae.chunk_size,
            "wrapper_scale_factor": vae.scale_factor,
            "wrapper_downsample": vae.downsample,
        }
        require(
            checks
            == {
                "diffusers_version": "0.32.2",
                "use_tiling": False,
                "use_slicing": False,
                "sample_size": 256,
                "latent_channels": 4,
                "wrapper_chunk_size": 1,
                "wrapper_scale_factor": 0.18215,
                "wrapper_downsample": 8,
            },
            "C2 declared VAE path differs from the reviewed S39/S40 invariant set",
        )
        require(
            loading.get("status") == "LOADED_C2_PENDING_VARIANT_INVARIANTS",
            "C2 factory did not finish its bounded component load",
        )
        loads = loading.get("state_dict_loads")
        require(
            isinstance(loads, list)
            and bool(loads)
            and all(
                isinstance(item, dict)
                and item.get("missing_keys") == []
                and item.get("unexpected_keys") == []
                and "strict_requested" in item
                for item in loads
            ),
            "One or more C2 state-dict attempts is incomplete",
        )
        gate_api.validate_gate(gate)
        hook_installation = install_verified_unit_hook(runtime["pipeline"], gate, manifest)
        loading.update(
            retrieval_variant=gate_api.exact_retrieval_variant(),
            retrieval_unit_hook=hook_installation,
            status="PASS_S47_C2_DECLARED_VARIANT_COMPONENT_LOADING_ONLY",
            row=gate_api.RUN_ROW,
            variant=gate_api.VARIANT,
            variant_invariants=checks,
            original_sd21_equivalence_verified=False,
            codec_numerics_verified=False,
            generation_completed=False,
        )
    except BaseException as error:
        loading.update(
            status="FAILED_S47_C2_DECLARED_VARIANT_INVARIANTS",
            row=gate_api.RUN_ROW,
            error_type=type(error).__name__,
            error=str(error),
        )
        raise
    finally:
        atomic_save_runtime_receipt(path, loading, Path(manifest["output_root"]), gate)
    return runtime
