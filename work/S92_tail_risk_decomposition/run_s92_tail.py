from __future__ import annotations
import hashlib, json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'work/S92_tail_risk_decomposition'
P=ROOT/'results/S15B_consumer_predictions/target_predictions.npz'
G=ROOT/'results/S15B_consumer_scores/evaluation_gt.npz'
N=224
BLOCK=16
B=1000


def sha(p):
 h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

def ci(v):
 return [float(np.quantile(v,.025)), float(np.quantile(v,.975))]

def one_target(e0,e1,abs0,abs1,rr,cc,seed):
 # Spatial block bootstrap over non-empty 16x16 blocks.
 bid=(rr//BLOCK)*(N//BLOCK)+(cc//BLOCK)
 ub,inv=np.unique(bid,return_inverse=True)
 K=len(ub)
 cnt=np.bincount(inv,minlength=K).astype(float)
 sums={
  'mae_never':np.bincount(inv,weights=abs0,minlength=K),
  'mae_all_new':np.bincount(inv,weights=abs1,minlength=K),
  'absrel_never':np.bincount(inv,weights=e0,minlength=K),
  'absrel_all_new':np.bincount(inv,weights=e1,minlength=K),
  'signed_improvement':np.bincount(inv,weights=e0-e1,minlength=K),
  'improved':np.bincount(inv,weights=(e0>e1).astype(float),minlength=K),
 }
 rng=np.random.default_rng(seed)
 out={k:np.empty(B,float) for k in ['mae_delta','absrel_delta','signed_mean','improved_fraction']}
 for j in range(B):
  draw=rng.integers(0,K,size=K)
  w=np.bincount(draw,minlength=K).astype(float)
  den=float(np.dot(w,cnt))
  out['mae_delta'][j]=np.dot(w,sums['mae_all_new']-sums['mae_never'])/den
  out['absrel_delta'][j]=np.dot(w,sums['absrel_all_new']-sums['absrel_never'])/den
  out['signed_mean'][j]=np.dot(w,sums['signed_improvement'])/den
  out['improved_fraction'][j]=np.dot(w,sums['improved'])/den
 return {k:ci(v) for k,v in out.items()}, int(K)

def main():
 pred=np.load(P,allow_pickle=False); gt=np.load(G,allow_pickle=False)['depth_m'].astype(float)
 d0=pred['depth_m'][0].astype(float); d1=pred['depth_m'][1].astype(float)
 records=[]
 for ti in range(4):
  g=gt[ti]; p0=d0[ti]; p1=d1[ti]
  valid=np.isfinite(g)&(g>0)&np.isfinite(p0)&(p0>0)&np.isfinite(p1)&(p1>0)
  rr,cc=np.where(valid)
  g=g[valid]; p0=p0[valid]; p1=p1[valid]
  abs0=np.abs(p0-g); abs1=np.abs(p1-g); e0=abs0/g; e1=abs1/g
  y=e0-e1; w=np.maximum(-y,0); gain=np.maximum(y,0)
  wp=w[w>0]
  q={f'q{q}':float(np.quantile(wp,q/100)) if len(wp) else None for q in [50,90,95,99]}
  order=np.sort(wp)[::-1] if len(wp) else np.array([])
  total_w=float(w.sum()); total_g=float(gain.sum())
  top5_n=max(1,int(np.ceil(.05*len(w))))
  top1_n=max(1,int(np.ceil(.01*len(w))))
  top5=float(order[:top5_n].sum()/total_w) if total_w>0 else None
  top1=float(order[:top1_n].sum()/total_w) if total_w>0 else None
  cis,blocks=one_target(e0,e1,abs0,abs1,rr,cc,seed=20260912+ti)
  records.append({
   'target_index':20+ti,'n_pixels':int(len(y)),'n_blocks_16x16':blocks,
   'mae_never_m':float(abs0.mean()),'mae_all_new_m':float(abs1.mean()),'mae_delta_all_new_minus_never_m':float(abs1.mean()-abs0.mean()),
   'absrel_never':float(e0.mean()),'absrel_all_new':float(e1.mean()),'absrel_delta_all_new_minus_never':float(e1.mean()-e0.mean()),
   'signed_absrel_improvement_mean_never_minus_all_new':float(y.mean()),
   'improved_fraction':float(np.mean(y>0)),'worsened_fraction':float(np.mean(y<0)),'tie_fraction':float(np.mean(y==0)),
   'improvement_component_mean':float(gain.mean()),'worsening_component_mean':float(w.mean()),
   'positive_improvement_total':total_g,'positive_worsening_total':total_w,
   'worsening_pixel_count':int((w>0).sum()),'improvement_pixel_count':int((gain>0).sum()),
   'worsening_absrel_quantiles':q,
   'top_1_percent_worsening_mass_fraction':top1,'top_5_percent_worsening_mass_fraction':top5,
   'block_bootstrap_replicates':B,'block_size_pixels':BLOCK,
   'bootstrap_95ci':cis,
   'interpretation':'tail-consistent' if (y.mean()<0 and y.mean() and np.mean(y>0)>.5 and top5 is not None and top5>.05) else 'descriptive-only'
  })
 out={'schema':'s92-saved-future-error-tail-risk-v1','status':'DESCRIPTIVE_ONLY','protocol_sha256':sha(OUT/'PROTOCOL.md'),'inputs':{str(p.relative_to(ROOT)):sha(p) for p in [P,G]},'method_mapping':{'never':0,'all_new':1},'targets':records,'limitations':['single already-exposed TUM segment','saved predictions and saved evaluation_gt only; no new model call or GT acquisition','pixels within a target are spatially correlated; block bootstrap is descriptive and does not establish scene-level generalization','tail decomposition does not identify geometry as the cause and does not validate GRC-Memory','S91R-C control audit and its stop rule are separate and unchanged']}
 (OUT/'results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 lines=['# S92（保存数据未来误差尾部风险分解）','','## 结论','', '状态：`DESCRIPTIVE_ONLY`。本轮只对已保存 S15B 预测和 `evaluation_gt.npz` 做回顾性尾部诊断，没有新模型调用、没有新 GT。']
 lines.append('S91R-C 观察到的“多数像素改善但平均 AbsRel 变差”可用下表检查是否由少数高幅度恶化像素造成。')
 lines += ['', '|目标|有效像素|MAE never→all_new (m)|AbsRel never→all_new|改善/恶化/持平|恶化 q50/q90/q95/q99|恶化总量中最高5%占比|','|---:|---:|---:|---:|---:|---:|---:|']
 for r in records:
  q=r['worsening_absrel_quantiles']; lines.append(f"|{r['target_index']}|{r['n_pixels']}|{r['mae_never_m']:.5f} → {r['mae_all_new_m']:.5f}|{r['absrel_never']:.5f} → {r['absrel_all_new']:.5f}|{r['improved_fraction']:.3f} / {r['worsened_fraction']:.3f} / {r['tie_fraction']:.3f}|{q['q50']:.4f} / {q['q90']:.4f} / {q['q95']:.4f} / {q['q99']:.4f}|{r['top_5_percent_worsening_mass_fraction']:.3f}|")
 lines += ['', '## 逐目标结果与区间','']
 for r in records:
  lines += [f"### 目标 {r['target_index']}", '', f"- 有效像素 `{r['n_pixels']}`，16×16非空空间块 `{r['n_blocks_16x16']}`。", f"- MAE：`{r['mae_never_m']:.6f} m → {r['mae_all_new_m']:.6f} m`，差值 all_new−never=`{r['mae_delta_all_new_minus_never_m']:.6f} m`。", f"- AbsRel：`{r['absrel_never']:.6f} → {r['absrel_all_new']:.6f}`，差值=`{r['absrel_delta_all_new_minus_never']:.6f}`；有符号改善均值 never−all_new=`{r['signed_absrel_improvement_mean_never_minus_all_new']:.6f}`。", f"- 像素比例：改善 `{r['improved_fraction']:.4f}`，恶化 `{r['worsened_fraction']:.4f}`，持平 `{r['tie_fraction']:.4f}`。", f"- 恶化像素 AbsRel 尾部 q50/q90/q95/q99=`{r['worsening_absrel_quantiles']}`；最高1%/5%恶化质量占全部恶化质量 `{r['top_1_percent_worsening_mass_fraction']:.4f}` / `{r['top_5_percent_worsening_mass_fraction']:.4f}`。", f"- 16×16块 bootstrap 95%区间（1000次）：MAE差 `{r['bootstrap_95ci']['mae_delta']}`，AbsRel差 `{r['bootstrap_95ci']['absrel_delta']}`，净改善均值 `{r['bootstrap_95ci']['signed_mean']}`，改善比例 `{r['bootstrap_95ci']['improved_fraction']}`。", '']
 lines += ['## 解释边界','', '若净均值为负、改善比例超过一半且恶化尾部质量集中在少数像素，这只支持“局部改善被少数大幅恶化抵消”的诊断。它不说明这些像素一定由几何风险造成，更不能替代 S91 的同记忆身份、固定预算和未见场景验证。S91R-C 的 `STOP_GRC_METHOD_CLAIM` 保持不变。','', '证据：`run_s92_tail.py`、`results.json`、`PROTOCOL.md`。']
 (OUT/'RESULTS.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps({'status':out['status'],'targets':records},ensure_ascii=False))
if __name__=='__main__': main()
