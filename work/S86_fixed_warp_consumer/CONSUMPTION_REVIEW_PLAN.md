# S86 保存量消费链独立核验计划

这是执行前源码与检查范围；没有读取运行中的数组、参考图，也没有生成核验结果。只针对本轮 `execution_01`，不调模型、不再跑完整采样、不读取其他场景或答案。

## 冻结与运行

不同作者核器 `check_saved_consumption.py` 不导入生成、hooks、fusion或评分作者源码。使用项目原路径 `.venv-cut3r/bin/python -I`（不能将解释器符号链接 resolve 到无 NumPy 的 base runtime）。当前只做源读取、AST/内存 compile 与少量纯人工 NumPy 值核查。

真实生成和监督封存后，由root写 `CONSUMPTION_REVIEW_BINDING.json`，包含以下四个**实际完整SHA**：`checker_sha256`、`generation_contract_sha256`、`generation_receipt_sha256`、`supervision_sha256`。生成合同固定为 `954c4353745280d5d3f48ac9db124b8a23aa877e1c59e9ecdd13f399416e844f`。Root全文核读后给绑定文件的SHA，只允许一次运行：

```text
R/.venv-cut3r/bin/python -I R/work/S86_fixed_warp_consumer/check_saved_consumption.py --binding-sha256 <实际绑定文件SHA>
```

输出仅 `INDEPENDENT_CONSUMPTION_REVIEW.json`，排他新建；异常保存状态与已完成检查，不修改数据/标准，不自动重试。完整比较要求正式四臂终态；若真实生成失败，程序拒绝完整PASS，由root报告真实失败，不把失败补成四臂分数。300秒、4GiB自身峰值检查、SIGALRM；这不是OS硬内存隔离。

## 精确读取范围

- 四份合同绑定的S85 TARGET原档案只提取 `warp_rgb`、`mask`；对全档案SHA/大小核验。不会解码这些NPZ中未消费的几何数组。
- S86共同保存的RGB、mask、encoder_input、ENCODED_WARP；两个完整臂的noise、all8_latents、targets_fp32、7字段LAST_STEP；Gguide全50份raw/used clean；两派生臂targets_fp32及Gterminal两种latent存档。
- 精确SHA绑定的生成回执、监督回执；其绑定的progress、各数组/档案和所有字段描述；另逐字典核对各臂receipt与总回执，并核读steps、完整common/entry/terminal RNG JSON、model_baseline元数据。
- 不读取目标参考、原RGB/深度、模型权重、新生成PNG或uint8输出数组。uint8发图和正式MSE由另一作者评分器及root独立算术核验负责。监督status只回传，资源/终止原因由root结合监督回执接受。

## 算术、保存与计数

1. 原4warp与保存RGB/mask逐字节一致；黑洞0、编码2RGB−1、前4历史latent零；原bool mask按每8×8共64格整数计数，再除64，独立验证软覆盖和历史全0。warp编码latent只核已保存值的身份/shape/finite和历史零，不声称独立重算VAE。
2. 50份Gguide raw/used全部独立FP32融合；历史槽及零mask位置要求逐字节保持，包括signed zero。它是直接clean保护，不意味着后续模型传播或解码完全隔离历史影响。
3. 两链分别核50个完整步骤、50个prepare/CFG/callback、一链0融合/另一链50融合；G0透明性用实际trace的对象标志与raw/used body SHA，并用实际末步数组补核。G0没有保存50份raw，不能写成50份全部逐数复算。
4. 两链7末步张量固定shape/dtype与body SHA；next sigma严格0、gamma0、原sigma_hat保留 `+1e-6`；按原 `d=(x-clean)/sigma_hat`、`dt=next_sigma-sigma_hat`、`x+dt*d` 的FP32顺序重算。G0等价于零融合重演；Gguide使用其实际末步used，并核该used来自第50份实际融合。
5. Gterminal从原G0真实末步raw重新融合、重演Euler，核actual clean/latent和解码输入副本，所有受保护末步latent逐字节等于G0。不会另执行VAE解码。
6. Gpaste从实际G0 raw的原条件分支先转RGB01再clamp，随后原图mask×0.25混合；孔洞位置逐字节等于转换后的G0值。没有额外denoiser。
7. 两条链初始noise逐字节一致，完整entry/terminal RNG文件重算canonical SHA，50步前后hash逐项相同且相邻连续；共同restore同一SHA。中间RNG只保存了运行时实际状态hash，不伪称这里重新生成50份完整状态；派生无RNG、G0末步逐字节重演及模型身份不变按封存运行记录一起检查，不替代模型重跑。

## 固定算术容差

身份、key/shape/dtype、离散mask、输入副本、保护位置与重复保存量用严格字节相等。融合和Euler独立NumPy重表达保留FP32各步顺序，每项误差限固定为 `8*eps(float32)*operand_magnitude + 8*smallest_subnormal(float32)`。

融合的operand_magnitude为两项加权项的绝对值之和；Euler为 `|x| + |dt/sigma_hat|*(|x|+|clean|)`，包含相减前的两项以避免相消时误差限错误归零。系数、mask和输入均固定，这只是少量单精度算术的保守误差包络，不是视觉质量阈值。每个比较保存实际最大绝对差、非零差个数和界；不根据实际误差改阈值。严格字节保护仍不受此容差豁免。

PASS的最窄含义是本轮保存量和已声明消费算术一致。不能据此证明几何真实、生成改善、盲测、多个独立场景或创新。VAE/denoiser的数值正确性与完整原系统等价性不在该保存量核验范围。
