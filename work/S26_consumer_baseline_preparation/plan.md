# S26：封存六头进入原 VMem GA 的真实消费者基线（待冻结）

**当前结论：源码接口可对接，尚无运行或数值兼容结论。** 本轮仅准备 source/metadata、独立 adapter；0 模型初始化/前向、0 GA、0 NPZ/PNG 解码、0 GT pose 坐标解析。不会改 S17C/S21/S22/S24 冻结文件。父任务须完成独立审查、runner/observer/scorer 和正式 manifest 后决定执行；这里没有自动执行入口。

目标是问：**在相同给定相机和同一份旧深度下，三强基线的已保存预测，是否在 VMem 真正使用的 GA depth/pointmap/focal/conf 上仍有差异，能否完成新4帧深度的同条件组件比较？** 这是原消费者的组件基线，没有新方法、Surfel 合并、检索或生成。本次不重算8帧自由ATE，不作自由ATE与consumer排序一致/反转的结论。8 帧不完成 proposal，也不证明自然失败、统计显著性或长期生成一致性。

## 1. 固定候选输入与共同条件

- 候选为 S21/S22 fr2_desk 已封存、相同且完整的首 8 个 RGB–pose 配对帧，索引 0–7，时间 `1311868164.363181` 至 `1311868164.599061`，跨度约 0.235880 秒。旧 prefix 为 0–3，新帧为 4–7，不根据结果选帧。仅作数据接口和受约束 GA pilot；如此短的时间跨度不能承载算法优劣结论。
- 三种 8 帧输出来自 `results/S21_baseline/cut3r`、`results/S21_baseline/ttt3r`、`results/S22_filt_shared_precision/filt3r`。来源与逐帧 archive SHA 继承各自 PASS receipt，详 `candidate_inputs.json`；本轮仅查 metadata 和文件 stat，未重新核 archive 内容。
- **共同相机**：未来单独的 control producer 按 S21 固定 `gt_time` 提取同一 8 个 TUM c2w。所有方法使用完全相同的 CPU FP32 `[8,4,4]` tensor 和 SHA。它是显式的 **GT 相机条件 / oracle camera control**，不是盲测，也不是可部署的相机估计。相机坐标解析须在日志中当场记录，不能沿用 S21 的 `gt_coordinates_used=False` 标签。
- 坐标合同：`prepare_output` 接收光学相机 c2w（相机深度为 +Z）；TUM c2w 直接进入此接口，不再额外翻转 Y/Z。若展示 pipeline 的内部表示，记 `C_pipeline=C_TUM·diag(1,-1,-1,1)`，原 `get_transformed_c2ws` 再翻列后恰为 `C_TUM`。冻结前对非平凡 SE(3) 做独立往返检查，未来对共同矩阵检查底行、SO(3)、正行列式、有限性；不按方法单独旋转、归一化尺度或重新配对。此处未读取任何 GT 坐标来检查运动量。
- **共同旧深度只能来自一次原 CUT 的前 4 帧 GA**：用 `results/S21_baseline/original4` 的六头和上述前 4 个相机，`depths=None`，原 GA 400 步/.01。保存并封存最终 `[4,384,512]` depth，一次生成、全部方法共用。不得用传感器 GT depth，不得分别运行 CUT/TTT/FILT 旧图并各用各的旧 depth；GA 的同一次 post-clean depth 与 pre-clean depth应一致。

这是一项受控 `4 old + 4 new` 分解，不冒充 VMem 默认导航真实批次：生成器默认 context4/target4/total8，首次留存数受请求/padding影响；原几何每次重跑全部历史 N，anchor 始终历史0。S25 消费者审计已经区分这些语义，本 pilot 没有生成 chunk。

## 2. 四个 GA 作业，原数学不变

