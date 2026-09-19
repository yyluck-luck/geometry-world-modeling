# S79：SIFT + LightGlue 的本机执行前检查

状态：`SOURCE_AND_DEPENDENCY_PREFLIGHT_ONLY`。首个实际时钟锚 2026-09-10T15:13:48Z；本报告的源码/缓存观察截至 2026-09-10T15:19:22Z（北京时间 23:19:22）。后续 root 正另建 S80 setup；其新取得文件应以 S80 回执更新，不能把本快照的“尚缺”当永远缺失。

**当前已有图像和大部分基础依赖，可准备 CPU 全12对实验；本轮检查时尚不能从当前默认环境直接离线执行。** 官方包/权重尚未完整落地；SIFT/utils 官方固定源码现已补齐，旧 S20 的 Kornia 依赖可隔离复用。没有导入 Torch/Kornia、提取特征或运行匹配模型；没有读取图片/权重正文、安装软件或修改旧实验。本轮只获取了公开官方源码文本及 release 元数据，未获取权重。

## 已有文件与具体缺口

| 项目 | 本轮实际核到 | 对执行的含义 |
|---|---|---|
| 首选解释器 | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/.venv-cut3r/bin/python`；Python 3.12.14，arm64 | 复用既有解释器，不改 venv |
| 该环境基础包 | 元数据/导入定位：Torch 2.7.0、torchvision 0.22.0、OpenCV-headless 4.11.0.86、NumPy 1.26.4、Pillow 10.3.0、packaging 26.3 | 只定位/读取元数据，未实际导入或验证联合运行 |
| 默认环境缺包 | 两个项目 venv 均找不到 `lightglue`、`kornia`；`.venv-cut3r` 无 matplotlib、kornia_rs、pycolmap、flash-attn | 不能将默认导入可用写成已就绪。pycolmap 与 flash-attn 对选定 OpenCV + CPU 路径非必需 |
| 旧隔离依赖 | `work/S20_environment/site-packages/kornia` 0.8.0；同处 `kornia_rs` 0.1.8；扩展 `kornia_rs/kornia_rs.cpython-312-darwin.so` 为 Mach-O arm64 | 可供 Python3.12 arm64 隔离复用；真正 import/ABI 联合兼容仍未执行。Kornia 0.8.0 的元数据要求 kornia_rs、packaging、Torch，均有本地候选 |
| 旧 Kornia LightGlue | `work/S20_environment/site-packages/kornia/feature/lightglue.py`，SHA `79ac721918df4d5d07aae87bb59a0c8f2958e044e86ff49e44b664b8d9874b2f` | 是 Kornia 适配版，不是已冻 cvg 官方源码。此方案只借 Kornia 作为依赖，不偷偷改成这份 matcher |
| 官方 matcher 源 | `work/S76_relative_camera_response/innovation_sources/response_selectivity/lightglue.py`；SHA `dcb75b9cad1985c5e7a537c512d4318d47fbcc99df75b39a513de60e027c039f` | 固定 commit `eb42fee2d71449efb0aa5c10549752b5d75384d8`；单文件不等于完整可导入包 |
| 新补官方 SIFT | `work/S79_observer_alternative/official_source_01/sift.py`；8194 字节；SHA `9fa24851ff25b6f09cb06fa62aed1d07fa9cb6aa340c79d6467b3bdfdd4508cd` | 同一固定 commit，全文已核；尚未导入 |
| 新补官方 utils | `work/S79_observer_alternative/official_source_01/utils.py`；5510 字节；SHA `c6d9260656a24d826128b68c95d0b7798106d04f4244a77f3b1856573f58e690` | 同一固定 commit，全文已核；尚未导入 |
| 权重缓存 | 两个缓存变量 TORCH_HOME/XDG_CACHE_HOME 未设置；默认 `/Users/rocket/.cache/torch/hub/checkpoints` 不存在；项目文件名及所查 Torch/HF 缓存中未见 sift_lightglue 权重 | 这是指定范围的文件名检查，不是全机所有盘扫描。不能以联网自动构造器补权重后声称全离线 |
| 原评分图片 | source19 + real/A0/B × 20–23，共13张PNG：路径均存在、非空且权限可读 | 组成12对。仅 stat/access；本轮没有重算图片 SHA 或解码尺寸，后续运行需绑定原合同身份 |

13 图路径的权威清单仍是 `work/S73_generated_fixed_geometry/CONTRACT.json` 的 `anchor/generated_images`，加 `work/S72_fixed_requested_geometry/CONTRACT.json` 的 `targets`。共同源是 S72 `execution_01/real_anchor_19.png`；12 个目标都位于 S70 `visuals_01`，文件名分别 `reference_target_20…23.png`、`A0_target_20…23.png`、`B_target_20…23.png`。

官方 requirements 还列 matplotlib 与 `opencv-python`；当前使用 headless OpenCV 已具备 cv2。选定 SIFT/matcher 路径未见绘图调用，不必为本实验先引入 matplotlib 或让 pip 再装另一份 cv2。完整官方 `__init__.py` 会同时导入其他特征类，未来使用源码目录时仍须核该 import 链；不能靠改写 `__init__.py` 而声称官方包完全未变。[固定依赖表](https://raw.githubusercontent.com/cvg/LightGlue/eb42fee2d71449efb0aa5c10549752b5d75384d8/requirements.txt)，[固定包入口](https://raw.githubusercontent.com/cvg/LightGlue/eb42fee2d71449efb0aa5c10549752b5d75384d8/lightglue/__init__.py)。

## 官方 SIFT 语义已核清

固定源码的默认值为：RootSIFT 开；`nms_radius=0`；4096点；OpenCV 后端；检测阈值0.0066667、edge10、first_octave−1、num_octaves4；提取前默认长边1024。OpenCV 路径将 `num_octaves` 传给 `nOctaveLayers`，first_octave 只影响 pycolmap。输出尺度来自 `cv2.KeyPoint.size`，方向由度转弧度，描述子为128维；RootSIFT 顺序为 L1 归一化、最小值夹到1e−6、开平方、L2归一化。`nms_radius=0` 仍执行像素格去重，只有 None 才跳过该过滤；去重的格索引使用 `round(points−0.5)`，不是改写原 keypoint 坐标。[官方 SIFT 固定源码](https://raw.githubusercontent.com/cvg/LightGlue/eb42fee2d71449efb0aa5c10549752b5d75384d8/lightglue/sift.py)。

输入图为归一化浮点 CHW；RGB 在 SIFT 内经 Kornia 转灰，再到 CPU/OpenCV uint8。`extract` 返回带 batch 的 keypoints、scales、oris、descriptors，通常还含 keypoint_scores，另加原图 image_size；xy 回映用 `(xy+0.5)/resize_scale−0.5`。显式 `resize=None` 时该回映为恒等，不应另加0.5；缩放开启时 utils 只回映 xy，不回映尺度字段，故本实验禁用自动缩放。浮点灰度→uint8 路径与 S73 的 cv2 整数灰度不同，不能预设相同 ID 或 N。[官方 utils 固定源码](https://raw.githubusercontent.com/cvg/LightGlue/eb42fee2d71449efb0aa5c10549752b5d75384d8/lightglue/utils.py)。

空图/无特征情况下官方提取器的实际返回仍未做运行验证。未来若异常，保留失败；不能自动换图、加点或放松阈值。

## 对 root 最新设计的评审：支持同特征两匹配器

root 拟让新 BF 和新 LightGlue 消费**同一份新官方 RootSIFT 特征**，覆盖原13图/12对。这能隔离这次 BF 与 LightGlue 的匹配规则差异；新 BF/新 LG 相对旧 S73 仍是整个观察器的变化，不能称纯 matcher 替换。

提议参数应全部显式记入新合同：

| 部分 | 建议冻结内容 |
|---|---|
| 官方提取器 | `backend=opencv, rootsift=True, max_num_keypoints=1500, nms_radius=0, detection_threshold=0.0066667, edge_threshold=10, first_octave=-1, num_octaves=4`；每次 `extract(..., resize=None)` |
| 新 BF | 在该相同 RootSIFT 描述子上 BF L2；双向 k=2；严格 ratio<0.75；再互选；所有接受点保留 |
| LightGlue | SIFT 接口；CPU float32；input_dim128、add_scale_ori=True；9层、4 heads；`flash=False, mp=False, depth_confidence=-1, width_confidence=-1, filter_threshold=0.1` |
| 运行形状 | 每图提取一次保存全部特征；源19共用；12对逐对串行；matcher在 eval/inference_mode；两路使用相同保存坐标/ID/描述子 |
| 科学评分 | 固定请求 F；无几何过滤；完整12对、两匹配器各自的匹配/缺失/分母/空间覆盖；旧 S73/S77 回执不变 |

此处1500、显示尺度、分数门槛均是明确的提取/观察器设置，不是新方法成功标准。S73 已存描述子只有 SHA/shape 等，不足构造这些完整特征；因此**必须新增特征提取**，也必须保存新 N 与原 slot 身份。不能沿用旧 N=1239、三臂共同 ID 或 S78 的六点去挑选新实验样本。

LightGlue 的接受依据是 `matches0>=0` 或官方 compact `matches`，而不是 `matching_scores0>0`。其过滤先互选，再要求分数严格大于门槛；低于门槛的槽可为−1而分数仍非零。无效/拒绝/裁减信息应原样保留。若未来启用裁减，官方 compact 索引已映回原槽；这次关闭裁减有利于复核但不是数值结果。image_size 应显式保持 `[576,576]`，免得 normalization 退回由 keypoint 包围范围决定的尺寸。

## 权重来源、大小与哈希边界

官方 release API 本轮成功返回：asset ID **131252238**，名称 `sift_lightglue.pth`，大小 **47,632,573字节**；创建于2023-10-18T21:09:29Z，更新于21:09:32Z，`digest=null`。下载URL是 [cvg 官方 release 权重](https://github.com/cvg/LightGlue/releases/download/v0.1_arxiv/sift_lightglue.pth)。元数据已保存在 `official_source_01/release_metadata.json`（SHA `c0479ced8d0a04cc20d10e5b45b8fa8bd8f1e282fbc827f4bf0930d9ba5acc0b`）。

本轮**没有官方预期 SHA256 可提供**；大小、release标签或ETag都不能冒充 SHA。后续从该官方URL取得一次字节后，须记录实际 SHA、重定向来源、大小和真实用时；该 SHA 是之后的本地冻结身份，不应称为上游预先发布的摘要。不得从不明镜像替代。root 已计划另在 S80 setup 一次有界获取，本子任务不重复获取。

固定官方构造器 `LightGlue(features='sift')` 会走 `torch.hub.load_state_dict_from_url`，默认缓存名为 `sift_lightglue_v0-1_arxiv.pth`。缺缓存时会自动下载，因此不能在科研正式运行中直接用它探路。可在未来明确走官方本地 weights 分支：`features=None, weights='sift_lightglue', input_dim=128, add_scale_ori=True`，其路径是该源码包下 `lightglue/weights/sift_lightglue.pth`；在新隔离源码树中用已绑定权重文件/链接供给。必须显式冻结SIFT网络配置，并审核加载后缺失/多余参数；官方使用 strict=False，构造器成功不能代替“所有应加载的学习参数已经加载”的证据。此分支本轮未运行。

## 最小隔离获取与运行路径

1. 复用 `.venv-cut3r/bin/python`。完整官方源码从固定 commit 的官方 codeload/仓库取得到新的 `work/S80_lightglue_observer/setup_01`；核提取后的 matcher、SIFT、utils 与上述 SHA 相同。不要改两个旧 venv。
2. 依赖最小候选是旧 S20 的 Kornia 0.8.0 与 kornia_rs 0.1.8，加首选 venv 的已有包。该 overlay 还含 diffusers/open_clip/timm 等；避免把整个 overlay 放在最前面而无意遮蔽现有包。优先在 S80 独立 `deps` 目录只引用这两个包及对应 dist-info，保持原包只读、记录来源。本文只给步骤，未创建/安装这些引用。
3. 正式执行前做一次不加载权重的包导入/版本/原生ABI检查，记录实际 `__file__`，确定官方 lightglue 与指定 Kornia 路径生效。不得用 `python -I` 同时假定 PYTHONPATH 生效；若必须隔离模式，应由 runner 显式加入经过审查的两个绝对路径。
4. 单独准备官方权重并冻结身份；进入正式运行时禁用隐式网络获取。缺包、源码错位、权重不符、关键模型参数未加载，应保留失败并停止，不自动换后端、重下模型或改设置。

当前可执行且不加载模型的路径检查草案（不代替上述正式导入测试）：

```sh
'/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/.venv-cut3r/bin/python' -I - <<'PY'
import importlib.util
for name in ('torch', 'torchvision', 'cv2', 'numpy', 'lightglue', 'kornia'):
    spec = importlib.util.find_spec(name)
    print(name, None if spec is None else spec.origin)
