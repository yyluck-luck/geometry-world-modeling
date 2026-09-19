# S86 独立核验最低要求与固定评分建议

记录 UTC：2026-09-10T21:14:46.075108+00:00。当前为源码与旧文本元数据审查，尚未读 S86 科学数组/新 RGB、加载模型或实算分数。root 正写生成入口和合同，另一作者正写局部挂钩；本文件不是执行许可。后续收到精确源码与合同 SHA 再作前审。

已恢复项目 AGENTS、原则 v2.11、当前记忆与最新主账。沿用本地 `/Users/rocket/.claude/skills/sci-scientific-critical-thinking/SKILL.md` 的控制、构念效度及限制审查；本次只用与本实验有关的步骤，不调用 Claude 模型或扩建审查框架。

## 1. 当前固定点可执行的条件

root 提定一个普通探索点：λ=0.25，Gguide 全 50 步同 λ，Gterminal 末步同 λ；Gpaste 用图像 mask 和同一 λ。warp 保持 S85 原孔洞 RGB0 后再转 [-1,1]，因此孔洞编码输入为 −1；同一 VAE 的确定性 latent mean×0.18215 编码一次。576 bool mask 按 8×8 avg_pool 变为 72×72 的覆盖比例，历史槽 mask 为 0。

这些约定本身无设计层 blocker，但必须在首次真实输出前冻结。root在生成前将早期草案的灰洞RGB0.5改为保持原黑洞RGB0；本文件旧稿保留为 `INDEPENDENT_CHECK_REQUIREMENTS_before_hole0.md`，没有依据新的生成结果挑选。avg_pool 数值是格内预测支持比例，不是置信度或物理可见性；VAE 感受野会让填洞值影响邻近 latent。Gpaste 和 latent 融合同一个标量 λ 不代表同等 RGB 干预强度。Gguide 对 Gterminal 的末步 warp/latent/mask/λ 必须完全相同，才可讨论较早融合及其后续传播；累计融合强度仍是竞争解释。

## 2. 挂钩与真实保存量的最小核验

| 对象 | 源码前审及保存量需能确认什么 |
|---|---|
| 共同条件 | 原 S70 A 顺序 history19/18/13/12，target20–23；原完整条件、相机/内参、原模型/VAE版本、CPU FP32/8线程、576、50步不变。共同 warp 来源绑定已接受 S85。孔洞、编码、mask及日程的实际数组与字节身份保存。 |
| G0 透明 | 原 sampler_step 原样委托；prepare_inputs 和原 MultiviewCFG 每步各恰调用一次，G0返回原 CFG 张量对象与字节。挂钩不抽噪声、不改 dtype、条件、CFG batch 顺序或原加噪/Euler公式。人工原采样器对照可证明适配透明，真实 G0 记录逐步对象/字节/RNG与50次完成；不为此再跑一条完整 G0。 |
| RNG | 所有准备/共同 warp 编码之后恢复同一完整 Python/NumPy/Torch CPU 状态，再进入两条链。保留实际初始 noise（原位缩放前）、entry/terminal和各步before/after RNG身份。原churn0仍randn_like和+1e−6必须保留。G0与Gguide的状态/输出自然可不同，但随机抽样流应一致；仅相同seed不足。 |
| Gguide | 在原 CFG 合并之后、to_d 导数之前融合。明确 `cfg_clean_raw` 与 `cfg_clean_used`，别把源码中的导数 `d` 当clean预测。作者新增 `on_clean(step_index, raw_clean, used_clean)` 回调，由root入口每个真实引导步保存这两个全8槽数组，供后验逐项重算普通融合；50×2×8×4×72×72×4=66,355,200 B的原始载荷，足够且无需重跑 denoiser。 |
| 历史保护 | 前4槽 history=True 表示保护。逐步 used 相对**本步 raw**的历史槽和零支持位置必须字节一致，包括 signed zero；不得要求 Gguide后续历史预测与G0相等，这会冻结干预后代并改掉问题。所有占位值须有限，不能用NaN乘零。 |
| G0末步 | 全量保存真实加噪后、CFG双倍batch前的 x_tilde，Euler sigma_hat/next_sigma、原sigma/gamma、raw/used clean及原step输出；shape/dtype/body身份明确。应是实际第50步且next_sigma全0。不能从最终RGB重编码或只用最终latent冒充这些量。 |
| Gterminal | 只取同一G0末步保存量，替换clean预测后沿原 to_d→dt→x+dt*d 的FP32顺序重演，再用原VAE解码。无融合重演与G0原末步输出须byte exact。不得调用 sampler_step、denoiser或重新抽噪声，也不得把精确算术等价的clean_terminal直接当原Euler字节结果。记录真实解码与RNG。 |
| 发图量化 | G0/Gguide/Gterminal保留原 tensor_to_pil 的逐帧 min<−0.1 分支、255/clip/uint8截断，并从保存raw RGB独立核原发图字节。Gpaste先按G0原分支取RGB01，再与同域warp融合；不能把RGB01与未转换VAE输出相加。NaN/Inf在量化前应失败，不能转成0后掩盖。 |

