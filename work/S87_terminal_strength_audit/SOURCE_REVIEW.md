# S87 独立生成源审

**GO：允许 root 绑定后执行一次当前有界六策略任务，未发现剩余实质 blocker。** 此结论仅指源码可执行审查，不能写成真实解码成功或科学结果已接受。审查时间 2026-09-10 23:33:17 UTC；复核者与生成/监督实现作者不同。

精确文件身份：

- `generate_terminal_controls.py`：`fea09f959f9ecfe86407fabc57408f95eb7a6fa7652322f06f172c24e8eca5d6`
- `GENERATION_CONTRACT.json`：`337982b200182b50ade46aee4625c5c7ff3d87f5acce01bd48343451015c2538`
- `supervise_derivatives.py`：`35efdf242b8375c6631569564da42d341102bc887521833bd7b510036503ce57`

已全文读执行器/合同/监督器与人工检查源码及实际人工回执，核回原 `append_dims/to_d`、`replay_last`、融合函数与 `AutoEncoder`。最终修改仅涉及平台/未导入原去噪网络断言及回执身份存放，不改变数学。六组次序、三种强度、四目标与历史顺序完整；输入绑定旧 S86 保存量和既定 ft-mse VAE，生成侧无目标参考读取。VAE 单次加载，原 `.18215` 缩放、3 次完整8槽解码和24个 chunk1；无新 denoiser/encoder/噪声/几何。

clean 融合先按 mask/history 形成权重，再保留 `where`；Euler 使用真实保存的 `sigma_hat` 和 `x_tilde`，没有用 clean 直接冒充输出。RGB 族保留原 Torch 分支、clamp 和 bool mask，发图保留另一条原 NumPy 量化路径。独立核器准备期间确认负零与 −.1 阈值的跨库差异，已记录人工证据；它们要求核器精确复现原语义，不要求更改科学执行器或放宽容差。

初读发现的单组回执自引用问题已改为 top `arm_receipts`；落盘单组内容现在可以与总回执 `arms` 精确比较。root 评分草稿也已改成读取实际 nested `counts`。评分最终版本另审，不阻塞本次生成。

作者人工回执 SHA `d6aa2e852723cdbd547db86af0a2eb4a9c412d6943bcfcd51bf4113d897ccaa2`，对应人工源码 SHA `86d9055d886a6ba8484f6bf164b345c9c5829c80253da47063d33d756f3bff63`：38项、24个小型 stand-in wrapper chunks、0真实解码，实际0.577298333秒。本审查只读这些证据，没有重跑该批，也没有读取真实数组/权重。

监督器绑定 root freeze/执行器/合同 SHA，保持未 resolve 的虚拟环境解释器路径。600秒总时限、120秒单 terminal、16GiB进程树RSS按2秒采样检查；超限实际记录 SIGTERM，10秒退出宽限后才 SIGKILL。这是带采样与退出宽限的限制，不是瞬时硬峰值保证。失败和未运行策略保留，运行目录新建且无自动重试。初始化后的 Python/NumPy/Torch CPU 完整 RNG 状态前后比较，不能扩称逐调用随机历史已重建。

后验核器可与本次实际运行并行准备，在 root 绑定最终回执前不运行。它只核保存量算术及身份，不重新解码、不评分真实几何或画质；普通末端有限对照不构成新方法。
