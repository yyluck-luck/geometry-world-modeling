# DeepSeek Harness 本地科研辅助

官方0.1.2-rc.1，已有Node24.19。已真实启动并连接科研工作区；OpenRouter凭据已配置，本地凭据mode600且Git排除。默认模型现为 `deepseek/deepseek-v4-flash-0731`，低价优先。

已完成一次自动科研审稿调用：headless → OpenRouter → DeepSeek V3，23.33秒，正文和session模型身份/11514输入+687输出tokens已核。这是切换默认Flash0731之前的首次任务。用户在Web界面发起的Flash0731问候也已可见回答，不能算成自动科研实验。

以后服务停止时，可双击[启动DeepSeek](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/启动DeepSeek.command>)。已运行时无需重复启动。科研目录已注册到左侧；目前辅助会话Read Only。

[具体用法与验收](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/HARNESS_GUIDE.md>)。DSH负责文献比较/gap/方案红队第二意见，所有引用和意见仍由主agent核查。
