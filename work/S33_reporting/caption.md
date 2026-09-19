# S33 四条件结果图

已保存的主评分显示，普通公共pair尺度约束在三个可评分窗口的平均AbsRel都低于零步和事后公共比例恢复；不同作者的保存量算术复核已实际通过（UTC 20:39:24.560079–20:39:28.089159），本图据此更新核验状态。前3条件从S32原值导入，分别为零步、修getter的原400步、以及该终点使用自身零步估计一个公共k的事后恢复；第4条件为S33新增400步，约束三条有效pair尺度的几何均值保持该窗实际初态值，并不分别冻结每条pair尺度。符号展示全部48个实际帧点，每条件从左到右是帧0–3，黑横线与数字是4帧等权均值；首窗缺给定相机而保留16行NA，全4窗总体均值仍为NA，AbsRel为绝对相对深度误差百分数，越低越好。相机使用给定GT光学位姿，场景及本批约0.10秒短窗已有曝光，相邻帧相关，不做帧/像素独立样本显著性或CI；没有GT尺度拟合、confidence mask或far-depth cut。此为普通对照的局部真实结果，不是新算法、优化根因、长时记忆或生成视频收益证明。

源：results/S33_pair_scale_scoring/metrics.json与per_frame.csv；原三控由imported_s32_metrics.json及imported_s32_per_frame.csv完整保留，图脚本核旧48行与CSV字节前缀一致。全部64条（含16NA）、12均值、单位与坐标、來源SHA见plotted_data.json；没有打开NPZ或传感器PNG重算。

独立回执：[receipt.json](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S33_independent_numeric_review/receipt.json>)，SHA256 `057b369b82e6b16af640222c16ada5536f67851b06dee7d248ce61eee6d21b0e`。复核覆盖完整64行、原48导入、新12评分及4NA、保存的优化/梯度/尺度记录和边界量；未重新反传或做外部物理世界复现。`plotted_data.json` 保留首次制作时全部字节，包括当时的 PENDING 历史标记；当前状态以本图和本回执为准。旧图/脚本/回执已保存到 `history_v1_before_verified_status/`。
