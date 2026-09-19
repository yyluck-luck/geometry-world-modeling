from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,re,sys
R=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling'); H=R/'work/S39_auth_recovery'
now=datetime.now(timezone.utc).isoformat()
files=[Path(x['path']) for x in json.loads((H/'current_records_sync.json').read_text())['current_files']]
obs=json.loads((H/'clip_disk_observations.jsonl').read_text().splitlines()[-1])
extra=f'''最新接续UTC：{now}。CLIP会话36631在04:16:56工具检查仍运行，临时文件已实际写入1,140,213,633字节，未完成校验。冻结工具又经另一作者全文审查PASS；仍未执行prepare或加载。系统curl单次HF入口探测也TLS失败，未发CDN Range。下一轮先接续同一CLIP句柄，待其终态再独立恢复原VMem；不启动重复并行下载。详见[实际接续清单](<{H}/progress_handoff.json>)。\n\n'''
for p in files:
 s=p.read_text()
 if '<!-- CURRENT_STATUS_BEGIN -->' in s:
  s=s.replace('<!-- CURRENT_STATUS_BEGIN -->\n','<!-- CURRENT_STATUS_BEGIN -->\n'+extra,1)
 elif p.name=='RESEARCH_MEMORY.md':
  s=s.replace('## S39当前：认证已恢复，资源与加载准备\n\n','## S39当前：认证已恢复，资源与加载准备\n\n'+extra,1)
  s=re.sub(r'更新UTC：[^\n]+',f'更新UTC：{now}；S39认证已成功、具名VAE完整校验，CLIP实际下载运行，VMem两次传输失败已终止；未新增模型或视频实验。',s,count=1)
 else:
  parts=s.split('\n\n',1); s=parts[0]+'\n\n'+extra+parts[1]
 p.write_text(s)
report=R/'docs/S39_AUTH_AND_COMPONENT_LOADING.md'
s=report.read_text(); s=s.replace('## 正在准备的下一步',f'''## 本轮后续实际完成

- curl入口诊断04:13:40.801864–04:13:41.456307UTC，exit35、无目标HTTP状态、0正文；未取得签名URL，0次CDN Range。不能据此宣布整个网络或账号失败。[回执](../work/S39_auth_recovery/transport/curl_range_01/receipt.json)。
- 新freeze_manifest工具与协议完成，04:15:09.862158不同作者全文源审PASS；tool SHA e7c03af60ed4d50bd5a9a1fb40f12df360f390a7a7fce1fe6f907f74bd8fb6b1。[源码前审](../work/S39_component_variant/freeze_independent_source_review.json)。实际core仍不存在，不是已运行。
- 04:16:56.325573UTC，CLIP同一会话36631/PID72930仍运行，临时文件1140213633B；Xet累计1条TLS EOF，无新终态。后续须先查同一句柄，不重启。[实测落盘记录](../work/S39_auth_recovery/clip_disk_observations.jsonl)。
- 当前10入口首轮SHA/41链接已核。后续头部更新单独绑定进度交接；初始回执不回改。

## 正在准备的下一步''',1);report.write_text(s)
handoff={'recorded_utc':now,'goal_turn_classification':'progress','reason':'Official auth actually recovered; complete declared VAE downloaded and hashed; new independently reviewed loading/freeze implementation; original transmission failures diagnosed. No scientific result claimed.', 'goal_complete':False,'auth_status':'official device flow successful; user handled website approval; no further login question', 'live_processes':[{'session_id':36631,'pid':72930,'wrapper_pid':70729,'role':'official CLIP download, sequential companion script','script':str(H/'download_companions.py'),'receipt':str(H/'companion_download_receipt.json'),'last_verified_utc':obs['observed_utc'],'partial_bytes':1140213633,'resume':'write_stdin session36631; inspect receipt if terminal; do not restart while live'}], 'terminal_sessions':{'67487':'VMem Xet SIGINT after 12 TLS EOF; exit1 04:03:07UTC','52760':'VMem HTTP fallback TLS EOF exit1 04:08:09UTC','54601':'Original SD2.1 config CLI returned Repository not found; exact HTTP code not exposed'}, 'components':{'vmem':'NOT_COMPLETE','clip':'LIVE_DOWNLOAD_NOT_COMPLETE','cut3r':'previously verified unchanged; recheck runtime','declared_vae_config':'COMPLETE_SHA_MATCH','declared_vae_weight':'COMPLETE_SHA_MATCH','original_sd21_vae_identity':'UNKNOWN'}, 'executions':{'new_model_loads':0,'new_model_forwards':0,'generation_batches':0,'freeze_prepare_calls':0,'freeze_attach_calls':0}, 'next_steps':['Resume same CLIP process and record terminal/full SHA, keep failures.','After current large transfer ends, one separately recorded low-concurrency original VMem attempt if official parameter support verified; no claim it will fix TLS.','Once all five files complete, reviewed freeze_manifest prepare with original changi and source domain; actual core must be reviewed by two real authors.','Attach those exact core-bound receipts and run bounded declared-component loading once, then independently inspect real receipts.','Continue original-proposal real two-batch generation under explicitly declared VAE variant; exact original baseline identity still unresolved.'], 'workflow_check':{'last_checked_utc':'2026-09-07T03:59:36.922078+00:00','next_target_utc':'2026-09-07T04:26:36.922078+00:00','deadline_utc':'2026-09-07T04:29:36.922078+00:00'}, 'unchanged_scientific_environment':True,'source_review_is_not_runtime_review':True,'report':str(report),'current_files':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
(H/'progress_handoff.json').write_text(json.dumps(handoff,ensure_ascii=False,indent=2)+'\n')
sys.path.insert(0,str(R/'scripts'));from research_log import append_event
append_event('S39实质进展交接：认证与VAE完成，CLIP同一句柄继续','当前goal turn为progress，不是完全blocked：正式认证恢复、具名VAE完整校验、加载v2及冻结工具由不同作者源码审查通过。CLIP04:16:56仍实际运行且已写1140213633B临时文件；不是完成。原VMem两次实际失败及curl探测保留；下轮先接续CLIP，避免并发重启。尚无新模型加载或生成，整体目标不完成。',evidence=['work/S39_auth_recovery/progress_handoff.json','work/S39_component_variant/freeze_independent_source_review.json','docs/S39_AUTH_AND_COMPONENT_LOADING.md'],next_step='保持当前下载与真实句柄；完成原组件后按实际清单审查进入加载，不重跑成功阶段。',occurred_at=now)
print(json.dumps({'recorded_utc':now,'live_session':36631,'current_files':len(files),'goal_complete':False}))
