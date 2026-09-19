"""C2 baseline-only generation gate derived from the sealed S40 resource path.

This standard-library gate separates reusable component-loading evidence from
the new, independently hashed C2 input.  It never calls a model or decodes an
image.
"""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import builtins
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from types import ModuleType, SimpleNamespace


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S39 = ROOT / "work/S39_component_variant"
BASE_S40 = ROOT / "work/S40_declared_variant_generation/review_attachment_01/manifest.json"
BASE_S40_SHA256 = "9951a78909a7d792dd536cea067c14e369cff776115a078d2f61c66c085cdebe"
S42_PROTOCOL = ROOT / "work/S42_baseline_failure_preregistration/PROTOCOL.md"
S42_PROTOCOL_SHA256 = "89fb44e0b77a85a66fe611cd2f885fed0288229cbb027e04da25fc0631507b3f"
C2_PROTOCOL = HERE / "PROTOCOL.md"
C2_PROTOCOL_SHA256 = "93b40a8e9d94b80cbfbd80d5da680ce417a010faac6b18649ed0f0f0e6d45031"
FREEZE_PROTOCOL = HERE / "FREEZE_PROTOCOL.md"
FREEZE_PROTOCOL_SHA256 = "f5a4607218f3742467386822de5e1688c3838805ccac49609220729677ac55bd"
C2_INPUT = Path("/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/test_samples/living_room.jpg")
C2_INPUT_SHA256 = "e9d718849d2ddbe5dda7ed3fa80df7d93e99f2d509b07a46019818c2e188d278"
C2_INPUT_BYTES = 536341
C2_ORIGINAL_SIZE = [1588, 958]
C2_CONFIG = HERE / "inference_seed44.yaml"
C2_CONFIG_SHA256 = "90871e1df4d0569f52a8baa7919f66000ec2f1a4f9a9275a2e4fbe384a6a07b9"
C2_OUTPUT = ROOT / "results/S47_C2_confirmation_generation"
ATTACHMENT_ROOT = HERE / "review_attachment_01"
PUBLISHED_MANIFEST = ATTACHMENT_ROOT / "manifest.json"
PUBLISHED_RECEIPT = ATTACHMENT_ROOT / "receipt.json"
PUBLISHED_METADATA_GATE = ATTACHMENT_ROOT / "metadata_gate.json"
AUTHORIZATION_TOOL = HERE / "create_launch_authorization.py"
LAUNCH_AUTHORIZATION = HERE / "launch_authorization_01.json"
AUTHORIZATION_ATTEMPT = HERE / "launch_authorization_attempt_01"
AUTHORIZATION_ATTEMPT_RECEIPT = AUTHORIZATION_ATTEMPT / "success_receipt.json"
ATTACH_PREFLIGHT_ROOT = HERE / ".review_attachment_01.preflight"
ATTACH_PREFLIGHT_MANIFEST = ATTACH_PREFLIGHT_ROOT / "manifest.json"
PREPARE_STAGING_LEASE = HERE / ".freeze_attempt_01.staging"
ATTACH_STAGING_LEASE = HERE / ".review_attachment_01.staging"
FINAL_REVIEW_PATHS = {
    "final_attachment": HERE / "FINAL_ATTACHMENT_REVIEW.json",
    "launch_readiness": HERE / "LAUNCH_READINESS_REVIEW.json",
}
FINAL_REVIEW_STATUSES = {
    "final_attachment": "PASS_S47_C2_FINAL_ATTACHMENT_REVIEW",
    "launch_readiness": "READY_TO_LAUNCH_S47_C2_SINGLE_ATTEMPT",
}
FINAL_REVIEW_SCHEMA = "s47-c2-final-launch-review-v1"
AUTHORIZATION_SCHEMA = "s47-c2-launch-authorization-v1"
AUTHORIZATION_STATUS = "AUTHORIZED_S47_C2_SINGLE_ATTEMPT"
PINS = {
    "s39_variant_gate.py": "cf667bdc0bc43f902d0dca3041c4dbf33a53d908ee4e5d13ebfba2f853a78f4e",
    "load_components.py": "7b554276d5f00e6f14283a0c3a3d06bccda73b3c9dd2b6a9ef2514287732738e",
}
SCHEMA = "s47-c2-confirmation-two-batch-v1"
FROZEN = "FROZEN_C2_BASELINE_CONFIRMATION_TWO_BATCH_EXECUTION"
SOURCES = (
    "generation_gate.py",
    "runtime_adapter.py",
    "launch_generation.py",
    "create_launch_authorization.py",
    "PROTOCOL.md",
)
REVIEW_STATUSES = {
    "source_review": "PASS_S47_C2_GENERATION_SOURCE_REVIEW",
    "runtime_freeze": "READY_TO_ATTEMPT_S47_C2_BASELINE_GENERATION",
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
    digest, _ = hash_regular_file(Path(path).absolute(), "Bound file")
    return digest


def hash_regular_file(path, label):
    """Stream one regular file through one stable no-follow descriptor."""
    path = Path(path)
    require(path.is_absolute(), label + " path must be absolute")
    flags = (os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
             | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        require(stat.S_ISREG(before.st_mode), label + " must be a regular file")
        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            total += len(chunk)
        after = os.fstat(descriptor)
        require(
            (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
            == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
            and total == before.st_size,
            label + " changed while its descriptor was open",
        )
        identity = {
            "device": before.st_dev,
            "inode": before.st_ino,
            "size": before.st_size,
            "mode": stat.S_IMODE(before.st_mode),
            "mtime_ns": before.st_mtime_ns,
            "ctime_ns": before.st_ctime_ns,
        }
        return digest.hexdigest(), identity
    finally:
        os.close(descriptor)


def read_regular_snapshot(path, label):
    """Return bytes and stable identity from one O_NOFOLLOW descriptor."""
    path = Path(path)
    require(path.is_absolute(), label + " path must be absolute")
    flags = (os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
             | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        require(stat.S_ISREG(before.st_mode), label + " must be a regular file")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
        before_identity = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        after_identity = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        payload = b"".join(chunks)
        require(before_identity == after_identity and len(payload) == before.st_size,
                label + " changed while its descriptor was open")
        identity = {
            "device": before.st_dev,
            "inode": before.st_ino,
            "size": before.st_size,
            "mode": stat.S_IMODE(before.st_mode),
            "mtime_ns": before.st_mtime_ns,
            "ctime_ns": before.st_ctime_ns,
        }
        return payload, identity
    finally:
        os.close(descriptor)


def verified_bytes(path, expected, label):
    payload, identity = read_regular_snapshot(Path(path).absolute(), label)
    require(
        isinstance(expected, str)
        and len(expected) == 64
        and hashlib.sha256(payload).hexdigest() == expected,
        label + " SHA-256 differs",
    )
    return payload, identity


def read_json_snapshot(path, label, expected=None):
    if expected is None:
        payload, identity = read_regular_snapshot(Path(path).absolute(), label)
    else:
        payload, identity = verified_bytes(path, expected, label)
    try:
        document = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError(label + " is not valid UTF-8 JSON") from error
    return document, hashlib.sha256(payload).hexdigest(), identity


def execute_verified_module(name, path, expected, *, builtins_override=None):
    """Execute exactly the source snapshot whose bytes satisfy expected."""
    payload, _ = verified_bytes(path, expected, "Bound source " + str(path))
    module = ModuleType(name)
    module.__file__ = str(Path(path).absolute())
    module.__package__ = ""
    if builtins_override is not None:
        module.__dict__["__builtins__"] = builtins_override
    sys.modules[name] = module
    try:
        exec(compile(payload, str(path), "exec", dont_inherit=True), module.__dict__)
    except BaseException:
        if sys.modules.get(name) is module:
            del sys.modules[name]
        raise
    return module


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def core_sha256(manifest):
    return hashlib.sha256(
        canonical({key: value for key, value in manifest.items() if key != "review_receipts"})
    ).hexdigest()


def parse_utc(value, label):
    require(isinstance(value, str) and value, label + " must be a timestamp string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise RuntimeError(label + " is not a valid timestamp") from error
    require(
        parsed.tzinfo is not None and parsed.utcoffset() == timedelta(0),
        label + " must be timezone-aware UTC",
    )
    return parsed


def validate_launch_review(review, kind, bindings, attachment_completed_utc):
    require(kind in FINAL_REVIEW_STATUSES, "Unknown C2 terminal review kind")
    require(
        isinstance(review, dict)
        and review.get("schema") == FINAL_REVIEW_SCHEMA
        and review.get("review_kind") == kind
        and review.get("status") == FINAL_REVIEW_STATUSES[kind]
        and review.get("author_role") == "/root"
        and isinstance(review.get("reviewer_role"), str)
        and bool(review["reviewer_role"])
        and review["reviewer_role"] != "/root"
        and review.get("bindings") == bindings
        and review.get("executed") is False
        and review.get("model_or_scientific_imports") == 0
        and review.get("pixels_decoded") == 0
        and review.get("generation_calls") == 0
        and review.get("blocking_findings") == []
        and review.get("quality_status") == "NOT_EVALUATED"
        and review.get("method_or_novelty_status") == "NOT_EVALUATED",
        "C2 terminal review is incomplete, overclaims, or binds another bundle: " + kind,
    )
    attached = parse_utc(attachment_completed_utc, "C2 attachment completed_utc")
    reviewed = parse_utc(review.get("reviewed_utc"), kind + " reviewed_utc")
    require(attached < reviewed, kind + " review was not completed after attachment")
    return reviewed


def build_launch_authorization_document(
    *,
    bindings,
    attachment_completed_utc,
    review_documents,
    review_hashes,
    created_utc,
    tool_sha256,
):
    require(
        set(bindings)
        == {
            "manifest_sha256",
            "core_file_sha256",
            "core_sha256",
            "attachment_receipt_sha256",
            "metadata_gate_sha256",
        }
        and all(isinstance(value, str) and len(value) == 64 for value in bindings.values()),
        "C2 launch authorization requires five exact SHA-256 bindings",
    )
    require(
        set(review_documents) == set(FINAL_REVIEW_STATUSES)
        and set(review_hashes) == set(FINAL_REVIEW_STATUSES)
        and all(isinstance(value, str) and len(value) == 64 for value in review_hashes.values()),
        "C2 launch authorization requires both exact terminal review hashes",
    )
    times = {
        kind: validate_launch_review(
            review_documents[kind], kind, bindings, attachment_completed_utc
        )
        for kind in FINAL_REVIEW_STATUSES
    }
    roles = [review_documents[kind]["reviewer_role"] for kind in FINAL_REVIEW_STATUSES]
    require(len(set(roles)) == 2, "C2 terminal reviews require two distinct non-root roles")
    created = parse_utc(created_utc, "C2 launch authorization created_utc")
    require(all(reviewed < created for reviewed in times.values()),
            "C2 launch authorization must be created strictly after both reviews")
    require(isinstance(tool_sha256, str) and len(tool_sha256) == 64,
            "C2 authorization tool SHA-256 is malformed")
    review_refs = {
        kind: {
            "path": str(FINAL_REVIEW_PATHS[kind]),
            "sha256": review_hashes[kind],
            "status": FINAL_REVIEW_STATUSES[kind],
            "reviewed_utc": review_documents[kind]["reviewed_utc"],
            "reviewer_role": review_documents[kind]["reviewer_role"],
        }
        for kind in FINAL_REVIEW_STATUSES
    }
    return {
        "schema": AUTHORIZATION_SCHEMA,
        "status": AUTHORIZATION_STATUS,
        "created_utc": created_utc,
        "author_role": "/root",
        "row": "C2",
        "tool_source": {"path": str(AUTHORIZATION_TOOL), "sha256": tool_sha256},
        "bindings": copy.deepcopy(bindings),
        "attachment_completed_utc": attachment_completed_utc,
        "reviews": review_refs,
        "single_attempt_only": True,
        "execution_directory": str(HERE / "execution_01"),
        "output_root": str(C2_OUTPUT),
        "executed": False,
        "model_or_scientific_imports": 0,
        "pixels_decoded": 0,
        "generation_calls": 0,
        "quality_status": "NOT_EVALUATED",
        "method_or_novelty_status": "NOT_EVALUATED",
        "blocking_findings": [],
        "authorization_effect": "Permit one separately monitored attempt of the exact attached C2 baseline; no completion or scientific claim",
    }


def bind_s39():
    for name, expected in PINS.items():
        require(sha(S39 / name) == expected, "Reviewed S39 source changed: " + name)
    s39_path = S39 / "s39_variant_gate.py"
    s35_gate_path = ROOT / "work/S35_generation_integration/resource_gate.py"
    s35_gate_sha = "c949f85573b8fa23db59c8782354608cb6ca1334ea782712fcd9c334337df759"

    class SnapshotLoader:
        def create_module(self, spec):
            return None

        def exec_module(self, target):
            payload, _ = verified_bytes(
                s35_gate_path, s35_gate_sha, "Pinned S35 resource-gate source"
            )
            target.__file__ = str(s35_gate_path)
            exec(compile(payload, str(s35_gate_path), "exec", dont_inherit=True), target.__dict__)

    class SnapshotImportUtil:
        @staticmethod
        def spec_from_file_location(name, path):
            require(Path(path) == s35_gate_path,
                    "S39 attempted to load an unexpected helper source")
            return SimpleNamespace(name=name, loader=SnapshotLoader())

        @staticmethod
        def module_from_spec(spec):
            target = ModuleType(spec.name)
            target.__file__ = str(s35_gate_path)
            target.__package__ = ""
            sys.modules[spec.name] = target
            return target

    real_import = builtins.__import__
    proxy = SimpleNamespace(util=SnapshotImportUtil())

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "importlib.util":
            return proxy
        return real_import(name, globals, locals, fromlist, level)

    safe_builtins = dict(vars(builtins))
    safe_builtins["__import__"] = guarded_import
    module = execute_verified_module(
        "_s47_c2_s39_gate", s39_path, PINS["s39_variant_gate.py"],
        builtins_override=safe_builtins,
    )
    module.sha = sha

    def safe_read_manifest(path, expected):
        path = Path(path)
        require(path.is_absolute(), "S39 frozen manifest path must be absolute")
        document, _, _ = read_json_snapshot(path, "S39 frozen manifest", expected)
        require(
            document.get("schema") == module.SCHEMA
            and document.get("variant") == module.VARIANT,
            "Explicit named component variant is required; never original identity",
        )
        return path, document

    module.read_manifest = safe_read_manifest

    def safe_stat_record(path):
        path = Path(path)
        current = os.stat(path, follow_symlinks=False)
        module.require(stat.S_ISREG(current.st_mode), "S39 component is not a regular file")
        return {
            "path": str(path),
            "size": current.st_size,
            "mtime_ns": current.st_mtime_ns,
            "device": current.st_dev,
            "inode": current.st_ino,
        }

    def safe_same_stat(record):
        try:
            current = safe_stat_record(record["path"])
        except (KeyError, OSError, TypeError, module.REF.NotReady):
            return False
        return all(current[key] == record.get(key) for key in current)

    def safe_ref_required_sources():
        """Rebuild the inherited S35 source domain from one manifest snapshot.

        The sealed S35 helper hashes its source manifest and then opens that
        pathname again to parse it.  V4 replaces that transitive call as well:
        the expected hash and JSON parse apply to the same bytes read through
        one no-follow descriptor.
        """
        source_manifest, _, _ = read_json_snapshot(
            module.REF.S20_MANIFEST,
            "Pinned S20 source manifest",
            module.REF.S20_MANIFEST_SHA,
        )
        files = source_manifest.get("source_files")
        module.require(isinstance(files, list) and bool(files),
                       "Pinned S20 source manifest has no source files")
        result = {}
        for entry in files:
            module.require(
                isinstance(entry, dict)
                and isinstance(entry.get("path"), str)
                and bool(entry["path"])
                and not Path(entry["path"]).is_absolute()
                and ".." not in Path(entry["path"]).parts
                and isinstance(entry.get("final_sha256"), str)
                and module.REF.HEX.fullmatch(entry["final_sha256"]),
                "Pinned S20 source-manifest entry is malformed",
            )
            source_path = module.REF.SOURCE / entry["path"]
            key = str(source_path)
            module.require(key not in result, "Duplicate pinned S20 source path")
            result[key] = entry["final_sha256"]
        result[str(module.REF.S20_MANIFEST)] = module.REF.S20_MANIFEST_SHA
        result[str(module.REF.ROOT / "src/s20_generation_trace.py")] = module.REF.S20_TRACE_SHA
        for name in (
            "resource_gate.py",
            "runtime_factory.py",
            "integrate_original.py",
            "archive_outputs.py",
            "launch_original.py",
        ):
            source_path = module.REF.HERE / name
            result[str(source_path)] = sha(source_path)
        return result

    # Replace every inherited source-domain primitive that could otherwise
    # hash one pathname and parse/open it again through the sealed S35 helper.
    module.REF.sha = sha
    module.REF.stat_record = safe_stat_record
    module.REF.same_stat = safe_same_stat
    module.REF.required_sources = safe_ref_required_sources

    def safe_check_manifest(path, expected, *, metadata_only=False):
        path, manifest = safe_read_manifest(path, expected)
        module.require(manifest.get("status") == module.FROZEN,
                       "Draft is not authorization to load")
        module.require(
            manifest.get("controls") == module.REF.CONTROLS
            and manifest.get("loading_limits") == module.LIMITS,
            "Inherited scientific settings or bounded loading budget changed",
        )
        module.require(manifest.get("runtime") == module.RUNTIME,
                       "Wrong virtualenv or import order")
        module.require(
            isinstance(manifest.get("output_root"), str)
            and Path(manifest["output_root"]).is_absolute(),
            "Fresh absolute variant output root required",
        )
        components = manifest.get("components", {})
        module.require(set(components) == module.REF.ROLES,
                       "All five component files required")
        records = {}
        for role in sorted(module.REF.ROLES):
            item = components[role]
            module.require(
                isinstance(item, dict)
                and (item.get("size"), item.get("sha256")) == module.PUBLISHED[role],
                "Wrong published component identity: " + role,
            )
            raw = item.get("path")
            module.require(isinstance(raw, str) and Path(raw).is_absolute(),
                           "Missing absolute local component: " + role)
            record = safe_stat_record(Path(raw))
            module.require(record["size"] == item["size"],
                           "Missing/incomplete component: " + role)
            records[role] = dict(record, sha256=item["sha256"])
        vae_config = Path(components["vae_config"]["path"])
        vae_weight = Path(components["vae_weight"]["path"])
        directory = vae_config.parent
        module.require(
            vae_config.name == "config.json"
            and vae_weight.name == "diffusion_pytorch_model.safetensors"
            and vae_weight.parent == directory,
            "One exact official VAE directory required",
        )
        directory_entries = set()
        for entry in directory.iterdir():
            entry_stat = os.stat(entry, follow_symlinks=False)
            if stat.S_ISREG(entry_stat.st_mode):
                directory_entries.add(entry.name)
        module.require(
            directory_entries == {"config.json", "diffusion_pytorch_model.safetensors"},
            "Ambiguous alternate VAE files",
        )
        source_ids = manifest.get("source_identities", {})
        module.require(source_ids == module.required_sources(),
                       "Exact inherited and variant source domain required")
        evidence = manifest.get("review_receipts", {})
        module.require(set(evidence) == set(module.REVIEW_STATUSES),
                       "Two real reviews of this variant core required")
        small = dict(source_ids)
        for entry in evidence.values():
            module.require(isinstance(entry, dict) and set(entry) == {"path", "sha256"},
                           "Invalid review record")
            small[entry["path"]] = entry["sha256"]
        for key in ("config", "input_image"):
            item = manifest.get(key, {})
            module.require(isinstance(item.get("path"), str)
                           and Path(item["path"]).is_absolute(), "Missing " + key)
            small[item["path"]] = item.get("sha256")
        module.require(manifest["config"]["sha256"] == module.REF.ORIGINAL_CONFIG_SHA,
                       "Original inference YAML must remain fixed")
        for filename, digest in small.items():
            module.require(Path(filename).is_absolute()
                           and isinstance(digest, str)
                           and module.REF.HEX.fullmatch(digest),
                           "Missing source/input/review identity")
            current = os.stat(filename, follow_symlinks=False)
            module.require(stat.S_ISREG(current.st_mode),
                           "Source/input/review is not a regular file: " + filename)
        core = module.REF.core_sha256(manifest)
        for name, status in module.REVIEW_STATUSES.items():
            entry = evidence[name]
            review, _, _ = read_json_snapshot(
                Path(entry["path"]), "S39 " + name + " review", entry["sha256"]
            )
            module.require(
                review.get("status") == status
                and review.get("core_sha256") == core
                and review.get("variant") == module.VARIANT,
                "Review did not approve this declared variant core",
            )
        if metadata_only:
            return {
                "schema": "s39-variant-metadata-v1",
                "status": "PASS_METADATA_ONLY",
                "variant": module.VARIANT,
                "manifest_path": str(path),
                "manifest_sha256": expected,
                "execution_authorized": False,
                "weight_bytes_read": 0,
                "image_bytes_read": 0,
                "scope": "Paths/sizes/published identities, current source domain and review bindings only; full content verification still required",
            }
        for filename, digest in small.items():
            module.require(sha(filename) == digest,
                           "Frozen source/input/review changed: " + filename)
        for role, record in records.items():
            digest, identity = hash_regular_file(Path(record["path"]), "S39 component " + role)
            module.require(
                digest == record["sha256"]
                and identity["size"] == record["size"]
                and identity["mtime_ns"] == record["mtime_ns"]
                and identity["device"] == record["device"]
                and identity["inode"] == record["inode"],
                "Component content mismatch or changed during SHA: " + role,
            )
        return {
            "schema": "s39-variant-resource-gate-v1",
            "status": "PASS_DECLARED_VARIANT_RESOURCE_GATE",
            "variant": module.VARIANT,
            "manifest_path": str(path),
            "manifest_sha256": expected,
            "controls": module.REF.CONTROLS,
            "components": records,
            "source_identities": source_ids,
            "evidence_kind": "recorded_component_variant_loading",
            "verified_utc": datetime.now(timezone.utc).isoformat(),
            "scope": "Exact declared ft-mse identities; original SD2.1 VAE remains UNKNOWN",
        }

    def safe_validate_gate(gate):
        module.require(
            isinstance(gate, dict)
            and gate.get("schema") == "s39-variant-resource-gate-v1"
            and gate.get("status") == "PASS_DECLARED_VARIANT_RESOURCE_GATE"
            and gate.get("variant") == module.VARIANT,
            "A completed declared-variant full gate is required",
        )
        _, manifest = safe_read_manifest(gate["manifest_path"], gate["manifest_sha256"])
        module.require(
            manifest.get("status") == module.FROZEN
            and manifest["controls"] == gate["controls"] == module.REF.CONTROLS
            and manifest["runtime"] == module.RUNTIME
            and manifest["loading_limits"] == module.LIMITS,
            "Gate core changed",
        )
        module.require(set(gate["components"]) == module.REF.ROLES,
                       "Incomplete resource gate")
        for role, record in gate["components"].items():
            item = manifest["components"][role]
            module.require(
                record["path"] == item["path"]
                and (record["size"], record["sha256"])
                == (item["size"], item["sha256"])
                == module.PUBLISHED[role]
                and safe_same_stat(record),
                "Verified component changed: " + role,
            )
        module.require(
            gate["source_identities"] == manifest["source_identities"] == module.required_sources(),
            "Source domain changed",
        )
        for filename, digest in gate["source_identities"].items():
            module.require(sha(filename) == digest,
                           "Source changed before/after loading: " + filename)
        for key in ("config", "input_image"):
            module.require(sha(manifest[key]["path"]) == manifest[key]["sha256"],
                           "Small frozen runtime input changed: " + key)
        return gate

    module.check_manifest = safe_check_manifest
    module.validate_gate = safe_validate_gate
    return module


S39_GATE = bind_s39()
VARIANT = S39_GATE.VARIANT
RUNTIME = S39_GATE.REF.RUNTIME
CONTROLS = copy.deepcopy(S39_GATE.REF.CONTROLS)
CONTROLS["seed"] = 44
require(
    {key for key in CONTROLS if CONTROLS[key] != S39_GATE.REF.CONTROLS[key]} == {"seed"}
    and S39_GATE.REF.CONTROLS["seed"] == 42,
    "C2 controls must differ from S40 only by seed 42 to 44",
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
        and isinstance(expected, str)
        and S39_GATE.REF.HEX.fullmatch(expected),
        label + " record is missing or changed",
    )
    document, _, _ = read_json_snapshot(path, label, expected)
    return document


def read_base_s40():
    base, _, _ = read_json_snapshot(BASE_S40, "Sealed S40 manifest", BASE_S40_SHA256)
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
        require(path.is_file(), "Missing prepared C2 source: " + name)
        identities[str(path)] = sha(path)
    return identities


def exact_parent_bindings():
    return {
        "s40_manifest": {"path": str(BASE_S40), "sha256": BASE_S40_SHA256},
        "s42_preregistration": {"path": str(S42_PROTOCOL), "sha256": S42_PROTOCOL_SHA256},
    }


def exact_input_record():
    return {
        "path": str(C2_INPUT),
        "sha256": C2_INPUT_SHA256,
        "size_bytes": C2_INPUT_BYTES,
        "original_size": C2_ORIGINAL_SIZE,
        "scope": "Predeclared C2 JPEG bytes; full bytes hashed before model construction, pixels not decoded by gate",
    }


def exact_config_record():
    return {"path": str(C2_CONFIG), "sha256": C2_CONFIG_SHA256}


def require_single_seed_config_derivation(base):
    original_path = Path(base["config"]["path"])
    require(
        base["config"]["sha256"] == S39_GATE.REF.ORIGINAL_CONFIG_SHA,
        "Sealed S40 inference config changed",
    )
    original, _ = verified_bytes(
        original_path, base["config"]["sha256"], "Sealed S40 inference config"
    )
    candidate, _ = verified_bytes(C2_CONFIG, C2_CONFIG_SHA256, "C2 seed-44 config")
    require(
        original.count(b"seed: 42") == 1
        and b"seed: 44" not in original
        and candidate
        == original.replace(b"seed: 42", b"seed: 44") + b"\n"
        and not original.endswith(b"\n")
        and candidate.endswith(b"\n")
        and not candidate.endswith(b"\n\n"),
        "C2 inference config must be the S40 bytes with the unique seed 42 changed to 44 plus exactly one terminal LF",
    )


def exact_derivation_policy():
    return {
        "row": "C2",
        "base_row": "B0/S40",
        "allowed_scientific_differences": {
            "input_image": {"from": "changi.jpg", "to": "living_room.jpg"},
            "seed": {
                "from": 42,
                "to": 44,
                "yaml_byte_policy": "UNIQUE_SEED_SUBSTITUTION_PLUS_ONE_TERMINAL_LF",
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
        "Frozen C2 manifest SHA required",
    )
    path = Path(path)
    require(path.is_absolute(), "C2 manifest path must be absolute and unredirected")
    manifest, _, _ = read_json_snapshot(path, "Frozen C2 manifest", expected)
    base = read_base_s40()
    require(
        manifest.get("schema") == SCHEMA
        and manifest.get("status") == FROZEN
        and manifest.get("evidence_kind") == "recorded_execution"
        and manifest.get("variant") == VARIANT,
        "A separately frozen C2 declared-variant manifest is required",
    )
    require(
        manifest.get("controls") == CONTROLS
        and manifest.get("runtime") == RUNTIME
        and manifest.get("generation_limits") == LIMITS,
        "C2 controls, runtime, or budgets changed",
    )
    require(
        {key: value for key, value in manifest["controls"].items() if key != "seed"}
        == {key: value for key, value in base["controls"].items() if key != "seed"},
        "C2 controls differ from S40 beyond the frozen seed",
    )
    require(
        manifest.get("components") == base.get("components")
        and manifest.get("config") == exact_config_record()
        and manifest.get("runtime") == base.get("runtime")
        and manifest.get("generation_limits") == base.get("generation_limits"),
        "C2 changed a sealed S40 component, config, runtime, or budget",
    )
    require_single_seed_config_derivation(base)
    require(
        manifest.get("input_image") == exact_input_record()
        and manifest.get("output_root") == str(C2_OUTPUT)
        and manifest.get("source_identities") == required_sources()
        and manifest.get("parent_bindings") == exact_parent_bindings()
        and manifest.get("derivation_policy") == exact_derivation_policy(),
        "C2 input, output, source domain, parent, or difference policy changed",
    )
    for key in (
        "s39_loading_manifest",
        "s39_resource_core_sha256",
        "s39_loading_evidence",
        "s39_loading_review",
    ):
        require(manifest.get(key) == base.get(key), "C2 changed sealed loading evidence: " + key)
    try:
        created = datetime.fromisoformat(manifest.get("created_utc", "").replace("Z", "+00:00"))
    except (TypeError, ValueError) as error:
        raise RuntimeError("C2 created_utc is not a valid timestamp") from error
    require(created.tzinfo is not None, "C2 created_utc must be timezone-aware")
    preparation = manifest.get("freeze_preparation", {})
    freeze_tool = HERE / "freeze_c2_manifest.py"
    require(
        preparation.get("schema") == "s47-c2-core-freeze-v1"
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
        == "Await two separately authored reviews of the exact C2 baseline core",
        "C2 freeze-preparation record is incomplete or changed",
    )
    return manifest


def require_published_attachment(path, expected, manifest):
    """Bind executable manifests to the terminally successful attach bundle."""
    path = Path(path)
    require(path == PUBLISHED_MANIFEST, "Only the canonical C2 attached manifest is executable")
    require(
        not os.path.lexists(PREPARE_STAGING_LEASE)
        and not os.path.lexists(ATTACH_STAGING_LEASE)
        and not os.path.lexists(ATTACH_PREFLIGHT_ROOT),
        "A C2 freeze/attach staging or preflight lease remains occupied",
    )
    attachment_stat = os.stat(ATTACHMENT_ROOT, follow_symlinks=False)
    require(stat.S_ISDIR(attachment_stat.st_mode),
            "Canonical C2 attachment root is redirected")
    entries = {}
    for entry in ATTACHMENT_ROOT.iterdir():
        current = os.stat(entry, follow_symlinks=False)
        entries[entry.name] = stat.S_ISREG(current.st_mode)
    require(
        entries
        == {"manifest.json": True, "metadata_gate.json": True, "receipt.json": True},
        "Canonical C2 attachment must contain exactly three regular success files",
    )
    receipt, receipt_sha, _ = read_json_snapshot(
        PUBLISHED_RECEIPT, "Successful C2 attachment receipt"
    )
    require(
        receipt.get("schema") == "s47-c2-freeze-tool-receipt-v1"
        and receipt.get("status") == "S47_C2_REVIEWS_ATTACHED_METADATA_GATE_PASSED"
        and receipt.get("mode") == "attach"
        and receipt.get("manifest_path") == str(PUBLISHED_MANIFEST)
        and receipt.get("manifest_sha256") == expected
        and receipt.get("core_sha256") == core_sha256(manifest)
        and receipt.get("review_receipts") == manifest.get("review_receipts")
        and receipt.get("tool_source_path") == str(HERE / "freeze_c2_manifest.py")
        and receipt.get("tool_source_sha256") == sha(HERE / "freeze_c2_manifest.py")
        and receipt.get("freeze_protocol_sha256") == FREEZE_PROTOCOL_SHA256
        and receipt.get("scientific_status") == "NOT_EVALUATED"
        and receipt.get("source_unchanged_at_close") is True
        and receipt.get("metadata_gate_status") == "UNPUBLISHED_ATTACHMENT_PREFLIGHT_ONLY"
        and receipt.get("metadata_gate_path") == str(PUBLISHED_METADATA_GATE)
        and isinstance(receipt.get("metadata_gate_sha256"), str),
        "C2 attachment receipt does not authorize this exact manifest",
    )
    metadata, metadata_sha, _ = read_json_snapshot(
        PUBLISHED_METADATA_GATE,
        "C2 attached metadata gate",
        receipt["metadata_gate_sha256"],
    )
    require(
        metadata.get("schema") == "s47-c2-generation-metadata-v1"
        and metadata.get("status") == "UNPUBLISHED_ATTACHMENT_PREFLIGHT_ONLY"
        and metadata.get("manifest_sha256") == expected
        and metadata.get("execution_authorized") is False
        and metadata.get("unpublished_attachment_check") is True
        and metadata.get("attachment_receipt") is None
        and metadata.get("launch_authorization") is None,
        "C2 attached metadata gate does not bind this manifest",
    )
    parse_utc(receipt.get("completed_utc"), "C2 attachment receipt completed_utc")
    return {
        "path": str(PUBLISHED_RECEIPT),
        "sha256": receipt_sha,
        "status": receipt["status"],
        "metadata_gate_sha256": metadata_sha,
    }


def launch_review_bindings(manifest, expected):
    """Recompute the five immutable identities reviewed before authorization."""
    core_path = HERE / "freeze_attempt_01/manifest_core.json"
    core, core_file_sha, _ = read_json_snapshot(core_path, "Frozen C2 manifest core")
    stripped = copy.deepcopy(manifest)
    stripped["review_receipts"] = {}
    require(
        core.get("review_receipts") == {}
        and stripped == core
        and core_sha256(core) == core_sha256(manifest),
        "Published C2 manifest does not differ from its core only by review receipts",
    )
    receipt, receipt_sha, _ = read_json_snapshot(
        PUBLISHED_RECEIPT, "Published C2 attachment receipt"
    )
    metadata, metadata_sha, _ = read_json_snapshot(
        PUBLISHED_METADATA_GATE, "Published C2 metadata gate"
    )
    require(
        receipt.get("manifest_sha256") == expected
        and receipt.get("core_sha256") == core_sha256(manifest)
        and receipt.get("metadata_gate_sha256") == metadata_sha
        and metadata.get("manifest_sha256") == expected,
        "C2 launch-review bindings differ from the published attachment",
    )
    attachment_completed_utc = receipt.get("completed_utc")
    parse_utc(attachment_completed_utc, "C2 attachment completed_utc")
    return {
        "manifest_sha256": expected,
        "core_file_sha256": core_file_sha,
        "core_sha256": core_sha256(manifest),
        "attachment_receipt_sha256": receipt_sha,
        "metadata_gate_sha256": metadata_sha,
    }, attachment_completed_utc


def require_launch_authorization(manifest, expected):
    """Validate the fixed post-review authorization before any published gate passes."""
    document, authorization_sha, authorization_identity = read_json_snapshot(
        LAUNCH_AUTHORIZATION, "Fixed read-only C2 launch authorization"
    )
    require(authorization_identity["mode"] & 0o222 == 0,
            "Fixed C2 launch authorization is writable")
    require(
        manifest.get("source_identities", {}).get(str(AUTHORIZATION_TOOL))
        == sha(AUTHORIZATION_TOOL),
        "C2 authorization tool is outside or differs from the frozen source domain",
    )
    require(
        isinstance(document.get("reviews"), dict)
        and set(document["reviews"]) == set(FINAL_REVIEW_STATUSES),
        "C2 launch authorization does not bind exactly two terminal reviews",
    )
    review_documents = {}
    review_hashes = {}
    for kind, review_path in FINAL_REVIEW_PATHS.items():
        ref = document["reviews"].get(kind, {})
        require(
            ref.get("path") == str(review_path)
            and isinstance(ref.get("sha256"), str),
            "C2 launch authorization review is absent, redirected, or changed: " + kind,
        )
        review_hashes[kind] = ref["sha256"]
        review_documents[kind], _, _ = read_json_snapshot(
            review_path, kind + " terminal review", ref["sha256"]
        )
    bindings, attachment_completed_utc = launch_review_bindings(manifest, expected)
    rebuilt = build_launch_authorization_document(
        bindings=bindings,
        attachment_completed_utc=attachment_completed_utc,
        review_documents=review_documents,
        review_hashes=review_hashes,
        created_utc=document.get("created_utc"),
        tool_sha256=sha(AUTHORIZATION_TOOL),
    )
    require(document == rebuilt, "C2 launch authorization content is incomplete or changed")
    lease, _, lease_identity = read_json_snapshot(
        AUTHORIZATION_ATTEMPT_RECEIPT, "C2 authorization-attempt success receipt"
    )
    require(
        lease_identity["mode"] & 0o222 == 0
        and lease.get("schema") == "s47-c2-authorization-attempt-receipt-v1"
        and lease.get("status") == "AUTHORIZED_AND_ATTEMPT_SEALED"
        and lease.get("attempt_path") == str(AUTHORIZATION_ATTEMPT)
        and lease.get("authorization_path") == str(LAUNCH_AUTHORIZATION)
        and lease.get("authorization_sha256") == authorization_sha
        and lease.get("tool_source_sha256") == sha(AUTHORIZATION_TOOL)
        and lease.get("retry_permitted") is False,
        "C2 authorization attempt lease is absent, incomplete, or unsealed",
    )
    return {
        "path": str(LAUNCH_AUTHORIZATION),
        "sha256": authorization_sha,
        "status": AUTHORIZATION_STATUS,
        "bindings": bindings,
        "reviews": copy.deepcopy(document["reviews"]),
        "attempt_receipt": {
            "path": str(AUTHORIZATION_ATTEMPT_RECEIPT),
            "status": lease["status"],
        },
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
        "C2 component-loading parent differs from its reusable component scope or config derivation",
    )
    require_single_seed_config_derivation(base)
    require(
        parent["input_image"] == base["input_image"]
        and manifest["input_image"] != parent["input_image"],
        "C2 must separate the new input from the old component-loading input",
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


def evaluate_manifest_snapshot(path, expected, manifest, *, metadata_only, unpublished_preflight):
    """Evaluate one already verified manifest snapshot without reopening its path."""
    attachment = None
    authorization = None
    if not unpublished_preflight:
        attachment = require_published_attachment(path, expected, manifest)
        authorization = require_launch_authorization(manifest, expected)
    loading_chain(manifest)
    reviews = manifest.get("review_receipts", {})
    require(set(reviews) == set(REVIEW_STATUSES), "Two exact C2 reviews are required")
    core = core_sha256(manifest)
    core_path = HERE / "freeze_attempt_01/manifest_core.json"
    _, core_file_sha, _ = read_json_snapshot(core_path, "Frozen C2 manifest core")
    reviewer_roles = []
    for role, status in REVIEW_STATUSES.items():
        review = read_json_record(reviews[role], "C2 " + role)
        require(
            review.get("schema") == "s47-c2-generation-core-review-v1"
            and review.get("status") == status
            and review.get("variant") == VARIANT
            and review.get("row") == "C2"
            and review.get("core_path") == str(core_path)
            and review.get("core_file_sha256") == core_file_sha
            and review.get("core_sha256") == core,
            "C2 review does not approve this exact core: " + role,
        )
        require(
            review.get("author_role") == "/root"
            and isinstance(review.get("reviewer_role"), str)
            and review["reviewer_role"] != "/root"
            and review.get("executed") is False
            and review.get("model_or_scientific_imports") == 0
            and review.get("pixels_decoded") == 0
            and review.get("blocking_findings") == [],
            "C2 review execution or independence boundary differs: " + role,
        )
        reviewer_roles.append(review["reviewer_role"])
    require(len(set(reviewer_roles)) == 2, "C2 reviews require two distinct non-root roles")
    for filename, digest in manifest["source_identities"].items():
        require(sha(filename) == digest, "Changed C2 generation source: " + filename)
    input_stat = os.stat(C2_INPUT, follow_symlinks=False)
    require(stat.S_ISREG(input_stat.st_mode) and input_stat.st_size == C2_INPUT_BYTES,
            "C2 input path or byte count differs")
    config_stat = os.stat(C2_CONFIG, follow_symlinks=False)
    require(stat.S_ISREG(config_stat.st_mode), "C2 seed-44 inference config is missing")
    if metadata_only:
        return {
            "schema": "s47-c2-generation-metadata-v1",
            "status": (
                "UNPUBLISHED_ATTACHMENT_PREFLIGHT_ONLY"
                if unpublished_preflight
                else "PASS_METADATA_ONLY"
            ),
            "variant": VARIANT,
            "row": "C2",
            "manifest_sha256": expected,
            "execution_authorized": authorization is not None,
            "unpublished_attachment_check": unpublished_preflight,
            "component_bodies_read": 0,
            "input_body_read": 0,
            "config_body_bytes_read": config_stat.st_size,
            "attachment_receipt": attachment,
            "launch_authorization": authorization,
            "scope": (
                "Fixed attach-preflight snapshot only; no published PASS and no execution authorization"
                if unpublished_preflight
                else "Sealed parents, core/final-review/authorization hashes, exact small config derivation, paths and input size only; worker component/input full hashes remain"
            ),
        }
    full = S39_GATE.check_manifest(
        manifest["s39_loading_manifest"]["path"],
        manifest["s39_loading_manifest"]["sha256"],
    )
    require(sha(C2_INPUT) == C2_INPUT_SHA256, "C2 input full SHA-256 differs")
    require_single_seed_config_derivation(read_base_s40())
    return {
        "schema": "s47-c2-generation-resource-gate-v1",
        "status": "PASS_C2_DECLARED_GENERATION_RESOURCE_GATE",
        "manifest_path": str(path),
        "manifest_sha256": expected,
        "manifest_snapshot": copy.deepcopy(manifest),
        "output_root": manifest["output_root"],
        "variant": VARIANT,
        "row": "C2",
        "components": full["components"],
        "controls": manifest["controls"],
        "source_identities": manifest["source_identities"],
        "config": exact_config_record(),
        "input_image": exact_input_record(),
        "attachment_receipt": attachment,
        "launch_authorization": authorization,
        "s39_full_gate": full,
        "evidence_kind": "recorded_execution",
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "identity_scope": "Declared official-ft-mse variant with separately hashed C2 input; not exact original SD2.1",
    }


def check_attachment_preflight(path, expected):
    """Narrow non-PASS route for the one fixed attach staging manifest."""
    path = Path(path)
    require(path == ATTACH_PREFLIGHT_MANIFEST,
            "Only the fixed C2 attach-preflight manifest may use this route")
    root_stat = os.stat(ATTACH_PREFLIGHT_ROOT, follow_symlinks=False)
    require(stat.S_ISDIR(root_stat.st_mode), "C2 attach-preflight root is redirected")
    require(
        not os.path.lexists(ATTACHMENT_ROOT)
        and not os.path.lexists(PREPARE_STAGING_LEASE)
        and not os.path.lexists(ATTACH_STAGING_LEASE)
        and not os.path.lexists(LAUNCH_AUTHORIZATION)
        and not os.path.lexists(AUTHORIZATION_ATTEMPT)
        and not os.path.lexists(HERE / "execution_01")
        and not os.path.lexists(C2_OUTPUT),
        "C2 unpublished preflight requires every later formal path to be absent",
    )
    manifest = read_frozen(path, expected)
    return evaluate_manifest_snapshot(
        path, expected, manifest, metadata_only=True, unpublished_preflight=True
    )


def check_manifest(path, expected, *, metadata_only=False):
    """Canonical published route; metadata and full calls both require authorization."""
    path = Path(path)
    require(path == PUBLISHED_MANIFEST,
            "Only the canonical published C2 manifest may use the generation gate")
    manifest = read_frozen(path, expected)
    return evaluate_manifest_snapshot(
        path, expected, manifest, metadata_only=metadata_only, unpublished_preflight=False
    )


def validate_gate(gate):
    require(
        isinstance(gate, dict)
        and gate.get("schema") == "s47-c2-generation-resource-gate-v1"
        and gate.get("status") == "PASS_C2_DECLARED_GENERATION_RESOURCE_GATE"
        and gate.get("variant") == VARIANT
        and gate.get("row") == "C2",
        "A completed C2 full resource gate is required",
    )
    manifest = read_frozen(gate["manifest_path"], gate["manifest_sha256"])
    authorization = require_launch_authorization(manifest, gate["manifest_sha256"])
    require(
        gate.get("manifest_snapshot") == manifest
        and gate.get("output_root") == manifest["output_root"] == str(C2_OUTPUT)
        and gate.get("controls") == manifest["controls"]
        and gate.get("source_identities") == manifest["source_identities"]
        and gate.get("config") == manifest["config"]
        and gate.get("input_image") == manifest["input_image"]
        and gate.get("components") == gate.get("s39_full_gate", {}).get("components"),
        "C2 gate data changed",
    )
    require(
        gate.get("launch_authorization") == authorization,
        "C2 full gate launch authorization changed",
    )
    S39_GATE.validate_gate(gate["s39_full_gate"])
    require(
        gate["s39_full_gate"]["manifest_sha256"] == manifest["s39_loading_manifest"]["sha256"],
        "C2 gate has another component-loading parent",
    )
    require(sha(C2_INPUT) == C2_INPUT_SHA256, "C2 input changed before/after loading")
    require_single_seed_config_derivation(read_base_s40())
    check_manifest(gate["manifest_path"], gate["manifest_sha256"], metadata_only=True)
    return gate
