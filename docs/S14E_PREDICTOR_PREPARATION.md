# S14E 状态复用预测入口准备

本任务已经完成程序准备和人工测试；**没有读取真实 NPZ 数组、没有读取权重、没有运行真实模型，也没有做坐标对齐或真实评分**。它是否能逐字节复现 S14D 查询，需要根任务完成独立审读、冻结后实际验证。

## 问题与固定动作

已保存的 S14D 五张量历史状态能否在新进程恢复，并精确复现旧 Q0 zero 占位查询？只有该控制通过，才依次计算预先封存的四个真实轨迹相机条件。这里的“真实轨迹”描述相机条件来源；预测程序不读取轨迹原文件，不读取任何目标照片或深度答案。

程序 `scripts/run_s14e_state_reuse_queries.py` 沿用既有官方 commit、CPU 8 线程、FP32、seed 0、weights-only 白名单加载和 signed RoPE 兼容层。旧 S14D 程序不改。99 个上游 Python 文件、现有 checkpoint、兼容层、旧状态/控制输出、新相机条件和所有实际控制文件由根任务运行前冻结。外部 caller 负责 600 秒、32 GiB 监控；本入口本身不宣称实施资源强杀。

## 根任务联调合同

CLI：`python scripts/run_s14e_state_reuse_queries.py --manifest <新冻结JSON> --output <新目录>`。

manifest `schema=s14e-state-reuse-manifest-v1`，以下路径均为 canonical absolute path 并列入 `identities` 的 path→SHA256：

| 字段 | 输入与用途 |
| --- | --- |
| `prior_run_metadata` | 成功 S14D metadata，仅身份、环境版本、五状态 array SHA；不解码其中的照片路径 |
| `state_npz` | 旧 `state_before.npz`，五状态；与旧 metadata 的 shape/dtype/byte SHA 相同 |
| `parity_inputs_npz` | 旧 `probe_inputs.npz`；只解码 target_poses、K、ray_maps 三字段，不解码 history 两字段 |
| `parity_output_npz` | 旧 `query_call_1.npz`，仅 Q0 zero 控制的六输出 |
| `condition_npz` | 新封存条件，严格三个字段，见下文 |
| `condition_seal` | schema=`s14e-condition-seal-v1`，`condition_npz_sha256` 与冻结身份相同，`sealed_utc` 不晚于预测开始 |
| `repo/commit/python/runner/checkpoint/rope_check` | 与旧环境保持同一身份，runner 为新程序；repo/commit/python 作为执行配置，runner/checkpoint/rope_check 必须入身份表 |

新 condition 严格数组域：`target_poses` float64 `[4,4,4]`、`K` float64 `[4,3,3]`、`ray_maps` float32 `[4,224,224,6]`。固定四个条件，共用 K 也由 prepare 复制成四份。所有值有限、齐次底行规范、焦距为正。相机对齐、尺度、射线语义的正确性由前置 prepare/独立审读负责；预测阶段不计算、修正或根据模型结果选择相机。

contract 严格值：`target_count=4`、`query_count=5`、`dummy_values=[zero,zero,zero,zero,zero]`、`query_flags={img_mask:false,ray_mask:true,update:false,reset:false}`、`device=cpu`、`cpu_threads=8`、`seed=0`、`size=[224,224]`、`dtype=float32`、`wall_seconds=600`、`monitored_rss_bytes=34359738368`；`history_rgb_allowed/target_rgb_allowed/target_depth_allowed` 全 false。

预测的身份表会逐文件做前后 SHA，不能混入 prepare 阶段读取的真实照片、原始深度或原始轨迹文件；这些来源可通过 prepare manifest/seal 的文字与 SHA 传递。程序拒绝常见图像/NPY后缀、非四个允许角色的额外 NPZ，以及 groundtruth.txt/rgb.txt/depth.txt。其“无目标照片/深度读取”主张属于此固定代码与调用范围的追踪，不是操作系统级任意文件读沙箱证明。给定相机条件本身是合法输入，不能说一切 GT 信息都未提供。

## 实际执行顺序与完成门

