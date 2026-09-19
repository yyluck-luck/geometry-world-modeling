# S29 最小实现边界

当前为未执行候选。原 S26B `original_context`／原 adapter 构造同 8 PIL→原 4 保存头；原 `init_minimum_spanning_tree`、`init_from_pts3d`、pair registration／depth setter 不改。只包装 `align_multiple_poses` 的返回：先原函数一次求 s0/R0/T0，再按 C2t／C2a 返回规定 s/T，R0 不变。`getter.diff` 是沿用 S28 的唯一表达式修复。

立即复制 pre-Sim3 点图／相机／focal 与原参数和 buffer，避免原后续原地修改；包装原 RoMa 调用一次捕获 raw s，记录原 near-zero 分支条件与最终实际 Python/Tensor 类型，不重跑注册，不按 `s0==1` 猜分支。原 MST 返回后启用已验证 getter，在原 optimizer loop 入口保存完整初态并一次 no_grad objective，然后以 sentinel 合法退出。守住 backward／Adam／clean 禁止门。每臂精确 1 MST、3 PnP、1 alignment、1 objective，其他计算计数为 0。

两臂都封存之后，独立进程才解码它们和已保存 B 初态。C2t/C2a 的完整前缀字节、原 s0/R0/T0 必须一致，否则 FAILED；B 历史前缀没有保存，只作已绑定输入／源码的 post-MST 数值参考，不声称其 pre-Sim3 字节已检查。三个 pre-log z 比例与 stored depth 对照、中心均值、原目标独立参考、depth→world 核验统一保存；负／非有限 z 不因原 nan_to_num 被隐藏。

`PASS_INITIALIZATION_EXECUTED` 只表示该控制按原路径走到零步终点。`PASS_VALIDATION_EXECUTED` 表示比较已完成；仍必须查看 `hypothesis_passed` 与 `failed_checks`。数值假设被否定会保存负结果并禁止作为有效尺度控制推进；输入／前缀身份失配是 FAILED。没有新 sensor 读取或深度准确率评分。

资源：两臂顺序新进程 CPU8，每臂 60 秒／4 GiB；封存后比较另 60 秒／4 GiB。复用原父资源监督，只核实际加载的 overlay 源，不扫大依赖全树。旧成功 S28/S27M 不执行；没有任何后续 400 步的实现。

正式运行必须由 root 另存 `status=FROZEN` 的 `contract.json`，给出其精确 SHA；当前 candidate 不可执行。准确 CLI：

```sh
cd '/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling'
.venv-cut3r/bin/python work/S29_scale_control_preparation/run_s29.py dispatch --contract work/S29_scale_control_preparation/contract.json --sha256 ROOT_FROZEN_CONTRACT_SHA256
```

上式 `ROOT_FROZEN_CONTRACT_SHA256` 是尚未产生的 root 冻结摘要占位，不是可执行摘要；候选准备命令为 `python3 work/S29_scale_control_preparation/prepare_s29.py`（仅源／JSON／AST，不读数组）。
