"""Exact S35 constructor routed through the C2 gate, with S40 invariants."""
from __future__ import annotations

import ast
import copy
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


def manifest_from_verified_gate(gate):
    manifest = gate.get("manifest_snapshot")
    require(
        isinstance(manifest, dict)
        and manifest.get("output_root") == gate.get("output_root") == str(gate_api.C2_OUTPUT)
        and gate.get("manifest_path") == str(gate_api.PUBLISHED_MANIFEST),
        "C2 runtime requires the full gate's detached canonical manifest snapshot",
    )
    return copy.deepcopy(manifest)


def same_directory_identity(path, descriptor):
    by_path = os.stat(path, follow_symlinks=False)
    by_fd = os.fstat(descriptor)
    return (
        stat.S_ISDIR(by_path.st_mode)
        and (by_path.st_dev, by_path.st_ino) == (by_fd.st_dev, by_fd.st_ino)
    )


def atomic_save_runtime_receipt(receipt, record, output):
    """Publish via one stable output dirfd and a fixed O_EXCL/O_NOFOLLOW temp."""
    output = Path(output)
    receipt = Path(receipt)
    require(
        output == gate_api.C2_OUTPUT
        and receipt == output / "runtime_loading.json",
        "C2 runtime receipt path is not the frozen output-root record",
    )
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    directory_fd = os.open(output, directory_flags)
    temporary_name = ".runtime_loading.s47-c2.tmp"
    receipt_name = "runtime_loading.json"
    payload = (
        json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")
    temporary_fd = None
    try:
        require(same_directory_identity(output, directory_fd),
                "C2 output directory inode changed before runtime receipt staging")
        try:
            os.stat(temporary_name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise RuntimeError("Fixed C2 runtime receipt staging name is occupied")
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        temporary_fd = os.open(temporary_name, flags, 0o600, dir_fd=directory_fd)
        view = memoryview(payload)
        while view:
            written = os.write(temporary_fd, view)
            require(written > 0, "Short C2 runtime receipt write")
            view = view[written:]
        os.fsync(temporary_fd)
        staged = os.fstat(temporary_fd)
        require(stat.S_ISREG(staged.st_mode) and staged.st_size == len(payload),
                "C2 runtime receipt staging inode differs")
        try:
            current = os.stat(receipt_name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            current = None
        require(current is None or stat.S_ISREG(current.st_mode),
                "C2 runtime receipt destination is not a regular file")
        require(same_directory_identity(output, directory_fd),
                "C2 output directory inode changed before runtime receipt publication")
        os.close(temporary_fd)
        temporary_fd = None
        os.replace(
            temporary_name,
            receipt_name,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )
        os.fsync(directory_fd)
        published_fd = os.open(
            receipt_name,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
            dir_fd=directory_fd,
        )
        try:
            published = b""
            while True:
                chunk = os.read(published_fd, 1024 * 1024)
                if not chunk:
                    break
                published += chunk
            require(published == payload and json.loads(published) == record,
                    "Published C2 runtime receipt differs from staged bytes")
        finally:
            os.close(published_fd)
        require(same_directory_identity(output, directory_fd),
                "C2 output directory inode changed after runtime receipt publication")
    finally:
        if temporary_fd is not None:
            os.close(temporary_fd)
        os.close(directory_fd)


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
        and receipt_writer_sites == 1,
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
    }
    exec(compile(derived, str(FACTORY) + "[S47 C2 gate/labels]", "exec"), namespace)
    return namespace["create_runtime"]


def create_runtime(gate):
    gate_api.validate_gate(gate)
    runtime = derive_factory()(gate)
    manifest = manifest_from_verified_gate(gate)
    path = Path(manifest["output_root"]) / "runtime_loading.json"
    loading, _, _ = gate_api.read_json_snapshot(path, "C2 runtime loading receipt")
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
        loading.update(
            status="PASS_S47_C2_DECLARED_VARIANT_COMPONENT_LOADING_ONLY",
            row="C2",
            variant=gate_api.VARIANT,
            variant_invariants=checks,
            original_sd21_equivalence_verified=False,
            codec_numerics_verified=False,
            generation_completed=False,
        )
    except BaseException as error:
        loading.update(
            status="FAILED_S47_C2_DECLARED_VARIANT_INVARIANTS",
            row="C2",
            error_type=type(error).__name__,
            error=str(error),
        )
        raise
    finally:
        atomic_save_runtime_receipt(path, loading, Path(manifest["output_root"]))
    return runtime
