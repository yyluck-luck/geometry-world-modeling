# S33 评分候选：原48行不动，只评分新16行

当前仅源码和既有JSON/CSV身份准备；未读取预测NPZ、RGB、sensor-depth PNG或相机文件，未运行模型、GA或度量。根任务另审后冻结正式manifest，显式传 `--manifest FILE --sha256 SHA` 单次执行。CPU1、120秒、2GiB由根调用者外控；源码在数值导入前把BLAS/OMP线程固定1。候选中的未来producer合同、四个终态回执、dispatch屏障与新输出SHA仍null，不可执行；本协议不是已完成实验。

## 原结果导入与完整分母

严格绑定S32的metrics/CSV/主PASS回执/正式评分manifest/独立v2PASS回执五个已存在文件SHA。原metrics与CSV逐字复制成 `imported_s32_metrics.json`、`imported_s32_per_frame.csv`；合并CSV以原文件完整字节为前缀，只追加新16行。合并JSON先原48行再新16行，旧12组及三个旧条件的两种汇总都直接复制，并在输出前逐值检查未改变。不重新打开S32旧端点数组，不重新计算旧48分数，也不把过去的GT曝光改写成未知。

窗口顺序固定fr2_desk_j1、fr2_desk_j2、fr1_xyz_j1、fr1_xyz_j2；旧条件为initial_0step/corrected_getter_400/global_rescaled_400，新条件唯一common_pair_scale_400。完整设计4窗×4条件×4帧=64行、16组。缺pose窗的新4行仍NA；若新producer失败，只新候选该窗4行NA，原S32三条件不受影响。全部4窗的严格均值保持NA；事先3个相机可用窗的描述均值同样只在三个均有定义时给出，不悄悄缩分母。

## 冻结接口与读取顺序

manifest字段：`schema/status/output_root/endpoints/resource/selection_path/selection_sha256/old_scoring_sha256/control_sha256/producer_contract/terminal_barrier/windows`。每个window有id、availability、reason、producer_receipt、frames、endpoint。frames完整复用S32正式评分manifest中的index、RGB时间、sensor配对、path和实际已封存SHA，不新关联、不提前读取深度字节。producer_contract最终指向 `work/S33_preparation/contract.json`，终态屏障为 `work/S33_execution/dispatch_receipt.json`。

每窗producer路径为 `results/S33_pair_scale_control/{window}/receipt.json`，必须有window_id/selection_sha256/contract_sha256以及PASS、FAILED或固定缺poseUNAVAILABLE。PASS还须candidate_available=true，outputs覆盖 `common_pair_scale_400.npz`，其中唯一键depth、FP32、完整(4,384,512)。4终态都要与实际dispatch `COMPLETE_FIXED_WINDOW_MATRIX_SEALED` 的状态及回执SHA一致；该状态是完整矩阵结束，不意味着四窗都PASS。

所有新PASS producer的全部输出逐文件核SHA，随后才解码新候选NPZ、再读sensor-depth字节/解码。FAILED的半成品不打开、不评分。GT仅对新可用窗口每帧解码一次（最多12张），同原S32路径和SHA；这些GT曾在S32评分使用，工程顺序隔离不恢复盲测。S32旧数组始终不读取。

## 度量与缺失

度量直接调用已冻结 `scripts/score_s26b_consumer.py` 的load_sensor_depths/depth_metrics；缺失、四帧汇总与窗口均值复用已冻结S32 scorer的empty_row/aggregate_group/window_summary，不重写数学。sensor uint16 640×480按中心nearest映射到512×384、除5000米制；主分母为正有限GT，不按置信度/远深度筛选，不做GT scale fit。FP32预测只在原度量内转FP64。新端点不计算k、D*、SS或附加ATE。

保留AbsRel、RMSE、严格δ1<1.25、有效GT/预测无效计数及无效比例。正GT上的任一非正/非有限预测使该帧AbsRel/RMSE为null，δ1把无效预测作为失败；GT空时原null规则保留。缺窗口的GT/预测计数未知为null，不编成0。帧和像素不作为独立样本，不做显著性或CI。

## 输出、失败与证据边界

输出 `results/S33_pair_scale_scoring`：完整metrics.json/per_frame.csv、新16行与4组另存、原S32两文件逐字副本、输入seal、数组schema、GT回执及最终PASS/FAILED回执。已有输出拒绝覆盖；运行内异常保留FAILED和部分文件，哈希/schema失败不得被静默改成NA，也不自动重试。正式入口前的候选/来源拒绝由外层调用者保留失败回执。

评分PASS表示完整表已构造，不保证新条件提升。输入是已见场景的已评分短窗和给定GT相机，普通共同pair尺度约束不是新方法，也没有old4→new4记忆或视频闭环。独立数值复核须后续实际执行，本候选不冒称通过。
