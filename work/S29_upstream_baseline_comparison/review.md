# S29 上游基线源码对照：恢复梯度语义，不是新算法

完成：2026-09-06T17:43:30.304810+00:00（UTC）。本轮只读当前执行源码、已保存源码分析和官方文本；**0 数组／GT／模型／MST／GA／反传／人工数值实验**。这是三个指定机制的有界对照，不是源码全量审计、issue 调查或论文写作。原文件与主账均未改。

**结论：S28 的修复是在本地逐帧 ParameterList 结构中恢复 DUSt3R 已有的“深度参与梯度优化”语义，不是发现了上游本来没有的新优化方法。共同尺度归一化关闭也不是 VMem 独有的遗漏：官方已知相机分支已经这样处理。初始化中的自由 Sim(3) 与局部深度取法同样继承上游，剩余误差需要受控实验解释，不能据源码亲缘认定因果。**

## 固定身份及历史证据

UTC 2026-09-06T17:39:57.567083+00:00 实际解析官方 main 为 `4c24a6ebf04809f2cfe59915e51779c8984aaa40`，该 commit 日期为 2025-07-01T12:36:01Z；“当前 main”只指本次观察，不是 2026 新版本。只取了 optimizer 单文件历史的一页（请求上限10，返回5），再看最早列出的 `add code` 固定版本 `c4f675b177434225ffa69d176182956388f6a538`（2024-02-27）。当前及该历史版本的 getter/helper AST 相同，足以确认健康的梯度读法早已存在；没有追踪所有分支或给某个作者归责。[当前源码](https://github.com/naver/dust3r/blob/4c24a6ebf04809f2cfe59915e51779c8984aaa40/dust3r/cloud_opt/optimizer.py) · [历史源码](https://github.com/naver/dust3r/blob/c4f675b177434225ffa69d176182956388f6a538/dust3r/cloud_opt/optimizer.py) · [有界文件历史](https://api.github.com/repos/naver/dust3r/commits?path=dust3r/cloud_opt/optimizer.py&per_page=10)

实际本地 optimizer SHA `f78f52eee0fc5e435e2c8b16a868174a285e7155577c11eef0f82a464e207b11`，base SHA `edd07a0d04e72c5687149f9dd90c36bfebcdac365c424e3ba9161fc73c495134`，init SHA `b3f59fbf32fd9690e63551ac14dc957edef9145bb3d5544fcb53a6eb3758bb21`。抓取文件、SHA、实际时间及对应函数范围见 `sources.json`；语法树对照见 `source_comparison.json`，差异全文另存三份 `.diff`，不表示逐行差异均已作语义审计。

## 三项差别与本次解释边界

| 核查项 | 官方 DUSt3R 固定源码 | 当前执行的内嵌版本 / S28 | 可支持与不可支持的判断 |
|---|---|---|---|
| **深度叶子及 getter** | 构造时把逐帧初值打包为最终注册 Parameter；getter 直接对该 Parameter 求 exp。helper 中 detach/new Parameter 发生在初始化参数创建阶段。 | 取消构造期 depth 打包，保留逐帧叶子；getter 却每次再次调用会 detach/new-leaf 的 helper。其 flag 一致断言还变为只有 is_param 真时执行。S28 在 getter 直接 stack 原叶子，保留本地逐帧冻结结构。 | 恢复已有可微语义的局部工程修复。没有恢复官方完整数据布局／padding／冻结接口；不能把整份上游 optimizer 直接替换就认作等价。真实 common4 支持本阶段，人工 mixed8 仍不等于真实8图端到端验证。 |
| **共同尺度规范** | 默认 norm 开启、base_scale=0.5；有效 edge scale 为 exp(raw_logscale)×exp(log(base_scale)−mean(raw_logscale))。已知 pose 的 preset_pose 最后冻结 poses 并无条件关闭 norm。 | `get_pw_norm_scale_factor`、`get_pw_scale`、`get_pw_poses`、`_set_pose` AST 与上游相同。preset_pose 只有相关执行顺序／打印差异，最终 fixed poses 与 norm=False 一致；S28 未改此项。 | 不能写“VMem 漏掉上游防坍缩约束所以导致本次失败”。反过来，切回 norm=True 是新的目标参数化控制，会重新固定全局尺度约定，不是已知pose分支的原样恢复，也不保证米制正确。 |
| **已知 pose 初始化尺度** | 对相机中心及短 z 轴端点做可估尺度的配准；点图和预测相机同步变换，再除掉相机旋转块中的s；之后按变换后预测相机求局部z，已冻结场景pose拒绝再写。 | 初始化数学顺序 AST 相同，只有末尾 verbose objective 打印去掉。`align_multiple_poses` 额外加入 epsilon≥1e−6，以及 abs(s)<1e−6 时把s改为1；不是所有情况下固定s=1。 | 自由尺度初始化与按预测相机求z的路径是继承关系；局部数值保护另列。S27M 已存s≈0.173不是该极小尺度回退的输出，不能用回退解释它。未检查当前 epsilon floor 是否触发，不能推测其影响。 |

第一行依据 [optimizer.py 构造／getter/helper](https://github.com/naver/dust3r/blob/4c24a6ebf04809f2cfe59915e51779c8984aaa40/dust3r/cloud_opt/optimizer.py#L28-L60)；第二行依据 [尺度函数](https://github.com/naver/dust3r/blob/4c24a6ebf04809f2cfe59915e51779c8984aaa40/dust3r/cloud_opt/base_opt.py#L178-L195) 及 [已知 pose 分支](https://github.com/naver/dust3r/blob/4c24a6ebf04809f2cfe59915e51779c8984aaa40/dust3r/cloud_opt/optimizer.py#L66-L81)；第三行依据 [init_from_pts3d](https://github.com/naver/dust3r/blob/4c24a6ebf04809f2cfe59915e51779c8984aaa40/dust3r/cloud_opt/init_im_poses.py#L80-L120) 与 [上游配准](https://github.com/naver/dust3r/blob/4c24a6ebf04809f2cfe59915e51779c8984aaa40/dust3r/cloud_opt/init_im_poses.py#L308-L316)。

## 三个容易混淆的“尺度”

1. 论文 §3.4 为自由全局对齐使用 edge-scale 乘积约束以排除零尺度平凡解；固定代码默认把有效尺度几何均值设为0.5，即乘积为0.5的边数次方。它是共同尺度约定，不是传感器米制校准；论文常数1与代码常数0.5不可逐字当成相同数值设定。[DUSt3R 原文 §3.4](https://arxiv.org/html/2312.14132v3#S3.S4)
2. 已知相机分支关闭这个共同归一因子，返回因子1；**不表示每条 pair scale 本身等于1或被冻结**。pair logscale仍为可训练参数；短而非零的给定相机基线也不自动证明它无法约束尺度。此处源行为与上游一致。[官方尺度读法](https://github.com/naver/dust3r/blob/4c24a6ebf04809f2cfe59915e51779c8984aaa40/dust3r/cloud_opt/base_opt.py#L178-L195)
3. 初始化配准求出的s是另一处具体操作。既有分析的精确算术式 `Q'⁻¹(P'−c') = s Q⁻¹(P−c)` 表明同步变换的公共R/t相消，s留下；源码两版都遵循这一路径。这是条件代数结论，不是本轮重算，也不说明130°朝向残差造成0.173。仅固定s=1是采用当前预测的名义单位先验，仍须另行验证。

## 对 S28/S29 的具体影响

- S28 只改梯度连接、初态逐字匹配，其负结果仍有效：在本地已见 common4 的条件下，梯度恢复不足以改善原尺度误差。不能因此声称官方 DUSt3R 已复现同样的数值失败；官方 packed Parameter、数据与完整执行没有在这里运行。
- 下一步初始化尺度／平移控制属于普通强对照。保持s但重算中心平移，与固定s=1并重新匹配中心平移，可以分开两个干预；它不是“应用上游最新修复”。本轮没有读取任何 S29 运行结果或执行候选。
- 若以后比较默认尺度 norm 与已知pose分支，需新冻结输入、尺度常数和参数自由度；不能把 norm=True 直接追加到本次 matched 结果，或拿 sensor GT 比例选择常数。
- 没有检索或声称找到“官方同名 ParameterStack bugfix issue”。这次正证据来自上游健康实现及历史版本，已经足够否决新颖性；没有搜到某个 issue 也不能证明原创。

## 记录边界

核心入口共5项源码／单文件历史加1篇原论文，仅关注上述函数与论文段落；main API 和官方仓库主页仅用于确认出处。第一次并行下载 base_opt 发生 TLS EOF，其他文件成功，随后只补取缺失文件；原始失败及成功状态在 `sources.json` 说明，未隐藏为首次全成功。没有外部留言、权重下载、原代码修改、实验重算或主账修改。
