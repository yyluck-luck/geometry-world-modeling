# 下一次最小模型对照：复用历史 latent，新增 VAE 解码

记录UTC：2026-09-09T08:05:07.488361+00:00；作者：/root/next_control_feasibility。此次仅源码、JSON元数据与目录清单审查，未读取PNG/NPZ/NPY或大权重正文，未导入模型，没有产生新实验结果。实际开始时刻未单独采样，不能把下方记录时间倒填为开始时间。

## 二选一结论

**现有保存输出不能回答“ft-mse VAE 回环本身是否造成同类取景偏移”。建议下一步复用 S68 已接受的五个真实历史 latent，新增一次仅 VAE 的解码对照；不要重做五次 encode，更不要重新运行 S70 三臂。** 这是明确局部竞争解释的组件诊断，不是新算法。

| 选项 | 能回答什么 | 新增操作 | 裁决 |
|---|---|---|---|
| 直接依赖现有输出 | S68 证明五次编码实际完成、来源及shape/finite绑定；S70证明三臂实际执行并将全8 latent 解码，且A0/A1精确重放。 | 0模型 | 不足：S68只保存latent/embedding/K，未保存重建RGB；S70只保存target RGB，历史槽的decoded RGB未保存。数值finite和重放不证明重建取景正确。 |
| 历史照片回环 | 给定既有编码 E(x)，测 D(E(x)) 与同一预处理真实x的空间位置/外观偏差；可检验该组件是否在这五张历史图上引入大偏移。 | 一次本地334,643,276B VAE权重加载；五次已有latent的decode；生成五份重建与同预处理参考，独立离线评分。无需CLIP/VMem、无需新encode或50步采样。 | 推荐；若预算只允许最小单例，可预先固定历史19，但五图更好且来源早已固定，不能结果后挑最好图。 |

## 精确可用输入和原操作

- `work/S68_tum_vmem_cache_bridge/execution_01/history_{12,13,14,18,19}.npz`：每份字段 `latent` FP32 `[4,72,72]`、82,944B；`embedding` FP32 `[1024]`；`K_pixels_576`、`K_normalized_576`各 `[3,3]`。只需要latent，禁止将source ID当紧凑行号。每份伴随JSON记录整个NPZ SHA、逐字段body SHA、真实PNG路径/SHA和 `image_tensor_sha256`。本次只读JSON，未读取或解码NPZ。
- 历史19的NPZ SHA `61c8ddd761ffd4fddf955c161ee2cb6af494dbc481a4933f760a2339c964a8e9`，latent body SHA `ec1b8f5df7d1711c4e63fb28bedf3cab690f55de68a09f6259a2b61a9262ad6a`。其输入PNG为 `data/tum/fr2_desk_timestamp_guard/rgbd_dataset_freiburg2_desk/rgb/1311868171.663411.png`，元数据SHA `c7127660fd25468f35db330cc3200bf68451cec4e13adef640ee7b16c27f32ee`；预处理tensor SHA `9190d2c4978a23c9b5247a27122016b29182b827717d7de2f926c7f97fd75757`。
- 组件取S68/S70共同 `INPUTS.json.components.vae_config` 和 `.vae_weight`：`data/vae_official_ft_mse/config.json` SHA `92d3dfb746fca211a2c9e019e285f8597412211728dce3c5bcf4eda0f2d62e7e`，权重 SHA `a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815`。这些是本次读取元数据里的既有pins，本次未重新读取大权重核SHA。
- 原wrapper `work/S20_environment/isolated_vmem_source/modeling/modules/autoencoder.py`：encode是posterior mean×0.18215，decode是 `module.decode(z / 0.18215).sample`。因此缓存latent已经包含scale，不能二次encode、额外乘scale或重复除scale。保持CPU FP32、eval、chunk_size1、无tiling/slicing和原wrapper解码路径。
- 参考RGB应由原 `load_img_and_K` / `transform_img_and_K` 对同五张历史源执行原Torch FP32 area覆盖缩放至768×576、中心裁剪576×576，并比对每张S68 `image_tensor_sha256`。不能用uint8 OpenCV预处理替换。参考和重建明确统一[-1,1]或[0,1]单位；不要用frame.min触发的分支暗改展示尺度。

## 为什么S70旧文件不能替代

`generate_fixed_contexts.py` 第358–375行确实调用原 `do_sample` 全8解码，随后 `target = samples[~input_masks]` 仅保存 `targets_fp32` 与 `targets_uint8`；第349行保存的 `all8_latents` 是采样器输出。三个arm的实际receipt均只列这三类数组，目录清单无历史重建RGB。不能用“曾经解码成功”推定被丢弃的历史图像取景正确。也不应直接将采样器前4槽当作原S68 latent；若要这样用，须另证槽值相等，但它没有比直接解码已接受S68缓存省模型调用。

## 判读边界与停止条件

1. 若五张历史回环保持取景、只有小重建差异，可削弱“该ft-mse VAE在这些真实编码latent上普遍制造巨大取景变化”的解释；**不能排除模型生成latent离开编码流形时的解码异常，也不能证明其latent与VMem训练期latent兼容**。
2. 原SD2.1 VAE身份始终UNKNOWN。ft-mse自洽重建好，不等于原SD2.1组件相同或可互换；同一VAE可补偿自身编码/解码，但不匹配另一个模型学得的latent坐标。
3. 若回环出现同类偏移，说明VAE/预处理/解码/展示链值得查，不能单凭它定位权重本身；先查统一单位、crop、scale及绑定。不按结果替换原S70分数。
4. 冻结全部五图、主位移与可用匹配分母，并保留逐图MSE/失配/长尾；SIFT对应仍非真值，同视图匹配不能拟合几何变换后才报“恢复”。科学数组与图像读取由root另行冻结新协议后进行。
5. 一次新增decode已足以回答上述窄问题；结束后进入能区分生成器条件遵从与组件域不匹配的下一决定，不把组件检查扩成无限循环。此次尚无新运行、无创新验证。

应用技能：`/Users/rocket/.claude/skills/sci-scientific-critical-thinking/SKILL.md` validity/control/measurement段；具体用于区分有限重建质量、生成latent分布和组件身份三种不同主张。
