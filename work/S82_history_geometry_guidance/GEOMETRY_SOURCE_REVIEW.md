# S82 四历史原始前向：精确实现独立前审

记录 UTC：2026-09-10T18:16:59.297804+00:00

**结论：PASS_FOR_ONE_BOUNDED_RAW_FOUR_HISTORY_ATTEMPT。无剩余执行 blocker；root 核读本结论后可按本合同默认入口执行一次。** 限定原始六 head 前向归档；不授权 optimizer、render、GT/传感器深度、新生成、重试或扩大输入。审查者不同于实现作者，已全文核冻结 runner 与合同的执行项；98 项源码身份全量当前哈希一致，语义审查限设计审查及下列实际调用链，不称98个源码全文通读。

## 精确绑定

- runner：`5f4c76b2ea475d66d3556b8a044f5f9a5f04972d1de12856d26d102d1eb6e49e`
- FOUR_HISTORY_CONTRACT.json：`cb60e53793942e9356eb1935544f490dc4a86be3be330bfdb2fe5abf285b0f46`
- 独立输出检查器：`6c8ab60aa9b222b05583041101bb8a18efb94911ff364add882f47faed57c6f2`

## 四项最小核验

1. **输入与坐标，PASS。** 合同固定历史 `[12,13,18,19]`，对 S68 已执行记录的路径/已记 SHA/大小一致。新生成槽映射 `[3,2,1,0]` 保持原 `[19,18,13,12]`。runner:202–235 用原 prepare_input 和原 load_images_for_eval；四 RGB 先各一次 hash-read，再由 PIL 各一次解码打开，回执明确两次文件访问而非一次。实际输入必须 `[1,3,384,512]`、true_shape384×512、CPU/float32/finite；NaN ray placeholder 由 ray_mask=False允许。已知 K/resize 矩阵只随预处理归档，不进入 raw 模型、不承诺米制；没有读取共同相机或评分数组。
2. **实际调用，PASS。** runner:239–267沿用本地 checkpoint的原 from_pretrained，精确size/mtime核旧已验身份，并分别记录 inherited SHA/current_sha256_recomputed=false；扫描+load两个文件open，不冒充新3.17GB hash。safe_globals与强制weights_only、原源码路径、98源码和包版本核查闭合。显式eval并逐模块读回；CPU/FP32输入/参数，原signed RoPE兼容层，原inference_recurrent装饰与内部精度规则保持。fresh状态由官方recurrent首帧创建，四张update=True/reset=False/revisit1；恰一次列表前向、四次head，没有额外optimizer/render/generation调用。
3. **输出，PASS。** runner:272–312每个raw六head先保存及哈希再检查shape/dtype/finite；失败不丢该完整head。官方 helper解码 wxyz+平移为 float32 c2w，另存四pose档。self/cross为独立head，未加入二者必须刚体相等的伪约束。rgb为模型head，不称新视频。技术完成状态明确不表示质量或创新。
4. **运行边界，PASS。** 新 execution_geometry_01 目录排他创建；默认入口一次，不循环重试、不覆盖旧结果。300秒/20GiB由父进程0.1秒采样、进程组终止、结束elapsed与worker ru_maxrss再核；此为有采样间隔的有界监督，不是硬虚拟内存保证。失败/超限与partial回执保留；网络与未列科学后缀文件有本地audit防误读。审查不把它说成针对恶意本地并发篡改的安全沙箱。

## 已实际运行的有限检查

`GEOMETRY_PREEXECUTION_SYNTHETIC.json`：按 runner的真实import顺序导入原模块，绑定98个source hash，未实例化模型；人工loader只构造四个384×512常量输入供原prepare_input，核ID/顺序/masks/update/reset/NaN ray/identity placeholder/true_shape。五个人工pose调用官方helper后与不同作者的float64归一化wxyz公式比较，最大绝对差2.220446049250313e-16；容差见输出计划。模型实例/forward/新科学文件读取/图片解码/网络均0。它不代替真实loader或head结果核验。

第一次独立小检查先导入camera再导入model，触发原模块循环import；已保留 `GEOMETRY_PRECHECK_IMPORT_ORDER_FAILURE.json`。这与冻结runner的model-first顺序不同，修正检查环境后通过，不修改runner、不把审查脚本次序失误当科研失败。

输出checker旧版根据未冻稿误设5条full hash-read，现改为4条RGB实际hash+checkpoint独立继承身份，并核五个路径各两次open。按root意见补预处理固定键/4ID/images与rgb01 shape、dtype、规范范围/逆归一化、四坐标矩阵对合同全等。无true_shape独立档案时用固定空间维度和receipt processed_wh，不虚造字段。旧检查器保留 `output_checker_archive_v1/`；自测V2仅五pose+零四元数，不宣称新增预处理条款已跑过真实数据或构造整套档案。

## 当前停止点

精确前审完成。此刻没有由本审查者读取新RGB/深度/NPZ数据、加载checkpoint或执行模型。下一步由root执行一次，结束后再授权本检查器读输出；只验组件完整与独立位姿解码。S81、旧125页报告及原实验结果未改。
