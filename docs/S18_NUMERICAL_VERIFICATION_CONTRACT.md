# S18 独立数值核验合同

状态：真实数组读取前的实现与人工前审合同。最终执行身份由 root 的 S18 manifest 冻结。本合同与 [S18_EXECUTION_PROTOCOL.md](S18_EXECUTION_PROTOCOL.md) 共同约束；不能在看到真实误差后放宽标准。实现为 `scripts/verify_s18_memory_bridge.py`，独立公式为 `work/S18_independent/numerical_reference.py`；不调用 producer、原 kernel 或 Torch/PIL。准备回执记录最终 SHA 与实际时间。

## 输入、身份和执行停点

独立环境固定本项目 `.venv/bin/python`、NumPy 2.3.5。只解码 S17C 已封存 `final_result.npz` 的六数组：point_clouds、depths、confidences、focal、R、t。先核五件已固定上游文件及 S18 manifest、caller、output seal，不递归读取 S17C 旧身份集合；原 PNG、RGB tensor、colors/pp、GT、模型权重均不解码。全 NPZ 的 SHA 字节核验区别于解码其中六成员。

CLI 必须提供 `--manifest`、`--manifest-sha256`、`--output-seal`、`--output-seal-sha256`、`--model-caller`、`--model-caller-sha256`、`--run`、`--output`。所有目录使用明确绝对路径，output 必须不存在。真实执行只由 root 在前审和冻结后调用。任何身份、模式、数值或离散条件失败，保留 FAIL 回执和已生成诊断，不替换输入或改容差。

执行前核 caller 的实际完整命令、PASS、returncode 0、600 秒/32 GiB、monitor 与 before/after 身份成功；核 producer 的完整 contract、实际 NumPy1.26.4/Torch2.7.0、CPU8、seed0、manifest 与源码绑定、原 AST 核验及实际 kernel 路径。producer 输出文件清单、每文件 SHA/大小、全部 NPZ 与 seal 相互核对。成功、无 Surfel、无可见来源是不同合法完成状态；失败不能改标为空结果。

独立过程另有 600 秒信号停止与每 0.1 秒自身峰值 RSS 8 GiB 监控，记录实际耗时/峰值。这是进程内监控，不是操作系统硬隔离。禁止独立过程中运行模型、优化、读 GT 或导入 Torch/PIL。

## 冻结数值标准及核验路径

连续量一律预定 `abs(error) <= 1e-5 + 1e-5 * abs(reference)`，使用 NumPy allclose；非有限值失败。空数组按其确切 shape 验证。布尔 mask、候选/像素 ID、来源列表、首写字段、树结构与候选遍历顺序必须 exact，**没有边界豁免、允许错几个像素或事后调阈值**。

这是一组串联组件核验：先独立核连续结果，再把已经通过的 producer 连续数组作为后续原离散算法的固定输入。它隔离跨库浮点重排引起的临界差异；不能称作跨库逐位重算整条连续链。

| 阶段 | 独立计算与接受条件 |
|---|---|
| 三路 .05 缩小 | 独立按给定 scale 算源坐标 `20*i+9.5`，直接取四邻域，两个方向分量加权；384×512→19×25。输入坐标、四邻域索引和四个 .25 权重全表 exact；三路值连续容差核对。 |
| 相机与焦距 | FP32 identity 矩阵填 R/t，光学 c2w 不翻轴；原 focal、scaled focal、两帧 mean 后乘 .65 的 `[2,1]` FP32 路径 exact。render_pp 为 `[256,144]` int64，匹配原 tuple 输入。 |
| 法向 | 在已核 reduced world XYZ 上用右/下差向量、独立平方和开根和分量叉积复算；阈值 1e-8，末行/末列零 exact。原零差导致 NaN 时失败，不补法向。 |
| 分位与 mask | 在整帧 reduced depth 上排序，FP32 `.999`、FP32 rank 与近端 lerp 算分位；threshold 连续核，depth/conf 通过域及完整 mask、C-order reduced IDs exact。没有先筛 conf 再算分位。 |
| normal 翻转与 radius | 已核 original normal 为下游固定输入；独立 eps1e-12 view normalize、dot<0 翻向、原顺序 radius。flip mask exact，normal/dot/radius 连续核。全格四项诊断独立核并注明不参与原 Surfel 选择。 |
| 原合并 | 在已核 candidate 数据上独立计算 mean+.5*population std，并验证实际阈值。随后使用已验证的原记录阈值，独立构建默认 Octree10，保留原顺序、inclusive 多孩子收同点、潜在漏查；不用最近邻替代。 |
| 树/来源 | 原 child-before-parent 节点表的中心、half-size、叶 ID、孩子数 exact；每候选的整个原邻居序列、重复项、首个严格 normal dot>.6、由捕获 break 推得的访问截止位置和 final ID exact。独立重建路径及 dot 阈值 margin 留存；不声称原树等于完整暴力邻域。 |
| 首写和来源保留 | 两张地图的 position/normal/radius 都必须逐位来自对应首个原候选，owner_frame 与 reduced flat ID exact。合并只追加来源；全 candidate_provenance 和有序 source lists exact，color=None。 |
| 两次渲染 | 从已核最终 Surfel 数据独立计算 FP32 R inverse，写入 FP64外参，分量投影、法向朝向、16 边形整数像素 parity。使用有效顶点平均 camera z，不用平面求交替代。每个 ID exact，depth/cos 连续核；保存全域 ID 差异 mask、所有差异坐标与逐 Surfel 投影诊断。 |
| 原来源投票 | 使用已经通过渲染验证的原 FP32 depth/cos，独立 C-order 累计 `cos/(1+depth)`，保留首项双加。原 raw source 插入顺序 exact；raw/normalized 数值连续核；原两来源各一候选的整数 pairs 与 source 集合 exact。 |

