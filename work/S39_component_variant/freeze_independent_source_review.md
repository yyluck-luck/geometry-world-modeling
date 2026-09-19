# S39 新冻结工具：不同作者源码前审

**PASS，限定新增冻结工具的源码审阅；没有批准实际资源 core 或加载。** 已全文读 `freeze_manifest.py`、`FREEZE_PROTOCOL_DRAFT.md` 与作者准备回执，核其源码身份；未执行 prepare、attach、模型、旧测试或人工镜像测试，未读取权重、照片或 GT/预测数组。v2 加载器无变化部分不重审。记录时间与精确 SHA 见 JSON。

1. **齐件后才开始大文件哈希。** `prepare:102–133` 固定 gate/draft、原配置和 214 项来源，VMem/CLIP 接受显式绝对路径，CUT 来自原 draft，VAE 是两个指定文件。先检查五组件完整大小、不同路径、专用 VAE 目录、所有小来源/原 changi 路径存在，再进入大组件内容读取。小文件实际 SHA 在五权重之前全部核对。changi 是本次对固定原路径建立的字节身份，不是解码结果或凭文件名证明历史像素未变。
2. **全量内容与实际文件绑定。** `hash_once:67–86` 以 8 MiB 块累计实际读入字节，SHA 对固定预期；读取前后 pathname 与打开 FD 的 size/mtime/ctime/device/inode 均相同才接受。每项的成功或内容失配读数先追加并 fsync；`prepare:141–154` 在发布 core 前再核全部签名和 draft。`signature` 要求普通文件。文件身份检查服务可信项目的防误改，不是对可任意恢复元数据者的安全隔离。
3. **prepare 的 core 仍不可执行。** `prepare:145–161` 只在上述门全过后新建 core，empty review_receipts 不满足旧 gate 的两回执门。FROZEN 值是让之后批准时无需改 core，单独不构成执行许可；receipt 也写 execution_authorized=false。新目录与 exclusive write 防覆盖，0444 仅防误写，后续 SHA 仍是依据。
4. **追加真实审阅不改 core。** `attach_reviews:164–202` 要求调用者提供 core 文件 SHA 和两份现有回执的各自文件 SHA，核 source_review/runtime_freeze 的不同预定 status、完整 variant 与同一规范 core SHA。只深拷贝后填 review_receipts，并比较排除该字段后的整个 canonical JSON SHA 不变，复核 core 文件未变，再调用原 metadata gate。它没有生成、代签或猜测批准，也不验证人类/agent 身份；不同作者的真实阅读由根任务安排，协议已如实说明。当前源码审回执不能被当作尚未存在的真实 core 批准。
5. **来源域与复用不被偷换。** 新工具/协议 SHA 放到 `freeze_preparation.tool_sources`，仍保持旧 gate 要求的完整 214 项 source_identities。attach 核两个工具当前 SHA，审阅者须核实际 core 中这两项与本次审定版本一致。旧来源代码、CPU/FP32、种子和加载控制不变。
6. **哈希次数与失败范围准确。** prepare 每个组件全读一次，attach 只查大文件签名并核小文件；原 worker 仍另一次完整内容 SHA。协议清楚说这是两个不同时点，没声称总共只读一次或用旧 stat 绕过 worker。prepare/attach 失败保留新目录、已写 audit 和异常回执；若发布 manifest 后 metadata 失败，文件前缀仍可能存在，调用者必须以终态回执为准，不能以文件存在当成功。后续加载仍受原 gate 再核。

未发现必须修改的新增源码问题。下一步保持此版本，等所有完整组件齐备后由根任务执行一次 prepare；再审实际 core/内容哈希回执并让两名实际作者分别绑定批准。没有执行就没有文件齐全、冻结成功、资源可加载或视频可生成的结论。这里沿用本地 scientific-critical-thinking 的来源、身份、执行与结果分级，不把准备工具当实验。
