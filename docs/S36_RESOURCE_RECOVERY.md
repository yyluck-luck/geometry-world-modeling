# S36：原模型资源来源核验

**本轮找到了一条可核实的 VAE 候选线索，但原完整生成仍不能启动。** 原 VMem 没有找到新的正式公开权重入口；VAE 的社区副本与官方另一产品公布相同参数指纹，但尚未证实它就是原 SD2.1 仓库发布的那一份。没有下载权重、运行模型、重复S35人工检查或新增精度结果。

本轮是资源来源调查，不能按一次算法实验或创新结果计数。root和两名agent分别核本地/候选来源、VMem作者公开渠道、VAE配置及加载源码。实际请求、原始小响应与独立核验在[本轮证据目录](../work/S36_resource_recovery/)，时间追加至[研究主账](../RESEARCH_LOG.md)。

## 原 VMem：新渠道没有解除缺件

实际读取作者仓库公开的16个issue、1个PR、20条评论、仓库功能、实时Releases页面及原HF模型社区。新来源没有给出可核为原权重的下载或迁移地址；当前Releases页面确为空，补上了上轮该接口TLS失败留下的不确定性。作者2025年的代跑样例提议不是权重下载入口，本轮没有联系作者。[VMem路线报告](../work/S36_resource_recovery/vmem_route.md)；[作者仓库](https://github.com/runjiali-rl/vmem)；[Releases](https://github.com/runjiali-rl/vmem/releases)。

这一分工用了3次限定检索和5次直接HTTP请求，后者全200、正文275331字节，实际UTC 2026-09-06 **23:55:58.938782–23:56:55.844200**。没有重复S34的六个URL或尝试获取受限权重正文。公开元数据可读不代表当前账号可下载模型。

## VAE：确认了两仓库的关系，原来源仍有断点

4次新的直接HTTP请求全200，共11387字节。两个元数据请求在UTC 2026-09-07 **00:00:23–00:00:24**；两个固定版本配置在 **00:01:13–00:01:14**，即北京时间08:00–08:01。[请求汇总](../work/S36_resource_recovery/vae_summary.json)。

| 已核对象 | 社区SD2.1-base候选 | Stability官方ft-mse产品 |
|---|---|---|
| 仓库 | `sd2-community/stable-diffusion-2-1-base` | `stabilityai/sd-vae-ft-mse` |
| 固定revision | `4e63672c03103b6c636b8fb4119ba982469b2955` | `31f26fdeee1355a5c34592e401dd41e45d25a493` |
| 发布的VAE参数大小 | 334643276字节 | 334643276字节 |
| 发布的LFS SHA256 | `a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815` | 相同 |
| 实际取得的配置大小 | 553字节 | 547字节 |
| `sample_size` | 768 | 256 |
| `_diffusers_version` | `0.10.0.dev0` | `0.4.2` |

两份参数条目的LFS指针身份也相同；两份配置原字节不同，各自Git blob和实际文件大小/SHA都核对成功。**参数指纹来自服务端元数据，没有读取完整334MB参数，不能说已完成本机权重校验。** 原始来源：[社区元数据](https://huggingface.co/api/models/sd2-community/stable-diffusion-2-1-base?blobs=true)、[官方ft-mse元数据](https://huggingface.co/api/models/stabilityai/sd-vae-ft-mse?blobs=true)。

另一作者独立核对小响应、配置与本机Diffusers 0.32.2源码后确认：两个配置仅上述两字段不同。原VMem没有开启空间分块，`sample_size`在这个分支只设置未使用的分块阈值。因此，在相同权重、其他参数、库、设备、精度和非分块条件下，可以从源码推断有效算子结构相同；**本轮没有实测加载或输出相等**。

如果以后为了省内存开启空间分块，576像素输入会使256阈值配置走分块，而768阈值配置不走，不能笼统称配置差异无效。这个限制需要保留到将来的实验合同。[独立配置与源码审阅](../work/S36_resource_recovery/vae_relation_review.md)；[独立回执](../work/S36_resource_recovery/vae_relation_review_receipt.json)。

现在确认的是“社区候选 ↔ 官方ft-mse”；还缺“原 `stabilityai/stable-diffusion-2-1-base/vae` → 上述参数与原配置”的可信来源链。社区名称、复制的模型说明、参数兼容和数值接近都不能单独证明历史来源。因此保持S35资源门及原实验草稿不变，没有填写原VAE身份已确认。以后若采用替代VAE，需要独立标注的替代基线，不能回填为严格原复现。

## 本机状态和电脑访问

限定项目、原VMem checkout及已记录模型缓存的文件名/元数据检查，没有发现本轮新增的已验收VMem/VAE/完整CLIP；已有CUT3R完整文件与旧partial的大小/mtime仍同前次，本轮没有重复读取3GB权重。范围不包括全电脑所有文件。

初次进程子串筛选误包含系统sync服务，已改为可执行文件名精确匹配；第一次S20缓存路径写成`hf_cache`，已补查实际的`huggingface-cache`目录。两份初始回执均保留，这些纠正不属于模型实验失败。[初始元数据检查](../work/S36_resource_recovery/local_delta.json)；[进程纠正](../work/S36_resource_recovery/process_delta_corrected.json)；[实际缓存与原checkout补查](../work/S36_resource_recovery/local_delta_supplement.json)。

尝试通过电脑工具检查原HF模型页面时，工具明确报告Mac锁屏且自动解锁失败。没有获取浏览器内容，现有账号是否已经有访问权限仍未知；没有读取token、登录或提交资料。

## 下一步与记录

1. 电脑解锁后，可检查浏览器已有的原模型访问权限。若页面要求额外申请或提交个人资料，保留该事实，不自动代提交。
2. 原VMem文件可取得且VAE原来源链补齐后，再统一获取缺少的原CLIP，冻结真实原组件身份，执行已有S20两批协议。完整CPU耗时和内存仍未知。
3. 若没有新的资源、来源或账号访问证据，本次检索到此结束；不重复网站搜索、S35人工检查或短窗调参来填充“持续科研”。S34真实结果与S35完整交付继续有效，最终创新和完整视频目标尚未完成。

本轮9次可计量直接HTTP请求全200，正文合计286718字节；另有7个检索查询和网页工具页面阅读，其后台流量/HTTP状态不由工具暴露，不合并冒称精确总网络字节。根任务4条检索与页面用途另记[来源索引](../work/S36_resource_recovery/vae_web_source_index.json)。未再次探测原VAE失败入口，不用不同仓库的200推断原入口恢复。

本轮继续应用Supervisor第2章的基线优先及本地Claude科学批判的来源/运行证据分层。最近恢复实查UTC **2026-09-06 23:56:56.421978**，实际距前次33.797773分钟，已超过30分钟；触发本身晚42.17秒，恢复核查另耗时，均如实留账，没有追认准点。定时频率和实际完成时刻是两回事。