| 作业 | 网络预测来源 / 序列 | 给定相机 | 给定深度 | 产出及用途 |
|---|---|---|---|---|
| A：common-old | S21 original4，完整0–3 | 共同相机0–3 | None | 唯一共享旧4 depth，先封存 |
| B：CUT | S21 cut3r，完整0–7 | 共同相机0–7 | A的全部旧4 depth | 后4新depth及完整GA字段 |
| C：TTT | S21 ttt3r，完整0–7 | 同B、同SHA | 同A、同SHA | 同B字段 |
| D：FILT | S22 shared-precision filt3r，完整0–7 | 同B、同SHA | 同A、同SHA | 同B字段 |

每作业独立新进程、CPU8、FP32、在模块导入后重置 Python/NumPy/Torch/OpenCV seed=0；不加载模型权重。原 `prepare_output(output, poses, depths, lr, niter, outdir, device, save_flag=False)` 保持完整 AST，调用固定 `lr=.01,niter=400,device='cpu',save_flag=False`。它内部开启 scene 梯度；**不能用 torch.inference_mode 包住 GA**。

固定原 `GlobalAlignerMode.PointCloudOptimizer`、定向星形 `(0,1)…(0,N−1)`、MST/PnP、原 loss/Adam/linear schedule、原 clean 顺序。A为3条边，B/C/D各7条边。相机全冻结；B/C/D只有前4深度冻结，后4可优化；focal继续原设置可优化，principal point原默认固定，pairwise pose仍由原优化器处理。原 `preset_pose` 关闭 pair scale normalization。不得用 `pose × self pointmap` 代替 GA，也不得把 raw other pointmap 原样冒充最终世界点。

总计 **4次新真实 GA、1600次原 Adam step、0次新网络前向**。若未来 observer 每作业增加一次只读最终目标求值，则为1604次目标调用/1600次 step；须单独记名，不混淆最后一次返回 loss 与更新后目标。重复兼容作业不包含在这个最低运行数内，增加前必须修改协议，不静默重跑。

## 3. 最小字段与可执行 adapter

`saved_heads_adapter.py` 提供五个待调用接口：`configure_original_geometry`、`load_saved_predictions`、`load_original_views`、`assemble_saved_output`、`run_original_ga`。没有 CLI、模型实例化或 GT 文件读取代码。`CommonOldDepth` 要求 A 的输出seal SHA、depth内容SHA及其共同prefix pose内容SHA；调用时实际重算后两项tensor哈希并核对。完整来源链仍由父任务 runner 核验：必须验证 A 的完成receipt/seal及output.npz文件SHA，且depth内容SHA确实来自该封存输出，不能给任意tensor配一个自算字符串就当合法来源。

**NPZ 最小完整六头合同**（每帧均FP32/finite，保持原值；此轮不读 header/数组）：self、other、rgb 各 `[1,384,512,3]`；conf_self、conf 各 `[1,384,512]`；camera_pose `[1,7]`。raw conf 必须正，满足原 log 权重定义。全部字段装回预测 dict；没有消费者访问的头仍保留作来源与诊断，不能混用 rgb head 充当 view.img。

**View 合同**：同一真实 RGB 来源、原 `prepare_input_from_pil(size=512,revisit=1,update=True)` 重建 view；img `[1,3,384,512]`、true_shape `[[384,512]]`、idx/instance为0…N−1、image=True/ray=False/update=True/reset=False、原identity camera占位与NaN ray占位保持。给定相机是单独的 GA `poses` 参数，不能塞进 view 的占位 camera_pose 并声称已preset。

adapter 从原 wrapper 的348–398行抽取**全部星形拼装语句**，唯一移除网络调用 `outputs,state_args=inference(...)`，改由已保存 `outputs={views,pred}` 提供。原 collate/排序保持；结果为 view1/view2/pred1/pred2。GA实际取 `pred1.self/conf_self` 与 `pred2.other/conf`，即反复使用anchor0 self及后续帧other；不使用raw camera_pose、非anchor self或rgb head。

