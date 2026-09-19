"""Build the four-page S86 result report only from root-bound accepted metadata.

Preparation never executes this entry point. Missing/unknown fields stop; no
placeholder numbers or fabricated result image is produced. No scientific NPZ,
NPY, source RGB/GT or model is read. The sole figure is the accepted overview PNG.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import time
import traceback

HERE=Path(__file__).resolve().parent
S86=HERE.parent
NAME='S86_固定历史投影四臂实际结果'
ROLES={'generation':'execution_01/RECEIPT.json','supervision':'supervision_01/SUPERVISION.json',
       'scoring':'scoring_01/RECEIPT.json','consumption_review':'INDEPENDENT_CONSUMPTION_REVIEW.json',
       'score_review':'INDEPENDENT_SCORE_REVIEW.json','export':'visuals_01/EXPORT_RECEIPT.json'}
ARMS=('G0','Gpaste','Gterminal','Gguide')
GEN_SHA='954c4353745280d5d3f48ac9db124b8a23aa877e1c59e9ecdd13f399416e844f'
READS=[]


def need(ok,why):
    if not bool(ok):raise ValueError(why)


def sha(data):return hashlib.sha256(data).hexdigest()


def read(path,digest):
    need(re.fullmatch('[0-9a-f]{64}',digest) is not None,'real full SHA required')
    data=Path(path).read_bytes();need(sha(data)==digest,'source identity: '+str(path))
    READS.append(dict(path=str(path),sha256=digest,bytes=len(data)))
    return data


def load(path,digest):
    def bad(x):raise ValueError('nonfinite JSON '+x)
    return json.loads(read(path,digest),parse_constant=bad)


def esc(value):
    table={'\\':r'\textbackslash{}','_':r'\_','%':r'\%','&':r'\&','#':r'\#','$':r'\$','{':r'\{','}':r'\}'}
    return ''.join(table.get(c,c) for c in str(value))


def number(x):
    need(type(x) in (int,float) and math.isfinite(x),'required finite number')
    return f'{x:.12g}'


def integer(x):
    need(type(x) is int,'required exact integer');return f'{x:,}'


def mse(row,region):
    count=row[region+'_channels'];value=row[region+'_mse']
    need(type(count) is int and count>=0,'region channel count')
    if count==0:
        need(value is None and row[region+'_empty'] is True and row[region+'_sse']==0,'empty region NA contract')
        return 'NA'
    need(row[region+'_empty'] is False and value is not None,'nonempty finite score')
    return number(value)


def row(values):return ' & '.join(str(x) for x in values)+r'\\'


def timestamp(value):
    parsed=dt.datetime.fromisoformat(value)
    need(parsed.tzinfo is not None,'timestamp must carry zone')
    return parsed.astimezone(dt.timezone(dt.timedelta(hours=8)))


def main(binding_sha):
    binding=load(HERE/'RESULT_REPORT_BINDING.json',binding_sha)
    need(binding['schema']=='S86_ROOT_ACCEPTED_RESULT_REPORT_BINDING_V1' and binding['accepted'] is True,'root accepted binding required')
    need(binding['builder_sha256']==sha(Path(__file__).read_bytes()),'builder exact identity')
    template=read(HERE/'S86_实际结果报告.template.tex',binding['template_sha256']).decode()
    cutoff=timestamp(binding['scientific_cutoff_utc'])
    accepted=timestamp(binding['accepted_utc']);need(accepted>=cutoff,'acceptance cannot precede evidence cutoff')
    data={role:load(S86/path,binding['inputs'][role]['sha256']) for role,path in ROLES.items()}
    for role,path in ROLES.items():need(binding['inputs'][role]['path']==str(S86/path),'fixed input role path')
    root_spec=binding['inputs']['root_acceptance']
    need(Path(root_spec['path']).resolve().is_relative_to(S86),'root acceptance must belong to S86')
    root_acceptance=load(root_spec['path'],root_spec['sha256'])
    need(root_acceptance['accepted'] is True and root_acceptance['scope']=='saved-consumption and descriptive RGB scores only' and root_acceptance['novelty_authorization']=='NONE','root finite scientific acceptance')
    for role,key in [('generation','generation_receipt_sha256'),('scoring','scoring_receipt_sha256'),('consumption_review','consumption_review_sha256'),('score_review','score_review_sha256')]:
        need(root_acceptance[key]==binding['inputs'][role]['sha256'],'root acceptance matches '+role)
    visual_spec=binding['inputs']['visual_acceptance']
    need(visual_spec['path']==str(S86/'ROOT_VISUAL_ACCEPTANCE.json'),'fixed visual acceptance path')
    visual_acceptance=load(visual_spec['path'],visual_spec['sha256'])
    need(visual_acceptance['accepted'] is True and visual_acceptance['export_receipt_sha256']==binding['inputs']['export']['sha256'],'root accepted bound visual export')
    g,s,c,r,v,e=(data[k] for k in ('generation','supervision','scoring','consumption_review','score_review','export'))
    need(g['status']=='COMPLETE_FOUR_FIXED_CONSUMER_ARMS_PENDING_REVIEW' and g['contract_sha256']==GEN_SHA and g['unrun_arms']==[],'four complete bound arms')
    need(s['status']=='COMPLETE' and s['returncode']==0 and s['worker_receipt_sha256']==binding['inputs']['generation']['sha256'],'successful accepted supervision')
    need(c['status']=='COMPLETE_DESCRIPTIVE_SCORES_PENDING_INDEPENDENT_REVIEW' and c['rows_completed']==16,'complete fixed scoring')
    need(c['generation_final_sha256']==binding['inputs']['generation']['sha256'],'score belongs to generation')
    need(r['status']==v['status']=='PASS','both independent reviews must actually pass')
    for review in (r,v):
        need(any(x['path']==str(S86/ROLES['generation']) and x['sha256']==binding['inputs']['generation']['sha256'] for x in review['reads']),'review belongs to generation')
    need(any(x['path']==str(S86/ROLES['scoring']) and x['sha256']==binding['inputs']['scoring']['sha256'] for x in v['reads']),'statistics review belongs to scores')
    need(e['status']=='COMPLETE_FIXED_COMPARISON_EXPORT_PENDING_VISUAL_QA' and e['total_pngs']==33 and e['native_pngs']==32,'all display images exported')
    need(binding['accepted_full_overview_visual_QA'] is True,'root overview visual acceptance required')
    for role in ('generation','scoring'):
        need(any(x['path']==str(S86/ROLES[role]) and x['sha256']==binding['inputs'][role]['sha256'] for x in e['reads']),'figure uses same accepted result')
    need(all(timestamp(x['completed_utc'])<=cutoff for x in data.values()),'cutoff must include every bound stage')
    artifacts={Path(x['path']).name:x for x in c['artifacts']}
    payload={}
    for name in ('FRAME_SCORES.json','ARM_SUMMARY.json','CONTRASTS.json'):
        spec=artifacts[name];need(spec['path']==str(S86/'scoring_01'/name),'fixed scoring artifact path')
        payload[name]=load(spec['path'],spec['sha256'])
    rows=payload['FRAME_SCORES.json'];summary=payload['ARM_SUMMARY.json'];contrasts=payload['CONTRASTS.json']['overall']
    need(len(rows)==16 and [(x['arm'],x['target_id']) for x in rows]==[(a,t) for a in ARMS for t in range(20,24)],'complete16 row order')
    need(len(contrasts)==3 and [x['comparison'] for x in contrasts]==['Gguide-Gterminal','Gguide-G0','Gguide-Gpaste'],'complete3 primary contrasts')
    need(g['full_chain_calls']==2 and g['warp_encoder_calls']==1 and g['derived_decoder_calls']==1,'real two-chain/two-derived protocol')
    for a in ARMS:need(g['arms'][a]['status']==('COMPLETE_CHAIN' if a in ('G0','Gguide') else 'COMPLETE_DERIVED'),'arm complete')
    for x in rows:
        need(x['full_pixels']==331776 and x['full_channels']==995328,'fixed full-frame denominator')
        need(x['support_pixels']+x['hole_pixels']==331776,'full pixel partition')
        for region in ('full','support','hole'):
            need(x[region+'_channels']==3*x[region+'_pixels'],'RGB region channels');mse(x,region)
    for a in ARMS:need(summary[a]['full']['total_channels']==3981312 and summary[a]['full']['complete_four_frames'] is True,'no target dropping')
    image=[x for x in e['images'] if Path(x['path']).name=='overview_4targets_6columns.png']
    need(len(image)==1,'one complete overview');image=image[0]
    need(image['path']==str(S86/'visuals_01/overview_4targets_6columns.png') and image['size']==[3540,2720] and image['pixel_readback_exact'] is True,'exact overview identity')
    png=read(image['path'],image['sha256'])
    need(png[:8]==b'\x89PNG\r\n\x1a\n','actual PNG required')
    delta={x['comparison']:x['full_total_sse_difference'] for x in contrasts}
    def verdict(label):
        value=delta['Gguide-'+label]
        return '低于' if value<0 else '高于' if value>0 else '等于'
    main_finding='Gguide的完整四帧主MSE'+verdict('G0')+'G0，'+verdict('Gterminal')+'Gterminal，'+verdict('Gpaste')+'Gpaste。判断依据完整有符号SSE差，而非只看某一张图或某一区域。'
    if delta['Gguide-G0']>0:
        interpretation='本轮多步引导的主MSE高于原基线，因此不能报告总体改善。即使它相对其他融合方式有较低误差，也只是在这些干预之间作有限比较；原基线更好的事实必须保留。'
        negative='直接说“这一固定设置下，多步融合未改善主像素指标，甚至高于原基线；我保留全部四目标和负结果，接下来先检查普通竞争解释。”不能把局部好看或胜过较差对照当成功。'
    elif delta['Gguide-G0']==0:
        interpretation='本轮Gguide与G0的完整主指标相等；不把对其他对照的差或图片印象改写成超越原生成。整数SSE相等只说明此汇总指标相等，不保证两组图逐像素相同。'
        negative='直接报主指标相等，继续保留逐目标差和图像变化；不把“改变了生成”偷换成“改善了生成”。'
    elif delta['Gguide-Gterminal']>=0:
        interpretation='Gguide主MSE低于G0，但未观察到超越末步融合对照的额外MSE收益。不能据此确认较早融合或多步传播具有额外价值，也不能宣称已经唯一解释了全部机制。'
        negative='如实说明相对原生成的收益和相对强对照的不足；保留Gterminal而不只展示较弱对照，不为保住多步方案补调参数。'
    else:
        interpretation='在这一固定已见设置中，Gguide主MSE低于G0与Gterminal。它仍不足以把收益唯一归因于引导时机：额外前49步干预及后续传播也增加了累计干预量，且原参考、单场景和组件变体限制仍在。相对Gpaste的方向以上表为准，不删掉不利对比。'
        negative='即使主指标有收益，也要同时讲所有对照与失败目标；当前没有未见场景验证，不能将一次描述性收益写成新方法成立。'
    denom_rows=[x for x in rows if x['arm']=='G0']
    timings={a:g['arms'][a]['elapsed_seconds'] for a in ARMS}
    time_rows=[row(('G0完整链',number(timings['G0']),'Gguide完整链',number(timings['Gguide']))),row(('Gpaste派生',number(timings['Gpaste']),'Gterminal派生',number(timings['Gterminal']))),row(('共同warp编码',number(g['warp_encode_seconds']),'科学进程总计',number(g['elapsed_seconds']))),row(('外层监督总计',number(s['elapsed_seconds']),'固定评分',number(c['elapsed_seconds'])))]
    float_diffs=[x['max_abs_difference'] for x in r['checks'] if 'max_abs_difference' in x]
    need(float_diffs,'actual consumption arithmetic checks required')
    score_errors=[x['abs_error'] for x in v['float_checks']];need(score_errors,'actual score floating checks required')
    values={
        'CUTOFF_SHORT':cutoff.strftime('%m-%d %H:%M 北京时间'),
        'CUTOFF_FULL':cutoff.strftime('%Y-%m-%d %H:%M:%S 北京时间'),
        'ACCEPTED_STATE':'真实四臂生成、完整固定评分和团队内不同作者消费/统计复核已完成，结果经root有限范围接受；本报告版面验收另行记录。',
        'MAIN_FINDING':esc(main_finding),
        'ARM_TABLE':'\n'.join(row((a,integer(summary[a]['full']['total_sse']),number(summary[a]['full']['equal_frame_mean_mse']))) for a in ARMS),
        'CONTRAST_TABLE':'\n'.join(row((esc(x['comparison']),integer(x['full_total_sse_difference']),number(x['full_mean_mse_difference']))) for x in contrasts),
        'RUN_INTERVAL':esc(timestamp(g['started_utc']).strftime('%Y-%m-%d %H:%M:%S')+' 至 '+timestamp(g['completed_utc']).strftime('%Y-%m-%d %H:%M:%S')+'（北京时间）。'),
        'COST_TABLE':'\n'.join(time_rows),
        'COST_NOTE':esc('监督采样进程树峰值 '+number(s['peak_tree_rss_bytes']/1024**3)+' GiB。消费复核 '+number(r['elapsed_seconds'])+' 秒，统计复核 '+number(v['elapsed_seconds'])+' 秒。各阶段是包含/重叠关系，不能把编码、臂耗时与进程总计再相加。耗时是本机实际动作，不是学生本人投入工时。'),
        'FRAME_TABLE':'\n'.join(row((esc(x['arm'])+'/'+str(x['target_id']),integer(x['full_sse']),mse(x,'full'),mse(x,'support'),mse(x,'hole'))) for x in rows),
        'DENOM_TABLE':'\n'.join(row((x['target_id'],integer(x['support_pixels']),integer(x['hole_pixels']),integer(x['support_channels']),integer(x['hole_channels']))) for x in denom_rows),
        'REVIEW_RESULT':esc('全部50步Gguide融合及真实末步/派生保存量核验通过，所记录浮点算术比较最大绝对差为 '+number(max(float_diffs))+'；保护位置按字节核。统计复核覆盖16行/48区域及全部对比，浮点展示相对精确分数的最大绝对差为 '+number(max(score_errors))+'。这两项差属于各自的计算核验量，不能跨单位当视觉精度。'),
        'IMAGE_IDENTITY':r'总览文件SHA256：\par\noindent\path{'+image['sha256']+r'}',
        'INTERPRETATION':esc(interpretation),
        'NEGATIVE_ANSWER':esc(negative),
        'EVIDENCE_NAV':'\n'.join(r'\noindent\path{'+path+r'}\par' for path in list(ROLES.values())+['scoring_01/FRAME_SCORES.csv','scoring_01/ARM_SUMMARY.json','scoring_01/CONTRASTS.json','visuals_01/IMAGE_INDEX.json'])}
    need(set(re.findall(r'@@([A-Z_]+)@@',template))==set(values),'all template fields known')
    for key,value in values.items():template=template.replace('@@'+key+'@@',value)
    need('@@' not in template,'unfilled template field')
    output=HERE/'build';output.mkdir(exist_ok=False)
    images=HERE/'images';images.mkdir(exist_ok=False)
    (images/'overview_4targets_6columns.png').write_bytes(png)
    tex=HERE/(NAME+'.tex');tex.write_text(template)
    for pass_id in (1,2):
        result=subprocess.run(['/opt/homebrew/bin/xelatex','-interaction=nonstopmode','-halt-on-error','-output-directory=build',tex.name],cwd=HERE,capture_output=True,timeout=120)
        (output/f'compile_{pass_id}.txt').write_bytes(result.stdout+result.stderr)
        need(result.returncode==0,'actual XeLaTeX compile failed')
    log=(output/(NAME+'.log')).read_text()
    need('Missing character' not in log and 'Overfull' not in log,'document missing glyph/overflow')
    from pypdf import PdfReader
    pdf=output/(NAME+'.pdf');reader=PdfReader(pdf)
    need(len(reader.pages)==4 and all(p.extract_text() for p in reader.pages),'exact4 nonempty result pages')
    qa=HERE/'qa';qa.mkdir(exist_ok=False)
    result=subprocess.run(['/opt/homebrew/bin/pdftoppm','-scale-to','1600','-png',str(pdf),str(qa/'page')],capture_output=True,timeout=120)
    need(result.returncode==0,'actual page rendering failed')
    renders=sorted(qa.glob('page-*.png'));need(len(renders)==4,'all4 actual page renders required')
    return dict(status='BUILT_PENDING_ALL_PAGE_VISUAL_QA_AND_ROOT_REPORT_ACCEPTANCE',pdf=dict(path=str(pdf),sha256=sha(pdf.read_bytes()),pages=4),tex=dict(path=str(tex),sha256=sha(tex.read_bytes())),renders=[dict(path=str(p),sha256=sha(p.read_bytes())) for p in renders],scientific_cutoff_utc=binding['scientific_cutoff_utc'],scientific_new_model_or_score_calls=0,images_copied=1,reads=READS)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--binding-sha256',required=True);args=parser.parse_args()
    receipt=HERE/'BUILD_RECEIPT.json';need(not receipt.exists(),'build receipt exists; preserve prior attempt')
    began=time.monotonic();report=dict(status='STARTED',started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),reads=READS)
    try:report.update(main(args.binding_sha256))
    except BaseException as exc:report.update(status='FAILED_DOCUMENT_BUILD_PRESERVED',error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc())
    finally:
        report.update(completed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-began)
        with receipt.open('x') as f:json.dump(report,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({'status':report['status']}))
    raise SystemExit(0 if report['status'].startswith('BUILT_') else 1)
