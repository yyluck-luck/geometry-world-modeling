"""Render accepted saved statistics; no model or feature extraction."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

D = Path(__file__).absolute().parent
b = (D / 'execution_02/receipt.json').read_bytes()
assert hashlib.sha256(b).hexdigest() == '8a953c7a477ddbc84721be4fe6f9974e923a45cd6718c840a2dfb149b958ba01'
assert json.loads((D/'ROOT_RESULT_ACCEPTANCE.json').read_text())['status'] == 'ACCEPTED_S73_EXISTING_IMAGE_ARITHMETIC_ONLY'
r = json.loads(b)
out = D/'visuals_01'
out.mkdir(exist_ok=False)
started = datetime.now(timezone.utc).isoformat()
plt.rcParams.update({'font.size':10, 'svg.fonttype':'none', 'axes.spines.top':False, 'axes.spines.right':False})
fig, axs = plt.subplots(1, 2, figsize=(11.4, 5.3))
arms = ['real','A0','B']
labels = ['Real photos (reused control)', 'A0 generated', 'B generated']
colors = ['#555555','#0072B2','#D55E00']
markers = ['o','s','^']
for k, (arm, label, col, marker) in enumerate(zip(arms, labels, colors, markers)):
    rows = [next(p for p in r['pairs'] if p['arm']==arm and p['target_id']==j) for j in range(20,24)]
    x = np.arange(4) + (k-1)*.23
    vals = [100*p['matched_fraction'] for p in rows]
    axs[0].bar(x, vals, width=.21, color=col, alpha=.85)
    for xi, y, p in zip(x, vals, rows):
        axs[0].text(xi, y+.5, str(p['match_count']), ha='center', va='bottom', fontsize=9)
    qs = np.array([p['residual_quantiles_px'] for p in rows])
    axs[1].vlines(x, qs[:,0], qs[:,3], color=col, lw=1.1)
    axs[1].vlines(x, qs[:,0], qs[:,2], color=col, lw=4, alpha=.55)
    axs[1].plot(x, qs[:,1], linestyle='none', marker=marker, color=col, markersize=6, label=label)
    axs[1].plot(x, qs[:,3], linestyle='none', marker='_', color=col, markersize=8)
axs[0].set(title='A  Match availability', ylabel='Matched anchor features / 1,239 (%)', ylim=(0,31))
axs[0].text(.03,.98,'Counts above bars; order: real / A0 / B', transform=axs[0].transAxes, va='top', fontsize=9)
axs[1].set(title='B  Error on available matches', ylabel='Symmetric point-to-line distance (px; log)', yscale='log', ylim=(.5,500))
axs[1].text(.03,.98,'Marker: median; thick: IQR; cap: 95th percentile', transform=axs[1].transAxes, va='top', fontsize=9)
for ax in axs:
    ax.set_xticks(range(4), ['20','21','22','23'])
    ax.set_xlabel('Requested target ID (same real anchor 19)')
    ax.grid(axis='y',alpha=.18)
    ax.set_axisbelow(True)
handles, names = axs[1].get_legend_handles_labels()
fig.legend(handles,names,loc='upper center',bbox_to_anchor=(.5,.94),ncol=3,frameon=False)
fig.suptitle('S73  |  Existing generated images disagree with fixed requested geometry', y=.99, fontsize=13)
fig.subplots_adjust(top=.80,bottom=.25,left=.075,right=.985,wspace=.26)
fig.text(.075,.13,'Three-way shared anchor IDs (real / A0 / B): 92, 48, 6, 0 for targets 20–23.', fontsize=10)
fig.text(.075,.085,'Both all-four paired events: UNKNOWN (target 23 has no common support).', fontsize=10, weight='bold')
fig.text(.075,.037,'One exposed scene; different match populations. Quantile ranges are not confidence intervals. Approximate K; no new generation.',fontsize=9)
files=[]
for ext in ['svg','png']:
    p=out/f'S73_support_and_error.{ext}'
    fig.savefig(p,dpi=180,facecolor='white')
    files.append(dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
plt.close(fig)
receipt=dict(started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),input_sha256=hashlib.sha256(b).hexdigest(),matplotlib=matplotlib.__version__,numpy=np.__version__,files=files,scope='Plot accepted all12 saved rows only. No images, SIFT, models or new scientific scores.',new_method_validated=False)
with (out/'EXPORT_RECEIPT.json').open('x') as f: json.dump(receipt,f,indent=2);f.write('\n')
for p in out.iterdir(): p.chmod(0o444)
print(json.dumps(receipt))
