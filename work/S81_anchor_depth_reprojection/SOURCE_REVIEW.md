# S81 实现前不同作者审查

实际完成 UTC：2026-09-10T17:10:25.096938+00:00。

**结论：PASS_FOR_ONE_BOUNDED_EXPLORATORY_EXECUTION。未发现实质 blocker；允许 root 对下面的精确版本执行一次合同内的有界探索。** 该结论不是实际运行成功、数据已对齐或物理真值验证。

- `run_reprojection.py` SHA：`ce9f929e2d106b831144a262ff9f616e4e45d5ba8d82f733fc1af70524cd8d73`。
- `CONTRACT.json` SHA：`ae317145a909f12fe94cd0ad221fa54da1a032855f585b73bc996b3ec0cc57a4`。
- 原独立纯数学参考 34/34；针对这份实际实现另外调用 `sample/project` 的 28/28 合成检查通过。
- 测试只导入受 `__name__` 守卫的模块并调用两个纯帮助函数，没有调用 `main`。0真实 RGB、深度、NPZ、GT 文件读取；0网络、模型或匹配；125页报告不变。

## 四项最小门

**G1_INPUT_IDENTITY_AND_TIME：PASS_FOR_DECLARED_APPROXIMATION。** 合同锁定S8原RGB19/depth关联，深度晚17.126ms；Z=raw/5000、零值缺失、OpenNI RGB注册、1.031已应用来源由SOURCE_FEASIBILITY提供。新PNG只在实际执行读并核SHA/bytes/16bit grayscale/size。沿用原光学metric c2w与FP32-origin K；明确不作时间补偿/轴翻转/重新标定。不同步仍是限制。

**G2_PURE_GEOMETRY_AND_BOUNDARIES：PASS。** 原独立精确Fraction34检查作为数学参考保留；实际root sample/project另用人工数组28检查通过。新增明确覆盖冻结的<=639/479及<=575连续域、half-up、零深度、NaN、后方/epsilon、平移/旋转方向、Z而非range及出视野保留。

**G3_FIXED_SCORE_CONSUMPTION：PASS。** main受__name__守卫，合同/源码必须匹配传入SHA；不存在RGB/匹配器/模型/网络调用。depth只用于评分；1313源点先唯一取样并对四目标缓存投影，各arm/matcher复用。逐点检查期望点在原目标极线以及点误差>=目标单向线距，不错误使用双向均值。

**G4_DENOMINATORS_AND_PAIRING：PASS。** 锁定24行与7757记录，source N1313；原接受索引/源xy身份回读核对，全部记录保存、无效为NaN/null/空CSV字段并有原因。M/V/N与无效数、出视野有限误差保留，阈值无真值准确率主张。28组固定shared-source比较，交集缺失保留；同目标图完整BF/LG相同特征边作相等检查。

## 保留的非阻断限制

1. **边界规则差异已明确核对。** 原 `synthetic_review.py` 采用连续域 `[0,width)`，合同采用 `0≤u≤639, 0≤v≤479`，后者更保守。不能把原34项直接冒充候选覆盖。新增实现测试具体核了639/639.2、479/479.2、575/575.2；源576坐标(575,575)映射到(559+1/6,479+1/6)，按本合同记SOURCE_OUTSIDE，虽取整索引仍在数组内。保留该规则，不建议在读结果前临时扩域或改源码。
2. **真实时间与成像近似仍未消除。** 17.126ms错位、近似ROS K、未额外去畸变、最近邻深度赋给未取整特征射线等已写入合同。没有目标深度不是本批blocker，但visibility始终UNKNOWN；出视野的有限正Z误差仍进入主量。没有声称传感器Z是精确同步表面真值。
3. **执行范围是这份冻结S80档案。** M分母处未为任意未来空行写通用兼容代码，但此合同固定24个非空旧匹配行且核身份，因此不阻止本批。共有源点交集为空时量为null；未来换输入不能沿用本票。失败会停止并保留失败回执，不得把不完整输出写为24行成功。
4. **字段语义应在读出时说明。** ALL_RECORDS.csv的target_id是目标feature index；目标帧、arm和matcher从row_id识别。不得把这个列当20–23帧号连接。PAIRED.json里的target_feature_id已经明确，未发现计算连错。

测试覆盖：零运动子像素恒等、已知相机平移及方向、Z与range区别、源/目标旋转的转置方向、名义576逆裁剪、floor(v+0.5)、严格连续域与取整、零深度/NaN、Z≤epsilon/相机后方、出视野仍有效、沿极线差30px但线距0。人工样本不证明真实深度有效率或真实投影误差。

## 实际执行与后审边界

root可执行这份精确合同/源码一次，60秒预算、唯一execution_01目录，不自动重试或调参。实际读入时仍须通过冻结的SHA、字节数、PNG/数组身份、相机逐值一致与几何恒等检查。本票不提前声称这些真实检查已通过。

后续由另一作者复算保存量及分母，判断应保留的最窄结论。新的源深度评分不能把错误匹配变成已知物理对应，也不能把二维点误差直接等同S80的双向点到线均值。当前依然是已知观察器的有界诊断：NO_METHOD_SELECTED / novelty_authorization=NONE / new_method_validated=false。

可复核文件：SOURCE_REVIEW.json、synthetic_review.py、SYNTHETIC_REVIEW.json、implementation_synthetic_review.py、IMPLEMENTATION_SYNTHETIC_REVIEW.json。实际来源核查使用已读的SOURCE_FEASIBILITY.md与SOURCE_PATHS_AND_HASHES.json；其历史二进制SHA不冒充本轮新像素读取。没有增加框架或重复全历史检查。
