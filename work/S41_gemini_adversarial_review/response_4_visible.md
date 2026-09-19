# Gemini 第四轮可见回答转录

- 取得方式：用户已登录的 Gemini 网页，模式界面显示 `Pro Extended`。
- 证据边界：这是从浏览器可访问性树人工转录并排版的可见文字，不是 Gemini 后端导出，也不保证逐字节一致。
- 科学地位：外部意见；未经 Codex 对源码和原论文逐项复核前，不是事实、实验结果或新颖性证据。

## 1. 主张的明确撤回与保留

Gemini 撤回上一答的核心建议“Geometry-Guided Token Masking”：VMem 每张历史图只提取一个未归一化的 1024 维全局 CLIP 向量，cross-attention K/V 长度为 1，没有 patch token 可供几何 mask。它保留“concat 通道可能主导”以及先做输入置零/消融的诊断建议。

## 2. 近邻压死测试

Gemini 将普通“利用三维几何引导特征读取/路由”判断为已被下列近邻大量覆盖：

- **SPAD / EpiDiff（CVPR 2024）**：输入多视角图像与相机；状态为空间特征图；没有显式长期缓存；沿极线或局部对极邻域读出 patch/latent 特征。
- **WorldStereo（CVPR 2026）**：输入历史帧与三维先验；状态为 global-geometric memory 和 spatial-stereo memory；按时空几何更新；以三维对应限制 attention receptive field。
- **Spatia（CVPR 2026）**：输入视频流与 SLAM 轨迹；状态为可更新点云空间记忆；通过视觉 SLAM 融合；渲染或投影到当前视角作为条件。

Gemini 的意见是，普通 geometry-guided routing 操作空间特征或点云已有直接近邻，不能用改名获得新颖性。

## 3. 剩余最窄问题

在 `[K/V length = 1]` 的全局压缩和 `global CLIP cross-attention + spatial latent concat` 双通路结构中，多视角全局语义直接求均值是否不可逆地破坏回访实例身份；或者该 cross-attention 通路已被模型忽略，只充当全局语义或色调控制器。

Gemini 明确把它称为待验证的架构诊断问题，并未判断为新颖贡献。

## 4. 五臂诊断顺序

共同固定历史帧 ID、历史 latent、pose/K、噪声和随机数。

1. **原始 mean**：`mean(CLIP_1...N)`，K/V 长度 1。
2. **zero CLIP**：输入全零 `[1024]` 向量；计算形状相同，但信息被删除，用于判断 cross-attention 是否有作用。
3. **single source**：固定取一张预先声明的历史图向量；计算形状相同，但信息不同，用于判断均值混叠。
4. **source sequence**：不求均值，令 N 个向量形成 `[N, 1024]`；信息与计算量均增加，只作为“若保留来源身份是否出现差异”的上界诊断，不能与 mean 公平比较算法收益。
5. **mismatched scene**：保持 concat 历史 latent 和几何正确，送入无关场景 CLIP 向量；计算形状相同、语义信息不同，用于判断该通路更像局部身份控制还是全局风格控制。

## 5. 立即退出条件

- zero CLIP 与原始 mean 在预先定义的回访区域指标和视觉结果上无稳定差异：停止研究 CLIP 聚合。
- mismatched scene 只改变整体色调/风格而不改变实例结构：不再声称 mean 导致局部身份丢失。
- source sequence 不比 mean 恢复更多预先定义的身份/局部细节：global CLIP 本身缺少空间映射，保留多个全局向量也不足以解决问题。
- 真实原始基线没有稳定出现预注册的回访失败：该问题没有经验基础，停止此方向。

## 6. Gemini 裁决

当前仍属于基线架构调试；已有工作已经覆盖宽泛的三维几何路由，而 VMem 的单全局向量是否形成可研究的新问题，必须先用真实基线和排他性干预建立证据。

