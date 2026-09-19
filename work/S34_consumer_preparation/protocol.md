# S34 原地图消费者适配器：执行前候选协议

范围是保存真实几何 packet 到原 Surfel 地图、追加、渲染和来源票权；当前只准备源代码与元数据，不读取预测数组、RGB 或 sensor-depth，不运行模型、GA、clean、渲染或科学人工数组测试。普通消费者衔接，不是新方法。根在源码前审及四 packet 全部封存后另行冻结 manifest 和运行。

## 输入与封存顺序

`results/S34_geometry_producer/{common_old,old_fixed_zero,old_fixed_free_400,old_fixed_common_scale_400}/packet.npz`，所有 packet 仅有 `depth(N,384,512)`、`point_cloud(N,384,512,3)`、`conf(N,384,512)`、`focal(N,1)`、`pp(N,2)`、`c2w(N,4,4)`，全部 FP32，common-old N=4、端点 N=8。conf 必须由 producer 原 clean 产生；consumer 不再 clean。每个同目录 receipt 固定 `status=PASS`、`contract_sha256` 和 `outputs['packet.npz']=SHA256`；manifest 绑定全部四份回执与 packet SHA。该合同字段由 geometry producer 作者与 root 对齐。

先核四份 receipt 全部 PASS、同正式 producer contract，然后核四 packet 全文件 SHA 和给定相机 SHA，落 `input_seal.json` 后才导入数值库并解码。任一 producer 未 PASS 不消费。不给部分旧图或某个成功条件临时换输入。原给定光学相机是 `work/S26_execution/control_c2w.npy`（既存 SHA `c004c415b5bca43ae9a22cf63b542e7171eec29e31bf985c7e36327d1f5c0194`），不是 sensor-depth GT。本文记录身份来自 S26B manifest JSON，准备期未读相机 NPY。

核 packet decoded c2w 与共同给定相机前缀在 atol=rtol=1e-5 内；端点旧4 depth 与 common-old depth 同容差，承认 log→exp 往返。原 source4 与 source8 头不同，不建立不存在的跨源相等门；不拿端点旧4重建地图覆盖已提交旧地图。

## 一次旧图与三个隔离消费者

使用 `src/s18_original_kernels.py` 的原 `resize_scene_inputs`/`store_reduced_scene`、原 pointmap/normal、`vmem_memory_kernel.py` 的 merge/Octree/renderer 和 `vmem_retrieval_kernel.py` 的原查询变换/来源投票/配额。复用 S18 的源码 AST 核查函数（只核原函数与语句片段），另核 `average_camera_pose` 与 `get_transformed_c2ws` 原 AST；不复用 S18 二帧数值断言，不导入完整 VMemPipeline 构造器。

common-old 的已 clean packet 建图一次。原倍率 .05，384×512→19×25，bilinear 默认参数；conf>=1、depth .999 分位、radius_scale=.5，merge_normal_threshold=.6。position_threshold 仍不传：由原 mean-radius + .5 std 自适应；原 Octree 和 max_points=10 不修。所有候选、真实匹配分支、源列表和地图都保存，非有限候选不被修复或掩掉。空共同旧图无法保证仅新4追加，保留失败，不回退成全8首图。

对三个固定条件分别 `deepcopy(common)`，实核旧 Surfel 对象、position/normal 数组、可变 source 列表、c2ws、surfel_Ks 与 depth cache 无共享内存，复制后的几何字节与来源完全一致。每臂原 all8 focal 追加至 old4 的 `surfel_Ks`，长度 **4→12**；all8 depth cache 替换为8项。完整固定 c2ws 共8项；没有伪造用于 latent 的 `Ks`、latent、embedding 或 NMS initial_threshold。

给定光学 c2w 右乘列符号转换成为 pipeline 相机；再调用原 get_transformed_c2ws 回光学，核同原控制字节。原 store 看到非空旧图后 `start_idx=8-4=4`，严格仅第4–7帧候选 append。merge 的分支观察器只读取真实 locals，不修改对象、数学、树或返回结果。候选→最终 surfel ID 存全量；matched_candidates 与 unique_matched_existing_ids、source_list_additions 分开，不把多候选匹配同一点计成同一个量。旧 surfel 的 position/normal/radius 原 dtype 与字节必须不变，旧来源列表可按原规则追加新帧4–7。

## 原渲染和来源配额的截止点

唯一预定 target 是同输入内第8相机（索引7），标签为 **同视角消费者自查询**，不是未来/新视角评测。调用原 average_camera_pose，即使单相机也走原 quaternion 均值；再原 get_transformed_c2ws。三条件的实际 query optical pose 要逐字相同。各自 render focal 仍是 **本臂12项历史focal均值×.65**；原512×288、中心(256,144)、disk_resolution=16、near/far/法线/多边形/z-buffer语义不变。

保存完整 render depth、surfel_index_map、cos_value_map、query inputs、所有 raw source votes 的插入顺序、归一化 weights、candidate quotas 和扩展候选来源列表。原来源首次贡献先赋值再 `+=`，首次会重复；原配额余数 `result[idx]=1`，不是加一。本轮两处都不修，也不手工重写其计算。投票和渲染后核地图/source未被修改。三臂整数 surfel ID 属于各自地图，必须用保存的 world/source 对应解释，不能直接比较 ID 当几何质量。

不调用 `get_context_info`、距离排序/NMS 或 latent 打包。4→8冷启动没有原5帧时建立的 NMS threshold，也没有合法 latent/encoder cache，`final_context_ids=null` 且 `NOT_RUN_MISSING_NMS_AND_LATENT_HISTORY`。candidate quotas 不是最终选图。原 render depth 是虚拟画布多边形深度，不与 sensor-depth 简单 resize 对照，不称可见性准确率、选图更好或视频收益。

## 输出、失败与预算

固定输出 `results/S34_original_consumer/`，已存在就拒绝；common-old 与三臂分别有完整 map.npz、sources.json、cache.npz、reduced.npz、各帧候选和对应ID、store_trace.json；三臂另存 query_inputs.npz、render.npz、votes.json，整轮 receipt 与 input seal 绑定输入/源代码前后 SHA。主评分器独立工作；consumer 失败时不能称消费成功，也不抹去已封存几何的可评分性。

root 已在冻结前明确调整为 **整个 common-map + 三次追加/渲染合计 CPU8、120秒、4GiB**，由外层监控执行；common-old packet/clean 在 producer 另占120秒，两GA各240秒，总研究设计预算不增加。这里不再给地图额外120秒，也不因规模/超时扩大预算。内部检查 wall，root 必须外控 wall/RSS；失败/超时保留输出，不自动重试、降画布、修树、改阈值或加第四条件。

准备检查仅标准库 AST/编译与源码身份，0真实/人工数组计算。执行期 NumPy1.26.4/Torch2.7.0、既有科学Python，全部三条件按固定顺序保存。协议 PASS 只能表示接口/源码准备完成，不能先授予渲染或科学结果 PASS。
