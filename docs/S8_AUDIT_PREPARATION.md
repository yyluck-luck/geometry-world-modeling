# S8 独立审计准备记录

结论：**准备检查 PASS；真实 S8 审计未运行。** 本记录形成于北京时间 2026-09-06 02:15:41（UTC 2026-09-05 18:15:41）。当前只完成审计实现、旧已核文件的只读格式检查和人工边界样例；没有读取新 fr2desk 数据、没有读取其未完成评分、没有运行模型或 surfel renderer。本记录不能作为 S8 研究结果。

## 交付与身份

新入口为 `scripts/verify_s8_results.py`，分析环境为项目 `.venv/bin/python`。七个必填参数是 `--manifest --protocol --freeze --runs --data --results --output`。其中 `--runs` 指新模型 controller 目录，`--results` 指新 event replay 完成目录，`--output` 必须是从未存在的新审计目录，包括悬空符号链接也拒绝。

当前字节 SHA256：

| 文件 | SHA256 |
|---|---|
| `scripts/verify_s8_results.py` | `6ae1ee6fa5373a378cacb53babb1475a12b669419d8ebe96529aab079ba72878` |
| `scripts/verify_s6_scores.py` | `bd6bd1d88c3297e89cd556fd6d6c4b3517f2828562aea272f23ce0069ce159a2` |
| `scripts/verify_s7_replay.py` | `506ad1e33a053b2d9d0fabe69fd2a611f48ce4b7201e860fa98c2f60e5fd42e0` |
| `docs/S8_EXTERNAL_SCENE_PROTOCOL.md` | `5b6563643d4deb69dd7f66789ebf0f0620666cac372858831aa96fd376186df6` |
| `work/s8_audit_preparation/preparation_checks.json` | `55c333f14386dd9e3df3a46bf6fe976c98751a7d10a1477ce3540f43f21c3a62` |

两个旧独立审计源保持不变，并在新入口中固定其已核版本哈希。没有导入生产 `run_s8_replay`、`run_s6_memory`、`s7_event_replay` 或其他生产评分模块。执行冻结须在下载、取样和 QA 之后按真实时点创建，包含 `frozen_utc`、协议/清单 SHA、执行源 SHA 与测量来源 SHA；不得把现在的设计冻结误作最终执行冻结。

## 已做的准备检查

编译及 `--help` 均通过。`work/s8_audit_preparation/check_preparation.py` 在北京时间 02:14:13.472019 完成以下四组检查，明细保存在上述 JSON：

1. 独立 GT 包装函数：精确首行、精确内部行、孤立末行直接由四元数和平移构造位姿，gap=0；非精确合法时刻继续旧独立 SLERP；外推或超过 0.1 秒间隙拒绝。旧 S6 函数未修改。
2. 人工时间戳样例：1,334 对 RGB/depth，独立生成 4 个合法固定时长窗口并选择 `[0,1,3]`，验证首次/中间向下取整/末次规则。样例不是研究样本。
3. 未完成入口保护：仅给 `running` 状态文件，其他数据和协议路径全部不存在；入口先以退出码 2 拒绝，未创建输出目录。该检查没有新 S8 数据路径。
4. 旧已核 S6/S7 block0 格式：仅读取 28 个旧源文件，其中 20 张旧 RGB。stride8/12 的独立接受身份、颜色、偏移、过滤计数均精确相同；位置最大差 `4.440892098500626e-16`，法线最大差 `2.220446049250313e-16`，半径最大差 0。105 条旧状态/staging 格式检查通过。所有 28 个旧文件 SHA 在检查前后相同。

所有几何浮点比较继续使用固定 `atol=1e-9, rtol=1e-10`。没有放宽容差或修改旧结果。新数据上尚未证明这些检查都会通过。

另由 S8 replay 实现代理进行有界静态同行检查：已核生产字段、每例 35 项预测封存成员、整数支持分子、空共同掩码的 null 语义、GT 精确端点、状态/RSS 字段和事件 trace 对应。未报告必修错误；该同行复查没有读取新数据或运行真实审计。

## 新运行完成后将实际核查的范围

