# S8 取样审计入口独立准备审查

结论：**PASS，当前没有剩余必修问题。真实新场景取样审计尚未由本审查运行。** 审查时点为北京时间 2026-09-06 02:49:47（UTC 2026-09-05 18:49:47）。本次只读审查新入口和既有固定数学，用临时人工数据验证；没有读取真实新 fr2desk 数据、压缩包或 partial，没有启动下载、模型、评分或 RGB QA。

## 审查对象与字节身份

- `scripts/verify_s8_sampling.py`：`ae220927afd53337b4154c84fe62c708f1181de6dfecf77e8a5fd1fcd0419e66`。
- 固定独立取样数学 `scripts/verify_s8_results.py`：`6ae1ee6fa5373a378cacb53babb1475a12b669419d8ebe96529aab079ba72878`，保持不变。
- 最终入口快照 `work/s8_sampling_audit_review/final_auditor_snapshot.py` 与被审入口 SHA 完全相同。
- 19 个最终样例结果 `work/s8_sampling_audit_review/final_checks.json`：`0c47084e041d61d75b113bace2495c76cf7013edd9183f0235d411c9b69dbd5a`。

审查者没有直接修改被审入口、取样协议、生产取样代码或主账。发现的问题由根任务在该新入口尚未真实运行、尚未冻结前修正。

## 已发现并修正的问题

初读版本核了实际 RGB/depth 配对与 SHA，但遗漏逐帧 `target_timestamp` / `snap_error_seconds` 以及块的 nominal 时间、实际跨度、RGB 间隔和双传感器偏移。根任务补齐这些字段，并补上 sampling 协议/源 SHA、未解码声明和全部读取文件的开始/结束字节稳定核对。

第一份测试快照已经包含上述首批修正（SHA `4832d317051ecdfcf6e8de9f827501ecad4648d97db8bddfe0b051ab11e791e5`）。该版仍允许把接受窗口的 RGB 时间副本改成 999，或把 frame0 写成 `false` 后通过。根任务随后补齐接受窗口 index/RGB 时间副本、身份索引严格整数类型、schema/runner、archive SHA 跨记录一致性、原文本数量和 72 入选数量；设计绑定源也加入结束 SHA 复查。原测试快照与发现记录保存在 `work/s8_sampling_audit_review/original_auditor_snapshot.py` 和 `original_checks.json`，没有覆盖。

最终上述错误均被拒绝。没有放宽数值比较，旧固定数学与生产协议未修改。

## 纯时间戳边界及人工测试

GT 读取函数只将每个 8 列记录的第 1 个 token 转为浮点；其余 7 个 token 不解释为平移或四元数。传给独立 `sampling_from_timestamps` 的数组为 N×1；该函数只使用 `trajectory[:,0]`，无需 GT 位姿列。图片仅参与安全路径、inode、文件字节与 SHA 读取；没有像素解码调用。导入含图像函数的审计模块不会执行那些函数。

临时合法样例使用 1,334 对时间记录、4,001×1 的 GT 时间数组和四个接受窗口，首中末索引为 `[0,1,3]`。GT 的其余 7 列刻意写成非数字字符串，144 个入选“图片”文件刻意只含唯一的非图像字节。合法例仍通过 1,524 条检查，这与静态代码共同支持“本入口没有解析 GT 位姿或解码图像”的范围判断。人工窗口 metadata 用生产 `plan_windows` 从人工时间记录生成，以覆盖真实保存 schema；被审入口仍只执行独立取样实现。

最终 19 个样例：1 个合法例通过，以下 18 个负例全部按预期拒绝。

| 负例 | 首个相关拒绝检查 |
|---|---|
| 配对索引错误 | `B0F0/index` |
| 中间窗口选择错误 | `block1/window` |
| 候选窗口目标时间错误 | `window0/targets` |
| 原文件字节改变 | `B0F0/rgb/sha` |
| 入选帧目标时间错误 | `B0F0/target` |
| 入选帧采样误差错误 | `B0F0/snap_error` |
| 块时间/间隔摘要错误 | `block0/nominal_times` |
| sampling 协议/来源不一致 | `sampling_protocol_sha` |
| 接受窗口 RGB 时间副本错误 | `window0/rgb_timestamps` |
| 帧号用布尔值冒作整数 | `B0F0/integer_fields` |
| 接受窗口 index 错误 | `window0/index` |
| manifest schema 错误 | `manifest_schema_runner` |
| runner SHA 错误 | `manifest_schema_runner` |
| 两份 archive SHA 不一致 | `archive_hash_cross_record_consistency` |
| 文本记录数量错误 | `metadata_table_counts` |
| 块号用布尔值冒作整数 | `block_integer_ids` |
| 匹配号用布尔值冒作整数 | `B0F0/integer_fields` |
| 审计途中修改已读时间表 | `source_unchanged/.../rgb.txt` |

有一次测试装置本身需要修正：中途改文件的 hook 最初直接比较 macOS 临时 `/var` 与解析后的 `/private/var` 路径，未触发，因此测试总断言失败。仅将测试 hook 比较改为 `resolve()` 并加“hook 确已触发”断言；被审入口未改。保留 `check_final_attempt1_temp_path.py` 和 `fixture_attempt1_temp_path.json`，最终测试脚本为 `check_final.py`。这是人工测试装置问题，不是 S8 实验失败。

## 实际覆盖与后续使用边界

入口独立从全部 RGB/depth 时间表做严格 20ms 内全候选配对、唯一贪心匹配，GT 闭区间/缺口及双时间可用性判断、连续段、固定 8.840 秒窗口、最近 24 目标、50ms 上限、去重、窗间隔与首中末选择。它核全部**接受窗口**的数量、顺序、时间、配对、目标与误差，再核实际三块 72 帧的对应字段和原文件 SHA/唯一性。结束重新核设计、协议、清单、sampling 记录、文本、数学源与 144 个入选文件字节。

`candidate_attempts`、`excluded_pairs`、叙述性的 segment/GT 区间编号及相关解释日志没有逐项复算。独立算法重建得到的全部接受窗与实际选择仍被核对，不能因此把未核的解释日志称为已独立重放。TGZ 的 archive SHA 在此只核 sampling/manifest 两份记录一致且格式有效；没有重新读取完整 TGZ 或验证 gzip/tar，完整下载器证据仍由根任务另核。

本入口需要实际取样 `status=completed`，在 RGB QA 前执行；不受评分审计的“新 replay completed”限制，因为它不读取像素、GT 位姿或分数。新输出目录必须不存在，失败状态与 traceback 会保留。本审查的 PASS 只表明该入口已通过有界准备审查，不能代替实际新场景取样审计通过，更不能代替 PNG/GT 评分审计。
