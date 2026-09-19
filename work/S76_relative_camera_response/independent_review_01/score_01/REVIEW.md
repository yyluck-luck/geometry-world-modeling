# S76 保存评分独立复算

算术核验通过：`PASS_S76_INDEPENDENT_SAVED_SCORE`，19,823/19,823 核项通过，0 blocker/discrepancy。两族预定的全四目标正中位事件均为 TRUE，没有 undefined/null。其含义仅是固定匹配集合上的相对方向描述，不代表全图相机正确。

冻结 verifier 实际执行一次，外部 2026-09-09T09:45:43.013024+00:00 至 2026-09-09T09:45:43.299168+00:00，0.286174542 秒，return 0、无超时、stderr 空。内部 0.116609417 秒，self peak 103,825,408 B；35 次读取，32 个独立文件，3,815,031 B。只读冻结源码/metadata、保存 numeric camera/H/FOV 和匹配 JSON；未读 PNG、权重或重新提取 SIFT、模型、生成。逐点投影使用独立标量齐次计算与 math.hypot，分位数使用排序及线性插值，未导入作者函数。原冻结 scalar/H/ray 容差未放宽。

| 目标 | 全匹配 M / 记录的 N | 共同 FOV C / 记录的 Nc | 全匹配 paired median identity−H px | 共同 FOV paired median px | 全匹配 H 中位 px | 全匹配正/负数 |
|---|---:|---:|---:|---:|---:|---:|
| 20 | 304/1281 | 302/1272 | 53.274359983 | 53.278746088 | 18.428090932 | 304/0 |
| 21 | 254/1172 | 254/1160 | 51.420688185 | 51.420688185 | 19.810091776 | 254/0 |
| 22 | 89/651 | 88/632 | 38.173156042 | 46.099145707 | 39.185465167 | 83/6 |
| 23 | 10/727 | 6/681 | 5.622094567 | 46.221459457 | 102.650659658 | 5/5 |

这里是同一批点的每点 `identity error − prescribed H error` 再取中位；不是两个边际中位数之差。完整 657 个匹配点均保留，650 个在共同 FOV，7 个处于其外，没有 invalid 点。四目标分布、最大值、全部正/负/零、覆盖、匹配 ID 一一性/范围、分母算术和 UNKNOWN 优先逻辑均独立核对。

目标 23 是必须保留的弱支持边界：全部仅 10/727（约 1.376%）匹配，共同 FOV 仅 6/681（约 0.881%），不能代表未匹配区域。其全匹配正负为 5/5，预定线性插值中位仍为正；不能把这个事件叫多数点可靠或统计显著。该目标全匹配 H 中位约 102.651 px，p95 344.506 px，最大 349.562 px。目标 20/21/22 的 H 最大分别约 378.901/403.796/226.645 px，也没有删除这些尾部。

N 与 Nc 是原 scorer 实际记录的 SIFT feature counts；冻结 scorer 没有保存全部未匹配 keypoints，因此本复算可验证它们与 M/C 的范围及比例算术，不能独立重建 N/Nc 的特征提取真值或所有 feature 的 FOV 归属。没有为补足这一记录限制重新匹配。匹配对应本身也不是独立真值。

固定 H 用实际 FP32 相机经 FP64 的独立标量相乘重建，全部整数 FOV mask 一致；true-inverse 近似偏差沿原计划另列诊断，未替换 H。保留固定图像网格 RNG，并不意味着噪声对 H 严格等变。本次可以描述同一场景、同一随机实现下的系统方向响应；不能隔离 ray/CFG/内容等单一原因，也不证明几何精度、镜头校准、完整画面服从、跨场景泛化或创新成立。原 S73 UNKNOWN/NO_METHOD 不被这次 TRUE 事件覆盖。

内部回执 `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S76_relative_camera_response/independent_review_01/score_01/receipt.json` SHA256 `52ef6eb4846eee0187bf0e7474251fde6ebb1c71662c5da90312cf5dc07fd922`。

外部回执 `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S76_relative_camera_response/independent_review_01/score_external_01/receipt.json` SHA256 `9e2c5e2072c28745def5e3650495ed1a8b98d134bc1fd1974e134d0397c9ace9`。

实际主评分回执 SHA256 `4bd270fceec5d06c040288f1cf0fb33762a0edd625d5a265338ea21f758f397c`；冻结 verifier SHA256 `d7bf57ef8d90b94719cdcbf5e8688e0accaa0d056ad9b4d16a309d6c34c84b50`。
