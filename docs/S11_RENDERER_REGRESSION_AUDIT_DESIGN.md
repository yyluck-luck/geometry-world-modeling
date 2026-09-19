# S11 既有变体回归结果的不同脚本审计设计

准备时点：2026-09-05 21:58 UTC 后，在根任务通知冻结运行后编写。脚本只读确认原运行 `status=completed`、结束时间 `2026-09-05T21:58:47.197244+00:00`，才允许后续实际结果扫描。本稿在审计器首次执行前保存，已知道原运行自检全过；不称结果未知的预注册。

入口 `scripts/verify_s11_renderer_regression.py`，必填 `--results --protocol --freeze --output`。绑定 S11 执行冻结 SHA `d51522ebca03450293e23072b6c6f0a4656d1a7d61f4b8f99a051b1f392a20b3`，协议 SHA `0a427ad89df0a642300034f2b78c6e1548d38aba8e9dcffbaf31049c95609926`，原入口 SHA `a6fa8ee30fd4b72905f0c954b04193dcffb46c6b4cab91b01ed0dc22fc9b53c0`。

该代理也编写原回归入口，因此只称同作者的不同脚本复核。复用 SHA `4f422c968974a25c4d44f10ea6daea4ee84e13a4f62fbb2f8c07ff4bdf0ca9fe` 的既有 S10 审计器基础 Reader/Check、ZIP 核验、票权和已保存距离下的 NMS 分支逻辑。没有导入生产 runner、生产 validation、Torch、候选 renderer；不执行渲染、模型、GT、原图或性能实验。

检查分为五部分：

1. 完成门、冻结、原 13 源、316 输入、682 继承证据、全部冻结审查项及四个归档的精确成员、CRC、SHA；审计末复核每个读取原件不变。
2. 独立生成 192 条固定计划，核新 168 调用、继承 24、coverage 无缺失或重复；新 calls 目录恰有 336 文件，旧 S10 calls 恰有 672 文件。只读旧全部文件 SHA，解码旧 24 份初始候选 NPZ 作为继承输出，不重跑其余旧调用。
3. 192 条实际/继承输出的 576 个数组，逐个与各自原封存 render 的 shape、dtype、C bytes 完全相同，包括正负零。完整 official trace、票权/次数、排序/NMS、最终 ID 对照原参考。另从 192 个原缓冲区与来源映射累票并回放记录距离下的 NMS 分支；相机距离不重新计算。
4. 直接从 48 个地图数组与来源编码重算 documented memory digest。从保存的预测 poses、固定相机内参、坐标转换、占位上下文和参考初始阈值，独立构造 168 条预期 state_identity，逐项对照 initial 与 state_after，并核 state_before SHA。此处不调用原 Memory 构造器、state_identity 或初始化函数。阈值仍对照原记录，不把它称为重新计算全部相机距离。
5. 从完整覆盖重建 summary 的全部数值与布尔字段，核无单次性能时间、零原 renderer、零 warmup 和环境记录。AST 只验证原方法恢复及单调用点/无性能时钟，沿用已纠正的去缩进方法，避免类内 docstring 字符串缩进误比。

所有输入为只读，只有全新审计输出目录可写，失败保留 verification、异常和两个审计源码快照；不得覆盖失败目录。结果只扩展已有两场景、24 相关查询的软件一致性证据，不声称 192 个独立查询、未见泛化、速度、创新或完整视频质量。历史运行时点/资源、未保存的任意内部对象仍属于记录证据，不冒称操作系统追踪或完整内存快照。
