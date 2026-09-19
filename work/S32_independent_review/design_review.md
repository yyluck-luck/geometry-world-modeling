# S32 四窗口设计与原消费者入口审查

**结论：固定四个时间窗口和三种普通对照的设计可以推进；A 应使用原 embedded VMem 的 `inference` 入口。新 runner／正式合同尚待其稳定后的源码审查，本文件不是执行 PASS。** 本次只读源码、已有回执与技能正文，没有读取新 RGB 像素、真实 NPZ 或 GT 图片，没有选择替代窗口、启动模型／MST／GA／反传，也未改主账。确切时间与源码身份见同目录 `design_review_receipt.json`。

## 1. 原入口与 fresh 状态

原本地消费者链条已直接读到：

`modeling/pipeline.py::construct_and_store_scene` → `surfel_inference.py::run_inference_from_pil` → 原 `prepare_input_from_pil` → **`src.dust3r.inference.inference`** → `loss_of_one_batch(..., inference=True)` → `model.forward` → `_forward_impl`。

`surfel_inference.py:355` 实际调用是 `inference(views, model, device)`，虽然同处还导入了 `inference_recurrent`。因此本轮直接沿这个入口，不必另外跑 recurrent 兼容对照。此前检查 S21 `original4` 仅用于找到本机可行路径；它用另一个本地 CUT3R 源与 recurrent 入口，不能作为新 embedded 原入口已经数值验证的证据。已有 S21 四帧监督记录约 12.20 秒、RSS 6.27 GB，只是相邻设备条件下的可行性信息，不是 S32 的速度或内存承诺。

原 `_forward_impl` 每次调用都只对传入 views 做 `_encode_views`，以该调用第 0 帧的 `feat[0], pos[0]` 重新 `_init_state`，从 learned pose memory 建立并 clone 初始状态；没有接收历史 `state_args`。之后四帧依次更新 state 与 pose memory。因此“每窗 fresh 子进程＋仅传本窗四帧＋原 inference”即可形成新 anchor。原视图 `reset=False, update=True, revisit=1` 应保持；不能把每帧 `reset=True` 当作窗口重置，否则会改变窗口内时序状态。

原 `inference` 带 `@torch.no_grad()`，`inference=True` 分支关闭该处 autocast。原 `pipeline.py:90` 对 `surfel_model.eval()`，A 应保留 eval。权重须来自已验证的本地 512 DPT 文件；本地 `from_pretrained` 检查文件存在后走 `weights_only=True` 的 loader。要核实际全部键匹配，不能让路径错落入远端模型名分支。CPU 上已有 signed-RoPE 兼容适配需明确记录来源／SHA，不能称纯原 GPU 程序或新算法。

**禁止从 S21／S24 长序列切片 `other` 头。** 这些头的 anchor、状态和 pose memory 由各自序列起点与历史决定；只改索引或做一个坐标变换也不等价于重新运行本窗。A 必须实际产生四张图的六个完整 FP32 头并封存，保留窗口内索引 0…3 和原图片身份。

## 2. namespace、PIL 与真实消费者相关性

推理和 GA 都应使用新进程。embedded 源内部同时出现 `src.dust3r` 与 `dust3r` 导入，实际模块路径必须都落到冻结的同一个 embedded 根，避免 Python 缓存混入 S21 原 CUT3R、TTT 或 FILT。不能只核一个顶层模块的名字。此入口不需要加载 VMem 的完整视频生成模型。

A 直接使用原 `prepare_input_from_pil`：EXIF transpose、RGB 转换、原 resize、居中裁剪、ImgNorm 和原视图标志均不改。B 要按相同四张图和同一函数重新准备 views，并与 A 保存的 img／true_shape（以及必要视图标志）逐字比较。相同 `(1,3,384,512)` shape 不能代替像素数值相同；不能把 S26 对另一组图片的预处理 PASS 回执移接成新窗的实际 PASS。

原 star assembly 对四帧建立 `(0,1),(0,2),(0,3)`。实际使用的 `cloud_opt/dust3r_opt/base_opt.py` 消费 anchor 的 `pts3d_in_self_view/conf_self` 和其余帧的 `pts3d_in_other_view/conf`，不是每帧 self 深度，也不是把 self 乘预测 pose 后自创点图。仓库另有 `cloud_opt/base_opt.py` 旧接口，不能误当实际入口绑定。

这与 VMem **没有旧 depth prior 时的首次建图几何消费者**相关：原 `prepare_output` 建 scene、可固定给定 pose、MST 初始化后优化。但这里只取四张连续实拍，既非完整导航历史 5／9 帧流程，也未运行 old4→new4 更新、Surfel 存储／查询或生成视频。原 pipeline 会把其 OpenGL c2w 的 Y/Z 列翻转后进入 `prepare_output`；本实验若直接输入 TUM optical c2w，应在这个转换之后接入，**不再翻转一次**。GT pose 是三种对照共享的显式 oracle 相机输入，sensor depth 仍只作评分答案。

