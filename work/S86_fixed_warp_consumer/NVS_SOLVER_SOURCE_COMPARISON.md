# NVS-Solver：一条公开 DGS 推理路径与 S86 的源码对照

实际整理完成时间：2026-09-10T22:04:30.248574+00:00。**找到了公开融合实现；它是 latent 标量排序后的硬替换，再作 Euler 更新，并非式 12 的逐元素凸平均。** 可据此准备下一轮普通排序替换对照，但不能直接称为完整 NVS-Solver 复现或已验证强基线。当前 S86 合同、运行与结果均未改动。

## 来源身份与实际读取边界

官方仓库：[ZHU-Zhiyu/NVS_Solver](https://github.com/ZHU-Zhiyu/NVS_Solver)。本次 GitHub API 返回 main commit **`40c6555e53f45d6532a00b5c1e13aaa120dc9973`**，commit 时间 2025-03-30 06:33:57 UTC。所有随后源码请求固定此 SHA，没有使用漂移的 main 文件。读取记录在 `nvs_solver_source_01/FETCH_RECEIPT.json`；原字节归档记录包含 5 次成功 HTTP 获取：commit 元数据、README、demo、一个 single-image DGS 文件及它调用的 Euler scheduler 文件；另外通过浏览工具打开了仓库页面与作者 arXiv HTML，不将那两次页面读取遗漏为没有发生。

限定路径是 **README → demo.sh 的单图向右 DGS 命令 → svd_interpolate_single_img_dgs.py 内置 pipeline → scheduler.step_single_dgs → 解码与输出**。这里的“调用链”指公开源码规定的路径，**不是本机实际运行轨迹**。没有展开 POST、multi-image、dynamic 或 arbitrary-trajectory 分支，也没有泛扫整个仓库。仅定向阅读这些文件的入口、预处理/warp、编码、循环、被调用 scheduler 方法、日程与输出；没有宣称全文审完仓库。

没有下载模型、示例图、depth、sigma 数组或权重配置，没有安装、导入或运行作者代码，没有读 S86 正在生成的科学数组/参考。不能从这些源码确认作者论文评测具体执行的 commit、实际模型配置或本机可运行性。论文对应作者 [arXiv HTML v2](https://arxiv.org/html/2405.15364v2) 的 §4.1 式 11–14、§4.2 式 17–18 和 §5 Implementation Details；本轮实际读 HTML，未读会议 PDF。

## 可定位的完整单路径

以下 `P` 指 [svd_interpolate_single_img_dgs.py](https://github.com/ZHU-Zhiyu/NVS_Solver/blob/40c6555e53f45d6532a00b5c1e13aaa120dc9973/svd_interpolate_single_img_dgs.py)，`E` 指 [scheduling_euler_discrete.py](https://github.com/ZHU-Zhiyu/NVS_Solver/blob/40c6555e53f45d6532a00b5c1e13aaa120dc9973/src/diffusers/schedulers/scheduling_euler_discrete.py)。行号均按保存原字节文件计。

| 环节 | 文件、行号 | 实际源规则 |
|---|---|---|
| 公开入口 | [demo.sh 30–41](https://github.com/ZHU-Zhiyu/NVS_Solver/blob/40c6555e53f45d6532a00b5c1e13aaa120dc9973/demo.sh#L30-L41)；P 1106–1137 | 选 single-image DGS 向右命令：radius 60/70、每帧 1 度、CLI weight_clamp=0.2。主函数先 warp，再读取 `sigmas/sigmas_100.npy` 求日程，最后调用 `svd_render`。本次没有执行。 |
| 原条件准备 | P 701–863、940–999 | 一张源 RGB 与一个预测 depth NPY；原图变为 1024×576，depth 用 `10000/depth` 与截断/resize，名义焦距 260、主点 (512,288)，构造 25 个椭圆轨迹相机。不是 S85 的四历史/已知相机/hard Z winner。 |
| warp 与孔洞 | P 781–863、967–995 | 四邻足迹按深度函数加权并归一化颜色；支持还要求累计权重在 (0,0.6]。孔洞 mask 反转后做 5×5 膨胀；8×8 均值后以 0.2 二值化为 latent 孔洞，RGB 相应位置置黑。不是物理可见性真值。 |
| 模型入口 | P 1000–1010、314–340 | `stable-video-diffusion-img2vid-xt`，fp16、CUDA，25 帧（1 输入＋24 新视角）、100 步，解码 chunk=8。调用没有传 generator。源码有默认 CFG 从第 1 帧的 1 到末帧的 3。这不是 VMem 的 8 槽/50 步/CPU 设置。 |
| warp 变成 latent | P 170–191、444–484 | RGB 经预处理；VAE `latent_dist.mode()` 编码，建立 CFG 两分支；拼入源帧，再**硬编码除以 5.6**。融合使用其中条件分支 `[1:2]`。形状是 [分支,25,4,72,128]；mask 广播到 4 通道。不是在 RGB 上排序。 |
| 原预测 → 融合 | P 533–558；E 818–962 | U-Net 输出先 CFG 合并；`step_single_dgs` 根据 prediction_type 将其转 clean latent，再逐帧排序/硬替换。权重配置实际取决于运行加载的 scheduler；本次没有读取模型配置，不能把某一 prediction_type 分支冒称已执行。 |
| Euler 与发图 | E 964–980；P 575–584、221–248、1006–1010 | 用融合后 clean 构造 `(sample−clean)/sigma_hat`，按下一 sigma 差作 Euler；cast 回 model_output dtype。末态按 VAE 配置 scaling_factor 解码，再 postprocess；保存 25 PNG 与 fps=7 的视频。未接本项目 uint8 MSE 评分。 |

## 式 12、式 13 与实际硬选择如何对应

论文式 12 令 `r=λ/(1+λ)`，得到 `μ̃=(1−r)μ+r·warp`；式 13 用 `μ̃` 代入 clean 形式的扩散更新。§5 另明确采用排序选取以避免直接平均造成模糊。因此，**硬选择是作者公开说明的实现替代，不是式 12 对每个元素的代数等价实现**。[论文 §4–5](https://arxiv.org/html/2405.15364v2)

E 930–958 的实际顺序如下：取某个目标帧条件 latent `FEA`，取 `lambda_ts[step,tau]`，把预测与 FEA 各乘二值支持 mask；差值取绝对值并把 **C×H×W 全部展平**排序，形成阈值；所有 `abs(diff)≤阈值` 且在支持内的元素直接改成 FEA。同一空间位置的四个通道可以部分替换，代码没有先求通道 L2 范数并把整个空间像素一起选中。每帧各排自己的元素，没有跨 24 帧统一排序。第 0 输入帧则每步全量替换为其条件 latent（E 962），不经过排序。[实际选择代码](https://github.com/ZHU-Zhiyu/NVS_Solver/blob/40c6555e53f45d6532a00b5c1e13aaa120dc9973/src/diffusers/schedulers/scheduling_euler_discrete.py#L923-L970)

所以选中处相当于系数 1、未选处为 0；它不保留统一的 soft 系数 r。论文连续凸组合的误差不等式不能未经额外推导就当作这个离散选择程序、或 S86 消费者的已证明保证。此处是源码及数学语义判断，不是质量实验结论。

## 三个会影响最小适配的具体细节

**1. 名义比例不等于严格替换比例。** E 934–953 的 `num_zero` 只计 [1,1,H,W] 的无支持空间位置，但排序数组有 [1,4,H,W] 元素。令总空间格数 P、孔洞数 q、名义比例 r，则当前截点为 `floor(r·(4P−q))+q`，而 masked 差里实际已有 4q 个孔洞零值。它不等于在 4(P−q) 个有效标量中精确选 r 比例。再加 `≤` 会把阈值平局全部取入；真实零差也参与排序。因此不能把保存值 r 报成实际替换率。这个差异可从维度直接推出，本次没有运行人工数组试验。未来适配要明确保留原选择语义，还是单独声明修正为有效元素计数及固定平局规则，不能静默修完还称逐字复现。

**2. CLI 下限没有沿这条路径传到 scheduler。** P 1004 把 weight_clamp 传入 pipeline，但 P 558 的 scheduler 调用没有传它。E 827 默认 `None`，E 950 因而不是 demo 所写 0.2 的下限。不能把这条公开命令解释为实际执行了最小 20% 的替换；这是源调用不一致，未通过模型运行验证。

**3. 公开日程与论文表中固定系数不是一回事。** P 1012–1105 读取 sigma 列表后，搜索 v1=0.001…0.009、v2=50…1000（间隔50）、v3=10…100（间隔10）。它用归一化 sigma、tau/24、k=0.8、b=−0.2 的四个候选根，保存的是 **λ/(1+λ)**，以所有步/帧中超过 0.5 的项数择优；不是按新图评分调参。首帧对应比例为 1。该源码搜索不能直接等同论文 §5 列的系数，也没有读取运行时 sigma 数组与 scheduler 配置来证明二者一致。不得把源码名 `lambda_ts` 再做一次 λ/(1+λ) 转换。

## 对 S86 的最小结论与适配边界

**可移植的是普通“按预测—warp 的 latent 标量差排序后硬替换”的消费者操作；不能直接移植整个公开入口。** 下一合同可在 S86 已有 CFG 后 hook 接受 `raw_clean / warp_latents / eligibility_mask / per-step-per-target ratio`，产生 `used_clean`；仍委托原 VMem Euler 与原 RNG，保留四历史、四目标、同一输入几何与当前 VAE 变体。需要保存每步实际选中 mask、支持/候选/选中计数及阈值或 tie 规则，才能独立复算“用了多少”。它不需额外深度模型，但改变逐步 clean 后必须重新跑一条完整生成链，不能用当前 Gguide 保存量假作新输出。

冻结前只需具体决定三个接口差异：S86 8×8 平均后的**软覆盖**怎样变成排序的合法集合；是否保留作者的通道/孔洞/阈值平局语义；比例日程是原搜索适配还是与当前 S86 对照匹配。本文不选阈值、比例或新日程，不启动后续实验。若仅保持 S86 日程而替换算子，应称“借鉴 NVS-Solver 公开 DGS 选择规则的 VMem 对照”，不能称完整 NVS-Solver 或其论文最佳结果复现。

尤其 S86 的 λ=0.25 是**直接凸融合系数**，对应上述 r；它不等于论文 λ=0.25（后者 r=0.2）。即使 nominal r 匹配，连续平均与硬选择仍不等实际干预剂量。历史保护也不能照搬该程序每步覆盖第 0 帧的做法；保留 S86 四历史直接保护是任务适配差别，必须披露。固定同一 S85 warp 可隔离消费者差异，同时也意味着不复现作者的单图深度、warp、mask、SVD、时长和相机路线。

**裁决：有公开且可定位的候选强对照来源；最小算子适配在结构上可行，但尚未实现、运行或证明更强。** 原文/源码差异削弱把“普通 clean 融合”称创新的依据，不预先决定本次 S86 胜负。不同任务、模型和输出不能直接拿论文数值替代本项目结果。

## 保存文件身份

本机原字节副本均在 `work/S86_fixed_warp_consumer/nvs_solver_source_01/`。只保存公开源码/元数据，合计小于 120 KB（不含本说明），无权重或科学图像。

| 文件 | 字节 | SHA-256 |
|---|---:|---|
| commit.json | 5428 | `bc7b748ffbddc0cadc885b1f88d654abd76362f6f8d5beaa8de6defe32fe8b02` |
| README.md | 12025 | `f8e61620c3c7c38e353c3be22065c590377ffff68c468a49449d04aad42747a0` |
| demo.sh | 2456 | `ed1aa466cc563688c84dba4a8064c922dab3dd6777233507b1a6d1f25d6c5c1b` |
| svd_interpolate_single_img_dgs.py | 48174 | `01e6527cccb494fd7e97af9cdd3b3617044766c4aedede495856ba8a0bdf1142` |
| src/diffusers/schedulers/scheduling_euler_discrete.py | 49576 | `574d19a23d661dfa4a30571370c192641dfc5909f4f9565c4947dd558d8ffc15` |
| FETCH_RECEIPT.json | 2266 | `1bb35c2386885c8f0d2de22a34b910c1ded9850bd631c80c30979a3ff29782c7` |
