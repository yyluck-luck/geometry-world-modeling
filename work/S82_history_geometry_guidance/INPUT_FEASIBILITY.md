# S82 四历史 CUT3R 几何输入可行性

审查开始：2026-09-10 17:16:07 UTC（北京时间 2026-09-11 01:16:07）。本文实际记录时间：2026-09-10T17:26:30.899608+00:00。作者为输入审查岗位；这里只读源码、已有 JSON 收据和文件 stat。没有打开或解码 RGB/深度，没有读取 NPZ 科学数组、权重正文，没有加载或运行模型，没有创建真实几何缓存。主账和旧结果由 root 保持不变。

## 结论与最小决定

**现有已核缓存不能作为 A0 恰四历史 [19,18,13,12] 的等输入几何。** 在此次有限检索中未找到匹配这四个原始 RGB 身份、没有额外历史/目标图的几何结果；这不是对整个磁盘不存在此类文件的穷尽证明。原四图文件与 512 DPT 权重路径均存在，历史收据与当前 stat 尺寸一致，因此从输入身份和现成源码接口看，本机可准备一次仅四历史重建；本次没有实际执行，也不能承诺质量、时长或成功。

建议只构建一次 512 DPT 原始几何：按时间 [12,13,18,19] 输入，fresh recurrent state，revisit=1，四张均 update=True，不加 ID14，不加任何目标 RGB，也不载入旧 recurrent state。生成历史槽保持 [19,18,13,12]，对应新推理行 [3,2,1,0]。如果四历史构建失败，保留失败，不能回退到 S8 缓存并仍声称相同四图输入。

下一份执行合同最少需冻结：512 入口与源码版本；原始 self/cross 输出采用哪一种几何解释；是否使用现成 known-pose 优化及其迭代/学习率/清理行为；源 K 如何绑定；资源边界；输出与相机读回核验。本文不是执行合同，不新增成功阈值或科学结果。

## 实际缓存覆盖及排除理由

此次列举并筛查 `results/**/run_metadata.json` 共 53 份，以四图计数或包含 anchor 时间戳 1311868171.663411 的元数据为候选，另定向读 S8、S21、S26B 的输入清单和收据。没有读取这些缓存的数值数组。

| 来源 | 已核身份 | 能否直接复用为本次四历史几何 |
|---|---|---|
| S68 appearance bridge | 五张 [12,13,14,18,19] 的字段只有 latent、embedding、K_pixels_576、K_normalized_576；geometry_calls=0 | 不能，根本不含 depth/pointmap。可继续复用四张既有外观缓存，但那是另一种输入 |
| S8 block0 | 24 输入，20 history、4 query；224 linear 权重；固定输入含 0–23 | 不能，额外历史已经不等于只四张。query_updates_state=false 也不改变这个事实；本审查不据此进一步断言目标一定污染了前面每一张的输出 |
| S21 original4 | 确有一次原版 512 四图运行，但是 1311868164.363181、.399026、.430940、.463055，属于另一组前缀 | 不能，仅“4”相同而 RGB 身份不同 |
| S21 主运行及 S26B consumer | S21 主合同 300 帧；S26B seal 为 8 个旧 S21 heads，400 次优化，model_forwards=0 | 不能，既不是本四图身份，也不是四历史独立前向；已有优化输出不能换名复用 |

S68 自己明确这些 selection IDs 是此前曝光的固定集合，旧选择涉及目标信息。本次重新只读四图，可约束新的重建输入；**不会把历史 selection 变成从未看过目标的在线选择试验**。与 A0 比较只能在既有固定集合上成立。

## 四图和顺序

以下 SHA 来自 S68 已记录原始 RGB 身份，本轮只核路径存在和 stat，未重读图片字节重哈希。完整 SHA、路径、已有相机和当前源码 SHA 在 `SOURCE_PATHS_AND_HASHES.json`。

