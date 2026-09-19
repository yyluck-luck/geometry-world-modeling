from __future__ import annotations
import hashlib, json, math
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work/S91R_saved_future_error_reanalysis"
P = ROOT / "results/S15B_prefix_proposals/proposals.npz"
T = ROOT / "results/S15B_consumer_predictions/target_predictions.npz"
G = ROOT / "results/S15B_consumer_scores/evaluation_gt.npz"
TC = ROOT / "work/S15B_witness_preparation_root/target_camera_inputs.npz"
N = 224

def sha(path: Path) -> str:
    h = hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()

def ridge_fit_predict(xtr, ytr, xte, alpha=1e-3):
    # Fixed standardization and ridge; no tuning and no test-target statistics.
    mu = xtr.mean(0); sd = xtr.std(0); sd = np.where(sd > 1e-12, sd, 1.0)
    a = (xtr - mu) / sd; b = (xte - mu) / sd
    # Explicit intercept, normal equations are adequate for this fixed audit.
    aa = np.column_stack([np.ones(len(a)), a])
    bb = np.column_stack([np.ones(len(b)), b])
    reg = np.eye(aa.shape[1]); reg[0, 0] = 0.0
    beta = np.linalg.solve(aa.T @ aa + alpha * reg, aa.T @ ytr)
    return bb @ beta

def r2(y, pred):
    den = float(((y - y.mean()) ** 2).sum())
    return None if den <= 0 else float(1.0 - ((y - pred) ** 2).sum() / den)

def rankdata(x):
    order = np.argsort(x, kind="mergesort")
    r = np.empty(len(x), float); r[order] = np.arange(len(x), dtype=float)
    vals = x[order]; i = 0
    while i < len(x):
        j = i + 1
        while j < len(x) and vals[j] == vals[i]: j += 1
        if j - i > 1: r[order[i:j]] = 0.5 * (i + j - 1)
        i = j
    return r

def spearman(x, y):
    if len(x) < 3: return None
    a = rankdata(x); b = rankdata(y); a -= a.mean(); b -= b.mean()
    den = math.sqrt(float((a*a).sum() * (b*b).sum()))
    return None if den == 0 else float((a*b).sum() / den)

def edge_map(z):
    # Past-only geometric edge proxy; no RGB or future data.
    out = np.empty_like(z, dtype=float)
    for i in range(z.shape[0]):
        gy, gx = np.gradient(z[i])
        den = np.maximum(np.abs(z[i]), 1e-9)
        out[i] = np.sqrt(gx*gx + gy*gy) / den
    return out

def quantile_audit(d, pred, gt):
    out = []
    for method, mi in [("never", 0), ("all_new", 1)]:
        for ti in range(4):
            ids = pred["source_pixel_identity"][mi, ti].astype(int)
            p = pred["depth_m"][mi, ti].astype(float)
            future_valid = (ids >= 0) & np.isfinite(p) & (p > 0) & np.isfinite(gt[ti]) & (gt[ti] > 0)
            src = ids // (N*N); loc = ids % (N*N); rr = loc // N; cc = loc % N
            for si in range(4):
                # Correct: edges from all past finite pixels, before future mask.
                past = d[si]; past = past[np.isfinite(past)]
                edges = np.quantile(past, [0, .2, .4, .6, .8, 1]).astype(float)
                m = future_valid & (src == si)
                x = d[si, rr[m], cc[m]]
                y = np.abs(p[m] - gt[ti][m]) / gt[ti][m]
                z = np.isfinite(x) & np.isfinite(y)
                x, y = x[z], y[z]
                bins = np.digitize(x, edges[1:-1], right=True)
                means = [float(y[bins == k].mean()) if np.any(bins == k) else None for k in range(5)]
                out.append({"method": method, "target_index": 20+ti, "source_ordinal": si,
                            "n": int(len(x)), "past_only_edges": edges.tolist(),
                            "corrected_error_mean_by_quintile": means,
                            "corrected_high_minus_low": (means[-1]-means[0]) if means[0] is not None and means[-1] is not None else None})
    return out

