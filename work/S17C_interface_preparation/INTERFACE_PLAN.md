# S17C：VMem 内嵌 CUT3R 两图建图接口与隔离依赖方案

2026-09-06。状态：**源码及依赖元数据准备完成，尚未安装、加载权重或运行模型。**
这是给 root 和独立前审者的可执行方案，正式 manifest 尚未冻结。

## 结论与研究定位

可以直接运行 VMem 内嵌的 `surfel_inference.run_inference_from_pil`，无需构造
`VMemPipeline` 或加载主生成器、VAE、OpenCLIP。该函数接受已经加载的 CUT3R
模型，内部执行原两图前向、从第一帧到其它帧的有向边构造、原全局对齐和置信度
清理，最后返回稠密几何与相机。

S17C 建议固定同 S17B 的已见 Bonn RGB 0/1、size 512、CPU FP32、8 线程、seed 0、
`poses=None, depths=None, lr=0.01, niter=400, visualize=False, save_flag=False`。
源码实证：`configs/inference/inference.yaml:35–36` 是 lr 0.01、niter 400；
`modeling/pipeline.py:1309` 将 config 的值传给 `construct_and_store_scene`，后者
在第 978 行左右传给原 `run_inference_from_pil`。函数自己的默认 300 和方法默认
1000 都不是实际配置调用值，本轮不能靠默认值猜测。

边界必须保留：完整 pipeline 的 `construct_and_store_scene` 还会传入它已有的
相机（先翻转旋转的第 1/2 列），以后还传已有 `surfel_depths`。本轮无 GT、
无先验的两图调用验证的是作者公开 wrapper 的独立几何组件；**不能声称复现了
VMem 线上相机/历史深度约束、surfel 记忆更新或视频生成回路**。自由重建有尺度/
坐标规范选择，输出不是已经证明的米制准确深度，也没有未见评测声明。

## 固定源码、差异和透明补丁

VMem 原 checkout：
`/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem`
，commit `39291e4f272f6b4f270691d930926ab5930f942e`。
独立 CUT3R 是同 workspace 的 `work/cut3r-local`，commit
`8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf`。检查使用 `/usr/bin/git`；shell 默认
git 不能理解独立 checkout 的 worktreeConfig，失败没有通过修改仓库配置规避。

本目录 `isolated_vmem_source/` 是透明源码副本：原仓库全部已跟踪 `.py/.cpp/.cu/
.c/.h/.hpp/.sh/.yaml/.yml` 及许可证、README、requirements，198 个原文件，
1,697,413 字节；无图片、视频、模型、数据集资产或 Git 元数据库。它包含完整
可执行 Python/CUDA/C++ 源码和配置，不是包含外部数据的完整 Git 工作树。
`source_plan.json` 逐文件记录原路径与 SHA；原 checkout 保持不变。

两个版本的 embedded `src/` 共比较 95 个 Python 文件，91 个字节相同。
包括实际 inference、DPT head、CroCo/CUT3R attention blocks 和 image loader
均相同。4 个差异是：

| 文件 | 嵌入分支差异及影响 |
|---|---|
| `src/croco/models/pos_embed.py` | CPU fallback 被注释，缺 curope 时 `RoPE2D` 未定义；S17B 成功也不会自动修复它。 |
| `src/dust3r/model.py` | 显式 `weights_only=False`，另有无关 import 差异；前向核心无其他 diff。 |
| `src/dust3r/losses.py` | 注释 gsplat import，pose loss clipping/倍率不同；本轮 inference 不导入训练 loss。 |
| `src/dust3r/datasets/bedlam.py` | 训练 pose 路径不同；本轮不导入/访问该数据集。 |

候选补丁 `cpu_geometry_candidate.patch` 只有 3 个文件：

1. `pos_embed.py` 加显式 CPU/CUDA dispatcher。
2. 新 `rope_cpu.py` 是 S17 已通过 123 个组件检查的 signed RoPE：保留负位置、
   F0，内部 FP32，恢复官方调用传入的 FP16 dtype；CUDA/MPS/训练不在验证范围。
3. `model.py` 的唯一修改是将已有 `torch.load(... weights_only=False)` 改为
   `weights_only=True`。未来 runner 必须用下文固定安全全局集合加载。

该补丁 SHA-256：`7815b4d5be146f8ef202ff11a691aa02aca776018505f33efd898758773b91ee`。
`source_plan.rope_only_v1.json` 留存 root 提出安全加载修改前的准备版本；
`source_plan.json` 是当前三个差异的版本。未引入 S17 的主生成器 Attention 或
do_sample 补丁。原 `run_inference_from_pil`、`prepare_input_from_pil`、
`prepare_output`、全局优化实现保持源码相同。

