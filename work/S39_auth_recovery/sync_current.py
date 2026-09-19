from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, re, sys
R=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
W=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
H=R/'work/S39_auth_recovery'
now=datetime.now(timezone.utc); utc=now.isoformat()
current=[Path(x['path']) for x in json.loads((R/'work/S38_paper_learning/completion.json').read_text())['current_files'] if not x['path'].endswith('RESEARCH_PRINCIPLES.md')]
backup=H/'current_before_update'/now.strftime('%Y%m%dT%H%M%SZ'); backup.mkdir(parents=True,exist_ok=False)
for i,p in enumerate(current):
 (backup/f'{i:02d}_{p.name}').write_bytes(p.read_bytes())
summary=f'''更新UTC：{utc}。**S39官方设备认证已成功；用户亲自完成网页授权。ft-mse图像解码器的配置与权重均已完整下载并通过SHA校验。原VMem和CLIP尚未确认完整；当前没有新增模型或视频生成实验。**

原VMem第一次Xet真实传输后因重复TLS握手错误终止；官方普通HTTP第二次尝试也已明确失败，当前排查具体传输环节，不能把它们写为仍在运行。CLIP另一个下载会话36631仍存活，须接手先查其实际结果，不重复启动。旧S38的CLI401仅为历史，现在认证已解决。

独立源码审查已通过单独的“VMem + stabilityai/sd-vae-ft-mse”组件版本，并修正不完整权重加载可能被内部捕获的问题。它还不是已加载模型；原SD2.1 VAE身份仍UNKNOWN，因此不能称精确原版复现。下一步完成余下权重校验，绑定真实文件与审查回执，再尝试有时间/内存上限的真实加载。之后才是两批视频闭环、自然失败分析和方法实验。

研究仍遵循Supervisor 02_Idea_Generation的强基线→失败→原因→方法顺序；S38两agent的8篇论文学习与Gemini两轮核验已完成。保留“正确选图后CLIP平均是否损失回访细节”的待检验问题，普通加权不算创新。PhD/CCF A质量目标尚未达到。

[本轮实际记录](<{R}/docs/S39_AUTH_AND_COMPONENT_LOADING.md>)；[模型访问现状](<{R}/docs/MODEL_ACCESS_CURRENT.md>)；[主记忆](<{R}/RESEARCH_MEMORY.md>)；[全部时间记录](<{R}/RESEARCH_LOG.md>)。旧封存结果保持，下面历史状态不覆盖此最新更新。
'''
report=f'''# S39：正式认证恢复与真实组件准备

更新UTC：{utc}；本报告按新增证据继续更新，未宣称阶段全部结束。

## 已发生的事情

1. 官方HF CLI1.30.0隔离安装到work/S39_auth_recovery/cli-env，原科学Python和包版本不改。默认连接曾TLS失败，使用本机已存在代理的进程环境后正式device flow成功。用户本人在官网完成批准，CLI返回成功；无凭据内容进入项目记录。
2. 原VMem固定revision ac5921080a57f5a634f4b9acbbc8f3db67c9d113，预期5056346672字节/SHA675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4。attempt1从03:49:37至04:03:07实际传输，Xet日志重复TLS EOF，根发送SIGINT后exit1。原会话67487已终止，不再轮询。网络计数不是已验文件进度。
3. 官方HF_HUB_DISABLE_XET=1普通HTTP attempt2实际04:08:08.102843–04:08:09.829835UTC，exit1，代理TLS连接EOF，会话52760已终止。两次日志/回执分开保留。
4. 具名ft-mse配置在03:58:27完成；334643276字节权重在04:05:41.623194下载完成，04:05:41.753737全文件SHA匹配a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815。这是资源完成，不是模型推理。
5. CLIP固定revision 1c2b8495b28150b8a4922ee1c8edee224c284c0c，从04:05:41.754101开始，属于会话36631/PID72930；04:10:02仍运行，当时日志有1条TLS EOF警告，不能据此断言终止。目标3944517836字节、SHA0084e75319a50ad85ef45377bad5bc38f2f58824459eb690048d51c9f8863be5。
6. 原SD2.1新授权小探测两次ConnectError，没有HTTP结果。根另用成功认证CLI的同环境作一次原config获取，终态Repository not found，工具没有给出具体HTTP码。不据此认定永久删除；原件身份继续UNKNOWN。
7. S39单独声明VAE组件版本的加载代码v2已由不同作者审查PASS。它增加全部state_dict加载记录最终检查，缺失或多余键均拒绝，不改原数学；原S35及失败v1均保留。源审尚未绑定实际core，不能直接当执行批准。真实组件加载、VAE encode/decode、模型forward和完整视频均0次。

## 正在准备的下一步

完成VMem与CLIP原权重后，固定五组件、changi输入、配置与全部源码，生成不可变资源core，另一作者审查实际core后进入独立受控worker。加载限制CPU8、FP32、1800秒、45GiB、至少10GiB空闲；第一次只加载和核组件，不把成功加载叫生成成功。后续真实两批闭环仍需另立具名组件版本协议，不改S35精确原件门。

当前innovation问题来自S38：正确选图之后的CLIP平均是否削弱回访细节。尚无自然生成失败、机制增益或跨场景确认，不能宣布新算法成立。

## 可复现材料

- [认证真实回执](../work/S39_auth_recovery/auth_recovery_execution.json)
- [VMem首次下载终态](../work/S39_auth_recovery/vmem_download_receipt.json)
- [传输中断依据](../work/S39_auth_recovery/xet_transport_interruption.json)
- [HTTP第二次终态](../work/S39_auth_recovery/vmem_http_attempt2_receipt.json)
- [组件下载实际回执](../work/S39_auth_recovery/companion_download_receipt.json)
- [VAE新认证探测](../work/S39_auth_recovery/original_vae_authenticated_probe.json)
- [原VAE官方CLI返回](../work/S39_auth_recovery/original_vae_default_cli.log)
- [加载协议草稿](../work/S39_component_variant/PROTOCOL_DRAFT.md)
- [源码审查](../work/S39_component_variant/independent_review.md)
- [源码与未绑定core回执](../work/S39_component_variant/independent_review.json)

正常SDK读取自己的凭据缓存以访问已授权模型；没有读取浏览器cookie或导出认证值。成功下载后仍按原SHA验收，不关闭TLS验证。
'''
(R/'docs/S39_AUTH_AND_COMPONENT_LOADING.md').write_text(report)
for p in current:
 if p.name in ('START_HERE_CURRENT.md','最新科研进展.md'):
  p.write_text('# 最新科研进展\n\n'+summary)
 elif p.name=='RESEARCH_MEMORY.md':
  s=p.read_text(); s=re.sub(r'更新UTC：[^\n]+',f'更新UTC：{utc}；当前以S39段为准：正式认证成功、具名VAE完整校验，VMem传输仍待恢复、CLIP下载在运行；未新生成视频。',s,count=1)
  s=s.replace('## S38当前：论文方法学习、Gemini与原资源','## S38历史：论文方法学习、Gemini与原资源')
  marker='## S38历史：论文方法学习、Gemini与原资源'
  section='## S39当前：认证已恢复，资源与加载准备\n\n'+summary+'\n实际最近流程检查2026-09-07T03:59:36.922078+00:00，间隔27.835069分钟；下次目标04:26:36、截止04:29:36UTC。旧检查时刻不覆盖此条。\n\n'
  s=s.replace(marker,section+marker,1)
  s=s.replace('最新状态以本文件S38段为准','最新状态以本文件S39段为准')
  p.write_text(s)
 elif p.name=='MODEL_ACCESS_CURRENT.md':
  p.write_text('# 当前模型访问状态\n\n'+summary+'\n目标原VMem文件身份与各次终态、当前CLIP句柄、原VAE来源边界详见S39报告。认证已经成功，无需让用户重做网页同意。\n')
 else:
  s=p.read_text(); assert s.count('<!-- CURRENT_STATUS_BEGIN -->')==1
  s=re.sub(r'<!-- CURRENT_STATUS_BEGIN -->.*?<!-- CURRENT_STATUS_END -->','<!-- CURRENT_STATUS_BEGIN -->\n'+summary+'<!-- CURRENT_STATUS_END -->',s,count=1,flags=re.S)
  p.write_text(s)
