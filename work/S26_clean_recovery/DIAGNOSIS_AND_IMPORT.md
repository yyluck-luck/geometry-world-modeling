# S26 原 clean 失配诊断与保存结果导入

结论：这次失败由独立参考的 FP32 数值路径不同引起。原 clean 能精确重放保存结果；修正数值合同后的独立公式也逐字节相同。原 S26 仍为 **FAILED**，没有追认成 PASS。另经29项保存量核验，这份已完成400步的 common_old 可按新 S26B 合同显式导入，结论为 **IMPORT_VALIDATED**，无需重复400步。

原失败发生于 UTC 2026-09-06 15:37:36.803991，外控21.692806秒。独立 clean 诊断实际执行于15:45:42.808228–15:45:44.440792，1.632417秒；保存量补核实际执行于15:55:14.373349–15:55:15.694898，1.321563秒。上述是实际程序运行时间，不是学生工时，也不是新模型或新 GA 的耗时。

## 失配是什么

最终4×384×512=786432个置信度值中，旧 NumPy 参考失配12个，四帧分别为2/2/3/5。全部保存的 `clean_mismatch_diagnostics.npz` 数组已重新计算并逐元素核对，包括所有12个交叉视角，未抽样或豁免边界。

原代码先以 `torch.linalg.inv` 求 camera inverse，再做两次矩阵乘法，随后 round 得到目标像素。旧参考改成逐相机 `np.linalg.inv` 和分量相乘相加。两者数学公式相同，但 FP32 的计算次序和实现不同。四个逆矩阵共64个元素中44个不完全相等，最大差1.1920928955e-7；全部12个跨视角投影最大差0.0010681152像素、深度坐标最大差2.3841857910e-7米。

这些差值没有被当成可忽略项。原算法根据整数像素查深度和动态置信度，小的坐标变化可以改变完整逻辑分支。12个最终失配中，11个由半像素取整改变查表坐标造成，另1个来自此前清零结果的传播。

例如 frame0 的(row226,column69)投向 frame2 时，原 y=214.4999389648，旧参考 y=214.5001220703，分别查第214与215行；原规则清零置信度，旧参考保留8.505985。frame3 的(row335,column338)两者都投向 frame2 的(row346,column345)，但该目标点已经受另一处取整失配影响，导致后续置信度比较不同。

`all_mismatch_pixels.csv` 列出全部12点；`all_mismatch_pair_traces.json` 保存这12点在全部36个相关有序对中的投影、取整、深度/置信度余量及前后状态。`mismatch_classification.json` 给出逐点分类和传播链。全部7条数值路径各检查12对、每对196608点，84行总比较在 `all_pair_comparison.csv`，全部 full-grid bad masks 在 `all_12_pair_bad_masks.npz`。旧路径总共515个 pair-pixel 的整数查表坐标不同，不等于515个最终置信度失配。

## 定位不是放宽容差

| 逆矩阵来源 | 乘法路径 | 最终失配数 |
|---|---|---:|
| Torch | Torch matrix multiplication | 0 |
| NumPy逐个 inverse | NumPy分量乘加（旧参考） | 12 |
| NumPy逐个 inverse | Torch matrix multiplication | 8 |
| Torch | NumPy分量乘加 | 3 |
| NumPy逐个 inverse | NumPy matrix multiplication | 8 |
| Torch | NumPy matrix multiplication | 0 |
| NumPy FP64 inverse后转FP32 | Torch matrix multiplication | 8 |

因此单独更换逆矩阵或单独更换乘加次序都不充分。补查同库 Torch 逐个/批量 inverse，值完全相同；比较其不同内存布局后，全部12对的相机点和投影也完全相同。不能把 NumPy/Torch 差异简单归咎于“逐个”或“批量”本身，更高精度求逆再转FP32也不是复现原 FP32 分支的办法。

新文件 `clean_reference_torch_fp32.py` 不导入原 producer/model；保留原 FP32 inverse、矩阵乘法、除法与 round 运算合同，用独立的全网格逻辑和 dense gather/where 更新代替原 valid-pixel压缩与scatter控制流。接口仍为：

```python
clean_reference(confidence, depth, world, focal, pp, rotation, translation)
# returns: FP32 confidence ndarray, visits list, margins dict
```

