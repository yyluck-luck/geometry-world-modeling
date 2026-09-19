# S28 执行草稿与边界

本目录代码尚未执行真实 GA、模型或数组。`prepare_candidate.py` 只用标准库读取源码／JSON、核唯一 AST 和编译语法，并写候选合同。Root 已单独完成 `work/S28_root_getter_semantics/` 的人工张量语义测试；本目录不重复它。实际运行须另存 `status=FROZEN` 合同并提供精确 SHA，由不同作者前审后 root 冻结。

`run_candidate.py` 复用原 S26B 完整 `ga_worker`，仅显式 AST 派生三处调度：允许 `original/gradient_only` 名称、帧数恒 4、归档名恒 `common_old_depth_original4`。三处归一后 AST 与原函数相同。原保存、原 400 Adam 步／MST／clean 计数、目标、反投影、独立 clean、实际 loaded geometry/overlay 模块 SHA 核验不改。运行过程中的 `manifest_sha256` 仍指原父输入合同；本轮身份独立用 `s28_contract_sha256` 同时写入输入封存和 PASS/FAILED 回执，避免把旧父来源改写成新实验。

新 Observer 是原 `SceneObserver` 子类。原 MST/PnP 全部完成后才保存原始参数／buffer，B 在这一时点比较新 A 的完整 raw tensor bytes、名称、shape、dtype、flags 与初始目标，然后安装唯一 getter 表达式修复。跨进程不比较 Python id 或压缩 NPZ SHA 作为数值相等证据；文件 SHA 只校验封存，数组逐字比较另做。同臂 getter 前后检查对象 id 和 metadata/tensor SHA 不变，raw/reshape 返回与原 objective 字节不变。

每步调用的原优化 iteration 不变。额外 Adam 前门检查真实 depth grad（A 为 None、B 为非 None 且有限，允许恰为零）；每步后记录全部 4 深度的 log/depth 统计、相对初态变化、focal/pair scale、更新前 loss、实际 lr、该步梯度。全部注册参数／buffer 的名字和对象不变，冻结 pose/pp 等逐值检查。首尾完整 raw 快照保留。每臂另外两次 getter 边界 no-update objective forward、原 clean 前一次 postfinal objective，共 403 次原 objective forward、400 次 backward/Adam；`get_depthmaps/get_pts3d` 统计读取不是新增 objective forward。没有新增模型 forward。

`score_candidate.py` 直接调用原冻结 scorer 的 `seal_producers/decode_outputs/nearest_grid/load_sensor_depths/depth_metrics/aggregate`。只把两个生产者设为 4 帧，并去掉本轮不适用的共同 old-depth 冻结跨方法比较；数学不另写。两臂全 400 步、数值门、输出文件 SHA 封存且 B raw 初态匹配后，才统一解码前 4 传感器深度。共同 GT 有效像素、原尺度指标、无 confidence mask、无远点切除、无 scale fitting 保持。该已见片段用于工程因果诊断，普通梯度修复与这个小组件结果不能称科研创新或视频增益。

启动接口（仅示意，候选当前不可运行）：使用已有 `.venv-cut3r/bin/python` 执行本目录 `run_candidate.py dispatch --contract <root另存的冻结合同> --sha256 <精确冻结SHA>`。dispatch 用原资源监督逐臂新进程，每臂 600 秒／16 GiB、CPU8；两臂后评分 180 秒／2 GiB。实际两臂总新增 800 Adam 步；旧 S26/S26B/S27M 成功阶段一律不重新标号。任何失败保留原产物，不自动重跑。

本草稿根审曾发现原归档路由不能随新臂名称直接索引，已新增上面的第三处显式路由替换；这是执行前源码修正，没有实际错误运行或数组结果。原冻结源码未改。
