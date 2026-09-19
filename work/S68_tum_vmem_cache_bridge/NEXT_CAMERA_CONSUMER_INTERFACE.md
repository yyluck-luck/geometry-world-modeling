# 下一步：RGB 时刻相机到原 conditioning 的最小接口

**源码上可接；九份实际相机与 ray 数值尚未核。** 本次仅查看既有 S52 协议/源码及回执身份、S68 已知输入合同、原 pipeline/util 与 S64 配置。未读 RGB/depth/GT 轨迹正文/权重或新编码正文，未重算 S52 的 18、19、20 三张相机，未运行任何数值或模型。

1. **补齐相机。** 对历史 `{12,13,14,18,19}` 和目标 `{20,21,22,23}`，以原冻结 RGB 时间戳关联同一个 S52 固定 groundtruth 文本（SHA `f19dc674dc43b6c4957038e1a22906122c19c60893e664dafb0e0abe537906ca`）。复用“平移线性插值＋归一化 xyzw 四元数最短弧 SLERP、不外推”的合同；已有 18/19/20 可按保存身份消费，新增六份须核真实括号与时间。输出光学 camera-to-world、米单位；插值运动假设保留。九份完整时间覆盖、合法旋转、有限可逆性及目标尺寸元数据本次未核，不能由前三份通过推定。

2. **显式轴约定。** TUM 公布投影为 `X=(u-cx)Z/fx, Y=(v-cy)Z/fy`，即光学 x 向右、y 向下、z 向前。原 `get_cond` 对 c2w 的第 1、2 列翻号，再求逆；`get_plucker_coordinates` 由正焦距的 `[u,v,1]` 回投，因此应保存 TUM 光学矩阵为权威原值，并在消费边界明确 `C_input=C_TUM @ diag(1,-1,-1,1)`，让原函数的一次翻号恢复光学姿态。是相机局部基变换，不能左乘成世界变换，也不能把已经转过的矩阵再转两次。这个接法由源码代数推得；实际非平凡方向/相对 ray 对应仍未数值验证，不能声称已验证真实图像对齐。

3. **每臂仅 4 context＋4 target。** 保留旧顺序 geometry `[19,18,13,12]` 与 pose14 `[19,18,14,13]`，用 S68 显式 ID→storage_row 映射取四份 latent `[4,4,72,72]`、embedding `[4,1024]`、context c2ws `[4,4,4]` 和 K `[4,3,3]`；目标顺序固定 20–23。拼接 all_c2ws `[8,4,4]`、all_Ks `[8,3,3]`，mask 为四真四假。使用 FP32/CPU 独立副本，因为两个原方法均就地修改相机。每臂沿原顺序先 `get_translation_scaling_factor` 再 `get_cond`。实例仅需 `device`、`dtype`、`camera_scale=2.0`、`config.model.num_frames=8`；直接抽取方法不调用 pipeline 构造器，不需要 VAE/CLIP/视频权重、get_context_info 或 surfels。

4. **完整 helper 闭包与 K。** 两方法之外需原 `get_plucker_coordinates`、`get_center_and_ray`、`get_image_grid`、`img2cam`、`cam2world`、`to_hom`、`to_hom_pose`、默认分支 `get_default_intrinsics/DEFAULT_FOV_RAD`，以及 torch、`einops.repeat`。固定消费 S68 `K_pixels_576`，目标同样按已声明的 640×480→576 crop 合同构造 K；无需打开目标图。原 ray helper 会自行转为归一化 K，再映射到 72×72，并使用半像素中心；不要再手工缩放一遍。目标尺寸/处理合同需靠元数据绑定。输出预期 c/uc：crossattn `[8,1,1024]`、replace `[8,5,72,72]`、concat `[8,7,72,72]`、dense_vector `[8,6,72,72]`，以及相机/K/mask；有限值、slot、target 占位、变换前后身份须在未来一次小消费中核实。

**比较边界。** 数据没有已确认的必然阻断，但完整九相机及上述数值合同尚待补齐。旧固定集只支持“给定 GT 相机和旧选择答案”的条件对照；S8 查询相机曾读取目标 RGB，不能改称在线、未见或无目标照片检索。改变 context 集同时改变 latent、embedding、context 相机；原缩放也由本臂全部八相机的中心化和首相机距离决定，数值可能不同。保留原算法，不为凑相同系数私改尺度；本比较是整套 context 输入敏感性，不能单归因于 CLIP、外观或检索机制。没有生成或创新结论。

审查者：`/root/c2_v9_source_primary`；记录 UTC：2026-09-09T01:17:34.318012+00:00。

只读来源 SHA：
- `work/S52_next_discriminating_prediction/interpolate_rgb_cameras.py`：`e06f06ae445bd7d8b7f68ebc24aea2e08094fe4e59baff558cd5f598415b0268`
- `work/S52_next_discriminating_prediction/RGB_TIME_CAMERA_RECEIPT.json`：`c9c28b9cacd78073c3a68e2d3deb995758ae15d805462b31bb355177a2713d80`
- `work/S20_environment/isolated_vmem_source/modeling/pipeline.py`：`680da1c14db8a6780a37fca3a8bac5bb59f0aa7d395db96d4360b352eb7f2255`
- `work/S20_environment/isolated_vmem_source/utils/util.py`：`30a97451f7a895e99ab881e97249f564e6b97eca2b5ea4d8f83953c26c4cf65e`
- `work/S68_tum_vmem_cache_bridge/INPUTS.json`：`f14621d1988566f0fb09d314e02e0736e352fbe0a49c1055249c0011a34454bc`
