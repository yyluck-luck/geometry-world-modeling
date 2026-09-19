# S8 时间戳派生器准备说明

新程序：`scripts/prepare_tum_timestamp_derivative.py`。按 `S8_TIMESTAMP_AMENDMENT_REVIEW.md` 全文合同实现，只新增文件，不修改旧脚本、结果、V1协议或原数据。当前仅通过小型合成fixture和帮助/编译检查；没有处理真实TUM数据、读取新图片或解析任何GT位姿数值。V2协议和执行源码仍由根任务独立审查、冻结后运行。

## 输入与输出

```text
.venv/bin/python scripts/prepare_tum_timestamp_derivative.py --source ORIGINAL/rgbd_dataset_freiburg2_desk --output FRESH_PARENT --protocol V2_PROTOCOL.md --design-freeze V2_DESIGN_FREEZE.json
```

`--output` 为全新父目录，不能和原source互相包含，不能是现存目录或悬空符号链接。其内产生 `rgbd_dataset_freiburg2_desk/`、`derivation_metadata.json`、README、协议/设计冻结原字节副本和处理脚本快照。派生数据根保持原文件及目录相对路径集合，不在其中附加说明文件；父目录README明确这是本研究派生版本，不能冒称原封官方解压树或“官方真值已修复”。

设计冻结至少提供 `protocol_sha256`、`frozen_utc`、`original_gt_sha256`、`source_sha256`。后者必须包含本脚本，可用项目相对路径或绝对路径；所有提供的源哈希均在运行前后核验。源路径别名重复拒绝。实际原GT哈希在完整源清单及读取前绑定original_gt_sha256，结束时再独立核原GT未变。

## 明确的数值语义

只把每条GT数据行的第一个byte token转换为Python float（二进制64位），要求有限值和8列结构。其余7个pose token仅计数，绝不转换数值或比较质量。空白/注释行按原始bytes保留。扫描整个GT后以float相等作为重复键，不按RGB范围、窗口或pose token内容限制扫描。

排除规则严格为 `any(abs(t - d) <= 0.051 for d in all_duplicate_float_timestamps)`。实现逐组直接计算该表达式，不用Decimal、isclose、端点舍入或额外容差；重叠邻域取并集。原行顺序与保留行每个byte均不变，不排序补行或重写位姿。派生GT须非空，保留时间严格递增/唯一；否则失败。每个重复键记录最终最近保留左右邻点，二者均存在时要求差严格大于0.100；一侧缺失则标具体轨迹边界。间隙不可是非有限值。

`gt_derivation`记录重复组、每条排除行的原行号/时间/raw_line_sha256/覆盖它的重复键；保留GT行记录原/新行号、时间、原行SHA，`retained_line_mapping`另覆盖注释和空白行。记录原/派生总行数和GT数据行数、原/新GT SHA、每组屏障与校验标志。发布前再次从原GT按声明排除行号做字节减法，与派生文件逐字节比较。

## 全树复制与失败保留

递归扫描原树，任何symlink、FIFO或其他非普通文件均拒绝。每个普通文件在读取前后核inode/大小/mtime稳定，并计算全SHA；空目录也纳入路径集合。除了GT生成新保留行内容，其余文件全部用新建独立文件逐字节复制，不硬链接、不解码图像；复制流SHA、落盘SHA和新inode都检查。

完成后再读取全部原/新文件，核原始目录/文件成员、SHA、大小与inode前后相同；派生成员集相同，所有非GT字节与大小相同，所有派生文件与对应原件inode不同。原树没有任何写入操作。`files`保存完整来源/目标身份；`source_inventory_before/after`与`derived_inventory`支持独立核查。

进入新输出目录后的异常保存failed、失败阶段、traceback、实际开始/结束时间及已得到记录，README标尚未完成；重试必须用新目录。输入路径不存在、根目录为symlink或目标已存在等初始拒绝发生在创建输出前，不改原源或先前目录。不会选择新窗口、调用模型或因派生数据不足而放宽规则。

## 小型fixture结果

`tests/test_tum_timestamp_derivative.py`共6项通过：所有重复组/重叠并集与CRLF原字节；0.051闭区间及相邻binary64值的严格区分；整个GT扫描与边界情形；坏结构/非有限时间及无序/空输出失败；完整合成目录的独立复制与全SHA/inode；symlink及格式失败留痕。fixture刻意使用7个非数字pose token和不是有效PNG的图片文件字节，证明此阶段既不解析pose数值，也不解码图片。它们不是新场景研究结果。