## 权重与加载门

使用 S17B 同一完整公开 512 DPT 权重；只有 root 的下载及完整核验成功后才可读取：
3,173,761,006 字节，SHA-256
`45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103`。
不能用部分文件、HTTP 状态或仅 ZIP 能打开来替代完整身份。

沿 S17B 固定以下 `torch.serialization.safe_globals`，不得根据失败临时扩大：
`omegaconf.DictConfig`、`omegaconf.base.ContainerMetadata`、`typing.Any`、
`dict`、`collections.defaultdict`、`omegaconf.nodes.AnyNode`、
`omegaconf.base.Metadata`。先调用 `get_unsafe_globals_in_checkpoint`，要求返回
的全局名称不超集合；在其作用域内调用原
`ARCroco3DStereo.from_pretrained(local_checkpoint).float().to('cpu').eval()`。
本轮不会调用原嵌入分支的 `weights_only=False` 路径。

保留原 loader 的 checkpoint constructor 配置机制，但记录实际配置和加载文本；
要求全部 state_dict keys matched、head_type dpt、DPTPts3dPose、patch 配置 512、
PatchEmbedDust3R、24 个 image encoder blocks。原 loader 的 `strict=False` 不能
被当成允许缺失/多余 keys：任何不全匹配都停止并保留失败。

## 最小依赖与隔离安装计划

源文件的导入链直接绕过 `modeling.pipeline` 和 `utils/__init__`。
新的进程只把隔离 `extern/CUT3R` 和其 `src` 加入 sys.path。原 wrapper 的
`src.dust3r.inference` 与模型的 `dust3r.*` 绝对导入都必须解析到这一隔离源码，
所有实际加载的 `dust3r/src.dust3r/models/croco/cloud_opt` 模块记录 `__file__`/
SHA 并检查根路径，拒绝混入独立 CUT3R 或原 checkout。同一文件出现不同 Python
包别名必须如实记录，不能用假包填充来掩盖导入问题。

现有 `.venv-cut3r` 已有 torch/torchvision、NumPy、SciPy、Pillow、einops、roma、
transformers、accelerate、OmegaConf、tqdm、OpenCV 等模型路径依赖。
直接 wrapper 多出的必需导入是 imageio；global optimizer 顶层导入 evo；
其 `dust3r.viz` 顶层导入 matplotlib。即便 visualize=False，三者仍需满足。
trimesh 的缺失由原 viz 文件捕获且仅影响未调用的可视化，不能据此引入完整
VMem 的 open3d/CLIP/diffusers/gradio 依赖。

采用**完整标准包依赖的独立 overlay**方案，不移动原函数的 import、不伪造 evo
或 matplotlib 类，也不修改旧 venv。现已仅查询 PyPI 元数据并枚举现有发行包，
没有下载 wheel、执行安装或导入完整几何栈。

