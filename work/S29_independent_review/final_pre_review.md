# S29 最终不同作者源码前审

时间：2026-09-06T17:51:22.429831+00:00。**通过当前源码前审，可以由 root 冻结并执行两次零步初始化。** 这不是数值假设已通过，也未运行实际初始化。

全文读过 `run_s29.py`、原 `validate_s29.py`、`prepare_s29.py`、候选 JSON 及 `EXECUTION_NOTES.md`；最后仅增量审核 validator 的 21 行补丁和候选变化，没有重复整轮审查。最终候选 SHA `c8c45df377da7e8a9d8626172e4efc0b571cacc53bb3f1917db3ce45d275f59a`，runner `5293c691dae0377d1e271a0021f98e15f61268e4e54ddde8684c6281aedca81f`，validator `07352bf650256b755d08aaae1d9180036e3cd7679274f9c95fe8f2ae5b763872`。详细绝对路径与 SHA 见同目录 JSON。

之前三项必要修改均已落实：`b.array` 明确 `copy=True`，scene snapshot 也复制，pre-Sim3 点图不会被原地更新污染；原 RoMa 一次返回被只读观察，near-zero 条件与 Python/Tensor 类型实际记录，C2t 保留原 s0、C2a 安全构造 1；历史 B 明确只比较已保存 post-MST 初态。新补的固定 16 个实际消费张量覆盖 12 个 pred/conf 参数和 4 个 stacked-pred/weight buffer，名字、shape、FP32 和全部字节在 C2t/C2a/B 三者间核验；空集合不能通过，失配作为输入 FAILED 保存。

我实际读取了当前 S26B control receipt：`manifest_sha256=147357aa…` 正确对应此次父 manifest；`original_manifest_sha256=d517…` 是导入来源。不能照搬 S27M 的旧字段把它改错。相机 NPY 在本次前审仅继承已封存的 SHA，没有读取内容。

原 MST/PnP、init_from_pts3d、pair registration、深度 log 存储路径保持；只替换 align 返回的 s/T，R0 不动。MST 后安装既有 S28 getter，原 global_alignment_loop 入口 sentinel 终止，在原 Adam 建立／迭代前保存一次 no_grad objective。backward/Adam.step/clean 有禁止门；模型／GT 零调用由抽取的原 wrapper 和当前实际源路径保证，不把 0 计数器单独当证明。

validator 在两臂及历史初态全部封存后才解码，逐像素比三条 pre-log 等式，另列 log/exp 后 stored depth；用 mapped predicted 中心核均值，不用固定 given pose 做恒等检查。原目标与反投影独立公式复核继续保留；1e-5 几何门和原 1e-5/1e-4 objective 门预先固定，失败保存，不在执行后放宽。

允许保留的局限：FP32 门是本次可证伪核验而非所有输入的理论误差上界；PnP 3 次是此固定 4 帧 star 的合同，若原路径实际不符应停止而非临时改计数；`PASS_INITIALIZATION_EXECUTED`／`PASS_VALIDATION_EXECUTED` 只表示相应操作完成，科学结论必须另看 `hypothesis_passed` 与 failed_checks。四帧 oracle-camera 控制、无深度准确率／泛化／新颖性结论，0 新优化步。

本次实际轻量检查：三份 Python AST/compile；runner 和修订前 validator 的 `--help` 均 exit 0（标准库入口）。最终 validator 仅新增上述身份 gate，完成增量 AST 检查，未再次跑入口。0 真实数组／GT 字节读取，0 模型／MST／GA／backward；不导入或重 hash 大依赖树。未改变作者文件、冻结源或主账。
