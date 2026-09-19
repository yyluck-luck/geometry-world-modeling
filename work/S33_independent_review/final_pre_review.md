# S33 不同作者源码前审

结论：**PASS_S33_SOURCE_PRE_REVIEW**，当前版本无阻断。仅阅读全文源码、协议、三个派生 diff、证明与合同 JSON，做来源身份、AST 与入口检查；0 NPZ/RGB/sensor-depth PNG/GT pose 文本读取，0 模型、MST、GA、backward。没有将候选准备写成实际数值通过。

唯一新增机制对应已选定的普通对照：`m0 = ell.detach().mean().clone()`，实例因子 `exp(m0 - current_ell.mean())`。只有初态常量 detach，当前均值在实际训练 forward 中保持梯度。代数上有效 log-scale 为 `ell_i - mean(ell) + m0`，导数为 `δij - 1/3`；这保留相对尺度，去除有效共同模式。raw ell 的均值可以因 Adam 更新而漂移，不应要求其本身固定。源门核的是有效尺度的均值和相对比率。该约束不保证给定非共心相机下精度提高或物理解等价。

插入位置正确：原 C2a MST 后，第一次 no-update objective/初态快照已完成；新 callback 先与本窗 S32 的完整33项 raw/meta、全部 decoded/objective、alignment tuple 逐字匹配，再安装实例因子。初因子精确为1，尺度、有效配对矩阵、adaptors、focal、pp、c2w 都与安装前一致；随后继承修 getter 和第二次无更新 objective/值/对象/flags 门。沒有额外 `scene()`，仍是每窗原400优化加3观察共403 objective。

`norm_pw_scale=False` 保持，因而没有连带启用 adaptor 归一或默认0.5。原 `get_pw_scale` 和 `get_pw_poses` 未改，后者仍缩放整个3×4，包括编码平移解码值；每步前后也核完整矩阵。实例方法由已审 observer patch/restore 管理，`m0` 不新增 trainable 参数。400条新尺度记录不调用 objective 或反传。原深度梯度、相机/pp/frozen 参数、optimizer 成员、400步日志、clean exact、反投影和 loaded source 门继续运行。独立 pair objective 使用 factor 生效时保存的有效 pairwise 矩阵；observer.restore 不会将这份数组改回 raw 尺度。

新 worker 只替换端点保存段，保留原完整 GA 输出；顶层仅 `common_pair_scale_400` 一列，旧三条件不重跑、不撤销。固定首窗仍纯元数据 UNAVAILABLE；其他新整窗失败只使新4行 NA。评分器不由此候选自动触发，必须全部四窗新终态先封存；旧48行按已有评分身份原样导入，合并64行/16组的完整分母。预算保持每窗 CPU8/120秒/4GiB；最多三个新400，0新网络。

实际源检查核47项 source/JSON 身份、完整继承字段和所有历史参考 SHA 元数据；没有为了准备读取引用 NPZ。三个 AST 派生在实验 Python3.12 中编译且完整 unparse diff 与作者文件一致，Python3.13 中原/新 AST dump SHA 与证明一致。首次静态 probe 因两个 Python 版本的 AST 文本格式不同而出现哈希不一致，已作为检查过程记录；它不是科学运行失败，也不需要修改冻结科学代码。candidate 提前拒绝执行及实际实验环境 `--help` exit0。

本审查范围是生产者源码；S33 实际优化、评分器、保存量复核均未由本审查执行。保留零步与普通 k 强基线、已见窗口的探索性、指标混合和原始失败。普通公共尺度机制有既有文献先例，本项不能直接形成创新或视频收益结论。精确时间、源 SHA、83项源/元数据检查及实际访问边界见 JSON 回执。
