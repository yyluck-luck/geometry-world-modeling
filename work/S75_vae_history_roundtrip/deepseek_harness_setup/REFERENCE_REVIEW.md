# DeepSeek Harness 官方入口与本机隔离配置审查

作者 `/root/next_control_feasibility`；记录UTC 2026-09-09T08:54:21.263977+00:00。官方仓库本批固定commit `5dda764ed3aa172535a7967b06ff95d9cbfe536a`，源码版本标注0.1.5-alpha.1；它不自动等于root实际安装的npm版本。仅下载原文/源码并审读，不安装、不启动、不读取任何实际凭据、不调用外部模型。

**DeepSeek Harness是官方开源agent运行框架，和DeepSeek模型是两个组件。可以先安装/检查/启动本地界面；未配置可用模型路由和相应凭据之前，不能声称已经能让DeepSeek帮忙科研。** 官方首页直接链接该仓库及npm命令。[官方入口](https://www.deepseek.com/harness/)，[固定README](https://github.com/deepseek-ai/deepseek-harness/blob/5dda764ed3aa172535a7967b06ff95d9cbfe536a/README.md)。

## 最小隔离配置

真正支持的环境变量是 `DSH_HOME`，不是推测名称。`resolveDshHome`源码优先显式configured参数，再非空DSH_HOME，最后`~/.dsh`；使用专属绝对目录可隔离这次安装产生的会话、配置与凭据。不要改系统HOME或CODEX_HOME。研究产物目录若会整体打包，建议把DSH_HOME放在独立本地运行目录，避免把后续凭据混入研究快照。[路径实现](https://github.com/deepseek-ai/deepseek-harness/blob/5dda764ed3aa172535a7967b06ff95d9cbfe536a/packages/util/home-paths/src/index.ts)。

profile位于 `$DSH_HOME/profiles/<name>`，默认web/headless/sdk/sdk-minimal/acp首次使用可从内置模板初始化。`--profile <name> --from-default-profile web`可创建未占用的自定义名；仅隔离DSH_HOME时直接使用web profile已足够。profile包含package.json和cordis.patch.yml，home还可有cordis.patch.yml；模型配置是 `$DSH_HOME/settings.yaml`。不要为了隔离另写未知CLI配置路径参数。[CLI说明](https://github.com/deepseek-ai/deepseek-harness/blob/5dda764ed3aa172535a7967b06ff95d9cbfe536a/apps/cli/README.md)。

## 本地界面与无key检查

源码文档确认 `--profile web`、`--host`、`--port`、`--no-open`。拟用结构如下，实际可执行路径/版本由root安装回执决定，先以所安装版本help复核：

```sh
DSH_HOME='/absolute/separate/dsh-home' /absolute/installed/dsh --profile web --host 127.0.0.1 --port 3080 --no-open
```

默认是127.0.0.1:3080；无需开放局域网或加trusted-host。启动URL含进程认证token，浏览器用它换cookie后转干净URL；root应将完整启动URL留在私有运行输出，不复制到研究报告/聊天。Web文档概述关于all-interface绑定有不一致措辞，本任务只采用已明确支持的loopback，未验证公网/LAN模式。[Web app说明](https://github.com/deepseek-ai/deepseek-harness/blob/5dda764ed3aa172535a7967b06ff95d9cbfe536a/packages/bundle/web-app/README.md)，[启动URL实现](https://github.com/deepseek-ai/deepseek-harness/blob/5dda764ed3aa172535a7967b06ff95d9cbfe536a/packages/bundle/web-app/src/index.ts)。

无API key可进行 `dsh --help`、`dsh --version`、`dsh --profile web --dump-default-config`。后者和 `--dump-config` 在源码中只组合并输出配置，不boot插件、不执行`!!js`；但profile准备可能创建本地目录，不应称完全无文件副作用。本批没有实际执行这些命令，能否在root安装包成功由其检查确定。[参数实现](https://github.com/deepseek-ai/deepseek-harness/blob/5dda764ed3aa172535a7967b06ff95d9cbfe536a/apps/cli/src/args.ts)，[配置展开实现](https://github.com/deepseek-ai/deepseek-harness/blob/5dda764ed3aa172535a7967b06ff95d9cbfe536a/apps/cli/src/dump-config.ts)。

## API key与模型启用

官方入门顺序是启动Web → Settings → Models填写DeepSeek API key →保存，再选workspace和模型。保存后立即生效，无需重启。文档说key是write-only，界面收到redacted描述，实际secret放 `$DSH_HOME/.credentials.yaml`，settings只留凭据引用；不得读出这个文件来检查或把key写进科研主账。当前说明不支持Codex一类OAuth登录provider，所以已有ChatGPT登录不能直接视作DSH的API凭据。[入门](https://github.com/deepseek-ai/deepseek-harness/blob/5dda764ed3aa172535a7967b06ff95d9cbfe536a/docs/user/guide/index.md)，[模型配置](https://github.com/deepseek-ai/deepseek-harness/blob/5dda764ed3aa172535a7967b06ff95d9cbfe536a/docs/user/guide/providers.md)。

可配置自有OpenAI-compatible端点或其他provider，但需要真实可用端点和正确协议/凭据。官方mock测试文档确认DeepSeek适配器环境名 `DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`，不过本批没有成功读取完整DeepSeek适配器README，所以优先按已完整核实的UI配置路线，不扩大环境变量优先级/默认值结论。

## 没有key的测试不等于免费真实模型

仓库有 `@deepseek-ai/dsh-llm-mock-server`：供测试/演示预编脚本的OpenAI兼容HTTP/SSE成功/失败响应，`pnpm run mock:llm`是源码开发命令；该package没有独立可安装binary。它不推理真实模型，也不能作为科研辅助答复来源。相邻llm-replay在文档中被列为已记录成功轨迹回放，本批没检查其实现。没有发现承诺免费DeepSeek真实推理的模式；不要把mock/replay或UI启动称模型已经可用。[mock说明](https://github.com/deepseek-ai/deepseek-harness/blob/5dda764ed3aa172535a7967b06ff95d9cbfe536a/packages/test-support/llm-mock-server/README.md)。

## npm与运行时界限

固定仓库root package.json：name `@deepseek-ai/dsh-root`，version0.1.5-alpha.1，Node engines `^22.19.0 || >=24.0.0`，pnpm11.7.0；build走tsx scripts/build.ts，test先构建native再vitest，postinstall为install-lefthook脚本。apps/cli/package.json发布名 `@deepseek-ai/dsh`、bin `lib/bin.js`，自身没有engines或scripts字段。**这并不证明整套npm依赖没有安装脚本**，root须查看实际发布包/依赖安装结果，不用仓库private root的脚本代替发布包安装行为。[root package](https://github.com/deepseek-ai/deepseek-harness/blob/5dda764ed3aa172535a7967b06ff95d9cbfe536a/package.json)，[CLI package](https://github.com/deepseek-ai/deepseek-harness/blob/5dda764ed3aa172535a7967b06ff95d9cbfe536a/apps/cli/package.json)。

此批取得README、入门、providers、CLI配置/参数/展开、home-paths、web-app及mock文档/源码。初次误猜models.md/cli.md得到404，改按真实文档链接；部分raw/API TLS EOF后有限改路取得内容，失败回执保留。没有启动外部agent或读取个人数据。下一步由root以安装的固定npm版本核版本/help、隔离配置展开和loopback界面；有已授权且已配置模型路由后再发真实研究任务。
