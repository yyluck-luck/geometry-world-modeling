# 科研 Harness：安装、接入和分工

更新UTC：2026-09-09T09:45:31.627619+00:00。

**已接通官方DeepSeek Harness和OpenRouter，科研工作区已注册。** 本机安装@deepseek-ai/dsh 0.1.2-rc.1，使用既有Node24.19。原Node22.14依赖警告已保存，未改全局Node。实际启动命令在runtime目录为 `npx @deepseek-ai/dsh web`；09:00:01Z启动，认证后HTTP200，Chrome界面可见。

安装位置 `tools/deepseek-harness/runtime/`。专用 `tools/deepseek-harness/state/` 保存凭据、会话和私有启动认证日志，已Git排除；凭据文件mode600。**不要把state目录复制到报告/共享包，不打印或索引其中Key/启动token。** Key经用户明确授权配置于内置openrouter，而非deepseek-official。官方说明：[Providers](https://deepseek-harness.github.io/deepseek-harness/en/guide/providers)。

原custom provider ID openrouter与内置目录冲突，草稿取消后通过Add provider→openrouter保存。模型列表读取不算模型回答。原Web目录按钮走macOS原生choose folder，未观察到对话框；已依据安装包真实接口，通过认证后的workspace/create注册现有项目，09:25:00Z返回created:true。workspace ID a638e86f-4d3a-42bb-ad92-2dbe0383161d，UI左侧已显示geometry-world-modeling，项目内会话可用，无需重启。

## 已实际调用

第一次自动科研任务采用官方headless，输入自包含S76方案，模型OpenRouter/deepseek/deepseek-chat。实际09:24:09.903996–09:24:33.230540Z，23.326379秒return0，3220字节正文。归档会话请求/响应均指向该模型；11514输入/687输出tokens，无工具事件。任务为只读第二意见，不是重新读论文/模型实验。证据：work/S76_relative_camera_response/dsh_protocol_review_01/attempt_01及ROOT_REVIEW_DECISION.md。

root拒绝原答中两项错误：反向yaw时应反转的是物体位移方向，e_identity−e_H改善量在两个正确方向下都应偏正；未保存全部epsilon正文不自动推翻相同draw路径/RNG状态核验。单场景、匹配真假、FOV和FP32限制继续保留。不能因为DSH说sound就接受新方法。

用户17:28在Web发出问候，第一条仍用deepseek-official而报MISSING_CREDENTIAL；切换到OpenRouter Flash0731后第二条有真实答复。该用户操作与自动科研调用分开，未冒充我们的科研任务。当前Web模型选择和已保存agent-default-model均为openrouter/deepseek/deepseek-v4-flash-0731，辅助会话Read Only。

## 低价与自动调用

用户要求低价优先，后续默认 `deepseek/deepseek-v4-flash-0731`。2026-09-09官方页面最低列价为每百万tokens输入$0.05、输出$0.16；不同路由供应商价格不同，非本次账单。参考[OpenRouter模型页](https://openrouter.ai/deepseek/deepseek-v4-flash-0731)。首次V3任务页面列价约$0.2574/$1.029；其账单未查询，不能称实扣。优先合并提取/比较、短输入和有限回答，不自动升级高价模型或循环求好评。

本版本正确CLI为 `dsh --profile headless --patch /absolute/overlay.yml "任务正文"`。没有 --model/--provider/--no-tools这些CLI参数；模型通过单次专用settings选定，以免原共享默认值压过composition。实际成功的patch/settings在上面任务目录。只保存apiKeyEnv引用，不复制Key。stdout为最终正文，stderr可能含推理/报错，单独私有保存。只读权限不等于零工具或无网络；本次实际session未出现工具调用。

主agent仍负责科研流程、真正检索、实现、执行、证据验收和记忆；DSH用于文献提取、横向比较、gap候选、方案/统计/论文红队。其输出须原文或代码/数值核验。已冻结实验不静默改指标；普通工程接入不算创新。

## OpenAI参考资料

[文章离线阅读版](</Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/Harness_Engineering_2026-09-09/Harness_Engineering_离线阅读.html>)和项目适用性审阅已保存。直接HTML403原件保留；正文经官方读取接口归档，未下载图片，不是安装包。继续采用短AGENTS入口、原文和可核验反馈；当前检查器只做必要的S76状态分支修正，没有宣称完成大规模框架重构。

自动入口为 `python scripts/run_dsh_review.py --prompt 已核材料.txt --output 项目内新目录`（在项目根目录使用既有Python环境）。默认Flash0731、180秒模型进程外控、无包装器自动重试；root已读完整源码并实际执行v2一次。900词是软提示，不是token或费用硬上限；provider内部重试不由包装器保证。


## 以后统一归入geometry-world-modeling专栏

所有新DSH科研任务均从项目根目录`/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling`启动。包装器同时将headless cwd及只读sandbox workspaceRoot设为该目录，`--output`只决定本次研究产物位置。**cwd正确并不自动完成专栏归组**：结束后还需以实际完整session ID调用官方session/create，指定已注册workspace ID `a638e86f-4d3a-42bb-ad92-2dbe0383161d`，不同时传cwd。

包装器只对前后路径差得到的新会话读取首个zstd header帧；必须唯一匹配项目cwd才附加。用现有本机bootstrap与CookieJar认证，所有认证/附加请求只允许127.0.0.1:3080，不打印token或复制凭据。完整RPC返回及session ID确认成功才记`ATTACHED_PROJECT_WORKSPACE`。模型返回但归组失败时，正文仍保留，`GROUPING.json`明确记录未完成；不要为修复分组再调用一次模型。

本轮已成功自动归组：2026-09-09T09:41:58.132092+00:00至2026-09-09T09:42:30.587362+00:00，模型调用32.455113秒return0，正文5942字节；2026-09-09T09:42:30.687531+00:00归组完成。会话`session-3d41fa3c-73cb-4062-87ea-be48865e783e`，root本轮报告已在左侧专栏看到、选中并重命名“创新审查 01｜事件记忆与固定预算”。请求模型和界面选择均为`openrouter/deepseek/deepseek-v4-flash-0731`；此次会话请求/响应身份和usage独立审计仍待完成，不能由设置值替代。参见[实际返回回执](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S76_relative_camera_response/dsh_event_memory_review_01/RECEIPT.json>)和[归组回执](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S76_relative_camera_response/dsh_event_memory_review_01/GROUPING.json>)。

第一次V3方案审查从`dsh_protocol_review_01`子目录启动，因此旧会话仍在Ungrouped。官方接口要求已有session.cwd与workspace.path精确匹配，不能通过attach迁移该旧cwd；保留旧成功证据，不修改历史。用户要求适用于以后所有新科研会话。正文建议、会话归组和科学有效性分别验收，不改变冻结实验。