该检查共享数值原语，必须称数值一致性复核，不能称跨数值库的精确独立实现。独立 FP64 世界点和目标函数检查仍保留。没有调整tol、bad_conf、数据、mask、相机、depth或旧协议。保存 conf、原 source 函数重放、新独立公式的 tensor 字节 SHA 均为 `186b444dc9076875a98b22195c6d77d6bc0530f4129b3920a098f804900ce625`。

## 导入前补核的科学可读量

29项检查覆盖全部六字段 schema/有限值/正值域、给定相机、实际star目标和log权重、preset点/conf/pose/pp/adaptor、三份原预处理与colors、独立目标与世界点、全像素clean和400条trace。

- 原4份 head 与实际 consumed_inputs 点、原 log-conf 权重和 preset 全部精确相符；没有把raw相机头当成目标。
- 颜色与三种既有预处理档案的首4帧完全一致。没有读取新的实拍文件，更不是生成照片。
- 给定camera与输出c2w最大差1.1920928955e-7；preset pose的独立FP64解码与最终pose最大差1.2885520329e-7。
- 原 `PointCloudOptimizer.forward` 仅对保存状态作一次无梯度纯函数求值，得0.015937957912683487；另一实现的FP64目标得0.015937958255902666。两者通过原固定阈值。此时没有构造scene、optimizer、神经模型或执行GA。
- 全世界点独立FP64重建最大差1.7241756911e-7米，满足原阈值。
- 400条trace的序号恰为0–399，loss/lr全有限，linear schedule最大误差1.7347234760e-18。真实 Adam400/MST1/clean1 的额外证据来自冻结runner在记录失配前已经越过该断言；不能仅凭trace行数证明Adam调用。
- 当前566个源/控制文件和5523个overlay依赖字节SHA全部通过。它是当前磁盘身份检查，不是旧进程的模块清单。

这一步额外读取4份已存原预测头、3份已存预处理档案和以前已生成的共同camera数组；没有读取传感器GT PNG、重新解析GT groundtruth.txt，没有新的模型前向、optimizer.step或GA。之前工具一次因未设置项目工作目录找不到相对Python路径，已改为明确workdir后执行；该次未启动Python或实验。

## 不能恢复的旧观测

原进程在写最终observer report前退出。因此当时的post-final objective标量、完整parameter flags/中间快照、PnP各次细节、loaded geometry/overlay module inventory没有落盘，保持 `NOT_RECORDED`。此次新计算值不冒充那些历史观测。

原preset文件存在；冻结代码的约束断言在失败前通过，最终保存量也已补核。这些是可引用的控制流/文件证据，不是补造逐时刻张量。原失败产物第一次诊断前新增字节快照在 `pre_read_seal.json`，补读其余保存输入前的快照在 `recovery_input_seal.json`；均明确不是历史PASS output seal。

## 给 S26B 的固定接口

`recovery_receipt.json` 的 status=`IMPORT_VALIDATED`、passed=true，SHA：`65efcbe2c181cb866e40b0d33e3846edbb1565e9d3644102ae6e22f7ce273927`。

- `old_output_npz_sha256`：`fcb001fdba0a728d39366ea7219db3407e807b87b3132df71fce30adf4ee31cd`
- `revised_clean_sha256`：`1ac18e88d2aec9e121da2d326f91f6a6d7950d7325473eb6e83dc0791a2f0b3e`
- `depth_tensor_sha256`：`a68a166a3007a083b656794f5d8a3ab3f62840ebf33f4ac0faddab27bc3203b4`
- `control_pose_prefix_tensor_sha256`：`4262eedf6db3a76025d1b01662c34e92f15caf0add89fd930adfcc2062030760`

新合同应绑定此回执与34项保存输入身份，将原字节复制到明确标作recovered saved GA的producer。原目录及FAILED receipt保持不动。其余三项8帧GA仍必须通过新合同的完整运行门，sensor GT仍在全部producer封存之后。新函数只替换数值验证的clean部分，旧 `pair_objective` 等参考函数继续使用，不要把只有clean的文件错误充当完整reference。

本轮解决的是复核工具的数值失配，并建立可审的保存结果导入路径；没有得出新方法、记忆机制、长期泛化、传感器准确性或视频生成收益。按Supervisor第2章先把强baseline做实，再分析它真实未解决的问题；本地科学批判技能在此具体落实为区分技术失败与科学失败、保留失败和历史缺失、结论与证据匹配。
