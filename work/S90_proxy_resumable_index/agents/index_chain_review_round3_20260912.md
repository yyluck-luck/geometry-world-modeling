# S90 可恢复索引第三轮链与回执审查

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


审查时间：2026-09-12（Asia/Shanghai）  
审查对象：`index_rtmv_resumable.py` 当前工作树版本、`INDEX_PLAN.json` 及其绑定的 S88/S89/S90 本地回执。  
网络边界：**没有发起网络请求**，没有读取归档新正文，也没有运行模型。  
结论：**REVISE；当前版本不能启动，修正后仍需再做离线测试，再决定是否网络执行。**

## 一、最严重的启动阻塞：S89 绑定字段不兼容

当前代码 `seed_members()` 第 121--123 行检查：

```python
s89.get("archive_commit") != plan.get("archive_commit")
```

但实际绑定的
`../S89_matched_view_index/INDEX_PLAN.json` 没有 `archive_commit` 字段。它只有已经核验过的 URL：

```text
https://huggingface.co/datasets/TontonTremblay/RTMV/resolve/
855627f73a6fdd4db7fa150097a576f6e890c569/abc.tar
```

因此首次运行会在第 123 行直接抛出：

```text
RuntimeError: S89 archive identity changed
```

本地复现命令（只调用 `seed_members`，没有网络）已经得到该错误。随后第 124--126 行虽然新增了 commit/name URL 片段检查，但到不了那里。

最小修正是删除对不存在字段 `s89.get("archive_commit")` 的比较，并构造唯一的预期 URL，要求 `s89["url"]` 与其**完全相等**，同时检查 `archive_bytes`、`scene` 和 `archive_name`：

```python
expected_url = (
    "https://huggingface.co/datasets/TontonTremblay/RTMV/resolve/"
    f"{plan['archive_commit']}/{plan['archive_name']}"
)
if (
    s89["archive_bytes"] != plan["archive_bytes"]
    or s89["scene"] != plan["scene"]
    or s89["url"] != expected_url
):
    raise RuntimeError("S89 archive identity changed")
```

实际代码应把 `expected_url` 集中成一个函数，首次运行和 resume 共用，避免只检查 substring。也建议要求 S88 receipt 的 `url` 等于同一 `expected_url`；其现有 SHA 绑定可以防止历史回执被无声替换，但不能替代语义检查。

## 二、`state.members` 与请求链：新增函数存在，但 seed 仍可被篡改而通过

当前版本已经加入 `verify_member_chain()` 并在 resume 路径调用，这是正确方向。它验证：

- 扫描区成员数量与成功请求数量；
- 每个请求的 offset 和 `tar_member`；
- 扫描区成员的连续 `next_header_offset`；
- 首个新增成员等于冻结 `start_offset`；
- `next_header_offset` 接在最后扫描成员之后。

但它没有重新执行 `seed_members(plan)`，也没有把 checkpoint 前 `seed_member_count` 个成员与 S88/S90 的已绑定 seed 逐字段比较。它只检查 seed offset 非负且 512 对齐，并检查整个成员名不重复。因此可以构造一个成功请求链，把 seed 成员替换成任意自洽的假成员，函数仍返回通过：

```text
TAMPERED_SEED_ACCEPTED
```

这是离线构造的 tar header 测试结果，不是科学数据结果。

最小修正：resume 时重新得到 `expected_seed_members, expected_url = seed_members(plan)`，检查 `state.seed_member_count`、`state.members[:seed_member_count]` 与 expected seed 完全相等（或逐字段比较固定 identity 字段），并把 archive identity 一并存进 state。若担心重复读取本地证据，可把首次 seed 的完整 hash/identity 写入 state，但仍应以绑定文件 SHA 和重新派生结果作恢复校验。

此外，`verify_member_chain()` 当前对 seed 只检查偏移合法性，不检查 seed offsets 的有序性；虽然历史 S88 members 当前顺序正确，但恢复校验不应依赖未声明的隐含事实。

## 三、零块终止回执仍不能恢复

