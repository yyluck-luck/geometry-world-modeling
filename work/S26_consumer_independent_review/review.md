# S26 原 VMem 消费者 pilot：独立静态可行性审查

**裁决：源码与候选输入准备通过；真实执行尚未就绪。** 本裁决绑定作者最终 plan/adapter；root 后续新增执行脚本另行审查。当前 adapter 保留了原 VMem 的关键消费者语义，可以继续完成 supervisor runner、observer、scorer 与冻结合同。这里没有运行模型、GA、真实 NPZ、RGB 或 GT 深度解码；16 项检查是源码／元数据检查，不是数值兼容实验。准确版本、实际时间与范围见 [review_receipt.json](review_receipt.json) 和 [static_check_receipt.json](static_check_receipt.json)。

本审查服务用户指定的第 2 章路线：强 baseline → 真实剩余失败 → 新机制。S26 的完整 8 帧仅约 0.235880 秒，其中旧 4 帧、新 4 帧；这个 pilot 最先解决接口与受约束消费者可测性问题，不能据此宣布自然失败、方法创新、Surfel/检索改善或生成成功。

## 1. 已独立核实的路径

原 VMem commit 为 `39291e4f272f6b4f270691d930926ab5930f942e`。本审查直接读取原仓库相关源码，并将实际使用的 S17C isolated source 与其比较。wrapper、PointCloudOptimizer、BasePCOptimizer、MST 初始化、image utilities、pipeline 六个相关文件均字节相同。S26 source binding 中 203 项源码及控制元数据哈希也全部匹配；这不表示已逐行审查全部 203 个文件，也不表示重新验证了所有第三方数值依赖。

独立 AST 对比确认：`listify`、`collate_with_cat`、`prepare_input_from_pil`、`prepare_output` 四个完整函数保持原样；原 wrapper 的星形拼装区域仅删除网络 `inference` 调用，其余 11 条原语句保持原 AST，再返回 output。S17C 的既有三处透明补丁属于 RoPE/模型加载路径，没有借本轮更改 GA 数学；此次不实例化网络，不能由此宣称不同 backbone 全头等价。

| 环节 | 实际原行为 | S26 对应合同与注意事项 |
|---|---|---|
| 历史重放和 anchor | 每次原几何调用处理全部历史，星形有向边为 `(0,j)`，anchor 是历史第 0 帧 | 候选必须是完整前缀 0–7；4+4 只是受控组件分解，不假装默认导航 chunk，也不把旧 4 帧设成 4 个互换 anchor |
| GA 点与置信 | `pred1.pts3d_in_self_view/conf_self` 反复来自 anchor0；`pred2.pts3d_in_other_view/conf` 来自 j≥1 | adapter 保留六头以保持来源，但 raw camera_pose、非 anchor self、预测 rgb 均不能代替实际被读的头 |
| 相机 | `preset_pose` 逐相机写入参数后冻结完整 im_poses；关闭 pair scale normalization | 所有 B/C/D 作业必须使用同一份已封存相机 tensor；相机是已知控制条件，不是该实验要预测的相机 |
| 旧 depth | `preset_depth` 的 zip 只写入所给的前 4 张 depth 并冻结相应 Parameter；MST 的后续 `_set_depthmap` 对已冻结项不覆盖 | 共同 old4 只能由 original4 + 共同前4 pose + depths=None 的一次原 GA 产生；传感器 GT depth 禁止进入该 prior |
| 内部参数与输出 | depth 以 log 参数保存、输出 exp；pose 经 quaternion 和 signed log/expm1 编码 | 正确的“冻结”证据是 preset 后参数到 MST/GA 后参数不变；输入 depth/c2w 与解码输出可能有 FP32 往返误差，不能要求字节相同，更不能覆写输出来消除误差 |
| 最终几何 | world points 由最终 depth、focal、pp 和固定 c2w 重建；focal 可优化，pp 默认固定，pairwise poses/adaptors 仍按原逻辑优化 | 不可用 pose×self 或 raw other 代替原 GA 输出。旧 depth 固定不意味着 world point 不变，因为 focal 可变 |
| clean | clean 只替换 im_conf，不应改 depth、pose 或 points | 需要保存 clean 前后字段；clean 保留率不等于真实可见性正确率 |
| 优化次数 | 原循环每次前向 loss→backward→Adam step；返回的是最后一步更新之前的 loss | 最低四作业合计计划 1600 个 step。若另算最终目标必须单列调用，不将它算成第 1601 次优化或偷偷新增训练 |

