# S79 metadata attempt01：V3 ZIP 独立补审

结论：**PASS；本次受审 V3 的剩余 blocker = 0。** V2 的原阻断结论保留；本结论只对应下列 V3 SHA。root 应核读本报告及绑定源码后，再决定执行合同中的唯一网络动作。本审查未发起该动作。

## 版本与归档身份

| 文件 | 本次独立计算 SHA-256 |
|---|---|
| `fetch_project_metadata.py`（V3） | `765a905945c612af6f948fdeb2ae80ea25337a77cb34a91db7b64167cf3d4f9f` |
| `EXECUTION_CONTRACT.md`（V3） | `88697906bc32e4a32dd205de343c6b53b63450215aba22bb9285deea6107caf1` |
| `archive_v2/fetch_project_metadata.py` | `2a177143f6b3b544b3c3941ed847b9affed409ae9567de230c148871f7c6aa45` |
| `archive_v2/EXECUTION_CONTRACT.md` | `83def5ebf1ace940bb7be39b95d6adcae4c44ac9f8f71ea241dfd1c90fae3922` |
| `archive_v2/AUTHOR_PREEXECUTION_SELFTEST_V2.json` | `7ee462aff55d3370904147002f53aa7ee4026e8066bdfb8d5f3881d5891be8e7` |
| `archive_v2/ARCHIVE_RECEIPT.json` | `cd9c8a16dd88d0f6686e068f3b150a075d95a2dc8177aeb36cee8ba9e37c9fb7` |

归档源码与合同逐字节 SHA 与我上轮实际审查的 V2 一致。归档作者自测与 `ARCHIVE_RECEIPT.json` 中的 SHA 一致；上轮未单独封存作者自测 SHA，因此对该自测的历史身份仅能声明与归档回执一致。未改写这些归档文件或上一份 `INDEPENDENT_PREEXECUTION_REVIEW.md`。

## 两个旧 blocker 的处理

| 旧问题 | V3 源码核验 | 结论 |
|---|---|---|
| 重复名字可使按名字读取反复选择最后成员；仅加总目录声明长度不足以代表实际读取量 | `fetch_project_metadata.py:234–256` 先检查全部成员，将 POSIX 路径折叠结果再作 NFC，重复即拒绝；`:258–282` 保存并使用具体 `ZipInfo` 对象打开成员，分块累计单成员及全档案实际字节，超限拒绝并核对声明长度。正常返回的清单同时记录声明量和实际展开量。 | 已修复 |
| Unix FIFO/socket/device 等未被拒绝，与合同不符 | `fetch_project_metadata.py:242–249` 只允许类型位为 0、regular 或 directory；其余类型及加密成员拒绝。非空目录拒绝；目录不进入 JSON 内容读取。 | 已修复 |

`EXECUTION_CONTRACT.md:36–40` 已明确上述边界和 V2 归档。当前读取过程中没有按成员名字调用 `read()` 的旧路径，没有向文件系统解压成员，没有执行档案内容。

## 独立执行的新增合成检查

执行时间（UTC）：2026-09-10T15:33:51.176341+00:00；北京时间为 UTC 加 8 小时。检查记录：`INDEPENDENT_ZIP_SELFTEST_V3.json`，SHA-256 `88c89073697f229546d3ab601cf6653d24c18cd00ab39ad579fbc22f90167293`。

**23 项检查全部 PASS**：

- 正常 regular 与类型位 0 的成员可投影，实际展开量与每成员声明量一致；空目录被跳过。
- 完全重复、点路径别名、重复分隔符别名、Unicode NFC 别名四类重复拒绝。
- FIFO、socket、symlink、character device、block device 五类特殊成员拒绝。
- 上级路径、绝对路径、反斜杠路径、非 JSON 文件及非空目录拒绝。
- 目录声明的单成员与全档案上限各自触发正确固定错误码。
- 使用**合成成员流替身**分别覆盖实际单成员超限、实际累计超限、实际长度与声明不符、加密标记拒绝；核对 `open` 参数是原 `ZipInfo` 对象，并逐成员只打开一次。这些流替身专用于验证计数分支，不能写成对真实恶意 ZIP 的实验。

真实 ZIP 容器测试全部是内存中人工生成的小档案。未运行完整作者 `selftest()`：AST 对比确认 `Scanner`、`Reject`、`now`、`sha`、`save` 未变；按本轮范围不重跑未改 JSON 套件。正常 ZIP 的投影用到合成最低 metadata，这是新增 ZIP 正常路径的必要验证。顶层模块以非 `__main__` 名称加载，未调用 `run()`。

## 非 blocker 与结论限度

1. 实际读取使用“剩余额度 + 1”探测上限：最多额外读取 1 个字节以发现超限，随后在存入 chunks、JSON 投影或结果发布之前拒绝。因此这里的 80MB/100MB 是可接受展开内容的上限；不能表述为解释器或底层解压器在所有情况下连一个额外字节都不会接触。此有界探测不恢复 V2 的重复读取漏洞。
2. 类型位 0 被明确兼容，这是合同允许的 ZIP/DOS 普通项；没有文件系统解压或执行，因此不需据此增加新协议门。
3. 本补审不证明官方样例能成功获取、不证明真实 ZIP 一定符合 schema，也不证明答案盲性由此建立。V2 已审的单次获取、curl 配置隔离、白名单和固定错误输出结论只在未改路径范围内继承。新方法、数据结果及科学结论均未在此验证。

实际行动计数：**0 网络请求，0 真实原 ZIP 读取，0 `run()` 调用，0 视频/图片读取，0 模型运行。** 修改范围只有本报告与本次独立合成测试回执；下一步只在 root 通知投影已取得后，独立核其字段范围和缺失项。
