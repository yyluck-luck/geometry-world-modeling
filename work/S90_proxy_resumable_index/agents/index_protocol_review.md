# S90 RTMV 可续 tar 索引协议独立审查

<!-- EXPERIMENT_NAME_LEGEND_20260912_BEGIN -->
> **S编号与具体试验名称说明（2026-09-12更新）**  
> 文档中的 `S86`–`S90` 是项目内部阶段编号，保留它们是为了让结果、日志和回执可以追溯；括号内是给新读者看的具体名称。编号不是论文术语、结果等级或“实验成功”的标志。S88–S90主要是数据资格/传输与协议审查，不能误读成模型性能实验。
>
> - **S86（单场景四目标几何条件注入基线实验）**：在一个已见静态场景、四个相关目标上，比较历史几何注入方式的真实生成链和RGB误差。
> - **S87（末端引导强度控制与多步引导必要性反例实验）**：复用S86缓存，比较末端处理强度与持续多步引导；它只检验该已见场景的有限反例，不验证GRC或长期几何收益。
> - **S88（RTMV相机JSON元数据与静态投影数据资格检查）**：核对归档身份、相机元数据和可访问的静态文件头；不是RGB-D配对性能实验。
> - **S89（RTMV配对数据TLS接续失败审查）**：记录两种TLS/传输接续尝试及其失败边界；失败本身不等于数据缺失或科学负结果。
> - **S90（RTMV归档配对数据恢复与索引协议审查）**：检查受限Range传输、归档成员身份、断点恢复和索引安全条件；已恢复的512B文件头不等于取得可用深度正文。
>
> 后续报告首次出现编号时应同时写成“**S86（单场景四目标几何条件注入基线实验）**”这类形式；后文可使用编号，但不要只写编号来替代试验名称。
<!-- EXPERIMENT_NAME_LEGEND_20260912_END -->


**审查时间：** 2026-09-11 18:16（Asia/Shanghai）  
**审查对象：** `work/S90_proxy_resumable_index/index_rtmv_resumable.py`、`INDEX_PLAN.json` 及其绑定的 S88/S89/S90 回执。  
**执行边界：** 只读源代码和 JSON；没有发起网络请求，没有读取新的归档正文，没有运行模型。  
**审查结论：** **REVISE（修正后再执行）**。核心“精确 512B Range + 固定 archive size + 原子 checkpoint + 失败停止”设计方向正确，但当前代码仍有几项会影响归档身份、严格 payload 边界和断点语义的缺口。未发现必须永久否决整个方案的理由；在修正前不应把索引执行称为通过。

## 1. 已通过的部分

### 1.1 Range 和响应长度的基本守卫

`request_header()` 第 165–179 行使用固定的 `Range: bytes=offset-offset+511`，并设置 `--retry 0`、连接/请求时间上限和重定向上限。第 211–219 行要求：curl 返回码为 0、最后 HTTP 状态为 206、最后一个 `Content-Range` 精确等于 `[offset, offset+511, archive_bytes]`，正文长度等于 512。这样可以拒绝常见的 200 全文响应、错误偏移和短响应。

`INDEX_PLAN.json` 也明确写了 512B 头、最多 64/256 个成功请求、300 秒协作窗口和首个错误停止。固定归档 commit `855627f73a6fdd4db7fa150097a576f6e890c569`、大小 `12064450560` 和起点 `12605440` 已绑定到计划。

### 1.2 tar 头解析和路径安全

`decode_tar_header()` 第 34–57 行要求头长度正好 512B、非负成员大小、只接受 regular/alias/directory 类型，并拒绝绝对路径、`..` 和空名。`next_header_offset()` 按 tar 512B 块对齐计算下一头。脚本不解压、不读取成员正文，符合“先找同 basename，不下载 RGB/depth”的范围。

### 1.3 失败停止和可见的负结果

传输、HTTP、Content-Range、正文长度、tar 解析、越界和重复名异常都会进入 `failed_requests` 并停止；失败的 `.part` 文件不会被伪装成成功头。`STOPPED_TRANSPORT`/`STOPPED_ERROR` 状态会阻止同一 checkpoint 自动重试，符合不无限循环的研究原则。

### 1.4 来源绑定和基本断点校验

首次运行通过 `load_bound()` 检查绑定 JSON/头的 SHA，并重解码 S88/S90 头。每次正常写入后，`persist()` 原子替换 `MATCHED_VIEWS.json` 和 `CHECKPOINT.json`。恢复时会检查 plan/code SHA，并由 `verify_checkpoint_headers()` 重读已记录的 512B 头、校验 SHA 和 tar 字段。

### 1.5 完整三件套识别的基本逻辑

`matched_views()` 只在计划 scene 中收集五位 view ID，并要求恰好各有 `json`、`exr` 和 `depth.exr` 三类 regular member；重复同名成员会在扫描循环中停止。`scope`、`body_contents_verified=false` 和 `scientific_method_validated=false` 也正确提醒：头部三件套不等于真实格式、物理同步或科学结果。

