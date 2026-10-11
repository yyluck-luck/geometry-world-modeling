#!/usr/bin/env python3
"""R269: render report figures from one immutable Git revision, on CPU.

Run from the repository root with a Python containing NumPy and Matplotlib:
python -B docs/report/figures/make_figures.py. Only this directory receives outputs.
Missing committed inputs are reported; local ignored results are never read.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import re
import shlex
import struct
import subprocess
import sys
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
# Suppress font-cache writes, including on machines without a populated cache.
# Matplotlib itself uses the already-existing output directory for configuration.
os.environ["MPLCONFIGDIR"] = str(OUT)
import matplotlib
matplotlib.use("Agg")
# Temporarily intercept only the font-cache file opens and lock creation.
# All other reads retain their normal behaviour; no input image is loaded.
import builtins
_real_open = builtins.open
_real_path_open = Path.open
_real_check_output = subprocess.check_output


def _skip_font_discovery(command, *args, **kwargs):
    # These optional system tools may update their own caches. The shipped
    # DejaVu Sans font is sufficient and is still discovered by Matplotlib.
    if Path(command[0]).name in ("fc-list", "system_profiler"):
        raise OSError("Optional system font discovery disabled for read-only rendering")
    return _real_check_output(command, *args, **kwargs)


def _cache_open(file, mode="r", *args, **kwargs):
    name = str(file)
    if "fontlist-v" in name and ("w" in mode or "a" in mode or "x" in mode):
        return io.StringIO()
    return _real_open(file, mode, *args, **kwargs)


def _path_cache_open(self, mode="r", *args, **kwargs):
    if "fontlist-v" in self.name and ("w" in mode or "a" in mode or "x" in mode):
        return io.StringIO()
    return _real_path_open(self, mode, *args, **kwargs)


@contextlib.contextmanager
def _no_font_cache_lock(path):
    yield


with patch("builtins.open", _cache_open), patch.object(Path, "open", _path_cache_open), \
        patch("matplotlib.cbook._lock_path", _no_font_cache_lock), \
        patch("subprocess.check_output", _skip_font_discovery):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
import numpy as np

COLORS = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#D55E00", "#56B4E9"]
MARKERS = ["o", "s", "^", "D", "P", "v"]
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 12,
    "axes.titlesize": 14, "axes.labelsize": 12,
    "xtick.labelsize": 11, "ytick.labelsize": 11,
    "legend.fontsize": 10, "axes.spines.top": False,
    "axes.spines.right": False, "axes.axisbelow": True,
    "grid.color": "#D7DBDF", "grid.linewidth": 0.6,
    "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.dpi": 300,
})

PATHS = {
    "S139": "work/S139_crossseq_revisit/results/S139_ANALYSIS.json",
    "S139_B": "work/S139_crossseq_revisit/results/S139_BASELINE_CONTRASTS.json",
    "S140": "work/S140_warp_guided/results/CONFIRM_ANALYSIS.json",
    "S139_SSIM": "work/S140_warp_guided/results/s139_ssim/S139_SSIM_ANALYSIS.json",
    "S141": "work/S141_finetune/results/S141_ANALYSIS.json",
    "S143": "work/S143_context_ranking/results/S143_ANALYSIS.json",
    "FRESH": "work/S143_context_ranking/results/S143_FRESH.json",
    "WARP": "work/S143_context_ranking/results/WARP_SCORES.json",
    "POOL": "work/S143_context_ranking/POOL.json",
    "DEV": "work/S144_A_wgs/results/SCORES_dev.json",
    "GATE": "work/S144_A_wgs/results/DEV_GATE.json",
    **{f"KPS{i}": f"work/S146_fresh12/diag/KPS_DIAG_{i}.json" for i in range(3)},
}
DATA, SOURCES, VALUES, FIGURES, CHECKS, BLOCKED = {}, {}, [], [], [], []


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], stderr=subprocess.PIPE)


def load(alias, revision):
    path = PATHS[alias]
    try:
        raw = git("show", f"{revision}:{path}")
    except subprocess.CalledProcessError:
        return None
    data = json.loads(raw)
    SOURCES[alias] = {"path": path, "sha256": hashlib.sha256(raw).hexdigest(),
                      "blob": git("rev-parse", f"{revision}:{path}").decode().strip()}
    DATA[alias] = data
    return data


def ptr(*parts):
    return "/" + "/".join(str(x).replace("~", "~0").replace("/", "~1") for x in parts)


def value(fig, label, metric, val, source, key, kind="MEASURED", ci=None, formula="direct"):
    val = float(val)
    if not math.isfinite(val):
        raise ValueError(f"Non-finite plotted value: {fig} {label} {metric}")
    if ci is not None:
        ci = [float(x) for x in ci]
        if not all(math.isfinite(x) for x in ci) or not ci[0] <= val <= ci[1]:
            raise ValueError(f"Invalid interval: {label}: {val}, {ci}")
    VALUES.append({"figure": fig, "label": label, "metric": metric, "value": val,
                   "ci": ci, "source": source, "key": key, "kind": kind, "formula": formula})
    return val


def save(fig, stem, title, caption, sources):
    fig.canvas.draw()
    for ext in ("png", "pdf"):
        metadata = {"Creator": "R269 make_figures.py", "Title": title,
                    "CreationDate": None, "ModDate": None} if ext == "pdf" else None
        fig.savefig(OUT / f"{stem}.{ext}", dpi=300, facecolor="white", metadata=metadata)
    plt.close(fig)
    FIGURES.append({"stem": stem, "title": title, "caption": caption, "sources": sources})


def forest(stem, title, rows, category, source="S141", footer=None):
    """Plot archived intervals without recomputing confidence limits."""
    fig, axes = plt.subplots(1, 2, figsize=(11.6, max(4.8, 1.1 + 0.63 * len(rows))))
    fig.subplots_adjust(left=0.34, right=0.975, top=0.80, bottom=0.23, wspace=0.36)
    fig.suptitle(title, y=0.97, fontsize=15, fontweight="bold")
    for ax, metric, xlabel in zip(axes, ("psnr_db", "ssim"), ("Δ PSNR (dB)", "Δ SSIM")):
        for y, (section, key, label, primary) in enumerate(rows):
            d = DATA[source][section][metric][key]
            m = value(stem, key, metric, d["mean"], source,
                      ptr(section, metric, key) + "/{mean,ci95}", ci=d["ci95"])
            lo, hi = d["ci95"]
            color = COLORS[0] if primary else COLORS[2]
            marker = "D" if primary else "o"
            ax.errorbar(m, y, xerr=[[m-lo], [hi-m]], fmt=marker, color=color,
                        markersize=7, capsize=4, linewidth=1.6)
            ax.annotate(f"{m:+.3f}", (m, y), xytext=(0, 9), textcoords="offset points",
                        ha="center", fontsize=9, color="#27313A")
        ax.axvline(0, color="#69737D", linewidth=1, linestyle="--")
        ax.set_yticks(range(len(rows)), [r[2] for r in rows] if ax is axes[0] else [])
        ax.set_ylim(len(rows)-0.45, -0.6)
        ax.margins(x=0.16)
        ax.set_xlabel(xlabel)
        ax.grid(axis="x")
    fig.text(0.34, 0.035, footer or "Points: mean contrast. Bars: archived 95% window-bootstrap CI.\nPositive values favour the first arm; PSNR and SSIM use separate scales.", fontsize=10)
    save(fig, stem, title, category, [source])


def fig_s141():
    d = DATA["S141"]
    registered = [
        ("PRIMARY_A: A_mem - base_mem", "Primary A: A_mem − base_mem", True),
        ("PRIMARY_B: B_mem - B2_warp", "Primary B: B_mem − B2 warp", True),
        ("A_mem - A_static", "A_mem − A_static", False),
        ("B_mem - base_mem", "B_mem − base_mem", False),
        ("A_static - base_static", "A_static − base_static", False),
        ("base_mem - base_static (S139 replica, seeds 3-6)", "Base memory − base static\n(S139 seed-subset replica)", False),
    ]
    forest("fig02a_s141_chess", "S141 · Chess: primary contrasts and supporting comparisons",
           [("contrasts", *r) for r in registered],
           "A_mem improves over base_mem in the archived PSNR and SSIM contrasts; B_mem vs warp has opposite signs across the metrics. Diamonds identify the registered primary arm contrasts (PSNR primary, SSIM secondary); circles are supporting comparisons, including the seed-subset replica. All use window means over seeds 3–6 and archived window-bootstrap 95% intervals. A is attention LoRA; B adds the warp-latent branch. Chess was excluded from training but exposed in prior stages.")
    exploratory = [("contrasts", "B_mem - A_mem (exploratory)", "B_mem − A_mem", False)]
    for key in d["exploratory_Bstatic"]["psnr_db"]:
        label = key.replace(" - ", " − ").replace("B2_warp_static", "B2 warp (static)").replace("B2_warp_mem", "B2 warp (memory)")
        if key.startswith("(B_mem"):
            label = "(B_mem − B_static)\n− (A_mem − A_static)"
        exploratory.append(("exploratory_Bstatic", key, label, False))
    forest("fig02b_s141_exploratory", "S141 · Chess: exploratory contrasts", exploratory,
           "The exploratory contrasts do not replace the registered primaries. Every top-level exploratory contrast in the analysis JSON is included, with the archived 95% window-bootstrap CI; history-favourable subgroups and covered/hole analyses are outside this requested panel.")
    rgbd = [("rgbd_secondary", key, key.replace(" - ", " − ").replace("B2_warp", "B2 warp"), False)
            for key in d["rgbd_secondary"]["psnr_db"] if key != "means"]
    forest("fig02c_s141_rgbd", "S141 · RGB-D Scenes: secondary transfer panel", rgbd,
           "A_static improves over base_static, while B_static trails the warp and both learned comparators in these archived contrasts. This exposed secondary panel uses static contexts, seed-averaged windows and archived 95% window-bootstrap intervals.")
    CHECKS.append("S141: every top-level contrast included once for both metrics; archived CI bounds retained.")


def fig_s143():
    analysis, fresh = DATA["S143"], DATA["FRESH"]
    rules = {1: "Static recent", 2: "Pose NMS", 3: "VMem retrieval", 4: "Nearest-4", 5: "Coverage greedy", 6: "Random"}
    fig, ax = plt.subplots(figsize=(8.6, 5.7))
    fig.subplots_adjust(left=0.13, right=0.96, bottom=0.19, top=0.85)
    for i, (rule, name) in enumerate(rules.items()):
        d = analysis["per_rule_means"][str(rule)]
        warp_values = []
        for w in DATA["POOL"]["windows"]:
            matches = [s for s in w["sets"] if rule in s["rules"]]
            if len(matches) != 1:
                raise ValueError(f"Rule {rule} not uniquely mapped in {w['window_id']}")
            warp_values.append(DATA["WARP"]["windows"][w["window_id"]]["sets"][matches[0]["set_id"]]["warp_psnr"])
        if not math.isclose(float(np.mean(warp_values)), d["Q_W"], abs_tol=1e-10):
            raise ValueError(f"Rule {rule}: POOL/WARP disagrees with analysis")
        x = value("fig03a_s143_rules", f"Rule {rule}: {name}", "warp PSNR dB", d["Q_W"], "S143", ptr("per_rule_means", rule, "Q_W"))
        y = value("fig03a_s143_rules", f"Rule {rule}: {name}", "generated PSNR dB", d["Q_G"], "S143", ptr("per_rule_means", rule, "Q_G"))
        ax.scatter(x, y, color=COLORS[i], marker=MARKERS[i], s=105, edgecolors="#28323A", linewidths=0.6)
        offsets = {1: (10, 10), 2: (10, 10), 3: (10, -19), 4: (-12, 13), 5: (-12, -20), 6: (-12, -20)}
        dx, dy = offsets[rule]
        ax.annotate(f"{rule}. {name}", (x, y), xytext=(dx, dy), textcoords="offset points", ha="left" if dx > 0 else "right", fontsize=11)
    ax.set(xlabel="Mean warp PSNR (dB)", ylabel="Mean generated PSNR (dB)", xlim=(12.7, 15.9), ylim=(11.0, 12.15))
    ax.grid()
    fig.suptitle("S143 · Warp and generator rank context rules differently", fontsize=15, fontweight="bold", y=0.96)
    fig.text(0.13, 0.04, "Exploratory discovery panel · one labelled point per context rule\nDescriptive means; no fitted trend or causal interpretation.", fontsize=10)
    save(fig, "fig03a_s143_rules", "S143 per-rule warp versus generated PSNR",
         "The rule with the highest mean warp PSNR differs from the rule with the highest mean generated PSNR. Each point is an archived per-rule discovery mean. POOL maps each rule to a per-window set; its WARP_SCORES mean is checked against Q_W. No images or target frames are read.", ["S143", "WARP", "POOL"])
    rows = [("S143", "R_2seed_hindsight", "Discovery: hindsight selector − warp selector"),
            ("S143", "global_rule_gap", "Discovery: local selector − global rule"),
            ("FRESH", "C_frozen4_discovery", "Fresh: frozen hindsight selector − warp selector"),
            ("FRESH", "local_vs_global", "Fresh: frozen local selector − global rule")]
    rule_labels = {
        "r_disc(rule 4) - rule 3 (mem_vmem)": "Fresh: nearest-4 − VMem retrieval",
        "r_disc(rule 4) - c_W": "Fresh: nearest-4 − warp selector",
        "r_disc(rule 4) - rule 1 (static)": "Fresh: nearest-4 − static recent",
    }
    if set(rule_labels) != set(fresh["rule_contrasts"]):
        raise ValueError("Unexpected S143 fresh-rule contrast keys")
    for key, label in rule_labels.items():
        rows.append(("FRESH", ("rule_contrasts", key), label))
    fig, ax = plt.subplots(figsize=(11.7, 6.5))
    fig.subplots_adjust(left=0.44, right=0.975, top=0.81, bottom=0.19)
    for y, (src, key, label) in enumerate(rows):
        parts = (key,) if isinstance(key, str) else key
        d = DATA[src]
        for part in parts:
            d = d[part]
        ck = "ci95" if src == "S143" else "window_bootstrap_ci95_descriptive"
        m = value("fig03b_s143_contrasts", label, "PSNR contrast dB", d["mean"], src, ptr(*parts) + f"/{{mean,{ck}}}", ci=d[ck])
        lo, hi = d[ck]
        if src == "FRESH":
            if set(d["seed_panel_means"]) != {"42", "7", "1", "2"}:
                raise ValueError("Unexpected S143 fresh seed panel keys")
            if not math.isclose(np.mean(list(d["seed_panel_means"].values())), m, abs_tol=1e-10):
                raise ValueError("S143 fresh mean differs from mean of seed panels")
        color = COLORS[0] if src == "S143" else "#303C47"
        ax.errorbar(m, y, xerr=[[m-lo], [hi-m]], color=color, fmt="D", capsize=4, markersize=7, zorder=4)
        for s, (seed, point) in enumerate(d.get("seed_panel_means", {}).items()):
            v = value("fig03b_s143_contrasts", f"{label}; seed {seed}", "seed-panel PSNR contrast dB", point, src, ptr(*parts, "seed_panel_means", seed))
            ax.scatter(v, y + 0.10 + 0.07*s, color=COLORS[s], marker=MARKERS[s], s=42, edgecolor="white", linewidth=0.5, zorder=5)
    ax.axvline(0, color="#737C85", linestyle="--", linewidth=1)
    ax.axhline(1.5, color="#C3CAD0", linewidth=1)
    ax.set_yticks(range(len(rows)), [r[2] for r in rows])
    ax.set_ylim(len(rows)-0.3, -0.65)
    ax.set_xlim(-0.13, 1.11)
    ax.set_xlabel("Δ generated PSNR (dB)")
    ax.grid(axis="x")
    seeds = list(fresh["C_frozen4_discovery"]["seed_panel_means"])
    handles = [Line2D([], [], color="#303C47", marker="D", linestyle="none", label="Mean + interval")]
    handles += [Line2D([], [], color=COLORS[i], marker=MARKERS[i], linestyle="none", label=f"Seed {s}") for i, s in enumerate(seeds)]
    ax.legend(handles=handles, loc="lower right", bbox_to_anchor=(1.0, 1.035), ncol=3, frameon=False)
    fig.suptitle("S143 · Discovery contrasts and fresh-seed descriptions", fontsize=15, fontweight="bold", y=0.97)
    fig.text(0.08, 0.025, "Target-informed hindsight selectors on the same exposed chess windows. Fresh seeds are descriptive, not new scenes.\nBars: archived 95% window-bootstrap intervals; no seed-generalization guarantee for fresh intervals.\nSmall symbols: fresh seed-panel means (vertically offset for visibility); discovery seed points are unavailable.", fontsize=10)
    save(fig, "fig03b_s143_contrasts", "S143 discovery and fresh contrasts",
         "The archived discovery and fresh contrasts have positive means. The selectors are target-informed hindsight selectors on fixed exposed chess windows, not deployable target-blind selectors or fresh-scene confirmation. Discovery uses two-seed cross-fitting; fresh uses selections frozen from all discovery seeds. Fresh seed panels are the unit and no formal seed-level inference is made. Fresh intervals are explicitly descriptive window bootstraps, not confidence intervals over seed panels. The discovery JSON contains no seed-panel points.", ["S143", "FRESH"])
    CHECKS.append("S143: all six Q_W values independently agree with POOL + WARP means (absolute tolerance 1e-10 dB).")
    CHECKS.append("S143: discovery intervals and all five fresh contrasts retained; 20 fresh seed-panel points; means agree with seed-panel averages.")


def fig_s144():
    d, gate = DATA["DEV"], DATA["GATE"]
    arms = ["B2", "V", "F_C", "F_R", "A_C", "A_R", "A_none", "P_V", "P_FC", "P_AC", "REV_AC", "BL_V", "BL_FC", "BL_AC"]
    if any({k for k, v in r.items() if isinstance(v, dict) and "psnr_db" in v} != set(arms) for r in d["runs"].values()):
        raise ValueError("Unexpected S144 arm/control keys")
    means = {}
    for arm in arms:
        by_window = {}
        for r in d["runs"].values():
            cells = by_window.setdefault(r["window_id"], {})
            if r["seed"] in cells:
                raise ValueError("Duplicate S144 window-seed cell")
            cells[r["seed"]] = r[arm]["psnr_db"]
        if not all(set(cells) == set(d["seeds"]) for cells in by_window.values()):
            raise ValueError("Incomplete S144 window-seed cells")
        means[arm] = value("fig04_s144_development", arm, "PSNR dB", np.mean([np.mean(list(v.values())) for v in by_window.values()]),
                           "DEV", f"/runs/*/{arm}/psnr_db", kind="DERIVED",
                           formula="mean over windows of mean over seeds, grouped by /runs/*/window_id and seed")
    for arm in arms:
        key = f"A_R-{arm}"
        if key in gate["means"] and not math.isclose(means["A_R"] - means[arm], gate["means"][key], abs_tol=1e-10):
            raise ValueError(f"S144 gate contrast mismatch: {key}")
    interaction = (means["A_R"]-means["A_C"])-(means["F_R"]-means["F_C"])
    if not math.isclose(interaction, gate["means"]["I"], abs_tol=1e-10):
        raise ValueError("S144 interaction mismatch")
    value("fig04_s144_development", "Interaction I (annotation)", "PSNR dB", gate["means"]["I"], "GATE", "/means/I")
    fig, ax = plt.subplots(figsize=(9.7, 7.8))
    fig.subplots_adjust(left=0.22, right=0.94, top=0.86, bottom=0.16)
    ys = np.arange(len(arms))
    colors = ["#8F9AA4"] * 2 + [COLORS[0]] * 2 + [COLORS[2]] * 3 + [COLORS[3]] * 4 + [COLORS[1]] * 3
    bars = ax.barh(ys, [means[a] for a in arms], color=colors, height=0.68, edgecolor="#3B444C", linewidth=0.5)
    ax.bar_label(bars, labels=[f"{means[a]:.3f}" for a in arms], padding=5, fontsize=10)
    labels = ["B2 · warp", "V · VAE round-trip", "F_C · frozen, clamp", "F_R · frozen, release", "A_C · adapted, clamp", "A_R · adapted, release", "A_none · adapted only", "P_V · covered paste", "P_FC · covered paste", "P_AC · covered paste", "REV_AC · reverse paste", "BL_V · fitted blend", "BL_FC · fitted blend", "BL_AC · fitted blend"]
    ax.set_yticks(ys, labels)
    ax.invert_yaxis()
    ax.set_xlim(0, max(means.values())*1.13)
    ax.set_xlabel("Development mean PSNR (dB)")
    ax.grid(axis="x")
    status = "PASS" if gate["PERFORMANCE_GO"] else "FAIL — stopped at development gate"
    fig.suptitle(f"S144 · {status}", fontsize=15, fontweight="bold", y=0.97)
    fig.text(0.22, 0.89, f"Interaction I = {gate['means']['I']:+.4f} dB", fontsize=12)
    fig.text(0.07, 0.035, "Development only. Blends were fitted on this panel; their scores are optimistic.\nEqual weight per window after seed averaging. No confidence intervals are supplied for arm means.", fontsize=10)
    save(fig, "fig04_s144_development", "S144 development arm/control PSNR",
         "S144 fails its archived development gate. Bars include every scored arm/control and start at zero. V denotes the warp's VAE round-trip; F/A are frozen/adapted backbones, C/R are terminal clamp/release, P replaces covered pixels, REV reverses that paste, and BL is a development-fitted global blend. These development scores do not establish held-out improvement.", ["DEV", "GATE"])
    CHECKS.append("S144: complete, unique seed cells; derived arm differences and interaction agree with DEV_GATE (1e-10 dB).")


def fig_s146():
    rows = [(src, i, r) for src in ("KPS0", "KPS1", "KPS2") for i, r in enumerate(DATA[src]["rows"])]
    if len({r["window_id"] for _, _, r in rows}) != len(rows):
        raise ValueError("Duplicate S146 windows across shards")
    rooms = sorted({r["room"] for _, _, r in rows})
    sizes = sorted({int(s) for _, _, r in rows for s in r["constructions"]})
    failure, depth = np.empty((len(rooms), len(sizes))), np.empty((len(rooms), len(sizes)))
    labels = [[""] * len(sizes) for _ in rooms]
    for i, room in enumerate(rooms):
        selected = [(src, j, r) for src, j, r in rows if r["room"] == room]
        for k, size in enumerate(sizes):
            cs = [(src, j, r["constructions"][str(size)]) for src, j, r in selected]
            n_bad = sum(not math.isfinite(c["err"]) for _, _, c in cs)
            for _, _, c in cs:
                if len(c["positive_depth_frac"]) != size or not all(0 <= z <= 1 for z in c["positive_depth_frac"]):
                    raise ValueError("Invalid S146 depth fractions")
            frac = n_bad / len(cs)
            dep = min(z for _, _, c in cs for z in c["positive_depth_frac"])
            key = f"/rows/*[room={room}]/constructions/{size}"
            failure[i, k] = value("fig05_s146_kps", f"{room}; construction {size}", "non-finite objective fraction", frac, "KPS0,KPS1,KPS2", key+"/err", kind="DERIVED", formula=f"count(not isfinite(err)) / windows = {n_bad}/{len(cs)}; pooled across shards")
            depth[i, k] = value("fig05_s146_kps", f"{room}; construction {size}", "minimum positive-depth fraction", dep, "KPS0,KPS1,KPS2", key+"/positive_depth_frac/*", kind="DERIVED", formula="minimum over all views in all windows of this room and construction size; includes failed objectives")
            labels[i][k] = f"{frac:.3f}\n({n_bad}/{len(cs)})"
    fig, axes = plt.subplots(1, 2, figsize=(11.1, 4.6))
    fig.subplots_adjust(left=0.16, right=0.95, top=0.73, bottom=0.22, wspace=0.40)
    for ax, matrix, title in zip(axes, (failure, depth), ("Non-finite objective fraction", "Minimum positive-depth fraction")):
        im = ax.pcolormesh(np.arange(len(sizes)+1)-0.5, np.arange(len(rooms)+1)-0.5,
                           matrix, vmin=0, vmax=1, cmap="viridis", shading="flat")
        ax.set_ylim(len(rooms)-0.5, -0.5)
        for i in range(len(rooms)):
            for k in range(len(sizes)):
                label = labels[i][k] if ax is axes[0] else f"{matrix[i,k]:.5f}"
                ax.text(k, i, label, ha="center", va="center", color="white" if matrix[i,k] < 0.5 else "#13212D", fontsize=12)
        ax.set_xticks(range(len(sizes)), [str(s) for s in sizes])
        ax.set_yticks(range(len(rooms)), [r.replace("_", " / ") for r in rooms] if ax is axes[0] else [])
        ax.set_xlabel("Construction size (frames)")
        ax.set_title(title, fontsize=12, pad=12)
        cb = fig.colorbar(im, ax=ax, fraction=0.055, pad=0.035, ticks=[0,0.5,1])
        cb.set_label("Fraction", fontsize=10)
        cb.solids.set_rasterized(False)
    fig.suptitle("S146 · KPS bank-only geometry diagnostic", fontsize=15, fontweight="bold", y=0.97)
    fig.text(0.08, 0.035, "Left: failed whole objectives / windows, pooled across diagnostic shards.\nRight: worst view across those windows, including failed objectives. This is a preflight diagnostic, not generation quality.", fontsize=10)
    save(fig, "fig05_s146_kps", "S146 per-room KPS diagnostic",
         "The KPS diagnostic records non-finite whole objectives and low positive-depth fractions in some room/construction cells. Non-finite means not math.isfinite(err), including Infinity. Each denominator is the number of windows in that room, after pooling shards. The depth statistic is the minimum over every stored view, including constructions with non-finite objectives; n_views is not used as the objective denominator.", ["KPS0", "KPS1", "KPS2"])
    CHECKS.append("S146: unique windows across shards; pooled room denominators; all depth lists match construction sizes and lie in [0,1].")


def validate_outputs():
    records = []
    for f in FIGURES:
        for ext in ("png", "pdf"):
            path = OUT / f"{f['stem']}.{ext}"
            raw = path.read_bytes()
            if ext == "png":
                if raw[:8] != b"\x89PNG\r\n\x1a\n":
                    raise ValueError(f"Invalid PNG: {path}")
                width, height = struct.unpack(">II", raw[16:24])
                pos, dpi = 8, None
                while pos < len(raw):
                    length = struct.unpack(">I", raw[pos:pos+4])[0]
                    if raw[pos+4:pos+8] == b"pHYs":
                        x, y, unit = struct.unpack(">IIB", raw[pos+8:pos+17])
                        dpi = (x*0.0254, y*0.0254) if unit == 1 else None
                    pos += 12+length
                if dpi is None or any(abs(x-300) > 0.02 for x in dpi):
                    raise ValueError(f"PNG DPI mismatch: {dpi}")
                detail = f"{width}x{height}; dpi={dpi[0]:.4f}"
            else:
                if not raw.startswith(b"%PDF-") or b"%%EOF" not in raw[-1024:]:
                    raise ValueError(f"Invalid PDF: {path}")
                if re.search(rb"/Subtype\s*/Image\b", raw):
                    raise ValueError(f"Unexpected raster image in vector PDF: {path}")
                detail = "PDF signature and EOF verified; no raster image objects"
            records.append((path.name, len(raw), hashlib.sha256(raw).hexdigest(), detail))
    return records


def write_readme(revision, command, outputs):
    lines = [f"DATA_REVISION {revision}", f"COMMAND {command}",
             f"SCRIPT_SHA256 {hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}",
             f"ENV Python={platform.python_version()} NumPy={np.__version__} Matplotlib={matplotlib.__version__}",
             "new_method_validated=false; novelty_authorization=NONE"]
    for s in BLOCKED:
        lines.append("BLOCKED " + s)
    lines += ["PLOTTED VALUES (round-trip Python float representations)",
              "figure | label | metric | value | ci95_low | ci95_high | evidence | source:key | derivation"]
    for r in VALUES:
        ci = r["ci"] or [None, None]
        lines.append(" | ".join(map(str, (r["figure"], r["label"], r["metric"], repr(r["value"]),
                     repr(ci[0]), repr(ci[1]), r["kind"], r["source"]+":"+r["key"], r["formula"]))))
    lines += ["CHECK " + c for c in CHECKS]
    lines += [f"OUTPUT {name} bytes={size} sha256={sha} {detail}" for name, size, sha, detail in outputs]
    status = "PARTIAL" if BLOCKED else "COMPLETE"
    lines.append(f"{status} {len(FIGURES)} figures; {2*len(FIGURES)} verified exports; {len(BLOCKED)} blocked figure request(s)")
    transcript = "\n".join(lines) + "\n"
    sections = ["# R269 report figures", "",
                f"**{status}: {len(FIGURES)} figures / {2*len(FIGURES)} verified PNG and PDF exports.** Figure 1 is blocked by missing committed S139/S140 inputs; details below." if BLOCKED else f"**Complete: {len(FIGURES)} figures / {2*len(FIGURES)} verified exports.**", "",
                f"Source snapshot: `{revision}`. CPU only; all numeric inputs are Git blobs from this snapshot. Local ignored/uncommitted JSONs, source images, target frames, weights and datasets are not read.", "",
                "`new_method_validated=false`; `novelty_authorization=NONE`.", "",
                "## Reproduce", "", "From the repository root:", "", "```bash", command, "```", "",
                "The script prints every plotted value and interval with its JSON key, verifies source consistency, writes this README, and checks export signatures and PNG DPI. `--revision` freezes inputs even if another process advances HEAD. Missing sources are explicit and never replaced with different-seed results or transcribed report prose.", "",
                "## Produced figures", ""]
    for f in FIGURES:
        sections += [f"### {f['title']}", "", f"[{f['stem']}.png]({f['stem']}.png) · [{f['stem']}.pdf]({f['stem']}.pdf)", "",
                     f["caption"], "", "Sources: " + ", ".join(f"`{s}`" for s in f["sources"]) + ".", ""]
    sections += ["## Missing sources / limitations", ""]
    sections += ["- " + x for x in BLOCKED] or ["None of the requested input files are missing from this snapshot."]
    sections += ["", "The brief's POOL file is committed at `work/S143_context_ranking/POOL.json`, outside its `results/` directory. S141 is split across three figures and S143 across two to keep individual labels readable. No new statistical intervals are fitted: only archived intervals are shown; arm means and diagnostics without supplied intervals remain descriptive.", "",
                 "## Source files and content hashes", "", "| Alias | Committed file | Git blob | SHA-256 |", "|---|---|---|---|"]
    for alias, s in SOURCES.items():
        sections.append(f"| {alias} | `{s['path']}` | `{s['blob']}` | `{s['sha256']}` |")
    sections += ["", "## Definitions and code provenance", "",
                 "JSON paths below use JSON Pointer syntax; `*` and `[room=...]` explicitly denote the filters described in the derivation column. `MEASURED` means an archived experimental summary copied from JSON, not a new experiment. `DERIVED` means a deterministic aggregation of stored measurements. Decimal strings preserve the loaded Python floats; plot labels are rounded only for legibility.", "",
                 "- S141 window-mean contrasts and bootstrap: `work/S141_finetune/analyze_s141.py:22`, `:33`, `:63`, `:70`, `:96`; registration and scope: `work/S141_finetune/PROTOCOL.md:51`, `:72`.",
                 "- S144 seed averaging and gate: `work/S144_A_wgs/analyze_s144.py:14`, `:28`, `:49`; control definitions: `work/S144_A_wgs/PROTOCOL.md:9`.",
                 "- S143 rule names: `work/S143_context_ranking/PROTOCOL.md:14`. Rule mapping is checked against the committed POOL and WARP files. Fresh inference scope is stated by `FRESH:/note`. No discovery seed-panel points are fabricated.",
                 "- S146 uses the stored whole-objective `err` and `positive_depth_frac` fields. A non-finite objective is counted once per construction/window; it is not a per-view failure count.", "",
                 "## Design and validation", "",
                 "Experimental-results guidance from the figure-designer skill was applied: vector PDFs plus 300 dpi PNGs, DejaVu Sans at readable panel sizes, an Okabe–Ito qualitative palette and viridis diagnostic scales, direct labels/marker shapes in addition to colour, and no fitted trend or selective winning-arm display. Forest plots include zero; S144 bars start at zero; scatter and heatmap axes are explicit. Use panels near their intended full slide/report width; do not shrink multi-panel figures into a narrow column.", "",
                 "The complete final script stdout follows, including the exact-value table, consistency checks, export sizes and SHA-256 hashes. Repository tests are not invoked by the figure script; this is a deterministic visualization of archived results, not a new model experiment.", "",
                 "### Environment correction and repository check", "",
                 "The supplied project venv has NumPy but lacks Matplotlib. No packages or environments were changed. Rendering uses the existing Homebrew Python environment named by the command above. The initial attempt ended before rendering:", "",
                 "```bash", ".venv-cut3r/bin/python -B docs/report/figures/make_figures.py --revision 52bdb866eb5987cb97f4d68c1f991d4e1e4ab05c", "```", "", "Complete output (initial script version):", "", "```text",
                 'Traceback (most recent call last):',
                 '  File "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/report/figures/make_figures.py", line 31, in <module>',
                 '    import matplotlib', "ModuleNotFoundError: No module named 'matplotlib'", "```", "",
                 "A scoped existing CPU metric test was run with bytecode writes disabled; it checks the repository's synthetic RGB-D metrics, not the figure code. No root linter configuration or existing plotting tests were found. The full unrelated repository suite was not run under this task's restricted-write boundary.", "",
                 "```bash", "PYTHONDONTWRITEBYTECODE=1 .venv-cut3r/bin/python -B tests/test_rgbd_metrics.py", "```", "", "Complete output:", "", "```text", "..........", "----------------------------------------------------------------------", "Ran 10 tests in 0.011s", "", "OK", "```", "",
                 "## Exact command and complete stdout", "", "```text", transcript.rstrip(), "```", ""]
    (OUT / "README.md").write_text("\n".join(sections))
    print(transcript, end="")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default="HEAD", help="Git commit to read; resolved once")
    args = parser.parse_args()
    revision = git("rev-parse", "--verify", args.revision + "^{commit}").decode().strip()
    for alias in PATHS:
        load(alias, revision)
    missing = [PATHS[s] for s in ("S139", "S139_B", "S140", "S139_SSIM") if s not in DATA]
    if missing:
        BLOCKED.append("Figure 1 (S139/S140) not plotted: requested result JSONs absent from this committed snapshot: " + "; ".join(missing) + ". These paths are ignored by Git in this checkout. Commit the authoritative files, then add/verify their schema before rendering this panel; no ignored result bytes were read.")
    else:
        raise RuntimeError("Figure 1 source schema must be verified before first committed-input rendering.")
    required = [s for s in PATHS if s not in ("S139", "S139_B", "S140", "S139_SSIM")]
    if any(s not in DATA for s in required):
        raise RuntimeError("Missing committed inputs: " + str([s for s in required if s not in DATA]))
    fig_s141()
    fig_s143()
    fig_s144()
    fig_s146()
    outputs = validate_outputs()
    command = shlex.join([sys.executable, "-B", "docs/report/figures/make_figures.py", "--revision", revision])
    write_readme(revision, command, outputs)


if __name__ == "__main__":
    main()