1. 新目录、冻结身份、官方 clean commit、既有安全加载设置、Python/NumPy/PyTorch 版本、旧产物身份、新条件 seal 均通过后，解码四个允许 NPZ。共 17 个数组：5 state + 3 old condition + 6 old outputs + 3 new condition。旧历史 pose 两字段不解码；没有 history forward。
2. 恢复五个状态张量；同旧形状与 dtype，其中 state_pos 为 int64，其余 float32。对原状态 metadata 的逐张量字节身份进行验证。
3. 第一次调用严格使用旧 Q0 ray、旧 Q0 pose、相同 zero dummy/flags/idx。返回六个 tensor 后立即存 `query_call_0.npz`，再验证 shape/dtype/finite、五状态身份、encoder 使用、六输出逐字节 parity。六输出包含 RGB head，它是模型 tensor，不是读取真实照片或完成视频。
4. 控制通过才依次做四新条件；每次返回立即存 `query_call_1..4.npz` 再过门，不据结果筛选或调整条件。每次 image encoder 处理 batch 数累计 0、ray encoder 累计 call+1。五状态每次 byte/schema 身份不变。
5. 最后保存 30 个聚合输出数组、state_after、metadata、源码/manifest 快照、逐文件输出 SHA、前后输入身份、实际调用/时间/资源等。只有全部五次通过才记 SUCCESS。parity 失败时不执行新条件。

计数区分尝试、成功打开、数组成功解码、query 已尝试与已经返回；阶段 metadata 在读取/调用前写出，任何 Python 异常更新 FAILED/traceback，已返回每次 NPZ 保留。外部超时或强杀另由 caller 留痕，不把未回传结果记为模型返回。PIL.Image.open 在模型导入/执行段被显式拒绝并记录尝试。

## 人工测试与准备纠错

`scripts/check_s14e_predictor_artificial.py` 使用人工数组与 stub query 回调，未导入 CUT3R 模型或读取真实实验数组。`work/S14E_predictor_preparation/artificial_v1/receipt.json`：35 项 schema/finite/contract/byte 检查通过，含 -0.0 与 +0.0 字节区别；6 执行路径通过：正常五次、parity 失败、state 改动、图像 encoder 误用、非有限输出、模型异常。失败路径均只尝试首个 query，已返回结果先保存；模型未返回时计数 0。正常路径返回 30 个数组、5 个 call 文件。以上是作者自检，不写成独立审计，也不是实际 CUT3R 模型实验。

准备时查阅官方 `generate_pseudo_intrinsics` 源码，发现旧 K 明确为 float32；将初稿的 float64 断言修为 float32，旧源码保存 `before_prior_k_dtype_correction.py`。这是运行前源码核对修正，没有发生真实运行失败。新 condition 的 K 仍约定 float64，不暗改 prepare 合同。

## 实际应用的技能与界限

应用 Supervisor `vibe-research-workflow` 的 coding 分流及 `references/vibe-coding.md`：先明确输入/不包含项、拆成 pure schema 和可注入控制流、小步人工验证、保留错误与旧稿。应用 `/Users/rocket/.claude/skills/sci-scientific-critical-thinking/SKILL.md` 的构念有效性、控制与盲法、透明性部分：把“状态可复用”控制与“几何准确率”分开、预测输入与后置深度评分隔离、保留全部四条件与失败。未调用 Claude 模型或 CLI；未套用不适合本接口的临床 GRADE/统计显著性框架，也未为工具数量生成图。

六条科研行为边界沿用本项目授权：AI 可辅助检索/代码/表达；用户拥有并需理解研究问题与实质；所有事实以真实产物核验；引用不编造；数据/结果不虚构且不掩饰抄袭；投稿时另核具体 AI 披露要求。本任务不替用户虚构私人阅读、逐句确认或投稿合规证明。

下一步由不同作者审读输入绑定、恢复/parity、失败边界；根任务完成相机 prepare 与身份冻结后单次实际运行。本准备不表示上述真实验证已经完成，不表示新算法/创新/准确率/视频有效。