## 2. 必须在执行前修正（REVISE）

### R1. 断点不是严格 exactly-once

当前循环在 `request_header()` 返回后，先把成功请求写入 `state`，再把 `members`、下一偏移和 checkpoint 原子落盘（第 300–317 行）。如果进程在网络请求成功、但 `persist()` 前崩溃，下一次运行会从旧偏移再次请求同一个头；当前代码没有扫描已有 final header 并认领它。因此计划中的“never repeat a successful header”在崩溃窗口内不成立，实际语义是 **at-least-once**。

建议二选一并改名：

1. 明确写为 at-least-once，并在恢复时允许同一偏移重复请求、以 `(offset, body_sha256)` 去重；或
2. 启动时扫描未被 checkpoint 引用的 final/part 文件，验证其 512B、Content-Range 记录和 tar 头后再原子认领，然后才继续请求。

没有这个修正，重跑可能重复传输，且回执不能声称每个成功头只请求一次。

### R2. 恢复路径没有重新验证 S89 绑定文件

首次运行 `seed_members()` 会核 S89/S88/S90 绑定 SHA；但恢复分支第 237–245 行只检查当前 plan/code SHA，然后直接重新读取 `S89 INDEX_PLAN.json` 的 `url`。它没有再次检查 S89 文件的绑定 SHA、archive commit、archive size 或 scene。若绑定文件在两次调用之间被替换，checkpoint 仍可能使用不同 URL。

建议每次启动（包括 resume）都重新验证所有 `bindings`，并把已核验的 URL/commit/size 写入 state；恢复时只使用经过同一 SHA 检查的 URL。

### R3. 归档身份检查不完整

`seed_members()` 只比较 `s89["archive_bytes"]` 和 `s89["scene"]`（第 100 行），没有比较 `archive_commit`、`archive_name` 或预期 URL。S90 probe 回执也只校验状态、offset 和 tar_member（第 128–133 行），没有校验它来自相同 commit/总大小。仅有相同字节数不能证明是同一归档。

建议在首次和恢复时要求：

- S89 `archive_commit == INDEX_PLAN.archive_commit`；
- archive name/URL path 与计划一致；
- probe receipt 中 archive commit、archive bytes、scene 与计划一致；
- 将这三项写入每个请求回执。

### R4. TLS 校验结果只记录、没有作为成功条件

第 195–196 行记录 `ssl_verify_result`，但第 211–219 行没有要求它等于 0。通常没有 `--insecure` 时证书错误会让 curl 非零退出，但协议不应把这种行为假设当成显式守卫。

建议加入 `record["ssl_verify_result"] == 0`，并在失败原因中保留安全的证书/传输摘要。继续禁止 `-k/--insecure`。

### R5. 200 错误响应可能落盘超过 512B

计划意图是只保存 512B tar 头，但 curl 的 `--max-filesize` 使用计划值 8192（第 170 行）。若服务端忽略 Range 返回 200，curl 可能把最多 8192B 写入 `.part`；第 213 行随后才拒绝状态。那一段可能包含 tar 成员正文，违反“headers only”边界，即使最终标记失败。

建议把传输 cap 改为 512B，或使用能在首 512B 后立即关闭连接的严格读取器；失败时也要删除/隔离含有超过 512B 的 `.part`，并在回执记录 `body_bytes`。若重定向必须允许少量响应正文，应把重定向探针和 tar 头索引分成不同脚本/计划。

### R6. 没有强制 HTTPS/记录最终重定向身份

`-L`/`--max-redirs 5`（第 172–179 行）允许跟随任意最终 scheme/host；代码只检查最终 Content-Range 和大小，没有保存 `url_effective` 或重定向链，也没有拒绝 HTTPS 降级。CDN 重定向本身可能是正常的，但协议应能说明最终响应来自哪个 URL。

建议：限制 `--proto '=https'`（或等价的 HTTPS-only 选项），记录脱敏后的 `url_effective`/重定向数，并允许的 CDN host 列表写入计划；至少拒绝 HTTP 降级和非预期 scheme。不要把公开 query 当作秘密，但继续脱敏保存。

### R7. checkpoint 不能验证成员链和种子一致性

`verify_checkpoint_headers()` 只逐项核 `successful_requests` 的 body 和 tar_member；它没有检查：

- `state["members"]` 是否与成功请求按 offset 一致；
- `next_header_offset` 是否等于最后成员的 `next_header_offset`；
- seed 成员是否按 offset 递增、无重名、在 archive 范围内；
- 成功请求的 offset 是否 512B 对齐、是否重复。

建议恢复时重建并比较整个 member chain；发现不一致就进入 `STOPPED_ERROR`，而不是继续索引。首次 `seed_members()` 也应对 S88+S90 成员做排序/范围/重名检查。

