# S100：条件于其他记忆的收益——原文与代码创新审查

开始时钟：2026-09-14T06:48:52Z（北京时间14:48:52）。写稿依据时钟：2026-09-14T06:51:24Z（北京时间14:51:24）；这是本轮工具时刻，不是学生工时。

结论：**“单条记忆的价值取决于其余记忆”已有直接先例，不能作为本项目独立创新。** 当前值得完成的是固定预算、幅度匹配下的真实几何消费者诊断，判断 S99 的排序失败是否涉及上下文依赖。`new_method_validated=false`，`novelty_authorization=NONE`。

已读项目 AGENTS、RESEARCH_PRINCIPLES、RESEARCH_MEMORY 最新状态、RESEARCH_LOG 最新条目及 S99 RESULTS/NEXT_MECHANISM_HYPOTHESIS。局部应用 `/Users/rocket/.codex/skills/idea-evaluator/SKILL.md` 与 `references/fatal-flaws.md` 的 F1 原文近邻审查、F6 可检验性及已被数据反驳机制停止规则；不把这次有边界审查冒充完整评分或系统综述。不改主实验与研究主账，交 root 汇总。

## 1. 先分清三个对象

设 C 是共同背景，a、b 是可互换候选，L 是在固定评分规则下由完整消费者得到的误差。

- **内在低风险**：r(b)，例如历史几何不一致度小。它既没有减去旧状态误差，也不一定使用其他已选块。
- **条件增量收益**：B(b | C) = L(C) − L(C ∪ {b})。正数才表示加 b 有益；若预算要求不能少一块，则只把这个式子用作定义解释。
- **固定预算替换收益**：D(a→b | C) = L(C ∪ {a}) − L(C ∪ {b})。这是 S100 可直接比较的对象，两边预算相同。

同一候选在不同 C 中收益改变，才是上下文依赖。低 r(b) 不能推出 B(b | C)>0；分布变化幅度、MI 或自报 helpfulness 也不能自动解释为对独立真值的有符号收益。未来真值只能用于预测封存后的评分，不能成为部署时选择输入。

## 2. 三个最接近的工作

### GIM-World：已有世界记忆中的集合条件信息选择

