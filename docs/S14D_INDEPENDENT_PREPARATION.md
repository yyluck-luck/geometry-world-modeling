# S14D ray-only 独立核验准备

入口为 `scripts/verify_s14d_ray_only_independent.py`，准备回执为 `work/S14D_independent_preparation/receipt.json`。本阶段只编写核验器和运行人工数学/数组例，没有运行真实模型、解码真实NPZ、读取图像或GT。实际源码SHA和时间以回执为准，根冻结后调用。

已读当前AGENTS、RESEARCH_MEMORY、最新RESEARCH_LOG及 `docs/S14D_GENERATION_INTERFACE_AUDIT.md`。S14C的负结果与成功计算保持原样。本次只补“20张历史RGB建立状态后，可否在无目标照片时进行给定相机查询”的技术接口证据，不检验几何准确性、检索质量、新颖性或视频生成。

本作者沿用此前已实际阅读的本地 `sci-scientific-critical-thinking` 技能：独立方法复算、信息边界、输入/状态/结果身份与结论范围。未调用Claude模型或CLI。生产作者的runner只读取CLI、输出和metadata字段以对齐接口；不读/导入它的ray计算函数，也不导入torch、CUT3R或旧实验测量模块。只额外阅读官方 `camera.py` 中平移与四元数的保存语义，用另一种旋转表达式独立核历史pose编码。

根当前合同覆盖接口审计中的建议值：用S8 block0前20张历史RGB，新推理状态固定。基准为这次推理的最后历史c2w；相对首历史t0的20个平移距离中，取严格大于1e−6者的中位数，再乘0.05得到d。四个局部偏移为0、+x、−x、+z；局部偏移乘最后历史R后加t，不能直接沿世界坐标轴移位。所有距离在预测尺度中，不称厘米或米。

独立数值核验使用以下不同实现：

- 历史20个7维pose编码：将实部在前的四元数归一化，以Rodrigues矩阵式 `(w²−v·v)I+2vvᵀ+2w[v]×` 重建R，核保存的20个c2w；不调用官方逐元素矩阵解码函数。
- ray：对每个整数像素u/v分别展开 `(u−cx)/fx,(v−cy)/fy,1`，用标量乘法、`math.fsum`、`math.hypot` 计算 `origin=t; encoded_direction=normalize(R K^-1[u,v,1]+t)`。这里保留平移t；它不是普通纯旋转方向，也不是Plücker表示。四幅224×224×6输入全量比较。
- 固定K为fx=fy=√(224²+224²)、主点(112,112)，不从目标照片/GT估计。

计算浮点门固定为 `abs(actual-reference)<=1e-6+1e-5*abs(reference)`，不使用纯绝对1e−6门。FP32存储的焦距与双精度公式会有约数个1e−6的舍入差，仍需按预定组合容差判断；输出响应的1e−6阈值是另一个固定诊断定义。

四个主NPZ必须全成员为非空有限数值数组且无重复键、无object加载。`probe_inputs.npz` 的五项shape和有效ray FP32强制核对；query输出按call0–4逐键核全量，必须有两个pts3d、两种confidence和camera_pose编码，可有额外动态tensor，不能只核required键而忽略其他输出。call0的NaN占位与call1的zero占位必须在所有保存tensor上shape/dtype/原始字节完全相同。另有五份query_call_i.npz，逐字段shape/dtype/C连续字节与已验证有限的合并输出精确相同，从而核对每次实际落盘快照与最终结果一致。

state_before/state_after必须恰好五个字段state_feat、state_pos、init_state_feat、mem、init_mem。核每项shape、dtype、finite与C连续字节SHA，原值逐字节相同；每个调用记录的五项SHA必须都等于实际before快照。逐调用的flags、输入shape/dtype、显式H/W、目标camera_pose、输出键和时间顺序也会核对。图像打开尝试、成功打开、实际解码的三份路径台账必须按顺序精确等于冻结的20历史文件，query图像编码器batch为0、ray编码器调用为5。

三个移位target的两个pts3d字段分别计算相对基准最大绝对差，再核runner的max和 `>1e−6` 布尔值。**FALSE会保留为“未检测到该阈值以上的条件响应”，不会使技术接口核验自动FAIL。** TRUE也只表示输出随条件变化，不表示变化正确或有实用价值；不对confidence/rgb好看程度做质量筛选。

运行前先核manifest绑定、调用者退出/超时/内存记录、所有冻结源/输入身份，以及结果的保存SHA；固定完整13载荷为四主NPZ、五call NPZ、frozen_manifest/source_snapshot、checkpoint_load.txt和extracted_ray_factory.py。两个辅助文本只核SHA，不当成NPZ，也不导入/读取其ray函数内容。验证全部字节后才解码NPZ。结束再核输入/结果/manifest/caller/自身源码身份。独立程序不重新运行模型，不读取目标RGB、GT、旧query预测或质量评分；冻结文稿/源码/历史RGB的身份检查只读取字节SHA，不解码成评分资料。冻结身份中的所有图像必须恰好是20历史图，不允许旧NPZ/NPY输入；官方模块记录必须属于已冻结源码集合。

调用者必须schema=s14d-caller-v1、status=PASS、monitor_ok=true、returncode=0、没有timeout/RSS越界，manifest与实际命令的Python/runner/输入输出参数均匹配。核限值600秒/34,359,738,368字节、实际elapsed与maxrss在限值内，并确认probe时间位于caller起止时间内。这些预算控制不是性能优越性证据。

```sh
python3 scripts/verify_s14d_ray_only_independent.py --manifest docs/S14D_EXECUTION_MANIFEST.json --result results/S14D_ray_only_probe --caller work/S14D_execution/caller_receipt.json --output results/S14D_independent_verification
```

路径由根最终合同确定；输出目录已有即拒绝覆盖。新目录保存核验源码快照、UTC/环境、各项有含义的数组/字段检查、首个错误上下文和完整失败traceback。不通过人工放大检查计数来充当样本量；四幅射线的200,704个像素仍只来自这一技术probe。

准备的16个人工检查覆盖：90°已知四元数、局部坐标偏移与中位数、中心像素含平移的手算方向、全部像素与显式解析参考式相符；五次调用/五状态字段、可选RGB的dummy差异拒绝、state突变与有符号零字节差拒绝、零四元数/静止历史/非有限NPZ/错误K/零长度encoded direction拒绝。完整人工4×224×224输入和五次假输出中有一个移位输出保持不变，核验照常通过且该响应诊断为FALSE。人工例并非真实模型结果。

随后按根要求补了一次完整runtime接口人工检查，固定13载荷/9个NPZ、五份逐次快照、完整call metadata与caller预算字段，共398项有含义的字段/数组核验PASS。没有外部执行生产runner或模型；人工源占位、图像字节占位、全零预测、计数和2000年的时间戳都是明确标注的测试字面量。只有独立核验程序实际运行。fixture路径、实际检查UTC和SHA见准备回执；这个接口检查不替代前述独立数学对照或后续真实模型probe。