代码已经尝试在 `verify_member_chain()` 中特殊处理终端零块：若最后成功请求没有 `tar_member` 且状态为 `FIRST_ZERO_TAR_BLOCK`，则从成员链比较中剔除该请求。这一思路是对的，但 resume 顺序先调用 `verify_checkpoint_headers(state)`（第 316 行附近），而该函数假设每个成功请求都有：

- `body`
- `body_sha256`
- `tar_member`

零块记录由 `request_header()` 有意不写 `tar_member`，因此恢复会在 `verify_checkpoint_headers()` 中直接出现：

```text
KeyError: 'body'
```

离线测试已复现这一点。修正方式有两种，推荐第一种：

1. `verify_checkpoint_headers()` 明确识别 terminal-zero record，验证其 body 文件为 512 个零字节、hash、offset、HTTP/Content-Range 回执和状态，然后跳过 tar-member 解码；同时要求它只能是 `successful_requests` 的最后一项且 checkpoint 状态为 `FIRST_ZERO_TAR_BLOCK`。
2. 或把零块作为单独的 `terminal_request` 字段，而不是混在 `successful_requests`；这样“成功 tar header 请求”和“终止哨兵请求”语义清楚。

当前实现不能声称 zero-block checkpoint 可恢复。

## 四、`next_header_offset` 与成功请求的语义

对于普通非零 header，当前写入顺序是：请求成功 → 加入 `successful_requests` → 解码 → 计算 `following` → 加入 `members` → 更新 `next_header_offset` → persist。正常持久化后的普通链，`verify_member_chain()` 能发现 gap 和错误 next offset。

但有两个边界需明确：

- 普通请求在 `successful_requests.append()` 后、`members.append()`/`persist()` 前出错时，内存已有不完整记录；最终异常路径会保存 `STOPPED_ERROR` checkpoint。这个状态不应允许恢复，当前 main 已拒绝 STOPPED_ERROR，方向正确。
- 零块没有下一成员，当前 `next_header_offset` 保持在零块 offset；这可以作为“终止哨兵 offset”，但必须在 schema 和恢复验证中显式说明，不能让它被当作“最后 tar member 的 next offset”。

建议在 `state` 中增加 `terminal_request_type` 或在 receipt 中记录 `terminal_offset`，并单独校验。

## 五、失败回执审查

普通 HTTP/Range/长度/TLS/解码失败会在 `request_header()` 内构造结构化记录，包含 offset、时间、curl 返回码、HTTP、TLS、body 长度/hash、stderr 和安全响应头；失败大于 512B 的 `.part` 会删除。这些修正有效。

仍有两个问题：

- `subprocess.run(..., timeout=...)` 的 `TimeoutExpired` 在函数体外发生，不会进入 `request_header()` 的结构化异常分支；外层只保存 `{"offset": ..., "error": ...}`，缺少 elapsed、body_bytes、partial_body、curl 状态等关键信息。应在 `request_header()` 内捕获 `TimeoutExpired`，终止/等待子进程，构造结构化 timeout record，并清理或明确保留受限 `.part`。
- 失败 record 没有统一 schema/version。建议至少增加 `kind`（`transport_failure`/`timeout`/`range_failure`/`tar_decode_failure`）、`offset`、`started_utc`、`completed_utc`、`elapsed_seconds`、`body_bytes`、`partial_body_discarded` 和安全错误字段。失败 record 不能包含代理凭据或带签名 URL。

## 六、身份、seed 衔接和 resume 的最小验收清单

网络执行前，离线测试必须证明：

1. 在真实绑定文件上，`seed_members(plan)` 可以成功返回 S88 成员加 S90 probe，并且最后 probe 的 `next_header_offset == plan.start_offset`。
2. 改动 archive commit、archive name、archive bytes、scene 或 URL 中任意一项，首次运行和 resume 均拒绝。
3. 改动任意 seed 成员、seed count、普通成员、successful request、body hash 或 `next_header_offset`，resume 均拒绝。
4. 普通连续链、空扫描链、场景边界链和 512B 零块终端链分别能通过正确路径；其中零块 checkpoint 可以安全 resume/no-op。
5. 模拟 timeout、HTTP 非 206、错误 Content-Range、TLS verify 非零、body >512B、坏 tar header，均产生结构化失败回执并清理/标记 part。
6. output 目录非空无 checkpoint、第二进程并发、checkpoint 与 plan/code SHA 不同，均拒绝启动。