| 新推理行 | 历史 ID | 原 RGB 文件 | 原生成槽（0 起） | 字节 |
|---|---:|---|---:|---:|
| 0 | 12 | 1311868168.963348.png | 3 | 513004 |
| 1 | 13 | 1311868169.363470.png | 2 | 505590 |
| 2 | 18 | 1311868171.299368.png | 1 | 538723 |
| 3 | 19 | 1311868171.663411.png | 0 | 530537 |

原图目录：`data/tum/fr2_desk_timestamp_guard/rgbd_dataset_freiburg2_desk/rgb/`。原分辨率 640×480 来自 S68/S69 已执行记录，不是本轮新读取。

## 已有可用推理入口

首选复用 `scripts/s21_baseline.py` 的 **original4 调用路径**：现有原版 CUT3R、`load_images_for_eval(size=512,crop=True)`、四个 image-only views、官方 `inference_recurrent`、官方 `pose_encoding_to_camera`，逐帧保留预测 head。它的旧 CLI 固定读取 S21 旧 manifest，因此不能直接原样调用获得本四图；只需给该已存在调用路径一个新的四图清单和小入口，不需要另建大框架。

原版 checkout 为工作区 `work/cut3r-local`，`.git/HEAD` 当前文本为 `8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf`。本机旧 git 不接受 `worktreeconfig` 扩展，故没有取得 git status；本报告用实际源文件 SHA 限定所读实现，不把 HEAD 当成所有文件未改的证明。

可用权重为 `data/cut3r/cut3r_512_dpt_4_64.pth`，3173761006 字节；已有 S21/S17 记录 SHA `45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103`，本轮 size/mtime 与 S21 manifest 一致，没有重新读取 3.17 GB 文件。已有 S21 original4 收据记载 4 帧前向并归档 6.0470 秒、峰 RSS 6758957056 字节；这只是另一输入的历史资源证据，不能当新四图测量。该旧收据 training_flag=true 且 stochastic_modules=[]；新构建应显式 `.eval()`，而不是笼统宣称复制了已确认的 eval 运行。

现有 `scripts/run_cut3r_local.py` 支持任意 `--images` 且显式 eval，但源码硬编码 224/linear 并检查架构，不能只替换权重路径就称 512 DPT。它可以作为较低分辨率备选，但需单独声明，不能伪装成上述 512 基线。S21 使用已存 signed RoPE 兼容层；需记录该层当前 SHA，不能把外层 float32 误写为内部从不发生精度转换。

## 原始输出、像素、尺度

1. 512 DPT 原始 head 给 `pts3d_in_self_view`、`conf_self`、`pts3d_in_other_view`、`conf`、`camera_pose`、`rgb`。`camera_pose` 是 3 维绝对平移加实部在前的 wxyz 四元数；由官方 helper 解码成 c2w。不能把它直接当 TUM 的 xyzw。
2. DPT 的 self 和 cross 是不同 head。源码**不保证** `pts3d_in_other_view == c2w * pts3d_in_self_view`；因此不得混用 self 的深度、cross 的坐标和任意替代相机。原始 learned 点图、位姿的尺度也不能直接认证为 TUM 米。需保存原始两种输出，固定后续使用路径。
3. 按已记录 640×480 和该 loader 的明确规则，512 输入是 512×384，长边缩放 0.8、不再裁切；不是 512×512。对应原 K 的理想坐标变换为 fx=fy=420、cx=255.6、cy=191.6。此处是源码与已存尺寸导出的坐标合同，不是新图像转换结果。
4. 原评分/生成 576×576 使用先 768×576 后水平裁 96 的规则：u576=1.2u640−96，v576=1.2v480。由此 u576=1.5u512−96、v576=1.5v384。不能将 512×384 点图拉伸到正方形并仍用原 K。后续推荐把点转到统一世界后用已冻结 K576 正式投影，而不是缩放数组冒充重投影。
5. K 始终是既有 ROS 默认近似值、未去畸变；实际 576 K 为已有 float32 数组，应复用字节身份，不手抄 287.4 替代 287.4000244… 的保存值。

## 与已合法请求相机统一：现成接口及未冻结项

