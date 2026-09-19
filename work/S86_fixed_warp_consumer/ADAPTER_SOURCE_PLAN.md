# S86 最小采样适配方案：捕获 G0 末步，再重演 Gterminal

实际源码核查记录：2026-09-10 20:32:30 UTC。作者：/root/s77_science_closure。本次只读源码、协议和 JSON 身份，0 模型导入/实例、0 科学数组读取、0 新生成、0 人工张量执行；仅新增本文件。没有选择融合强度 λ 或干预日程。S85 已接受的投影是后续共同输入，不是准确性标签；本方案不是可直接启动的完整生成合同。

## 1. 保留原采样器，用两个小挂钩

工程位置 R = /Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling。

原入口为 R/work/S70_fixed_context_generation/generate_fixed_contexts.py。保留其已验证加载、条件消费、随机状态恢复、模型状态核验及原 do_sample 路径；后续只在 S86 新入口中适配，不能导入 S70 后直接调用 run()，因为它的路径/三臂/执行目录属于旧实验。

新入口在原 312–315 行对应位置创建原 sampler 后，先核其 guider 原类为 MultiviewCFG，再安装下列组合。只给这一 sampler 实例替换属性，不改原类、源文件或全局 to_d。

1. 沿用原 317–338 行 observed_step 的实例包装，保留 original_step = sampler.sampler_step 这个原绑定方法。其准确调用签名（去掉 self）为：

       observed_step(sigma, next_sigma, denoiser, x, scale, cond, uc,
                     gamma=0.0, **guider_kwargs)

   每步只登记 step_index、原 sigma/next_sigma、gamma 和是否最后一步，然后把同一实参逐项交给 original_step。step_index 由实际进入/成功次数记录；最后一步是冻结 50 步中的第 50 次，并另核 next_sigma 全零。失败保持 entered/failed，不当作完成。原返回值原样返回；仅末步另复制保存 all8_step_output。不要在这里重写加噪、denoiser 或 Euler 公式。

2. 将 sampler.guider 换成一个持有 base_guider 的普通 Python 代理。源码实际只调用它的这两个接口：

       prepare_inputs(self, x, s, c, uc)
       __call__(self, x, sigma, scale, c2w, K, input_frame_mask)

   prepare_inputs 原样委托 base_guider.prepare_inputs(x, s, c, uc)。最后一步在委托前复制 x 和 s 为 x_tilde、sigma_hat；这里已经执行原加噪，尚未构造 CFG 的双倍 batch。不要重新计算 sigma_hat，也不要把双倍 batch 的输入误存为 x_tilde。

   __call__ 先且仅调用一次 base_guider(x, sigma, scale, c2w, K, input_frame_mask)，得到 raw_clean。G0 直接返回这个原张量对象；末步只另存 detached clone。Gguide 才在冻结的干预步调用 S82 纯函数，然后返回其结果。不得在 CFG 分成无条件/有条件两半之前融合；不得改 prepare_inputs 的 uc 在前、c 在后顺序。记录各步 prepare/CFG 委托恰各一次，避免漏挂或重复前向。

原 sampler.sampler_step 使用当前 self.guider，因此这两个实例包装能配合，不需要复制 EulerEDMSampler 或改它的循环。开始下一臂时使用原流程创建新的 sampler/denoiser 和新的代理状态，不复用上臂计数器。

## 2. 实际挂钩的位置与容易混淆的量

R/work/S20_environment/isolated_vmem_source/modeling/sampling.py 中：

| 行 | 原语义 | 本方案 |
|---|---|---|
| 393–396 | sigma_hat = sigma × (gamma+1) + 1e−6；仍 randn_like；得到加噪后的 x | 完整保留；prepare_inputs 的 x 正是 x_tilde |
| 398 | 原 denoiser 消费 CFG prepare_inputs 的 16 槽输入 | 完整保留；模型额外输入 num_frames=8 不变 |
| 399 | 原 MultiviewCFG 输出 8 槽 denoised | 代理先得到 raw_clean，再作规定融合 |
| 400 | d = to_d(x, sigma_hat, denoised) | 源码这个 d 是导数，不是 clean prediction |
| 401–402 | dt = append_dims(next_sigma−sigma_hat, x.ndim)；x + dt × d | 完整保留 |