源码来自已完成 S17C 的 `work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R`，commit `39291e4f272f6b4f270691d930926ab5930f942e`；已控制的3处透明补丁不变。准确依据：`surfel_inference.py:174–214,348–398`；`cloud_opt/dust3r_opt/base_opt.py:132–154,243–247,349–359`；`optimizer.py:102–121,206–261,269–288`；`init_im_poses.py:78–139`。`source_binding.json` 绑定199份源码与既有manifest/环境记录；父任务冻结时须完整继承依赖身份，而非只信 sys.path。

环境复用 `.venv-cut3r/bin/python` 与 `work/S17C_environment/site-packages`；既有 import smoke 为 PASS，S17C 原2图 GA 已真实运行。核心 NumPy1.26.4/Torch2.7.0/SciPy1.16.2 保持原环境，overlay不能替换它们；GA路径所需 evo/roma/OpenCV/图像与viz顶层依赖已有记录。本轮仅核文件存在、source SHA 和历史 import receipt，不声称做了新的 import 验证。真实运行仍需记录所有 `cloud_opt/dust3r/src.dust3r/models` 的加载文件，拒绝源混入。

## 4. 冻结前仍需的兼容、observer 与独立检查

1. **重放/拼装**：真实运行准备阶段核 archive SHA→`allow_pickle=False`加载→tensor逐字段无损往返；原 AST star拼装与独立简洁参考实现，对所有被消费 tensor/idx形状和值精确一致。8个图以S21原 `load_images_for_eval(crop=True)` 和VMem原PIL入口分别预处理，比 img/shape/idx逐tensor一致；RGB重解码是新增数据处理，日志计数，非新增模型。若不一致先停止定位，不做额外 resize 或填假图。
2. **与既有兼容边界分开**：S21 原CUT↔TTT源CUT的4帧六头通过 `atol=5e-4,rtol=1e-4`，不是bitwise；S22共享精度的CUT4同样通过。不把这些结果扩大成8帧/嵌入CUT的逐值等价。此阶段的严谨名称是“封存三基线预测经同一原VMem消费者”，不称原生成pipeline整机复现；无新模型等价测试由此偷偷省略的承诺。
3. **原 GA 事件**：待写只委托 observer 记录进入optimizer的点/权重、MST/PnP成功或fallback、preset后的parameter requires_grad、400次global_alignment_iter及400次真正Adam step、最后objective、clean前后字段。第一次只读observer必须返回原对象、不得更换优化器或skip失败边。原S17C observer/scorer硬编码2图，不能直接套用其PASS；须改写为新文件并独立审查动态4/8图与3/7边。
4. **给定约束与数值重建**：单独核共同相机 SHA和旧depth SHA相同，参数冻结正确。在preset完成后保存pose参数/旧depth log参数的快照，要求这些参数经过MST、400步GA及clean仍逐元素完全不变，且focal仍requires_grad=True、后4depth仍requires_grad=True。输出c2w通过rotmat→quat/signed_log1p→expm1重构、旧depth通过log/exp重构，均可能有FP32舍入；返回值与原共同输入比较建议 `atol=1e-5,rtol=1e-5`，不可要求字节完全相等或偷偷覆写返回值。用独立 NumPy 从最终 depth/focal/pp/c2w重建world点；完整重算clean，核clean只改conf；独立原目标复算。所有容差须父任务在读真实结果前冻结，沿用S17C原公式/累加误差依据，不以结果后放宽。

## 5. 隔离深度评分与最小保存量

共同相机是输入；**传感器深度是评价数据**。A/B/C/D全部GA预测封存后，独立 scorer 才能打开GT depth PNG。它不得把这些depth回传producer。按既有S23 RGB-depth配对和像素映射协议读取：首8帧8/8有匹配文件，|dt|为6.081–13.984ms；只有元数据覆盖已核，真实有效像素数量未知。来源清单及文件size见 `candidate_inputs.json`，本轮0 PNG读取。GTdepth不能作为A的旧depth，也不能用于初始化、筛帧、决定迭代或事后挑最佳step。

