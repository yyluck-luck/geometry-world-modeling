#!/usr/bin/env python3
"""V4 standard-library static/adversarial checks; never run a formal C2 gate."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from types import ModuleType


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRODUCTION = (
    HERE / "PROTOCOL.md",
    HERE / "FREEZE_PROTOCOL.md",
    HERE / "generation_gate.py",
    HERE / "runtime_adapter.py",
    HERE / "launch_generation.py",
    HERE / "freeze_c2_manifest.py",
    HERE / "create_launch_authorization.py",
    HERE / "inference_seed44.yaml",
)
PYTHON_SOURCES = tuple(path for path in PRODUCTION if path.suffix == ".py") + (
    HERE / "static_selftest.py",
)
FORMAL_PATHS = (
    HERE / "freeze_attempt_01",
    HERE / "review_attachment_01",
    HERE / "FINAL_ATTACHMENT_REVIEW.json",
    HERE / "LAUNCH_READINESS_REVIEW.json",
    HERE / "launch_authorization_01.json",
    HERE / "launch_authorization_attempt_01",
    HERE / ".review_attachment_01.preflight",
    HERE / ".freeze_attempt_01.staging",
    HERE / ".review_attachment_01.staging",
    HERE / "execution_01",
    ROOT / "results/S47_C2_confirmation_generation",
)
SCIENTIFIC_PREFIXES = (
    "torch",
    "numpy",
    "PIL",
    "diffusers",
    "open_clip",
    "omegaconf",
    "kornia",
    "cv2",
)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_module_snapshot(name, path):
    payload = Path(path).read_bytes()
    module = ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = ""
    sys.modules[name] = module
    exec(compile(payload, str(path), "exec", dont_inherit=True), module.__dict__)
    return module


class DenyScientificImports:
    def find_spec(self, fullname, path=None, target=None):
        if any(fullname == prefix or fullname.startswith(prefix + ".")
               for prefix in SCIENTIFIC_PREFIXES):
            raise ImportError("V4 static self-test denied scientific import: " + fullname)
        return None


def rejected(function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except (RuntimeError, OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return True
    raise RuntimeError("Negative V4 static case was accepted")


def source_function(tree, name):
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


def write_capability_record(launcher, execution, state, *, parent_pid=None):
    record = {
        "schema": "s47-c2-worker-capability-record-v1",
        "status": "ISSUED_ONCE_BY_MONITORED_PARENT",
        "parent_pid": os.getppid() if parent_pid is None else parent_pid,
        "worker_pid": os.getpid(),
        "manifest_sha256": "a" * 64,
        "launcher_sha256": launcher.snapshot_sha(Path(launcher.__file__).absolute()),
        "execution_directory": str(execution),
        "output_root": str(execution.parent / "synthetic-output"),
        "created_utc": "2026-09-08T00:00:00+00:00",
        "secret_sha256": hashlib.sha256(state["secret"]).hexdigest(),
        "capability_transport": "FORK_INHERITED_OPAQUE_MEMORY_TOKEN_WITH_ONE_BYTE_PARENT_SYNC",
        "public_worker_cli": False,
        "reusable": False,
    }
    launcher.write_new_json(execution / launcher.CAPABILITY_RECORD, record)


def main():
    require(sys.version_info[:2] in {(3, 12), (3, 13)},
            "V4 self-test requires reviewed Python 3.12 or 3.13")
    require(all(not os.path.lexists(path) for path in FORMAL_PATHS),
            "A formal C2 freeze/attach/auth/preflight/execution/result path exists")

    parsed = {}
    for path in PYTHON_SOURCES:
        payload = path.read_bytes()
        parsed[path.name] = ast.parse(payload, filename=str(path))
        text = payload.decode("utf-8")
        if path.name != "static_selftest.py":
            require("seed: 43" not in text and "S44" not in text,
                    "Stale row/seed label in " + path.name)

    gate_tree = parsed["generation_gate.py"]
    public_gate = source_function(gate_tree, "check_manifest")
    preflight_gate = source_function(gate_tree, "check_attachment_preflight")
    require(
        [arg.arg for arg in public_gate.args.args] == ["path", "expected"]
        and [arg.arg for arg in public_gate.args.kwonlyargs] == ["metadata_only"]
        and "_allow_unpublished_attachment" not in ast.unparse(gate_tree)
        and "path == ATTACH_PREFLIGHT_MANIFEST" in ast.unparse(preflight_gate)
        and "UNPUBLISHED_ATTACHMENT_PREFLIGHT_ONLY" in ast.unparse(gate_tree),
        "Unpublished attach preflight is not isolated from the canonical gate",
    )
    freeze_preflight = source_function(parsed["freeze_c2_manifest.py"], "preflight_attachment")
    freeze_preflight_text = ast.unparse(freeze_preflight)
    freeze_source_text = ast.unparse(parsed["freeze_c2_manifest.py"])
    require(
        "gate.ATTACH_PREFLIGHT_ROOT" in freeze_preflight_text
        and "gate.ATTACH_PREFLIGHT_MANIFEST" in freeze_preflight_text
        and "gate.check_attachment_preflight" in freeze_preflight_text
        and "TemporaryDirectory" not in freeze_preflight_text,
        "Freeze attach preflight is not bound to its fixed hidden path",
    )
    require(
        ".freeze_attempt_01.staging" in freeze_source_text
        and ".review_attachment_01.staging" in freeze_source_text
        and "time.time_ns" not in freeze_source_text
        and "tempfile.mkdtemp" not in freeze_source_text
        and "failed_" not in freeze_source_text,
        "Freeze/attach staging can escape its fixed one-attempt lease",
    )

    launcher_main = source_function(parsed["launch_generation.py"], "main")
    launcher_text = ast.unparse(parsed["launch_generation.py"])
    require(
        "parse_exact_arguments(argv, internal=False)" in ast.unparse(launcher_main)
        and "namespace['parent'](args)" in ast.unparse(launcher_main)
        and "derive_launcher()['main']" not in ast.unparse(launcher_main)
        and "os.fork()" in launcher_text
        and "worker_entry(internal, capability)" in launcher_text
        and "capability is capability_state.get('token')" in launcher_text
        and "secrets.token_bytes(32)" in launcher_text
        and "CONSUMED_ONCE_BEFORE_WORKER_GATE" in launcher_text,
        "Parent-only single-use worker capability route is incomplete",
    )
    authorization_source = (HERE / "create_launch_authorization.py").read_text()
    authorization_text = ast.unparse(parsed["create_launch_authorization.py"])
    require(
        "os.mkdir(ATTEMPT, mode=448)" in authorization_text
        and "authorization.staging.json" in authorization_source
        and "failure_receipt.json" in authorization_source
        and "time.time_ns" not in authorization_text,
        "Authorization does not use one fixed terminal attempt lease",
    )
    runtime_text = ast.unparse(parsed["runtime_adapter.py"])
    require(
        "manifest_from_verified_gate" in runtime_text
        and "O_NOFOLLOW" in runtime_text
        and "dir_fd=directory_fd" in runtime_text
        and "same_directory_identity" in runtime_text,
        "Runtime snapshot/stable-inode receipt hardening is incomplete",
    )
    for name in (
        "generation_gate.py",
        "freeze_c2_manifest.py",
        "create_launch_authorization.py",
        "launch_generation.py",
    ):
        text = ast.unparse(parsed[name])
        require("O_NOFOLLOW" in text and "os.fstat" in text and "compile(payload" in text,
                "Same-descriptor source/JSON primitive is incomplete in " + name)
        require("SourceFileLoader" not in text,
                "Cached/path-reopened source loader remains in " + name)
        require(".read_text(" not in text and ".read_bytes(" not in text,
                "Path-reopened source/JSON reader remains in " + name)

    blocker = DenyScientificImports()
    sys.meta_path.insert(0, blocker)
    try:
        gate = load_module_snapshot("generation_gate", HERE / "generation_gate.py")
        runtime = load_module_snapshot("_s47_c2_runtime_v4_static", HERE / "runtime_adapter.py")
        launcher = load_module_snapshot("_s47_c2_launcher_v4_static", HERE / "launch_generation.py")
        freeze = load_module_snapshot("_s47_c2_freeze_v4_static", HERE / "freeze_c2_manifest.py")
        authorization = load_module_snapshot(
            "_s47_c2_authorization_v4_static", HERE / "create_launch_authorization.py"
        )

        require(gate.C2_PROTOCOL_SHA256 == sha(HERE / "PROTOCOL.md")
                and gate.FREEZE_PROTOCOL_SHA256 == sha(HERE / "FREEZE_PROTOCOL.md"),
                "Gate protocol pins differ")
        require(freeze.FREEZE_PROTOCOL_SHA256 == sha(HERE / "FREEZE_PROTOCOL.md"),
                "Freeze protocol pin differs")
        require(
            launcher.GATE_SHA256 == sha(HERE / "generation_gate.py")
            and authorization.GATE_SHA256 == sha(HERE / "generation_gate.py"),
            "Launcher/authorization trust bootstrap does not pin the reviewed gate",
        )
        require(freeze.SOURCE_HASHES == {
            name: sha(HERE / name)
            for name in (
                "generation_gate.py",
                "runtime_adapter.py",
                "launch_generation.py",
                "create_launch_authorization.py",
                "PROTOCOL.md",
            )
        }, "Freeze transitive source pins differ")
        require(
            gate.S39_GATE.check_manifest.__name__ == "safe_check_manifest"
            and gate.S39_GATE.validate_gate.__name__ == "safe_validate_gate"
            and gate.S39_GATE.REF.required_sources.__name__ == "safe_ref_required_sources",
            "Transitive S39/S35 same-snapshot overrides are not active",
        )
        require(len(gate.required_sources()) == 219, "C2 V4 source-domain count changed")

        launcher_proof = launcher.derive_launcher(compile_only=True)
        runtime_proof = runtime.derive_factory(compile_only=True)
        require(
            launcher_proof["reversible_full_AST_equal"] is True
            and launcher_proof["security_hardening_counts"] == {
                "capability_spawn": 1,
                "worker_ticket_snapshot": 1,
                "worker_receipt_snapshot": 1,
                "worker_receipt_bound_digest": 1,
            }
            and runtime_proof["reversible_full_AST_equal"] is True
            and runtime_proof["manifest_snapshot_sites"] == 1
            and runtime_proof["stable_atomic_receipt_writer_sites"] == 1,
            "Reversible launcher/runtime security derivation proof failed",
        )

        public_valid = [
            "--manifest", str(launcher.PUBLISHED_MANIFEST),
            "--manifest-sha256", "a" * 64,
            "--execution-directory", str(launcher.EXECUTION),
        ]
        internal_valid = ["--worker"] + public_valid
        require(launcher.parse_exact_arguments(public_valid, internal=False).worker is False,
                "Canonical public split vector was rejected")
        require(launcher.parse_exact_arguments(internal_valid, internal=True).worker is True,
                "Canonical internal split vector was rejected")
        cli_negative = {
            "alternate_execution": [
                "--manifest", str(launcher.PUBLISHED_MANIFEST),
                "--manifest-sha256", "a" * 64,
                "--execution-directory", str(HERE / "execution_02"),
            ],
            "repeated_split": public_valid + ["--execution-directory", str(launcher.EXECUTION)],
            "split_then_equal": public_valid + ["--execution-directory=" + str(launcher.EXECUTION)],
            "equal_then_split": ["--execution-directory=" + str(launcher.EXECUTION)] + public_valid,
            "equal_only": public_valid[:-2] + ["--execution-directory=" + str(launcher.EXECUTION)],
            "repeated_equal": public_valid[:-2] + [
                "--execution-directory=" + str(launcher.EXECUTION),
                "--execution-directory=" + str(launcher.EXECUTION),
            ],
            "abbreviation": public_valid[:-2] + ["--execution-dir", str(launcher.EXECUTION)],
            "split_then_abbreviation": public_valid + ["--execution-dir", str(launcher.EXECUTION)],
            "public_worker": ["--worker"] + public_valid,
            "double_dash": ["--"] + public_valid,
            "manifest_equals": [
                "--manifest=" + str(launcher.PUBLISHED_MANIFEST),
                "--manifest-sha256", "a" * 64,
                "--execution-directory", str(launcher.EXECUTION),
            ],
        }
        for vector in cli_negative.values():
            require(rejected(launcher.parse_exact_arguments, vector, internal=False),
                    "Unsafe public CLI vector passed")

        internal_args = launcher.parse_exact_arguments(internal_valid, internal=True)
        require(rejected(
            launcher.consume_worker_capability,
            internal_args,
            object(),
            {"token": object(), "secret": b"x" * 32, "issued": False, "consumed": False},
        ), "External direct worker route passed without the fork-inherited capability")

        with tempfile.TemporaryDirectory(prefix=".s47-c2-v4-static-", dir=HERE) as temporary:
            scratch = Path(temporary)

            original = scratch / "snapshot.json"
            moved = scratch / "snapshot.opened.json"
            original.write_bytes(b'{"value":"A"}\n')
            descriptor = os.open(original, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            opened_stat = os.fstat(descriptor)
            os.rename(original, moved)
            original.write_bytes(b'{"value":"B"}\n')
            opened_bytes = os.read(descriptor, 1024)
            require(opened_bytes == b'{"value":"A"}\n'
                    and os.fstat(descriptor).st_ino == opened_stat.st_ino
                    and os.stat(original).st_ino != opened_stat.st_ino,
                    "Open descriptor did not retain the reviewed snapshot")
            os.close(descriptor)

            regular = scratch / "regular.json"
            regular.write_bytes(b'{"ok":true}\n')
            symlink = scratch / "symlink.json"
            os.symlink(regular, symlink)
            directory = scratch / "directory"
            directory.mkdir()
            fifo = scratch / "fifo"
            os.mkfifo(fifo)
            snapshot_negative = {}
            for module_name, module in (
                ("gate", gate),
                ("freeze", freeze),
                ("authorization", authorization),
                ("launcher", launcher),
            ):
                snapshot = module.read_regular_snapshot(regular, module_name + " regular")
                payload = snapshot[0] if isinstance(snapshot, tuple) else snapshot
                require(payload == regular.read_bytes(), "Regular snapshot differs")
                snapshot_negative[module_name] = {
                    "symlink": rejected(module.read_regular_snapshot, symlink, "symlink"),
                    "directory": rejected(module.read_regular_snapshot, directory, "directory"),
                    "fifo": rejected(module.read_regular_snapshot, fifo, "fifo"),
                }

            old_execution = launcher.EXECUTION
            try:
                fork_execution = scratch / "fork_execution_01"
                fork_execution.mkdir()
                launcher.EXECUTION = fork_execution
                fork_token = object()
                fork_state = {
                    "token": fork_token,
                    "secret": bytes(reversed(range(32))),
                    "issued": False,
                    "consumed": False,
                }
                fork_command = [
                    str(launcher.ROOT / ".venv-cut3r/bin/python"),
                    "-B",
                    str(Path(launcher.__file__).absolute()),
                    "--worker",
                    "--manifest", str(launcher.PUBLISHED_MANIFEST),
                    "--manifest-sha256", "a" * 64,
                    "--execution-directory", str(fork_execution),
                ]

                def synthetic_fork_worker(args, capability):
                    launcher.consume_worker_capability(
                        args, capability, fork_state
                    )
                    return 0

                with (fork_execution / "stdout.txt").open("x") as stdout, \
                        (fork_execution / "stderr.txt").open("x") as stderr:
                    fork_process = launcher.spawn_capability_worker(
                        fork_command,
                        cwd=str(ROOT),
                        env=dict(os.environ),
                        stdout=stdout,
                        stderr=stderr,
                        start_new_session=True,
                        execution=fork_execution,
                        manifest_sha256="a" * 64,
                        launcher_sha256=launcher.snapshot_sha(
                            Path(launcher.__file__).absolute()
                        ),
                        output_root=fork_execution.parent / "synthetic-output",
                        worker_entry=synthetic_fork_worker,
                        capability=fork_token,
                        capability_state=fork_state,
                    )
                    fork_returncode = fork_process.wait(timeout=5)
                fork_consumed, _ = launcher.read_json_snapshot(
                    fork_execution / launcher.CAPABILITY_CONSUMED,
                    "Synthetic fork capability consumption",
                )
                require(
                    fork_returncode == 0
                    and fork_state["issued"] is True
                    and fork_consumed.get("status") == "CONSUMED_ONCE_BEFORE_WORKER_GATE"
                    and fork_consumed.get("worker_pid") == fork_process.pid,
                    "Fork-inherited capability did not enter exactly one synthetic child",
                )

                synthetic_execution = scratch / "execution_01"
                synthetic_execution.mkdir()
                launcher.EXECUTION = synthetic_execution
                token = object()
                capability_state = {
                    "token": token,
                    "secret": bytes(range(32)),
                    "issued": True,
                    "consumed": False,
                    "parent_pid": os.getppid(),
                }
                write_capability_record(
                    launcher, synthetic_execution, capability_state
                )
                synthetic_args = copy.copy(internal_args)
                synthetic_args.execution_directory = str(synthetic_execution)
                consumed = launcher.consume_worker_capability(
                    synthetic_args, token, capability_state
                )
                require(consumed["status"] == "CONSUMED_ONCE_BEFORE_WORKER_GATE"
                        and consumed["reusable"] is False,
                        "Valid parent capability did not consume exactly once")
                replay_rejected = rejected(
                    launcher.consume_worker_capability,
                    synthetic_args,
                    token,
                    capability_state,
                )

                forged_execution = scratch / "forged_execution_01"
                forged_execution.mkdir()
                launcher.EXECUTION = forged_execution
                forged_token = object()
                forged_state = {
                    "token": forged_token,
                    "secret": b"x" * 32,
                    "issued": True,
                    "consumed": False,
                    "parent_pid": os.getppid(),
                }
                write_capability_record(launcher, forged_execution, forged_state)
                forged_args = copy.copy(internal_args)
                forged_args.execution_directory = str(forged_execution)
                forged_rejected = rejected(
                    launcher.consume_worker_capability,
                    forged_args,
                    object(),
                    forged_state,
                )
            finally:
                launcher.EXECUTION = old_execution

            old_authorization_paths = {
                name: getattr(authorization, name)
                for name in (
                    "AUTHORIZATION", "EXECUTION", "ATTEMPT", "ATTEMPT_STARTED",
                    "ATTEMPT_SUCCESS", "ATTEMPT_FAILURE", "STAGE"
                )
            }
            try:
                auth_root = scratch / "authorization"
                auth_root.mkdir()
                authorization.AUTHORIZATION = auth_root / "launch_authorization_01.json"
                authorization.EXECUTION = auth_root / "execution_01"
                authorization.ATTEMPT = auth_root / "launch_authorization_attempt_01"
                authorization.ATTEMPT_STARTED = authorization.ATTEMPT / "attempt_started.json"
                authorization.ATTEMPT_SUCCESS = authorization.ATTEMPT / "success_receipt.json"
                authorization.ATTEMPT_FAILURE = authorization.ATTEMPT / "failure_receipt.json"
                authorization.STAGE = authorization.ATTEMPT / "authorization.staging.json"
                synthetic_output = auth_root / "result"
                authorization.require_formal_freshness(synthetic_output)
                os.mkdir(authorization.ATTEMPT, mode=0o700)
                identity = authorization.attempt_identity()
                authorization.write_new(authorization.ATTEMPT_STARTED, b"{}\n")
                authorization.write_new(authorization.STAGE, b"staged\n")
                authorization.write_new(
                    authorization.ATTEMPT_FAILURE,
                    authorization.json_bytes({
                        "status": "AUTHORIZATION_ATTEMPT_FAILED_AND_SEALED",
                        "retry_permitted": False,
                    }),
                )
                authorization.require_post_claim_freshness(synthetic_output, identity)
                lease_retry_rejected = rejected(
                    authorization.require_formal_freshness, synthetic_output
                )
                require(authorization.STAGE.name == "authorization.staging.json"
                        and authorization.ATTEMPT_FAILURE.is_file(),
                        "Failed fixed authorization attempt was not retained")
            finally:
                for name, value in old_authorization_paths.items():
                    setattr(authorization, name, value)

            synthetic_manifest = {"output_root": str(gate.C2_OUTPUT), "marker": "A"}
            synthetic_gate = {
                "manifest_snapshot": synthetic_manifest,
                "output_root": str(gate.C2_OUTPUT),
                "manifest_path": str(gate.PUBLISHED_MANIFEST),
            }
            detached = runtime.manifest_from_verified_gate(synthetic_gate)
            synthetic_manifest["marker"] = "B"
            require(detached["marker"] == "A", "Runtime manifest snapshot was not detached")

            old_c2_output = gate.C2_OUTPUT
            try:
                runtime_output = scratch / "runtime-output"
                runtime_output.mkdir()
                gate.C2_OUTPUT = runtime_output
                receipt = runtime_output / "runtime_loading.json"
                runtime.atomic_save_runtime_receipt(receipt, {"status": "FIRST"}, runtime_output)
                runtime.atomic_save_runtime_receipt(receipt, {"status": "SECOND"}, runtime_output)
                require(json.loads(receipt.read_bytes())["status"] == "SECOND",
                        "Runtime atomic receipt update differs")
                victim = scratch / "victim.txt"
                victim.write_bytes(b"untouched")
                os.symlink(victim, runtime_output / ".runtime_loading.s47-c2.tmp")
                temp_symlink_rejected = rejected(
                    runtime.atomic_save_runtime_receipt,
                    receipt,
                    {"status": "THIRD"},
                    runtime_output,
                )
                require(victim.read_bytes() == b"untouched"
                        and json.loads(receipt.read_bytes())["status"] == "SECOND",
                        "Runtime temp symlink altered a victim or receipt")

                stable = scratch / "stable-dir"
                stable.mkdir()
                stable_fd = os.open(stable, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
                moved_stable = scratch / "stable-dir-opened"
                os.rename(stable, moved_stable)
                stable.mkdir()
                directory_swap_rejected = not runtime.same_directory_identity(stable, stable_fd)
                os.close(stable_fd)

                destination_output = scratch / "destination-output"
                destination_output.mkdir()
                destination_victim = scratch / "destination-victim.txt"
                destination_victim.write_bytes(b"safe")
                os.symlink(destination_victim, destination_output / "runtime_loading.json")
                gate.C2_OUTPUT = destination_output
                destination_symlink_rejected = rejected(
                    runtime.atomic_save_runtime_receipt,
                    destination_output / "runtime_loading.json",
                    {"status": "SHOULD_NOT_PUBLISH"},
                    destination_output,
                )
                require(destination_victim.read_bytes() == b"safe",
                        "Runtime destination symlink altered its target")
            finally:
                gate.C2_OUTPUT = old_c2_output

            require(rejected(
                gate.check_manifest,
                Path("/tmp/not-a-c2-manifest"),
                "0" * 64,
                metadata_only=True,
                _allow_unpublished_attachment=True,
            ), "Legacy caller-controlled unpublished flag remains accepted")
    finally:
        sys.meta_path.remove(blocker)

    scientific_loaded = sorted(
        name for name in sys.modules
        if any(name == prefix or name.startswith(prefix + ".")
               for prefix in SCIENTIFIC_PREFIXES)
    )
    require(scientific_loaded == [], "Scientific modules were imported: " + repr(scientific_loaded))
    require(all(not os.path.lexists(path) for path in FORMAL_PATHS),
            "V4 static self-test created a formal C2 path")

    result = {
        "status": "PASS_S47_C2_V4_CANDIDATE_STATIC_SELFTEST",
        "python": {
            "version": ".".join(str(value) for value in sys.version_info[:3]),
            "executable": sys.executable,
            "isolated": sys.flags.isolated == 1,
            "dont_write_bytecode": sys.dont_write_bytecode,
            "no_site": sys.flags.no_site == 1,
        },
        "scope": "standard-library source/AST/config and disposable synthetic adversarial checks only",
        "row": "C2",
        "seed": 44,
        "source_count": 219,
        "formal_gate_calls": 0,
        "prepare_calls": 0,
        "attach_calls": 0,
        "authorization_main_calls": 0,
        "launcher_main_calls": 0,
        "worker_calls": 0,
        "model_or_scientific_imports": 0,
        "generation_calls": 0,
        "input_image_body_bytes_read": 0,
        "pixels_decoded": 0,
        "formal_paths_created": 0,
        "checks": {
            "launcher_full_ast_reversible": True,
            "runtime_full_ast_reversible": True,
            "cli_exact_split_only": True,
            "cli_negative_cases": sorted(cli_negative),
            "external_worker_without_capability_rejected": True,
            "worker_cli_dispatch_absent": True,
            "fork_inherited_opaque_capability": True,
            "fork_capability_synthetic_child_returncode": fork_returncode,
            "valid_capability_consumed_once": True,
            "capability_replay_rejected": replay_rejected,
            "capability_wrong_parent_rejected": forged_rejected,
            "same_fd_path_replacement_retained_original_snapshot": True,
            "snapshot_negative_matrix": snapshot_negative,
            "authorization_fixed_failed_lease_blocks_retry": lease_retry_rejected,
            "legacy_unpublished_boolean_rejected": True,
            "fixed_preflight_status_is_not_pass": True,
            "runtime_manifest_snapshot_detached": True,
            "runtime_temp_symlink_rejected": temp_symlink_rejected,
            "runtime_destination_symlink_rejected": destination_symlink_rejected,
            "runtime_directory_inode_swap_detected": directory_swap_rejected,
        },
        "candidate_sha256": {path.name: sha(path) for path in PRODUCTION},
        "static_selftest_sha256": sha(HERE / "static_selftest.py"),
        "withdrawn_history": {
            "v3_selftest": {
                "sha256": sha(HERE / "CANDIDATE_STATIC_SELFTEST_V3.json"),
                "authority": "NONE",
            },
            "blocked_primary": {
                "sha256": sha(HERE / "FREEZE_TOOL_SOURCE_REVIEW_V2.json"),
                "authority": "NONE",
            },
            "blocked_adversarial": {
                "sha256": sha(HERE / "FREEZE_TOOL_SOURCE_REVIEW_V2_ADVERSARIAL.json"),
                "authority": "NONE",
            },
        },
        "formal_lexists": {str(path): os.path.lexists(path) for path in FORMAL_PATHS},
        "next_gate": "TWO_NEW_DIFFERENT_AUTHOR_V4_EIGHT_FILE_SOURCE_REVIEWS_BEFORE_UNIQUE_PREPARE",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
