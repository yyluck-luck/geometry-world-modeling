# S90 GRC 数学 sanity test 独立复核

<!-- EXPERIMENT_NAME_LEGEND_20260912_BEGIN -->
> **S编号与具体试验名称说明（2026-09-12更新）**  
> 文档中的 `S86`–`S90` 是项目内部阶段编号，保留它们是为了让结果、日志和回执可以追溯；括号内是给新读者看的具体名称。编号不是论文术语、结果等级或“实验成功”的标志。S88–S90主要是数据资格/传输与协议审查，不能误读成模型性能实验。
>
> - **S86（单场景四目标几何条件注入基线实验）**：在一个已见静态场景、四个相关目标上，比较历史几何注入方式的真实生成链和RGB误差。
> - **S87（末端引导强度控制与多步引导必要性反例实验）**：复用S86缓存，比较末端处理强度与持续多步引导；它只检验该已见场景的有限反例，不验证GRC或长期几何收益。
> - **S88（RTMV相机JSON元数据与静态投影数据资格检查）**：核对归档身份、相机元数据和可访问的静态文件头；不是RGB-D配对性能实验。
> - **S89（RTMV配对数据TLS接续失败审查）**：记录两种TLS/传输接续尝试及其失败边界；失败本身不等于数据缺失或科学负结果。
> - **S90（RTMV归档配对数据恢复与索引协议审查）**：检查受限Range传输、归档成员身份、断点恢复和索引安全条件；已恢复的512B文件头不等于取得可用深度正文。
>
> 后续报告首次出现编号时应同时写成“**S86（单场景四目标几何条件注入基线实验）**”这类形式；后文可使用编号，但不要只写编号来替代试验名称。
<!-- EXPERIMENT_NAME_LEGEND_20260912_END -->


**复核时间：** 2026-09-11 18:14:31 +0800  
**复核者：** 独立 prior-code agent  
**目的：** 不覆盖主 agent 的结果，重新执行 `grc_math_sanity.py`，核对七个断言、结果字段、官方 CRC 导入路径和 commit 身份。

## 1. 独立执行与路径

执行命令：

```text
python3 grc_math_sanity.py \
  --output agents/math_repro_20260911_1814/GRC_MATH_SANITY_RESULTS.json
```

独立输出：

* JSON：`innovation_agent/agents/math_repro_20260911_1814/GRC_MATH_SANITY_RESULTS.json`
* stdout：`innovation_agent/agents/math_repro_20260911_1814/stdout.json`
* return code：`0`
* schema：`s90.grc_math_sanity.v1`
* status：`PASS`
* test count：`7`
* 独立运行时间（UTC）：`2026-09-11T10:14:31.573055+00:00` 至 `2026-09-11T10:14:31.782851+00:00`，耗时 `0.209796` 秒。

该运行没有使用真实视频、RGB-D 数据、模型权重或 GPU；它是合成数学反例加一个官方 CRC 辅助函数的执行。

## 2. 与主结果逐字段比较

主结果：`innovation_agent/GRC_MATH_SANITY_RESULTS.json`（UTC 10:13:02 运行）。独立运行读取两个 JSON 后的比较如下：

| 字段/检查 | 主结果 | 独立结果 | 判定 |
|---|---:|---:|---|
| `schema` | `s90.grc_math_sanity.v1` | `s90.grc_math_sanity.v1` | 一致 |
| 顶层 `status` | `PASS` | `PASS` | 一致 |
| `test_count` | 7 | 7 | 一致 |
| 七个 `tests` 对象 | 完整 | 完整 | **逐字段值一致** |
| `official_crc_file_sha256` | `ddf93c30cc703aa782c1d4f0201ca1360616b510000662cfbd0a506e91cc7546` | 同值 | 一致 |
| `official_crc_commit` | `3eff946390a8f188b1e5ab700fce21a66a215e7c` | 同值 | 一致 |
| `script_sha256_before_result_write` | `cc1753959a654cd553836f6096fc6edba18fc9ba0af8b8d23716c6a2116e3f66` | 同值 | 一致 |
| `started_utc`, `completed_utc`, `elapsed_seconds` | 10:13 运行 | 10:14 运行 | 预期不同 |

