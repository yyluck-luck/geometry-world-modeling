# S84 冻结源码与合同：不同作者执行前审

**结论：无实质 blocker，可由 root 按冻结合同执行一次。**

记录UTC：2026-09-10T19:01:32.872497+00:00；源码 SHA `2bd6f28fb23cf4c2e4b938fbdf191ebe0f674973bd6c50609926ba28c9f20edb`；合同 SHA `f570b7d02ec7343cb8db3f48fcc292f4ad45aac8fa4a17355e632d8b6e9cd98e`。

已完整阅读源码和合同，核9份来源文字hash、两预测档案元数据与S83实际回执、512映射矩阵的字节hash。0真实PNG/NPZ数组、0传感器解码、0真实评分、0模型或优化。

- History order exact [12,13,18,19] verified before row3; INITIALIZED_STATE is post-MST, final is100updates pre-clean. State depth/K/c2w/full archive identity bound.
- Camera-Z depth field and metre comparison match audited S83 semantics; reference divisor5000, no1.031 repeat/no range norm/no scale or offset fitting.
- 1.25 integer-grid inverse, floor(+.5), fixed continuous/integer domains, shared sensor-only V; all196608 rows and missing/invalid partitions retained.
- Both prediction states read before one16bit grayscale reference. Whole archives read/hash and all4depth maps decode are explicitly disclosed; score onlyhistory19. No false selective-byte claim.
- Stage invalid/nonpositive and nonfinite partitions disjoint; null/status with UNSCORABLE avoids inf-inf. Complete comparisons have mutually exclusive epsilon branches.
- FP64 MAE/AbsRel/median and strict paired signs match hand calculations. No confidence/depth-range/edge/visibility selection or common-finite primary substitution.
- Source/contract invocation identity, exclusive execution directory, input read-once function, runtime versions, no-network/subprocess/write guard,120s signal and sampled1GiBselfRSS are consistent with disclosed resource scope.
- Allpixels NPZ/CSV preserve undefined values as NaN or explicit literal, SUMMARY strict JSON uses null/status; traceback and partial outputs retained on errors. Outcome remains pending independent recomputation and not scientific acceptance.

独立人工值只调用从冻结源码提取的纯 score/require。固定形状人工数组中放4个非零参考，其余参考缺失：MAE 1→0.75米、Δ=−0.25；AbsRel13/24→5/24；误差中位1→0.5米；3点误差下降、1点上升。检查2.5→3及637.5→638舍入。额外核双方分别NaN/零预测、空参考和0/0.5e−9/2e−9变化，UNSCORABLE及三段互斥均通过。这些是人工算术，不是科学结果。

原设计两项歧义已在当前准确版本中消除；无需修改代码或再造执行流程。120秒与1GiB仅依合同所述内置信号/采样自RSS，不冒充硬内存上限。实际运行后仍须根据保存回执与独立重算验收。

允许的最窄结论仍是这个已见锚点的参考MAE前后变化；不把像素数当独立样本、不把proxy下降当物理精度改善、不向已冻结预测回流评分答案。
