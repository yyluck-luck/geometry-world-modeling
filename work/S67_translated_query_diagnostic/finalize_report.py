"""Record the completed S67 diagnosis without rerunning scientific work."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import sys

R = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
D = R / 'work/S67_translated_query_diagnostic'
now = datetime.now(timezone.utc)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
expected = {
    'diagnose.py': '4a6c2e5d6438346ed4a83743cef4ca462b9bc7cf44c0c6b6d2a186ee37d5b4bc',
    'PROTOCOL.md': 'bd2fbab02c1b4ee40f3e0cd083e6acb9d0789d832c62a82b50eff1c2a11a6c36',
    'SOURCE_REVIEW.json': 'ef6e0760ff2f7262883846a88be67529e123f988d27d5f3518d08cf7a353e7b3',
    'external_01/receipt.json': '0901737bb4009166b5975578fe5ddc436e0ff7335c94eabf5d45d9ead5b17131',
    'execution_01/receipt.json': '5ec04455ba9155913882155d36fd64b7e32c8022c8959e14bc6a5023f1d29f70',
    'INDEPENDENT_RESULT_REVIEW.json': '94459144d6df8194f3b5ff13269f2ff4b435ccf74936e5e28f220ddcbd693fed',
    'INDEPENDENT_RESULT_REVIEW.md': 'd5993b45b2102e2147bf9a1872abc3d4066feb90cf5262def42eb7e3acffaf8f',
    'figures/manifest.json': '2ed62f2c1fd9f36d48dc405697c1e7c436f63e42348a38c543eb237988ab4187',
    'NEAREST_WORK_BOUNDARY.md': '18cc7192ff432ec5895e5fbbfa4f6701ecbb9e8a97c3abe3b9ff54d4dde32b41',
}
for rel, value in expected.items():
    assert sha(D / rel) == value, rel
review = json.loads((D/'INDEPENDENT_RESULT_REVIEW.json').read_text())
assert review['status'] == 'PASS_S67_BOUNDED_INDEPENDENT_RESULT_REVIEW'
assert review['blockers'] == []
assert all(v['exact_array_bytes_equal'] for v in review['A_B_context_comparison'].values())
worker = json.loads((D/'execution_01/receipt.json').read_text())
assert worker['status'] == 'COMPLETE_FIXED_PAIR_DIAGNOSTIC'
assert worker['model_calls'] == worker['RGB_body_reads'] == worker['get_cond_calls'] == 0
manifest = json.loads((D/'figures/manifest.json').read_text())
for rel, value in manifest['outputs'].items():
    assert sha(D/'figures'/rel) == value, rel
acceptance = {
    'recorded_utc': now.isoformat(),
    'status': 'ACCEPTED_BOUNDED_S67_RESULT_AFTER_INDEPENDENT_REVIEW',
    'review_finalized_utc': review['finalized_utc'],
    'source_author_role': review['source_author_role'],
    'reviewer_role': review['reviewer_role'],
    'evidence_sha256': expected,
    'review_scope': 'Team different-author numerical validation; not external independent model reproduction.',
    'root_acceptance_scope': 'Read frozen result review and verify final source/protocol/review/receipt/figure identities. Earlier root direct context comparison remains in ROOT_ACTUAL_RESULT_OBSERVATION.json. No new scientific run.',
    'conclusion': review['conclusion'],
    'new_method_validated': False,
    'novelty_authorization': 'NONE',
    'next_step': 'Find an available real translated-reference witness and freeze matched ordinary baselines before selecting a method. No further generation for this unchanged selected-ID path.',
}
with (D/'ROOT_FINAL_RESULT_ACCEPTANCE.json').open('x') as f:
    json.dump(acceptance, f, ensure_ascii=False, indent=2)
    f.write('\n')

report = f'''# 深度变化能否改变记忆选择：一次实际诊断的结果

记录UTC：{now.isoformat()}；北京时间：{now.astimezone(timezone(timedelta(hours=8))).isoformat()}。

**本轮得到一个有限的负结果：投影位置最多变化约58像素，但最终选中的四张历史帧及其全部返回缓存仍完全相同。** 不同作者已经独立复算通过。它帮助我们排除这个具体案例中的“改变深度便能通过选图改变后续条件”的解释；目前没有得到新方法收益。

可以把实验理解为：把记忆里的物体沿原视线移近或移远，再让同一台虚拟相机向旁边移动一点。我们检查这种深度差异是否会让系统改选参考照片。A使用保存的原几何，B使用预先固定的人为深度变化，两组采用完全相同的新查询相机、历史缓存和选择程序。这里只比较系统如何反应，尚不知道A或B哪一种更接近真实世界。

这是真实执行的保存数据数值实验，使用已有5个来源、515个点；不是新采集数据，也没有重新生成视频。人为改深度和虚拟平移属于实验干预，不是已经观察到的自然失败。原诊断北京时间07:59:29.452768–07:59:34.517464实际运行，外部返回0，用时5.064598秒，两组各执行一次原渲染、检索和缓存返回程序。实际读取1496份数值文件、1,631,256字节；没有读取RGB正文或调用生成模型。

| 检查内容 | 实际结果 | 能说明什么 |
|---|---|---|
| 五个历史相机下的点投影 | 最大差3.33×10⁻¹⁶，原生K坐标；预定容差10⁻¹⁰ | 对这些点，历史纯旋转投影不能区分这两种深度；不保证遮挡、法线或整图等价 |
| 同一个平移查询下的投影 | 最大位移57.9713像素，中位7.5179像素；514/515点超过10⁻⁶像素 | 本次干预确实改变了新视角中的投影 |
| 五个来源的检索权重 | 权重绝对差之和0.0268168 | 中间权重有变化 |
| 参与来源和分配数量 | 两组均为来源0–4，每个来源配额1 | 在本例中没有改变来源成员或配额 |
| 最终有序记忆ID | 两组均为[0,2,4,1] | 最终选图不变 |
| 返回给后续程序的缓存 | 相机、latent、语义embedding、标定及ID五个数组字段逐字节相同；每组348592字节 | 此次选择路径返回的条件不变；没有测量新视频效果 |

![全部515点与5个来源的诊断图]({D}/figures/S67_projection_changes_context_unchanged.png)

图左包含全部515个点，图右包含全部5个来源，没有按结果挑点或挑来源。515个点不是515个独立场景。可编辑的[SVG图]({D}/figures/S67_projection_changes_context_unchanged.svg)与[图片清单]({D}/figures/manifest.json)一并保留。

独立复算由源码作者以外的agent完成：北京时间08:05:49.470835–08:05:49.925290，实际一次返回0，08:07:20.960364封存。采用另一套矩阵求逆与投影算术，实际解包比较缓存，并与原来源缓存逐项对应。历史投影残差与作者的末位差至多1.11×10⁻¹⁶，未改原容差；不能说S67所有数学位级完全一致。核验实际读取1052个科学文件、1,218,136文件字节，没有重新执行原renderer/NMS或模型，也没有重读全部1496份原输入。完整范围见[独立复核报告](<{D}/INDEPENDENT_RESULT_REVIEW.md>)。

创新判断也经过原文对照：[WorldStereo](https://arxiv.org/html/2603.02049v1)已有基于3D视野重叠的参考选择和空间条件；[Coverage Optimization for Camera View Selection](https://arxiv.org/html/2604.05259v1)研究相机覆盖与信息增益，但其固定几何下的属性回归信息量不能直接当作深度正确性的后验。这两项原文使普通“几何选图”或“信息增益”不足以独立构成我们的创新。此次读取的是方法、有关实验与限制，不宣称所有论文或外链已读完；详见[近邻与适用边界](<{D}/NEAREST_WORK_BOUNDARY.md>)。

**下一步先补一个能够判断对错的真实参考。** 查已有真实RGB-D序列中的平移相机、时间同步和标定，确认能否留下独立参考帧，同时设置相同候选数量和计算预算的普通相机距离/视野选择基线。先冻结新的窄问题与参考误差边界，再执行。旧TUM单RGB流不满足原RAIMA的三同步参考合同，新实验若使用它，只能另立更窄的发现性问题，不能宣称旧合同通过。若没有独立的几何或图像答案，仅有投影、权重或ID变化仍不够判断帮助还是损害。

本例不再追加视频生成，也不按看到的结果调整位移或深度重新试到选图改变。当前仍为NO_METHOD_SELECTED、new_method_validated=false、novelty_authorization=NONE；不能说已经达到PhD或CCF A方法贡献。前一阶段真实生成及其评分另见[客厅九帧结果](<{R}/docs/S66_FIXED_SCORE_AND_VISUAL_RESULT.md>)：8张模型输出加1张输入，共9张，不能把模型图称为实拍照片。

本轮实际应用Supervisor的vibe-research-workflow小步执行和不同作者复核、handbook2.3隐藏假设审查、idea-evaluator的可验证性/先有问题再选方案两项筛查、本地Claude科学批判skill，以及figure-designer的全数据实验图规范。没有调用Claude模型。S65已有Gemini咨询，本轮没有为这项已固定的诊断重复咨询。绘图第一次因现有解释器缺Matplotlib在导入阶段失败，已保存回执；随后使用另一现有绘图环境成功导出，未安装依赖或改变实验环境。

可追溯证据：[结果前协议](<{D}/PROTOCOL.md>)、[结果前不同作者源审](<{D}/SOURCE_REVIEW.md>)、[实际外部回执](<{D}/external_01/receipt.json>)、[实际数值回执](<{D}/execution_01/receipt.json>)、[最终接受记录](<{D}/ROOT_FINAL_RESULT_ACCEPTANCE.json>)、[完整时间主账](<{R}/RESEARCH_LOG.md>)。所有旧失败、旧协议及评分保持原样。
'''
# Local Markdown destinations with spaces must be enclosed in angle brackets.
report = report.replace(']('+str(R), '](<'+str(R))
lines = []
for line in report.splitlines():
    if ']('+str(R) in line:
        raise AssertionError('Unwrapped local Markdown destination')
    if '](<'+str(R) in line:
        import re
        line = re.sub(r'\]\(<(/Users/[^<>]*?)\)', r'](<\1>)', line)
    lines.append(line)
with (R/'docs/S67_TRANSLATED_QUERY_RESULT.md').open('x') as f:
    f.write('\n'.join(lines)+'\n')

current = R/'work/resumption_20260909/CURRENT_STATUS.md'
old = current.read_text()
with (D/'CURRENT_STATUS_BEFORE_S67_COMPLETION.md').open('x') as f:
    f.write(old)
paras = old.split('\n\n')
assert paras[0].startswith('**最新完成') and paras[1].startswith('**当前下一步')
paras[0] = f'**最新完成：S67固定平移查询诊断及不同作者独立复算已通过。** 新查询投影最大变57.9713像素、中位7.5179像素；两组最终ID均[0,2,4,1]，四类context及ID全部字节相同。实际只运行一次固定配对CPU诊断5.064598秒，0新模型/RGB。这是人为深度干预下的有限选图不变结果，不是新方法收益。见[最新中文报告](<{R}/docs/S67_TRANSLATED_QUERY_RESULT.md>)。S64/S66真实8帧输出+输入、固定评分和全九帧查看亦已完成，主MSE=0.0006382446123931144、PSNR=31.950128425132405dB、预定MSE>0.01为false；见[客厅报告](<{R}/docs/S66_FIXED_SCORE_AND_VISUAL_RESULT.md>)。'
paras[1] = '**当前下一步：从已存在数据确认一个真实平移相机与独立参考的最小见证，再冻结匹配的普通相机/视野选择基线。** S67本固定案例的所选ID路径解释已被否决，不再为它生成视频或按结果调参重跑。两种深度哪种正确、选图是否有益仍无标签。只读数据可行性审查正在进行，完成后见work/S67_translated_query_diagnostic/NEXT_REAL_REFERENCE_FEASIBILITY.md；文件存在不等于后续实验已运行。旧TUM单流不满足旧RAIMA三同步参考合同；另立窄问题需明示参考误差，不复活旧方法。不要重跑已成功的S60–S67。'
new = '\n\n'.join(paras)
old_row = next(x for x in new.splitlines() if x.startswith('| S67问题与资源 |'))
new_row = '| S67实际完成与边界 | 2026-09-08T23:59:29.452768–23:59:34.517464Z实际return0；1496数值blob1631256B，两臂同rawquery/缓存，历史投影最大差3.33e-16原生K坐标，新query514/515点变化>1e-6px。权重L1=0.02681681069040924，5来源/配额1/ID[0,2,4,1]不变；5字段每臂348592B全字节相同。不同作者独立算术00:05:49Z一次return0，00:07:20.960364Z最终PASS；未重跑renderer/模型。仅NO_SELECTED_ID_OR_RETURNED_CONTEXT_EFFECT_IN_THIS_FIXED_CASE。 |'
new = new.replace(old_row, new_row)
new = new.replace('本轮S66只复用这些仍适用的原文与数学，没有凑数重复咨询/检索。', 'S66复用这些仍适用的原文与数学；S67另实际检索WorldStereo和Coverage Optimization for Camera View Selection方法/相关实验/限制，root核原文，未重复Gemini咨询。')
start = new.index('每项实际开始、完成、失败、修订经')
end = new.index('\n\n', start)
new = new[:start] + f'每项实际开始、完成、失败、修订经scripts/research_log.py追加到[主账](<{R}/RESEARCH_LOG.md>)。最新流程实查2026-09-09T00:07:59.573059Z，实际间隔30.648497分钟；下一次到00:37:59.573059Z后执行。此前提前调用被拒及实际延迟均保留，不倒填准点。应用自动任务本轮实际读取为ACTIVE/30分钟，计划不等于历史准点；旧检查器S40原始pending字段属历史，不覆盖已完成S64/S66/S67。模型已退出，本轮无新模型；诊断及独立复算也已退出。' + new[end:]
new = new.replace('最新正在写的S67源码不等于已有实验结果，最终交付后才消费作者/审查文件。', 'S67作者源码、不同作者源审、实际结果和独立复核已依序完成；不要把早期“源码准备中”或“待复核”历史当成最新状态。')
current.write_text(new)
with (R/'docs/INNOVATION_GUIDANCE_CURRENT.md').open('a') as f:
    f.write(f'\n\n## {now.isoformat()}：S67固定案例收束\n\n本次真实CPU离线干预与不同作者独立复算确认：新query投影最大变化57.9713像素，检索权重变化，但最终[0,2,4,1]和四类返回context/ID字节相同。只否决本固定案例selected-ID路径解释，不推广为几何普遍无用，也不为该不变路径追加视频。WorldStereo已有3D-FoV参考选择；Coverage Optimization的信息增益建立在属性回归等假设上，不能未经验证用于深度正确性。先查实际可得的平移参考和普通匹配基线，再决定新机制。未选择方法，novelty_authorization=NONE，new_method_validated=false。详见docs/S67_TRANSLATED_QUERY_RESULT.md及work/S67_translated_query_diagnostic/NEAREST_WORK_BOUNDARY.md。\n')

sys.path.insert(0, str(R/'scripts'))
from research_log import append_event
append_event('S67不同作者结果核验已接受并形成中文结论', '最终核验00:07:20.960364Z封存PASS。root核最终源码/协议/源审/回执/独立报告/图身份；接受本固定案例投影改变、最终ID与全部返回context不变的有限结论。实际实验和独立算术时间来自冻结回执，此时只写报告和同步决策，0新科学运行。', ['work/S67_translated_query_diagnostic/ROOT_FINAL_RESULT_ACCEPTANCE.json', 'docs/S67_TRANSLATED_QUERY_RESULT.md', 'work/S67_translated_query_diagnostic/INDEPENDENT_RESULT_REVIEW.json'], '交付报告/诊断图并完成真实平移参考的有限可行性审查；不为本例不变选图路径增加视频。')
print(json.dumps({'recorded_utc': now.isoformat(), 'report_sha256': sha(R/'docs/S67_TRANSLATED_QUERY_RESULT.md'), 'acceptance_sha256': sha(D/'ROOT_FINAL_RESULT_ACCEPTANCE.json')}, ensure_ascii=False))