后验仅重演已保存的50步融合算术、末步Euler、RNG身份/事件以及发图量化；不重新运行完整链或denoiser，也不必为了复核再解码一次VAE。VAE本身属于已冻结组件，实际encode/decode入口、来源和输出身份由源码/执行回执核，不能冒称独立重实现其网络。

## 3. 固定完整四目标主指标

建议沿 S70 既有口径，且 root 已同意：**四个完整576×576 emitted uint8画面，各自除255后算RGB MSE，再四帧等权平均**。

`L_arm = (1/4) Σ_target [ Σ_(pixel,channel) ((U_arm−U_ref)/255)^2 / 995328 ]`。

每帧分母 576×576×3=995,328 个通道标量；四帧合计 3,981,312，四帧权重各1/4。四臂都保留全部4目标，共16条“臂×目标”记录；“16”不是独立场景数。主量不以预测mask裁剪，也不做配准、曝光调整、挑像素、裁掉失配帧或改分辨率。

报告 Gguide 相对 Gterminal、G0、Gpaste 的有符号 ΔMSE（负值才表示该指标降低），所有逐帧值与四帧均值都保存。只有胜 Gterminal 才保留“这一固定设置下较早融合及其后续传播有额外作用”的描述；若仍输 G0 不能报总体改善。不同控制回答不同问题，不能只挑最有利一项。数值降低不等于统计显著、感知改善或新颖性。

独立评分可用 uint8 差先转有符号整数，以 int64 累计平方和 SSE，再除 `995328×65025`；这些规模不会溢出 int64。这样可与原S70 float64实现核对，且各臂总SSE差的符号可精确判断，无须拿浮点噪声当收益。若正式评分仍用浮点均值，可固定小数值核验容差；容差不承担科学显著性或最小重要效应的角色。

次级仅固定 S85原图mask的 support 与hole 两区：各自明确 `3×区域像素数` 分母、目标ID及计数，空区为 NA，不能写0误差或从主量删目标。区域是预测支持，不是GT可见性。若另加边界，必须在出结果前冻结具体形态算子/半径/边界padding及是否重叠；本文件不强制增设边界指标。任一臂缺帧、原始NaN/Inf或发图验证失败，整体主比较标未完整/不可解释，并保留可读逐项诊断；不得补0或用剩余帧平均冒充完整4目标。

## 4. 参考身份与原 S70 处理

以下4份原RGB为历史上已读取的评分参考。这里只从 S70合同与实际评分 JSON 回执核对身份，没有打开这些PNG：

| target ID | 原文件名 | 已记录原PNG SHA256 |
|---|---|---|
| 20 | `1311868172.063426.png` | `0551c248bdd3d4c1e485392e9883675f54470597497772beeb9ebd775670a991` |
| 21 | `1311868172.463477.png` | `c3623ecdba3305a25f3f8f0ad31a0b232a13094ec832e53fe9703bc8fd78ed11` |
| 22 | `1311868172.799623.png` | `f8211be43e9a826111088dbd1885a162ed2874f787f0520e4cca3604363948da` |
| 23 | `1311868173.199628.png` | `4ae66610502ec747d65c293be54503bc18ddcc331ea78be8d758218bd11eea43` |

共同目录：`data/tum/fr2_desk_timestamp_guard/rgbd_dataset_freiburg2_desk/rgb/`，原图640×480。原 S70 helper在FP32中读为[-1,1]，Torch area缩放至768×576，左裁96/上裁0得到576×576；参考用已知范围 `(x+1)/2`→clip[0,1]→×255→uint8截断。预测仍保留原内容相关分支，不能偷偷把二者预处理改成统一PIL resize或统一归一化。

已存完整预处理参考：`work/S70_fixed_context_generation/scoring_01/transformed_targets_uint8.npy`，3,981,440 B，SHA `e144e842fc36c795baa05841761670555a21bc7b9c36e0a56b8440b6a2324442`，预期uint8[4,576,576,3]、顺序20–23。建议在S86预测和实际挂钩/保存量封存之后，直接读取这份已接受参考做评分并核整档身份，避免无科学必要地重开原PNG。旧答案可复用，但此时序不能恢复盲测资格。

S70评分合同 SHA `a776fd9cc1af9014de2e9226364f8990e9a2461c45b23aa6e03e5354370df8ac`；评分源码 SHA `4c698efddeca50a2c35812632516ca458ab0f1a8f9dec8f4aa4cdde0f1584ab5`。旧实际软件为 NumPy1.26.4/Torch2.7.0/torchvision0.22.0/Pillow10.3.0。解释器保持原 `.venv-cut3r/bin/python` 路径，不resolve到基础Python。

## 5. 当前最窄解释与下一动作

这是已见短序列、四个相关视角、给定请求相机、近似K/无额外去畸变、既有ft-mse VAE变体的一次普通消费探索。MSE可能奖励模糊；一份共同noise不估计随机方差；同一warp更相似不能自证收益。输入已看过不能叫确认集，当前仍 `novelty_authorization=NONE/new_method_validated=false`。

下一步优先收取实际挂钩/人工结果和root runner/合同的精确SHA，审这些要求的实际落实，收束真正影响比较的blocker。完整真实链预计量级沿S70，而非S85数组投影的秒级耗时；不靠缩步数偷偷改实验。设计审查不替代实现前审或真实保存量复核。
