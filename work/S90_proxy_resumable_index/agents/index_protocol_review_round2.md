# S90 RTMV 索引协议第二轮只读审查

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
对象：`index_rtmv_resumable.py`、`INDEX_PLAN.json`  
边界：未发起网络请求，未读取新归档正文，未执行模型。

## 已确认的修正

- 第 72--77 行已要求 JSON、RGB/EXR、depth 成员均为非空；因此空 regular file 不再被标为 complete。
- 第 175--196 行增加了 Python `subprocess.run(timeout=...)`，并将 curl body cap 固定为 512B；第 240--247 行会删除超过 512B 的失败 part。第 182 行和计划第 16 行一致。
- 第 186 行 `--proto`, `=https` 禁止非 HTTPS 传输；第 224--234 行把 curl 返回码、HTTP 206、TLS verify=0、Content-Range 和 512B 长度都作为成功条件。
- 第 101--103 行和第 264--271 行在首次/恢复时检查 S89 archive bytes、scene、archive_commit；计划和代码可通过 `py_compile`，本轮得到脚本 SHA `de584d33997f3a4ce994a35eea5855d50ff9c4d5498417b882fa8a308e64c242`、计划 SHA `f2275efdbdfff277ee250980de0985f51e4daf15d9725ce9cd955d4d4f121e99`。

## 仍需修正或明确

1. **归档身份仍不完整（R3，计划 5--9；代码 101--103、124--136、264--271）。** 代码没有比较 `archive_name`、URL 的预期路径，S90 probe receipt 也没有要求其中的 commit/bytes/scene 与计划相等。相同大小和 commit 字段不足以证明 URL 实际返回同一个归档。首次和 resume 都应检查并把 archive name/commit/bytes/scene/脱敏 URL 写入 state。
2. **TLS/重定向结果缺少可审计身份（R6，代码 175--191）。** `--proto =https` 已防止降级，但未保存 `%{url_effective}`、最终 scheme/host 或重定向次数，也未对最终 host 设置 allowlist；`safe_response_headers` 可能含 Location，但没有“最终身份”字段。若允许 CDN，应在 plan 固定允许 host，并记录脱敏最终 URL；否则拒绝任何非预期 host。
3. **断点链校验仍不充分（R7，代码 141--157、263）。** `verify_checkpoint_headers()` 只按成功请求的 offset 检查递增/对齐和名字唯一，没比较 `state.members` 与请求链，也没核 seed 成员的顺序、offset 范围、与第一新 offset 的衔接，亦没核 `next_header_offset` 是否等于最后成员的下一头。恢复可能接受成员列表被篡改但每个 header 自洽的 checkpoint。应重建完整链并拒绝差异。
4. **崩溃窗口语义应保持 at-least-once（计划 28 已改名，但实现未去重）。** 第 327--344 行在 `successful_requests` 写入后、`persist` 前崩溃时会重复同一 offset；计划现在诚实地声明 at-least-once，但需实现 offset+hash 去重，或明确在结果与用户报告中不再声称 exactly-once。
5. **并发/旧输出目录风险未处理（R9，代码 255、计划 13）。** 固定 `index_01` 且无 lockfile；两个实例可能同时写 checkpoint/tmp，删除 checkpoint 后残留 header 还可能混入新运行。执行前应加单进程锁，并在无 checkpoint 但目录非空时拒绝启动，或每次冻结计划使用不可复用新目录。
6. **异常超时的回执不完整（R10，代码 175、327--359）。** `TimeoutExpired` 在 `subprocess.run` 处直接抛出，外层捕获为 `STOPPED_ERROR`，但不会生成包含 elapsed、returncode、body_bytes、stderr 的结构化 failed record，也没有显式清理/标记 timeout part。建议捕获 `subprocess.TimeoutExpired`，杀掉进程并写安全失败记录。
7. 第 40--41 行仍拒绝 PAX/GNU 扩展，这属于保守边界；必须把因此停止解释为“索引不完整”，不能解释为场景不存在。第 81 行的 complete 仍只是 header-complete，已有 `body_contents_verified=false` 是必要的。

## 结论

**REVISE（修正后再执行）。** 本轮没有发现语法回归；修正后的 TLS、512B、非空三件套和 Python 超时守卫有效。但上述身份、链、并发与超时回执缺口仍足以影响可复现性。未完成前不应发起新的网络请求，也不能把 `selected_development_view` 当作有效 RGB-D 科学样本。
