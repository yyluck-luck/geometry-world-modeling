#!/usr/bin/env python3
"""Descriptive analysis of completed RGB-D component experiments.

Geometry is counted once per (block, stride, bias, query), irrespective of the
number of retrieval resolutions. Repeated conditions in one environment are
never treated as independent scenes. No inferential tests or CIs are computed.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import csv
import hashlib
import itertools
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
METHODS = ("first_write", "frame_mean")
LABELS = {"first_write": "First write", "frame_mean": "Frame mean"}
COLORS = ("#0072B2", "#D55E00", "#009E73", "#CC79A7")


def read_json(path):
    return json.loads(Path(path).read_text())


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def key(record):
    return (int(record["block"]), int(record["stride"]), float(record["first_frame_depth_axis_bias_m"]), int(record["query"]))


def mean(values):
    values = [float(value) for value in values if value is not None and np.isfinite(value)]
    return float(np.mean(values)) if values else None


def median(values):
    values = [float(value) for value in values if value is not None and np.isfinite(value)]
    return float(np.median(values)) if values else None


def delta(a, b):
    return None if a is None or b is None else float(b - a)


def percentage(value):
    return None if value is None else float(value * 100)


def write_csv(path, rows):
    if not rows:
        raise ValueError(f"No rows for {path}")
    fields = list(dict.fromkeys(field for row in rows for field in row))
    with Path(path).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite_json(value, location="input"):
    if isinstance(value, float):
        require(np.isfinite(value), f"Nonfinite JSON number at {location}")
    elif isinstance(value, dict):
        for name, child in value.items():
            finite_json(child, f"{location}.{name}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            finite_json(child, f"{location}[{index}]")


def load_completed(directory):
    meta_path = directory / "run_metadata.json"
    record_path = directory / "records.jsonl"
    metadata = read_json(meta_path)
    finite_json(metadata, "metadata")
    require(metadata.get("completed_utc") and metadata.get("errors") == 0, "Analysis requires a completed experiment with zero errors")
    records = [json.loads(line) for line in record_path.read_text().splitlines() if line.strip()]
    finite_json(records, "records")
    records.sort(key=key)
    require(bool(records) and len(records) == len({key(row) for row in records}), "Missing or duplicate query records")
    cases, files = {}, [meta_path, record_path]
    aggregate = {key(row): row for row in records}
    case_queries = []
    for path in sorted(directory.glob("*/result.json")):
        result = read_json(path)
        finite_json(result, str(path))
        condition = (int(result["block"]), int(result["stride"]), float(result["bias_m"]))
        require(condition not in cases, f"Duplicate case {condition}")
        require(sorted(row["query"] for row in result["records"]) == [0, 1, 2, 3], f"Case {condition} must contain four unique queries")
        require(all(key(row)[:3] == condition and aggregate.get(key(row)) == row for row in result["records"]), f"Case/aggregate mismatch {condition}")
        case_queries.extend(key(row) for row in result["records"])
        cases[condition] = result
        files.append(path)
    config = metadata["config"]
    expected = set(itertools.product(config["blocks"], config["strides"], map(float, config["biases"])))
    widths = sorted(config["resolutions"])
    require(set(cases) == expected, "Completed case conditions do not equal config")
    require(len(case_queries) == len(records) == metadata["paired_queries"] and set(case_queries) == set(aggregate), "Query count does not equal completed cases")
    require(len(cases) == metadata["expected_cases"] == metadata["completed_cases"], "Case metadata count mismatch")
    require(len(records) * len(widths) == metadata["paired_retrieval_rows"], "Retrieval metadata count mismatch")
    for row in records:
        require(set(row["retrieval"]) == {str(width) for width in widths}, f"Missing retrieval resolution in {key(row)}")
        require(row["split"] == ("development" if row["block"] == 0 else "test"), f"Unexpected temporal split in {key(row)}")
        require(0 <= row["common_prediction_pixels"] <= row["valid_target_pixels"], "Invalid common pixel count")
        for method in METHODS:
            require(row["geometry"][method]["n"] == row["common_prediction_pixels"], "Primary metrics do not use the same pixels")
            for width in widths:
                selected = row["retrieval"][str(width)][method]["selected"]
                require(len(selected) == len(set(selected)) == 4 and all(0 <= i < 20 for i in selected), "Invalid four-frame selection")
        for control in ("recent4", "nearest_pose4"):
            selected = row["query_controls"][control]["selected"]
            require(len(selected) == len(set(selected)) == 4 and all(0 <= i < 20 for i in selected), "Invalid control selection")
        require("all_history_support_coverage" in row, "Missing all-history support diagnostic")
    hashes = {str(path.relative_to(directory)): sha256(path) for path in files}
    verification = directory / "verification.json"
    verification_status = None
    if verification.exists():
        verification_status = read_json(verification).get("status")
        require(verification_status == "passed", "Existing verification report has not passed")
        hashes["verification.json"] = sha256(verification)
    return metadata, records, cases, widths, hashes, verification_status


def stability(record, widths):
    out = dict(has_160_and_320=160 in widths and 320 in widths)
    if not out["has_160_and_320"]:
        return dict(out, changed_at_160=None, changed_at_320=None, changed_at_both=None,
                    changed_at_either=None, identical_transition_at_both=None)
    low, high = record["retrieval"]["160"], record["retrieval"]["320"]
    low_changed, high_changed = bool(low["selection_set_changed"]), bool(high["selection_set_changed"])
    identical = all(set(low[method]["selected"]) == set(high[method]["selected"]) for method in METHODS)
    return dict(out, changed_at_160=low_changed, changed_at_320=high_changed,
                changed_at_both=low_changed and high_changed, changed_at_either=low_changed or high_changed,
                identical_transition_at_both=low_changed and high_changed and identical)


def query_tables(records, cases, widths):
    geometry, retrieval, stable = [], [], []
    for record in records:
        identity = dict(split=record["split"], block=record["block"], stride=record["stride"],
                        bias_m=record["first_frame_depth_axis_bias_m"], query=record["query"], timestamp=record["timestamp"])
        case = cases[key(record)[:3]]
        g = dict(identity, valid_target_pixels=record["valid_target_pixels"], common_prediction_pixels=record["common_prediction_pixels"],
                 common_coverage_fraction=record["common_prediction_pixels"] / record["valid_target_pixels"] if record["valid_target_pixels"] else None,
                 all_history_support_coverage=record["all_history_support_coverage"])
        for control in ("recent4", "nearest_pose4"):
            g[f"{control}_support_coverage"] = record["query_controls"][control]["fixed_measurement_support_coverage"]
            g[f"{control}_selected"] = ",".join(map(str, record["query_controls"][control]["selected"]))
        for method in METHODS:
            for metric in ("median_abs_mm", "mae_mm", "p90_abs_mm", "within_30mm", "coverage_of_valid_target"):
                g[f"{method}_{metric}"] = record["geometry"][method][metric]
            g[f"{method}_map_points"] = case["maps"][method]["points"]
            g[f"{method}_build_seconds"] = case["maps"][method]["total_build_seconds"]
        g["median_abs_delta_mm"] = delta(g["first_write_median_abs_mm"], g["frame_mean_median_abs_mm"])
        g["mae_delta_mm"] = delta(g["first_write_mae_mm"], g["frame_mean_mae_mm"])
        g["geometry_coverage_delta_pp"] = percentage(delta(g["first_write_coverage_of_valid_target"], g["frame_mean_coverage_of_valid_target"]))
        geometry.append(g)
        stable.append(dict(identity, **stability(record, widths)))
        for width in widths:
            pair = record["retrieval"][str(width)]
            r = dict(identity, width=width, selection_set_changed=pair["selection_set_changed"],
                     coverage_delta_pp=percentage(pair["coverage_delta"]), all_history_support_coverage=record["all_history_support_coverage"])
            for control in ("recent4", "nearest_pose4"):
                r[f"{control}_support_coverage"] = g[f"{control}_support_coverage"]
            for method in METHODS:
                trace = pair[method]
                r[f"{method}_selected"] = ",".join(map(str, trace["selected"]))
                r[f"{method}_support_coverage"] = trace["fixed_measurement_support_coverage"]
                r[f"{method}_coverage_of_all_history_supported"] = trace["coverage_of_all_history_supported"]
                r[f"{method}_selection_seconds"] = trace["selection_seconds"]
                for control in ("recent4", "nearest_pose4"):
                    r[f"{method}_minus_{control}_pp"] = percentage(delta(g[f"{control}_support_coverage"], trace["fixed_measurement_support_coverage"]))
            retrieval.append(r)
    return geometry, retrieval, stable


def aggregate_group(records, cases, widths, identity):
    summary = dict(identity, queries=len(records), unique_camera_queries=len({(r["block"], r["query"]) for r in records}),
                   cases=len({key(r)[:3] for r in records}), common_pixels_total=sum(r["common_prediction_pixels"] for r in records),
                   mean_common_pixels=mean([r["common_prediction_pixels"] for r in records]),
                   mean_common_coverage_fraction=mean([r["common_prediction_pixels"] / r["valid_target_pixels"] if r["valid_target_pixels"] else None for r in records]))
    summary["mean_all_history_support_coverage"] = mean([r["all_history_support_coverage"] for r in records])
    for control in ("recent4", "nearest_pose4"):
        summary[f"{control}_mean_support_coverage"] = mean([r["query_controls"][control]["fixed_measurement_support_coverage"] for r in records])
    conditions = {key(r)[:3] for r in records}
    for method in METHODS:
        metrics = [r["geometry"][method] for r in records]
        summary[f"{method}_queries_with_geometry"] = sum(m["n"] > 0 for m in metrics)
        summary[f"{method}_mean_query_median_abs_mm"] = mean([m["median_abs_mm"] for m in metrics])
        summary[f"{method}_median_query_median_abs_mm"] = median([m["median_abs_mm"] for m in metrics])
        summary[f"{method}_mean_query_mae_mm"] = mean([m["mae_mm"] for m in metrics])
        total = sum(m["n"] for m in metrics)
        summary[f"{method}_pooled_common_mae_mm"] = sum(m["mae_mm"] * m["n"] for m in metrics if m["n"]) / total if total else None
        summary[f"{method}_mean_geometry_coverage"] = mean([m["coverage_of_valid_target"] for m in metrics])
        summary[f"{method}_mean_map_points"] = mean([cases[c]["maps"][method]["points"] for c in sorted(conditions)])
        summary[f"{method}_mean_build_seconds"] = mean([cases[c]["maps"][method]["total_build_seconds"] for c in sorted(conditions)])
    summary["mean_median_abs_delta_mm"] = mean([delta(r["geometry"]["first_write"]["median_abs_mm"], r["geometry"]["frame_mean"]["median_abs_mm"]) for r in records])
    summary["mean_mae_delta_mm"] = mean([delta(r["geometry"]["first_write"]["mae_mm"], r["geometry"]["frame_mean"]["mae_mm"]) for r in records])
    summary["mean_geometry_coverage_delta_pp"] = percentage(delta(summary["first_write_mean_geometry_coverage"], summary["frame_mean_mean_geometry_coverage"]))
    stable = [stability(r, widths) for r in records]
    for name in ("changed_at_both", "changed_at_either", "identical_transition_at_both"):
        values = [s[name] for s in stable if s[name] is not None]
        summary[f"{name}_160_320_count"] = sum(values) if values else None
    for width in widths:
        pairs = [r["retrieval"][str(width)] for r in records]
        prefix = f"width{width}"
        deltas = [p["coverage_delta"] for p in pairs if p["coverage_delta"] is not None]
        summary[f"{prefix}_changed_queries"] = sum(p["selection_set_changed"] for p in pairs)
        summary[f"{prefix}_queries_with_coverage"] = len(deltas)
        summary[f"{prefix}_mean_coverage_delta_pp"] = percentage(mean(deltas))
        summary[f"{prefix}_coverage_increased_queries"] = sum(d > 1e-12 for d in deltas)
        summary[f"{prefix}_coverage_decreased_queries"] = sum(d < -1e-12 for d in deltas)
        summary[f"{prefix}_coverage_unchanged_queries"] = sum(abs(d) <= 1e-12 for d in deltas)
        for method in METHODS:
            scores = [p[method]["fixed_measurement_support_coverage"] for p in pairs]
            summary[f"{prefix}_{method}_mean_support_coverage"] = mean(scores)
            summary[f"{prefix}_{method}_mean_coverage_of_all_history_supported"] = mean([p[method]["coverage_of_all_history_supported"] for p in pairs])
            for control in ("recent4", "nearest_pose4"):
                differences = [delta(r["query_controls"][control]["fixed_measurement_support_coverage"], r["retrieval"][str(width)][method]["fixed_measurement_support_coverage"]) for r in records]
                summary[f"{prefix}_{method}_minus_{control}_mean_pp"] = percentage(mean(differences))
    return summary


def aggregate_tables(records, cases, widths):
    case_groups, split_groups = defaultdict(list), defaultdict(list)
    for record in records:
        case_groups[key(record)[:3]].append(record)
        split_groups[(record["split"], record["stride"], float(record["first_frame_depth_axis_bias_m"]))].append(record)
    case_rows = [aggregate_group(rows, cases, widths, dict(split=rows[0]["split"], block=b, stride=s, bias_m=v))
                 for (b, s, v), rows in sorted(case_groups.items())]
    split_rows = [aggregate_group(rows, cases, widths, dict(split=split, blocks=",".join(map(str, sorted({r["block"] for r in rows}))), stride=s, bias_m=v))
                  for (split, s, v), rows in sorted(split_groups.items())]
    return case_rows, split_rows


def configure_plotting():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 11,
                         "axes.labelsize": 10, "xtick.labelsize": 9, "ytick.labelsize": 9,
                         "legend.fontsize": 9, "pdf.fonttype": 42, "ps.fonttype": 42,
                         "axes.spines.top": False, "axes.spines.right": False})
    return plt


def save_figure(fig, output, name, plt):
    for extension in ("png", "pdf"):
        fig.savefig(output / f"{name}.{extension}", dpi=180, bbox_inches="tight")
    plt.close(fig)


def equality_axes(ax, values, percent=False):
    values = [x for x in values if x is not None and np.isfinite(x)]
    upper = max(values, default=1.) * 1.08
    if percent:
        upper = min(100., max(upper, 1.))
    upper = max(upper, .01)
    ax.plot([0, upper], [0, upper], color="#666666", linestyle="--", linewidth=1, zorder=0, label="Equal values")
    ax.set(xlim=(0, upper), ylim=(0, upper))
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=.15)


def plot_raw_test(records, widths, output, plt):
    rows = [r for r in records if r["split"] == "test" and r["first_frame_depth_axis_bias_m"] == 0.]
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 5.5))
    colors = {b: COLORS[i % len(COLORS)] for i, b in enumerate(sorted({r["block"] for r in rows}))}
    markers = {s: marker for s, marker in zip(sorted({r["stride"] for r in rows}), itertools.cycle(["o", "^", "s", "D"]))}
    values = [[], []]
    legend_seen = set()
    plotted = [0, 0]
    for row in rows:
        identity = (row["block"], row["stride"])
        label = f"Block {identity[0]}, stride {identity[1]}" if identity not in legend_seen else None
        legend_seen.add(identity)
        x, y = [row["geometry"][method]["median_abs_mm"] for method in METHODS]
        if x is not None and y is not None:
            axs[0].scatter(x, y, c=colors[identity[0]], marker=markers[identity[1]], s=47, alpha=.8, edgecolors="black", linewidths=.4, label=label)
            values[0].extend([x, y]); plotted[0] += 1
        x, y = [percentage(mean([row["retrieval"][str(w)][method]["fixed_measurement_support_coverage"] for w in widths])) for method in METHODS]
        if x is not None and y is not None:
            axs[1].scatter(x, y, c=colors[identity[0]], marker=markers[identity[1]], s=47, alpha=.8, edgecolors="black", linewidths=.4)
            values[1].extend([x, y]); plotted[1] += 1
    for i, ax in enumerate(axs):
        equality_axes(ax, values[i], percent=i == 1)
        if not plotted[i]:
            ax.text(.5, .5, "No eligible observed values", transform=ax.transAxes, ha="center")
    axs[0].set(xlabel="First write: median |depth difference| (mm)", ylabel="Frame mean: median |depth difference| (mm)",
               title=f"(a) Common-pixel geometry: {plotted[0]} query conditions")
    axs[1].set(xlabel="First write: measured support coverage (%)", ylabel="Frame mean: measured support coverage (%)",
               title=f"(b) Selected-frame support: {plotted[1]} query conditions")
    if rows:
        axs[0].legend(loc="best", fontsize=8)
    fig.suptitle("Original measurements: fixed test blocks in the same environment", fontsize=12)
    fig.text(.5, .015, "Each point is one query and stride; panel (b) averages configured retrieval widths. Dashed line: equal values.\nDepth agreement and measured support are component diagnostics, not video quality.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .10, 1, .94))
    save_figure(fig, output, "raw_test_paired_comparison", plt)
    return dict(eligible_query_conditions=len(rows), plotted_geometry=plotted[0], plotted_support=plotted[1])


def case_label(row):
    return f"{'Dev' if row['split'] == 'development' else 'Test'} B{row['block']} | s{row['stride']} | +{row['bias_m'] * 1000:g} mm"


def plot_resolution_table(case_rows, widths, output, plt):
    columns = [(f"{width} px\nchanged", f"width{width}_changed_queries") for width in widths]
    if 160 in widths and 320 in widths:
        columns += [("Both widths\nchanged", "changed_at_both_160_320_count"),
                    ("Same transition\nin both", "identical_transition_at_both_160_320_count")]
    data = np.array([[row[field] / row["queries"] for _, field in columns] for row in case_rows], dtype=float)
    fig, ax = plt.subplots(figsize=(max(8.5, len(columns) * 1.5), max(5., len(case_rows) * .32 + 2.)))
    ax.imshow(data, aspect="auto", cmap="Blues", vmin=0, vmax=1)
    for i, row in enumerate(case_rows):
        for j, (_, field) in enumerate(columns):
            ax.text(j, i, f"{row[field]}/{row['queries']}", ha="center", va="center", color="white" if data[i, j] > .65 else "black", fontsize=9)
    ax.set_xticks(range(len(columns)), [label for label, _ in columns])
    ax.set_yticks(range(len(case_rows)), [case_label(row) for row in case_rows])
    ax.tick_params(axis="both", length=0)
    ax.set_title("First write versus frame mean: final selected-set changes", pad=13)
    for i in range(1, len(case_rows)):
        if case_rows[i]["block"] != case_rows[i - 1]["block"]:
            ax.axhline(i - .5, color="black", linewidth=1)
    fig.text(.5, .012, "All configured cases; each count uses the same four held-out queries. Two temporal test blocks share one environment.\nA changed set does not establish a better set. Same transition requires identical before/after sets at 160 and 320 px.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .065, 1, 1))
    save_figure(fig, output, "resolution_set_change_table", plt)


def plot_map_coverage(case_rows, widths, output, plt):
    y = np.arange(len(case_rows))
    fig, axs = plt.subplots(1, 3, figsize=(14., max(6.5, len(case_rows) * .31 + 1.8)), sharey=True,
                            gridspec_kw={"width_ratios": [1.15, 1., 1.]})
    first = np.array([r["first_write_mean_map_points"] / 1000 for r in case_rows])
    update = np.array([r["frame_mean_mean_map_points"] / 1000 for r in case_rows])
    axs[0].hlines(y, np.minimum(first, update), np.maximum(first, update), color="#777777", linewidth=1)
    for method, values, color, marker in zip(METHODS, (first, update), COLORS, ("o", "^")):
        axs[0].scatter(values, y, color=color, marker=marker, s=35, label=LABELS[method], edgecolors="black", linewidths=.35)
    axs[0].set_yticks(y, [case_label(row) for row in case_rows])
    axs[0].invert_yaxis()
    axs[0].set(xlabel="Stored map points (thousands)", title="(a) Map size")
    axs[0].set_xlim(left=0)
    axs[0].legend(loc="best", fontsize=8)
    geometry = [row["mean_geometry_coverage_delta_pp"] for row in case_rows]
    axs[1].scatter(geometry, y, marker="D", color="#333333", s=29)
    axs[1].set(xlabel="Frame mean − first write (percentage points)", title="(b) Predicted-depth coverage change")
    for i, width in enumerate(widths):
        values = [row[f"width{width}_mean_coverage_delta_pp"] for row in case_rows]
        axs[2].scatter(values, y, marker=("o", "^", "s", "D")[i % 4], color=COLORS[i % len(COLORS)], s=36,
                       edgecolors="black", linewidths=.35, label=f"{width} px")
    axs[2].set(xlabel="Frame mean − first write (percentage points)", title="(c) Selected-frame support change")
    axs[2].legend(loc="best", fontsize=8)
    for ax in axs:
        ax.grid(axis="x", alpha=.2)
    for ax in axs[1:]:
        ax.axvline(0, color="#666666", linestyle="--", linewidth=1, zorder=0)
        limit = max(abs(v) for v in ax.get_xlim())
        ax.set_xlim(-max(limit, .01), max(limit, .01))
    fig.text(.5, .012, "All cases shown; coverage changes are unweighted means over four held-out queries. Map size is one build per case.\nDepth coverage and fixed measured-support coverage have different definitions; neither measures generated-video quality.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .065, 1, 1))
    save_figure(fig, output, "map_size_and_coverage_changes", plt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "results/S3_rgbd_memory")
    parser.add_argument("--output", type=Path, help="Default: INPUT/analysis")
    args = parser.parse_args()
    output = args.output if args.output is not None else args.input / "analysis"
    started = datetime.now(timezone.utc).isoformat()
    metadata, records, cases, widths, hashes, verification_status = load_completed(args.input)
    geometry_rows, retrieval_rows, stability_rows = query_tables(records, cases, widths)
    case_rows, split_rows = aggregate_tables(records, cases, widths)
    # No output directory is created until completed input and record checks pass.
    output.mkdir(parents=True, exist_ok=True)
    tables = {"query_geometry.csv": geometry_rows, "query_retrieval.csv": retrieval_rows,
              "query_resolution_stability.csv": stability_rows, "case_summary.csv": case_rows,
              "split_summary.csv": split_rows}
    for name, rows in tables.items():
        write_csv(output / name, rows)
    plt = configure_plotting()
    figure_counts = plot_raw_test(records, widths, output, plt)
    plot_resolution_table(case_rows, widths, output, plt)
    plot_map_coverage(case_rows, widths, output, plt)
    summary = dict(status="completed", started_utc=started, completed_utc=datetime.now(timezone.utc).isoformat(),
                   input_directory=str(args.input.resolve()), analyzer_sha256=sha256(__file__), input_sha256=hashes,
                   input_verification_status=verification_status, config=metadata["config"],
                   counts=dict(cases=len(cases), geometry_query_conditions=len(geometry_rows), retrieval_query_width_pairs=len(retrieval_rows),
                               distinct_camera_queries=len({(r["block"], r["query"]) for r in records}),
                               independent_environments=1, raw_test_figure=figure_counts),
                   interpretation=dict(evidence="Real Kinect depth and mocap-pose memory-component experiment; no learned estimator or generated video.",
                       split="Block 0 is development; blocks 1 and 2 are fixed temporal test blocks in the same environment, not independent scenes.",
                       geometry="One observation per block/stride/bias/query; retrieval resolutions never duplicate geometry. Depth differences are to held-out measured depths, not noiseless geometric truth.",
                       aggregation="Mean query medians and mean query MAEs are unweighted over queries. Pooled common MAE weights each query by its common-pixel count; this does not create independent samples.",
                       coverage="Support coverage is measured on a fixed held-out target mask. All-history coverage uses all 20 history frames; it is an upper bound for a four-frame subset, not an equal-budget baseline or optimal-four score.",
                       controls="recent4 and nearest_pose4 select four history frames without using target depth. Their measured support scores repeat across memory/bias/width settings and are not independent observations.",
                       resolution="Changed at both means both widths change final selected sets. Identical transition additionally requires the same first-write set and same frame-mean set at both widths.",
                       bias="Zero is the original measured input; 20/50 mm conditions inject an artificial first-frame optical-depth-axis shift, not a natural model error.",
                       method="Frame mean is a simple comparison rule, not an asserted novel contribution.",
                       uncertainty="Descriptive counts only: no p-values, confidence intervals, or claims of independent-scene replication."),
                   case_summary=case_rows, split_summary=split_rows,
                   outputs=list(tables) + [f"{name}.{ext}" for name in ("raw_test_paired_comparison", "resolution_set_change_table", "map_size_and_coverage_changes") for ext in ("png", "pdf")])
    (output / "analysis_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False))
    captions = """# Figure captions and interpretation\n\nThe figures are descriptive displays of saved results. Read the numerical CSVs alongside them; no direction of benefit is assumed.\n\n- **raw_test_paired_comparison:** All original-measurement query/stride conditions in fixed test blocks. Left: paired median absolute depth differences on common prediction pixels. Right: paired selected-frame measured-support coverage averaged across configured retrieval widths. Dashed lines indicate equal values; an individual point does not establish population performance.\n- **resolution_set_change_table:** Final four-frame set differences between first write and frame mean for every block, stride, and injected-bias condition. Counts use the same four held-out queries per case. “Same transition” requires matching before/after sets at both widths, not merely two nonzero changes.\n- **map_size_and_coverage_changes:** Stored point count and coverage changes for all cases. Coverage differences are frame mean minus first write, averaged over four queries. Predicted-depth coverage and selected-frame measured support are separate diagnostics.\n\nAll test blocks come from one environment. Neither Kinect measurement agreement nor support coverage is generated-video quality. PNGs are previews; PDFs preserve vector text and markers. No p-values or confidence intervals are computed.\n"""
    (output / "figure_captions.md").write_text(captions)
    print(json.dumps(dict(status="completed", output=str(output), counts=summary["counts"])))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"Analysis failed: {type(error).__name__}: {error}", file=sys.stderr)
        sys.exit(1)
