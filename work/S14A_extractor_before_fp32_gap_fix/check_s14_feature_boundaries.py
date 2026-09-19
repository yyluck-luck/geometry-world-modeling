#!/usr/bin/env python3
"""Artificial boundary checks only; never open the 30 actual experimental inputs."""
import argparse
import copy
import importlib.util
import json
import math
import platform
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Refuse existing output")
    args.output.mkdir(parents=True)
    src = Path(__file__).with_name("extract_s14_prediction_features.py")
    spec = importlib.util.spec_from_file_location("s14_extractor", src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rows = []
    receipt = dict(started_utc=datetime.now(timezone.utc).isoformat(), status="running",
                   scope="Artificial inputs only, same-author boundary checks; no independent review",
                   extractor_sha256=mod.sha(src.read_bytes()), checker_sha256=mod.sha(Path(__file__).read_bytes()),
                   environment=dict(python=sys.version, executable=sys.executable, platform=platform.platform()),
                   real_experimental_files_opened=0, real_feature_rows=0, checks=rows)

    def check(name, function, expected_error=None):
        try:
            function()
        except Exception as error:
            if expected_error is None or not isinstance(error, expected_error):
                rows.append(dict(name=name, passed=False, error=str(error)))
                raise
            rows.append(dict(name=name, passed=True, rejected=str(error)))
        else:
            if expected_error:
                raise AssertionError(f"{name}: expected rejection did not occur")
            rows.append(dict(name=name, passed=True))

    def close(actual, expected):
        assert math.isclose(actual, expected, rel_tol=0, abs_tol=1e-14), (actual, expected)

    def weight_known():
        s = mod.weight_statistics([[0, 1], [1, 1]])
        assert s["hhi"] == .5 and s["max_share"] == .5 and s["normalized_entropy"] == 1
        s = mod.weight_statistics([[0, 2], [1, 0]])
        assert s["hhi"] == 1 and s["max_share"] == 1 and s["normalized_entropy"] == 0
        assert mod.weight_statistics([[0, 2]])["normalized_entropy"] == 0

    def trace(chosen, base):
        steps, value = [], base
        for position, frame in enumerate(chosen[1:], 1):
            comparisons = []
            for earlier in chosen[:position]:
                comparisons.append([earlier, float(value)])
                value += 1
            steps.append(dict(frame=frame, accepted=True, comparisons=comparisons))
        return dict(selected=chosen, expanded_candidates=list(range(14)), sorted_frames=list(range(14)),
                    distances_float32=list(range(1, 15)), nms=True, steps=steps)

    source_trace, pose_trace = trace([0, 1, 2, 3], 1), trace([0, 4, 5, 6], 7)
    source_doc = dict(block=0, stride=8, split="development", queries=[
        dict(frame=q, maps=dict(A0P0=dict(official_trace=dict(
            selected=source_trace["selected"], candidates=list(range(14)),
            candidate_counts=[[i, int(i < 14)] for i in range(20)],
            weights=[[i, 1.0] for i in range(20)], cutoff_gap_14_15=0.0),
            readouts=dict(official=source_trace)))) for q in range(20, 24)])
    pose_doc = dict(stage="S7", block=0, query=20, split="development", trace=pose_trace,
                    full20_frame_order=list(range(20)), full20_distances_float32=list(range(1, 21)),
                    full20_sorted_frames=list(range(20)), pose14_ranked_candidates=list(range(14)))

    def known_row():
        row, lineage = mod.extract_row("S7", 0, 20, source_doc, pose_doc)
        expected = [14, 1, 1, 1/7, .05, .05, 1, 0, 1, 2.5, 4.75, 3.5, 1, 9.5, 7]
        assert set(row) == set(mod.METADATA_COLUMNS + mod.FEATURE_COLUMNS)
        for key, value in zip(mod.FEATURE_COLUMNS, expected):
            close(row[key], value)
        assert len(lineage["source_pair_provenance"]) == len(lineage["pose_pair_provenance"]) == 6

    def changed_trace(key, value):
        t = copy.deepcopy(source_trace)
        if key == "missing":
            t["steps"][-1]["comparisons"].pop()
        elif key == "duplicate":
            t["selected"][-1] = t["selected"][0]
        elif key == "nonfinite":
            t["steps"][-1]["comparisons"][0][1] = value
        elif key == "fallback":
            t["steps"].append(dict(fallback_added=[3]))
        return mod.selected_pairs(mod.project_trace(t))

    try:
        check("weights_hand_calculated_uniform_sparse_singleton", weight_known)
        check("weights_empty_rejected", lambda: mod.weight_statistics([]), ValueError)
        check("weights_all_zero_rejected", lambda: mod.weight_statistics([[0, 0], [1, 0]]), ValueError)
        check("weights_duplicate_id_rejected", lambda: mod.weight_statistics([[0, 1], [0, 2]]), ValueError)
        check("weights_nan_rejected", lambda: mod.weight_statistics([[0, float('nan')]]), ValueError)
        check("weights_negative_rejected", lambda: mod.weight_statistics([[0, -1]]), ValueError)
        check("row_15_features_against_hand_values", known_row)
        check("selected_missing_pair_rejected", lambda: changed_trace("missing", None), ValueError)
        check("selected_duplicate_id_rejected", lambda: changed_trace("duplicate", None), ValueError)
        check("selected_nonfinite_pair_rejected", lambda: changed_trace("nonfinite", float('inf')), ValueError)
        check("fallback_without_accepted_pair_proof_rejected", lambda: changed_trace("fallback", None), ValueError)
        check("duplicate_json_keys_rejected", lambda: mod.decode(b'{"x":1,"x":2}'), ValueError)
        with tempfile.TemporaryDirectory(prefix="s14a-artificial-") as temp:
            base = Path(temp)
            p = base/"artificial.json"
            p.write_text('{"not_an_experiment": true}')
            check("wrong_file_hash_rejected", lambda: mod.verified_bytes(p, "0"*64), ValueError)
            check("correct_file_hash_accepted", lambda: mod.verified_bytes(p, mod.sha(p.read_bytes())))
            manifest = dict(schema=mod.SCHEMA, extractor_sha256=receipt["extractor_sha256"],
                inputs=[dict(path=rel, sha256="0"*64) for rel in sorted(mod.expected_paths())])
            check("exact_path_domain_accepted_without_opening", lambda: mod.validate_manifest(manifest, receipt["extractor_sha256"]))
            check("wrong_source_hash_rejected", lambda: mod.validate_manifest(manifest, "0"*64), ValueError)
            bad = copy.deepcopy(manifest)
            bad["inputs"][0]["path"] = "results/S13_oracle_headroom_retry01/summary.json"
            check("nonallowlisted_path_rejected_without_opening", lambda: mod.validate_manifest(bad, receipt["extractor_sha256"]), ValueError)
            bad = copy.deepcopy(manifest)
            bad["inputs"][-1] = bad["inputs"][0]
            check("duplicate_manifest_input_rejected", lambda: mod.validate_manifest(bad, receipt["extractor_sha256"]), ValueError)
            check("existing_output_rejected_before_manifest_read", lambda: mod.run(base, base/"absent_manifest", base), ValueError)
        receipt.update(status="passed", check_count=len(rows), completed_utc=datetime.now(timezone.utc).isoformat())
    except Exception as error:
        receipt.update(status="failed", error=str(error), completed_utc=datetime.now(timezone.utc).isoformat())
        raise
    finally:
        mod.dump(args.output/"receipt.json", receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
