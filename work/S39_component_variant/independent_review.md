# S39 不同作者源码前审

**最终 PASS_S39_SOURCE_REVIEW，限定源码前审。** 初审 ISSUE_PENDING 的问题已由 v2 最小修复；候选两处源码身份更新已核，其他 212 个来源项未变。 本轮只读源码/JSON并做标准库 AST 检查，没有读取权重或科学数组，没有运行模型、生成、人工测试或旧成功套件。正式加载尚须真实资源门与根任务冻结。

唯一实质问题是原 CUT3R `src/dust3r/model.py:383–415` 的两层 broad except 可以吞掉 S35 `runtime_factory.py:104–110` 对不完整参数记录的拒绝，再过滤重载。尤其只有额外 key 时，最后一次过滤可能返回成功。v1 S39 只检查工厂完成状态，不能排除这条路径。这是源码反例，未声称固定权重实际出现过它。v1 已由作者于 03:57:01.413300 UTC 完整保存在 `history_v1_before_final_state_dict_gate/`；本审不覆盖该历史。

v2 在 PASS 前增加 8 行：取实际非空 `state_dict_loads`，对每条记录要求 missing/unexpected 严格等于空列表，存在 `strict_requested`，并保存全部记录。任一次拒绝被吞掉仍会在最后失败。原 CUT3R 本地入口 `model.py:86` 请求 `strict=False` 保持；不能把完整键集验收写成所有调用参数都是 strict=True。原工厂、原模型及科学构造未修改。本次只核这一个 delta，不新增人工测试。

其余已审：官方 ft-mse 两文件绑定 547 B/`92d3…`、334643276 B/`a1d993…`，revision `31f26fdeee1355a5c34592e401dd41e45d25a493`；继承 S36/S38 已核元数据，不当作本轮本机 payload 哈希。原 SD2.1 VAE 身份保持 UNKNOWN，使用不同 schema 与明确组件变体名，不伪造原件等价。

独立标准库 AST 检查实际于 03:56:30.498795 UTC 完成：工厂仅 1 gate import 与 4 标签各一处，反向还原全 AST 相同，compile 成功而未执行。原 VMem `pipeline.py:48–90` 构造并载权重；`Navigator.__init__` 只建立状态，不调用 initialize。原图片读取/576裁剪保留但不进入模型前向；模型构造仍会分配并初始化张量。

原 VMem 显式 strict=True，CLIP 原加载默认 strict=True。Diffusers 固定 `low_cpu_mem_usage=False` 的实际 `modeling_utils.py:981–1003,1102–1160` 返回四类 loading_info，形状错误抛异常；路由核全部为空，未伪造空返回。加载后的 VAE 属性检查不等于 encode/decode 数值验证。

加载门先核所有路径、大小、来源与回执，再由 fresh worker 一次完整 SHA 读取五组件；前后 stat 和小文件检查避免重复读 GB。214 个绑定来源不是整个软件环境全锁定证明。父进程每 0.5 秒采样全树 RSS，在 1800 秒/45 GiB/10 GiB 剩余磁盘边界终止。复用 S35 `launch_original.py:155–208` 向新会话及 PID/create_time 跟踪后代发 TERM/KILL，记录 survivors；源码具备异常/超限清理和失败前缀保存，未实测新入口 kill_tree。RSS 是采样预算，不能称 OS 硬上限或保证捕获每个瞬态峰值。

成功最多为具名组件加载完成待结果审，不能扩到 codec 数值、50 步生成、原版数值复现或新方法。正式清单补路径/初图 SHA 后 core 会变化，需根任务将最终输入与源码重新绑定；本次草案审不代替该步骤。

最终增量收口 UTC：2026-09-07T04:02:59.470298+00:00。当前草案仍是 DRAFT，原始空执行回执保留；本审没有填入正式运行 core。实际组件齐备后的 manifest core 须另作绑定。