源码位置：原 `surfel_inference.py:174–214,348–398,449–526`；`optimizer.py:102–121,146–166,206–261`；`base_opt.py:132–154,236–267,349–359,474–485,533–577`；`init_im_poses.py:78–139,349–382`；`pipeline.py:950–1056`。实际文件绝对路径和哈希见回执。

## 2. 光学坐标与相机输入

原 pipeline 将内部 c2w 的 Y/Z 列取负后传入 wrapper。若 `F=diag(1,-1,-1,1)`，右乘 F 是相机基变换，左乘不是同一操作。S26 从 TUM 得到光学 c2w 时，应直接传 `prepare_output`；若先表达为 pipeline 表示，则 `C_pipeline=C_TUM F`，再走原翻转恢复 `C_TUM`。不要对已经是光学坐标的 TUM 再翻一次。

本轮只核源码和合同，没有读 TUM pose 坐标。后续共同 control producer 必须记录真实坐标解析时点、固定配对的 `gt_time`、源内容身份、FP32 转换、底行／SO(3) 检查及最终共同 tensor 的 seal。不能逐方法独立解析或拟合相机，也不能继承旧日志中的“未使用 GT 坐标”标签。这里的 GT 相机是明确的 oracle camera control，不是盲测或可部署定位结果。

最便宜的坐标核验是在真实 GT 读取之前，用一个非平凡旋转和平移的人工 SE(3) 验证右乘 F 两次恢复原矩阵、+Z 光学射线及世界点变换方向；这只验证代码约定，不构成相机数据正确性证明。

## 3. Preprocessing 与封存头兼容

源码显示原 VMem PIL 入口与 S21 使用的 `load_images_for_eval(crop=True)` 都经过 EXIF transpose、RGB、最长边 512 的相同 resize 选择、16 对齐中心 crop 和相同 ImgNorm。当前 384×512 shape 合同合理，但相同 shape 不证明像素或张量相同。

真实执行前先做不含模型、也不含 GA 的兼容步骤：

1. 以已封存 RGB 身份加载全部 8 图，分别经过两条实际入口，检查完整 img、true_shape、idx 和所需 view 元数据一致。记录此次 RGB 解码，而非声称仍是 metadata-only。
2. 核验 28 份候选 archive 内容 SHA，再以 `allow_pickle=False` 加载，检查六头 schema、有限值和合法 conf；NumPy→Torch→NumPy 应无损。这里保留生产来源，不能用新的 tensor 加一个字符串冒充旧 archive。
3. 用独立简洁参考实现验证原 star 拼装的有序边和全部被消费 tensor。当前已完成 AST 保真，不是这一步的真实 tensor 检查。
4. 背景的 S21 原 CUT↔TTT 源 CUT4 容差兼容、S22 共精度 CUT4 检查不能扩大为原嵌入网络完整复现，也不能证明 8 帧或 300 帧逐值等价。严谨名称是“封存三基线预测经同一原 VMem 消费者”。

`configure_original_geometry` 的 fresh-process 要求、源身份和核心 NumPy/Torch/SciPy 版本检查有意义；未来 runner 仍需验证实际加载的 `cloud_opt`、`dust3r`、`src.dust3r`、`models` 文件及完整依赖身份。当前历史 import PASS 不能被写成本轮实际 import 成功。

## 4. 执行前尚缺的具体实现

这些是尚未实现的工程验收条件，不是要求用户额外授权。可以继续自主实现；当前不能直接把 adapter 当完整监督运行器启动。