为避免歧义，保存字段叫 cfg_clean_raw、cfg_clean_used，而不只叫 d。设计文中的“捕获 d”指原 denoised/clean prediction。DiscreteDenoiser 174 行还会把网络 sigma 映射到离散索引；Gterminal 必须使用 Euler 的实际 sigma_hat，不拿网络离散化后的 sigma 替代。179–185 行的历史 replace 在 denoiser 内部生效，也不能把其替换后的输入当作原 Euler 的 x_tilde。

S82 接口 R/work/S82_history_geometry_guidance/latent_geometry_guidance.py：

    fuse_clean_prediction(denoised, warp_latents, support_mask, history_slots, strength)

真实采样预期 denoised/warp_latents 为 CPU FP32 [8,4,72,72]；support_mask 为同 dtype/device [8,1,72,72]；history_slots 为 bool[8]。历史 19/18/13/12 对应前四槽 True，目标 20–23 对应后四槽 False，须与实际 input_masks 核对。warp_latents 的历史槽可用有限零占位、mask 为零，不能塞入 NaN，因为函数先检查全部张量有限。True 表示保护历史，不能反转。

原函数零强度或无支持返回原对象，非零融合以 where 保留无支持/历史值。这里“历史不改”只指当前一步 clean prediction 相比该步 raw_clean 不被直接融合；Gguide 的后续模型状态可自然变化，不能强制其历史 clean prediction 等于 G0，否则改变因果问题。

## 3. 从同一 G0 重演 Gterminal：只重做末步代数及解码

捕获 G0 第 50 步的 x_tilde、cfg_clean_raw、sigma_hat、next_sigma，保留原形状、FP32、CPU、实际字节。融合所用 warp_latents、support_mask、history_slots 和最后强度必须与 Gguide 最后一步相同。未来末步重演逻辑严格为：

    clean_terminal = fuse_clean_prediction(cfg_clean_raw, warp_latents,
                                          support_mask, history_slots, final_strength)
    derivative = sampling.to_d(x_tilde, sigma_hat, clean_terminal)
    dt = sampling.append_dims(next_sigma - sigma_hat, x_tilde.ndim)
    terminal_z = x_tilde + dt * derivative
    terminal_rgb_all8 = ae.decode(terminal_z, 1)

不能调用 sampler_step 重演，因为它会再次抽噪声并运行 denoiser；也不能把最后两行 Euler 运算改为直接解码 clean_terminal。即使 next_sigma=0 时两者精确算术等价，FP32 相消顺序可能改变结果。

重演沿用原 do_sample 的 torch.inference_mode 和 CPU autocast disabled 环境，模型 eval/frozen，原全 8 槽 chunk1 解码、scale_factor=0.18215 不变。先保留原 G0 末步返回值；不融合的同一保存量重演应与该返回值 body SHA 完全一致。这个检查不需要额外完整生成。Gterminal 另存完整 terminal_z，再按实际 input_masks 提取四目标；原 tensor_to_pil 的 min<−0.1 条件转换、乘255、clip、uint8 截断保持，并记录每目标实际分支。Gpaste 在 G0 明确转换得到的 RGB01 域操作，不能把 RGB01 warp 直接和未经转换的 VAE 原输出混合。

## 4. G0 数值/RNG 不变的实施边界与最少记录

原 do_sample 在进入 sampler 前创建初始 randn；原 prepare_sampling_loop 随后会原位缩放它。继续在 S70 observed_sampler 的位置、原位缩放前保存 noise。原 50 步在 churn=0 仍各执行 randn_like，且 +1e−6 不能删除。代理不得调用随机函数、重新 set_seed、重算 get_cond、改变 dtype/device、顺序、尺度或 cond/uc。

