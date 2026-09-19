# S30 实现与命令

目前仅候选源码／JSON／AST 准备，未读真实数组、GT或跑新初始化／优化。原文件不改。

`run_s30.py` 复用原 S26B 全部 `ga_worker`，仅三处调度（臂名 C2t/C2a、4图、原original4归档）；原 objective／Adam／clean／独立数值门／实际源依赖门保持。派生原 S28 observer 的初态比较块，改为比较自己的 S29 全33个原参数和 buffer、flags/shape/dtype/raw bytes、objective与 alignment 输入／返回值。两个臂都采用原已验证 getter 修复。逐步梯度／参数／冻结／400行轨迹观察不改；observer.diff 列全差异，worker.diff/getter.diff 列原三处路由与一处 getter 表达式。

初始化外包装先调用原 alignment 一次，再返回同 S29 C2t/C2a 的 s/R/T；s/T 两个表达式的 AST 与已执行 S29 精确相同。原 R0 不改，极小 s→Python float 1.0 的原返回类型继续保留。新 MST 的目的是在原路径新建原 optimizer；若与自己 S29 初态不相同，首步前停止，不倒推／替换近似值。每臂原MST/PnP保留，403次objective forward、400 backward/Adam、1clean；所有数学检查全过才能封存PASS。

`score_s30.py` 直接调用原S26 scorer的seal/decode/depth_metrics/aggregate/load_sensor_depths。先两臂PASS和全文件封存，再绑定已保存S29初态，随后统一读取4张旧GT。初态直接读S29 depth，不伪造新producer／不为评分重跑MST；两个臂初/终端点合计16行、4均值组，固定final−initial差。conf不筛选、GT不拟合尺度、不挑400步中更好的一步。

回执 `manifest_sha256` 指原S26B输入父合同，本轮独立字段为 `s30_contract_sha256`；S29引用有独立来源SHA。执行预算两臂顺序CPU8、各120秒/4GiB，评分120秒/2GiB；没有自动重跑。负科学结果照常保存，不改旧S28/S29。

Root审后需另存`status=FROZEN`合同，并把下面的摘要占位替换成精确真实SHA；当前候选不允许运行：

```sh
cd '/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling'
.venv-cut3r/bin/python work/S30_scale_optimization_preparation/run_s30.py dispatch --contract work/S30_scale_optimization_preparation/contract.json --sha256 ROOT_FROZEN_CONTRACT_SHA256
```

准备命令 `python3 work/S30_scale_optimization_preparation/prepare_s30.py` 仅源／JSON／AST，不读NPZ/RGB/GT。