合法相机源是 S69 `execution_01/optical_cameras.npz`（SHA `599543102f5c799ca4005ead413b69ee10e42269ef36a7942410f9066556d325`）；本轮只读对应 receipt 的 c2w JSON 和 archive 元数据，未开 NPZ。四个历史光学 c2w 按 [12,13,18,19] 重排，目标 [20,21,22,23] 仅作为已有请求相机参与投影；目标 RGB/深度/模型估计不得进入建图、缩放拟合或清理选择。

原 VMem 已有 `extern/CUT3R/surfel_inference.py`：`run_inference_from_pil(...,poses=...,depths=None,size=512,...)` 一次四图推理后组装首帧至另三帧的 star edges，进入 `prepare_output` 的 PointCloudOptimizer。`preset_pose` 将所有给定历史 c2w 冻结并关闭 pairwise scale normalization；已有 `get_pts3d` 实际用 `(u−cx)Z/f,(v−cy)Z/f,Z` 再乘 c2w 生成世界点。该路径提供了把四历史几何放入合法光学世界坐标与其平移单位的现成途径，**但它是有优化的几何拟合，不是无误差的尺度认证**。已固定相机、深度数值与尺度一致性仍要运行后检查。

为避免重复模型调用，可以先按 S21 路径保存四个 heads，再复用该 helper 的四帧 edge 组装和 `prepare_output`；或只调用 `run_inference_from_pil` 一次并同时存原始 heads。二者只能选定一次前向，不要先后各跑一遍。

必须显式处理以下源接口细节：

- 原 helper 默认 niter=300、lr=.01、init=mst、schedule=linear，结束后调用 `clean_pointcloud()`；pipeline 上层默认可覆盖为 1000，S26B 旧执行是 400。这三个数字不是同一合同。此次没有选择新迭代数或运行优化。
- PointCloudOptimizer 默认优化焦距，`optimize_pp=False`，主点固定在图像中心，512×384 为 (256,192)，与合法 K 的 (255.6,191.6) 不同。不能输出“已绑定 K”但实际只固定了 poses。
- 如果采用已知 K 的受控版本，已有 `preset_focal`、`preset_principal_point` 接口可用。不过 `_set_principal_point` 只有 requires_grad=True 或 force=True 才赋值；在默认 optimize_pp=False 上直接调用 preset 可能仍留中心值。最小明确路线是在构建优化器时 optimize_pp=True，立即 preset 主点使其赋值并冻结，再读回所有 K；必须核读回数值，不能把调用未报错当成功。该设置是相对原默认的声明变体。
- 使用 S69 原 optical c2w 时，投影采用光学坐标。VMem 的 `consumer_raw = optical @ diag(1,-1,-1,1)` 是相机局部基底转换，原 `get_cond` 还会翻回；不要在几何上重复翻轴。S69 geometry arm 的平移尺度 27.322040557861328 属于条件中心化/归一化，不是 CUT3R 原始点图的公制因子。
- 最简单的显示/目标投影是在原 TUM optical 世界米制坐标完成，直接用已有目标 c2w 的逆和 K576。若要进入已中心化的条件坐标，必须把相同平移中心和尺度施加给所有世界点及相机，不能只缩放相机或复用另一个 arm 的中心。

## 本次仍未做、因此不能声称

没有核新四图重建质量、置信度覆盖或遮挡关系；没有确认源 checkpoint 正文当前 SHA，没有加载依赖/模型；没有执行上述 optimizer/K 绑定路线；没有创建 render、latent guidance 输入或新生成。不能声称四张合法输入在预算中已完整计费：下一合同还应计入四图文件、权重/缓存读取、建图及几何优化成本。已有相机来自 GT 插值，选择集合与目标已历史曝光，K 近似/无去畸变等限制继续保留。

本轮重读 AGENTS、RESEARCH_MEMORY 头部与最新 RESEARCH_LOG；RESEARCH_PRINCIPLES 已在同一接续会话前面的 S81 阶段分段读完。本报告正文源码审查限上述函数、heads 和 metadata，不称每个历史文件或整个 CUT3R/VMem 已完整审完。本文和清单是后续四历史几何输入准备材料，不是新生成结果或创新验证。
