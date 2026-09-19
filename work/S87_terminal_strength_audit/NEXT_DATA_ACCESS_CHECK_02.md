# PointOdyssey 第二批访问：Drive 已核，具体同步小片段仍未知

**结论：未定位到可单独取得、具明确相机/同刻帧号对应的小片段，本批停止。** 新证据补齐了官方 Drive 重定向目的页：页面显示8个归档项，仍不是逐序列/逐帧入口。官方仓库还存在直接询问同步视角名单的未回复问题，但用户提问不能证明数据里不存在同步视角。没有新的作者说明足以把某个具体 sequence 确认为可用。

先读 `NEXT_SCIENTIFIC_DECISION.md`、`NEXT_DATA_ACCESS_CHECK.md` 与上一批302回执；本轮开始钟为 UTC 2026-09-11 00:03:19（北京时间08:03:19）。**恰3次官方请求，2次HTTP200、1次TLS失败；没有重试或继续搜索。** 每请求连接10秒、总30秒、响应上限1 MiB；不自动跟随重定向。下载内容仅为网页HTML/仓库issue元数据，共489,073 B，不含任何数据包、图像请求或NPZ；未渲染网页图片、执行模型或重跑S73–S87。所有写入限本文件与 `pointodyssey_access_02/`。

| 请求与实际范围 | UTC起止 | 结果 |
|---|---|---|
| [1. 已观察到的官方Drive目的页](https://drive.google.com/drive/folders/1W6wxsbKbTdtV8-2TwToqa_QgLqRY3ft0)；只解析页面文字/文件ID，不请求资源或下载按钮 | 00:03:54.782710–00:03:56.645853 | HTTP200，373,874 B；正文SHA `b2d12a274b089d2b6b4da80274568933728240b275427089102e0fa94e084ac6` |
| [2. 官方仓库issue列表API](https://api.github.com/repos/y-zheng18/point_odyssey/issues?state=all&per_page=100)；29项（含PR）、响应无续页Link，定向读同步/数据释放问题 | 00:04:17.026529–00:04:18.534251 | HTTP200，115,199 B；正文SHA `3f2e20aaed70ec304c4731cddcbdd3e539a20b201c96680f41d6a7770a84a58d` |
| [3. #10实际链接到的#7场景释放评论](https://api.github.com/repos/y-zheng18/point_odyssey/issues/7/comments) | 00:04:37.582441–00:04:38.002844 | 没有HTTP响应（curl状态000、返回35），0 B；`LibreSSL SSL_connect: SSL_ERROR_SYSCALL`。评论未读，不推断作者答复 |

## 获得的具体入口，以及仍然缺什么

Drive页面标题为 `point_odyssey_v1.2`，显示 `sample.tar.gz`、`test.tar.gz`、`train.tar.gz`、四个 `train.tar.gz.part*`、`val.tar.gz`。sample ID为 `1dnl9XMImdwKX2KcZCTuVDhcy5h8qzQIO`，test ID为 `1jn8l28BBNw9f9wYFmd5WOCERH48-GsgB`。页面将sample显示为 **3.1 GB**、test为 **24.7 GB**；这只是UI显示，不替代前批HF精确大小（分别3,324,284,510 B与26,521,309,703 B），也未证明两平台同名文件字节相同。Drive还显示完整train为125.11 GB。没有可见sequence子文件夹、同步清单或相机/时间索引小文件；未进入归档预览、读取包头或做Range取样。

[仓库问题 #23](https://github.com/y-zheng18/point_odyssey/issues/23)于2025-04-19询问具体哪些场景同步，并称提问者下载sample后未找到同步元数据。本次API显示它仍open、comments=0，作者关联为NONE。**只把它当未得到作者回答的相同缺项，不采用其个人下载经历认证数据内容。** [#10](https://github.com/y-zheng18/point_odyssey/issues/10)也是用户询问多视角释放，comments=0；[#24](https://github.com/y-zheng18/point_odyssey/issues/24)询问原始场景释放，也无评论。#7虽有2条评论，但本次获取失败，不能当作已读作者说明。

v1.2的131 train / 15 val / 13 test视频数仍只依据上一批官方README；本次没有得到具体sequence归属或跨视角同帧映射。训练场景重合、sample划分、独立测试资格均UNKNOWN。数据专项README的CC BY-NC-SA 4.0与作者HF卡MIT冲突未解决，未读取归档内许可；**本批不转发数据、不将代码许可视为数据再分发许可**。

**停止条件已满足。** 两个已核官方分发入口都没有暴露所需的小片段/索引；不能为取得一个编号继续盲目下载大包。恢复此方向所需证据仍是：具体v1.2 sequence及划分、同步视角ID与同一模拟时刻的帧号映射、可有界获取的RGB/K/RT/标签文件以及明确数据条款。本次没有这些证据，因此状态仍为 **SMALL_SYNCHRONIZED_CLIP_ACCESS_UNVERIFIED**。这不否定PointOdyssey的研究价值，也不证明同步数据不存在；更不能说真实相机传感数据已经落实。当前S87主量、已接受结果和下一机制判断均不因本次访问改变。

原始小响应、HTTP头、逐请求回执、Drive文字投影及相关issue字段见 [MANIFEST](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S87_terminal_strength_audit/pointodyssey_access_02/MANIFEST.json>)；其中完整正文保留原字节，展示用投影不冒充作者schema。旧批证据未覆盖或修改。