固定候选根包为 [evo 1.37.1](https://pypi.org/pypi/evo/1.37.1/json)、
[matplotlib 3.11.1](https://pypi.org/pypi/matplotlib/3.11.1/json)、
[imageio 2.37.4](https://pypi.org/pypi/imageio/2.37.4/json)。
递归按 Python 3.12/macOS、无 extras 的 Requires-Dist 条件展开，完整闭包 28 项，
所有 incoming 版本约束相容；6 个现有版本保留，22 个新增包各有匹配当前 CPython
3.12/macOS arm64 的 wheel。它们的元数据标示总下载量为 **29,513,889 字节**。
这只是元数据与 wheel tag 相容，尚不是 pip 解析或二进制 import 成功证明。

完整准确依赖边、版本、元数据 URL/SHA 位于 `dependency_plan.json`；固定可用
wheel 文件、URL、SHA、字节数位于 `overlay_wheel_plan.json`；22 个新增包版本与
单个选定 wheel hash 位于 `overlay_requirements.txt`。根包依赖如下（不含 extras）：

| 根包 | 直接依赖 |
|---|---|
| imageio 2.37.4 | numpy；pillow>=8.3.2 |
| matplotlib 3.11.1 | contourpy>=1.0.1；cycler>=0.10；fonttools>=4.28.2；kiwisolver>=1.3.1；numpy>=1.25；packaging>=20；pillow>=9；pyparsing>=3；python-dateutil>=2.7 |
| evo 1.37.1 | argcomplete；colorama>=0.3；matplotlib>=3.6；natsort；numexpr>=2.7.3；numpy>=1.18.5；packaging；pandas；pillow；pygments；pyyaml；rosbags>=0.11.1；scipy>=1.2；seaborn>=0.9 |

新增精确版本：evo 1.37.1、matplotlib 3.11.1、imageio 2.37.4、argcomplete 3.7.2、
colorama 0.4.6、natsort 8.4.0、numexpr 2.14.2、pandas 3.0.5、pygments 2.21.0、
rosbags 0.11.5、seaborn 0.13.2、contourpy 1.3.3、cycler 0.12.1、fonttools 4.64.0、
kiwisolver 1.5.1、pyparsing 3.3.2、python-dateutil 2.9.0.post0、apsw 3.53.4.0、
lz4 4.4.5、ruamel-yaml 0.19.1、zstandard 0.25.0、six 1.17.0。
保留 NumPy 1.26.4、packaging 26.3、Pillow 10.3.0、PyYAML 6.0.3、SciPy 1.16.2、
typing-extensions 4.16.0。rosbags 引入 apsw/lz4/ruamel.yaml/zstandard，pandas/
matplotlib 引入 python-dateutil，再引入 six；没有 GUI、ROS、ffmpeg、测试 extras。

准备阶段发生过一次 urllib SSL EOF 和一次 curl SSL 错误，后者保留于
`dependency_plan.failed1.json`；随后仅 metadata 查询启用有界 retry 成功。
这与模型/数据下载无关。

root 审核后可在全新 `work/S17C_deps_overlay` 安装选定 wheel，使用
`--target`、`--no-deps`、`--require-hashes`、`--only-binary=:all:` 与已冻结列表；
现有 6 个依赖已单独校验相容，不让 pip 更换旧 venv 里的 NumPy/torch。
正式 runner 显式添加 overlay 到 sys.path，并记录从 overlay 或旧 venv 解析到
的实际发行包和模块位置。先单进程执行 import-only 检查并禁止网络；不得在模型
正跑时进行正式性能测量。若任何 wheel/import 失败，保留证据，先修复方案再开
真实模型，而不是静默换版本。

## 候选 CLI 和 manifest（待独立前审后冻结）

建议 worker：`scripts/run_s17c_embedded_geometry.py`，接口：

```text
.venv-cut3r/bin/python scripts/run_s17c_embedded_geometry.py \
  --manifest ABS_FROZEN_MANIFEST.json --output ABS_FRESH_RESULT_DIR
```

必须由外部 600 秒 / 32 GiB RSS 监控包裹，并与正在进行的 S17B 正式运行错开。
此处尚无 worker 实现或正式执行命令的授权替代；root 正在审方案。

建议 schema `s17c-embedded-two-frame-geometry-manifest-v1`；顶层字段
`source_root, source_commit, source_plan, python, overlay, dependency_plan,
runner, checkpoint, history_images, identities, contract`。
`identities` 包含当前隔离全源码及 3 个差异、runner、协议、依赖准确元数据/实装
清单、完整 checkpoint、两张 RGB、外监控；不加入任何 GT、更多图片或旧预测。

contract 精确冻结：2 张已见 RGB、顺序 0/1、原640×480、size512→384×512、
CPU FP32/8线程/seed0（所有 imports 后再固定 Python/NumPy/torch 与 OpenCV RNG，
原 wrapper 顶层曾设置 random.seed(42)，不能让它覆盖最终种子）；原 wrapper
恰好一次；原 inference 恰好一次；2 image
frames、0 supplied rays/queries；原 first-frame star edge 恰好 `[(0,1)]`，
不是 all-pairs 或双向两边；poses/depths=None；lr=.01、niter400、schedule linear、
init mst、PnP默认10次、PointCloudOptimizer；默认 clean tol=.001、bad_conf=0；不调用 sky mask/
viewer、save_flag=False；600秒、34359738368字节 RSS。

## 真实输入、观测与输出

只允许同 S17B 两条固定 Bonn 路径/SHA，由 root manifest 复用；不重复打开其他
RGB 或任何 GT。PIL 两图按顺序各解码一次；由原 `prepare_input_from_pil` 做
exif/RGB、size512缩放、16倍数裁切、ImgNorm。记录实际 `[1,3,384,512]`、
`true_shape`、原尺寸和 flags，不把人工推算当实测。相机占位单位阵、mask 掉的
NaN rays 保留原构造，不当成真实相机/射线观测。

以只委托给原函数的 observer 保存真正输出，不再调用第二次模型：

1. 原 inference 回传后、global alignment 前保存两帧六头和最终 state。沿
   S17B 保存 19 个数组及真实 image/dummy-ray/encoder hooks；这次权重和嵌入
   RoPE 的数值差异必须如实记录，不能宣称与 S17B 逐位一致。
2. observer 记录传给 global_aligner 的两个 view 与 pred 索引及边 `[(0,1)]`。
   optimizer 用 frame0 `pts3d_in_self_view/conf_self` 和 frame1
   `pts3d_in_other_view/conf`；不是两帧 self-z 简单拼接。
3. 原 `global_alignment_iter` 委托 observer 计真实 400 次，记录每次 loss/lr。
   迭代0..399的线性 lr 是 .01 到 .0000259975；返回 loss 是最后一次
   optimizer.step **之前**的 objective，不可标成最终更新后 objective。若需另观测
   post-final objective，应只求值一次、单独命名和计数，不额外优化。
   不用全局 `torch.inference_mode()` 包裹原 wrapper，因为 prepare_output
   内的全局对齐需要 `torch.enable_grad()`；模型 inference 自带 no_grad。
   优化器改的是几何/相机/深度参数，不是训练 CUT3R 权重。
4. 在原 clean 前后保存必要相机/点/深度/置信度，独立检查 clean 的几何投影门。
   clean 原逻辑降低置信度，不删除稠密数组中的点、不更改它们的坐标/深度。
   独立复算须保留 i→j 遍历与 res 原地更新顺序，并用 Torch.round 的
   ties-to-even；不能换 half-up 四舍五入或并行无序清理。
5. 保存 wrapper 真正返回的 5 类结果，不根据预期自己制造字段：

| 返回字段 | 两图预期结构（正式按实际核验） |
|---|---|
| point_clouds | 2 个 `[1,384,512,3]` CPU tensors |
| colors | 2 个 `[1,384,512,3]`，来自输入图的处理后真实颜色，范围0..1 |
| depths | 2 个 `[1,384,512]` |
| confidences | 2 个 `[1,384,512]`，clean 后允许0 |
| camera_info | focal `[2,1]`；pp `[2,2]`；R `[2,3,3]`；t `[2,3]`，NumPy |

camera_info 是 MST/PnP 初始化后优化得到的 c2w；原 wrapper 没有拿六头的
camera_pose 去初始化，不能混用这两种相机。principal point 默认固定在图像
中心；base_scale=.5、norm_pw_scale=True。`get_conf(mode='none')` 返回未取 log
但已经 clean 的置信度；优化阶段使用的是原预测 conf 的 log 权重，不能让之后
clean 的值追改之前优化的解释。

保留原始输出后再核形状、有限值、正焦距/正深度、R 正交/行列式、相机底行、
优化 loss 有限和完整迭代计数。自由相机/焦距不能与 GT 做隐性校准。源 checksum、
输入允许集、实际调用计数和外部资源门必须同时 PASS 才标成功；部分失败目录
保留原始输出、traceback、准确时间和资源记录。

## “surfel” 字段不能偷换

原 wrapper 虽叫 surfel_inference，却返回**稠密几何**，不创建 `Surfel` 对象。
真正的 pipeline 后续还以 shrink_factor=.05 双线性下采样，再调用
`pointmap_to_surfels` 估计 normal/radius，执行 merge 并维护时间来源。
`utils/util.py:1274` 的 Surfel 字段是 position、normal、radius、color；
当前原 `pointmap_to_surfels` 创建时不传 color，实际为 None。

本阶段应准确交付上表的真实 wrapper 字段和 state/alignment 观测。若以后增加
完整 Surfel 对象链，需要单独冻结 downsample、confidence/depth quantile、
normal orientation、radius、相机先验和 provenance/merge 协议；不得把本轮
稠密点云改名为已经验证的完整 Surfel memory。

## 记录与接手

本任务应用此前已读 Supervisor vibe-research-workflow 与本地 Claude scientific-
critical-thinking 的小步验证/证据边界原则，没有调用 Claude 模型。
root 负责 canonical log；本目录保留源码比较、三个透明补丁、依赖原始元数据/
失败、精确 wheel 计划与本接口。独立前审由另一个 agent 进行。
下一步是 root 确认接口和隔离依赖方案后，准备 observer runner 与人工边界检查，
等待 S17B 正式运行释放资源，然后安装新 overlay 并做 import-only 门，最后才
冻结 S17C 真实运行 manifest。