**GT depth 身份的执行前缺口**：本轮继承的S23 manifest没有逐PNG内容SHA，路径/size/metadata哈希不能证明PNG字节身份。保持当前0 PNG读取；若父任务可从既有可信seal找到逐文件SHA，可只读该JSON继承并在评分时核验。否则须等A/B/C/D全部封存后，独立scorer先将本轮实际8个depth PNG字节封存为新快照（逐文件SHA、时间、父预测seal），再解码，并明确它不是历史已封存的PNG身份；评分每次重新核对。不得把新评分期快照追溯标为S23历史输入seal。

主要比较索引 **4–7的新深度**，共同旧0–3只用于约束保真检查，不能混入平均值制造三方法接近。使用原尺度、共同像素分母的 AbsRel/RMSE/delta1/无效预测量；不施加逐方法/逐帧median scale，不按clean置信丢弃难像素。另报告clean保留率；它不等于真实可见性准确率。本次不执行自由pose ATE评分；300/796帧ATE不能与4帧depth误差直接比较后宣称排序传递/反转。若未来正式提出排序传递问题，须另冻相同帧/支持范围的可比诊断。

每作业至少保存：实际GA输入点/conf与有序edge IDs；共同条件引用SHA；preset参数mask；MST/PnP记录；完整400步轨迹；clean前后 `world_points/depths/conf/poses/focal/pp/pw_poses/adaptors`；最终原wrapper五字段（colors来自真实view，不来自rgb head）；数组schema/SHA、源模块与环境、caller资源记录和完成seal。高密度快照只在必要阶段保存，400轮记录标量，不存400份点云。小组件若发现消费者depth没有改善，只能报告代理排序未传递；即便有改善，也仍缺Surfel可见性、真实context和长生成闭环。

父任务已指定正式主输出布局：`results/S26_consumer_baseline/{common_old,cut3r,ttt3r,filt3r}/output.npz`，keys为 `depth[N,H,W]`、`point_cloud[N,H,W,3]`、`conf[N,H,W]`、`focal[N,1]`、`pp[N,2]`、`c2w[N,4,4]`；A的N=4，其余N=8。原wrapper返回字段与这些稳定名称的转换/封存由父任务runner完成；额外observer快照另存，不替换主输出。父任务维护监督runner，独立agent维护评分器与审查；本目录只负责adapter、plan和metadata，不执行实验。正式运行须等待S24结束，避免CPU资源竞争。

## 6. 资源建议与退出条件

建议待冻上限：A 600秒，B/C/D各1200秒，CPU8，单进程树RSS16GiB，启动前空盘≥10GiB，四作业顺序执行；总上限4200秒。无GPU、无权重加载，预测/GA数组应远低于整模型常驻成本，但这只是资源推断。参考S17C2图模型+400GA+保存约33.4秒/6.4GiB的历史记录，**不能线性承诺8图耗时或RSS**。外监控超时/超内存则terminate、10秒后kill，保留已写结果；不自动减分辨率/改迭代/换帧/重跑。正式runner尚未写出，adapter自身不执行监控。

任一输入身份/字段/预处理不符，源混入、共享条件不一致、MST/PnP异常、给定约束被更改、niter/step计数不符、非有限量、独立公式或clean核验失败，都停止该pilot并保留失败；不得把失败处理改成方法特有逻辑。短前缀没有足够基线运动、误差几乎相同或对随机初始化敏感时，结论保持“兼容pilot不足判别”，不能临时选择更有利片段。

完成本pilot后，下一门仍是：扩大到预先选择的真实自然失败和更长历史，加入原Surfel/检索消费者，再完成实际生成闭环。不得用8帧/4个GA作业宣称创新成立、PhD/CCF A目标完成，或以几何代理实验替代原 proposal。
