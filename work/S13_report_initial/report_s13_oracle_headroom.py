#!/usr/bin/env python3
"""Post-hoc CSV/figure report from the independent S13 integer audit; no scoring."""
from pathlib import Path
from fractions import Fraction
from datetime import datetime, timezone
import csv
import hashlib
import json
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'results/S13_independent_audit'
OUT = ROOT / 'reports/S13'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csv_write(name, rows):
    with (OUT / name).open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    started = datetime.now(timezone.utc).isoformat()
    inputs = [AUDIT / f for f in ('verification.json', 'independent_records.json', 'independent_summary.json')]
    original_hashes = {str(p.relative_to(ROOT)): digest(p) for p in inputs}
    verification = json.loads(inputs[0].read_text())
    assert verification['status'] == 'PASS'
    assert verification['actual_combinations_enumerated'] == 164328
    assert verification['protocol_status'] == 'DISCLOSED_DEVIATION'
    records = json.loads(inputs[1].read_text())
    assert len(records) == 24
    OUT.mkdir(exist_ok=False)
    rows, strata_rows = [], []
    strata = ['S7_development_4', 'S7_test_8', 'S8_test_12']
    grouped = {s: [] for s in strata}
    for r in records:
        s = 'S7_development_4' if r['split'] == 'development' else ('S7_test_8' if r['stage'] == 'S7' else 'S8_test_12')
        grouped[s].append(r)
        for pool in ('geometry14', 'pose14'):
            cur, ora, all20 = r['current'][pool], r['oracle'][pool], r['oracle']['all20']
            assert cur['valid_pixels'] == ora['valid_pixels'] == all20['valid_pixels']
            d = cur['valid_pixels']
            within = Fraction(ora['supported_pixels'] - cur['supported_pixels'], d) * 100
            exclusion = Fraction(all20['supported_pixels'] - ora['supported_pixels'], d) * 100
            total = Fraction(all20['supported_pixels'] - cur['supported_pixels'], d) * 100
            assert within >= 0 and exclusion >= 0 and within + exclusion == total
            rows.append(dict(stratum=s, stage=r['stage'], block=r['block'], query=r['query'], pool=pool,
                valid_pixels=d, current_pixels=cur['supported_pixels'], pool_oracle_pixels=ora['supported_pixels'],
                all20_oracle_pixels=all20['supported_pixels'], current_support_percent=float(Fraction(cur['supported_pixels'],d)*100),
                pool_oracle_support_percent=float(Fraction(ora['supported_pixels'],d)*100),
                all20_oracle_support_percent=float(Fraction(all20['supported_pixels'],d)*100),
                within_pool_hindsight_gap_pp=float(within), candidate_exclusion_gap_pp=float(exclusion),
                total_hindsight_gap_pp=float(total), exact_within_pool_gap_pp=str(within),
                exact_candidate_exclusion_gap_pp=str(exclusion), exact_total_gap_pp=str(total),
                current_ids=' '.join(map(str,cur['selected'])), pool_oracle_ids=' '.join(map(str,ora['selected'])),
                all20_oracle_ids=' '.join(map(str,all20['selected'])),
                pool_oracle_ties=ora['optimal_combination_count'], all20_oracle_ties=all20['optimal_combination_count'],
                current_oracle_intersection=len(set(cur['selected']) & set(ora['selected'])),
                oracle_enforces_nms=False))
    for s in strata:
        for pool in ('geometry14', 'pose14'):
            subset = [r for r in rows if r['stratum'] == s and r['pool'] == pool]
            n = len(subset)
            out = dict(stratum=s, n_queries=n, pool=pool)
            for field, num in [('current_support_percent','current_pixels'),('pool_oracle_support_percent','pool_oracle_pixels'),('all20_oracle_support_percent','all20_oracle_pixels')]:
                out[field] = float(sum((Fraction(r[num],r['valid_pixels'])*100 for r in subset),Fraction())/n)
            for field in ('within_pool_hindsight_gap_pp','candidate_exclusion_gap_pp','total_hindsight_gap_pp'):
                exact = {'within_pool_hindsight_gap_pp':'exact_within_pool_gap_pp','candidate_exclusion_gap_pp':'exact_candidate_exclusion_gap_pp','total_hindsight_gap_pp':'exact_total_gap_pp'}[field]
                out[field] = float(sum((Fraction(r[exact]) for r in subset),Fraction())/n)
            out['zero_within_pool_gap_queries'] = sum(r['within_pool_hindsight_gap_pp'] == 0 for r in subset)
            out['oracle_ties_min'] = min(r['pool_oracle_ties'] for r in subset)
            out['oracle_ties_max'] = max(r['pool_oracle_ties'] for r in subset)
            out['aggregation'] = 'equal query mean; no pooling across strata'
            strata_rows.append(out)
    csv_write('all_24_queries_two_pools.csv',rows)
    csv_write('three_strata_two_pools.csv',strata_rows)
    font_path = '/System/Library/Fonts/Hiragino Sans GB.ttc'
    font_manager.fontManager.addfont(font_path)
    plt.rcParams.update({'font.family':font_manager.FontProperties(fname=font_path).get_name(),
                         'font.size':10,'axes.unicode_minus':False,'pdf.fonttype':42,'svg.fonttype':'path'})
    fig, axes = plt.subplots(3,1,figsize=(7.2,5.1),sharex=True)
    fig.subplots_adjust(left=.14,right=.95,top=.91,bottom=.17,hspace=.77)
    names = {'S7_development_4':'S7 开发 · 4 个查询', 'S7_test_8':'S7 测试 · 8 个查询','S8_test_12':'S8 测试 · 12 个查询'}
    limit = math.ceil(max(r['total_hindsight_gap_pp'] for r in strata_rows)/2)*2 + 2
    for ax, s in zip(axes,strata):
        rr = [r for r in strata_rows if r['stratum'] == s]
        a = [r['within_pool_hindsight_gap_pp'] for r in rr]
        b = [r['candidate_exclusion_gap_pp'] for r in rr]
        ax.barh([1,0],a,height=.47,color='#0072B2',label='池内余量：14池上限 − 当前四图')
        ax.barh([1,0],b,left=a,height=.47,color='#E69F00',edgecolor='#4a412b',hatch='///',linewidth=.4,label='候选排除差距：20池上限 − 14池上限')
        ax.set_yticks([1,0],['来源14','姿态14'])
        for y,aa,bb in zip([1,0],a,b):
            ax.text(aa+bb+.13,y,f'{aa:.2f} + {bb:.2f}',va='center',fontsize=9)
        ax.set_title(names[s],loc='left',fontsize=10,pad=6)
        ax.set_xlim(0,limit)
        ax.set_ylim(-.6,1.6)
        ax.set_axisbelow(True)
        ax.grid(axis='x',color='#e6e8ec',linewidth=.6)
        for side in ('right','top','left'): ax.spines[side].set_visible(False)
        ax.spines['bottom'].set_color('#999999')
        ax.tick_params(axis='both',length=0)
    axes[-1].set_xlabel('支持率差距（百分点）；两段相加 = 全20池上限 − 当前四图',fontsize=9)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower left',bbox_to_anchor=(.13,.003),fontsize=9,frameon=False,ncol=1)
    for ext in ('pdf','svg','png'):
        fig.savefig(OUT/f'oracle_gap_decomposition.{ext}',dpi=180)
    plt.close(fig)
    provenance = dict(started_utc=started,completed_utc=datetime.now(timezone.utc).isoformat(),
        inputs_sha256=original_hashes,script_sha256=digest(Path(__file__)),
        environment={'python':sys.version,'executable':sys.executable,'numpy':np.__version__,'matplotlib':matplotlib.__version__},
        rows={'per_query_two_pools':len(rows),'strata_two_pools':len(strata_rows)},
        checks={'exact_decomposition':48,'nonnegative_component_pairs':48,'input_unchanged':True},
        scope='Post-hoc arithmetic decomposition from audited integer counts. GT oracle relaxes NMS. Not causal attribution or deployable gain. No new scoring/model/NMS/raw data.',
        outputs_sha256={p.name:digest(p) for p in sorted(OUT.iterdir()) if p.is_file()})
    assert original_hashes == {str(p.relative_to(ROOT)):digest(p) for p in inputs}
    (OUT/'report_provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'output':str(OUT),'rows':provenance['rows'],'strata':strata_rows},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
