"""One pure source-schedule evaluation; never import a model or read scientific data."""
import ast, csv, hashlib, io, json, math, sys, time
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path
from typing import Union

HERE = Path(__file__).parent
def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def put(name, obj): (HERE/name).write_text(json.dumps(obj, indent=2, allow_nan=False)+"\n")
def fs(x): return str(x.numerator)+"/"+str(x.denominator)

def main():
    started, tick = now(), time.monotonic()
    with (HERE/"STARTED.json").open("x") as out:
        json.dump({"started_utc": started, "single_attempt": True}, out)
    result = {"status": "STARTED", "started_utc": started, "schedule_calls": 0,
              "model_calls": 0, "scientific_data_reads": 0}
    try:
        raw_contract = (HERE/"CONTRACT.json").read_bytes()
        cfg = json.loads(raw_contract)
        result["contract_sha256"] = sha(raw_contract)
        assert sha(Path(__file__).read_bytes()) == cfg["script_sha256"]
        src = Path(cfg["source"]["path"]).read_bytes()
        assert sha(src) == cfg["source"]["sha256"]
        tree = ast.parse(src)
        names = cfg["definition_names"]
        nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names]
        assert [n.name for n in nodes] == names
        # These are the original schedule's necessary numerical dependencies.
        import numpy as np
        import torch
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        env = {"torch": torch, "np": np, "Union": Union}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), cfg["source"]["path"], "exec"), env)
        result["definitions"] = [{"name": n.name, "first_line": n.lineno, "last_line": n.end_lineno} for n in nodes]
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "EulerEDMSampler")
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "sampler_step")
        assignment = next(n for n in method.body if isinstance(n, ast.Assign) and
                          any(isinstance(t, ast.Name) and t.id == "sigma_hat" for t in n.targets))
        result["sigma_hat_source"] = ast.get_source_segment(src.decode(), assignment)
        result["sigma_hat_line"] = assignment.lineno
        # Exactly one DDPMDiscretization instance and one 50-step call.
        disc = env["DDPMDiscretization"]()
        sigmas = disc(50, do_append_zero=True, flip=False, device="cpu")
        result["schedule_calls"] += 1
        assert sigmas.shape == (51,) and sigmas.dtype == torch.float32
        assert torch.isfinite(sigmas).all() and torch.all(sigmas[:-1] > sigmas[1:]) and sigmas[-1] == 0
        sigma, next_sigma = sigmas[:-1], sigmas[1:]
        sigma_hat = eval(compile(ast.Expression(assignment.value), cfg["source"]["path"], "eval"),
                         {"sigma": sigma, "gamma": 0.0})
        assert sigma_hat.dtype == torch.float32 and torch.all(sigma_hat > 0)
        s, sn, sh = sigma.tolist(), next_sigma.tolist(), sigma_hat.tolist()
        eta = [1-F(n)/F(h) for n,h in zip(sn,sh)]
        assert all(0 < e <= 1 for e in eta) and eta[49] == 1
        a, late_ids = F(1,4), set(range(25,49))
        pre_sum, late_sum = sum(eta[:49],F()), sum(eta[25:49],F())
        c = a*pre_sum/late_sum
        valid_c = 0 <= c <= 1
        uniform = [a]*50
        late = [c if k in late_ids else a if k==49 else F() for k in range(50)]
        bu = sum((e*l for e,l in zip(eta,uniform)),F())
        bl = sum((e*l for e,l in zip(eta,late)),F())
        assert bu == bl
        c32t = torch.tensor(float(c),dtype=torch.float32)
        c32 = F(c32t.item())
        late32 = [c32 if k in late_ids else a if k==49 else F() for k in range(50)]
        bl32 = sum((e*l for e,l in zip(eta,late32)),F())
        upper = F(torch.nextafter(c32t, torch.tensor(float("inf"),dtype=torch.float32)).item())
        lower = F(torch.nextafter(c32t, torch.tensor(float("-inf"),dtype=torch.float32)).item())
        rounding_bound = max(upper-c32,c32-lower)/2*late_sum
        assert abs(bl32-bu) <= rounding_bound
        bu64 = math.fsum(float(e)*float(l) for e,l in zip(eta,uniform))
        bl64 = math.fsum(float(e)*float(l) for e,l in zip(eta,late))
        assert abs(bl64-bu64) <= cfg["fp64_budget_atol"]
        rows = []
        for k in range(50):
            rows.append(dict(k=k, step_one_based=k+1, sigma_fp32=s[k], next_sigma_fp32=sn[k],
                sigma_hat_fp32=sh[k], eta_numerator=eta[k].numerator, eta_denominator=eta[k].denominator,
                eta_fp64=float(eta[k]), lambda_uniform=0.25, lambda_late_exact_as_fp64=float(late[k]),
                lambda_late_as_fp32=float(late32[k]), uniform_active=True, late_active=bool(late[k]),
                B_uniform_contribution_fp64=float(eta[k]*a),
                B_late_contribution_fp64=float(eta[k]*late[k]),
                B_late_fp32lambda_contribution_fp64=float(eta[k]*late32[k])))
        buf=io.StringIO(newline="")
        writer=csv.DictWriter(buf,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
        csv_bytes=buf.getvalue().encode()
        (HERE/"SCHEDULE_50.csv").write_bytes(csv_bytes)
        T=lambda x:x/2+F(1,2)
        P=lambda x:2*x
        Q=lambda x:3*x/4+F(1,4)
        early, late_toy=P(T(F())),T(P(F()))
        assert (early,late_toy,Q(early),Q(late_toy))==(F(1),F(1,2),F(1),F(5,8))
        toy={"setting":"Artificial scalar maps only; not a diffusion model",
             "T":"x/2+1/2", "F":"2*x", "Q":"3*x/4+1/4", "x":"0/1",
             "F_after_T":fs(early), "T_after_F":fs(late_toy),
             "early_pulse_injection":fs(T(F())-F()),
             "late_pulse_injection":fs(T(P(F()))-P(F())),
             "Q_after_early":fs(Q(early)), "Q_after_late":fs(Q(late_toy)),
             "squared_error_reference_1":[fs((Q(v)-1)**2) for v in (early,late_toy)],
             "squared_error_reference_0":[fs(Q(v)**2) for v in (early,late_toy)]}
        result.update(status="COMPLETED_FEASIBLE" if valid_c else "COMPLETED_INFEASIBLE",
            torch_version=torch.__version__, numpy_version=np.__version__, python=sys.version,
            source=cfg["source"], num_sigmas=51, csv_rows=50, gamma=0.0,
            c_exact=fs(c), c_fp64=float(c), c_within_unit_interval=valid_c, c_fp32=float(c32),
            eta_sum_pre49_exact=fs(pre_sum), eta_sum_pre49_fp64=float(pre_sum),
            eta_sum_late24_exact=fs(late_sum), eta_sum_late24_fp64=float(late_sum),
            B_uniform_exact=fs(bu), B_late_exact=fs(bl), B_exact_difference=fs(bl-bu),
            B_uniform_fp64=bu64, B_late_fp64=bl64, B_fp64_difference=bl64-bu64,
            B_late_fp32lambda_fp64=float(bl32), B_fp32lambda_difference_exact=fs(bl32-bu),
            B_fp32lambda_difference_fp64=float(bl32-bu), B_fp32_rounding_bound=float(rounding_bound),
            lambda_sum_uniform_exact=fs(sum(uniform,F())), lambda_sum_uniform_fp64=float(sum(uniform,F())),
            lambda_sum_late_exact=fs(sum(late,F())), lambda_sum_late_fp64=float(sum(late,F())),
            lambda_sum_late_fp32lambda_fp64=float(sum(late32,F())),
            uniform_nonzero_count=sum(bool(v) for v in uniform), late_nonzero_count=sum(bool(v) for v in late),
            counterexample=toy, csv_bytes=len(csv_bytes), csv_sha256=sha(csv_bytes),
            scope="Exact rational coefficient budget on original FP32 sigma/sigma_hat constants; not FP32 sampler output equivalence or realized guidance dose")
    except BaseException as exc:
        result.update(status="FAILED", error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        result.update(completed_utc=now(), elapsed_seconds=time.monotonic()-tick)
        put("RESULT.json",result)
    print(json.dumps({k:result[k] for k in ["status","c_fp64","c_fp32","B_uniform_fp64","B_late_fp64",
        "B_fp64_difference","B_fp32lambda_difference_fp64","lambda_sum_uniform_fp64",
        "lambda_sum_late_fp64","uniform_nonzero_count","late_nonzero_count","elapsed_seconds"]},indent=2))

if __name__=="__main__": main()

