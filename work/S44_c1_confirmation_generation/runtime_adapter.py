"""Exact S35 constructor routed through the C1 gate, with S40 invariants."""
from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import generation_gate as gate_api


require, sha = gate_api.require, gate_api.sha
FACTORY = gate_api.ROOT / "work/S35_generation_integration/runtime_factory.py"
FACTORY_SHA256 = "a7f812717c053b401433bac423ba0a63028a9dc1874b1cba3c4fbca6c276e3d0"
LABELS = {
    "LOADING_REAL_COMPONENTS": "LOADING_C1_DECLARED_COMPONENT_VARIANT",
    "PASS_ORIGINAL_COMPONENT_LOADING_ONLY": "LOADED_C1_PENDING_VARIANT_INVARIANTS",
    "original_vae_local_directory": "declared_official_ft_mse_local_directory",
    "recorded_execution": "recorded_c1_component_variant_loading",
}


def derive_factory():
    require(sha(FACTORY) == FACTORY_SHA256, "Original S35 runtime factory changed")
    original = ast.parse(FACTORY.read_text(encoding="utf-8"), filename=str(FACTORY))
    derived = copy.deepcopy(original)
    counts = {label: 0 for label in LABELS}
    imports = 0
    expected_seed_sites = {(74, 20), (74, 39), (74, 61), (78, 29)}
    seed_sites = set()
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
            node.value = 43
    require(
        imports == 1
        and all(count == 1 for count in counts.values())
        and seed_sites == expected_seed_sites,
        "Unexpected C1 runtime derivation edit count",
    )
    inverse = {value: key for key, value in LABELS.items()}
    restored = copy.deepcopy(derived)
    for node in ast.walk(restored):
        if isinstance(node, ast.ImportFrom) and node.module == "generation_gate":
            node.module = "resource_gate"
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in inverse:
            node.value = inverse[node.value]
        if (
            isinstance(node, ast.Constant)
            and type(node.value) is int
            and node.value == 43
            and (node.lineno, node.col_offset) in expected_seed_sites
        ):
            node.value = 42
    require(
        ast.dump(restored, include_attributes=False) == ast.dump(original, include_attributes=False),
        "C1 runtime derivation changed the S35 factory beyond the gate route, four labels, and four seed constants",
    )
    namespace = {"__file__": str(FACTORY), "__name__": "_s44_c1_declared_factory"}
    exec(compile(derived, str(FACTORY) + "[S44 C1 gate/labels]", "exec"), namespace)
    return namespace["create_runtime"]


def create_runtime(gate):
    gate_api.validate_gate(gate)
    runtime = derive_factory()(gate)
    manifest = json.loads(Path(gate["manifest_path"]).read_text(encoding="utf-8"))
    path = Path(manifest["output_root"]) / "runtime_loading.json"
    loading = json.loads(path.read_text(encoding="utf-8"))
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
            "C1 declared VAE path differs from the reviewed S39/S40 invariant set",
        )
        require(
            loading.get("status") == "LOADED_C1_PENDING_VARIANT_INVARIANTS",
            "C1 factory did not finish its bounded component load",
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
            "One or more C1 state-dict attempts is incomplete",
        )
        gate_api.validate_gate(gate)
        loading.update(
            status="PASS_S44_C1_DECLARED_VARIANT_COMPONENT_LOADING_ONLY",
            row="C1",
            variant=gate_api.VARIANT,
            variant_invariants=checks,
            original_sd21_equivalence_verified=False,
            codec_numerics_verified=False,
            generation_completed=False,
        )
    except BaseException as error:
        loading.update(
            status="FAILED_S44_C1_DECLARED_VARIANT_INVARIANTS",
            row="C1",
            error_type=type(error).__name__,
            error=str(error),
        )
        raise
    finally:
        temporary = path.with_suffix(".s44-c1.tmp")
        temporary.write_text(
            json.dumps(loading, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
    return runtime