在所有模型/warp 编码准备后，沿原方法恢复同一完整 Python/NumPy/Torch CPU 状态，再分别启动 G0 与 Gguide。原参数和共同输入继续固定；新增准备过程不能夹在恢复状态与原 do_sample 首次抽噪声之间。VAE 编码接口使用 latent_dist.mean，不改成 sample；warp RGB 到编码输入、孔洞填充值、mask 到 72×72 的规则及 λ/步表须在后续合同显式确定，本稿不选择。

最少新增记录：

- 每臂代理模式、原 guider 类、一步一次委托计数、冻结的每步强度表身份；50 次实际进入/完成及错误。
- 完整初始 noise、common/entry/terminal RNG；每步 before/after RNG SHA，沿 S70 记录。仅相同 seed 不够。原参数/缓冲区字节与训练模式前后身份继续保留。
- LAST_STEP.npz：x_tilde、cfg_clean_raw、cfg_clean_used、sigma_hat、next_sigma、原 sigma、all8_step_output。两个 sigma 向量保留实际 [8]，不能以 JSON 浮点或一个标量替代；gamma、step_index、dtype/device、各数组 body SHA、形状/字节另记 JSON。
- warp_latents、latent mask、history_slots 的实际保存量和来源/编码身份；历史/无支持位置融合前后 exact 字节检查。四目标对应顺序不可从输出好坏重排。
- Gterminal：G0 末步来源身份、重演无融合与原输出的 exact 结果、terminal_z、四目标原始/量化 RGB、真实解码次数与耗时，重演前后 RNG。原 G0 结果保持原样。

“无数值/RNG改变”现在是源级设计目标，不能因委托看似简单就预写验证成功。实现后最少用人工张量的原采样器与代理对照：同输入/真实 RNG 状态、零融合 exact 返回、末步重演 exact、历史/零 mask 不变。实际新 G0 再记录上述完整状态；旧 S70 的成功重放不能替代新挂钩检查，也无需为检查新挂钩额外再跑一次完整 G0。

## 5. 已读范围、身份与交接

已恢复 AGENTS、原则 v2.11、记忆头部和主账最新 S85 接受记录；记忆头部此时仍为 S84 截点，最新完成以主账及 root 新消息为准。当前实际核读 sampling.py 1–460；S70 runner 的加载 55–117、RNG/采样/解码 222–410；原 do_sample 全函数、tensor_to_pil 全函数；AutoEncoder 全文、S82 pure fusion 全文；S70 PROTOCOL 及 S85 NEXT_CONSUMER_CONTRAST/ROOT_CONSUMER_SOURCE_REVIEW。没有声称读完所有源码或历史结果。

本次从源码字节计算的 SHA 均与 S85 根审来源记录吻合：

| 相对 R 的文件 | SHA256 |
|---|---|
| work/S20_environment/isolated_vmem_source/modeling/sampling.py | dc07ca0ba571ba5fb48f9856515d2cb7dea25254008a6f8b315538817f352b24 |
| work/S20_environment/isolated_vmem_source/utils/util.py | 30a97451f7a895e99ab881e97249f564e6b97eca2b5ea4d8f83953c26c4cf65e |
| work/S20_environment/isolated_vmem_source/modeling/modules/autoencoder.py | ccb94f107fd07302fa34593f7b840b3066f73548fe800e647eccfd66da473807 |
| work/S70_fixed_context_generation/generate_fixed_contexts.py | ba3a5fb9954e10b51bc56b717fe3de213728560f5dd3c6bc7e319594f1391b92 |
| work/S82_history_geometry_guidance/latent_geometry_guidance.py | 11f9f53c3ce40d0d040deb8e08fa042f5fafe8c477dc43de166c94fc416d5c2f |

下一步直接实现这两个局部包装和末步重演函数，再冻结 warp 编码/mask、强度日程与一次生成合同。不新增采样框架，不改 S70/S82 原文件；主账和真正执行由 root 负责。Gguide 比 Gterminal 的差别是较早融合及其后续传播，在独立参考评分前没有收益结论，也不是新方法验证。
