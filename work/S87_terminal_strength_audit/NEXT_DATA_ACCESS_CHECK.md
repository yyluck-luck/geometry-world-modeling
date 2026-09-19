# PointOdyssey v1.2：小片段访问核查

**结论：尚未找到可单独获取、具有明确同刻多视角对应的小片段，停止本批。** 作者 Hugging Face 当前递归文件列表仅含整包；最小数据包是 3,324,284,510 B 的 `sample.tar.gz`。这只证明该入口的最小可见数据项，不证明所有官方渠道必须下载此包：作者 Google Drive 链接本次仅返回 302，目的页面未读取。没有下载任何图像、NPZ、数据归档或模型，也未运行科学评分。

本批开始钟 UTC 2026-09-10 23:55:15；三次实际 HTTP 请求在 23:55:45.969474–23:56:21.924417 完成；23:56:53 封存元数据清单（北京时间次日07:55–07:56）。使用 `/usr/bin/curl`，每请求连接10秒/总30秒/响应最多1 MiB，未重试、未自动跟随重定向。只有3个请求，共保存16,674 B正文；头部、原正文、起止时间、状态和SHA均在 [访问回执目录](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S87_terminal_strength_audit/pointodyssey_access_01/MANIFEST.json>)。元数据中的链接没有继续请求。

## 实际请求与版本

| 请求 | HTTP / 正文字节 | 确认内容 |
|---|---|---|
| [1. 官方 GitHub README 原文](https://raw.githubusercontent.com/y-zheng18/point_odyssey/main/README.md) | 200 / 9,785 B | release 2024-02-21：v1.2 修复更多 mask/depth 错误，159视频，131 train / 15 val / 13 test。文件来自当时 main，未另查 commit；正文SHA `f8bb2457a46f5121efa880437c0654ea85d8e6f89c03a550db38a95db096cbfd`。 |
| [2. 作者 HF 递归文件 API](https://huggingface.co/api/datasets/aharley/pointodyssey/tree/main?recursive=true&expand=true) | 200 / 6,889 B | 返回9个文件、0目录，响应无续页 Link。归档的 lastCommit 为 `3e6f11c3ebc49255d66c546d0e6bef772d63beed`（2024-02-22）；README 为 `4a2ec9492ca732dc3611adbb2a94248cc2bbe3eb`。API正文SHA `97822414bb982f696dfcfef60c79db1aed7ed9fc994eff2babe5685f608ad5fe`。 |
| [3. README 指向的官方 Drive v1.2 文件夹](https://drive.google.com/drive/u/1/folders/1W6wxsbKbTdtV8-2TwToqa_QgLqRY3ft0) | 302 / 0 B | Location 指向同ID的 `/drive/folders/…` 公共路径。没有访问目的页；不能把重定向说成拒绝访问，也不能说已读到其中序列。 |

HF 的实际可见文件是 `.gitattributes`（2,307 B）、`README.md`（129 B），以及：

| 数据项 | API 标明的实际对象字节数 |
|---|---:|
| `sample.tar.gz` | 3,324,284,510 |
| `test.tar.gz` | 26,521,309,703 |
| `val.tar.gz` | 20,399,261,433 |
| `train.tar.gz.partaa` / `partab` / `partac` | 各34,359,738,368 |
| `train.tar.gz.partad` | 31,254,171,521 |

API还提供各归档的 LFS对象标识，已留原正文；这是服务器宣告的元数据，**不是本机下载后校验成功**。上述9项总大小184,578,244,707 B；不含解压膨胀估计。没有单独 `sequence/`、逐帧文件、索引清单或可见同步表。

## 同步、划分和许可：能说什么

1. **具体 sequence / 时间对应仍 UNKNOWN。** 本次 README 的多视角段落说明如何自行渲染3视角或静态室内多视角，没有列出已发布哪几个序列互相同步、各视角帧号如何对应。旧批已读[官方项目](https://pointodyssey.com/)仅称部分场景有同步视角，本次未再访问。README 的 `recording_20210918_S05_S06_01` 是动作转换示例；前批 `reprojection.py` 的 `train/dancing` 是投影示例，均不能证明 sample/test 中存在所需同步对。渲染功能不等于该数据已发布成可取小片段。
2. **只确认视频数划分，不确认场景独立性。** 131/15/13 是 train/val/test 视频数；同场景可有多个视频，不能当159个独立场景。没有读取包内名单，sample 属何划分、同步视角是否跨划分、是否与当前模型训练重合均未核。
3. **数据条款应先看明确指向数据的声明。** 本次官方 README 的 Download 段明确把 full dataset 指向 **CC BY-NC-SA 4.0**；这是目前范围最直接的数据许可文字，不能用代码许可自动替换。前批实际读过的作者 HF 129 B README 却写 MIT，本次API确认其文件身份/大小，未重新获取内容。两处冲突保留；归档内是否另有 LICENSE 未核，不能宣称数据已确定可按 MIT 使用，也不替作者作法律裁定。

**下一决定所需最小信息：** 一个明确的 v1.2 序列ID及其 train/val/test归属、同一模拟时刻的视角ID/帧号映射、包含对应 RGB/K/RT/标签的有界获取方式，以及明确数据许可。如果官方只能提供当前整包，后续是否为这些信息获取3.32 GB应由root结合资源和任务价值决定；本批没有读取包头、Range试取、跟进Drive或第三方镜像。即使补齐，它仍是模拟数据，不能泛化为精确真机同步 RGB-D 已落实。当前状态保持 **SMALL_SYNCHRONIZED_CLIP_ACCESS_UNVERIFIED**。
