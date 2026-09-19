# S14E 相机准备程序接口

这是运行前接口，尚未解码真实数组或轨迹。入口 `scripts/prepare_s14e_known_camera.py --manifest <JSON> --output <新目录>` 仅构建封存相机条件与普通基线，不运行模型或评分。

## 输入

Manifest schema=`s14e-known-camera-prepare-manifest-v1`。顶层 runner/python/frozen_inputs/s8_metadata/s14d_metadata/s14d_manifest/history_predictions_npz/s14d_probe_npz/trajectory/viewer_path 为绝对路径。除python外，各路径必须列于 identities（canonical absolute path→SHA256）；控制文稿也可列入，但不得列入照片/实测深度/权重。frozen_inputs固定旧S8 block0，dataset_root是只用于字符串核对的绝对目录，不扫描或读取图像。

contract 固定：history_count=20、target_indices=[20,21,22,23]、history_time=rgb、target_time=depth、K=[[245.2734375,0,112],[0,245,111.5],[0,0,1]]、size=[224,224]、max_trajectory_gap_seconds=0.1、max_rgb_depth_offset_seconds=0.02、minimum_alignment_D_metric_squared=1e-12、rotation_atol=1e-5、roundtrip_atol=1e-5、roundtrip_rtol=1e-5、history_rgb_allowed=false、target_rgb_allowed=false、target_depth_allowed=false。数值比较独立预定 atol=1e-6/rtol=1e-5；不把它当作正交性门。

history_predictions_npz只逐键解码frame0..19的pts3d_in_self_view和camera_c2w，共40数组；s14d_probe_npz只解码history_poses一个数组。旧文件整体SHA含旧query预测字节，但不解码它们。相机缓存须与S14D history_poses逐字节相同；两metadata中state_feat与mem锚SHA须相同；不冒称其余三状态跨S8/S14D已比较。照片顺序/SHA、权重/commit、FP32/224/CPU8/seed0/版本/历史flags从冻结metadata核对，照片与权重实体不重读。

## 数学与输出

只用20历史拟合A=Rp0 Rg0.T，a=AΔGT，b=Δpred，D=sum||a||²，N=sum a·b，s=N/D（模型单位/米），c=p0-s*A*g0。D≤1e-12或s≤0/非有限即失败；不能abs、clip或换回归。目标R=A*Rg、t=s*A*g+c；主深度和基线均除同一s。GT轨迹平移线性、xyzw四元数规范化最短弧SLERP，精确样本不跨区间，无外推；插值区间≤0.1秒。给定GT相机属于公开允许输入，目标RGB/实测深度尚未提供。

FP32预测旋转不严格正交；不做SVD修正。按根2026-09-06本轮数据解码前选择，rotation_atol和相似变换往返atol/rtol均1e-5，往返仍用A.T；这承认已有FP32精度。不得用1e-9门误拒绝后才偷偷调宽。

| 输出 | 字段 |
| --- | --- |
| condition.npz | target_poses float64[4,4,4]、K float64[4,3,3]、ray_maps float32[4,224,224,6]；严格3keys，官方AST编码不改 |
| baselines.npz | history_zbuffer_m、history_constant_m，均float64[4,224,224] |
| baseline_provenance.npz | warp_source_index int64[4,224,224]（history*50176+raster，空=-1）、warp_valid bool同形 |
| history_inputs.npz | history_self_z float32[20,224,224]、history_poses float32[20,4,4] |
| allowed_gt_poses.npz | gt_poses float64[24,4,4]、selected_timestamps/rgb_timestamps/depth_timestamps float64[24] |
| alignment.json | s_model_per_metric、A、c、D_metric_squared、N_model_metric、残差/朝向/归一化RMS/轨迹方差/往返误差 |
| baseline_diagnostics.json | 每history有限/正z统计、每target投影和覆盖计数、常数样本数/中位数；不作评分 |
| run_metadata.json | schema=s14e-known-camera-prepare-v1；status SUCCESS或FAILED，开始/完成时间、分阶段读取与计数、output_sha256 |
| condition_seal.json | schema=s14e-condition-seal-v1、sealed_utc、condition_npz_sha256、payload_sha256（含已完成metadata，不含seal自身） |

物理基线单独使用标准pinhole：只取全部history finite且正的self-z，标准K回投、预测history pose入世界、目标pose逆变换；floor(u+.5)最近像素、正z取最小，精确tie取history index再raster index小者，空NaN且明确mask。不用网络self XY、confidence、补洞或目标答案。常数为相同20history有效z全局NumPy中位数/s。

每个输入记录JSON/轨迹/NPZ打开与逐键解码的尝试/完成数；异常保留metadata、traceback、此前产物。外部caller负责600秒/32GiB，prepare本身不实施强杀。全部输入身份前后核对，SUCCESS先落metadata再seal；模型入口只能消费成功封存条件。当前未进行真实执行；作者人工测试与独立审读结果另在work/S14E_prepare_preparation回执记录。

## 准备检查结果

作者人工检查已完成，见 `work/S14E_prepare_preparation/artificial_v2/receipt.json`：37项检查通过，含正向OLS 7/5反例、旋转/尺度/平移恢复、负尺度/零尺度/退化/非法旋转拒绝、最短弧SLERP及小角稳定性、外推/间隔拒绝、标准深度回投、遮挡最近z、精确tie来源、half像素rounding、空NaN/后方统计、常数中位数，以及完整CLI的41键读取与seal身份。

完整CLI仅用此work目录人工生成的20点图/poses和轨迹。额外放置未授权object类型query键与S14D target键；若逐键越界解码，在allow_pickle=False下会失败。本次未解码这些键，且人工照片目录/权重文件根本不存在，程序仍完成预期准备。这个测试是程序作者自检，不能称独立审计或真实数据实验。

第一版人工检查中“负尺度拒绝”例同时错误地改变了齐次矩阵底行，触发的是底行拒绝而非尺度门。原script/receipt与输出目录保留；第二版只改变平移以单独测试负尺度，并增加零尺度例，37项通过。生产源码未因这项测试修正而改变。尚需不同作者前审，当前不执行真实数组或模型。

技能局部应用沿本轮预测准备文稿：Supervisor Vibe Coding要求明确合同、小步验证与错误留痕；本地Claude scientific-critical-thinking用于区分给定相机监督与目标图像答案、尺度构念、普通基线与创新、作者测试与独立审读。不调用Claude模型，也不通过新增绘图或重复实验凑工具数量。
