# S34 图注

**图 1：固定旧四帧深度后，零步、自由 400 步和共同尺度约束 400 步的新四帧平均 AbsRel 分别为 4.6059%、4.3474% 和 4.3221%。** 图中完整显示帧 4–7 的 12 个值与三个等帧权重均值，统一纵轴从 0 开始；柱色与横向位置区分条件，点形区分帧，黑横线是均值。输入是已见的同一八帧短序列，并给定 GT 相机，邻近帧不独立；无置信区间或显著性主张，不能把普通约束的小幅差异表述成新方法成功。主评分及不同作者的保存分数算术核验已通过，绘图只将既有 AbsRel 乘 100，没有重新读取传感器 GT 或评分。

**图 2：三种条件的真实地图渲染保存量不同，但预 NMS 候选来源列表均为 0–7。** 这里展示的是已执行原 VMem kernel 的 512×288 深度栅格，固定查询为本输入相机 7；三图共用线性色标，包含三图全部最大值，原始零值单列浅灰表示未覆盖，没有空间裁剪、百分位截断或额外归一化。覆盖像素计数来自已有渲染记录，不是 RGB、sensor-GT 一致性、可见性准确率或未来视角质量。保存量和原票权/配额算术已有不同作者复核，但这不是另一个独立 renderer 的重实现；NMS 与 latent 历史缺失，最终 context IDs 未运行。

出处：`results/S34_depth_scoring/{metrics.json,per_frame.csv,receipt.json}`，`results/S34_original_consumer/*/render.npz`，`work/S34_independent_numeric_review/receipt.json` 和 `work/S34_consumer_numeric_review/executed/receipt.json`。完整路径、SHA、全部 12 帧点/3 均值/3 渲染栅格值见同目录 `plotted_data.json`。PNG 用于快速查看；分数图 PDF/SVG 是矢量，渲染深度栅格在 PDF/SVG 内仍为固有像素数据，文字和色标为矢量。
