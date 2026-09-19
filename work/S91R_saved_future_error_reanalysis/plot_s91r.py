from pathlib import Path
import json
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]; D=ROOT/'work/S91R_saved_future_error_reanalysis'
x=json.loads((D/'results.json').read_text())
fig,ax=plt.subplots(figsize=(9,4.8))
for method,marker,color in [('never','o','#1f77b4'),('all_new','s','#d62728')]:
 rows=[r for r in x['rows'] if r['method']==method and r['n']]
 xx=[r['target_index']+0.07*(r['source_ordinal']-1.5) for r in rows]
 yy=[r['risk_disagreement']['spearman_risk_error'] for r in rows]
 ax.scatter(xx,yy,label=method,marker=marker,color=color,s=42,alpha=.85)
ax.axhline(0,color='0.3',lw=.8)
ax.set_xticks([20,21,22,23]); ax.set_xlabel('Future target index (already saved)')
ax.set_ylabel('Spearman: past-only disagreement risk vs future AbsRel')
ax.set_title('S91R retrospective diagnostic; one exposed TUM segment')
ax.legend(frameon=False); ax.grid(axis='y',alpha=.25); fig.tight_layout()
fig.savefig(D/'risk_future_correlation.png',dpi=180); fig.savefig(D/'risk_future_correlation.svg'); print('PLOT_PASS')
