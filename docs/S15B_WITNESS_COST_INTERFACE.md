# S15B照片证据计算器接口

入口：`scripts/s15b_witness_costs.py`。本程序实现**已有两候选照片代价与筛选规则的探索组件**，不训练、不运行模型、不读取传感器深度或最后四张目标RGB，不产生准确率或新颖性结论。

```bash
.venv-cut3r/bin/python scripts/s15b_witness_costs.py \
  --manifest /absolute/path/witness_manifest.json \
  --output-dir /absolute/path/fresh_output_directory
```

`--output` 是 `--output-dir` 的兼容别名。输出目录必须事先不存在，失败产物原地保留。父任务可继续套用已有外部caller；其runner/python/identities字段由父任务提供，不属于本脚本自行遍历的读取授权。

## Manifest

```json
{
  "schema": "s15b-witness-costs-v1",
  "contract": "用Python导入模块CONTRACT原样写入对象，此处字符串只示意，不可直接执行",
  "proposal_seal": {"path": "/absolute/seal.json", "sha256": "..."},
  "proposal_npz": {"path": "/absolute/proposals.npz", "sha256": "..."},
  "source_images": [
    {"source_id": 0, "path": "/absolute/source0.png", "sha256": "..."},
    {"source_id": 3, "path": "/absolute/source3.png", "sha256": "..."},
    {"source_id": 6, "path": "/absolute/source6.png", "sha256": "..."},
    {"source_id": 9, "path": "/absolute/source9.png", "sha256": "..."}
  ],
  "witness_images": [
    {"frame_id": 12, "path": "/absolute/witness12.png", "sha256": "..."}
  ]
}
```

示意中的witness列表须完整8项、frame_id严格12…19；不能直接运行上述缩略例子。所有路径必须是已解析的绝对规范路径，十四份输入的路径不得重复。source/witness只接受PNG角色，原分辨率固定640×480。读取范围仅为manifest、脚本自身、seal、proposal NPZ和12张明确RGB，程序不递归打开seal里其他链接。

**封存职责：** 本脚本只核seal文件SHA，并不懂父任务全部seal schema；父任务冻结器与不同作者前审必须确认seal绑定这份proposal、共同相机、前缀和图像身份。脚本不重新估计相机/尺度，也不能凭数组值认证来源时序。任何六键适配NPZ须在见证RGB解码前，由父任务从已经封存的提案与已允许相机数组确定性生成并新封存，不能重拟合或读取深度答案。

## 唯一允许的NPZ字段

所有数组必须为浮点类型，以`allow_pickle=False`读取，并在计算中转float64。只接受恰好以下六键；不读取置信head或其他存档。

| 键 | 形状 | 含义 |
|---|---|---|
| old_self_z | (4,224,224) | 来源0/3/6/9旧提案的光轴z，模型单位 |
| new_self_z | (4,224,224) | 同来源同像素新提案，模型单位 |
| source_c2w | (4,4,4) | 两候选共用的给定source RGB时刻相机，已变换到共同模型坐标 |
| witness_c2w | (8,4,4) | 见证12…19 RGB时刻相机，经同一冻结A/s/c到模型坐标 |
| K | (3,3) | 224裁剪后共用的物理pinhole内参 |
| scale_model_per_meter | 标量() | 已冻结历史尺度，正有限；用于单位审查和来源记录，照片投影本身不再除以s |

pose必须有限、底行约[0,0,0,1]、旋转正交且det约+1（atol1e-5）。不强行正交化、不重对齐。depth提案允许非有限/非正值；它们进入invalid支持，不被当成成功预测。

## 固定照片和投影规则

每张640×480 PNG按PIL `convert("RGB") → resize((299,224), LANCZOS) → crop((37,0,261,224)) → convert("L")`。Census为5×5窗口，按dy从-2至2、dx从-2至2行序排除中心，邻居严格小于中心置1，共24位；边缘不作可评分中心。

source中心必须行列均在[2,221]。每个候选从z、K和source c2w物理反投影为world XYZ，再用witness c2w的刚体逆投到见证；先判断正z与有限值，按`floor(pixel+0.5)`取整，两个候选的见证中心都在[2,221]时才有同支持观察。不存在z-buffer或可见性过滤，投影在画内不等于实际可见。

同一source pixel用自身Census分别与两候选在同一witness落点处Census求Hamming整数。valid成本0…24，invalid哨兵255；统计中哨兵一律不参与求和。

## 全部784块和三条规则

来源4张×每张14×14个非重叠16×16块，共784块，无观察也输出。每块/每个见证保存paired_count、old_hamming_sum、new_hamming_sum。paired_count计**像素×见证观察**，同一像素在4张图出现算4次，不是独立样本数。

- `pool_new`：全部8见证中sum_old>sum_new才更新；无观察或tie保留旧。这条端点组件不另加64门槛，严格与同支持域整数二候选argmin等价。
- `split_new`：前4与后4见证组各count≥64，且两组均sum_old>sum_new才更新；其他保留旧。
- `matched_absolute_new`：只在与split同样的两组count≥64集合中，按全部8张的newsum/count从小到大取K块，K等于split接受数。用`fractions.Fraction`精确比较；tie按source_id、patch_row、patch_col。它是给绝对成本基线K的匹配诊断，不是独立可部署的门控。

mask对被接受的**整块16×16**置真，包括该块中没有Census证据的个别像素；下游输出仍需共同几何有效性规则，不能把这个mask当“该块所有像素被观测证实”。每块原提案、像素/照片来源身份由父任务保持不变。

## 输出和资源

| 文件 | 内容 |
|---|---|
| paired_costs.npz | paired_valid bool、old_hamming/new_hamming uint8，均(4,8,224,224)，invalid=255 |
| rule_masks.npz | 三个bool数组，均(4,224,224) |
| patches.csv / patches.json | 784行，完整整数观察数/总量及逐见证量、资格、动作、pool/argmin一致标记 |
| summary.json | 完整分母、支持块数、各动作数、整数成本总量、规则等价、证据边界 |
| run_metadata.json | 实际时刻、输入输出SHA、Python/NumPy/Pillow、CPU/RSS、解码计数、SUCCESS或FAIL及异常 |

没有用图像均值舍入决定动作；summary不把照片cost称深度误差。NPZ使用compressed保存。内部逐步检查CPU≤600秒、进程高水位RSS≤8GiB，并设600秒墙钟alarm；这不是操作系统硬RSS隔离，父任务外部monitor应继续施加约束。正常输入大小远低于此上限。

## 当前验证状态

仅做了小范围人工构造检查：严格Census与独立Python bit_count；恒等/平移/半像素/负深度/NaN/Inf投影；784块完整分母、两组64边界与同K不同选择；精确均值tie；人工12张恒定PNG＋六键NPZ全流程、解码前SHA拒绝及旧目录保护。最终版本结果见`work/S15B_witness_preparation/metadata_scope_version/receipt.json`；此前仅缺少seal职责说明字段的metadata版本检查保留在原`receipt.json`。这包括12张**程序生成的人工常量图片**，不是12张真实实验照片。

第一次人工tie样例遗漏了另一个成本更低的合法候选，程序正确选它但测试预期错误；只修复测试数据，原失败见`artificial_initial_failure.json`。本实现交付时没有读取任何真实RGB/NPZ/GT，也没有运行模型。父任务负责真实前审、封存、一次实跑与独立传感器评价。

