# S69：九个 RGB 时刻相机与两组原始条件构造

本轮是已有真实缓存的 CPU 组件计算，不运行神经网络、视频、检索、评分或图像查看。固定历史来源 `{12,13,14,18,19}`，两组有序 context 为 geometry `[19,18,13,12]` 与 pose14 `[19,18,14,13]`，目标均为 `[20,21,22,23]`。两组名称只标识旧 S12 已见集合，不声称无目标照片的在线检索；旧查询位姿曾使用目标 RGB。声明 ft-mse VAE 变体与原 SD2.1 VAE 身份 UNKNOWN 保持。

## 输入、相机与坐标

INPUTS.json 固定原 S8 文字元数据、S68 源审/结果审/实际回执、五份 NPZ 身份及逐字段描述。实际只读五份 NPZ 合计 **440740 B**，解码 latent、embedding 和两种 K 共 20 数组；逐文件 SHA/大小及逐字段 dtype/shape/body SHA/finite 核对，不重编码。所有 RGB/depth/权重正文及 PNG header 均为 0 读取。

九个时间以 S8 RGB 文件名中的原十进制时间为准，与 S68 历史及旧 S14E 目标元数据交叉核。复用 S52 RGB_TIME_CAMERA_RECEIPT 中 **18、19、20** 的已存光学 c2w，不重新插值；只对 **12、13、14、21、22、23** 六时刻读取同一已 pin 的 GT 文本（1417998 B，SHA `f19dc674dc43b6c4957038e1a22906122c19c60893e664dafb0e0abe537906ca`），执行原 S52 四函数：纳秒整数定位、不外推、平移线性插值、归一化 xyzw 最短弧 SLERP。原函数对新增六份自带 SciPy/正交/行列式/四元数符号核对；不再执行 S52 三份相机或其深度时刻分支。保留实际 GT 前后行、间隔、插值比例、四元数和 c2w。记录每份相机是复用还是新增。运动插值是帧间假设，不能称每个 RGB 时刻都有精确动捕实测；原 S52 与本环境 NumPy/SciPy 版本不同，原三份照保存值消费。

权威相机保存为 FP64 TUM optical camera-to-world、米单位，光学 x 右/y 下/z 前。消费前将其转成 FP32，并且**右乘** `D=diag(1,-1,-1,1)`，即 `C_consumer=C_optical@D`。这是局部相机基变换；原 get_cond 的列翻号恢复光学矩阵。所有九相机都检查 finite、4×4 形状、齐次末行精确等于 `[0,0,0,1]`、旋转正交与 determinant1（FP64绝对容差1e-10）。两臂实际 FP32 轴变换的反向转换必须逐值相同。此代数与数值一致性不等于真实图像无畸变或完整光学标定验证。

四目标的 640×480/RGB 尺寸依据真实旧 `work/S14E_reporting/figure_receipt.json` 中已解码记录，逐路径对原 S8 和 reporting_rgb_manifest 的 SHA；不以人工 fixture 或深度尺寸代替。沿 S68 已声明的 ROS 默认 K、不去畸变、同一640×480→576 crop 合同，先核五份实际 `K_pixels_576` 完全相同，再复制 ID19 的 K 给四目标。原 ray helper 在内部归一化一次并映射72²半像素中心，不消费或再次缩放 `K_normalized_576`。近似 K 与未去畸变限制保留。

## 原消费路径和结果前规则

从 pin 的原 pipeline 只抽取 `get_translation_scaling_factor` 与 `get_cond`，从原 util 抽取完整八函数 ray 闭包和 DEFAULT_FOV_RAD。实例只有 device=CPU、dtype=FP32、camera_scale=2、num_frames=8，不调用 pipeline 构造器。运行环境为未解析符号链接的 `.venv-cut3r/bin/python`、Python3.12/Torch2.7.0/NumPy1.26.4/SciPy1.16.2/einops0.8.1，CPU8；本次没有参数权重。

每臂用独立副本，自然执行原中心化和尺度：八相机的 torch 下中位、.97 quantile、原 valid mask/mean，以及首相机范数与原 `2/norm + .01` 分支全部不改。先保存 raw，执行原 scale 后保存 centered，随后执行 get_cond。不能为了目标一样而强制共用系数或冻结本臂后代。

预期每臂 c/uc 各四项：crossattn `[8,1,1024]`、replace `[8,5,72,72]`、concat `[8,7,72,72]`、dense_vector `[8,6,72,72]`，全部 finite FP32。context latent 前四槽逐值等于真实 S68 源、mask 通道1，target latent/通道0；CLIP 是所选四项均值广播；uc 的 appearance/replace 为0，concat 仅mask通道变0，c/uc ray相同。返回 K 和 mask 与各臂输入精确相等。光线方向长度1、方向与 moment 点积0的基础检查绝对容差2e-5。完整独立相对射线核验预先使用 abs/rel2e-5；此处的基本恒等式不能代替独立方向/轴约定复核。两臂方向或 moment 不要求字节相同；保存 scale 允许不同作者核结果前的有限预测。

## 一次执行与保存

在 root 和不同作者核收最终源码 SHA 后，由 root 一次运行：

```
.venv-cut3r/bin/python -B work/S69_tum_camera_conditioning/assemble_conditions.py
```

结果目录只新建 `execution_01`；`receipt.json` 是最终回执。保存 `optical_cameras.npz` 与完整插值 JSON；各臂 NPZ 包含 ordered IDs、raw optical/consumer、centered consumer、post-cond optical 相机、scale、K/mask、实际 context latent/embedding及完整 c/uc，每字段提供实际 descriptor/SHA。scalar scale 在 NPZ 是单元素数组。原 get_cond 返回量在断言前保存；一臂失败仍保留其异常与已返回量，并独立尝试另一固定臂，不补选图或改参数。无法进入 get_cond 的失败只有实际可用的输入/相机与异常，不伪造输出。五来源原缓存的内存字段 SHA 在两臂后复核不变。文件完成后只读，外部硬停止亦保留部分目录。

内部55秒，root外部60秒进程组超时观察；记录实际时间/返回码/stdout/stderr，不宣称有未实施的 RSS 硬限制。成功状态只表示两套原条件完成，仍明确 `PENDING_INDEPENDENT_RAY_REVIEW`；不运行任何后续模型。作者仅 stdlib AST/compile/定义接线自查，0真实GT数学/NPZ正文/get_cond/模型。全部旧结果、主账与当前入口保持不变。