比较脚本的实际输出是 `tests_equal True`、`source_crc_sha_equal True`、`source_crc_commit_equal True`、`script_sha_equal True`。因此独立复核没有发现主结果被手工改写或测试结果不稳定。

结果 JSON 没有记录 Python、NumPy、SciPy 版本或平台架构；本次复核使用同一台本机环境，因而不能把它当作跨环境可复现性证据。若将 sanity test 纳入长期交接，建议在 receipt 中加入 `sys.version`、`platform.platform()`、`numpy.__version__` 和 `scipy.__version__`。

## 3. 七个测试的逐项检查

### 3.1 官方 CRC 全局参数

`grc_math_sanity.py:50--83` 通过 `importlib.util.spec_from_file_location` 直接加载
`sources/conformal-risk/core/get_lhat.py`，输入形状为 `(4, 5)` 的有界损失表。修正后的列风险为：

```text
[0.24, 0.31, 0.39, 0.58, 0.83]
```

`alpha=0.5, B=1.0` 时，官方函数返回 `lambda=0.2`；这与 pinned 源码第 8--12 行的 `mean -> finite-sample correction -> one index` 逻辑一致。直接比较 `git show HEAD:core/get_lhat.py` 与当前文件也通过，远程为 `https://github.com/aangelopoulos/conformal-risk.git`，HEAD 为 `3eff946390a8f188b1e5ab700fce21a66a215e7c`。

**边界：** 这只验证了“官方 helper 返回一个全局 `lambda`”的代码语义；没有验证 CRC 定理条件，也没有验证每条记忆的条件风险上界。JSON 中的 `interpretation_limit` 写法是正确的。

### 3.2 选择诱导的分布偏移

`grc_math_sanity.py:86--121` 构造每个 query 9 个误差 `0.05` 的候选和 1 个误差 `0.90` 的候选；utility 总是选择最后一个候选。合并候选的线性 q90 为 `0.13500000000001933`，选择后 q90 为 `0.9`，超过合并阈值的比例为 `1.0`。断言与输出一致。

**边界：** 这是普通 pooled quantile 的反例，不是对官方 CRC 算法在任意选择器下失效的定理或真实数据结果。脚本的解释已经把结论限定为“部署策略必须进入 calibration”；建议报告中继续使用“selection-induced shift counterexample”，不要写“已证明 CRC 在本任务失效”。

### 3.3 向量标量化歧义

`grc_math_sanity.py:124--153` 对 `(reprojection, depth, visibility)` 计算 mean 与 max：A 的 mean 为 `0.3667`、max 为 `0.9`；B 的 mean 为 `0.5`、max 为 `0.5`。两种标量化给出相反排序，断言通过。

这正确地指出 `Q(r_i)` 在 `r_i` 为三维向量时没有唯一含义。它没有测试单位归一化或真正的联合 conformal set，因此只能支持“必须先冻结标量非一致性/联合损失”的设计要求。

### 3.4 非子模性与 greedy 失败

`grc_math_sanity.py:156--207` 定义一个有 A/B 协同项的集合 utility。贪心选 `{D,C}`、值 `2.0`；枚举最优为 `{A,B}`、值 `4.0`；比值 `0.5 < 1-exp(-1)=0.6321`。同时 `marginal_B_from_empty=0.1`、`marginal_B_after_A=3.9`，显示边际收益随已有集合增加，违反 diminishing returns。

**边界/小缺口：** utility 的单调性在数值上确实明显，但脚本没有穷举所有集合并用断言检查 `f(S∪{x}) >= f(S)`。因此“monotone”目前是由公式可读性支持的，而不是由独立断言验收。若要把这一点写成可复用测试，建议增加所有 `S,x` 的单调性循环；在没有该补充前，不应声称脚本已经形式化验证单调性。