Zhengxuan Wei、Xu Guo 等，2026，*Geometry-Aware Implicit Memory for Video World Models*。本轮实际读到[原论文 §3.2–3.4，Eq.15–18](https://arxiv.org/html/2606.02436v1#S3.SS4)，并由[作者项目页](https://gim-world.github.io/)确认官方代码入口；不是仅凭搜索摘要。

方法证据：保留集合 S 与丢弃历史之间的互信息是目标，贪心候选分数使用条件于当前 S 和其补集的 GP 方差之比。核输入为相机位置、朝向及时间。这已覆盖“固定容量下考虑已选记忆的冗余再选下一项”。它估计的是历史表示的信息代理，并未在该选择式中使用一次块替换所造成的未来真值损失差；论文中的几何监督与选择分数也不能混为一体。

代码证据：[固定版本 pruning.py](https://github.com/nagara214/GIM-World/blob/6d9b2090569e7d450d3baedc09ff82f662ad9ea2/gim/utils/pruning.py) 的 `_greedy_mi` 每轮更新已选集合 Cholesky 与剩余集合逆矩阵，重新求 `var_s/var_r`，并默认锚定首尾帧。已全文读本地固定副本并复核 SHA 与旧来源记录一致。**没有运行其世界模型，没有验证论文性能或全局核保证。** 本輪在线固定文件刷新出现 TLS EOF，不能说成功重新下载；原文和官方仓库页面可访问。

四轴差别：对象=历史帧；机制=GP 条件信息代理；粒度=帧；设置=视频世界模型。S100 是历史预测块的固定预算替换与几何消费诊断，尚不能因这些差别直接获得贡献资格。

### CUE-R：有符号干预及多证据交互均有先例

Siddharth Jain、Venkat Narayan Vedam，2026，*CUE-R: Beyond the Final Answer in Retrieval-Augmented Generation*。已读[原文 §3.3 Eq.7、§5.5、§6.8、§7](https://arxiv.org/html/2604.05467v1)。

方法证据：REMOVE、REPLACE、DUPLICATE 后重跑回答，报告相对原始回答的正确性、grounding 代理和置信误差差值；另外单列行为轨迹变化。两支持消融比较单独删除及共同删除。论文明确承认提示长度、内容分布和注意力共同变化，其实验只解释为操作层面的干预敏感性。

本审查的数学提醒：`joint drop > max(single drops)` 本身不能证明非加性；两个正的可加效应也满足它。应比较同一评价域的二阶差分，或固定候选对跨背景的替换收益变化。这个提醒是我们对判据的推导，不是作者验证结论。文中双支持无损、共同删除有损的个例则确实给出另一类上下文依赖证据。

四轴差别：对象=文本证据；机制=输入证据干预与结果差；粒度=chunk；设置=单次 RAG 问答。与 S100 相似的是有符号替换效果，区别在预算控制、几何遮挡消费者和独立深度评分。未找到并读取该工作的官方执行代码，**证据等级仅原论文正文，不称代码复现**。

### Utility-Oriented Visual Evidence Selection：utility 命名与单项代理并不新

Weiqing Luo、Zongye Hu 等，2026，*Utility-Oriented Visual Evidence Selection for Multimodal Retrieval-Augmented Generation*。已读[原文 §3–4 和 Appendix C](https://arxiv.org/html/2605.13277v1)，并从正文进入[作者代码仓库](https://github.com/Hcnaeg/utility-mrag)。

方法证据：原始目标是单个候选引起的回答分布 KL 变化；在非有害候选与单调混合等假设下联系 latent helpfulness，定理的最优性说明限 K=1。实际管线逐图计算 True-token logit，然后选 top-k。KL 非负，不等于对真值误差的有符号改善；也不能把 K=1 论证扩大成存在交互时的最优集合保证。

代码证据：`SurrogateSelector.score_example` 逐候选调用 `score_one`；该函数接收问题和单个候选，MRAG 时额外接收题目图片，没有当前已选证据集合 C；`select_top_k` 只按已存 score 排序切片。因此这里的“以效用替代相关性”与代理提速已被覆盖，但主选择实现不是每加入一项就条件于 C 重算的策略。只做源码阅读，未加载模型或复现精度。

四轴差别：对象=候选图像；机制=单图 helpfulness 代理排序；粒度=整图；设置=多模态问答。S100 的块替换诊断尚不是与它同任务的竞争方法。

## 3. 最强新颖性威胁与当前判定

最直接的**同领域机制威胁是 GIM-World**：它已经让选择分数依赖已选集合。最直接的**估计对象威胁是 CUE-R**：它已有逐证据有符号干预结果及多证据交互。第三篇进一步排除仅把风险评分改名为 utility、再用轻量代理排序的宽泛创新叙事。三个已有部件的组合也不会自动变成新方法。

对 S99 已被普通 confidence_gain 超过的“低不一致度优先就更有效”主张，按已冻结标准 **Reject and Pivot**；不能换尾部指标来救回原主张。对尚未运行的 S100 上下文机制问题，不套用“已被反驳”：允许把它作为诊断完成。这里不对整项 GRC、所有场景或投稿水平作否决，也不授予新颖性。

## 4. 一个可被推翻的机制问题

**在只用历史信息挑定的同源、改变量匹配候选对中，替换收益的正负是否仍随固定预算背景 C 改变，而且变化不能由评价域变化解释？**

最便宜检验：同一 (a,b) 在多个预先规定、均不含 a/b 的 155 块背景下，比较两套 156 块状态；每次完整重算投影、遮挡与来源身份。先封存候选、匹配失败、种子、缺失值规则和全部预测，再读取已见未来深度。固定一个可跨背景比较的全GT评分规则，并同时报告 coverage、尾部和来源竞争变化；可补共同有效域但必须报告其分母，不能让各条件自选更容易的像素。

若同一对的 D 在数值/重放容差外跨背景反号，支持该开发场景的条件依赖，**不证明找到通用选择器，也不把来源改变本身当正确率收益**。若反号仅来自域变化或匹配失效，机制解释不成立。若各背景差值均落在预先冻结容差内，停止这一轮的“背景交互可分辨”主张。若仅幅度控制就使差异消失，保留幅度解释，不训练忽略 C 的收益模型补故事。覆盖有限背景时，没有反号不能证明一般上下文无关。

本问题的新实验价值在于缩小本项目失败原因；非加性与上下文依赖的概念本身不是创新。下一方法要另证历史可计算代理能够预测该效应，并在真实记忆预算、未见场景及完整生成消费者上超过强基线。

## 5. 访问和代码可追溯记录

英文搜索词：`GIM-World memory subset selection`；`CUE-R evidence utility`；`Utility-Oriented Visual Evidence Selection`。本轮是三篇定向近邻检查，不是全面“无重复”检索。搜索摘要仅用于定位，方法事实以以上正文与代码为准；作者仓库上的会议标签不在本审查中当成已独立核实的录用状态。

| 已读代码 | 固定版本 | 本轮正文 SHA256 |
|---|---|---|
| GIM `gim/utils/pruning.py`（本地固定副本） | `6d9b2090569e7d450d3baedc09ff82f662ad9ea2` | `32add87f697c748c0f005e3d79107b6b639895f0f7f39ee97f21b8cd03806ce3` |
| utility `utility_mrag/selection/surrogate_selector.py` | `d5b9e573ece689dc1293220f659c6c1b0f1a5d16` | `416c4463e681aa5ce36c3cd8a51160ce23e94c5b5389a2fc51d22ac381d607f2` |
| utility `utility_mrag/selection/topk.py` | 同上 | `c9aa17a201f109534f1565541829554117f319e83fbd263661c64655af4a5e06` |
| utility `utility_mrag/scoring/helpfulness_score.py` | 同上 | `d3e1fa16374db2aaae6ba982c3ee57cffad8f684a4cf1e0f9f8a2a0f4fd5b417` |

utility 正文通过 GitHub API `repos/Hcnaeg/utility-mrag/contents/<path>?ref=<commit>` 实际取回并读完，上表是解码后文件字节的 SHA。首次 raw.githubusercontent.com 请求 TLS EOF，之后 API 成功取回三份 utility 文件；GIM API 刷新仍失败。GIM 本地副本位于 `work/S96_gim_saved_pose_audit/vendor/pruning.py`，既有来源时间记录在同目录 SOURCE_MANIFEST，未把旧获取时间改写为本轮。

本轮新增神经推理=0，视频生成=0，大模型下载=0，数值实验=0。研究结论不依赖 toy quickstart，也没有运行它。

完成核验时钟：2026-09-14T06:53:10Z（北京时间14:53:10）。文件存在且非空，`git diff --check` 未报告空白错误；这只是交付文件检查，不是科学结果验收。