### R8. 空 regular file 会被认作完整三件套

`matched_views()` 的完整条件只检查每种后缀恰好一个，并未要求 regular member `size > 0`。一个空 `.json`、空 `.exr` 或空 `.depth.exr` 头可能让脚本提前选择，尽管正文无效。

建议完整视角至少要求三项 `size > 0`，并把 `size` 写入选择理由；仍要标记 `body_contents_verified=false`，因为非空不等于 EXR/JSON 可解析。若保守地不加此条件，必须把“complete”改名为 `header-complete`，不得暗示可读取。

### R9. 输出目录和并发没有锁

`OUT` 固定为 `index_01`，只做 `mkdir(exist_ok=True)`。若旧 checkpoint 被手动删掉但旧 header 文件仍在，脚本可能覆盖同名文件并混入旧证据；两个同时启动的进程还会竞争同一个 `.tmp` 和 checkpoint。

建议每个冻结计划使用全新不可复用的 output 目录，若目录非空而无 checkpoint 就拒绝启动；增加 lockfile/`flock`，并在回执记录 PID、host 和 invocation UUID。不要依赖“用户不会同时启动”作为协议条件。

### R10. 全局 wall-clock 只靠 curl `--max-time`

外层循环根据 `remaining` 计算 curl 的 `--max-time`，但 `subprocess.run()` 没有 Python 层 timeout。若 curl 启动、代理或进程回收异常，实际 invocation 可能超过 300 秒。建议为 subprocess 设置略大于 remaining 的硬 timeout，超时后杀掉子进程、保存安全回执并停止；同时记录实际 wall time。

## 3. 可接受但应明确写入协议的限制

1. **tar 扩展头被拒绝。** `decode_tar_header()` 不接受 GNU/PAX/稀疏扩展。这是为避免读取扩展正文的保守选择；它可能提前停止在一个本来可解析的合法 tar，必须标为“索引不完整”，不能解释为视角不存在。
2. **scene boundary 后停止。** 这是计划范围内的安全停止；`members` 中仍会保留边界头，但 `matched_views()` 只统计计划 scene，报告中写明扫描前缀。
3. **只看 header 不验证格式。** `exr` 后缀、非零大小和 tar checksum 不等于 EXR 可读、RGB/depth 通道正确、单位正确或静态多视角同步。后续正文读取必须另立冻结合同。
4. **HTTP 206/Content-Range 不等于科学数据资格。** 它只验证传输片段和归档偏移；不能推出 GT、动态连续性、物理相机精度或 GRC 假设。
5. **失败状态不自动重试是正确的。** 任何新尝试必须有新的计划/审查和新输出目录，保留旧失败回执。

## 4. 秘密与隐私检查

当前脚本没有读取 NinjaDesktop 配置、订阅、账号或密钥；plan 中 proxy 是本机 loopback 地址，S89 URL 是公开归档 URL。`scrub()` 会处理带 query 的 URL，safe headers 只保留必要头，方向正确。

仍建议：

- 把 `url_effective`、`Location` 和 stderr 统一通过同一个 URL 脱敏器；
- 不把完整 curl argv 或环境变量写入回执；
- 对 checkpoint 的 `body` 字段强制只允许 `OUT` 下的 basename，避免篡改 state 后路径穿越；
- 不把 proxy 认证 URL 放进 plan；如将来需要认证，改用环境变量并只记录存在/不存在。

## 5. 执行前最小修订清单

在任何新网络请求前，至少完成并重新做 source review：

- [ ] R2/R3：每次 resume 复核所有绑定、commit、archive bytes、scene 和 URL 身份
- [ ] R4：把 `ssl_verify_result == 0` 设为硬条件
- [ ] R5：索引脚本正文 cap 改为 512B，失败 part 不保留超过头长的 payload
- [ ] R6：HTTPS-only、最终 URL/重定向链安全记录和允许 host 规则
- [ ] R7：恢复时验证完整 member chain、offset 对齐、seed 无重名/越界
- [ ] R8：三件套成员非零大小，或把状态名称改成 `header-complete`
- [ ] R9：新 output 目录 + 单进程 lock，拒绝无 checkpoint 的非空旧目录
- [ ] R10：Python subprocess 硬 timeout，记录真实 invocation wall time
- [ ] 修订后重新生成 code/plan SHA、独立审查票和新的冻结文件

## 6. 最终裁决

**REVISE。** 当前版本足以说明作者认真限制了 Range、失败和 payload 范围，也足以支持一次静态代码审查；但在 R1–R10 未处理前，不应执行批量索引，也不能把 `selected_development_view` 当作完整、可评分视角。修正后可重新申请一次有界索引；即便索引成功，也只得到“归档成员定位/格式准备”证据，不能替代 RGB-D 读取、几何评分、端到端生成或创新验证。

**本审查没有发起网络请求。**
