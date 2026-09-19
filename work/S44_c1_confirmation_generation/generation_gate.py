"""C1 baseline-only generation gate derived from the sealed S40 resource path.

This standard-library gate separates reusable component-loading evidence from
the new, independently hashed C1 input.  It never calls a model or decodes an
image.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S39 = ROOT / "work/S39_component_variant"
BASE_S40 = ROOT / "work/S40_declared_variant_generation/review_attachment_01/manifest.json"
BASE_S40_SHA256 = "9951a78909a7d792dd536cea067c14e369cff776115a078d2f61c66c085cdebe"
S42_PROTOCOL = ROOT / "work/S42_baseline_failure_preregistration/PROTOCOL.md"
S42_PROTOCOL_SHA256 = "89fb44e0b77a85a66fe611cd2f885fed0288229cbb027e04da25fc0631507b3f"
C1_PROTOCOL = HERE / "PROTOCOL.md"
C1_PROTOCOL_SHA256 = "77c72263f6f58f77e5990a7db1557773013b9b84b14fb040f20faaaae6e701b5"
FREEZE_PROTOCOL = HERE / "FREEZE_PROTOCOL.md"
FREEZE_PROTOCOL_SHA256 = "aa103a3fa58f03a5969be754f5f55abba11d0f3966386d5a9c02445035e1defe"
C1_INPUT = Path("/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/test_samples/jesus.jpg")
C1_INPUT_SHA256 = "d611976bb9d3e8d6e1740b86ead24028bfd7857944eba118458e09e7e645f3e1"
C1_INPUT_BYTES = 663677
C1_ORIGINAL_SIZE = [1702, 1276]
C1_CONFIG = HERE / "inference_seed43.yaml"
C1_CONFIG_SHA256 = "2fb88eb0a15c449b876386df5c9c0d2aad8da43c6be5aeccbd9b8d72be1908aa"
C1_OUTPUT = ROOT / "results/S44_C1_confirmation_generation"
ATTACHMENT_ROOT = HERE / "review_attachment_01"
PUBLISHED_MANIFEST = ATTACHMENT_ROOT / "manifest.json"
PUBLISHED_RECEIPT = ATTACHMENT_ROOT / "receipt.json"
PUBLISHED_METADATA_GATE = ATTACHMENT_ROOT / "metadata_gate.json"
PINS = {
    "s39_variant_gate.py": "cf667bdc0bc43f902d0dca3041c4dbf33a53d908ee4e5d13ebfba2f853a78f4e",
    "load_components.py": "7b554276d5f00e6f14283a0c3a3d06bccda73b3c9dd2b6a9ef2514287732738e",
}
SCHEMA = "s44-c1-confirmation-two-batch-v1"
FROZEN = "FROZEN_C1_BASELINE_CONFIRMATION_TWO_BATCH_EXECUTION"
SOURCES = ("generation_gate.py", "runtime_adapter.py", "launch_generation.py", "PROTOCOL.md")
REVIEW_STATUSES = {
    "source_review": "PASS_S44_C1_GENERATION_SOURCE_REVIEW",
    "runtime_freeze": "READY_TO_ATTEMPT_S44_C1_BASELINE_GENERATION",
}
LIMITS = {
    "seconds_per_batch": 1800,
    "total_seconds": 3600,
    "rss_bytes": 45 * 1024**3,
    "minimum_free_bytes": 10 * 1024**3,
    "threads": 8,
    "poll_seconds": 0.5,
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def core_sha256(manifest):
    return hashlib.sha256(
        canonical({key: value for key, value in manifest.items() if key != "review_receipts"})
    ).hexdigest()


def bind_s39():
    for name, expected in PINS.items():
        require(sha(S39 / name) == expected, "Reviewed S39 source changed: " + name)
    path = S39 / "s39_variant_gate.py"
    spec = importlib.util.spec_from_file_location("_s44_c1_s39_gate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


S39_GATE = bind_s39()
VARIANT = S39_GATE.VARIANT
RUNTIME = S39_GATE.REF.RUNTIME
CONTROLS = copy.deepcopy(S39_GATE.REF.CONTROLS)
CONTROLS["seed"] = 43
require(
    {key for key in CONTROLS if CONTROLS[key] != S39_GATE.REF.CONTROLS[key]} == {"seed"}
    and S39_GATE.REF.CONTROLS["seed"] == 42,
    "C1 controls must differ from S40 only by seed 42 to 43",
)


def read_json_record(entry, label):
    require(
        isinstance(entry, dict) and set(entry) == {"path", "sha256"},
        label + " requires one actual path/SHA record",
    )
    path = Path(entry["path"])
    expected = entry["sha256"]
    require(
        path.is_absolute()
        and path.is_file()
        and isinstance(expected, str)
        and S39_GATE.REF.HEX.fullmatch(expected)
        and sha(path) == expected,
        label + " record is missing or changed",
    )
    return json.loads(path.read_text(encoding="utf-8"))


def read_base_s40():
    require(sha(BASE_S40) == BASE_S40_SHA256, "Sealed S40 manifest changed")
    base = json.loads(BASE_S40.read_text(encoding="utf-8"))
    require(
        base.get("schema") == "s40-declared-variant-two-batch-v1"
        and base.get("status") == "FROZEN_DECLARED_VARIANT_TWO_BATCH_EXECUTION"
        and base.get("variant") == VARIANT,
        "Sealed S40 parent identity differs",
    )
    return base


def required_sources():
    identities = S39_GATE.required_sources()
    for name in SOURCES:
        path = HERE / name
        require(path.is_file(), "Missing prepared C1 source: " + name)
        identities[str(path)] = sha(path)
    return identities


def exact_parent_bindings():
    return {
        "s40_manifest": {"path": str(BASE_S40), "sha256": BASE_S40_SHA256},
        "s42_preregistration": {"path": str(S42_PROTOCOL), "sha256": S42_PROTOCOL_SHA256},
    }


def exact_input_record():
    return {
        "path": str(C1_INPUT),
        "sha256": C1_INPUT_SHA256,
        "size_bytes": C1_INPUT_BYTES,
        "original_size": C1_ORIGINAL_SIZE,
        "scope": "Predeclared C1 JPEG bytes; full bytes hashed before model construction, pixels not decoded by gate",
    }


def exact_config_record():
    return {"path": str(C1_CONFIG), "sha256": C1_CONFIG_SHA256}


def require_single_seed_config_derivation(base):
    original_path = Path(base["config"]["path"])
    require(
        base["config"]["sha256"] == S39_GATE.REF.ORIGINAL_CONFIG_SHA
        and sha(original_path) == base["config"]["sha256"],
        "Sealed S40 inference config changed",
    )
    original = original_path.read_bytes()
    candidate = C1_CONFIG.read_bytes()
    require(
        original.count(b"seed: 42") == 1
        and b"seed: 43" not in original
        and candidate.rstrip(b"\n")
        == original.replace(b"seed: 42", b"seed: 43").rstrip(b"\n")
        and sha(C1_CONFIG) == C1_CONFIG_SHA256,
        "C1 inference config must be the S40 bytes with only seed 42 changed to 43",
    )


def exact_derivation_policy():
    return {
        "row": "C1",
        "base_row": "B0/S40",
        "allowed_scientific_differences": {
            "input_image": {"from": "changi.jpg", "to": "jesus.jpg"},
            "seed": {
                "from": 42,
                "to": 43,
                "surfaces": ["manifest.controls.seed", "inference_config.seed", "python_numpy_torch_rng"],
            },
        },
        "administrative_differences": [
            "output_root",
            "schema_and_status_labels",
            "row_specific_source_identities",
            "review_bindings",
            "timestamps",
        ],
        "all_other_generation_controls_equal": True,
        "scoring_or_visual_access_in_this_stage": False,
    }


def read_frozen(path, expected):
    require(
        isinstance(expected, str) and S39_GATE.REF.HEX.fullmatch(expected),
        "Frozen C1 manifest SHA required",
    )
    path = Path(path).resolve()
    require(path.is_file() and sha(path) == expected, "C1 manifest missing or changed")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    base = read_base_s40()
    require(
        manifest.get("schema") == SCHEMA
        and manifest.get("status") == FROZEN
        and manifest.get("evidence_kind") == "recorded_execution"
        and manifest.get("variant") == VARIANT,
        "A separately frozen C1 declared-variant manifest is required",
    )
    require(
        manifest.get("controls") == CONTROLS
        and manifest.get("runtime") == RUNTIME
        and manifest.get("generation_limits") == LIMITS,
        "C1 controls, runtime, or budgets changed",
    )
    require(
        {key: value for key, value in manifest["controls"].items() if key != "seed"}
        == {key: value for key, value in base["controls"].items() if key != "seed"},
        "C1 controls differ from S40 beyond the frozen seed",
    )
    require(
        manifest.get("components") == base.get("components")
        and manifest.get("config") == exact_config_record()
        and manifest.get("runtime") == base.get("runtime")
        and manifest.get("generation_limits") == base.get("generation_limits"),
        "C1 changed a sealed S40 component, config, runtime, or budget",
    )
    require_single_seed_config_derivation(base)
    require(
        manifest.get("input_image") == exact_input_record()
        and manifest.get("output_root") == str(C1_OUTPUT)
        and manifest.get("source_identities") == required_sources()
        and manifest.get("parent_bindings") == exact_parent_bindings()
        and manifest.get("derivation_policy") == exact_derivation_policy(),
        "C1 input, output, source domain, parent, or difference policy changed",
    )
    for key in (
        "s39_loading_manifest",
        "s39_resource_core_sha256",
        "s39_loading_evidence",
        "s39_loading_review",
    ):
        require(manifest.get(key) == base.get(key), "C1 changed sealed loading evidence: " + key)
    try:
        created = datetime.fromisoformat(manifest.get("created_utc", "").replace("Z", "+00:00"))
    except (TypeError, ValueError) as error:
        raise RuntimeError("C1 created_utc is not a valid timestamp") from error
    require(created.tzinfo is not None, "C1 created_utc must be timezone-aware")
    preparation = manifest.get("freeze_preparation", {})
    freeze_tool = HERE / "freeze_c1_manifest.py"
    require(
        preparation.get("schema") == "s44-c1-core-freeze-v1"
        and preparation.get("tool_source")
        == {"path": str(freeze_tool), "sha256": sha(freeze_tool)}
        and preparation.get("freeze_protocol")
        == {
            "path": str(HERE / "FREEZE_PROTOCOL.md"),
            "sha256": FREEZE_PROTOCOL_SHA256,
        }
        and preparation.get("base_s40") == exact_parent_bindings()["s40_manifest"]
        and preparation.get("s42_preregistration")
        == exact_parent_bindings()["s42_preregistration"]
        and preparation.get("component_bodies_read") == 0
        and preparation.get("pixels_decoded") == 0
        and preparation.get("scientific_imports") == 0
        and preparation.get("purpose")
        == "Await two separately authored reviews of the exact C1 baseline core",
        "C1 freeze-preparation record is incomplete or changed",
    )
    return manifest


def require_published_attachment(path, expected, manifest):
    """Bind executable manifests to the terminally successful attach bundle."""
    path = Path(path).resolve()
    require(path == PUBLISHED_MANIFEST, "Only the canonical C1 attached manifest is executable")
    require(PUBLISHED_RECEIPT.is_file(), "Successful C1 attachment receipt is absent")
    receipt = json.loads(PUBLISHED_RECEIPT.read_text(encoding="utf-8"))
    require(
        receipt.get("schema") == "s44-c1-freeze-tool-receipt-v1"
        and receipt.get("status") == "S44_C1_REVIEWS_ATTACHED_METADATA_GATE_PASSED"
        and receipt.get("mode") == "attach"
        and receipt.get("manifest_path") == str(PUBLISHED_MANIFEST)
        and receipt.get("manifest_sha256") == expected
        and receipt.get("core_sha256") == core_sha256(manifest)
        and receipt.get("review_receipts") == manifest.get("review_receipts")
        and receipt.get("tool_source_path") == str(HERE / "freeze_c1_manifest.py")
        and receipt.get("tool_source_sha256") == sha(HERE / "freeze_c1_manifest.py")
        and receipt.get("freeze_protocol_sha256") == FREEZE_PROTOCOL_SHA256
        and receipt.get("scientific_status") == "NOT_EVALUATED"
        and receipt.get("source_unchanged_at_close") is True
        and receipt.get("metadata_gate_status") == "PASS_METADATA_ONLY"
        and receipt.get("metadata_gate_path") == str(PUBLISHED_METADATA_GATE)
        and isinstance(receipt.get("metadata_gate_sha256"), str),
        "C1 attachment receipt does not authorize this exact manifest",
    )
    require(
        PUBLISHED_METADATA_GATE.is_file()
        and sha(PUBLISHED_METADATA_GATE) == receipt["metadata_gate_sha256"],
        "C1 attached metadata gate is absent or changed",
    )
    metadata = json.loads(PUBLISHED_METADATA_GATE.read_text(encoding="utf-8"))
    require(
        metadata.get("schema") == "s44-c1-generation-metadata-v1"
        and metadata.get("status") == "PASS_METADATA_ONLY"
        and metadata.get("manifest_sha256") == expected
        and metadata.get("execution_authorized") is False
        and metadata.get("unpublished_attachment_check") is True
        and metadata.get("attachment_receipt") is None,
        "C1 attached metadata gate does not bind this manifest",
    )
    try:
        completed = datetime.fromisoformat(receipt.get("completed_utc", "").replace("Z", "+00:00"))
    except (TypeError, ValueError) as error:
        raise RuntimeError("C1 attachment receipt timestamp is invalid") from error
    require(completed.tzinfo is not None, "C1 attachment receipt timestamp must be timezone-aware")
    return {
        "path": str(PUBLISHED_RECEIPT),
        "sha256": sha(PUBLISHED_RECEIPT),
        "status": receipt["status"],
    }


def loading_chain(manifest):
    base = read_base_s40()
    binding = manifest["s39_loading_manifest"]
    parent = read_json_record(binding, "S39 loading manifest")
    S39_GATE.check_manifest(binding["path"], binding["sha256"], metadata_only=True)
    require(
        manifest["s39_resource_core_sha256"] == S39_GATE.REF.core_sha256(parent)
        and parent["components"] == manifest["components"]
        and parent["config"] == base["config"]
        and manifest["config"] == exact_config_record(),
        "C1 component-loading parent differs from its reusable component scope or config derivation",
    )
    require_single_seed_config_derivation(base)
    require(
        parent["input_image"] == base["input_image"]
        and manifest["input_image"] != parent["input_image"],
        "C1 must separate the new input from the old component-loading input",
    )
    evidence = manifest["s39_loading_evidence"]
    require(
        set(evidence) == {"launch", "worker", "runtime_loading", "full_resource_gate"},
        "Four sealed S39 loading records are required",
    )
    records = {name: read_json_record(entry, "S39 " + name) for name, entry in evidence.items()}
    launch, worker, loading, full = (
        records[name] for name in ("launch", "worker", "runtime_loading", "full_resource_gate")
    )
    pending = "VARIANT_LOADING_RETURNED_PENDING_INDEPENDENT_REVIEW"
    for record in (launch, worker):
        require(
            record.get("status") == pending
            and record.get("manifest_sha256") == binding["sha256"]
            and record.get("source_sha256") == PINS["load_components.py"]
            and record.get("variant") == VARIANT
            and record.get("source_unchanged_at_close") is True,
            "Sealed S39 loading process identity differs",
        )
    require(
        launch.get("worker_spawned") is True
        and launch.get("returncode") == 0
        and not any(key in launch for key in ("limit_exceeded", "unexpected_live_descendants"))
        and launch.get("worker_receipt_sha256") == evidence["worker"]["sha256"]
        and launch.get("worker_status") == pending,
        "Sealed S39 external loading completion differs",
    )
    require(
        worker.get("runtime_factory_calls") == 1
        and worker.get("runtime_loading_sha256") == evidence["runtime_loading"]["sha256"]
        and worker.get("generation_calls") == 0
        and worker.get("encode_decode_calls_requested") == 0,
        "S39 evidence exceeds or misses component-loading scope",
    )
    require(
        loading.get("status") == "PASS_DECLARED_VARIANT_COMPONENT_LOADING_ONLY"
        and loading.get("manifest_sha256") == binding["sha256"]
        and loading.get("variant") == VARIANT
        and loading.get("variant_invariants") == worker.get("variant_invariants")
        and loading.get("network_attempts") == 0
        and loading.get("generation_completed") is False,
        "Sealed component-loading invariants differ",
    )
    loads = loading.get("state_dict_loads")
    require(
        isinstance(loads, list)
        and bool(loads)
        and loads == worker.get("state_dict_loads")
        and all(
            isinstance(item, dict)
            and item.get("missing_keys") == []
            and item.get("unexpected_keys") == []
            and "strict_requested" in item
            for item in loads
        )
        and all(
            not loading.get("vae_loading_info", {}).get(key)
            for key in ("missing_keys", "unexpected_keys", "mismatched_keys", "error_msgs")
        ),
        "Sealed component-loading state-dict or VAE evidence is incomplete",
    )
    require(
        full.get("manifest_sha256") == binding["sha256"]
        and full.get("manifest_path") == str(Path(binding["path"]).resolve()),
        "S39 full gate belongs to another manifest",
    )
    S39_GATE.validate_gate(full)
    review = read_json_record(manifest["s39_loading_review"], "S39 loading evidence review")
    require(
        review.get("status") == "PASS_S39_LOADING_EVIDENCE_REVIEW"
        and review.get("variant") == VARIANT
        and review.get("loading_manifest_sha256") == binding["sha256"]
        and review.get("resource_core_sha256") == manifest["s39_resource_core_sha256"]
        and review.get("evidence_sha256")
        == {name: entry["sha256"] for name, entry in evidence.items()},
        "Different-author S39 loading review is absent or unbound",
    )
    return parent


def check_manifest(path, expected, *, metadata_only=False, _allow_unpublished_attachment=False):
    path = Path(path).resolve()
    require(
        not _allow_unpublished_attachment or metadata_only,
        "An unpublished attachment may be checked only as metadata",
    )
    manifest = read_frozen(path, expected)
    attachment = None
    if not _allow_unpublished_attachment:
        attachment = require_published_attachment(path, expected, manifest)
    loading_chain(manifest)
    reviews = manifest.get("review_receipts", {})
    require(set(reviews) == set(REVIEW_STATUSES), "Two exact C1 reviews are required")
    core = core_sha256(manifest)
    core_path = HERE / "freeze_attempt_01/manifest_core.json"
    require(core_path.is_file(), "Frozen C1 core is absent")
    core_file_sha = sha(core_path)
    reviewer_roles = []
    for role, status in REVIEW_STATUSES.items():
        review = read_json_record(reviews[role], "C1 " + role)
        require(
            review.get("schema") == "s44-c1-generation-core-review-v1"
            and review.get("status") == status
            and review.get("variant") == VARIANT
            and review.get("row") == "C1"
            and review.get("core_path") == str(core_path)
            and review.get("core_file_sha256") == core_file_sha
            and review.get("core_sha256") == core,
            "C1 review does not approve this exact core: " + role,
        )
        require(
            review.get("author_role") == "/root"
            and isinstance(review.get("reviewer_role"), str)
            and review["reviewer_role"] != "/root"
            and review.get("executed") is False
            and review.get("model_or_scientific_imports") == 0
            and review.get("pixels_decoded") == 0
            and review.get("blocking_findings") == [],
            "C1 review execution or independence boundary differs: " + role,
        )
        reviewer_roles.append(review["reviewer_role"])
    require(len(set(reviewer_roles)) == 2, "C1 reviews require two distinct non-root roles")
    for filename, digest in manifest["source_identities"].items():
        require(sha(filename) == digest, "Changed C1 generation source: " + filename)
    require(
        C1_INPUT.is_file() and C1_INPUT.stat().st_size == C1_INPUT_BYTES,
        "C1 input path or byte count differs",
    )
    require(C1_CONFIG.is_file(), "C1 seed-43 inference config is missing")
    if metadata_only:
        return {
            "schema": "s44-c1-generation-metadata-v1",
            "status": "PASS_METADATA_ONLY",
            "variant": VARIANT,
            "row": "C1",
            "manifest_sha256": expected,
            "execution_authorized": False,
            "unpublished_attachment_check": _allow_unpublished_attachment,
            "component_bodies_read": 0,
            "input_body_read": 0,
            "config_body_bytes_read": C1_CONFIG.stat().st_size,
            "attachment_receipt": attachment,
            "scope": "Sealed parents, source/review hashes, exact small config derivation, paths and input size only; worker component/input full hashes remain",
        }
    full = S39_GATE.check_manifest(
        manifest["s39_loading_manifest"]["path"],
        manifest["s39_loading_manifest"]["sha256"],
    )
    require(sha(C1_INPUT) == C1_INPUT_SHA256, "C1 input full SHA-256 differs")
    require_single_seed_config_derivation(read_base_s40())
    return {
        "schema": "s44-c1-generation-resource-gate-v1",
        "status": "PASS_C1_DECLARED_GENERATION_RESOURCE_GATE",
        "manifest_path": str(Path(path).resolve()),
        "manifest_sha256": expected,
        "variant": VARIANT,
        "row": "C1",
        "components": full["components"],
        "controls": manifest["controls"],
        "source_identities": manifest["source_identities"],
        "config": exact_config_record(),
        "input_image": exact_input_record(),
        "attachment_receipt": attachment,
        "s39_full_gate": full,
        "evidence_kind": "recorded_execution",
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "identity_scope": "Declared official-ft-mse variant with separately hashed C1 input; not exact original SD2.1",
    }


def validate_gate(gate):
    require(
        isinstance(gate, dict)
        and gate.get("schema") == "s44-c1-generation-resource-gate-v1"
        and gate.get("status") == "PASS_C1_DECLARED_GENERATION_RESOURCE_GATE"
        and gate.get("variant") == VARIANT
        and gate.get("row") == "C1",
        "A completed C1 full resource gate is required",
    )
    manifest = read_frozen(gate["manifest_path"], gate["manifest_sha256"])
    require(
        gate.get("controls") == manifest["controls"]
        and gate.get("source_identities") == manifest["source_identities"]
        and gate.get("config") == manifest["config"]
        and gate.get("input_image") == manifest["input_image"]
        and gate.get("components") == gate.get("s39_full_gate", {}).get("components"),
        "C1 gate data changed",
    )
    S39_GATE.validate_gate(gate["s39_full_gate"])
    require(
        gate["s39_full_gate"]["manifest_sha256"] == manifest["s39_loading_manifest"]["sha256"],
        "C1 gate has another component-loading parent",
    )
    require(sha(C1_INPUT) == C1_INPUT_SHA256, "C1 input changed before/after loading")
    require_single_seed_config_derivation(read_base_s40())
    check_manifest(gate["manifest_path"], gate["manifest_sha256"], metadata_only=True)
    return gate
