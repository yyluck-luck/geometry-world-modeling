# S11 人工来源控制：独立执行前审查

**PASS，限30个来源控制条件。** 无剩余主要或次要必修项。这是静态实现与准备检查结论，尚未运行参考选图或候选，不能写成30条件实际通过。此侧与168既有变体扩展独立，原侧的正式审查、结果与冻结均未在本审查中修改。

完成时间：**2026-09-05T22:07:15.530241+00:00**。全文核新来源入口、执行协议和独立设计；对照固定原renderer、原get_context_info、S6桥接、S7记录器以及S9/S10观察/加载工具。本审查未导入数值库、解码NPZ、读取新S11结果、执行renderer/selector/模型/真实计时或创建执行冻结。

## 参考缓冲是否合法

合法性限于当前固定普通Surfel类、源码、环境和实参。原renderer第61–179行没有读取self；AST独立检查确认对象仅读position、normal、radius，整个kernel对source映射的唯一读取在第229行的累票方法。Surfel第15–27行是普通属性存储，没有隐式来源getter。因此，只改mapping而保持几何/顺序和实际渲染实参时，旧原buffer可作为该渲染函数的参考。

完整get_context_info第265–268行仍会计算query平均姿态、Y/Z翻轴及surfel_Ks均值×0.65。新render_arguments按同一固定源构造预期参数；回放器核聚合几何数组的shape/dtype/C内容SHA，以及pose、focal、principal、宽高和16边形参数。几何摘要不包含mapping；完整state_identity另含mapping，避免把合法来源编辑误判为几何变化。宽高/分辨率现先要求内置整数，再转标准值，拒绝小数、bool和字符串的截断碰撞。该守卫限于当前构造的参数类型，并非任意自定义对象/NumPy标量类型的通用兼容承诺。

reference只是**原完整选择器 + 守卫封存buffer回放**。原投票、归一化、配额、距离、排序、NMS真实重算；原renderer本轮零调用。candidate才运行固定S10真实renderer。不能用这一reference的墙钟推算加速，也不能说两个renderer都重新运行。

## 条件域与计算规则

六个基础条件为S7/S8各三块的A0P0、stride8、width160、query20。复用原S10的52文件，旧loader会核全部24查询但筛出六个q20；没有因此重跑24条候选。每块先一次原mapping baseline回放，完整trace核旧参考。

每块从原mapping独立复制五次，按append_min_missing、drop_last、reverse、only_0、only_0_1_2执行，合计30条件；前18是来源编辑，后12是来源数边界。修改全体合格行，不依据可见性、候选输出或改选效果挑行。每行非空、无重复、历史ID0–19；位置/法向/半径/顺序/颜色/counts、20个history、相机/K、上下文和阈值保持。counts故意不重估，故不是实际观测、merge或物理更新历史。

原配额n=min(14,k)使当前有效k≤14每源一次、k>14选14源各一次；不会走n>k的重复配额分支。mapping列表顺序影响首次字典插入，可能影响浮点归一化与同票截断；第240–241行的最终ID排序不能消除前面影响。原首次出现的双加也保留。因此reverse不预设等于旧mapping，只要求A/B对相同编辑完全一致。

only_0和only_0_1_2保持20个历史数组，改变的是可见来源数。原max_frames允许输出1/3，而非强补4；封存buffer必须有正有效投票，否则停止，不换query。欠源结果不会被冒称完整模型可消费或实际来源更新现象。空/重复/越界来源不入成功域；空检索、一历史、五历史初始化及NMS=False路径未覆盖。

## 记录器适配与输出门

原S7 decision_trace已按maximum选择，但末尾两个长度验证硬要求4；直接复用会误拒合法1/3结果。新工厂只在内存中将这两个常数换成maximum，保留所有计算、NMS记录与ID范围；反向恢复整个函数AST完全相同，原源码不动。独立准备检查实际执行了这个纯AST工厂，未调用生成的NMS函数主体。原get_context_info函数身份在两臂均检查不变；每次记录selected还必须等于真实选择器返回ID。六个baseline的适配trace先核旧四ID参考，避免适配静默改变旧域。

每条件两臂独立且初始完整状态相同。reference回放必须恰一次，candidate真实计算一次；30候选 + 30修改来源参考 + 6旧mapping baseline，共66次完整选择器，36次合法buffer回放，原renderer0次。18个被拒守卫调用不计为合法回放或选图。