入口先只读取新 replay 的 `run_metadata.json`，要求 `status=completed` 且 `phase=complete`；否则不读取清单、PNG、GT、模型数组或评分，也不生成最终审计。该入口条件不是一个已经得到的 S8 结论。

- 从原 RGB/depth 时间戳表重新进行全表唯一贪心匹配，再按双时间同一 GT 闭区间、连续段、8.840 秒窗口、最近采样及去重条件独立核全部实际选择。对 72 个 RGB 与 72 个 depth 身份逐项核路径、inode、SHA、时间和字节数的唯一性；真实 RGB 解码用于尺寸和历史观测颜色核对。
- 从 72 个原深度 PNG 重建裁剪 target/mask，从新 GT 重建 RGB 时刻位姿及间隙，并核 72 个 depth 时刻合法性。与三份保存 `blockN_measurements.npz` 比较：target、mask、时刻和 gap 精确，位姿保持原浮点容差。首帧尺度只按独立 S6 公式计算，核尺度与有效像素数；不重新拟合其他帧。
- 从 504 个保存预测数组核 shape/dtype/有限性、范围、张量 SHA，独立重算三块预测归一化。由归一化预测深度、置信度及原 RGB 独立重建六例接受像素和观测属性，再以已逐项核过的保存 observations 对 12 条关联路径做穷举匹配检查；独立重放 24 幅地图、来源、count 和出生属性。地图及来源精确相同；固定 A 两臂非位置属性精确相同；对角与本轮直接建图保存结果精确相同。
- 从保存的 96 份原 render 独立重算票权、候选分配及 384 个完整排序/NMS/纯去 NMS 决定；保留展开候选重复 ID、float32 排序及原首项双加语义。未重新运行 surfel polygon renderer。
- 24 个查询×密度条件均从原测量重算 support/target/valid；四图的中心点投影、四图共同掩码及对角共同掩码分别重算。384 个支持分子整数与最终分数核精确相同；几何指标及交互用独立统计公式，仍按原容差核查。零共同像素保留 n=0 与 null。
- 核最终执行冻结、源 ZIP、源原路径、三份 normalized seal、六例完整预测 seal、controller/runner 源与快照、模型输入命令、504 数组记录、全部查询状态 flags/8 条状态记录、记录资源上限和时序。每个读取的原文件在结束时重查 SHA。

审计输出计划为 `verification.json`、完整 `records.json`、两密度总体 `aggregate.json`、六组 `aggregate_by_block.json`、尺度/取样摘要，以及独立测量、地图/来源、决定和投影文件。每次运行保存审计源及两个固定 helper 的快照。失败将保留检查列表、原容差与 traceback；下一次须用新输出目录。

## 后续接续

使用 `docs/S8_RUNBOOK.md` 的实际步骤，等最终执行冻结、新 controller 成功和新 replay 完成后，根任务可执行以下预定路径命令；路径或运行目录若发生变化，应传实际完成目录。现在不要执行：

```text
.venv/bin/python scripts/verify_s8_results.py \
  --manifest data/cut3r/S8_fr2desk_inputs/S8_inputs.json \
  --protocol docs/S8_EXTERNAL_SCENE_PROTOCOL.md \
  --freeze docs/S8_EXECUTION_FREEZE.json \
  --runs results/S8_cut3r_cpu \
  --data data/tum/fr2_desk_download/extracted/rgbd_dataset_freiburg2_desk \
  --results results/S8_event_replay \
  --output results/S8_independent_audit
```

若失败，应查出是审计实现/字段问题还是真实不一致，完整保留首次失败；不能默认通过，也不能调宽容差。只有独立审计实际通过并与主分析逐值核对后，才撰写 S8 结果结论。

范围限制仍然存在：模型推理和 surfel renderer 没有重跑；内部状态原张量未保存，只能核已保存完整记录，不能声称再次比较原张量；时序证据为记录与归档源码，不能恢复历史文件访问轨迹。三个块只有一个新增物理场景，12 个相关查询与 384 个条件不是 384 次独立重复。几何和参考支持指标不能当作生成视频质量。
