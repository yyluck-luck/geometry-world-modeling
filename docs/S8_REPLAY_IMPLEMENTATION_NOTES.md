# S8 replay 实施说明（真实实验运行前）

本文件描述 `scripts/run_s8_replay.py` 的新实现，不报告 S8 实验结果。本次实现没有运行真实图像/模型实验，没有下载数据，没有改动 S0–S7 冻结源码或旧结果。根任务须独立审查并冻结新执行源码后再运行。

## 调用与冻结契约

使用分析环境 `.venv/bin/python`，参数均必填：

```text
scripts/run_s8_replay.py --manifest INPUTS_JSON --protocol PROTOCOL_MD --freeze EXECUTION_FREEZE_JSON --runs NEW_S8_MODEL_DIRECTORY --data NEW_TUM_DATASET_DIRECTORY --output FRESH_RESULT_DIRECTORY
```

`--runs` 是 `run_s8_sequence.py` 成功的新 controller 输出。`--data` 是包含 rgb.txt、depth.txt、groundtruth.txt 及图像子目录的单一解包数据目录。输入、模型、数据可在项目外；旧绝对目录不是必需依赖。输出必须从未存在，包括悬空符号链接也拒绝；运行失败将状态、失败阶段、实际开始/结束时点及 traceback 写入新输出的 run_metadata.json，保留已产生文件。失败后的重试需另一个目录。

协议需有恰好一个 `s8-controller-json` 和一个 `s8-replay-json` 围栏。后者全部固定字段见新脚本 `REPLAY_CONTRACT`；额外解释字段允许，但不得改已声明参数。三个块均为 test；stride8/12、width160、四图、四读出、20历史+4查询、默认K、除5000、不重复1.031、RGB时间GT及0.1秒最大插值间隙均明确声明。

执行冻结JSON至少包含：

- `protocol_sha256`：所给协议字节哈希。
- `manifest_sha256`：本轮72图清单字节哈希。
- `execution_source_sha256`：源路径→哈希，至少覆盖脚本 `REQUIRED_SOURCES` 的20项（包括被间接导入的 experiment_io.py）；项目相对路径和绝对路径均支持，路径别名重复拒绝。
- `measurement_file_sha256`：测量来源路径→哈希，必须含所给新数据目录的 groundtruth.txt；可附rgb.txt/depth.txt。输入PNG的72个RGB及72个depth哈希来自manifest，controller/replay均重查。

先冻结采样设计，再下载并冻结清单/执行代码，是两个时点。replay只要求拿到最终执行冻结；完整时序由协议、采样/执行冻结和主账保留。测量文件的字节哈希不会解码深度；采样阶段可用GT时间戳判断可插值范围，不能声称从未访问GT文件。

## 预测和新 controller 的检查

新脚本读取新 controller 的 sequence_metadata、冻结输入/协议副本、controller/runner快照、每块元数据及 s8_output_verification。要求 controller complete/ok、3块/504有限数组、CPU8线程/seed0、224 linear、固定提交/权重、精度语义和兼容适配证据、每块成功且不超900秒/16GiB记录预算。实际168×3输出数组的键/形状/dtype/有限性/min/max/张量哈希重新核对，三个块的完整模型身份严格相同。

查询四组flag、25个状态快照计数、历史锚点20、两个状态字段×4次只读查询的schema/有限性/严格不变及记录哈希使用新controller纯验证函数检查。潜在状态原张量没有归档，不能把此审查称重新运行张量比较。此过程不重跑模型，不调用旧 `load_run` 中的旧项目测量/下载固定路径，不进行S5历史对比。

## 预测阶段产物和封存

复用未改 S6 normalize_predictions、surfel和selector，以及未改 S7 observations、record_path、replay、decision_trace。首图正预测Z中位数的倒数只用于无量纲归一化；3份 blockN_normalized_input.npz 保留首图归一化depth和24个预测pose。

每个 blockN_strideS 案例保留：

- observations.npz：每条(frame,u,v)身份、位置/法线/半径/真实RGB颜色、逐帧偏移。
- 两条 A0/A1 事件、直接建图trace、直接地图NPZ及来源映射。旧trace中 `_m` 名称保留原函数输出，值处于预测归一化单位，不是测量米；case的 prediction_normalization 记录换算因子。
- A0P0/A0P1/A1P0/A1P1 四图与来源。两个对角逐数组、完整digest、来源字典严格等于本轮直接记录地图；固定A时P0/P1非位置属性及来源严格相同。
- 每图×尾4查询共16份原renderer输出；prediction_only_selection.json 包含所有原票权/候选及完整读出决定。全轮96次独立decision_trace的有序ID严格等于原official输出；四种读出都需4个互不重复的历史ID；全候选读出在四图间严格相同。每次查询前后显式memory digest不变。

每例全部当时文件逐字节封存，3份归一化输入另有根目录封存表。只有6例都完成且哈希核验通过后，写 selections_sealed_utc，再进入 measurement_scoring。此脚本第一处 read_trajectory 和第一处深度PNG解码均在此边界后，并记录 first_gt_pose_decode_utc/first_depth_decode_utc。

## 新测量与分母

所有72个深度PNG从原图重新解码除5000，经原S6 measured_target的5×5/50mm有效筛选与224裁剪，RGB时刻GT插值上限0.1秒；另核同帧depth时刻也有合法插值支持。每块仅首图拟合 `first_frame_scale(normalized_first_depth, target0, mask0)`；测量尺度仅在选择封存后用于地图评分。blockN_measurements.npz 保留24张target/mask、24个GT pose、RGB/depth时刻和RGB插值间隙；几何裁剪参数另存JSON。

支持掩码用原 `run_s6_memory.measured_support` 从新测量/GT重建；投影用原 project_depth。每个读出先计算支持像素整数，再除有效目标整数分母；保存 supported_pixels、support。`records.json` 共24条查询×密度记录、384条图×读出条件，实际不同查询12，全部外部test。

每例每查询同时保存 `common_four` 与 `common_diagonal` 掩码。四图geometry均含四图共同误差/自身误差/自身覆盖；对角两图另含 common_diagonal 误差。记录两种共同像素数，不混为一个评分集合。零有效target失败并保留；零共同像素由原 residual_stats 写 n=0，MAE/中位数/p90等null，不崩溃、不写0或NaN冒充好结果。

收尾重新验证所有预测封存及冻结源字节；experiment_source.zip包含执行源、协议/冻结、清单、新controller/模型记录和新GT轨迹来源。项目外源使用 `external/父目录路径哈希/文件名` 安全归档；保存原路径→归档名对应。归档实际字节另核哈希后写入，避免固定relative_to(ROOT)限制。大权重和PNG不复制进此源ZIP，PNG哈希已记录。

## 实施验证和范围

新增 `tests/test_s8_replay.py` 5项小型边界检查已通过：禁止事后改参数/二次深度校正、根输入及各例封存变更检测、项目外同名文件安全归档、预检失败保留且未读GT/图片、零共同像素null语义。这里只使用临时字节/小数组，不是科研样本。脚本编译和 `--help` 通过；未运行真实模型或新场景评分。独立审查、执行冻结、运行、原始数据独立复算仍由根任务继续。
