# DeepSeek Harness：workspace 与 headless 的已核路由

结论：科研审稿子任务可直接从项目目录使用官方 headless，不依赖 Web 的 workspace 对话框。已安装版本为 `@deepseek-ai/dsh 0.1.2-rc.1`。本次仅核安装包源码/帮助文本定义，未调用模型、HTTP API、CLI boot，也没有读凭据或私有启动日志。开始 2026-09-09T09:17:03Z；结束 2026-09-09T09:21:58.393041+00:00。

## 优先路线：headless 科研分析

实际 CLI 为 `dsh --profile headless "任务正文"`。需加覆盖文件时是 `dsh --profile headless --patch /absolute/overlay.yml "任务正文"`，launcher 参数必须在 task 前。headless 自身仅接受 task 与 `--help`；没有 `--model`、`--provider`、`--workspace`、`--output-json` 或 `--no-tools` 开关，不能把其他产品的参数套进来。运行前把工作目录设为研究目录即可；runner 将 `process.cwd()` 放入新 Agent 元数据。它不启动 Web/HTTP 服务，因此不要求先修 workspace。

未来由 root 执行的最小 argv（本次没有执行）：

```text
executable: /Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime/node_modules/.bin/dsh
argv: ["--profile", "headless", "<已准备的 S76 审查材料及问题>"]
cwd: /Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling
environment: 与现有 Web 使用同一 DSH_HOME；建议显式 DSH_PERMISSION_MODE=read-only
```

**模型选择**：runner 读取 `agentDefaultModel.currentSelection()`，从 `agent-default-model` 的 `provider`/`model` 创建 Agent。`settings.yaml` 同名 section 的已保存选择优先于 composition 默认值；仅在 patch 改默认值不能保证盖过已有 settings。OpenRouter 路由来自 `llm-pi-ai.providers` 字典，其键就是 provider ID，model 必须为该路由 catalog 的实际 ID。UI 显示“provider 已配置”不证明默认选择已经指向它。最短可靠做法是先确认/选择已有 OpenRouter 的默认模型，再用同一 DSH_HOME 启动 headless；本次不读取用户 settings，也不猜模型 ID。源码默认仍为 `deepseek-official/deepseek-v4-flash`，不能静默依赖它。不要把 API key 放进 argv、patch 或输出。

**只读和禁工具不是一回事**：base 实际包含 `read-only` preset，`DSH_PERMISSION_MODE=read-only` 是 sandbox 默认覆盖。存储的 permission 默认仍可能在新会话应用；需 root 确认有效 preset。该模式不等于零工具、不等于无网络，也不禁止 harness 自己保存 session。`approval.policy=never` 表示拒绝所有需要审批的动作，并非自动批准所有动作；没有 answerer 的 `ask` 也会 fail closed。当前 CLI 没有完全禁工具开关；registry 的正式 `agentCtx.tools.restrict({allow: []})` 是 agent-scoped API，不是 headless CLI flag，而且 PTC 的 `run_code` 是特殊 transport，不能把这一个方法不加分析地叫成“零工具”。如必须严格无工具，应先用单次专用 composition/Agent setup 明确设置与检查 capability，而不能只靠 prompt。此处没有实现或试运行该改造。最省事的只读意见输入，是 root 在 task 文本内给出必要材料，而非请求模型自行探索整个仓库。

**保存结果**：原 runner 把最终 assistant 正文写 stdout，reasoning 增量及错误写 stderr；返回码 0 为 completed，其他/错误为 1。不提供独立 JSON 输出模式，中间 tool 结果不会打印到 stdout，但 session 会持久化。建议 root 的外部观察器分别保存 argv（无秘密）、开始/结束/超时/returncode、stdout.md、stderr.log 与 SHA。stderr 可能包含模型推理和敏感上下文，不应原样展示为研究报告。无首 token 时 stderr 可能沉默，不应判定为死锁。审稿模型意见属于第三方模型建议，不替代实际实验或独立数学核验。

## Web workspace：最短无需重启的官方 API 路由

按钮实际不是浏览器 `showDirectoryPicker`。UI native flow 自身返回 null（无 DOM），调用 host `directoryPicker.pick()`；loopback `127.0.0.1`、macOS、无 SSH 标记时 auto backend 选择 native，而 macOS backend 用 `osascript` 的 `choose folder`。因此“无 DOM 弹窗”本身符合 native 实现；本次没有观察 host chooser 进程，不能把其不出现归因到某个已证实 bug。

正式 API 是 `ctx.remote.workspace.create({path})`。它注册已存在目录，先 `resolveByPath`，已有则返回 `created:false`，否则创建 workspace 记录；不是创建项目文件夹。可以绕过 chooser，从已打开的 `http://127.0.0.1:3080` 页面发同源请求。以下是源码复核得到的实际 wire 形状，**本次未发送**：

```javascript
const reply = await fetch('/api/workspace/create', {
  method: 'POST',
  headers: {'content-type': 'application/json'},
  body: JSON.stringify({
    type: 'client-request',
    rpcId: crypto.randomUUID(),
    method: 'workspace/create',
    payload: {args: {request: {
      path: '/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling'
    }}}
  })
}).then(r => r.json());
console.log(reply);
```