def main():
    prop = np.load(P, allow_pickle=False); pred = np.load(T, allow_pickle=False)
    gt = np.load(G, allow_pickle=False)["depth_m"].astype(float)
    target_c2w = np.load(TC, allow_pickle=False)["target_c2w"].astype(float)
    old = prop["old_self_z_m"].astype(float); new = prop["new_self_z_m"].astype(float)
    conf = prop["new_conf_self"].astype(float)
    d = np.full(old.shape, np.nan); ok = np.isfinite(old)&np.isfinite(new)&(old>0)&(new>0)
    d[ok] = np.abs(new[ok]-old[ok]) / (0.5*(np.abs(new[ok])+np.abs(old[ok])))
    invconf = np.full(conf.shape, np.nan); okc = np.isfinite(conf)&(conf>0); invconf[okc] = 1/conf[okc]
    edge = edge_map(new)
    src_pose = prop["source_poses"].astype(float)
    target_pose = target_c2w
    source_valid = pred["source_valid"].astype(bool)
    conf_mask = pred["model_confidence_mask"].astype(bool)
    records = []
    for ti in range(4):
        ids0 = pred["source_pixel_identity"][0, ti].astype(int)
        ids1 = pred["source_pixel_identity"][1, ti].astype(int)
        p0 = pred["depth_m"][0, ti].astype(float); p1 = pred["depth_m"][1, ti].astype(float)
        valid = (ids0 >= 0)&(ids1 >= 0)&np.isfinite(p0)&(p0>0)&np.isfinite(p1)&(p1>0)&np.isfinite(gt[ti])&(gt[ti]>0)
        yy, xx = np.where(valid)
        ids = ids0[valid]; si = ids // (N*N); loc = ids % (N*N); rr = loc // N; cc = loc % N
        e0 = np.abs(p0[valid]-gt[ti][valid])/gt[ti][valid]; e1 = np.abs(p1[valid]-gt[ti][valid])/gt[ti][valid]
        y = e0 - e1
        xD = d[si, rr, cc]; xC = invconf[si, rr, cc]; xZ = np.log(new[si, rr, cc]); xE = edge[si, rr, cc]
        xM = conf_mask[si, rr, cc].astype(float); xV = source_valid[si, rr, cc].astype(float)
        pd = np.linalg.norm(src_pose[si, :3, 3] - target_pose[ti, :3, 3], axis=1)
        finite = np.isfinite(y)&np.isfinite(xD)&np.isfinite(xC)&np.isfinite(xZ)&np.isfinite(xE)&np.isfinite(pd)
        y=y[finite]; xD=xD[finite]; xC=xC[finite]; xZ=xZ[finite]; xE=xE[finite]; xM=xM[finite]; xV=xV[finite]; pd=pd[finite]
        X0=np.column_stack([xC,xZ,xE,xM,pd]); X1=np.column_stack([xC,xZ,xE,xM,pd,xD])
        same_ids = float(np.mean(ids[finite] == ids1[valid][finite])) if np.any(finite) else None
        records.append({"target_index":20+ti,"n":int(len(y)),"mean_signed_improvement":float(y.mean()) if len(y) else None,
                        "median_signed_improvement":float(np.median(y)) if len(y) else None,
                        "fraction_all_new_improves":float(np.mean(y>0)) if len(y) else None,
                        "same_source_identity_fraction":same_ids,
                        "spearman_D_signed_improvement":spearman(xD,y) if len(y)>=3 else None,
                        "features_source_valid_fraction":float(xV.mean()) if len(y) else None,
                        "X0":X0,"X1":X1,"y":y})
    cv=[]
    for hold in range(4):
        tr=[r for j,r in enumerate(records) if j!=hold]; te=records[hold]
        x0=np.concatenate([r["X0"] for r in tr]); x1=np.concatenate([r["X1"] for r in tr]); yt=np.concatenate([r["y"] for r in tr])
        p0=ridge_fit_predict(x0,yt,te["X0"]); p1=ridge_fit_predict(x1,yt,te["X1"])
        r20=r2(te["y"],p0); r21=r2(te["y"],p1)
        cv.append({"held_out_target":te["target_index"],"n_test":int(len(te["y"])),"mse_controls":float(np.mean((te["y"]-p0)**2)),"mse_controls_plus_D":float(np.mean((te["y"]-p1)**2)),"r2_controls":r20,"r2_controls_plus_D":r21,"delta_r2":(r21-r20) if r20 is not None and r21 is not None else None})
    # Avoid serializing large matrices in final JSON.
    for r in records: r.pop("X0"); r.pop("X1"); r.pop("y")
    deltas=[x["delta_r2"] for x in cv if x["delta_r2"] is not None]
    same=[x["same_source_identity_fraction"] for x in records if x["same_source_identity_fraction"] is not None]
    avg_delta=float(np.mean(deltas)) if deltas else None
    positive_folds=int(sum(x>0 for x in deltas))
    status="STOP_GRC_METHOD_CLAIM"
    reason=[]
    if len(deltas)<4 or positive_folds<3 or avg_delta is None or avg_delta<=0: reason.append("no stable held-out incremental ΔR²")
    if same and float(np.mean(same)) < 0.5: reason.append("never/all_new same-source identity is low; D is not same-item effect")
    out={"schema":"s91r-c-fixed-retrospective-control-v1","status":status,"protocol_sha256":sha(OUT/"CONTROL_AUDIT_PROTOCOL.md"),"inputs":{str(p.relative_to(ROOT)):sha(p) for p in [P,T,G,TC]},"counts":{"methods":2,"targets":4,"sources":4,"strata_total":32,"strata_per_method":16},"signed_outcome_definition":"y=AbsRel_never-AbsRel_all_new; positive means all_new improves","stratum_records":records,"leave_one_target_out":cv,"mean_delta_r2":avg_delta,"positive_delta_r2_folds":positive_folds,"corrected_quantile_audit":quantile_audit(d,pred,gt),"stop_reasons":reason or ["predefined stop rule triggered"],"limitations":["single already-exposed TUM segment","saved predictions and future GT; no new model call","source identity changes between methods for most paired target pixels","descriptive retrospective control; no GRC validation"]}
    (OUT/"control_audit_results.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    # compact human report
    lines=["# S91R-C（已保存数据的增量风险与有符号未来收益控制审查）", "", "## 结论", "", f"状态：`{status}`。这是一次固定的回顾性控制分析，不是新模型实验。", ""]
    lines.append(f"S91R 的分层计数为 2 方法 × 4 目标 × 4 来源 = 32；每个方法只有 16 个分层组合。原 S91R 的独立复算通过只证明同一数据账本可复算，不能称外部独立复现。")
    lines.append(f"留一目标控制模型平均 `ΔR²`={avg_delta!r}，4 个留出目标中正值={positive_folds}/4。`never` 与 `all_new` 配对像素的 source identity 相同率为 " + ", ".join(f"{r['target_index']}:{r['same_source_identity_fraction']:.4f}" for r in records) + "。")
    for r in records: lines.append(f"- 目标 {r['target_index']}：n={r['n']}，有符号改善均值={r['mean_signed_improvement']:.6f}（正值才表示 all_new 改善），改善比例={r['fraction_all_new_improves']:.4f}，D 与有符号改善 Spearman={r['spearman_D_signed_improvement']!r}。")
    lines += ["", "## 预先固定的否决结果", "", "- 由于两方法大多数目标像素的 source identity 不相同，D 不能解释为同一记忆条目被替换后的因果收益。", "- 若 `ΔR²` 未在至少 3/4 留出目标为正，或平均值不为正，则 disagreement 没有稳定的增量预测证据。", "- 因此本轮停止 GRC-Memory 方法主张；S91R 仅保留为单段已见数据的描述性风险信号。", "", "## 分位数泄漏修正", "", "原 S91R 的分位数边界在 future-valid mask 后计算，会让未来有效性参与分组。S91R-C 重新用每个来源全部过去 finite/positive old/new proposal 计算五分位边界，再应用到未来有效像素；修正结果只写入 JSON，不回写原 S91R。", "", "证据：`control_audit_results.json`、`CONTROL_AUDIT_PROTOCOL.md`、`run_s91r_control_audit.py`。"]
    (OUT/"CONTROL_AUDIT_REPORT.md").write_text("\n".join(lines)+"\n")
    print(json.dumps({"status":status,"strata_total":32,"strata_per_method":16,"mean_delta_r2":avg_delta,"positive_delta_r2_folds":positive_folds,"output":str(OUT/"CONTROL_AUDIT_REPORT.md")},ensure_ascii=False))

if __name__ == "__main__": main()