receipt={'recorded_utc':utc,'status':'CURRENT_RECORDS_SYNCED_AUTH_SUCCESS_DOWNLOADS_IN_PROGRESS','backup':str(backup),'current_files':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in current], 'scientific_runs':0}
(H/'current_records_sync.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
sys.path.insert(0,str(R/'scripts')); from research_log import append_event
append_event('S39权重部分完成、真实传输失败与当前记录同步','ft-mse配置和334643276B权重已完整SHA验证。原VMem Xet实际传输后因重复TLS EOF终止，HTTP attempt2亦实际TLS失败；两句柄终止、两回执保留。CLIP会话36631仍运行。独立v2加载源审PASS但未绑定实际资源core，0新模型/视频。10份当前入口已备份并同步，旧401不再是当前认证状态。',evidence=['docs/S39_AUTH_AND_COMPONENT_LOADING.md','work/S39_auth_recovery/current_records_sync.json','work/S39_auth_recovery/companion_download_receipt.json','work/S39_component_variant/independent_review.json'],next_step='有界定位VMem传输环节；接续同一CLIP句柄，资源齐备后真实冻结与加载。',occurred_at=utc,time_source='current clock; earlier download times from retained execution receipts')
print(json.dumps({'utc':utc,'files':len(current),'backup':str(backup)}))
