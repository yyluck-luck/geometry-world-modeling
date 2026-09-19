from pathlib import Path
import datetime,json,hashlib
ROOT=Path(__file__).resolve().parents[2]; OUT=Path(__file__).resolve().parent
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads((OUT/p).read_text())
audit=load('source_audit.json'); inv=load('local_inventory.json'); cand=load('public_512_candidate.json')
weights_sum=5056346672+3173761006+3944517836
report=f'''# S17：完整 VMem 视频基线的本机可行性与具体缺项

**现在还不能在本机直接跑完整 VMem：主要生成权重仍要求账号同意分享联系信息，匿名请求实际返回 401；原代码另有 CUDA 设备写死和本机依赖缺项。但作者指定的 CUT3R 512 DPT 几何权重已经确认公开可取，且支持带 Range 的响应；这个组件与 CPU 数学回退可以独立推进。**

检查时间：{now}。本报告由 agent `s15b_bonn_resolution` 只读项目记录、固定源码与公开元数据完成；没有加载权重、实例化模型、解码真实图像或生成视频。主要 15 个显式 HTTP 元数据请求及失败保存在 `work/S17_vmem_feasibility/`；Web 原文检查另列于回执。完整项目原验收见 [PROJECT_DELIVERY_TRACKER](PROJECT_DELIVERY_TRACKER.md)，组件成功不能勾掉完整视频项。

## 当前设备和本机已有资源

实查设备为 **Apple M3 Max，64 GiB 统一内存（68,719,476,736 字节）**。现有 `.venv-cut3r` 是 PyTorch 2.7.0，CUDA 不可用，MPS 已构建且可用。最新磁盘快照剩余 **{audit['disk']['free_bytes']:,} 字节，约 {audit['disk']['free_bytes']/2**40:.3f} TiB**，空间不是当前主要瓶颈。这是采样时可用量，会随并行任务变化。

本轮只检查项目 `data/cut3r`、固定 VMem checkout，以及相关 Hugging Face / CLIP 缓存目录，没有扫描整台电脑、读取账号 token 或把其他私人目录当研究资源。在这些指定位置，只发现已验证的 `cut3r_224_linear_4.pth`：2,994,205,002 字节，历史完整 SHA-256 为 `7a7d83e47f822e040980c8f5aff4c15aa94366d469d3ceae51fa30cc2f62327d`。本次核对文件存在和大小，未重新读完整 3 GB 文件；历史身份见 [CUT3R 准备与真实运行记录](CUT3R_LOCAL_READINESS.md)。

**这个 224 linear 权重不是 VMem 指定的 512 DPT 权重。** 换它进 VMem 可以是明确标注的变体研究，不能记为原基线复现。盘点时以下四个完整视频依赖都没有在指定缓存内找到：

| 组件 | 固定代码实际加载入口 | 发布元数据与大小 | 本轮可访问状态 |
|---|---|---|---|
| VMem 主生成器 | `liguang0115/vmem` 的 `vmem_weights.pth` | **5,056,346,672 B（4.709 GiB）**；revision `ac5921080a57f5a634f4b9acbbc8f3db67c9d113`；发布 LFS SHA `675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4` | API公开，但 `gated=auto`；文件匿名 HEAD **401 / GatedRepo**。必须账号满足条件，auto 不等于匿名开放。没有代替用户提交信息或点击同意。 |
| VMem 指定几何模型 | `liguang0115/cut3r` 的 `cut3r_512_dpt_4_64.pth` | **3,173,761,006 B（2.956 GiB）**；revision `b14faf986da0df405cff1b41e60e2975c4da2745`；发布 LFS SHA `45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103` | API `gated=false`；匿名 HEAD 经发布平台 CDN 成功返回 206。可以走下一项有界公开获取。 |
| 图像条件编码器 | OpenCLIP `ViT-H-14` / `laion2b_s32b_b79k` | 发布方 `laion/CLIP-ViT-H-14-laion2B-s32B-b79K`，revision `1c2b8495b28150b8a4922ee1c8edee224c284c0c`。`open_clip_model.safetensors` 为 **3,944,517,836 B**；`open_clip_pytorch_model.bin` 为 **3,944,692,325 B**。 | API公开、`gated=false`。只需兼容的一种格式，不能把两份重复计算为必需下载。项目未钉住 open_clip 版本，实际所选格式仍须在隔离环境固定。 |
| 图像 VAE 编解码器 | `AutoencoderKL.from_pretrained('stabilityai/stable-diffusion-2-1-base', subfolder='vae')` | 本轮没有取得该原入口的文件清单和可靠大小，**未知**。 | 两次独立 curl API 请求 TLS 失败；另用 Web 打开官方模型页得到 **401**。只确认本轮匿名入口失败，不能据此判断永久删除、私有或具体门控类型。不能静默替换为另一 VAE。 |

证据为 [VMem 发布模型页](https://huggingface.co/liguang0115/vmem)、[VMem 模型 API](https://huggingface.co/api/models/liguang0115/vmem?blobs=true)、[作者 CUT3R API](https://huggingface.co/api/models/liguang0115/cut3r?blobs=true)、[LAION 发布 API](https://huggingface.co/api/models/laion/CLIP-ViT-H-14-laion2B-s32B-b79K?blobs=true)；本地实际加载位置是 `modeling/pipeline.py:47–91`、`modeling/modules/autoencoder.py:10–18` 和 `modeling/modules/conditioner.py:11–16`，均有源码快照。

现有 CUT3R 环境还未安装 diffusers、open_clip、kornia、spaces、gradio、evo、open3d、imageio、pytorch_lightning。这里没有安装全部 requirements 来碰运气，也没有改动已有成功环境；后续应按实际生成调用的传递导入依赖建立隔离环境。某包没安装不能直接等同于算法不可能在 CPU 上实现。

## 官方代码与公开服务现状

本地完整 checkout 为 `/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem`，Git HEAD 与作者当前 main API 均为 **39291e4f272f6b4f270691d930926ab5930f942e**。既有七份冻结源码 SHA 全部仍一致，本轮另保存 18 份关键源码身份。不是以旧笔记猜测仓库仍没更新。

[作者当前 README](https://github.com/runjiali-rl/vmem) 仍要求 Hugging Face 登录并填写访问信息。已检查该仓库公开 issue 列表及两个运行问题的作者回答，没有找到作者提供的 CPU / MPS 完整视频成功路线。此为有限原始来源检查，不证明所有社区版本都不存在。[issue 2 作者回答](https://github.com/runjiali-rl/vmem/issues/2) 指向编译 curope，并没有提供 Mac 实测。

作者 [Hugging Face Space 元数据](https://huggingface.co/api/spaces/liguang0115/vmem) 在本轮为 **PAUSED**，请求硬件 `l4x1`、当前硬件为空；没有调用在线推理或上传用户照片。即使 Space 恢复，也只是作者托管服务，不能替代本机可复现基线。网页上可见历史演示不等于我们运行成功。

## CUDA 绑定中哪些可以保持数学语义地替换

| 固定代码位置 | 已核实行为 | 可执行的隔离适配方向与证据边界 |
|---|---|---|
| `utils/util.py:673–729` 的 `do_sample` | autocast 固定写 CUDA；相机、内参、输入帧 mask 用 `.to('cuda')`，尽管函数接收 device 参数 | 统一使用明确传入的 `torch.device`；CPU使用普通上下文或可审的精度设置。保持随机噪声、条件、相机、mask和采样步数不变。只改设备分派是可行软件改动，仍需小张量接口回归。 |
| `modeling/modules/transformer.py:60–76` 的 Attention | 显式只允许 `SDPBackend.FLASH_ATTENTION` | 允许 CPU / MPS 的 SDPA数学后端，或沿 query 维分块但每块始终看到完整 K/V。`softmax(QKᵀ/√d)V` 数学定义不变；不能分别对 key 块做独立 softmax。不同实现与精度通常不逐位相同，必须预定容差。实际 CPU 强制 FLASH 是否可用应小张量测量，不凭名称断言。 |
| `extern/CUT3R/src/croco/models/curope/setup.py` 与 `curope.cpp` | 安装用 CUDAExtension 和 `.cu`；但 C++ 本身存在 FP32 `rope_2d_cpu` 标量公式，按正负位置计算有符号角度 | 构建依赖 CUDA不等于数学不能用CPU。纯 PyTorch 可按同公式做旋转，正负位置、F0、dtype、in-place语义均须核。C++ 中有 CPU 分支，不能笼统说整个算子只有CUDA实现。 |
| 嵌入 CUT3R 的 `models/pos_embed.py:117–180` | 导入 CUDA RoPE 失败后只打印“fallback”；后面的 Python 类整段被注释，未定义可用 `RoPE2D` | 可在隔离副本接入经审的有符号旋转。已有 S4 224 的数学检查可复用思路，但不能自动宣称 512 DPT / 嵌入分支已经通过。嵌入 blocks.py 实际先把 q/k 转为 FP16，故CPU回退还必须检查半精度接口及还原dtype，不能只验证FP32。原代码保持不变。 |
| `app.py:21,156` | 只在 CUDA / CPU 中选设备，装饰器仍指定 CUDA；无 MPS 选择 | 最小实验使用无 UI 的明确入口，先避开 Gradio / Space 的外部服务装饰器。不是通过删除完整算法组件绕过问题。 |
| surfel 后处理与对齐 | 主要是 Torch、NumPy、SciPy 和 Python；`construct_and_store_scene` 实际传 self.device，配置仍有 400 次对齐迭代 | 尚未完成 MPS 的 quantile、SVD、插值、优化器等传递算子审计。必要时明确固定这部分在CPU，不偷偷改变数学或跳过对齐/清理。 |

[PyTorch 2.7 SDPA 原文](https://docs.pytorch.org/docs/2.7/generated/torch.nn.functional.scaled_dot_product_attention.html) 给出统一公式和后端切换，并明确融合浮点运算可能产生数值差。**因此现在可以推进“保持数学定义的 CPU 适配”，但不能保证与 CUDA 逐字节相同、整视频质量相同或本机足够快。** 根任务已另分派人工张量的数值预检；以其独立实际回执为准，本报告不预写通过。

## 内存估算的依据与不能推断的事

三个已知大文件（主生成器、512 DPT、一份 OpenCLIP safetensors）磁盘大小合计 **{weights_sum:,} B，约 {weights_sum/2**30:.3f} GiB**，还不含 VAE。它们的文件大小不是精确常驻 RAM；dtype、checkpoint附带内容、模型副本与加载器中间对象都会改变内存。代码在 `__init__` 中建立主模型后再保留 `state_dict` 至函数返回，存在额外加载副本的可能。OpenCLIP 创建完整模型再使用图像编码分支，也不能只按图像 embedding 大小预算。

默认生成调用硬写 576×576、T=8、50 个采样步骤，latent 网格 72×72。CFG 将条件 / 无条件批量拼接。根据源码形状，若普通 FP32 数学 attention 显式保存整张分数矩阵：

- 全分辨率空间 attention：`16 × 5 × 5184 × 5184 × 4` = **8,599,633,920 B，约 8.009 GiB**，只是一个 score 张量。
- `output_ds2` 的跨视图 attention：`2 × 10 × 10368 × 10368 × 4`，同样约 **8.009 GiB**。
- Softmax中间量、Q/K/V、残差、解码、模型参数和建图还要内存；上述数值既不是总峰值，也不能相加宣称两层同时常驻。CUDA融合实现可能不显式分配这些完整矩阵。

所以“机器64GB、权重只有5GB”不足以保证可运行。沿 query 维分块、保留完整 K/V 可降低数学回退的瞬时 score 空间，而不减少帧数或分辨率；这是待小型回归及真实资源门验证的工程路线。首次完整视频不应承诺耗时。本报告也不拿 UI `get_duration_navigate_video` 的硬编码 15 秒估算当实测性能。

**独立512两图前向的预算依据较明确：** 已有224两图CPU实际 RSS 峰值为 **6,384,320,512 B**，但它属于不同模型头。按两张640×480 Bonn照片和官方512预处理，输入应为512×384，每张patch token从196增至768，线性项约3.918倍、注意力二次项约15.354倍；一个两帧/16头 FP32 encoder score 矩阵估算为 **75,497,472 B（72 MiB）**。这不是完整模型峰值；DPT头、decoder state与加载峰值仍需实测。建议先使用 **32 GiB RSS / 600秒墙钟** 的外部停止门，明确这是保护预算而非预测它一定会用多少内存。不要把224耗时0.878秒直接乘比例当512保证。

## 公开512权重：可立即进入单独获取合同

固定公开下载入口：

```text
https://huggingface.co/liguang0115/cut3r/resolve/b14faf986da0df405cff1b41e60e2975c4da2745/cut3r_512_dpt_4_64.pth
```

期望大小：`3173761006`。发布者模型仓库 LFS SHA-256：

```text
45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103
```

匿名 HEAD 的 `x-linked-size` 和 `x-linked-etag` 与作者 API 一致；跟随官方重定向并带 `Range: bytes=0-0` 的 **HEAD** 返回 `206`、`Content-Range: bytes 0-0/3173761006`、`Accept-Ranges: bytes`。这证实远端对 Range 元数据的支持。**本任务没有 GET 权重载荷，实际断点载荷传输和最终完整 SHA 尚未由本任务验证。** CDN ETag 是另一个值，不能把它误当模型 LFS SHA。

[候选获取与两图合同](../work/S17_vmem_feasibility/public_512_candidate.json) 明确 revision、大小、发布SHA、只读原S15A索引0/1及资源门。后续获取必须逐段检查206与精确Content-Range，遇到整包200应拒绝，保留部分文件，结束核完整SHA和ZIP CRC后才允许反序列化。这个JSON是候选，不取代根任务最终冻结。根任务在本报告形成期间已通知另立 `work/S17A_checkpoint_acquisition/contract.json` 启动获取；**下载是否完成应看那个阶段的实际回执，不由本报告预写。**

## 最小真实测试与接下来的执行顺序

**下一实质工作一：512 DPT 两图组件验证。** 使用原S15A已见Bonn照片索引0/1，即 `1548340550.99864.png` 和 `1548340551.40132.png`，输入SHA来自原manifest。只跑两张、CPU FP32、8线程、seed0，真实预处理到512×384；新权重身份必须满足上表，载入后实际 head 必须为 DPT、模型配置为512。保存2×6输出头、位姿、状态、真实encoder计数、形状、有限值、时间和内存；不打开传感器GT、轨迹或其余照片，不声称深度准确率或新场景泛化。

旧 `scripts/run_cut3r_local.py` 第169行固定size224，第218行强制linear/[224,224]，并绑定旧权重清单，因此**不能只换文件名重用旧runner**。应建立新runner和独立manifest，保持旧程序、权重和结果不动。两张官方独立CUT3R前向成功后，还需核同一权重在VMem嵌入分支、对齐和完整建图调用中的兼容性；独立CUT3R成功不替代这一步。根任务已分派该新runner的代码/人工前审，实际执行等待其冻结与下载核验。

**下一实质工作二：CPU / MPS 数学回退。** 仅用人工小张量核attention公式/设备搬运/正负位置RoPE及失败条件；不同实现交叉核，而不装载GB权重或假装生成了视频。这个准备可以和公开512获取并行。

**真正视频的最小接受条件：** 主VMem、指定512几何、指定VAE、匹配OpenCLIP均具备且身份冻结，全部必要适配通过后，固定一张作者自带实拍（例如 `test_samples/changi.jpg`）、初始OpenGL相机与内参、确定的短移动轨迹和seed42。保留原50步/576²/T8，不用1步去噪结果冒称原基线。首次只有1张上下文时代码实际会填到**7张目标+1张上下文**；即使只请求1张目标，也仍填充到8帧计算，不能许诺单帧成本。要证明记忆闭环，至少完成第一批7目标生成与建图，再让第二批4目标真实查询并读回记忆，保存选择trace、条件ID、原始输出帧与编码后视频，并核视频可解码、帧数、分辨率和非重复内容。这是**至少两次生成批次、最多1+7+4=12张保存帧**的最小完整回路，仍不是长视频质量或论文指标复现。

首轮可先只让第一批闭合，按实测资源决定第二批；两者阶段标签必须区分。源码会对生成过的所有帧重新做几何及400次对齐，这个耗时目前没有本机实测。调用 Navigator 会清理名为 `visualization` 的目录，最小入口必须使用新的隔离工作目录，不能破坏已有展示材料。视频轨迹需先固定，不能看生成结果后挑最好片段。

**仍属外部缺项：** 主VMem访问条件和原VAE入口可用性。需要用户已合法拥有的明确权重文件或由用户自行完成所需账号条件后才能接上；我们不提交姓名、邮箱、申请或同意分享信息。本机其余适配和公开512组件可继续做，不必空等，也不把改用另一生成模型称作VMem复现。

## 回执、失败和技能边界

本报告应用本地 Claude `sci-scientific-critical-thinking` 的构念效度和替代解释检查：代码有CPU参数≠已支持完整CPU，权重公开metadata≠匿名可取，数学等价≠浮点逐位一致，组件真实前向≠完整视频。它只指导科研审查，没有调用Claude模型/CLI。与根任务和独立数学预检agent共享精确源码位置，未改根研究日志/记忆。

保存了原始HTTP响应、UTC起止、固定URL、源码SHA、机器/文件元数据、发布权重SHA和候选合同。失败包括两次Stable-Diffusion API TLS失败、一次CLIP API TLS失败后成功、VMem权重匿名401；Web模型页401、一次误猜HuggingFace collection入口失败和GitHub issues Web读取失败另记。一次本地文档检索工作目录写错、一轮issue作者为空导致打印中断，修正后完成实际读取；没有删失败，也未把这些错误解释成模型质量结果。

回执目录：[work/S17_vmem_feasibility](../work/S17_vmem_feasibility/)。本任务新增权重载荷、模型前向、真实RGB/GT解码、视频生成均为 **0**。下一步以独立S17A获取回执、S17B两图runner前审和实际CPU数学预检为依据推进；本报告是可行性证据，不是完整基线完成声明。
'''
(ROOT/'docs/S17_FULL_VIDEO_BASELINE_FEASIBILITY.md').write_text(report)
print(sha(ROOT/'docs/S17_FULL_VIDEO_BASELINE_FEASIBILITY.md'))