PY
```

未来实验命令形状应为“固定解释器 + 已审 runner + 精确合同 SHA + CPU + create-only 输出”；**当前本文件未提供或假装存在可直接执行的全12对 runner**。root 正在另立 S80 合同与实现。正式 runner 必须包含图像/特征/权重身份、两观察器全12对、原始结果、资源终态和失败保留；单个官方 demo 命令不足替代它。

## CPU/MPS 与资源边界

本机静态系统信息为 arm64、64GiB内存、16个物理/逻辑CPU、macOS26.7。本轮没有导入 Torch 查询 MPS，也没有做任何推理，所以 **MPS实机可用性、全12对耗时、峰值RSS均未测量**。源码存在CPU/MPS设备路径不等于本机已经通过。首选CPU可避免GPU依赖；没有必须使用CUDA/flash-attn/pycolmap的理由。选OpenCV SIFT时，提取器无论输入device仍转CPU运行。

无法凭源码给出已验证的最小RAM。作为规模参考，若两边各1500点，未融合的4-head float32注意力矩阵一份约36MB，另有网络权重、其它激活与运行时；这不是峰值或硬下界。一次只保留一个匹配批次、完整图像特征另存，可避免把12对的注意力同时放进内存。

采用 root 指定的**全阶段10分钟**上限、单进程/逐对执行、不调参；建议先冻结 CPU 线程数（如Torch4线程、OpenCV1线程）并记录，外部观察器采样RSS/子进程与终态。可保守设置8GiB RSS停止线及1GiB输出预算；这是拟议资源保护，不是测得的最低需求或成功保证。若超时/超内存，保存已完成项和缺失项，不换MPS、不减点/层或仅报告成功目标。MPS若以后使用应另立运行配置，不与CPU结果混写。

## 来源访问与未做事项

本轮官方网页接口全文读取 SIFT/utils、requirements、pyproject、包入口及README相关段。官方 release API 的网页工具读取失败已知；随后标准 HTTPS 元数据读取成功。第一次 urllib 读取 SIFT/requirements 遇TLS EOF，保存在 `official_source_01/FETCH_RECEIPT.json`；utils与release元数据成功。SIFT只用一次保留TLS验证的curl备用读取成功，回执 `FETCH_SIFT_ATTEMPT02.json`；requirements没有继续重试或假造本地成功文件。

本次未下载权重、安装包、改原venv、导入科学包、读取PNG正文、运行特征/匹配/生成或评分。报告是实际文件和接口预检，不是真模型结果；旧 S73/S77、S78视觉判定及创新状态保持独立。