成功应检查 `reply.result.ok === true`，并记录 `reply.result.value.workspace.workspaceId/path` 与 created 状态；失败保留真实错误。之后刷新 workspace 列表或选择新记录。API mutation 由 root 决定并执行；本次无调用，因此尚不声称实机创建成功。安装的 launcher/web startup 没有独立 `workspace add` 命令。备用 browse backend 可替代 native，但需要改 composition/重启，本任务没有实施，不应优先于同源 workspace API 或 headless。

## 实际源码范围和身份

以下全部为已安装公开包；只读指定源码及 README，未扫描 state。SHA 是当前文件全字节身份，阅读为相关段落；未声称完整审计每个 bundle 的无关代码。曾向不存在的 `dsh-base/cordis.yml` 和两个猜测的 package 路径查询，返回不存在，随后按实际包名定位；无任何修改。

- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime/node_modules/@deepseek-ai/dsh/package.json` — SHA256 `606a68d02cf561bc7d6ce9bdf86ae2b06761e727b35959a363e856ea20f64805`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime/node_modules/@deepseek-ai/dsh/lib/bin.js` — SHA256 `dc23f6c5dd7df8834e3e38bdb9609d77b459834681ae9b7133b417b0c35f3166`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime/node_modules/@deepseek-ai/dsh-headless/lib/startup.js` — SHA256 `1d93363af3f955b37a044cd1bd7b438881c9f842ef79c4ec222b082d3a65c157`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime/node_modules/@deepseek-ai/dsh-headless/lib/index.js` — SHA256 `6e5304e6aa338c4d58b5e587a6f3c3c7e343cc3fe54edd9b07002e03cf497532`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime/node_modules/@deepseek-ai/dsh-headless/cordis.patch.yml` — SHA256 `44d138bb9401c4ddf7dabcbb37cc6c627a7cd20c5cba4eec7bad2ef099ae8fae`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime/node_modules/@deepseek-ai/dsh-base/cordis.patch.yml` — SHA256 `e6cfc981b2c3fd83e95f4ef710dc961f91dca025232e196db7ace5dd6b30fe14`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime/node_modules/@deepseek-ai/dsh-agent-default-model/lib/index.js` — SHA256 `944261f8383c4fe135871da5ebac24f6d9aa0de40e948dbeb8b19d2e107936c4`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime/node_modules/@deepseek-ai/dsh-llm-pi-ai/README.md` — SHA256 `11d9c828753188d1b867c132a350167b0002758b481131bf2aa91be29adc5e10`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime/node_modules/@deepseek-ai/dsh-settings-file/lib/index.js` — SHA256 `b44bf0a905ff47bd7d4de357839225a44714cc0083850187fa7ff116c605e753`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime/node_modules/@deepseek-ai/dsh-tools/lib/index.js` — SHA256 `598d5a54cfed9fdc497b8504aefb464efe97ff6c6918e68888481bb6e3dfbda9`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime/node_modules/@deepseek-ai/dsh-user-approval/README.md` — SHA256 `1562cc906aee1155d82beecd1e9798219643c057e4201babd42674a456aa6b4c`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime/node_modules/@deepseek-ai/dsh-client-ui-workspace/lib/client.js` — SHA256 `53c40660195c42cde709b802e239f473dd721f45bc329684af31c01fdb73282a`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime/node_modules/@deepseek-ai/dsh-client-ui-directory-picker-native/lib/client.js` — SHA256 `2e6b8b235966362d6bf4da0af4f0539c251ad0d713bde42463e0f0accc4bd4b7`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime/node_modules/@deepseek-ai/dsh-host-directory-picker-auto/lib/index.js` — SHA256 `f7b7ac8cfd160e15ed47076f01718023ec90cd4f9cd814755d8aa9e6731ca8f1`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime/node_modules/@deepseek-ai/dsh-host-directory-picker-native/lib/index.js` — SHA256 `716633a2e4fbf240b618a844476319cd76d940c33f29f940905a5216889d1bd5`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime/node_modules/@deepseek-ai/dsh-api-workspace-controller/lib/index.js` — SHA256 `e1f66ef2a5fe8a18a00d30820fc2033431cdc49b15b10375d9e466b71d6c4df1`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime/node_modules/@deepseek-ai/dsh-api-workspace-controller/lib/typert.remote-client.js` — SHA256 `20661af30a79b4203f9371448592dcdc07ba8b659758bce99471e4aa8f5adaa6`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime/node_modules/@deepseek-ai/dsh-api-gateway/lib/index.js` — SHA256 `c69e238a1b9b7cf36950e05a6ad5e86228a476b956e4ad056fb9125dc156f8a8`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime/node_modules/@deepseek-ai/dsh-api-gateway/lib/client.js` — SHA256 `55dbd591222b28e557e7d47368f7770114a88d97206e910fae940768c83950cd`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/runtime/node_modules/@deepseek-ai/dsh-client-connection/lib/client.js` — SHA256 `1b8e76d7fb14c9305e6d43ab03bd908328341537af05c4159747d6da33308257`