### 3.5 非加性集合风险

`grc_math_sanity.py:210--228` 给出两个显式数值反例：协同失败时单项和 `0.2` 小于联合 `0.8`，冗余时单项和 `0.8` 大于联合 `0.45`。断言通过。

这是一组手工指定的合法区间数值，不是由模型或数据估计的风险。它足以反驳“直接把 `sum_i q_i` 当作一般集合风险”的无条件说法，但不能估计项目数据中的交互项大小。

### 3.6 反事实敏感度符号

`grc_math_sanity.py:231--278` 固定真实值为 `0`，让 helpful memory 把输出从 `-2` 改为 `0`，harmful memory 把输出从 `0` 改为 `2`。两者输出变化绝对值都为 `2`，但真实平方损失改变量分别为 `+4` 和 `-4`，断言通过。

这正确地区分了“输出敏感度”和“对未来几何真值有益”。脚本给出的
`tau_i(S)=E[L_geo(Yhat(S\{i}),Y_true)-L_geo(Yhat(S),Y_true)]`
符号约定也一致：正值表示删掉记忆会变差。当前测试是确定性单样本示意，没有估计随机种子期望，也没有检验记忆交互。

### 3.7 未来目标泄漏

`grc_math_sanity.py:281--300` 令历史预测为 `[0,1]`，未来真值分别为 `0` 或 `1`；直接用未见未来选择 oracle history 时，两个未来对应不同历史。断言通过。

这足以说明测试时直接读取 `Y_future` 选择记忆会泄漏目标；它不否定“用训练集未来目标训练一个 past-only predictor”的合法方案。JSON 的解释已保留该区别。

## 4. 官方 CRC 身份独立核验

本复核额外执行了：

```text
git -C sources/conformal-risk rev-parse HEAD
git -C sources/conformal-risk config --get remote.origin.url
git show HEAD:core/get_lhat.py == 当前 core/get_lhat.py
sha256 当前 core/get_lhat.py
```

得到：

* remote：`https://github.com/aangelopoulos/conformal-risk.git`
* HEAD：`3eff946390a8f188b1e5ab700fce21a66a215e7c`
* file SHA-256：`ddf93c30cc703aa782c1d4f0201ca1360616b510000662cfbd0a506e91cc7546`
* `git show` 内容相等：`True`

因此主结果记录的 helper 与固定仓库文件一致。需要注意的是，**脚本本身只记录 `git_head()`，没有把“期望 commit 等于 3eff946...”写成断言，也没有断言 remote URL**。若本地 HEAD 被替换，脚本仍可能产生 `PASS` 并只在 JSON 中留下新 SHA。正式审计版建议增加：

```python
EXPECTED_CRC_COMMIT = "3eff946390a8f188b1e5ab700fce21a66a215e7c"
assert git_head(CRC_ROOT) == EXPECTED_CRC_COMMIT
```

并记录并核对 remote；这属于 provenance 加固，不影响本次固定 checkout 的复核结论。

## 5. 总体结论与交付边界

* 七个测试在独立目录重跑全部通过，主结果的 `tests` 字段逐字段一致。
* 测试有效地否定了草案中的几个快捷推理：三维残差可直接取 quantile、 pooled calibration 自动适用于选择后分布、逐项风险可直接相加、输出敏感度等于帮助程度、任意 greedy 都有 `1-1/e`、测试时可以读未来真值。
* 这批测试没有测量 RGB-D、视频生成、相机位姿、未来位置误差、跨场景泛化或 GRC 性能；不能作为“GRC-Memory 有效/新颖/达到 PhD 或 CCF A”的证据。
* 当前最安全的科研写法是：把它们标为 **synthetic mathematical sanity checks / falsification tests**，然后用真实 matched RGB-D/pose 数据验证主假设 `low past geometry risk -> low held-out future position error`。
