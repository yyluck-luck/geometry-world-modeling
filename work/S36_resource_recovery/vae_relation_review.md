# S36：两个 VAE 候选的关系及原件身份边界

独立审阅 UTC：2026-09-07T00:05:54.368938+00:00。审阅者 `/root/supervisor_full_readthrough`。只读父任务已经保存的四份 HTTP 结果、两份小配置与本机 Diffusers 0.32.2 源码；本审阅新增网络请求、权重下载/读取、科学库导入、模型/数值实验均为 0。旧 S20/S35 文件未修改。

**结论：可以确认两个已查询仓库的元数据指向相同 safetensors 对象；可以条件性推断两个配置在原 VMem 的非空间分块路径中使用相同算子结构。仍不能确认原 `stabilityai/stable-diffusion-2-1-base/vae` 身份，不能据此通过 S35 的原件门。**

## 1. 实际取得的证据

父任务四请求均 HTTP 200/无重定向；元数据请求发生于 UTC 2026-09-07 00:00:23.494547–00:00:24.241805，固定 revision 配置请求发生于 00:01:13.957534–00:01:14.709058。该时间是原请求回执时间，不是本审阅重新请求。

| 角色 | 仓库与固定 revision | 配置字节/SHA256 |
|---|---|---|
| 社区 SD2.1-base 候选 | `sd2-community/stable-diffusion-2-1-base` / `4e63672c03103b6c636b8fb4119ba982469b2955` | 553 B / `424117cb534ce03497c41305ed868980123917b2b6abba4bbaa615e968772903` |
| 原出版者的 ft-mse 产品 | `stabilityai/sd-vae-ft-mse` / `31f26fdeee1355a5c34592e401dd41e45d25a493` | 547 B / `92d3dfb746fca211a2c9e019e285f8597412211728dce3c5bcf4eda0f2d62e7e` |

两份 metadata 的 `diffusion_pytorch_model.safetensors` 条目均为 334,643,276 B，LFS SHA256 为 `a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815`，Git blobId 为 `90464d67ac7303d0ee4696334df13da130a948ea`。LFS 条目的 Git blob 标识对应 LFS 指针对象，不能把它说成已下载权重的完整本机 SHA 校验。当前已核的是服务端声明的同一对象身份，权重正文尚未读取。

独立重算两配置的 Git blob SHA1，分别为 `9421ac5a7caf02657fa559cffe7c73a47572cd64` 和 `0db26717579be63eb0ddbf15b43faa43700dfe5a`，与各自 metadata 一致；四正文大小/SHA均与回执一致。不是只比较文件名。来源：[社区 metadata](https://huggingface.co/api/models/sd2-community/stable-diffusion-2-1-base?blobs=true)、[官方 ft-mse metadata](https://huggingface.co/api/models/stabilityai/sd-vae-ft-mse?blobs=true)、[社区固定配置](https://huggingface.co/sd2-community/stable-diffusion-2-1-base/raw/4e63672c03103b6c636b8fb4119ba982469b2955/vae/config.json)、[官方固定配置](https://huggingface.co/stabilityai/sd-vae-ft-mse/raw/31f26fdeee1355a5c34592e401dd41e45d25a493/config.json)；本轮依据是 [本地原回执与正文](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S36_resource_recovery/vae>)。

## 2. 两个配置差异怎样进入源码

逐字段比较仅两项不同：社区 `_diffusers_version=0.10.0.dev0`、`sample_size=768`；官方 ft-mse 分别为 `0.4.2`、`256`。两配置原字节不同，不能称配置身份相同。

- 在本机 `ConfigMixin.extract_init_dict` 中，下划线开头的私有项从构造实参移除；`_diffusers_version` 是可保留的历史元数据，不会自动切换到旧版本 Diffusers 执行。这里实际源码是已安装的 0.32.2。
- `AutoencoderKL.__init__` 不把 `sample_size` 传入 Encoder、Decoder、quant_conv 或 post_quant_conv。它只据此设 `tile_sample_min_size` 和 `tile_latent_min_size`；四层结构的后者分别为 768/8=96、256/8=32。
- `use_tiling` 和 `use_slicing` 默认 false。`_encode/_decode` 只有在 `use_tiling` 为 true 且输入空间尺寸超过阈值时才走空间切块；非分块分支没有 `sample_size` 驱动的 resize、裁剪或硬尺寸限制。
- 原 VMem `AutoEncoder` 没有开启 tiling。其 `chunk_size=1` 是逐批次分割，不是空间切块；encode 使用后验均值乘固定 0.18215，decode 先除该值。两份配置差异不会改这些原 wrapper 选择。

**条件性源码推断**：若以后加载的是相同已验证权重、相同其他构造参数/库版本/精度/设备/attention 路径，且保持 `use_tiling=false`，这两个配置差异不会改变这里原 encode/decode 的计算路径。该结论不是已经加载成功、逐位输出相等或原模型生成通过的实测证明。

如果以后开启空间 tiling，结论就不同：原生成尺寸 576 对应 latent 72，256/32 配置会触发分块，768/96 配置不会。拼接/重叠混合引入不同计算路径；不能笼统说 `sample_size` 永远无效，也不能为省内存偷偷启用它。上述576/72阈值判断仅是源码整数关系，未创建张量。

源码定位：[AutoencoderKL 初始化与 tiling](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_environment/site-packages/diffusers/models/autoencoders/autoencoder_kl.py:101>)、[encode/decode 分支](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_environment/site-packages/diffusers/models/autoencoders/autoencoder_kl.py:250>)、[私有配置字段过滤](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_environment/site-packages/diffusers/configuration_utils.py:511>)、[from_config 构造](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_environment/site-packages/diffusers/configuration_utils.py:248>)、[low_cpu_mem_usage=false 加载分支](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_environment/site-packages/diffusers/models/modeling_utils.py:983>)、[原 VMem VAE wrapper](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S20_environment/isolated_vmem_source/modeling/modules/autoencoder.py:6>)。

## 3. 可接受的候选与尚未连通的来源链

可以记录为：**“官方 ft-mse 固定对象与社区 SD2.1 VAE 的参数 metadata 同一；在当前原非分块 wrapper 下具有相同有效架构的候选。”** 官方 ft-mse 是原出版者的另一个具名产品；社区配置仍是社区来源。组合它们也必须保留两条来源和不同配置身份，不能统一改名为原 SD2.1。

当前关系是 `社区 VAE ⇄ 官方 ft-mse`；缺失的是 `原 stabilityai/stable-diffusion-2-1-base/vae → 这一权重和原配置`。原 VMem 调用未 pin revision，故仅看到社区模型名称或官方 ft-mse 属于 stabilityai 均不足以补上这条边。metadata 和读取到的配置没有提供原出版者迁移/等价声明。此前 [S20入口报告](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S20_DEPENDENCY_ACCESS.md>) 的未知原 revision/config/weight 状态仍成立；旧401与TLS记录均保留，不能由本次不同仓库200推断原入口恢复。

最小缺口是能绑定原 SD2.1-base VAE 的可信历史清单/文件身份或明确原出版者迁移/等价证据，同时包括原配置。若将来取得这种证据并且实际参数内容、完整加载与既定执行门都通过，才可提出原件恢复验收。源码兼容性或数值相近测试本身不能证明历史来源。

若项目以后选择先评价这个替代候选，应另立透明的“ft-mse/社区配置替代基线”合同并固定所有来源；它可以产生替代基线证据，仍不计为本项目目前要求的严格原件复现。本轮不下载、不创建该实验、不改变 S35 gate/manifest，也不填写 `VERIFIED_ORIGINAL_VAE_IDENTITY`。
