# S30 不同作者完整数值复核协议（准备，未执行）

本目录仅准备一个保存结果复核入口，不启动、轮询或安排执行。当前没有读取 S30 数组或 sensor GT 字节，没有加载模型、运行 GA/MST/backward。生产与主评分由其他作者完成；本复核复用已实际执行的 S28 独立 OpenCV/逐行数学实现，不冒称再写了第三套公式。沿用已读 Supervisor 2.2 的基线失败与根因对照、Claude 本地 scientific-critical-thinking 的证据边界；本任务不是文献调查或新方法提案。

## 绑定与开始条件

`recompute.py` 只导入字节固定的 `work/S28_independent_numeric_review/recompute.py`，SHA `2bef151226649a87b5c8cc29e6bd5173b2ece63900837f100dbf4338006d40f2`，不调用它的 main。不改 AST/数学函数，仅将模块的 BASE 指向 S30 结果目录。复用 `load_archive`、`validate_raw`、`trace_review`、`independent_frame`、`metric_match`。helper 仅 stdlib 顶层导入；NumPy/OpenCV 和实际数值操作位于全部封存完成之后。

S30 候选合同 SHA `d5e7326875cffaf314fadd48e7b5f43e4fd63d7afda3f7d3a63498bd8e04c86f` 已绑定。正式合同尚待 root 冻结；执行显式传入合同路径/SHA、复核源码 SHA、协议 SHA、helper SHA。拒绝候选状态、条件变更、已有 attempt/receipt。冻结可新增审阅元数据与身份项，原候选字段和身份项必须保留。正式主合同无需修改以导入本复核；caller 应独立记录这些参数与边界预算。

先核两 producer 与 scorer PASS、对应合同、原 400 步/一次 clean、每臂完整初始化门；再核直接源身份、两 producer 全产物/输入 seal/receipt、主评分全产物、两份各自 S29 零步 receipt 与四类参考文件。这些保存输入必须与主 scorer 的 `input_sha256` 一致。最后读取四张 GT 的全部字节并对原身份和 scorer 身份验 SHA。**以上所有字节封存完成、写出 input_seal.json 后，才允许任何 NPZ 或 PNG 解码。** 这是复核本身的次序，不声称原主评分也先读 GT 字节再解码预测。

## 完整数值与记录范围

1. 固定 C2t/C2a × S29 保存 initial/S30 final × 4 帧，16 个完整 384×512 网格，共 3,145,728 次像素访问。四张 GT 原图 480×640 uint16，用 OpenCV 解码一次；米制除 5000，整数中心映射 `5*(2*i+1)//8`。保留全部正 GT，不裁远点、不按置信度筛、不做 GT 尺度拟合。
2. 原独立 helper 逐行 float64/math.fsum 重算 AbsRel、RMSE、严格 δ1 与无效预测比例，以及六种计数、状态。δ1 使用两条严格乘积不等式；有效 GT 上出现任一无效预测，AbsRel/RMSE 为 null，δ1 仍使用完整有效 GT 分母；空 GT 保留 null。浮点绝对容差 `1e-12`、相对容差 `1e-10` 不变，整数/null/状态精确一致。
3. 四个完整等帧权重均值组共 16 个浮点聚合量、所有 defined_frames、分母和空帧/无效帧清单；另核 8 个“终点−初点”差以及 JSON/CSV 全 16 行。不能换成有值帧均值、像素池化或挑最好优化步。
4. 新 C2t 全部 33 个 parameter/buffer 对自己的 S29/C2t，新 C2a 全部 33 个对自己的 S29/C2a。完整名称、shape、dtype、requires_grad、张量 SHA 与每个字节一致，共 66 项。并独立要求两臂各自保存 initial decoded depth 和 objective 与 S29 精确一致。其余七个共同 decoded 字段记录字节比较；它们是描述，不额外改变预定深度/目标门。S29 额外 prelog_depth/norm_scale 核字段与形状；不从它们重建历史对象。末态完整 raw 元数据、张量内容 SHA、schema/flags 也核验。
5. 两臂 ordinary/gradient trace 各完整 400 行，复用 helper 原序号、loss/lr 对应关系、线性学习率、逐帧首尾统计及 focal/edge-scale 检查。该函数原条件为 `arm == 'original'`；C2t/C2a 均不满足，因此不改函数即要求两臂每步四个 depth 梯度存在。另核六个观测训练参数组均 400 次梯度存在且有限，**允许范数为 0**。保存全部 800 步摘要；梯度数值来自历史记录，不重新反传，不称独立重算梯度范数。
6. 结尾复核所有本次绑定源/输入 SHA 没变，输出完整 metrics、initial review、trace review 与 PASS/FAILED receipt。无优化收益要求；即使误差变差也不改变门或重试。

## 范围限制与交付

复核不读取额外 S24 数据，不重新拟合相机或计算 ATE，不重做已成功 GA，不改变 frozen producer/scorer。S29 alignment 数组只验文件身份及 producer gate 记录，本脚本不重新做 alignment 数学。大型依赖与 head 的完整历史检查继承生产回执/父 manifest；这里只重新核 S30 合同直接身份与全保存产物，不重新遍历上千依赖。

这是已见相邻 common4 的普通尺度初始化控制审查，不是未见测试、生成视频、长期记忆或新方法收益证明。运行后 PASS 只表示所列数值/身份/记录检查通过；准备阶段的 AST/compile 只能证明代码可解析。

本次准备的确切时间、源 SHA、执行计数 0 与 CLI 参数在 `preparation_receipt.json`、`candidate.json`。root 审阅与正式合同 SHA 到位后才可另行启动；没有等待循环或自动执行器。建议沿已知保存数据复算配置：CPU1、180 秒、2 GiB RSS，由 root 的外部 caller 实施资源限制，不在本复核里启动子进程。