## 七、结论与下一步

当前结论是 **REVISE**，且不是“可以先小规模网络试跑”的状态：首要的 S89 字段不兼容会让正式运行立即失败；即使绕过它，seed 篡改校验和 terminal-zero resume 仍有边界漏洞。

下一步只做本地修正和离线 fixtures，禁止网络请求。修正后先运行 `py_compile`、绑定文件 smoke test、链篡改矩阵和 timeout/zero-block fixtures；所有测试通过后再由主 agent 重新审读实验合同，并决定是否执行极小额度的 tar header 请求。即使索引成功，它也只能证明“归档前缀的 header 结构可读取”，不能证明存在合格 RGB-D 科学数据，更不能验证 GRC-Memory。

## 八、主 agent 修正后的快速复核（2026-09-12 更新）

主 agent 已修正三项关键问题：

- 删除了对 S89 不存在的 `archive_commit` 字段的硬比较；`seed_members()` 现在可在本地绑定文件上成功返回 8 个 seed 成员。
- resume 时重新派生 `expected_seed` 并比较 checkpoint 的 seed 前缀，seed 篡改会被拒绝。
- `verify_checkpoint_headers()` 已允许且校验终端 512 个零字节请求；普通成功请求仍要求 tar member。

本地无网络复核结果：

```text
SEED_PASS 8 .../855627f73a6fdd4db7fa150097a576f6e890c569/abc.tar
SEED_LAST 00000/00134.depth.exr 12605440 12605440
CHAIN_EMPTY_PASS
PYCOMPILE_PASS
```

因此，**初始启动阻塞已解除，普通空链和 seed 衔接达到本轮离线 smoke-test 通过**。原报告前面的启动阻塞结论应理解为修正前快照；不应再据此声称当前代码仍必然在第 123 行失败。

仍需在网络执行前修正/测试的缺口：

1. `seed_members()` 与 resume 的 archive URL 仍用 `expected_fragment in url`，不是完整 canonical URL 相等检查。绑定文件的 SHA 已提供保护，但协议层最好要求 scheme、host、commit、archive name、bytes 全部精确匹配，并把 identity 写入 checkpoint。
2. 终端 zero record 当前 `verify_checkpoint_headers()` 能校验 512 个零字节，但没有检查其 offset 必须等于扫描链的下一个预期 offset；`verify_member_chain()` 也没有显式校验 terminal zero 的 offset，篡改 zero offset 仍可能通过“仅对齐且 body 为零”的验证。应要求 `zero.offset == (last_member.next_header_offset 或 plan.start_offset)`，并要求无 tar-member 的请求只能是最后一项。
3. `verify_member_chain()` 对“中间出现无 `tar_member`、后面又有普通请求”的异常路径可能触发 KeyError 或不够清晰地拒绝；建议先检查所有无 tar-member request 的位置，再只允许最后一项且状态为 `FIRST_ZERO_TAR_BLOCK`。
4. `subprocess.run(..., timeout=...)` 仍未在 `request_header()` 内捕获 `TimeoutExpired`。超时回执仍会退化成外层的简短 `{"offset", "error"}`，缺少结构化 elapsed/body/partial-body 证据；这是可复现性缺口，建议在网络前修正。
5. resume 校验仍未将 archive identity 作为 checkpoint 字段保存；当前依赖 plan SHA、绑定文件 SHA 与每次重新派生。可运行但审计回执不够自描述。

本轮最新脚本通过 `py_compile`，没有发起网络请求。结论更新为：**REVISE（核心 seed/zero 结构修正有效；canonical identity、zero offset、timeout receipt 和异常位置检查完成后，再考虑极小网络索引）**。
