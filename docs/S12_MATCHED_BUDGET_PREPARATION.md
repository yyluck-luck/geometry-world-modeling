# S12 同候选数量对照：实现准备回执

记录时点：2026-09-05T22:52:22.867598+00:00。仅完成实现与纯预检；没有计算新 pose14 候选、没有运行新 NMS、没有解码评分字段。执行冻结由根任务在独立审查完成后另行创建，本回执不批准执行。

入口 `scripts/run_s12_matched_budget.py`，SHA `ccc36d5a7a0efcce82c7354818b878e91464e3822b680259e6dd03d504e7f6d5`。命令参数为必填 `--protocol --freeze --output`；协议固定 `docs/S12_MATCHED_BUDGET_PROTOCOL.md`，初次新结果目录固定 `results/S12_matched_budget`，若已存在则停止。任何运行失败保留现场。

固定输入76文件：两原运行各metadata/records四文件，以及12个block/stride case各predicted_poses、prediction_only_selection和q20–23四评分NPZ，共72文件。执行源码仅新入口和原三个函数来源，共4文件。协议、执行冻结及非空独立审查证据另随源码ZIP保存；所有原文件前后SHA、ZIP全部成员CRC/字节SHA核验。

从原源码AST提取五函数：average_camera_pose、RetrievalKernel.geodesic_distance、optical_to_vmem、initial_nms_threshold、decision_trace。原FunctionDef经过ast.unparse后再解析，完整AST包括docstring均与原node相同；源模块整体不导入。仅构造含预测相机、原阈值与距离记录器的最小对象，不加载地图、renderer、模型、PNG或GT位姿值。

新执行只24次decision_trace，0次旧选择器。先核六组前5历史初始阈值；每query重算20个FP64距离转FP32并核旧完整向量/排序和零并列，随后固定前14集合、ID升序各count1交原NMS。日志保存实际每次距离的两个完整矩阵、数组身份、权重、返回值与phase；所有distance_call_range为从0起的半开区间[start,end)。24份完整新选择、6组阈值和距离日志写出SHA总seal后，才首次解码旧48评分NPZ的support/valid。

评分先核两密度相同，整数计数重现768旧读出以及48个20历史支持上界，完全相等才接受新pose14评分。192配对行复用24个新选择，按S7dev4/S7test8/S8test12和每地图/密度分别汇总；主格A0P0/stride8，差方向来源14减姿态14。无新性能或显著性统计，不称新未见查询或视频效果。

预检证据：work/S12_matched_budget_preflight/receipt.json为首稿纯调度/输入路径/语法/help/AST检查；work/S12_matched_budget_preflight_v2/receipt.json为最终提取表示的语法/help与5完整原AST检查。第二次改动仅避免dedent改变docstring空白，未改任何数学或原源。两次均未导入NumPy/Torch，未执行提取函数；先前回执原样保留。

冻结合同模板 work/S12_matched_budget_preflight/contract.json；根任务将其放入协议唯一s12-matched-budget-json区块。冻结schema为s12-matched-budget-freeze-v1，status为approved_for_execution，包含frozen_utc、protocol_sha256、execution_source_sha256、input_sha256、review_evidence_sha256。600秒及16GiB为软预算；CPU八线程，不声称OS隔离。
