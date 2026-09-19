# S39：正式认证恢复与真实组件准备

更新UTC：2026-09-07T04:11:35.212928+00:00；本报告按新增证据继续更新，未宣称阶段全部结束。

## 已发生的事情

1. 官方HF CLI1.30.0隔离安装到work/S39_auth_recovery/cli-env，原科学Python和包版本不改。默认连接曾TLS失败，使用本机已存在代理的进程环境后正式device flow成功。用户本人在官网完成批准，CLI返回成功；无凭据内容进入项目记录。
2. 原VMem固定revision ac5921080a57f5a634f4b9acbbc8f3db67c9d113，预期5056346672字节/SHA675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4。attempt1从03:49:37至04:03:07实际传输，Xet日志重复TLS EOF，根发送SIGINT后exit1。原会话67487已终止，不再轮询。网络计数不是已验文件进度。
3. 官方HF_HUB_DISABLE_XET=1普通HTTP attempt2实际04:08:08.102843–04:08:09.829835UTC，exit1，代理TLS连接EOF，会话52760已终止。两次日志/回执分开保留。
4. 具名ft-mse配置在03:58:27完成；334643276字节权重在04:05:41.623194下载完成，04:05:41.753737全文件SHA匹配a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815。这是资源完成，不是模型推理。
5. CLIP固定revision 1c2b8495b28150b8a4922ee1c8edee224c284c0c，从04:05:41.754101开始，属于会话36631/PID72930；04:10:02仍运行，当时日志有1条TLS EOF警告，不能据此断言终止。目标3944517836字节、SHA0084e75319a50ad85ef45377bad5bc38f2f58824459eb690048d51c9f8863be5。
6. 原SD2.1新授权小探测两次ConnectError，没有HTTP结果。根另用成功认证CLI的同环境作一次原config获取，终态Repository not found，工具没有给出具体HTTP码。不据此认定永久删除；原件身份继续UNKNOWN。
7. S39单独声明VAE组件版本的加载代码v2已由不同作者审查PASS。它增加全部state_dict加载记录最终检查，缺失或多余键均拒绝，不改原数学；原S35及失败v1均保留。源审尚未绑定实际core，不能直接当执行批准。真实组件加载、VAE encode/decode、模型forward和完整视频均0次。

## 本轮后续实际完成

- curl入口诊断04:13:40.801864–04:13:41.456307UTC，exit35、无目标HTTP状态、0正文；未取得签名URL，0次CDN Range。不能据此宣布整个网络或账号失败。[回执](../work/S39_auth_recovery/transport/curl_range_01/receipt.json)。
- 新freeze_manifest工具与协议完成，04:15:09.862158不同作者全文源审PASS；tool SHA e7c03af60ed4d50bd5a9a1fb40f12df360f390a7a7fce1fe6f907f74bd8fb6b1。[源码前审](../work/S39_component_variant/freeze_independent_source_review.json)。实际core仍不存在，不是已运行。
- 04:16:56.325573UTC，CLIP同一会话36631/PID72930仍运行，临时文件1140213633B；Xet累计1条TLS EOF，无新终态。后续须先查同一句柄，不重启。[实测落盘记录](../work/S39_auth_recovery/clip_disk_observations.jsonl)。
- 当前10入口首轮SHA/41链接已核。后续头部更新单独绑定进度交接；初始回执不回改。

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

## 后续传输设置已核来源，尚未执行

已装hf_xet1.6.0支持固定并发1和同时文件数1；每请求至多1次内部重试不能当整个文件的重试上限。等待当前CLIP终态后才单独尝试原VMem，外控总1800秒；低并发尚未证明解决TLS。旧range变量和MAX_DURATION总时限解释不采用。[官方与本机来源核验](../work/S39_auth_recovery/transport/xet_settings_review/report.md)。

## 04:43前后实际资源推进

资源最新更新UTC：2026-09-07T04:43:28.864722+00:00。**原CLIP已完整下载，3,944,517,836字节及完整SHA于04:40:51通过。旧会话36631已退出0。原VMem低并发attempt3已单独启动，会话71130/PID84800，04:42:22仍活跃；临时文件当时0字节且Xet有1条TLS EOF警告，未判成功或失败。** 接续同一71130，不重启；外控总时限预计05:11:16UTC，精确终态以新receipt为准。它成功后才能冻结全部文件并实际加载。


[CLIP完整校验回执](../work/S39_auth_recovery/companion_download_receipt.json)；[原VMem当前attempt3](../work/S39_auth_recovery/vmem_low_concurrency_attempt3/receipt.json)。仅完成资源与源码准备，无新模型/生成。
