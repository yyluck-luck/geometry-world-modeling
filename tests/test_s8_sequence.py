"""S8 controller boundary tests; synthetic bytes/arrays only, no model or download."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_s8_sequence as s8


class TestS8Manifest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data = Path(self.temp.name) / "data"
        self.data.mkdir()
        self.protocol = deepcopy(s8.PROTOCOL_CONTRACT)
        self.protocol_sha = "a" * 64
        self.manifest = {"protocol_sha256": self.protocol_sha, "runner_sha256": s8.RUNNER_SHA, "blocks": []}
        for bid, split in enumerate(self.protocol["splits"]):
            block = {"block": bid, "split": split, "frames": []}
            for i in range(24):
                frame = {"frame": i}
                for kind in ("rgb", "depth"):
                    relative = f"{kind}_{bid}_{i}.bin"
                    # Deliberately not valid image bytes: validation must not decode depth.
                    content = relative.encode("ascii")
                    (self.data / relative).write_bytes(content)
                    frame[kind] = {"timestamp": bid * 100 + i + (0.01 if kind == "depth" else 0), "path": relative}
                    frame[kind + "_sha256"] = hashlib.sha256(content).hexdigest()
                block["frames"].append(frame)
            self.manifest["blocks"].append(block)

    def validate(self):
        return s8.validate_manifest(self.manifest, self.data, self.protocol_sha, self.protocol)

    def test_valid_72_inputs_and_depth_is_integrity_only(self):
        blocks, identities = self.validate()
        self.assertEqual(len(identities), 72)
        self.assertEqual([len(b["images"]) for b in blocks], [24] * 3)
        self.assertTrue(all("rgb_" in path.name for b in blocks for path in b["images"]))

    def test_parent_and_absolute_paths_are_rejected(self):
        for value in ("../outside", str(self.data / "rgb_0_0.bin"), "rgb/../rgb_0_0.bin", "C:\\a.png",
                      "./rgb_0_0.bin", "a//b.png"):
            with self.subTest(path=value), self.assertRaises(ValueError):
                s8.safe_data_path(self.data, value)

    def test_symlink_escape_is_rejected(self):
        outside = Path(self.temp.name) / "outside.bin"
        outside.write_bytes(b"outside")
        (self.data / "escape.bin").symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "inside --data"):
            s8.safe_data_path(self.data, "escape.bin")

    def test_duplicate_rgb_between_blocks_is_rejected(self):
        first = self.manifest["blocks"][0]["frames"][0]
        other = self.manifest["blocks"][1]["frames"][0]
        other["rgb"] = deepcopy(first["rgb"])
        other["rgb_sha256"] = first["rgb_sha256"]
        with self.assertRaisesRegex(ValueError, "Duplicate rgb"):
            self.validate()

    def test_copied_bytes_and_hardlink_alias_are_rejected(self):
        original = self.data / "rgb_0_0.bin"
        second = self.data / "rgb_1_0.bin"
        second.write_bytes(original.read_bytes())
        self.manifest["blocks"][1]["frames"][0]["rgb_sha256"] = s8.sha(original)
        with self.assertRaisesRegex(ValueError, "Duplicate rgb sha256"):
            self.validate()
        second.unlink()
        second.hardlink_to(original)
        with self.assertRaisesRegex(ValueError, "Duplicate rgb inode"):
            self.validate()

    def test_duplicate_depth_between_blocks_is_rejected(self):
        first = self.manifest["blocks"][0]["frames"][0]
        other = self.manifest["blocks"][1]["frames"][0]
        other["depth"] = deepcopy(first["depth"])
        other["depth_sha256"] = first["depth_sha256"]
        with self.assertRaisesRegex(ValueError, "Duplicate depth"):
            self.validate()

    def test_unsorted_and_nonfinite_timestamps_rejected(self):
        frames = self.manifest["blocks"][0]["frames"]
        frames[1]["rgb"]["timestamp"] = -1
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            self.validate()
        frames[1]["rgb"]["timestamp"] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite numeric"):
            self.validate()

    def test_wrong_protocol_or_runner_and_hash_rejected(self):
        for key in ("protocol_sha256", "runner_sha256"):
            prior = self.manifest[key]
            self.manifest[key] = "b" * 64
            with self.subTest(field=key), self.assertRaisesRegex(ValueError, key):
                self.validate()
            self.manifest[key] = prior
        self.manifest["blocks"][0]["frames"][0]["depth_sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "integrity mismatch"):
            self.validate()

    def test_frame_count_and_split_cannot_silently_change(self):
        self.manifest["blocks"][1]["split"] = "development"
        with self.assertRaisesRegex(ValueError, "split mismatch"):
            self.validate()
        self.manifest["blocks"][1]["split"] = "test"
        self.manifest["blocks"][1]["frames"].pop()
        with self.assertRaisesRegex(ValueError, "24 frames"):
            self.validate()


class TestS8ProtocolAndState(unittest.TestCase):
    def test_protocol_machine_fence_and_policy_declarations(self):
        contract = deepcopy(s8.PROTOCOL_CONTRACT)
        body = json.dumps(contract)
        self.assertEqual(s8.parse_protocol(body), contract)
        self.assertEqual(s8.parse_protocol("# Protocol\n\n```s8-controller-json\n" + body + "\n```\n"), contract)
        custom = dict(contract, splits=["development", "test", "test"])
        self.assertEqual(s8.parse_protocol(json.dumps(custom))["splits"], custom["splits"])
        self.assertEqual(contract["splits"], ["test"] * 3)
        with self.assertRaisesRegex(ValueError, "splits"):
            s8.parse_protocol(json.dumps(dict(contract, splits=["test"])))
        for key, value in (("history_count", 24), ("query_updates_state", True), ("cpu_threads", 16),
                           ("depth_sent_to_model", True), ("seed", False)):
            changed = dict(contract, **{key: value})
            with self.subTest(field=key), self.assertRaisesRegex(ValueError, key):
                s8.parse_protocol(json.dumps(changed))
        with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
            s8.read_json('{"a":1,"a":2}')

    def state_record(self):
        flags = s8.expected_flags()
        raw = {key: deepcopy(flags) for key in ("requested_view_flags", "prepared_view_flags",
                                                "view_flags_before_inference", "view_flags_after_inference")}
        raw.update(history_count=20, query_count=4, view_policy_preserved=True, history_only_memory_ok=True)
        checks = []
        for field, shape in (("state_feat", [1, 768, 768]), ("pose_memory", [1, 256, 1536])):
            for index in range(21, 25):
                checks.append({"field": field, "snapshot_index": index, "after_view": index - 1,
                               "shape": shape, "anchor_shape": shape, "dtype": "torch.float32",
                               "anchor_dtype": "torch.float32", "exactly_unchanged": True, "finite": True,
                               "anchor_finite": True, "same_shape_and_dtype": True, "max_absolute_difference": 0,
                               "tensor_sha256": "a" * 64, "anchor_tensor_sha256": "a" * 64})
        raw["query_state_write_audit"] = {"ok": True, "expected_snapshots": 25, "actual_snapshots": 25,
            "anchor_snapshot_index": 20, "history_count": 20, "query_count": 4,
            "fields": {"state_feat": 0, "pose_memory": 3}, "checks": checks}
        return raw

    def test_query_write_and_missing_or_changed_state_records_fail(self):
        raw = self.state_record()
        self.assertTrue(s8.verify_query_policy(raw)["ok"])
        self.assertEqual([flag["update"] for flag in s8.expected_flags()], [[True]] * 20 + [[False]] * 4)
        raw["view_flags_after_inference"][20]["update"] = [True]
        with self.assertRaisesRegex(ValueError, "view flags"):
            s8.verify_query_policy(raw)
        raw = self.state_record()
        raw["query_state_write_audit"]["checks"].pop()
        with self.assertRaisesRegex(ValueError, "coverage"):
            s8.verify_query_policy(raw)
        raw = self.state_record()
        raw["query_state_write_audit"]["checks"][0]["tensor_sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "hashes differ"):
            s8.verify_query_policy(raw)

    def test_existing_output_is_preserved_and_failed_preflight_recorded(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            existing = root / "previous"
            existing.mkdir()
            sentinel = existing / "sentinel"
            sentinel.write_text("preserve")
            command = [sys.executable, str(ROOT / "scripts/run_s8_sequence.py")]
            for flag in ("manifest", "protocol", "repo", "data", "checkpoint", "signed-rope-check"):
                command += ["--" + flag, str(root / "missing")]
            rejected = subprocess.run(command + ["--output", str(existing)], capture_output=True, text=True)
            self.assertEqual(rejected.returncode, 2)
            self.assertEqual(sentinel.read_text(), "preserve")
            self.assertEqual(list(existing.iterdir()), [sentinel])
            failed = root / "attempt"
            result = subprocess.run(command + ["--output", str(failed)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            metadata = json.loads((failed / "sequence_metadata.json").read_text())
            self.assertEqual(metadata["phase"], "failed")
            self.assertFalse(metadata["ok"])
            self.assertEqual(metadata["blocks"], [])
            self.assertTrue((failed / "sequence_runner_snapshot.py").is_file())


class TestS8ActualArrayVerification(unittest.TestCase):
    def test_schema_finiteness_and_metadata_are_checked_against_saved_arrays(self):
        # Smaller tensor shapes keep this parser boundary test tiny. All 24*7 keys
        # remain present; production constants are restored after the context.
        shapes = {key: [1, 2] for key in s8.ARRAY_SHAPES}
        values = {f"frame{i}_{key}": np.ones(shape, dtype=np.float32)
                  for i in range(24) for key, shape in shapes.items()}
        stats = {key: {"shape": list(value.shape), "dtype": "float32", "all_finite": True,
                       "finite_fraction": 1.0, "min": 1.0, "max": 1.0} for key, value in values.items()}
        first = next(iter(values))
        with tempfile.TemporaryDirectory() as temp, patch.dict(s8.ARRAY_SHAPES, shapes, clear=True):
            path = Path(temp) / "arrays.npz"
            np.savez(path, **values)
            self.assertEqual(len(s8.verify_output_arrays(path, stats)), 168)
            stats[first]["max"] = 2.0
            with self.assertRaisesRegex(ValueError, "statistics differ"):
                s8.verify_output_arrays(path, stats)
            stats[first]["max"] = 1.0
            values[first][0, 0] = np.nan
            np.savez(path, **values)
            with self.assertRaisesRegex(ValueError, "Nonfinite actual prediction"):
                s8.verify_output_arrays(path, stats)
            values[first] = np.ones((1, 3), dtype=np.float32)
            np.savez(path, **values)
            with self.assertRaisesRegex(ValueError, "schema differs"):
                s8.verify_output_arrays(path, stats)


class TestS8ResourceFailure(unittest.TestCase):
    def test_timeout_and_rss_failure_stop_child_and_preserve_evidence(self):
        # A tiny sleeping Python child exercises actual termination without loading
        # torch, reading a checkpoint, using data, or contacting a network service.
        for patch_name, limit, reason in (("TIMEOUT_SECONDS", 0.01, "timeout"),
                                           ("MAX_RSS_BYTES", 1, "observed_rss_budget_exceeded")):
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as temp:
                log = Path(temp) / "block.log"
                entry = {}
                command = [sys.executable, "-c", "import time; time.sleep(30)"]
                with patch.object(s8, patch_name, limit), self.assertRaisesRegex(ValueError, "Block failed"):
                    s8.run_monitored(command, log, entry, lambda: None)
                self.assertEqual(entry["stop_reason"], reason)
                self.assertIsNotNone(entry["returncode"])
                self.assertTrue(log.is_file())
                self.assertTrue(log.with_suffix(".rss.json").is_file())
                self.assertTrue(json.loads(log.with_suffix(".rss.json").read_text())["samples"])


if __name__ == "__main__":
    unittest.main()