| 缺口 | 必须实现的行为 | 最便宜的核验 |
|---|---|---|
| supervisor runner 与冻结合同 | 四作业 A→B/C/D 串行，独立进程、固定 seed/CPU8、资源上限、拒绝覆盖；源、输入、协议和工具实际身份冻结；失败保留且不自动改配置重跑 | 在不启动模型/GA的控制 fixture 中检查依赖门槛、失败退出、seal 身份不符即停；之后只跑最低计划的四个真实 GA |
| common camera／old-depth 内容绑定 | 共相机 tensor 来自已记录的控制 producer；A 输出完整封存后才可运行 B/C/D，三臂读同一深度内容 SHA | 作者最终 adapter 已增加 depth tensor 内容 SHA 和前4 pose tensor SHA 检查；runner 仍须从可信 A 生产 seal 取得这些预期值，不能临时自算并自证来源 |
| 动态 4/8 图 observer | 记录 3/7 条边、preset 后参数和 requires_grad、MST/PnP 状态、400 iter/400 Adam、完整标量轨迹、clean 前后数据；observer 原样委托且不改变返回对象／RNG | 小型人工接口 fixture 先验证日志不改调用语义；实际四作业内记录，不无故另重跑整 GA |
| 冻结保真 | preset 后记录 im_poses 和旧 im_depthmaps 参数；MST 和 GA 结束后参数逐值不变，requires_grad 和优化器参数集合正确 | 比较内部参数快照；输出与原输入按预先容差核算 log/exp、quat 往返，不能看结果放宽 |
| 独立数值复核 | 最终 depth/focal/pp/c2w→world point、原 loss 和 clean 有独立计算；控制容差在真实结果前确定 | 先人工非平凡几何 fixture；实际输出封存后运行独立计算。旧两图 S17C 检查不能直接宣称覆盖本次 4/8 图 |
| GT depth 内容身份 | 当前候选深度仅有路径、size、时间；root 已指定评分器继承 S23 gt_receipt 的逐 PNG SHA。评分器实现尚待审查，candidate JSON 哈希不能替代图像内容身份 | 若已有 S23 的对应 depth seal，可继承并在评分阶段验证；否则全部 GA 封存后先建立本轮 depth 字节 seal，再解码。必须称后建快照，不能追认历史封存 |
| 隔离 scorer | A/B/C/D 全部封存才打开传感器 depth；不得回流 prior、筛帧、调迭代、尺度拟合或阈值 | 主评分只用新帧4–7；共同 GT 像素分母，报告无效预测、全部有效像素、原尺度 AbsRel/RMSE/delta1。旧4只检查约束 |

不要以“原 default 会 fallback”掩盖某臂独有的失败；至少记录实际 MST/PnP 路径，按冻结规则决定停止或将共同原 fallback 明确作为协议行为。不要以最后返回 loss 代替最终更新后独立目标。最终图像和数值交付仍需实际检查。

## 5. 如何解释 pilot 输出

这轮可确认接口是否忠实、共享条件是否真被固定、不同已保存网络头经同一消费者后有什么差别。**数值有差别不等于变好**；几何评分变好也不等于 Surfel、检索或视频变好。root 已收窄本 pilot，只评分新4帧深度，不执行8帧自由 ATE或排序传递结论。若未来另行研究排序，须另冻相同支持范围的可比诊断；不能拿300帧整体ATE排序与4张新帧depth排序直接对比。

0.236 秒短前缀没有展示离开、回访、自然遗忘或长历史冲突。完成 pilot 后仍需独立选定真实失败条件、给出机制假设并排除近邻方法／简单解释，再扩展到 Surfel 可见性、context 身份和实际生成消费者。普通接口适配与缓存可以支撑实验，但不是创新主张。

## 6. 本轮工作范围

已读项目 `RESEARCH_MEMORY.md`、`IDEA_GENERATION_FOCUS_CURRENT.md`、S25 consumer relevance 和 S26 plan/adapter/元数据；已核相关原源码、source identity 和 AST 变换。没有读取真实 NPZ/header、GT coordinate、RGB/GT PNG 字节，没有模型/GA/import 数值试验，没有改被冻结 S24/S25、主账或作者文件。只在本审查目录写入独立产物。

阅读与源码核验已经完成；执行准备仍需上列 runner/observer/scorer。未执行项目不得用这份静态审查代替实际回执。
