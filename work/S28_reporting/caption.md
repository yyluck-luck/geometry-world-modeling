# S28 辅助图图注

On the four previously seen S28 frames, restoring depth gradients lowers the original optimization objective but increases final raw-depth absolute relative error (AbsRel) from 83.34% to 87.48%.
Both arms start from matched raw initialization and take 400 Adam steps with the original fixed-camera constraints; these are single runs of an engineering control, not independent repeated trials.
(a) Every pre-update objective is plotted at the number of already completed steps (0–399), with the separately recorded postfinal value shown as a diamond at step 400; the vertical axis is logarithmic.
(b) For each frame F0–F3, the plotted quantity is the saved mean over all 384×512 pixels of d_t(p)/d_0(p), not the ratio of frame means; all four original curves overlap exactly at 1, and no sensor depth enters this panel.
(c) Final saved AbsRel values (lower is better) are shown for all four frames and their equal-frame mean, with no scale fitting or confidence filtering; no stepwise sensor error, uncertainty bars, scale-collapse mechanism, generalization, or generated-video improvement is established by this figure.

中文说明：这四帧中，接通深度梯度后，优化目标降得更多，但最终深度误差从 83.34% 增至 87.48%。左图保留完整 400 步，菱形表示第 400 步完成后的额外目标求值；中图逐帧保留深度相对初始化的变化，使用“逐像素比例的均值”，原方法四条线均为 1；右图展示四帧最终误差和等帧均值，越低越好。它说明这次普通梯度修复不足以改善已见小组件；图本身不证明尺度退化是全部原因，也不是生成质量实验。

使用：论文／LaTeX 插入 `s28_gradient_control.pdf`（向量），可编辑版 `s28_gradient_control.svg`；`s28_gradient_control.png` 仅供预览。原生宽 7.5 英寸、最小字号 8 pt，缩小插入前应重新排版／增大字号，不能直接宣称所有期刊栏宽下均满足 8 pt。
