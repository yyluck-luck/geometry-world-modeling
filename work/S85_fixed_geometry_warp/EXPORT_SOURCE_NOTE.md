# S85 显示源码交付

实际准备时间：2026-09-10T20:28:50.057249+00:00。

- export_visuals.py SHA256：1b79aac9638eba4deea7b4ddb2c7054ec24e684e25d18d07e35c5d7baebb34fe。
- EXPORT_CONTRACT.json SHA256：ec54bc031f431f1a9c6f16d9735e6cb07697db0b677f0df26cb945621e1c9cc0。
- 当前仅完成 AST 语法解析；没有运行或导入导出器，没有读取科学数组，没有生成 PNG。
- 本次准备只读科学回执 JSON 来绑定四份 TARGET 身份；字体只作显示资源读取并绑定 SHA。之后执行会整份读取四个 NPZ 字节核 SHA，但仅解码 warp_rgb/mask。
- 输出为 12 张逐目标 PNG（原重投影、mask、孔洞标注）及 1 张 2×4 总览，原生 576×576，不重算投影、不缩放、不修改科学输入。总览为 2364×1346。
- 源码准备前的一次工具 JS 解析失败未执行任何文件写入或科学计算；当前源码与合同另行成功落盘。
- RESULT_EXPLANATION_TEMPLATE.md 是待填说明，未预写可视观察、科学接受或新生成结果。既有科学投影/复算的完成状态由 root 单独负责。

待 root 完整核读后唯一执行命令：

    '/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/.venv-cut3r/bin/python' -I '/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S85_fixed_geometry_warp/export_visuals.py'

脚本自行创建 visuals_01，若已存在则停止。每份 PNG 写后按字节读回并存 SHA/尺寸/模式；后续逐图视觉检查另做。资源边界为 120 秒、采样峰内存 1 GiB、输出 64 MiB；不是新增科学评分。原执行回执的 pending-review 字段按原文记录，不能覆盖后续独立/root接受记录。
