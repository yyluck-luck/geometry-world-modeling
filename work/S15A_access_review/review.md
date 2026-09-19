# S15A 有界 ZIP 提取器独立前审

结论：**最终源码与 metadata_contract_v2 在本次用途范围内通过独立前审。** 可据此获取 `rgb.txt` 与 `depth.txt` 的真实元数据；本报告本身未发起任何真实请求，也未打开任何真实图像、深度、轨迹成员。

最终绑定：

- `scripts/fetch_s15_zip_members.py` SHA `ec68dfa5831a2cc0e7a191f25c6ef3ddae23e8bde49ff7a74e8d5c949de578b9`
- `work/S15A_access/metadata_contract_v2.json` SHA `fa928f19eb7a1309453625d5491479920735feaff7cf76b15d5576ef0271b469`
- 独立检查：`checks_v2.json`，实际 UTC 2026-09-06 09:47:18.150824—09:47:18.181741，共 35 项判定通过。

由不同于下载器作者的 agent 阅读源码、合同、冻结目录并实现人工 ZIP/mocked HTTP。测试 ZIP 由 Python 标准库生成，验证输出原始字节；没有复用下载器解压公式构造期待输出。覆盖正确 stored/deflate、data-descriptor 头、payload CRC、头与目录 CRC 不一致、名字不一致、路径穿越/绝对路径/反斜杠、加密标志、签名、解压上限和 deflate bomb、请求/响应字节预算、中央目录边界，以及 HTTP 200、错误 Content-Range、来源 URL/ETag/Last-Modified 改变、错误 encoding/content-length、短/超长 body。响应头身份失败均验证 body 未读。

静态核查两个成员：`rgb.txt` 未压缩 73,620 B，`depth.txt` 77,694 B；均低于预定 200,000 B。冻结目录名称唯一，目录 SHA 与合同一致；只有上述两个成员入 allowlist。其余 ZIP 方法、加密、ZIP64 等不在当前已知成员合同内，不为凑数量扩展支持。

发现与修正保留：初版预算仅预核 length，实际读 length+1，故存在恶意超长响应让“恰好用尽的预算”超出 1 B 的逻辑边界。独立审查先反馈根；根在真实网络访问前修正为预核 length+1 并另立 v2 合同，旧合同保留。本 agent 没有改下载器。第一次人工脚本仍期待旧版探针暴露超读，但开始运行时已载入修正版本，末尾断言因此失败，实际结果是 0 请求/0 body 且提前报预算不足，见 `cases/hard_byte_budget_probe/output/receipt.json`。该失败属于人工预期与已修源码之间的时序差，不是下载失败或科学实验失败。旧脚本和完整人工 case 回执保留；最终 v2 新目录重新检查全部必要边界，35 项通过。

同时审阅 `docs/S15A_NATIVE_HISTORY_PROTOCOL.md`：首时刻+1秒开始、0.4秒间隔、24项唯一有序样本、nearest 时间并用较早者破同距、25ms偏差门槛、任何失败不换起点；只获取20 history 原生 RGB，4 future RGB、全部 depth PNG 和 GT trajectory不获取。模型只运行历史，条件/输出/资源界限事先固定，真实照片和模型输出区分。当前坐标审计只允许可运行性结论；协议明确不计算深度准确率，不宣称创新成立，范围适当。

访问器检验不替代真实服务器表现；真实请求仍应逐条保存响应身份、字节和解压 CRC。未来20 RGB的成员列表、下载预算与模型 manifest需要另行冻结，不能用本次2文本合同代替。后续若改源码或合同，应核实际改动再冻结；本次审查不能永久认证未来版本。
