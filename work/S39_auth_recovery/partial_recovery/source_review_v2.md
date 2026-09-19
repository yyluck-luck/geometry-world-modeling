# 原VMem片段恢复：独立源码审查 v2

结论：**静态源码通过，未执行恢复。** 审查者 `/root/research_novelty_routes` 与作者 `/root/s14_feature_extractor` 不同。实际审查 2026-09-07T04:55:29Z 至 2026-09-07T04:58:43.712309+00:00。

绑定源码 `65b72714d0b186a090ab92a86d158018043951a1f0dbbdfc62e58040a110d02e`。原v1的HEAD-only规则会拦官方OAuth刷新；此问题由root提出，v2仅新增同官方域、确切 `/oauth/token`、最多一次POST，与三次HEAD独立计数。已读SDK真实刷新函数和httpx请求hook/重定向源码，确认正文由SDK处理、客户端不跟POST重定向，也不记录正文或带签名query。v1问题记录另存source_review_v1.json。

已核：实际attempt3终态与child/group已结束、当前PGID不存在均先于打开硬链；复制前后核注册inode和完整stat且源只读；再核终态文件SHA与PGID后才允许网络。官方metadata必须匹配原repo/revision/总大小/LFS SHA；CDN用独立无SDK认证或cookie状态客户端。单次206、精确Content-Range、identity、尾部计数及完整文件SHA共同决定成功；200/错段/短体/超长不回退从0下载。无论 apparent size 多大，都不预认前缀有效；全尺寸片段也须完整SHA。新目录独占发布，不修改canonical或原硬链。

新v2变更未改terminal/Range/hash路径。失败前缀、内部错误码和时点保留；第三方异常只记录类型，不输出潜在URL/凭据。源审未看到其余阻断。完整条目和所读源码SHA见source_review_v2.json。

边界：本审查没有网络/测试/模型、没有读活跃片段/凭据/数组，也没有检查或signal任何真实进程。它不证明当前下载已结束、TLS可用或前缀可恢复；root仍须等实际终态。终态可信性依赖已读的root自有attempt3回执生产者，不能把手工伪造回执当真实。SIGKILL/断电/磁盘满也不能保证最终回执；这些不是已发生事实。完整SHA通过只证明该文件身份，不代表模型加载或科学实验完成。
