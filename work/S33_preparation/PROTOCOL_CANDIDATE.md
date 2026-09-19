# S33 普通公共配对尺度约束：执行候选

状态：源码/合同准备，未执行。本协议继承 S32 固定四窗以及其真实模型头、C2a 初始化、修复 getter、400 Adam/.01/linear、原目标/clean/评分规则。唯一新条件为 `common_pair_scale_400`；目的为检验普通尺度约束，不作新方法/长期记忆/视频收益主张。[决策依据](../S32_next_decision/review.md)。父任务有持续本机科研授权；本候选仍要求不同作者源码审与父冻结后执行。

## 唯一变化与插入时序

使用 S32 已封存每窗 fresh4 头与同一原 PIL、star anchor0 self/后续other（24全部head与12实际star tensors身份保持）。不再运行 A 或旧自由尺度臂。新进程重新执行一次原 C2a MST 是为了建立可训练实例；其完整33参数/buffer名字、shape、dtype、flags和raw bytes，以及全部decoded初态/objective/C2a alignment tuple必须与本窗 S32 实际初态逐字匹配，失败留档停止，不重新定义起点。

插入位于 S32 observer 的 `verify_window_initial_state` 原callback位置：原MST返回 → raw/decoded快照和第一无更新loss已存 → 与S32逐字核对 → 安装实例级公共factor → 原getter修复 → 第二无更新loss/值/对象核对 → 原400训练。所有 source 文件原件不改；实例override在原producer finally恢复。

令 `ell=scene.pw_poses[:,-1]`，保存 `m0=ell.detach().mean().clone()`。新 `get_pw_norm_scale_factor()` 返回 `(m0 - scene.pw_poses[:,-1].mean()).exp()`。只有初态常量detach；**当前mean不得detach**，训练时factor必须requires_grad。初态factor须逐值等于1，全部原decoded值/loss及参数对象不变。原 `norm_pw_scale` 保持False，不能连带改变adaptors；不引入默认0.5或强写1.0。

原 `get_pw_scale`、`get_pw_poses`、forward不变。有效scale=exp(ell)*factor，约束其log均值为m0，保留相对边尺度；原整个3×4包含旋转和平移一起缩放。depth/focal/pair rotation/encoded translation与相对scale仍训练，相机/pp及原非训练参数冻结。raw ell均值可以随Adam漂移，验证有效尺度而非raw均值。给定非共心相机下这是真正的约束变化，不能称无损纯坐标变换。

## 必须通过的门与记录

- 所有当前来源身份、冻结S32 A/B合同、4窗状态、各窗S32回执/参考初态文件SHA先核；准备阶段只从JSON继承array SHA，真实bytes由未来运行前核。本次没有打开NPZ/RGB/GT。不得以元数据封存冒充实际数组内容复核。
- 原完整33状态逐字门、原相机/pp冻结、actual400梯度finite/nonNone、same optimizer membership、原source实际加载路径、原目标独立重算、全像素clean、world反投影沿原成功代码。只继承必要已有门，不新增另一模型兼容实验或全依赖目录递归扫描。
- 初态与每步前/后有效log均值距离m0 `atol=1e-5`；3条相对尺度比原exp(raw)比 `atol=rtol=1e-5`；实际完整3×4与原_R/T解码乘有效scale逐值一致。保留400行 `s33_scale_trace.jsonl`，原400行loss及depth/focal/grad trace继续保存。新增trace不调用scene objective/反传。
- 每可用窗400Adam/400backward、1MST/3PnP、1原clean、403objective（原400+既有patch边界2+末端1），0网络。此次只替换patch边界callback，源前审须确认无额外scene()。MST之后设置factor，不干扰C2a的s=1初始化。
- 保存原完整 `GA/C2a/output.npz` 的depth/point_cloud/conf/focal/pp/c2w及effective pairwise state；`GA/C2a` 是继承producer内部兼容名，顶层新条件/receipt明确S33尺度约束，不能将它误记自由C2a。

## 输出/评分接口与完整分母

新输出：`results/S33_pair_scale_control/{window_id}/receipt.json`；顶层候选 `common_pair_scale_400.npz` 仅key `depth`、FP32、(4,384,512)。PASS回执有window_id、selection_sha256、contract_sha256、endpoint_files、outputs相对路径→SHA；顶层整窗FAIL则新4行NA，原S32三个对照仍按其历史回执保留，不撤销旧PASS。

fr2_desk_j1无给定相机，仍UNAVAILABLE；不插值/换窗/扩大匹配阈值。其余三窗各一个新400。全部四窗终态及新候选输出封存后独立评分器才能读GTdepth；GT相机是所有条件相同的已有oracle输入，非盲测。规则从S32固定JSON继承：相同nearest mapping、sensor /5000、完整有效GT域、无GT-scale-fit/confidence-mask/farcut、每窗四帧等权、无效预测保留与NA规则。

旧48行/12组原样按S32评分封存SHA导入；另加新16行/4组，合并64行/16组，预期48评分16NA。既定窗口分母始终4，不能以3窗代替。没有对候选新增k后处理端点；不重新模型推理或重评分旧端点。评分器由另一作者准备，此生产候选不自动启动评分。

## 资源、命令与停止

每窗fresh CPU8子进程、120秒、4GiB RSS，4窗顺序；3可用窗总1200新Adam/反传、3MST/9PnP/3clean，0网络。保留原监督器10GiB磁盘门；评分另120秒/2GiB。环境不改，复用 `.venv-cut3r/bin/python` 与已有overlay。root冻结后用候选回执中的实际命令，把显式 `--sha256` 填入冻结合同SHA；candidate状态不能运行。实际预算超限/来源变化/身份不匹配/科学门失败均保存FAILED，不能自动重复或调整参数。

科学解释沿决策稿：有效尺度门通过不等于GT改善；共同depth log偏移是否减小，与AbsRel/RMSE/δ1是否超过零步及普通k分别报告。新候选仍不胜两强控或结果混合，则原样报告；本轮不继续在三个已见短窗调m0/focal/先验/步数。无论结果如何普通尺度约束不构成创新；后续由实际消费者问题决定。

## 已应用技能与执行边界

Supervisor handbook2.2以强基线失败定位变量；idea-evaluator排除DUSt3R已覆盖公共尺度约束的创新声明；本地Claude科学批判用于因果、替代解释与外部有效性。沿S32_next_decision已读技能/来源，不为数量重复工具。本文件与prepare脚本只写`work/S33_preparation`，不动canonical记忆、旧源码、旧结果，主账由父维护。代码静态编译/help成功也不代表模型/GA/数值兼容通过。
