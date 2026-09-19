# S17C 不同作者代码前审与独立验证器

结论：已审 producer 当前版本没有发现阻止 root 冻结的代码问题。原 wrapper 委托、两图输入、无先验全局优化、400次原 step、一次额外只求值及保存字段与协议一致。**这是运行前代码审查结论，尚非 S17C 真实模型/全局优化成功。** root 仍须完成最终 manifest/外caller/完整权重身份，并等 S17B 释放资源后执行。

本报告与最终 SHA 见 `work/S17C_independent_preparation/formal_review_receipt.json`。producer 由 `/root/s15b_bonn_resolution` 编写，source/overlay 由 `/root/s15b_prefix_runner` 准备；本 agent 阅读原数学接口和 producer，另外实现 NumPy/SciPy 验证器。属于团队内不同作者核验，不是外部团队复现。root 维护主账，本报告不覆盖历史记录。

## 已核实的实现

- 固定两张 Bonn0/1及顺序，原 EXIF/RGB/512输入路径，observer 保存处理后的 tensor，实际图像打开守卫拒绝额外图像。source 原 NaN ray 占位保留，所有 ray mask false，真实有效 ray/query=0，内部零 dummy 一次单列记录。
- `run_inference_from_pil` 和实际 `inference` 各委托一次，原六头×2、五state、两种 raw pose 数组直接保存。没有调用 VMemPipeline、主生成器、VAE、CLIP、GT、可视化或视频函数；没有第二次模型前向。
- 原星形边只有 `(0,1)`。frame0 self/conf_self 与 frame1 other/conf 进入原优化器，poses/depths=None，区别于 VMem 正式流程给定相机/旧深度的构图回路。
- 原 PointCloudOptimizer、MST与PnP观察，scene参数 schema 完整保存。四份scene快照分别在构造、MST后、最终clean前/后；原点/相机/depth不被 observer 替换。
- 原 `global_alignment_iter` 实际400次，另包原optimizer.step计400，trace每步写盘。postfinal objective额外一次无梯度求值，总目标调用401；原返回loss明确是最后更新前。网络参数无梯度、eval，并检查optimizer参数对象不含网络参数。
- 默认clean顺序、严格阈值与Torch取整保持；除了confidence，前后所有scene字段 exact 不变。原返回五类结果拼接为八个最终数组，并逐项等于after-clean输出。
- 安全载入固定公开完整DPT权重：完整字节/SHA、七个有限globals、weights_only=True、全部keys匹配。CPU8/FP32，Python/NumPy/Torch/OpenCV在imports后seed0。NumPy1.26.4/Torch2.7.0/SciPy1.16.2的实际路径不得由overlay替代。

前审发现并已由作者修正：首版 `verify_modules` 只验证路径在隔离根下，未要求每个实际导入文件属于冻结manifest，且漏包根/croco前缀。定稿已覆盖这些名称，并要求每个文件路径和SHA都在manifest；在导入后与完成时各检查。原问题不影响既有S17B文件，首版准备及作者人工回执均保留。

## 来源和环境

固定 VMem commit `39291e4f272f6b4f270691d930926ab5930f942e`，source_plan SHA `e90ee3c071912ac594d6b41ed88be23321baae3bac60a221522d67cee4eb482d`。实际独立文本哈希核了198原文件覆盖两修改再新增1个RoPE文件，共199个最终文件，全部匹配，回执 `final_source_identity_check.json`。没有读取其外部权重或图片。

隔离环境实际完成的是 **34个wheel、5523个非bytecode安装文件**，不是早期22wheel元数据计划。正式环境依据：

| 文件 | SHA256 |
|---|---|
| `work/S17C_environment/environment_ready.json` | `a3247a14945d224d291b1aa0d3d32a7efc593f897b6b6289fdabd3d3f14783ca` |
| `work/S17C_environment/import_smoke_v2.json` | `86ec27d37f040c01358a6e7b3621c9ccc821f91add36aaed27072fa096672c24` |
| `work/S17C_environment/overlay_files.json` | `4b5d89ce0069c18086ec91c9f3f02ebc900b9ef7bc4066f44af4e5ba597b5d0b` |

本审查阅读并核对这些最终回执/清单身份；没有重复执行import smoke或独立重新安装。原环境代理记录的pass是 `PASS_IMPORT_ONLY_NO_MODEL`，模型、权重、图片尝试均0。原env保持检查是非bytecode文件stat/路径加METADATA/RECORD/bin字节哈希，不能说做过全部原env源文件字节认证。正式producer与独立验证器将读取manifest的完整源码/overlay身份做前后核对。

## 独立数值路径和人工证据

新 [verify_s17c_embedded_geometry.py](../scripts/verify_s17c_embedded_geometry.py) 不导入Torch、PIL、producer或原模型；使用固定 [numerical_reference.py](../work/S17C_independent_preparation/numerical_reference.py)。完整核验原19数组、2输入tensor、4×10 scene arrays、8最终数组，共69数组；PnP成功时额外1个pose，共70。身份、完整分母、所有调用计数、400行trace和resource也必须通过。

世界点由独立float64相机反投影重构；raw pose用SciPy quaternion。颜色从封存输入tensor反归一化。目标用原raw conf取log、三维欧氏norm及逐端完整area均值，重算一次postfinal objective。clean另以NumPy FP32分量投影与顺序更新复算；全部confidence要求exact，保存全域mismatch和xy/半像素/z/阈值margin。所有容差和“mismatch即FAIL，无边界豁免”已写 [运行前数值合同](S17C_INDEPENDENT_NUMERICAL_CONTRACT.md)，不看结果后调整。

人工源函数检查与NumPy路径比较见 `artificial_v1`、`numpy_artificial_v1`；最终完整schema人工包 `full_schema_artificial_v4` 通过69数组检查，并故意把一个clean confidence改成1：验证器拒绝，完整保存唯一错误坐标 `[0,1,2]`。人工包没有模型、实拍、权重、GT或真实全局优化；不能把其形状与断言数当真实实验数量。

**状态网格纠错已保留。** S17B真实前向后发现本 agent 旧验证器漏了官方 odd-width+1行：768状态的二维网格width应为28，而非27。S17C producer保存真实state没有这个错误；尚未冻结的C独立核验器与人工包最初也用了27，现已在v4改正，另AST读取实际加载文本的`state_size=768,state_pe='2d'`，用整数isqrt与奇偶补齐验证所有坐标。C的v1–v3人工回执以及更正前脚本都保留；它们不再支持状态坐标规则正确。根因与原S17B失败见 [S17B勘误](S17B_STATE_POSITION_CORRECTION.md)。

## 定稿接口与执行条件

独立CLI：

```text
.venv/bin/python scripts/verify_s17c_embedded_geometry.py \
  --manifest ABS --manifest-sha256 SHA \
  --seal ABS --seal-sha256 SHA --run-dir ABS \
  --caller-receipt ABS --output ABS_FRESH
```

root的manifest control_files须包含本验证器、numerical_reference.py及固定数值合同；验证器会核自己的执行SHA与helper SHA。producer协议、最终环境/overlay清单、最终源码、完整权重与两图身份一并绑定。当前producer和verifier SHA在正式回执中给出，冻结后不得更改；任何调整需新版本与新回执。

当前没有发现需要修改producer的剩余代码问题。真实运行失败仍须保留中间scene/trace、最新phase和外caller；超时、加载或独立数值差异不是新科学方法失败。即便最终所有门通过，仍只支持无先验嵌入几何组件完整性，不证明几何准确、surfel memory、完整视频或创新成立。
