# C2 V9 实际终止独立核验

裁决：**失败／部分完成，完成 1/2 批；C2 与三场景队列仍未完成。** 这是终止与保留证据核验，不授予成功读回、评分、重试或新方法权限。

审查者 `/root/c2_v9_source_primary`；实际执行作者 `/root`。审查完成于 `2026-09-08T17:29:28.940647+00:00`。审查只读终态文本、源码、事件哈希链与文件身份/尺寸；没有读取 C2 图像或张量载荷正文，没有评分、运行模型或修改旧证据。

| 已核事实 | 直接证据 |
|---|---|
| 外层真实返回 1；非外部超时 | 外部回执 16:45:42.636402–17:08:45.362273Z，耗时 1382.7257715 秒；stdout/stderr 均为空且哈希相符 |
| 各层一致为失败 | parent/worker 均 `FAILED_OR_PARTIAL_C2_BASELINE_RUN`；watchdog 转达 worker return 1；commit 为 `FAILED_OR_PARTIAL_ATTEMPT`、`standalone_success=false`，绑定的各回执 SHA 全部重核一致 |
| 第一批完成，第二批未采样 | 167 条完整 trace 事件哈希链；仅 batch_1、50 次 denoiser_call、1 次 sample_call/return；seq 164 于 17:08:43.322423Z 完成第一批，保留 frame IDs 1–4，cache history=5；seq 166 session_end 记 1 批 |
| 失败位置明确 | `turn_right → get_context_info → pipeline.py:711 → sorted_frames[0]` 抛出 `IndexError: list index out of range`。archive seq 62 于 17:08:44.732393Z 记录此次 retrieval_output 为 `([], [])`；源码 655–675 行从空 frame_count 导出空候选，711 行无空列表处理 |
| 部分档案保留 | archive 为 `ARCHIVE_PARTIAL`，67 条事件链核对成功，32 项捕获完成、0 捕获自身失败；11 个必需事件名计数不足，integration_return=0。3122 个列明文件均为普通文件且尺寸相符；其载荷哈希未重算，像素未解码 |
| 固定后备失败文件不存在 | `.execution_01.supervisor_failure.json`、`.execution_01.watchdog_failure.json` 均实际 lexists=false；这不覆盖非零返回和显式失败状态 |
| 登记进程已退出 | watchdog 记录 5 个 PID/create-time 身份全部消失、无需额外 cleanup action；17:29:28.929851Z 独立 ps 核 20689、20692、20693、20778、20781、20782、21071，返回 1 且输出空。只覆盖这些已登记身份 |
| 来源与目录身份一致 | manifest/trace/archive 的同一 219 项来源全部实际重算 SHA 相符；冻结 8 文件 SHA 与 0444 相符；ticket、parent、worker、watchdog、commit 所录 execution/output 目录身份与当前相符 |

`phase2_start_elapsed_seconds` 和 monitor 的 `budget_phase=2` 只表示第一批结束后预算进入下一阶段，不能写成“第二批采样已开始”。最后 monitor 于 17:08:45.303720Z 记录 completed_batches=1、RSS=0；此前最大采样 RSS 为 24,526,733,312 字节，未见外部超时或 watchdog 丢失监督存活信号。更晚写入的 17:11“仍运行”叙述不能覆盖真实 17:08:45 返回；root 负责追加更正，本审查不改主账。

当前仅识别到上下文选择的运行时失败。空检索的更深原因、C2 图像质量、画面相机服从和收益均未评价；5 个 PNG 的文件存在不能替代完整九帧读回。没有新重试授权。

机器可读完整证据：[TERMINAL_FAILURE_AUDIT.json](TERMINAL_FAILURE_AUDIT.json)，SHA-256 `118f2881f954ec2386a8d7bc54b91cd653908a1756d29078bd90f84f1235e74f`。

主要原件 SHA-256：

- 外部 receipt：`a0bd17374bca88edea96f21db5244cbc14fac5b9431f0cfcf6ed198e2feff149`
- parent receipt：`ab3ab2763527649d57c5bb7cc0b2697859cb7fb634f8148a3a9a12ef213d8719`
- worker receipt：`5ff82185bd0b534c265dd980133d9174f36f3e8e487ccf6db368b205889faec8`
- supervisor commit：`7266dadfcab500e6ab8d6043e33ca93fa42f59f84644d4a3a6955f812be11f9e`
- watchdog receipt：`df911eb573638aa9cc8563d52f915d9819ea2e88bbaf1816c1d500e2366edf8a`
- trace events：`bbddc730d521cebe16beaf7f990935ada45b2d7197e80e8152f1e15f380566d8`
- archive manifest：`7cfd56b59924fb3c603a3eb54c34f387db8439c72fc4a6fe08e3097dcf659b4c`
- archive events：`b51b39e1772a7a2cbc0221bc0846d95cd3b7c8b21f8978ddbbd0f1d2443f6ef7`
