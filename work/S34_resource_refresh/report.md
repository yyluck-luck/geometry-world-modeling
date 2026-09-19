# S34 后：S20 原始生成资源刷新

**当前仍未具备 S20 原 1→5→9 真实生成的四组件执行条件。限定扫描没有发现可用的原 VMem 主权重或指定 SD2.1 VAE；也没有发现原 OpenCLIP 完整权重。现成的 512 DPT 完整文件仍在。** 这只描述本轮指定项目／缓存范围，不外推用户整台电脑或所有账号都没有这些文件。

唯一科学执行门保持为：**先具备合法可用、原身份可核的 VMem 主权重和指定 VAE，再统一补齐并冻结四组件，接入 S20 原始两批生成／cache baseline。** 当前没有可诚实给出的完整生成启动命令。公开 CLIP 是届时可补的选项；只下载暂时无法启用的 3.94 GB 文件不列为必须的下一科研动作。本次刷新完成即停止，不扩检、不下载、不增加短窗实验。

实际官方请求时间：2026-09-06 22:03:10.759933–22:03:11.970887 UTC，即北京时间 2026-09-07 06:03:10–06:03:11。文件名／stat 检查为 22:03:44.750981–22:03:44.832128 UTC；报告写入时间见 receipt.json。6 个官方 URL 各一次，硬设 20 秒与 1 MiB 上限，禁重定向；实际最长 1.196660 秒，最大正文 25,101 B，累计 37,259 B。没有另用无限制网页检索或请求模型载荷。

## 四组件的实际状态