每条件两臂保存实际render、context、trace与before/after状态。候选三数组逐shape/dtype/C bytes对封存参考，包含±0；两臂所有上下文身份SHA与实际tensor值、完整official_trace/decision、返回ID全部一致。trace比较没有variant或mapping元数据伪差异。只读验证getter返回刚产生结果，不另跑renderer；实际数组在诊断前保存，renderer返回后selector失败也保留缓冲。输入状态在调用后逐项核对；only_0须[0]，only_0_1_2须恰好三ID且两臂顺序一致。

正常完成时60个条件臂各有render/context/trace/state四类产物；六baseline另保存完整trace，其渲染参考仍是旧封存buffer。本报告不把baseline重放副本计为新生成的原渲染。

## 负对照、冻结与失败留痕

每块在候选前固定修改相机平移、首面片位置、首焦距各0.001，共18个守卫负对照。新版先核实际签名恰有预定字段变化，再要求回放拒绝；每次立即保存拒绝原因、预期/实际差异摘要。它们不会改变正式输入，也不执行renderer。某条件或后续候选失败时，先前完成的负对照记录仍保留。

陈旧mapping负对照只比较旧baseline与修改后reference的实际official_trace/decision，不比较标签、摘要或输入SHA。预定前18编辑条件至少1个检出；12个明显欠源条件不能代替这道门。不是要求每个reverse都改变，也不要求最终ID必须改变：权重/配额或轨迹差异即可检出。不能在看完结果后换条件。

运行前必须有独立新冻结，绑定13项源码/许可、与S10完全相同的52输入、协议与旧/新冻结、**非空**设计/独立审查证据；前后核SHA。三个ZIP保存源、输入、审查；源码ZIP另含协议与两冻结。本脚本没有逐成员重开ZIP校验逻辑，后续归档/独立结果审计不应把已存ZIP本身当作全部成员已再核的证据。

版本固定，先设线程再导数值库；Tensor内核CPU/FP64几何与默认FP32排序保持。Python I/O守卫不是OS沙箱；600秒与16GiB为软守卫，只存总资源时间，不作性能比较。完整30条件、6baseline、18实参拒绝、至少1/18陈旧trace检出以及所有原件不变才completed。失败保留目录和异常，不放宽门、不改变候选/旧数据，不用部分结果宣布完整通过。

## 已关闭问题与实际准备检查

审查先指出低来源记录器硬4问题，已由上述AST适配解决。另提出三项冻结前修正：尺寸int截断、负对照仅结尾保存且缺少原因、review摘要可为空。最终源码均已修复，并逐项只读重核；这些不改变原选择器、候选或数值容差。

最终**29项纯准备检查全部通过**：五个确定列表编辑、原输入不变/键一致、六类非法来源拒绝、两终端guard适配和其余AST相同、八个尺寸类型guard实例、四个非空review guard实例。回执`work/S11_pre_run_review/source_pure_precheck_final.json`，实际UTC 2026-09-05T22:05:47.862613+00:00。原renderer来源依赖另3项AST检查于`source_dependency_static.json`。旧17项草稿回执保留；这32项是代码性质检查，不是32个实验样本或一次实际来源选图。

## 最终身份与结论边界

- 来源入口：`b2aa29f3c3486a062bbb2f1a388318e0be8ae72d5d9ce84d0f0926b5b69ed176`。
- 执行协议：`f6b029b958f5b04905d98a3b6866523e6c97136030677461a541de0a340beb38`。
- 来源设计MD：`230fa036ee5abc824fd48a63d872279b656e4bf256f2cd46f2f762638da28a9f`。
- 固定候选：`3e079d0bbbaed962b24bce599a5cf7198b6bbc2891ac3c91761f4ea5c4f0e521`。

完整SHA见同名JSON，已读源码副本存`work/S11_pre_run_review/source_final_reviewed/`。主任务可据此另冻结执行；本审查没有批准或创建冻结。只有冻结后的真实产物及独立复算才能宣布30条件运行成功。有限人工来源控制不证明连续导航、真实地图更新、缓存命中、跨版本泛化、视频质量、全VMem速度或论文创新。
