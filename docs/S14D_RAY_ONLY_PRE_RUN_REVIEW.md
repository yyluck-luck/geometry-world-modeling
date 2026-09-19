# S14D ray-only 接口探针：独立运行前代码审查

审查者是接口源码审计 agent，未编写生产 runner。当前审查结论为 **代码与指定设计通过；等待最终 manifest 的绑定核验，尚未执行模型**。本报告可以作为待冻结控制材料，最终文件身份核验另存回执，避免运行后覆盖本报告。

## 审查对象与限定问题

生产文件：`scripts/run_s14d_ray_only_probe.py`，本轮审查 SHA `859b0eb55da5751b72d9b65956cdbff1b19c9cb959c5c542687500a5bcef049a`。源代码快照在 `work/S14D_pre_run_review/v3/runner_snapshot.py`。

问题是：用 S8 block0 的前20历史 RGB 建立 CUT3R 状态后，是否能不读目标 RGB/GT，只给历史派生相机和射线进行真实预测，同时保持状态不变？此问题与既往24张含query RGB的S8推理不同；重新构造未保存的latent状态有必要，但不构成新独立场景、算法质量实验或视频生成。

四个目标按根给出的运行前方案：最后历史预测c2w，在其局部坐标轴偏移 `(0,0,0),(+d,0,0),(-d,0,0),(0,0,+d)`；`d=.05*median(||t_i-t_0|| where distance>1e-6)`，空域失败、不补参数。固定pseudoK焦距 `sqrt(224²+224²)`、主点112。按官方源码含平移的非标准射线约定构造6通道张量。调用顺序 Q0 NaN占位、Q0 zero占位、Q1/Q2/Q3 NaN占位，共5次 direct inference_step。

## 检查结果

| 检查 | 结论与依据 |
|---|---|
| 历史边界 | 生产代码要求恰好20个不重复路径并绑定SHA。最终manifest仍需独立核这些路径确实等于S8 block0 metadata的前20项。 |
| 目标信息来源 | targets只读本次history输出的相机；不读旧query预测、目标RGB或GT。固定偏移是预测尺度，不能叫厘米。 |
| 射线公式 | AST抽取官方viewer两个方法，未改为Plücker或标准纯方向公式。纯人工独立scalar公式对照通过。 |
| shape/兼容 | 有效ray `(1,224,224,6)`、显式true_shape、RGB占位。运行时要求PatchEmbedDust3R；保留既有signed RoPE，不增加未审适配器。 |
| CPU/精度 | CPU、8线程、seed0、FP32模型；外部caller已核600秒/32GiB监测、0.5秒采样、终止后10秒宽限再kill。 |
| checkpoint | 运行前核身份、禁止unsafe override、限定safe globals、所有权重键匹配、linear224架构；manifest必须绑定checkpoint、rope报告及adapter。 |
| 读图台账 | 图片打开尝试、成功打开、解码成功分别计数。`Image.open`仅在历史加载期间包裹，允许20条预定路径；query路径源码没有读图调用。禁止把固定零计数当作全系统I/O沙箱。 |
| query确实走射线 | 用两个patch embed hooks记录query图像编码batch应0、ray编码调用应5，补充源码证据。 |
| dummy隔离 | Q0两次使用相同ray/pose而不同图像占位，要求全部tensor键域一致、值和tensor_id（shape/dtype/bytes SHA）精确一致，不只比较一个几何数组。 |
| 状态不写回 | 每次核五元state的finite前提、shape、dtype、bytes SHA和数值精确相等；保存before/after。 |
| 输出形状 | required几何/置信度/pose有固定shape和FP32门；所有返回tensor都要求finite，保存所有键。camera_c2w是额外转换量，不误列官方必有键。 |
| 失败保留 | 新目录拒绝覆盖；查询调用前计attempt，返回后计completed；每次查询即保存npz，后续失败不丢先前调用产物；traceback写metadata。 |
| 响应范围 | rays须不同；`max_abs_geometry_difference>1e-6`仅报告预定接口响应诊断bool，不作为质量或成功门，不因未响应删目标。 |
| 文件身份 | 开始/结束核identities、manifest与载入上游模块；最终冻结必须覆盖实际会用的上游源码和外部caller。 |

## 先发现、后修正的缺口

V1（SHA `5f8cd1d3a4fbef5104b4d7ce0fb2d51c0ae2ff9036a11183ade1158771bc0c16`）被要求修正，未获实际运行通过：

1. 20张全部完成后才更新图片计数，中途失败会错误显示0。
2. query尝试和返回成功没有区分，且所有调用结束才保存数组。
3. 状态检查未显式核dtype/shape/hash。
4. 输出未核固定shape/dtype，dummy比较未核所有tensor键域。
5. 所有实际必需输入未显式要求出现在冻结字典。

根于运行前修复。V1文件与未通过回执保留在 `work/S14D_pre_run_review/v1/`；没有运行真实数据来调阈值。V2差异已逐项审读。

## 人工核验及未做的事

`work/S14D_pre_run_review/check_artificial.py` 对V1副本进行 **50项纯人工检查**：3种尺寸的pseudoK、3种人工相机及其采样像素射线、20个构造history姿态得到的尺度/局部轴四targets、空尺度失败，以及无torch导入。射线用不同scalar代数；绝对门在执行前固定为1e-7，仅补偿官方FP32逆K和scalarFP64除法的舍入差。该门不是研究效果门。

V2中 `extract_ray_factory`、`target_poses_from_history` 两函数AST与已测V1精确相同，已写 `v2/changed_code_review.json`；未机械重跑相同人工数值。其余修改在主调用、计数、保存、检查，已做源码diff审查。

真实模型运行0，checkpoint反序列化0，真实NPZ/GT/图像解码0。50项人工检查不是50个真实实验样本。当前尚未核最后manifest；外部预算caller已独立审查并通过人工失败路径检查；最后绑定通过后，只允许按冻结方案执行一次，后续失败修复要另存材料。


最终probe修订V3只增加dummy输出tensor_id精确门，对齐运行前协议的“字节相同”。旧V2审查和源码保持在v2/，新probe源码SHA如本报告首节。外部caller失败留痕和清理缺口已修正并单独核验，见下一节。当前仍不进行实际模型执行。


## 外部caller最终检查

`scripts/run_s14d_controlled.py` SHA `b58d57ddd78355cc28893ce9c5771b843a0859548443e02727aedf7355dc0a0e`。通过try/finally保存RUNNING/PID及最终回执；RSS的ps调用timeout5秒，活进程取不到有效采样即失败；异常时终止已启动进程；后置文件身份失败也保留FAILED。600秒墙钟检查和32GiB RSS检查均在单次循环，没有自动重试。RSS是0.5秒采样监测，不能宣称硬内核内存限制，最长终止还包括监测/终止宽限。

4个纯人工子进程案例（正常完成、非法RSS采样、Popen失败、超过RSS限制）共14项检查通过，包括失败回执、实际子进程已终止及异常信息保留。子程序只sleep，模型/权重/真实数据运行0；未等待600秒实际触发timeout，超时分支仅源码审读。证据 `work/S14D_pre_run_review/caller_artificial/receipt.json`。

最后dummy字节/schema门另有3个人工检查通过：有符号零差异、dtype差异被拒，相同FP32数组通过；见 `v3/dummy_byte_gate_checks.json`。累计人工数值/失败路径检查67项（50+3+14），这些全部不是研究样本。最后manifest绑定另出回执，必须核通过再实际执行。