固定原 NumPy1.26 语义必须在独立 NumPy2.3 中显式复原：mean/std 保持 FP32，但 `.5*std` 和总合并阈值为 FP64；np.float32 normal dot 与 Python `.6` 以 FP64 比较；根节点 center 为 FP32、half-size 为 FP64，但根数组/标量边界运算保留 FP32，子节点 center 为 FP64；渲染的 Python float 平均深度与 buffer 标量以 FP64 比较后写回 FP32；票权分母与贡献为 FP64。不能把整链随意转换 FP64，也不能用 NumPy2 默认标量提升代替。

相同平均深度 disk 并非必然先写者获胜：如果前一次写入 FP32 被向上舍入，后一次相同 Python float 仍可严格小于 buffer。人工原始示例已保留，独立实现以明确 FP64 比较复原该行为。该规则是原程序行为，不是 S18 的创新。

## 完整输出模式和空分支

| producer 数值文件 | 必须核对的字段 |
|---|---|
| reduced_inputs.npz | pointcloud `[2,19,25,3]`，depths/confs `[2,19,25]`，c2ws `[2,4,4]`，focal/scaled_focal/render_focal `[2,1]`，render_pp `[2]`；除 pp int64 外均 FP32。 |
| bilinear_provenance.npz | input_xy `[19,25,2]` float64、neighbor_yx `[19,25,4,2]` int64、weights `[19,25,4]` float64。 |
| frame0/1_geometry.npz | normal_map、scalar depth_threshold；完整 valid/depth/conf mask；candidate_flat_ids、candidate_positions/normals/radii、preflip_dot、flip_mask；fullgrid view/flipped_normal/preflip_dot/radius 四项诊断。每帧候选 N 必须在0..475。 |
| map_after_frame0/1.npz | positions/normals `[M,3]` FP32、radii `[M]` FP32、owner_frame/owner_reduced_flat_id `[M]` int64；M 在0..950。 |
| render_query0/1.npz | depth/cos_value_map `[288,512]` FP32、surfel_index_map `[288,512]` int32；空像素固定0/0/−1。 |

来源 JSON、候选 provenance、完整 merge trace 和原 Octree nodes 同时核验；只有原旧地图非空才出现 merge trace。producer 实际记录整树 postorder、每 query 返回的邻居序列与捕获的 break，并未记录每个原节点的 visited 轨迹；保存的 visited 路径来自独立重建。`actual_normal_visit_count` 由捕获 break 在原邻居序列中的首次位置推得，不是逐 dot 调用计数。

query 的 canonical 地图指纹由有序 position/normal/radius 原字节 hex、source lists、color=None 构成，用固定 JSON 编码。独立从 final map 重建该 SHA，并要求原每 query before/after 相等；不能只相信一个 `unchanged:true` 字段。

最终空地图保留两帧全部中间数组和两份 `[0,...]` 地图；要求 NO_SURFELS、0 render/process、无 query 文件。非空地图总执行两个已知相机 query，即使某 query 来源空也保留 render 与原空 votes；NO_VISIBLE_SOURCE 是合法退化，不能补图。非空权重和为0/非有限则失败。全域分母每 query 147,456，不用可见像素数冒充独立场景数。

正常非空模式共读取 63 个数组：上游6、reduced8、bilinear3、两帧 geometry30、两张地图10、两个 render6；最终空地图为57。实际读取计数必须如实记录，输出 extra/missing 文件不能静默忽略。operator counters 要求 final decode6、resize1、store1、pointmap2、normal2；merge/root query 由 frame0 是否非空决定，render/process 由最终地图是否非空决定。

## 人工前审、解释范围和技能

已执行的小型原 AST / NumPy1.26 / Torch2.7 人工 packet 与独立 NumPy2.3 分量公式对照见 `work/S18_independent/artificial_packet/receipt.json`、`artificial_check_receipt.json`。其27项条件检查覆盖本轮的新插值/法向/分位/半径、树拆分顺序、原精度渲染、票权和故意像素归属污染；不是27次科研实验。

新 observer/文件 schema 另用此前完全人工输入做一次完整接口检查，见 `work/S18_independent/schema_packet/packet_receipt.json` 与 `schema_check/receipt.json`。它只调用 producer 数值组件和独立 `verify_math`，没有测试真实 CLI 身份链，不能称作真实 S18 通过。代码/identity gates 再由不同作者静态审查及 root 冻结审核。所有人工数据和失败修正保留；没有读取真实 S17C NPZ。

本轮应用 Supervisor `vibe-research-workflow` 的先明确输入/小步实现/独立核验与错误留痕；本地 Claude `sci-scientific-critical-thinking` 用于限制构念：地图候选可被消费不代表检索更好、几何更准、未见泛化或视频生成完成。没有调用 Claude 模型，也没有声称用户已亲自逐行审阅。S18 的最大结论仍是这两张已见照片的限定原接口完整性；不作新颖性或论文级别保证。

```mermaid
flowchart LR
  A[冻结身份与六数组] --> B[连续公式独立核验]
  B --> C[以已核数组重建原离散选择]
  C --> D[全部出处与空分支核对]
  D --> E[保存PASS或FAIL与真实界限]
```
