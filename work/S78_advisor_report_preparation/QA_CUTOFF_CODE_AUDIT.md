# 官方QA源码审查：该演示不使用视频，也不消费cutoff映射

记录日期：2026-09-10。源码实际取得于北京时间23:00:03.352222–23:00:26.089524；本文件随后依据实际代码整理。

**结论：这份官方多选QA notebook不能解决cutoff帧是否包含的问题。它演示的是答案频率基线，主路径生成全零“帧”占位，然后直接丢弃frames参数；没有读取cut-frame映射，也没有以ffmpeg参数或数组切片实现前缀截断。** 这是定点源码发现，不是数据实验，不构成对整个官方评测协议的否定。

## 实际获取与阅读边界

- 来源：[固定commit的官方QA notebook](https://raw.githubusercontent.com/google-deepmind/perception_test/3938d2f1ba3a6b502025741cea4cd73c7b3bdfaf/baselines/mc_vqa.ipynb)，commit `3938d2f1ba3a6b502025741cea4cd73c7b3bdfaf`。
- 获取时间：2026-09-10T15:00:03.352222至15:00:26.089524 UTC；一次curl成功，returncode 0。未使用第二种获取途径。
- 实际文件大小：**21,425,832字节**；SHA256 `18704c69621515d38c93cb32ddfa3d42375ce34cf6a2618192adb29f426076a8`。前批网页工具对动态main路径报告的16,159,945字节不是本次固定版本文件的实际大小；保留两条来源，不混写。
- 本地原件：`qa_cutoff_code_audit/mc_vqa.ipynb`；精确回执：`qa_cutoff_code_audit/FETCH_RECEIPT.json`。
- 从JSON中只提取了**16个代码单元**，存为 `code_cells.json` 和 `code_cells.txt`。没有执行任何代码单元，没有解码/渲染内嵌媒体，没有查看输出单元，也没有下载或读取任何真实样例答案。JSON解析仅用于提取source；原notebook字节包含作者已有输出，因此不声称“原件没有输出字节”。

## 映射在代码里怎样被消费

**在所核版本的这条QA演示路径里，没有消费。** 对全部16个代码单元作大小写不敏感的定点搜索，`cut_frame`、`cut_frames`、`cutoff`、`cut_frame_mapping`、`ffmpeg`、`.subclip`、`trim`均无命中；再检查读帧、Dataset、模型与评测调用，逻辑如下。行号指提取后的 `code_cells.txt`，notebook单元编号是原JSON `cells`数组的零基编号。

| 源码位置 | 实际逻辑 | 能推出什么 |
|---|---|---|
| cell 7，151–181行 | 定义sample及train/valid QA标注下载；注释解释频率基线无需validation视频；没有定义或加载切帧映射。 | 该演示不是合法前缀构造例。下载调用仅被阅读，本次未执行。 |
| cell 10，241–259行 | `load_dataset` 按metadata split和任务存在性选择条目。 | 只做任务/split筛选，不建立时间边界。 |
| cell 10，290–300行 | `__getitem__` 以metadata总帧数生成形状为 `(num_frames,1,1,1)` 的全零数组；真正的读视频调用处于注释里。 | 活跃评测路径没有真实视觉输入，也没有视频尾段截断。 |
| cell 13，511–564行 | `answer_q` 明确删除未使用的frames变量，基于训练答案频率选择选项。 | 不能把它当作会使用旧图片的状态记忆消费者。训练集标签统计本身是该基线定义，不称作测试泄漏。 |
| cell 14，568–603行 | validation Dataset、training频率模型，调用 `answer_q`，最后用validation标签计算分数。 | source中模型输入和评分标签的角色可区分；本次未读任何具体答案或运行评分。 |
| cell 6，101–149行 | 未启用的读帧辅助函数从VideoCapture读取直到结束，按总帧数建立数组并校验；其唯一相关数组下标是逐帧写入 `vid_frames[idx]`。 | 即使未来直接启用这个辅助函数，也没有已实现的cutoff前缀。没有可报告的ffmpeg截断参数或类似 `frames[:c]` 的实际操作。 |

以上均来自[官方固定版本源码](https://github.com/google-deepmind/perception_test/blob/3938d2f1ba3a6b502025741cea4cd73c7b3bdfaf/baselines/mc_vqa.ipynb)。没有推断未阅读文件也遵循相同逻辑。

## cutoff、start与end分别还剩什么问题

前批README已确认train/valid有切帧映射，用于排除揭示答案的尾段。本次源码没有提供该映射值c对应“最后保留帧”还是“第一排除帧”的新证据。因此无法核实 `[0,c]` 或 `[0,c)` 哪一个是官方语义，也不能凭通用数组习惯选择。

该QA Dataset也没有把对象跟踪初始化时间、动作start/end与QA截止时间关联起来。对象第一次有效跟踪框和动作结束帧都不能替代QA cutoff。即使以后找到明确切片代码，仍要核查一个实际样例的split、video_id、时间/帧索引、初始化位置及答案隔离；**loader边界本身不等于样例已经完整合法。**

## 对当前科研的具体决定

给零基础的解释：我们本来想看“官方怎样在答案出现前关掉视频”。现在确认这份程序根本不看视频，它只统计某类问题过去最常见的答案。因此，它不能告诉我们应在哪一帧关掉视频，也不能验证系统是否记住了球所在的杯子。

保留对象身份＋容器状态跟踪作为下一项简单对照；不把这个频率演示升级成视觉强基线。当前没有取得可执行的官方cutoff语义证据，状态仍是 `CUTOFF_ENDPOINT_NOT_ESTABLISHED`。本批完成后停止继续网络获取；不猜边界、不重试sample下载、不改主实验或选择新方法。

下一项真正缺少的证据仍是明确的官方切帧实现或端点说明，以及实际样例的时间字段关联。前批小于1MB只是当时的人为阅读预算，本批已经解除并实际取得完整源码；当前未解决的是**所读程序没有相关逻辑**，不是文件大小或下载仍失败。
