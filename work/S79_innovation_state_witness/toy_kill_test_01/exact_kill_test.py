"""Finite synthetic probability enumeration; stdlib only; no data/model/network."""
from datetime import datetime, timezone
from fractions import Fraction as F
from hashlib import sha256
from itertools import product
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent


def now():
    return datetime.now(timezone.utc).isoformat()


def save(name, value):
    with (ROOT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def code_text(code):
    return ":".join(str(x) for x in code)


def stream_memory(which, w):
    observations = [w["Z"]] if which == "T1" else [w["Z1"], w["Z2"]]
    events = [("target", z) for z in observations] + [("other", w["D1"]), ("other", w["D2"])]
    state = {"recent": 0, "old_witness": 0, "posterior": 0,
             "persistent_state" if which == "T1" else "persistent_map": 1}
    trace = []
    for kind, value in events:
        state["recent"] = ((state["recent"] << 1) | value) & 3
        if kind == "target":
            if which == "T1":
                state["old_witness"] = value
                state["posterior"] = value
                state["persistent_state"] = value
            else:
                state["old_witness"] = ((state["old_witness"] << 1) | value) & 3
                state["posterior"] += value
                state["persistent_map"] &= value
        assert all(0 <= value <= 3 for value in state.values())
        trace.append({"event_kind": kind, "event_value": value, "state_codes": dict(state)})
    decoded = {"recent": (state["recent"] >> 1, state["recent"] & 1)}
    if which == "T1":
        decoded.update({name: (state[name], 0) for name in
                        ("old_witness", "posterior", "persistent_state")})
    else:
        decoded.update(old_witness=(state["old_witness"] >> 1, state["old_witness"] & 1),
                       posterior=(state["posterior"],),
                       persistent_map=(state["persistent_map"], 0))
    return decoded, trace


def worlds(which):
    result = []
    if which == "T1":
        for s, d1, d2, a in product((0, 1), repeat=4):
            result.append(dict(S=s, D1=d1, D2=d2, A=a, Z=s,
                               Y=s ^ a, probability=F(1, 16)))
    else:
        for s, n1, n2, d1, d2, a in product((0, 1), repeat=6):
            noise = (F(1, 4) if n1 else F(3, 4))
            noise *= F(1, 4) if n2 else F(3, 4)
            result.append(dict(S=s, N1=n1, N2=n2, D1=d1, D2=d2,
                               A=a, Z1=s ^ n1, Z2=s ^ n2,
                               Y=s ^ a, probability=F(1, 16) * noise))
    assert sum(w["probability"] for w in result) == 1
    return result


def evaluate(ws, encoder, capacity=4, details=True):
    groups = {}
    for w in ws:
        key = (encoder(w), w["A"])
        group = groups.setdefault(key, {"mass": F(0), "positive": F(0)})
        group["mass"] += w["probability"]
        group["positive"] += w["probability"] * w["Y"]
    codes = {key[0] for key in groups}
    if capacity is not None:
        assert len(codes) <= capacity
    reader = {key: g["positive"] / g["mass"] for key, g in groups.items()}
    brier = error = F(0)
    terms = []
    for i, w in enumerate(ws):
        code = encoder(w)
        prediction = reader[(code, w["A"])]
        # Strict > implements the declared tie-to-zero classification rule.
        decision = int(prediction > F(1, 2))
        bterm = w["probability"] * (prediction - w["Y"]) ** 2
        eterm = w["probability"] * (decision != w["Y"])
        brier += bterm
        error += eterm
        if details:
            terms.append({"world_index": i, "memory": list(code),
                          "prediction_probability": str(prediction),
                          "decision": decision, "brier_contribution": str(bterm),
                          "error_contribution": str(eterm)})
    grouped_brier = sum(g["mass"] * reader[k] * (1 - reader[k])
                        for k, g in groups.items())
    grouped_error = sum(min(g["positive"], g["mass"] - g["positive"])
                        for g in groups.values())
    assert brier == grouped_brier
    assert error == grouped_error
    result = {"reachable_codes": len(codes), "capacity_codes": capacity,
              "brier": str(brier), "bayes_error": str(error),
              "brier_from_groups": str(grouped_brier),
              "error_from_groups": str(grouped_error),
              "reader_groups": [
                  {"memory": list(k[0]), "A": k[1],
                   "mass": str(g["mass"]), "positive_mass": str(g["positive"]),
                   "prediction_probability": str(reader[k])}
                  for k, g in sorted(groups.items())]}
    if details:
        result["world_contributions"] = terms
    return result


def run():
    started = now()
    identity = {name: sha256((ROOT / name).read_bytes()).hexdigest()
                for name in ("PROTOCOL.md", "exact_kill_test.py")}
    save("RUN_STARTED.json", {"started_utc": started, "identities": identity,
                              "synthetic_only": True})
    t1, t2 = worlds("T1"), worlds("T2")
    arms = {
        "T1": {
            "recent": lambda w: (w["D1"], w["D2"]),
            "persistent_state": lambda w: (w["Z"], 0),
            "old_witness": lambda w: (w["Z"], 0),
            "posterior": lambda w: (w["Z"], 0),
        },
        "T2": {
            "recent": lambda w: (w["D1"], w["D2"]),
            "old_witness": lambda w: (w["Z1"], w["Z2"]),
            "posterior": lambda w: (w["Z1"] + w["Z2"],),
            "persistent_map": lambda w: (int(w["Z1"] == w["Z2"] == 1), 0),
        },
    }
    results, traces = {}, {}
    for name, ws in (("T1", t1), ("T2", t2)):
        traces[name] = []
        for index, w in enumerate(ws):
            streamed, trace = stream_memory(name, w)
            for label, encode in arms[name].items():
                assert streamed[label] == encode(w)
            traces[name].append({"world_index": index, "steps": trace})
        results[name] = {label: evaluate(ws, encode)
                         for label, encode in arms[name].items()}
        history = ((lambda w: (w["Z"], w["D1"], w["D2"])) if name == "T1"
                   else lambda w: (w["Z1"], w["Z2"], w["D1"], w["D2"]))
        results[name]["full_history_diagnostic"] = evaluate(ws, history, capacity=None)
        serialized = [{**w, "probability": str(w["probability"])} for w in ws]
        save(name + "_WORLDS.json", serialized)
    assert results["T1"]["recent"]["brier"] == "1/4"
    for arm in ("persistent_state", "old_witness", "posterior", "full_history_diagnostic"):
        assert results["T1"][arm]["brier"] == "0"
    for arm in ("posterior", "old_witness", "full_history_diagnostic"):
        assert results["T2"][arm]["brier"] == "3/20"
    assert results["T2"]["persistent_map"]["brier"] == "39/220"
    assert {g["prediction_probability"] for g in results["T2"]["posterior"]["reader_groups"]} == {"1/10", "1/2", "9/10"}
    assert {g["prediction_probability"] for g in results["T2"]["persistent_map"]["reader_groups"] if g["A"] == 0} == {"7/22", "9/10"}

    enumerations = {}
    for bits in (1, 2):
        rows = []
        for mapping in product(range(2 ** bits), repeat=4):
            # Observation order is exactly 00, 01, 10, 11.
            outcome = evaluate(t2, lambda w: (mapping[2 * w["Z1"] + w["Z2"]],),
                               capacity=2 ** bits, details=False)
            rows.append({"mapping_00_01_10_11": list(mapping), **outcome})
        minimum = min(F(r["brier"]) for r in rows)
        minimizers = [r["mapping_00_01_10_11"] for r in rows if F(r["brier"]) == minimum]
        assert len(rows) == (2 ** bits) ** 4
        assert minimum == (F(39, 220) if bits == 1 else F(3, 20))
        enumerations[str(bits)] = {"encoding_count": len(rows),
                                  "minimum_brier": str(minimum),
                                  "minimizer_count": len(minimizers),
                                  "minimizers": minimizers, "encodings": rows}

    save("ONLINE_STATE_TRACES.json", traces)
    save("ARM_CALCULATIONS.json", results)
    save("FINITE_ENCODER_ENUMERATION.json", enumerations)
    summary = {scenario: {arm: {key: result[key] for key in
                              ("reachable_codes", "capacity_codes", "brier", "bayes_error")}
                          for arm, result in outcomes.items()}
               for scenario, outcomes in results.items()}
    summary["finite_encoder_search"] = {
        bits: {key: value[key] for key in
               ("encoding_count", "minimum_brier", "minimizer_count")}
        for bits, value in enumerations.items()}
    summary["T2_map_minus_posterior_brier"] = str(F(39, 220) - F(3, 20))
    summary["scope"] = "Exact synthetic finite population, not fitted or real-data risk"
    save("SUMMARY.json", summary)
    artifacts = {}
    for name in ("T1_WORLDS.json", "T2_WORLDS.json", "ONLINE_STATE_TRACES.json", "ARM_CALCULATIONS.json",
                 "FINITE_ENCODER_ENUMERATION.json", "SUMMARY.json"):
        content = (ROOT / name).read_bytes()
        artifacts[name] = {"bytes": len(content), "sha256": sha256(content).hexdigest()}
    receipt = {"started_utc": started, "finished_utc": now(), "status": "PASS",
               "arithmetic": "fractions.Fraction only for probabilities and risks",
               "world_counts": {"T1": len(t1), "T2": len(t2)},
               "encoder_counts": {"1_bit": 16, "2_bit": 256},
               "identities": identity, "artifacts": artifacts,
               "real_data_reads": 0, "network_requests": 0, "model_runs": 0}
    save("RUN_RECEIPT.json", receipt)
    print(json.dumps({"status": receipt["status"], "summary": summary}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        if not (ROOT / "FAILURE.json").exists():
            save("FAILURE.json", {"recorded_utc": now(), "error_type": type(exc).__name__,
                                  "message": str(exc), "scope": "synthetic calculation"})
        raise
