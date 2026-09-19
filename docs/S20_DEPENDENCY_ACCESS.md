# S20：原 VAE 与 OpenCLIP 的官方依赖入口核验

核验日期：2026-09-06。实际 HTTP 请求覆盖 UTC 12:39:16–12:41:36（北京时间 20:39:16–20:41:36）。本轮只读固定源码、官方网页、元数据和小配置；没有下载模型权重，没有加载模型或读取图像、实验数组，没有安装包。本报告不代表完整 VMem 视频已经运行。

**结论：原 VAE 的匿名入口当前不可用，具体原因和确切权重身份尚未确定；原 OpenCLIP 对应的 LAION 权重公开可访问，已有固定 revision、字节数、LFS SHA 和可续传的官方 URL。** 因此可以继续准备 OpenCLIP 组件，但不能据此宣称原视频基线的依赖已经齐全。

采用本地 Claude [scientific-critical-thinking](/Users/rocket/.claude/skills/sci-scientific-critical-thinking/SKILL.md) 的证据分层方法：区分实际 HTTP 结果、源码推断和未执行的运行兼容性；未调用 Claude 模型。原流程与版本来源以 [VMem 固定作者提交](https://github.com/runjiali-rl/vmem/tree/39291e4f272f6b4f270691d930926ab5930f942e) 为准。作者没有在 requirements 中锁定本轮选用的 OpenCLIP 2.30.0；它是本机兼容候选，不能写成作者原始锁定环境。

## 1. 原 VAE：已知到哪里，尚缺什么

固定源码 `modeling/modules/autoencoder.py` 调用 `AutoencoderKL.from_pretrained("stabilityai/stable-diffusion-2-1-base", subfolder="vae", force_download=False, low_cpu_mem_usage=False)`，没有指定 revision。编码用后验均值乘 `0.18215`；解码先除该系数，缩小倍数为 8。后续适配必须保留这些选择。[原源码](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/modules/autoencoder.py)

| 官方请求 | 实际结果 | 能支持的结论 |
|---|---|---|
| [原模型 API](https://huggingface.co/api/models/stabilityai/stable-diffusion-2-1-base?blobs=true) | HTTP 401，41 B | 本次匿名请求无法取得模型元数据 |
| [原 vae/config.json](https://huggingface.co/stabilityai/stable-diffusion-2-1-base/resolve/main/vae/config.json) | HTTP 401，29 B | 本次匿名请求无法取得原 VAE 配置 |
| [Stability AI 名下 SD2 搜索 API](https://huggingface.co/api/models?author=stabilityai&search=stable-diffusion-2&limit=100) | HTTP 200，内容 `[]` | 本次公开列表未返回匹配项目 |
| [原 Stability-AI/stablediffusion README API](https://api.github.com/repos/Stability-AI/stablediffusion/readme) | HTTP 404；此前 raw 请求另有 curl 35 TLS 失败 | 此入口没有提供可核实的迁移说明 |

401 本身不能区分私有、受限访问、入口撤下或其他身份/平台状态，也不证明登录就能解决；空列表和 404 同样不能证明永久删除。**原 VAE 当前 revision、文件大小、文件 SHA 均记为未知。** 本轮有限官方检索未找到可以确认同一出版者迁移且保持权重身份的说明，不能把“未找到”写成不存在。

[Stability AI 官方 release notes](https://platform.stability.ai/docs/release-notes) 中 2024-10-11 的 SD2.1 API 弃用说明针对 API 服务，不能转用为 Hugging Face 权重删除或迁移证据。搜索出现的社区仓库不具备相同出版者身份，本轮未从其获取权重；不将其作为原基线来源。[官方 SVD 说明](https://github.com/Stability-AI/generative-models) 指出时序解码器作过修改，因此也不能用 SVD VAE 冒充本研究指定的 SD2.1 VAE。

下一项真正能解除阻碍的证据是：原出版者恢复的原入口，或原出版者明确给出的迁移位置及原 VAE 内容身份；也可以审计用户以后明确提供且有来源链的既有原权重。取得前不填写猜测的 SHA，不把其他 VAE 当作原复现。主 VMem 权重的既有 gate 不在本轮重复请求，依然是独立缺项。

## 2. OpenCLIP：可用的最小原权重路径

原 `conditioner.py` 构建完整 `ViT-H-14`，pretrained 标签为 `laion2b_s32b_b79k`，随后只使用 `encode_image`。这仍会构建包含文本塔的完整 CLIP；不能按只有图像塔估算原路径开销。原预处理是 Kornia 的 224×224 bicubic resize，`align_corners=True, antialias=True`，接着 `(x+1)/2` 和指定 mean/std；返回的 PIL transforms 未被原代码调用。[原 conditioner](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/modules/conditioner.py)

[LAION 原仓库 API](https://huggingface.co/api/models/laion/CLIP-ViT-H-14-laion2B-s32B-b79K?blobs=true) 实际 HTTP 200，`private=false, gated=false`，model card license 为 MIT，revision：

`1c2b8495b28150b8a4922ee1c8edee224c284c0c`

| 文件 | 官方字节数 | 用途与选择 |
|---|---:|---|
| `open_clip_model.safetensors` | 3,944,517,836 | **选择此 OpenCLIP safetensors 权重** |
| `open_clip_pytorch_model.bin` | 3,944,692,325 | 原旧格式备选；本轮不需要同时获取 |
| `model.safetensors` | 3,944,552,236 | 仓库中的另一格式；不是该版本 OpenCLIP 默认文件，不按相似名字替换 |
| `open_clip_config.json` | 637 | 已真实获取；用于来源与架构核对 |

推荐文件的官方 LFS SHA-256：

`0084e75319a50ad85ef45377bad5bc38f2f58824459eb690048d51c9f8863be5`

[固定 revision 的官方 safetensors URL](https://huggingface.co/laion/CLIP-ViT-H-14-laion2B-s32B-b79K/resolve/1c2b8495b28150b8a4922ee1c8edee224c284c0c/open_clip_model.safetensors) 的匿名 HEAD 于 UTC 12:41:34.668504–12:41:36.563421 实测 302→200；最终 `Content-Length: 3944517836`、`Accept-Ranges: bytes`，初始响应的 `x-linked-etag` 与上述 LFS SHA 一致，`x-repo-commit` 与固定 revision 一致。**HEAD 没有下载模型正文，官方 SHA 尚未由本机完整文件重算验证。** CDN 自身 ETag 是另一对象标识，不能代替 LFS SHA。回执保留响应头，但不保存带签名的重定向查询参数。

## 3. 为什么选 OpenCLIP 2.30.0 的这个格式

本轮通过作者 GitHub API 读取 `v2.30.0` 的 [pretrained.py](https://github.com/mlfoundations/open_clip/blob/v2.30.0/src/open_clip/pretrained.py)、[factory.py](https://github.com/mlfoundations/open_clip/blob/v2.30.0/src/open_clip/factory.py)、[constants.py](https://github.com/mlfoundations/open_clip/blob/v2.30.0/src/open_clip/constants.py) 和 [ViT-H-14 配置](https://github.com/mlfoundations/open_clip/blob/v2.30.0/src/open_clip/model_configs/ViT-H-14.json)，保存原文与 SHA，未安装或导入该包。

源码将指定 pretrained 标签映射到上述 LAION 仓库；安装 safetensors 时，下载器先尝试 `open_clip_model.safetensors`，失败会回退 `.bin`。factory 对 `.safetensors` 调用 `safetensors.torch.load_file`，也接受 `pretrained` 为已有本地文件路径。LAION 的 637 B 配置中 `model_cfg` 与 2.30.0 自带 ViT-H-14 配置逐字段完全相同：图像尺寸 224、视觉层数 32/宽度 1280/patch 14，文本层数 24/宽度 1024，输出维度 1024；mean/std 也与原 VMem 相同。23 项静态检查通过，仅证明源码与元数据一致，不证明真实权重加载或数值运行已经成功。

下一阶段应先按固定 URL 有界获取单一 safetensors 文件，保留中断文件，完整下载后核字节数与全文件 SHA，再通过明确的本地路径加载，避免原命名标签跟随 `main` 或在临时错误后自动下载另一份大文件。示意接口（**本轮未执行**）：

```python
model = open_clip.create_model_and_transforms(
    "ViT-H-14", pretrained=verified_local_safetensors_path,
    precision="fp32", device="cpu",
)[0]
```

该本地路径选择需要在新阶段透明记录，保持原架构、激活函数、完整模型、eval/frozen 权重与原 Kornia 预处理。不要强制 QuickGELU，不将库返回的预处理替换进原 wrapper。运行时还必须检查权重加载结果；静态架构相同不能代替真实检查。

[PyPI 2.30.0 元数据](https://pypi.org/pypi/open-clip-torch/2.30.0/json) 给出 Python ≥3.8，基础依赖为 torch≥1.9、torchvision、regex、ftfy、tqdm、huggingface-hub、safetensors、timm；不需要训练 extras。wheel 大小为 1,514,664 B，SHA-256 `68343092181a03a6a0b3ba8a3529856e40299d4c06bc83082ce73e0ba438187a`。采用 `ViT-H-14 + 本地权重` 时模型结构来自包内配置，无须另下 Transformers 格式整仓；637 B Hub 配置用于审计。原调用仍构建完整 CLIP，本轮没有验证删去文本塔的替代实现。

本机已有 Torch 2.7.0、torchvision 0.22.0、NumPy 1.26.4、transformers 4.48.3、HF hub 0.36.2、accelerate 1.4、safetensors 0.8；版本由主任务本轮检查提供。本报告只提出 OpenCLIP 2.30.0 的来源和格式方案。隔离 overlay 的包闭包、真实导入、权重加载、CPU 前向及内存上限，须由相应阶段的冻结协议与回执完成。

## 4. 留存记录与未解决问题

全部请求的时间、URL、HTTP 状态、curl 错误、正文长度和 SHA 在 [work/S20_dependency_access](/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_dependency_access/)；其中 [静态检查](../work/S20_dependency_access/static_compatibility.json)、[HEAD 回执](../work/S20_dependency_access/clip_weight_head.json) 和 [汇总回执](../work/S20_dependency_access/receipt.json) 可独立追溯。两次 curl 35 TLS 失败（原 Stability README raw、OpenCLIP tag 元数据）均保留；前者随后官方 API 404，后者不妨碍已分别成功取得的 v2.30.0 四个源码文件。网页工具的失败也保留在检索文本中，未用成功请求覆盖失败。

本轮边界：模型权重正文下载 0、模型加载 0、推理 0、图像解码 0、实验数组读取 0、包安装 0。没有读取凭据、提交联系信息或采用镜像绕过访问限制。**仍未拿到原 VAE 的可验证身份，也未完成完整视频生成。**
