# S57 后续调用的显式相机约定修复

本目录只修复未来的归档相机→单应矩阵构造。`camera_convention.py` 保留原 `requested_homography` 的完整函数源码语法树；新增入口要求明确指定 `convention='vmem_stored'` 或 `convention='opencv'`。前者复制相机并翻转 y、z 两列，后者只复制、不翻轴。两个相机都转换，平移列不变；没有改 K、图像、匹配、拟合、覆盖、校准或分类阈值。

依据已经独立审计并由 root 复核的固定生成源码：[pipeline.py:1129](../S20_environment/isolated_vmem_source/modeling/pipeline.py#L1129) 先对全部相机执行列转换，再构造相对于第一张上下文相机的射线；[util.py:65–99、154–176](../S20_environment/isolated_vmem_source/utils/util.py#L65) 使用像素 index+0.5、正 z 的针孔射线。令 `D=diag(1,-1,-1)`，归档旋转为 R，则实际射线旋转是 `R D`，所以 `H_ij = K_j D inv(R_j) R_i D inv(K_i)`。D 的行列式为 +1，属于基轴旋转；不能把所有角度统一取反，也不能改成左乘 D。

未来构造归档相机条件时使用：

```python
H = requested_homography_with_convention(
    K1_index, K2_index, stored_c2w1, stored_c2w2,
    convention='vmem_stored')
```

真实 OpenCV 相机或已按 OpenCV 定义的合成控制继续使用通用 `requested_homography(...)`，或明确传入 `convention='opencv'`。已经转换的相机不得再声明为 `vmem_stored`。K 必须已经处于 OpenCV 像素 index 坐标；本模块不估计真实照片 K，也不重复半像素转换。H 仍是原来的纯旋转映射；存在视差时不能把旋转射线投影当作场景点真值。

具体集成位置是原 `prepare_calibration.py:91` 的归档元数据构造。旧 `run_b0_c1_exploration.py` 消费的是已缓存的 `pairs[].requested_H`，仅换一个 import 不能修正那些旧值。未来需从已核实的 c2w/K 显式构造新 H，记录在另一个结果文件；旧 `CAMERA_METADATA_BINDING.json` 的 H 和状态文字只作历史记录。原合成控制在 `prepare_calibration.py:129` 附近直接用已知 `K Ry(-angle) inv(K)` 变换，应保持原样，不加 D。

作者唯一一次有限检查于 **2026-09-08T16:59:20.036137–16:59:20.122685 UTC** 实际返回 0，数值部分耗时 0.086370 秒。Python 3.12.14 / NumPy 1.26.4；未安装依赖。固定数值例子同时含 yaw、pitch、roll、非单位 anchor、非零公共光心、独立 anchor 位置、两组人工 K 及 7 个点。对照路径直接复刻源码的相对外参、逆位姿点减中心、射线归一化与目标投影，不使用待测转换函数。

- `vmem_stored` 对直接射线最大差 `3.979039320256561e-13 px`；`opencv` 最大差 `3.410605131648481e-13 px`，均低于预定 `1e-9 px` 数值容差。
- 全部 30 个既有纯 yaw H 与独立修正 JSON 最大元素差 `1.1546319456101628e-13`，低于 `1e-11`；两行 0→8 单位端点保留。任意旋转的同相机单位映射也通过。
- 通用函数语法树与旧源码相同，OpenCV 显式入口逐元素相同；输入相机不变。对该人工例子无差别翻轴会产生约 `510.638 px` 偏差，说明检查能揭示把修正误用于 OpenCV 控制的错误。

这次检查读取源码和已有 JSON，0 像素读取、0 特征重提取、0 校准重跑、0 模型、0 C2 访问。不是新相机质量实验，也没有补足原单纹理校准的局限。本地科学批判技能仅用于约定、测量有效性和证据边界；一名不同 agent 并行核对了源码射线推导，没有代替 root 的后续集成判断。

`SOURCE_PINS.json` 固定实际使用的 10 项来源；`CHECK_RECEIPT.json` 保留全部 30 项数值检查。交付后所有文件均为 0444，实际 SHA 见 `FINAL_DELIVERY.json`。原 S57、坐标审计和 V9 未改；主账由 root 记录。本目录不执行集成、不重新解释 B0/C1，也不授权 C2 图像解释。