| 组件 | 身份与所需文件 | 本轮观察 |
|---|---|---|
| VMem 主生成器 | 作者 `liguang0115/vmem`，revision `ac5921080a57f5a634f4b9acbbc8f3db67c9d113`；`vmem_weights.pth`，5,056,346,672 B，发布 LFS SHA `675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4`。 | [官方模型元数据](https://huggingface.co/api/models/liguang0115/vmem?blobs=true) HTTP 200，仍 `gated=auto`。限定项目和两个已记录 HF hub 下均未发现对应完整文件／仓库。未请求 gated 文件，也未测试账号访问权限。 |
| 指定 VAE | 原源码确切调用 `AutoencoderKL.from_pretrained('stabilityai/stable-diffusion-2-1-base', subfolder='vae', force_download=False, low_cpu_mem_usage=False)`；原作者没有固定 revision。需原 `vae/config.json` 与同 revision 完整 VAE 参数；当前 Diffusers 0.32.2 loader 默认先选 `diffusion_pytorch_model.safetensors`，允许回退 `diffusion_pytorch_model.bin`，这两者是 loader 文件名规则，不是已证存在的原发布载荷。 | [原模型元数据 API](https://huggingface.co/api/models/stabilityai/stable-diffusion-2-1-base?blobs=true) 本次 TLS 错误，无 HTTP 状态；**不是本次新 401**。原 config、revision、完整权重大小／SHA 仍未知；限定缓存未发现对应仓库或 config／权重。 |
| OpenCLIP | 原 `ViT-H-14`／`laion2b_s32b_b79k`；LAION revision `1c2b8495b28150b8a4922ee1c8edee224c284c0c`。选用 `open_clip_model.safetensors`，3,944,517,836 B，发布 LFS SHA `0084e75319a50ad85ef45377bad5bc38f2f58824459eb690048d51c9f8863be5`。 | [官方元数据](https://huggingface.co/api/models/laion/CLIP-ViT-H-14-laion2B-s32B-b79K?blobs=true) HTTP 200、`gated=false`，同历史身份；限定扫描未发现完整模型文件。S20 保存的 637 B config 与库代码不是权重。它可以以后尝试公开获取，本轮没有重新 HEAD／下载或承诺当前载荷传输成功。 |
| CUT3R 512 DPT | `data/cut3r/cut3r_512_dpt_4_64.pth`；当前 stat 3,173,761,006 B，device 16777234、inode 261770284、mtime_ns 1788694007362611958。 | 本次只读 stat。既有 S17B freeze 回执记录完整 SHA `45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103` 和归档 CRC PASS，后来真实几何已使用。未再次读 3 GB 做哈希；旧 533,225,219 B `.s17a.partial` 保留，不把它算第二份完整权重。 |

VAE 原编码取后验均值，再乘 0.18215；解码除同系数，downsample=8。源码中这些选择确定，但不能据此推断所有相似 VAE 参数等价，也不能从其他模型挑一个 VAE 冒充原 baseline。取得原发布者恢复入口、明确迁移链或有完整合法来源的原文件后，须冻结实际 config／参数 revision 和全文件 SHA，才进入四组件加载合同。[原 VAE 调用源码](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/modules/autoencoder.py)

## 官方更新与限定扫描

[当前 GitHub README API](https://api.github.com/repos/runjiali-rl/vmem/readme?ref=main) HTTP 200；解码 SHA `43024fe529340c4c0ff938c38cc99027b82eb0b56653f2baa0406092231850ba`，与固定 VMem commit `39291e4f272f6b4f270691d930926ab5930f942e` 及 S25 相同。仍要求 HF 认证与访问资料，没有新增官方替代入口。[作者项目页](https://v-mem.github.io/) 也为 HTTP 200，同 S25 SHA `2f9c318c93e13330c867e12a57076c75cb6b5ada81287119c1a10884677b9d30`；其中没有新的 ModelScope／Drive 权重链接。[Releases API](https://api.github.com/repos/runjiali-rl/vmem/releases?per_page=100) 本次 TLS 失败，不据此声称现在没有 release。两个失败各一次，无重试；6 请求额度已结束。

只查主项目、原 VMem checkout 的所需模型文件名（排除 git、软件包／pip cache、venv），以及先前明确记录的 `/Users/rocket/.cache/huggingface/hub`、`/Users/rocket/.cache/clip`、项目 `work/S20_environment/huggingface-cache/hub`。HF 只查四个指定模型仓库目录；它们均未出现。`~/.cache/clip` 不存在。没有列举其他账号仓库、访问 token、扫描家目录其他位置或读取模型内容。宽文件名匹配还命中 `work/S20_dependency_access/vae_config.receipt.json`，它是 729 B 历史请求回执，**不是原 VAE 配置**。

## CPU／MPS 资源结论

本次 sysctl 显示 Apple M3 Max、68,719,476,736 B 物理内存（64 GiB）；项目盘空闲 1,362,171,084,800 B，是本次时点的容量。磁盘空间不是当前两个原组件缺件的解释，权重字节总量也不能当完整生成峰值 RAM。

已有实际证据分别为：S20 完整 Pipeline／Navigator 在隔离 overlay 导入通过（历史 9.275 秒、峰约 665 MB，0 模型构造）；S17 CPU 原生 FLASH 的四组小张量实测；真实 CUT3R／几何消费者可在本机运行。S20 历史环境为 Torch 2.7／Diffusers 0.32.2／OpenCLIP 2.30.0。本次只读这些回执和所需 loader 源码，没有重导入或重做算子实验，也没有认证整套环境此后每个文件都未变化。

因此 CPU 路径有工程可行性依据，**完整 576²、T8、50 步×两批的生成耗时与峰值仍未知**；不能宣称机器无法运行，也不能宣称必然能在预算内成功。原默认 FLASH 无需因旧显式 dense-score 估算而改掉。S20 草案每批 1800 秒／45 GiB 是未来保护预算建议，不是实测预计值或本轮冻结合同。

MPS built/available 为 S17 当时的环境观察；本次未导入 Torch 重测 MPS，也没有完整生成 MPS 算子、数值或内存证据。S20 原计划是 CPU FP32／8 线程；MPS 不作为静默替代路径。

S20 原始闭环保持：初始1实拍，第一批请求4目标但模型实际处理7目标槽（3 padding不入历史），第二批请求4目标，历史1→5→9；原 len5 NMS初始化、真实生成 latent／CLIP缓存、5／9图几何与两个400步对齐必须实际执行。S34 已存八帧 map/render 和普通尺度结果不能替代这个生成链，也不能补造 NMS／latent 历史使它开跑。

本轮沿用 S20 记录的 Supervisor 原代码／最小改动／执行前固定规则，以及本地 Claude scientific-critical-thinking 的证据分层：metadata公开≠载荷已取得、stat≠全文件哈希、导入/组件成功≠完整生成成功、TLS≠新401。不调用 Claude 模型，不改 canonical ledger，不将资源缺件自动改成整个目标 blocked。

实际请求、文件 stat、原始小响应和文件身份见 [receipt.json](receipt.json)、[http_receipt.json](http_receipt.json)、[local_inventory.json](local_inventory.json)。
