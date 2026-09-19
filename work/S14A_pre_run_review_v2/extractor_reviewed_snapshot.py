#!/usr/bin/env python3
"""Extract fixed S14A diagnostics from 30 hash-allowlisted pre-score JSON files.

No fitting, routing, selection, GT, support arrays, image/model I/O, or imports
from the experimental runners. The caller must freeze a manifest first.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import platform
import struct
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path


SCHEMA = "s14a-prediction-feature-manifest-v1"
FEATURE_COLUMNS = (
    "candidate_intersection_count", "candidate_jaccard",
    "selected_intersection_count", "selected_jaccard",
    "source_weight_hhi", "source_weight_max_share",
    "source_weight_normalized_entropy", "source_weight_gap_14_15_raw",
    "pose_query_distance_gap_14_15_f32",
    "source_selected_query_distance_mean_f32",
    "pose_selected_query_distance_mean_f32",
    "source_selected_pair_distance_mean_f64",
    "source_selected_pair_distance_min_f64",
    "pose_selected_pair_distance_mean_f64",
    "pose_selected_pair_distance_min_f64",
)
METADATA_COLUMNS = ("stage", "block", "query", "split", "arm", "stride")


def now():
    return datetime.now(timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def no_duplicate_keys(pairs):
    obj = {}
    for key, value in pairs:
        require(key not in obj, f"Duplicate JSON key: {key}")
        obj[key] = value
    return obj


def decode(data):
    return json.loads(data, object_pairs_hook=no_duplicate_keys)


def dump(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def finite(value, label):
    require(type(value) in (int, float), f"Non-numeric {label}")
    require(math.isfinite(value) and value >= 0, f"Nonfinite/negative {label}")
    return float(value)


def saved_binary32_unit_value(value, label):
    """The pinned vote weights/gap must be exact finite binary32 values in [0, 1]."""
    value = finite(value, label)
    require(value <= 1, f"Outside source-weight range [0,1]: {label}")
    rounded = struct.unpack(">f", struct.pack(">f", value))[0]
    require(rounded == value, f"Saved value is not exactly binary32: {label}")
    return value


def binary32_weight_difference(left, right):
    """IEEE binary32 subtraction, round-to-nearest/ties-to-even, for 1>=a>=b>=0.

    Exact rational distances choose between the binary32 estimate and its two
    neighbors, avoiding an assumption that Python's binary64 subtraction itself
    is exact. Unit-range, exactly-binary32 operands preclude overflow; their
    binary64 difference cannot misplace the initial binary32 estimate by >1 ulp.
    Subnormal inputs are included; no tolerance or flush-to-zero is introduced.
    """
    left = saved_binary32_unit_value(left, "14th source weight")
    right = saved_binary32_unit_value(right, "15th source weight")
    require(left >= right, "Source weights are not descending")
    exact = Fraction.from_float(left) - Fraction.from_float(right)
    bits = struct.unpack(">I", struct.pack(">f", left-right))[0]
    candidates = range(max(0, bits-1), min(0x3F800000, bits+1)+1)

    def value_of(pattern):
        return struct.unpack(">f", struct.pack(">I", pattern))[0]

    best = min(candidates, key=lambda pattern: (
        abs(Fraction.from_float(value_of(pattern))-exact), pattern & 1))
    return value_of(best)


def validated_saved_weight_gap(weights, saved):
    require(len(weights) >= 15, "Fewer than fifteen source weights")
    ranked = sorted((saved_binary32_unit_value(w, "source weight") for w in weights), reverse=True)
    saved = saved_binary32_unit_value(saved, "saved source weight gap")
    require(binary32_weight_difference(ranked[13], ranked[14]) == saved,
            "Saved FP32 14/15 source weight gap mismatch")
    return saved


def ids(value, n, label):
    require(type(value) is list and len(value) == n, f"Wrong length: {label}")
    require(all(type(v) is int and 0 <= v < 20 for v in value), f"Bad ID: {label}")
    require(len(set(value)) == n, f"Duplicate ID: {label}")
    return list(value)


def prediction_path(stage, block):
    folder = "S7_event_replay" if stage == "S7" else "S8_event_replay_v2"
    return f"results/{folder}/block{block}_stride8/prediction_only_selection.json"


def pose_path(stage, block, query):
    return f"results/S12_matched_budget/selections/{stage}_block{block}_query{query}.json"


def expected_paths():
    result = set()
    for stage in ("S7", "S8"):
        for block in range(3):
            result.add(prediction_path(stage, block))
            result.update(pose_path(stage, block, q) for q in range(20, 24))
    return result


def validate_manifest(manifest, source_sha):
    require(manifest["schema"] == SCHEMA, "Manifest schema mismatch")
    require(manifest["extractor_sha256"] == source_sha, "Extractor source SHA mismatch")
    entries = manifest["inputs"]
    require(type(entries) is list and len(entries) == 30, "Exactly 30 inputs required")
    mapping = {}
    for entry in entries:
        require(set(entry) == {"path", "sha256"}, "Input entry fields differ")
        rel, digest = entry["path"], entry["sha256"]
        require(rel in expected_paths() and rel not in mapping, "Forbidden/duplicate input path")
        require(type(digest) is str and len(digest) == 64
                and all(c in "0123456789abcdef" for c in digest), "Invalid input SHA")
        mapping[rel] = digest
    require(set(mapping) == expected_paths(), "Input domain mismatch")
    return mapping


def verified_bytes(path, digest):
    data = path.read_bytes()
    require(sha(data) == digest, f"Input SHA mismatch: {path}")
    return data


def safe_input_path(root, rel):
    path = root / rel
    require(path.resolve() == path, f"Symlink/path redirection forbidden: {rel}")
    require(path.is_file(), f"Input is not a file: {rel}")
    return path


def weight_statistics(pairs):
    """Normalize saved source-vote weights, never candidate allocation counts.

    HHI=sum(p_i^2); normalized entropy=-sum(p_i log p_i)/log(n).
    Zero entries remain in n; a valid singleton has entropy zero.
    """
    require(type(pairs) is list and pairs, "Empty weights")
    require(all(type(p) is list and len(p) == 2 for p in pairs), "Bad weight pair")
    keys = ids([p[0] for p in pairs], len(pairs), "weight IDs")
    values = [finite(p[1], "source weight") for p in pairs]
    total = math.fsum(values)
    require(math.isfinite(total) and total > 0, "Nonpositive/nonfinite weight sum")
    normalized = [v / total for v in values]
    entropy = -math.fsum(p * math.log(p) for p in normalized if p > 0)
    return dict(hhi=math.fsum(p*p for p in normalized), max_share=max(normalized),
                normalized_entropy=entropy/math.log(len(values)) if len(values) > 1 else 0.0,
                total=total, ids=keys)


def project_trace(trace):
    """Explicit field whitelist. Unlisted fields never enter feature rows."""
    steps = []
    for index, step in enumerate(trace["steps"]):
        if "fallback_added" in step:
            require(not step["fallback_added"], "NMS fallback has no complete accepted-pair proof")
        if "frame" in step:
            steps.append(dict(index=index, frame=step["frame"],
                              accepted=step["accepted"], comparisons=step["comparisons"]))
    return dict(selected=trace["selected"], candidates=trace["expanded_candidates"],
                distances=trace["distances_float32"], ranked=trace["sorted_frames"],
                nms=trace["nms"], steps=steps)


def selected_pairs(trace):
    """Use only comparisons at each selected frame's accepted NMS step.

    They must name all earlier selected IDs, giving exactly six distinct pairs.
    Rejected comparisons and unvisited pairs are not substitutes for missing data.
    """
    chosen = ids(trace["selected"], 4, "selected")
    require(trace["nms"] is True, "Expected original NMS trace")
    accepted = []
    for step in trace["steps"]:
        require(type(step["accepted"]) is bool, "Invalid accepted flag")
        ids([step["frame"]], 1, "step frame")
        for comparison in step["comparisons"]:
            require(type(comparison) is list and len(comparison) == 2, "Bad NMS comparison")
            ids([comparison[0]], 1, "comparison frame")
            finite(comparison[1], "saved pair distance")
        if step["accepted"]:
            accepted.append(step)
    require([s["frame"] for s in accepted] == chosen[1:], "Accepted-step/selected order mismatch")
    values, provenance = [], []
    for position, step in enumerate(accepted, start=1):
        require([c[0] for c in step["comparisons"]] == chosen[:position],
                "Missing/duplicate selected pair in accepted step")
        for comp_index, (other, value) in enumerate(step["comparisons"]):
            values.append(float(value))
            provenance.append(dict(pair=sorted([step["frame"], other]),
                                   step_index=step["index"], comparison_index=comp_index,
                                   saved_distance=float(value)))
    expected = {tuple(sorted(p)) for p in itertools.combinations(chosen, 2)}
    require(len(values) == 6 and {tuple(p["pair"]) for p in provenance} == expected,
            "Six selected-pair distances unavailable")
    return dict(mean=math.fsum(values)/6, minimum=min(values), pairs=provenance)


def overlap(a, b):
    common = len(set(a) & set(b))
    return common, common / len(set(a) | set(b))


def validate_trace_distances(trace, distance_map):
    candidates = ids(trace["candidates"], 14, "trace candidates")
    ranked = ids(trace["ranked"], 14, "trace ranked candidates")
    require(set(ranked) == set(candidates), "Trace candidate/ranked domain mismatch")
    require(len(trace["distances"]) == 14, "Trace distance length mismatch")
    for frame, value in zip(candidates, trace["distances"]):
        require(finite(value, "trace query distance") == distance_map[frame],
                "Trace/full20 query distance mismatch")
    require([distance_map[i] for i in ranked] == sorted(distance_map[i] for i in candidates),
            "Trace distance order mismatch")
    require(set(ids(trace["selected"], 4, "trace selected")) <= set(candidates),
            "Selected ID outside candidates")


def extract_row(stage, block, query, source_document, pose_document):
    split = "development" if stage == "S7" and block == 0 else "test"
    require((source_document["block"], source_document["stride"], source_document["split"])
            == (block, 8, split), "Source metadata mismatch")
    queries = source_document["queries"]
    require([q["frame"] for q in queries] == list(range(20, 24)), "Source query domain mismatch")
    choice = queries[query-20]["maps"]["A0P0"]
    official = choice["official_trace"]
    source = project_trace(choice["readouts"]["official"])
    require((pose_document["stage"], pose_document["block"], pose_document["query"],
             pose_document["split"]) == (stage, block, query, split), "Pose metadata mismatch")
    pose = project_trace(pose_document["trace"])
    frame_order = ids(pose_document["full20_frame_order"], 20, "full20 frame order")
    require(frame_order == list(range(20)), "Full20 source order mismatch")
    require(len(pose_document["full20_distances_float32"]) == 20, "Full20 distance length")
    distances = {i: finite(d, "full20 query distance")
                 for i, d in zip(frame_order, pose_document["full20_distances_float32"])}
    ranked = ids(pose_document["full20_sorted_frames"], 20, "full20 ranked")
    require(len(set(distances.values())) == 20, "Unexpected full20 FP32 tie")
    require([distances[i] for i in ranked] == sorted(distances.values()), "Full20 order mismatch")
    pose_candidates = ids(pose_document["pose14_ranked_candidates"], 14, "pose14")
    require(pose_candidates == ranked[:14], "Pose14 does not match stored full20 order")
    require(set(pose_candidates) == set(pose["candidates"]), "Pose candidate identity mismatch")
    counts = official["candidate_counts"]
    require(type(counts) is list and all(type(p) is list and len(p) == 2 for p in counts),
            "Malformed candidate allocations")
    require(ids([p[0] for p in counts], 20, "allocation IDs") == frame_order,
            "Allocation frame domain mismatch")
    require(all(type(p[1]) is int and p[1] in (0, 1) for p in counts),
            "Expected saved unique zero/one allocations, not repeated candidate votes")
    source_candidates = ids(official["candidates"], 14, "source14")
    require(source_candidates == [i for i, n in counts if n] == source["candidates"],
            "Source candidate identities mismatch")
    require(official["selected"] == source["selected"], "Source selected identities mismatch")
    weight_summary = weight_statistics(official["weights"])
    require(weight_summary["ids"] == frame_order, "Expected all20 source weights")
    # Original select() subtracts NumPy FP32 scalars before converting to float.
    # Use the verified saved value as the feature, rather than a new FP64 gap.
    gap = validated_saved_weight_gap([w for _, w in official["weights"]],
                                    official["cutoff_gap_14_15"])
    validate_trace_distances(source, distances)
    validate_trace_distances(pose, distances)
    source_pair, pose_pair = selected_pairs(source), selected_pairs(pose)
    nc, jc = overlap(source_candidates, pose_candidates)
    ns, js = overlap(source["selected"], pose["selected"])
    features = dict(zip(FEATURE_COLUMNS, (
        nc, jc, ns, js, weight_summary["hhi"], weight_summary["max_share"],
        weight_summary["normalized_entropy"], gap,
        distances[ranked[14]] - distances[ranked[13]],
        math.fsum(distances[i] for i in source["selected"])/4,
        math.fsum(distances[i] for i in pose["selected"])/4,
        source_pair["mean"], source_pair["minimum"], pose_pair["mean"], pose_pair["minimum"],
    )))
    require(all(math.isfinite(v) for v in features.values()), "Nonfinite output feature")
    row = dict(stage=stage, block=block, query=query, split=split, arm="A0P0", stride=8,
               **features)
    provenance = dict(stage=stage, block=block, query=query,
                      source_path=prediction_path(stage, block), pose_path=pose_path(stage, block, query),
                      source_pointer=f"/queries/{query-20}/maps/A0P0",
                      source_candidates=source_candidates, pose_candidates=pose_candidates,
                      source_selected=source["selected"], pose_selected=pose["selected"],
                      weight_sum_before_normalization=weight_summary["total"],
                      source_pair_provenance=source_pair["pairs"], pose_pair_provenance=pose_pair["pairs"],
                      selected_pair_observations_used=12)
    return row, provenance


def run(root, manifest_path, output):
    require(not output.exists(), "Output directory already exists; choose a new directory")
    root = root.resolve()
    source_path = Path(__file__).resolve()
    source_bytes = source_path.read_bytes()
    manifest_bytes = manifest_path.read_bytes()
    manifest = decode(manifest_bytes)
    mapping = validate_manifest(manifest, sha(source_bytes))
    output.mkdir(parents=True, exist_ok=False)
    metadata = dict(schema="s14a-prediction-feature-run-v1", status="running", started_utc=now(),
                    root=str(root), manifest_path=str(manifest_path.resolve()),
                    manifest_sha256=sha(manifest_bytes), extractor_sha256=sha(source_bytes),
                    environment=dict(python=sys.version, executable=sys.executable, platform=platform.platform(),
                                     numerical_dependencies="Python standard library only"),
                    feature_columns=list(FEATURE_COLUMNS), metadata_columns=list(METADATA_COLUMNS),
                    counters=dict(input_hash_read_attempts_before=0, input_hash_verified_before=0,
                                  json_documents_decoded=0, input_hash_read_attempts_after=0,
                                  input_hash_verified_after=0, rows=0, selected_pair_observations_used=0),
                    scientific_scope="24 already-seen queries; unlabeled diagnostic extraction only; no new selection or fitted model")
    try:
        # Hash every experimental file before decoding any one of them.
        payloads, before = {}, {}
        for rel in sorted(mapping):
            metadata["counters"]["input_hash_read_attempts_before"] += 1
            payloads[rel] = verified_bytes(safe_input_path(root, rel), mapping[rel])
            before[rel] = sha(payloads[rel])
            metadata["counters"]["input_hash_verified_before"] += 1
        metadata["all_inputs_hash_verified_utc"] = now()
        documents = {}
        for rel, payload in payloads.items():
            documents[rel] = decode(payload)
            metadata["counters"]["json_documents_decoded"] += 1
        rows, lineage = [], []
        for stage in ("S7", "S8"):
            for block in range(3):
                for query in range(20, 24):
                    row, origin = extract_row(stage, block, query,
                        documents[prediction_path(stage, block)], documents[pose_path(stage, block, query)])
                    origin["source_sha256"] = before[origin["source_path"]]
                    origin["pose_sha256"] = before[origin["pose_path"]]
                    rows.append(row)
                    lineage.append(origin)
                    metadata["counters"]["rows"] += 1
                    metadata["counters"]["selected_pair_observations_used"] += origin["selected_pair_observations_used"]
        after = {}
        for rel in sorted(mapping):
            metadata["counters"]["input_hash_read_attempts_after"] += 1
            after[rel] = sha(verified_bytes(safe_input_path(root, rel), mapping[rel]))
            metadata["counters"]["input_hash_verified_after"] += 1
        require(before == after, "Inputs changed during extraction")
        source_after = source_path.read_bytes()
        manifest_after = manifest_path.read_bytes()
        require(source_after == source_bytes, "Source changed during extraction")
        require(manifest_after == manifest_bytes, "Manifest changed during extraction")
        metadata["extractor_sha256_after"] = sha(source_after)
        metadata["manifest_sha256_after"] = sha(manifest_after)
        require(len(rows) == 24 and metadata["counters"]["selected_pair_observations_used"] == 288,
                "Actual row/pair count differs")
        dump(output/"input_identity.json", dict(before=before, after=after))
        dump(output/"features.json", dict(feature_columns=list(FEATURE_COLUMNS),
             metadata_columns=list(METADATA_COLUMNS), rows=rows))
        with (output/"features.csv").open("x", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=METADATA_COLUMNS+FEATURE_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        dump(output/"row_provenance.json", lineage)
        (output/"frozen_manifest.json").write_bytes(manifest_bytes)
        (output/"extractor_snapshot.py").write_bytes(source_bytes)
        metadata.update(status="completed", completed_utc=now(), before_after_identity_pass=True,
                        output_sha256={p.name: sha(p.read_bytes()) for p in output.iterdir() if p.is_file()})
    except Exception as error:
        metadata.update(status="failed", completed_utc=now(), error_type=type(error).__name__, error=str(error))
        dump(output/"run_metadata.json", metadata)
        raise
    dump(output/"run_metadata.json", metadata)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--manifest", type=Path, required=True,
                        help="Frozen 30-input SHA allowlist and extractor SHA")
    parser.add_argument("--output", type=Path, required=True, help="New output directory; never overwritten")
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.manifest, args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