## 3. 窗口与 20 ms 关联

采用 parent 已固定的规则，不新增选择：每个原始 `rgb.txt` 的有效 RGB 行数为 N；j=1、2，起点为 `floor(j*(N−4)/3)`，各取原始有序 RGB 行的连续四帧。两个场景共四窗。这里的 N 不是先筛选 pose／depth 成功后的长度，也不是 S21 的 300 帧前缀长度。

原 pose `associate` 和 S23 depth 关联都是候选时间差排序的一对一贪心，差值必须严格 `<0.02 s`，没有 offset；不是简单每帧独立最近邻，也不是 `<=20 ms`。若声明沿用旧全序列关联，应先在相应完整时间列表上作同一关联，再 lookup 已预选四行。只拿四行重新关联可能改变邻近帧争用同一时间戳的结果，须避免默默换语义。关联只用时间元数据，不读深度像素来决定入选。

原始四行中缺 pose 会使给定相机条件无法按此合同完成；缺 depth 会形成预定缺失／NA。都应保留窗口与原因，不能改索引、跳过难帧或用另一窗补足。具体 exposure 与是否缺配由元数据作者记录，本审查没有替作者选窗或重算实际索引。

场景身份、RGB 是否曾被解码／推理、具体 GT 字节是否曾被评分、窗口结果是否参与规则选择要分别记录。fr1 的历史 S24 与 fr2 的 S21–S23 暴露域不同；不能从“该场景用过”推出每一帧都看过，也不能从“这次预测封存前没读 GT”推出 blind。对没有可靠历史记录的项用“未知”。共同输入的 pose 如果读取原 GT 轨迹，要明确标为已知相机条件，不能写成纯 RGB。

## 4. 三控只需一次初始化

同一新窗口只需要一次 fresh 推理和一次既定 C2a 初始化。S29 的单位尺度规则、居中平移和原 R0 保持；不据新窗口的结果切回 C2t。S30 已修的 getter 应继续保留注册叶梯度，原目标和 400 步预算不变。

在同一 scene、MST 完成且第一步 Adam 尚未发生时，将完整 raw 参数／buffers 与解码 depth、focal、pp、pose、world 独立复制并封存，作为零步对照；然后在这个 scene 上继续 400 步即可。可用已有 `b.array(..., copy=True)`／真正的 tensor clone，不能只保存指向活参数的引用或未 clone 的 `detach()`。三控共享同一起点不需要再次运行 MST，也不用为了零步另建一个随机初始化 scene。零步记录必须真实标为未优化／未 clean，不能套用完整 GA producer PASS 文案。

第三个对照复用该 scene 的第 400 步终点和刚保存的自身零步，按 S31 固定全部四帧像素的唯一 `k=exp(−mean(log(D400)−log(D0)))`；不得移植当前窗口的 k 数值。D* 只是输出深度诊断，不能复制原 world／pair state 冒充完整优化器或消费者修复。初末定义域任一非正／非有限按既定失败规则保留，不用掩膜补救。

所有预定窗口的 producer 状态与三控输出固定后再统一 sensor-depth 评分，保留原 AbsRel／RMSE／严格 δ1、缺失、无效预测和完整逐窗表。像素不是独立实验数量；四个固定窗口和两个已用场景只支持有限复查，不以 PASS 或局部改善宣称创新／泛化完成。S31 的公共 log-change 占比仍不能当作 GT 误差解释率。

## 5. 预算与后续源码审最小门

parent 已指定每窗 inference 180 秒／16 GiB、GA 120 秒／4 GiB。四窗分别监督，保持继承的 CPU 数值设置，记录树 RSS、实测墙钟、exit code 与失败原因；串行新进程可以避免四个模型同时占用内存。预算到即停止并保留失败，不自动换窗或延长。四个 inference 上限加四个 GA 上限是 1200 秒的阶段上限，另行明确预处理／评分／复核开销，不能报成已实测总时长。此设计预计四次本窗推理、四次初始化和 1600 个 Adam 步，真实数量必须由执行记录确认。

稳定 A 源码审只需落实：正式合同／源／本地权重身份；四窗元数据不可换；fresh embedded 原 inference＋原 PIL＋eval／CPU兼容；只 RGB 模型输入；六头完整归档／实际模块来源；逐窗时间与 RSS 监督；无 sensor depth 提前读取。B 仍需稳定源码再审一次实际共享初态、注册 depth 梯度和封存评分路径。本文件不把尚未出现的 A/B 程序视为已经核过。

技能的具体使用：Supervisor 02.2 让本阶段检验普通强基线的重复行为，避免先命名方法；本地 Claude `sci-scientific-critical-thinking` 的实验设计、选择偏差、构念效度与证据比例要求用于区分时间预选、已见数据、深度代理和完整消费者。仅局部应用这些相关原则，不机械套临床 GRADE、不声称新手已亲自核验；本次简短接口审不生成额外科研图或调用 Claude／其他模型。
