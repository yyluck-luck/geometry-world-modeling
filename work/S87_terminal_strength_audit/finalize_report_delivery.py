"""Finish S87 report delivery; no scientific arrays or model calls."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, sys

R = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
S = R/'work/S87_terminal_strength_audit'
B = Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/导师汇报_深入讲解第二版_2026-09-10')
P = B/'S87_09月11日末端反证与详细讲解'
C = S/'result_report/continuous'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def writej(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2)+'\n')
def copy_checked(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists(): assert sha(src)==sha(dst), str(dst)
    else: shutil.copy2(src,dst)
    assert sha(src)==sha(dst)
    return dict(source=str(src),destination=str(dst),sha256=sha(dst),bytes=dst.stat().st_size)

if __name__=='__main__':
    now=datetime.now(timezone.utc).isoformat()
    review=json.loads((C/'MERGE_REVIEW.json').read_text())
    for entry in review['source_files']:
        assert sha(Path(entry['path']))==entry['sha256']
    source=C/'完整汇报_含S87实际结果_168页.pdf'
    assert sha(source)==review['merged_pdf_sha256']
    assert review['merged_pages']==168 and not review['differing_pages'] and not review['text_empty_pages']
    assert all(review[k] for k in ['all_168_text_and_dimensions_equal','all_168_decoded_graphics_content_equal','four_new_key_pages_exact_pixels'])
    content=json.loads((S/'result_report/ROOT_REPORT_ACCEPTANCE.json').read_text())
    assert content['accepted'] and content['root_visual_pages_seen']==list(range(1,13))
    acceptance=dict(accepted=True,accepted_utc=now,pdf_sha256=sha(source),pages=168,
        merge_review_sha256=sha(C/'MERGE_REVIEW.json'),author_visual_review_sha256=sha(C/'AUTHOR_VISUAL_REVIEW.json'),
        source_report_acceptance_sha256=sha(S/'result_report/ROOT_REPORT_ACCEPTANCE.json'),
        checks='All168 source text, dimensions and decoded content equal; four new rendered source/merged pairs exact pixels; all12 source pages viewed by root; merged157 additionally viewed by root.',
        limit='No fresh visual reinspection of all historical156 pages; historical acceptances and source preservation retained. Document acceptance is not new method validation.',new_model_runs=0)
    assert not (C/'ROOT_MERGE_ACCEPTANCE.json').exists()
    writej(C/'ROOT_MERGE_ACCEPTANCE.json',acceptance)
    merged=B/'最新连续阅读版'/source.name
    copied=[copy_checked(source,merged)]
    for name in ['MERGE_REVIEW.json','MERGE_REVIEW.md','MERGE_INPUTS.json','AUTHOR_VISUAL_REVIEW.json','ROOT_MERGE_ACCEPTANCE.json','merge_and_verify.py']:
        copied.append(copy_checked(C/name,P/'文稿验收/continuous'/name))
    writej(S/'MERGED_PDF_COPY_READBACK.json',dict(completed_utc=now,files=copied,mismatches=[]))

    heading=f'''## 最新阅读入口：S87实际对照已完成，168页连续汇报（UTC {now}）

[完整168页汇报](<{merged}>)；[新增12页详细讲解](<{P/'S87_有限末端对照_实际结果与零基础讲解.pdf'}>)；[全部新数据、图片与证据](<{P/'00_从这里开始.md'}>)。

先看阅读器物理第157–168页了解S87，第143–156页了解投影原理与S86四臂；原第1–142页及原224页逐条主账均保留。历史页中的“待运行”按其截点理解，本段优先。

本轮确实进行了3次VAE全8槽解码和3组RGB处理，产生24条新目标记录，旧16条只引用。普通末步0.75全图四帧MSE 0.05116758，低于旧多步0.05242222，否定“这个分数非多步不可”的解释；目标22更差，画面仍有重影，尚无验证的新方法。53.74秒为复用缓存后的本轮派生时间，不是整个系统速度。

新增12页全部经过内容与视觉核验；合并168页逐页文字、尺寸和绘制内容与原稿一致，4组新页源/合并图像逐像素相同，未重新视觉检查全部历史156页。下一步核独立场景的同步视角与可靠几何参考，不继续本例强度细扫。

以下旧入口按日期保留。

---

'''
    backups=S/'before_final_delivery_sync';backups.mkdir(exist_ok=True)
    for i,p in enumerate([B/'00_从这里开始.md',B/'最新连续阅读版/00_先读这里.md']):
        shutil.copy2(p,backups/f'navigation_{i}.md')
        p.write_text(heading+p.read_text())
    pp=P/'00_从这里开始.md';shutil.copy2(pp,backups/'packet_readme.md')
    text=pp.read_text().replace('先读本目录12页PDF。它将在同级“最新连续阅读版”合入168页文件，最新是否完成以最终交付索引为准。',f'本目录12页PDF已通过全部页面和内容核验，并已合入[完整168页汇报](<{merged}>)，新增部分在PDF阅读器物理157–168页。原156页完整保留。最终文件身份与补充交接见FINAL_DELIVERY_INDEX.json。')
    pp.write_text(text)

    marker1='<!-- S87_CURRENT_BEGIN -->';marker2='<!-- S87_CURRENT_END -->'
    files=[R/'RESEARCH_MEMORY.md',R/'docs/RESEARCH_HANDOFF_CURRENT.md',R/'docs/PROPOSAL_PROGRESS_CURRENT.md',R/'docs/PROJECT_DELIVERY_TRACKER.md',S/'CONTINUE_HERE.md']
    for p in files:
        t=p.read_text();a=t.index(marker1);z=t.index(marker2)+len(marker2)
        block=t[a:z]
        block=block.replace('报告排版核验中','12页新报告及168页连续版已核验交付')
        first=block.index('报告同步：');end=block.index('\n\n最新七项检查',first)
        block=block[:first]+f'''报告同步（实际交付更新UTC {now}）：新增12页LaTeX已本机双遍编译；root实看全部12页，不同作者核24行/公式/成本和边界通过，无溢出/缺字警告。与原156页合成168页，逐页文字/尺寸/绘制内容等源、4关键页源/合并渲染像素一致，root接受，已复制回读SHA一致。连续入口：{merged}；全部数据/PNG/源LaTeX/证据：{P}。旧156页及各历史截点不改。完整交付以FINAL_DELIVERY_INDEX及其清单为准。

下一科研任务：NEXT_SCIENTIFIC_DECISION.md已核旧S73/S74/S77/S80/S81正负控制实际存在，不重复验证。PointOdyssey官方3个元数据请求暂未定位可单独获取的同刻多视角片段；最小HF数据包3,324,284,510字节，未下载，具体同步索引、场景独立性和数据许可冲突未核清。下一批只有限访问已观察到的官方入口，不启动新生成。真实传感器参照与模拟器真值分开。''' +block[end:]
        shutil.copy2(p,backups/(p.name+'.before_final'))
        t=t[:a]+block+t[z:]
        if p==S/'CONTINUE_HERE.md':
            t=t.replace('当前：完成报告全部页面/内容核验、与156页合并和用户快照；','当前：报告全部页面/内容核验、168页合并及用户资料复制已完成；')
        p.write_text(t)
    sys.path.insert(0,str(R))
    from scripts.research_log import append_event
    append_event('S87报告与168页合并正式验收并复制','新增12页全部视觉/内容通过；168页内容等源、4源/合并渲染像素一致；复制SHA一致。24条新记录和16条旧引用分开，0新增科学运行；root实际复看合并157页。创新/审查/报告三子岗继续有限批次。',
      evidence=[str(C/'ROOT_MERGE_ACCEPTANCE.json'),str(S/'MERGED_PDF_COPY_READBACK.json'),str(merged)],next_step='完成三岗补充审查与最终快照；科研转向独立场景的小片段和可信参考访问核查，停止本例强度细扫。',occurred_at=now,event_id='S87-report-merge-delivery')
    print(json.dumps(dict(time=now,merged_pdf=str(merged),sha256=sha(merged),copied_files=len(copied),new_science_runs=0),ensure_ascii=False))
