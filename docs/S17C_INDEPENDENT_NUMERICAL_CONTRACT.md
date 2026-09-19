# S17C 独立数值核验规则（真实运行前固定）

本合同只验证 S17C 保存的原 wrapper 组件输出和身份，不评价 GT 几何质量、surfel memory 或视频。由不同作者在 S17C 真实运行前准备；不读真实照片或权重，不改 S17B。最终 SHA 与准备时间保存在 `work/S17C_independent_preparation/numerical_contract_receipt.json`，runner/schema 完成后另有正式代码前审。

1. **世界点/相机。** 使用 NumPy float64、分量反投影及独立 c2w 变换，由保存的 camera-z、focal、pp、R/t 重构每个像素的世界点。固定 `atol=1e-5, rtol=1e-5`，完整报告最大绝对误差与容差失败像素数。正旋转 `R^T R` 和 det 使用 `atol=1e-4, rtol=0`；相机底行 `[0,0,0,1]` 精确，主点 `(256,192)` 精确，焦距/深度必须有限正数。原 raw pose head 另用 SciPy quaternion 复算，不要求它等于优化相机。

2. **clean 主门。** 原 Torch FP32 结果和独立 NumPy FP32 分量路径对比。逆矩阵用 NumPy，逐分量按 FP32 运算构造 camera point，再按原 K 乘法的齐次分子顺序投影；`np.rint` 对应 ties-to-even。保留原 i→j 顺序、`res` 更新、z>0、严格 `< .999*depth` 和严格低置信筛选。**最终全部置信像素要求 exact 相同；任何 mismatch 均使数值核验 FAIL 待解释，没有预授权“边界例外”或排除像素。** 此要求是预定的验收规则，不是预言浮点路径会不一致。

3. **边界证据。** 无论是否 mismatch，保存两个有向比较的投影 xy、z 距 0、xy 距最近半整数、valid mask、depth margin=`z-.999*target_depth`、confidence margin=`current_source_conf-current_target_conf`。无效投影对应 margin 为 NaN，只是诊断字段，不作为主输出数值缺失。最终保存整个图域的 mismatch mask、expected/actual cleaned confidence 和全部坐标索引，不只取少量示例。若发生差异，这些是独立路径的 margin，不冒称已保存原 Torch 中间值。事后进一步诊断须单列，不覆盖原 FAIL 或看完结果调容差。

4. **clean 不改几何。** scene before/after 的 world_points、depths、poses、focal、pp、intrinsics、pw_poses、adaptors、colors 精确不变。raw confidence 的单边聚合：image0=raw frame0 conf_self，image1=raw frame1 conf；clean 后可为 0。最终 wrapper 对应 fields 必须与 after-clean 保存值精确一致，不通过再缩放或旋转纠正。

5. **目标与迭代。** 原 `dist='l1'` 其实是逐点三维欧氏 norm，非坐标绝对值之和。独立用最终 world_points、原两端预测点/原 log confidence、scaled pw_poses 与 adaptors 重算目标，逐端完整 area 均值后相加，NumPy float64 + math.fsum。与额外一次无更新 postfinal objective 固定 `atol=1e-5, rtol=1e-4`。该计算不是用 clean confidence，也不等于原第399步更新前的返回 loss。保留400个真实 idx 0..399 与有限 loss；学习率误差 `atol=1e-12, rtol=0`，.01 至 .0000259975。不要求逐步 loss 单调。

6. **颜色和数据域。** 仅使用封存 processed input tensor 反归一化 `(x*.5+.5).clip(0,1)`，RGB/BCHW→BHWC，要求 scene 和 wrapper 的 color exact 一致。无需重新解码 RGB，更无 GT；不以预测 rgb head 代替实拍颜色。

7. **来源/资源门。** SHA 绑定 manifest、完整输出 seal、runner/所有数学辅助/协议与 source/overlay 身份；固定两图、一真实 forward、零有效 ray/query/主生成器/VAE/CLIP/GT/video，400 geometry steps 和一次只求值 postfinal objective。正式 CLI 和全部数组 schema 待作者完成后固定。外600秒/32GiB资源要求保持；不同作者独立核验不再跑模型，资源与开始/完成时间另记。

本核验可产生 PASS/FAIL，并必须保留失败目录。程序接口或字段未完成不能提前标 PASS；人工数组通过仅标 `PASS_ARTIFICIAL_ONLY`。
