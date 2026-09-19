# S70：固定条件三臂生成的最小源码方案

记录 UTC：2026-09-09T02:18:46.967449+00:00。作者：`/root/c2_v9_recovery_author`。**当前只是可实现方案，尚无生成执行源码包/新权重加载或启动；S69 回执为两套条件完成、独立 ray 结果仍由 primary 核验。不能将其写成生成已就绪。** 本文只读已存源码和 JSON 元数据，不读取权重、PNG、GT 或 S69 NPZ 正文。

## 直接复用的实际路径

从 S64 真实成功的来源复用 `VMemModelParams→VMemModel→VMemWrapper`、原 `AutoEncoder`、`DDPMDiscretization`、`DiscreteDenoiser(num_idx=1000)`、`create_samplers(...)[0]` 和 S20 已固定 CPU 适配的 `util.do_sample`。不是从内存复用已退出的 S64 模型：新进程须实际重新加载 VMem 与声明 ft-mse VAE。原 wrapper/网络/采样数学保持。

配置固定 CPU8/FP32、576×576、8 槽、latent C4/downsample8、完整50步、`cfg=2.0`、`guider_types=1` 即 MultiviewCFG、`cfg_min=1.2`。不能把 sampler 索引0误读为 VanillaCFG 类型0。原 MultiviewScaleRule 仍会依本臂 c2w/K/mask 决定近帧 scale，不能用全局常数替代。原 VAE 无 tiling/slicing、chunk1、scale_factor=.18215；`do_sample` 默认 `decoding_t=1`。

S69 输入映射只需两 NPZ 内 `c__*`/`uc__*`、`post_cond_optical_c2ws`、`K_pixels_576`、`input_masks`。这些已经是原 get_cond 的返回条件；不能再翻相机列或重新做中心化/scale。A0/A1 两臂都使用 geometry `[19,18,13,12]`，B 使用 pose14 `[19,18,14,13]`；末四槽严格映射真实目标20–23。S69 自然尺度及其下游条件全部随集合改变，不将 B 的相机或 ray 强行替成 A。

S69 元数据已封存的 NPZ SHA（本次未读 NPZ bytes）：geometry `ade8813c6c0b63f3570edf3452fa1d4d04ab62ebe8072640e54092e68b889ff7`；pose14 `e6d0865a1286ef0329469f48ff5e0e4477c83b2b6c2f99108528d670260540aa`。后续真正运行须从实际字节重新核 SHA 和每字段 descriptor，并绑定届时实际独立结果审查 SHA；本计划不填写未来票据占位 hash。

## 两份权重与最小新代码

只需已有本机：

| 组件 | 文件与字节 | 已封存 SHA256 |
|---|---|---|
| VMem | `data/vmem_recovery/xet_attempt4_01/vmem_weights.pth`，5056346672 B | `675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4` |
| ft-mse VAE | `data/vae_official_ft_mse/diffusion_pytorch_model.safetensors`，334643276 B | `a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815` |
| VAE config | `data/vae_official_ft_mse/config.json`，547 B | `92d3dfb746fca211a2c9e019e285f8597412211728dce3c5bcf4eda0f2d62e7e` |

路径均相对项目 R；权重 SHA 来自已成功 S64 manifest，本次没有重新读取大权重。后续 VMem 用已核同一 FD/bytes 经 `torch.load(...,map_location='cpu',weights_only=True)`，沿原 `.replace('module.','')` 键映射、strict=True、空 missing/unexpected；VAE 可复用 S68 的已核 bytes loader/原构造路由。无需 CLIP、CUT3R、Navigator、get_context_info、renderer、scene reconstruction 或在线缓存更新。ft-mse repo/revision 仍为 `stabilityai/sd-vae-ft-mse@31f26fdeee1355a5c34592e401dd41e45d25a493`，原 SD2.1 VAE 等价性 UNKNOWN。

一个小 `generate_fixed_contexts.py` 即可处理源/权重身份、两个组件、三个固定臂及实际回执；继续用 root 简单外部进程组观察器，不移植旧 C2 gate/prepare/attach/authorization 状态机。重要接点：普通 `import modeling.network` 会先执行 `modeling/__init__.py`，连带导入 pipeline/CUT3R。用受限的空 `modeling`/`modeling.modules` namespace 并从逐个已核字节依赖顺序加载原 transformer→layers→network，采样模块独立加载，AutoEncoder 与 do_sample 按已核原定义提取。原网络文件不改，fresh worker 不允许已有同名模块冲突。原 transformer 的 CPU attention 路径沿 S64 成功来源保留，不另换 backend/数学。

## 必须共享真实随机状态

原 do_sample:713 在 CPU `torch.randn((8,4,72,72))`；原 prepare_sampling_loop 会原地缩放该数组，所以观察器必须在调用原 sampler **之前**复制。原 sampler_step:393–396 无论 `s_churn=0` 都做 `sigma_hat=...+1e-6`、`torch.randn_like` 和噪声相加；50步后续 RNG 不能忽略。

最小办法：组件加载、输入解码、source checks 和 fresh sampler 配置准备完毕，设一次 seed44，然后把实际 Python random、NumPy legacy、Torch CPU RNG 状态以可恢复原值保存及哈希。每臂使用新条件副本、fresh 无累积状态的 denoiser/sampler；在 do_sample 前恢复完全同一状态，并核恢复后 byte SHA。用 S35 `archive_sampler` 同样的入口包装记录实际初始noise FP32 `[8,4,72,72]`（663552 B）与此时 RNG 状态，调用原 sampler 恰一次。实际 noise 三臂逐字节相同才满足共享噪声；不凭 seed 字面判断，也不改变 do_sample 的抽样公式。

另在原 sampler_step 外侧记录每步的 RNG 前后 SHA、step index/形状、返回量 finite 与实际50次计数；不 draw 额外随机数。保存公共完整初态和每臂终态，要求对应步 RNG 状态及最后状态相同。这与固定原 randn_like 路径一起核后续随机流，没有声称保存了未归档的每步原始 eps 数组。A0/A1 相同条件完整50步+解码重放，冻结前明确要求全8槽 latent 和四目标 FP32 RGB字节一致；不同则记录重放失败，不把 A/B 差归为 context 效应，也不事后改容差。B结果无论方向都保留。各臂复用同一已载入 eval/frozen 模型，记录参数/缓冲身份、版本与训练模式未变，不复制数GB模型三份；若发现模型状态变化则终止并记录，不能假称同模型状态。

骨架（非可执行程序）：

```python
network, vae = load_two_verified_components_only()
conditions = read_verified_S69_condition_arrays()
common_rng = seed_once_then_capture_actual_states(44)
for name, key in [('A0', 'geometry'), ('A1', 'geometry'), ('B', 'pose14')]:
    denoiser, sampler = fresh_original_sampler0_50steps_cfgmin1p2()
    data = independent_condition_copy(conditions[key])
    restore_and_verify(common_rng)
    samples, latents = original_do_sample(
        original_wrapper(network), vae, denoiser, observe_original_sampler(sampler),
        data.c, data.uc, data.post_cond_c2ws, data.K_pixels_576, data.input_masks,
        H=576, W=576, C=4, F=8, T=8, cfg=2.0,
        decoding_t=1, verbose=True, global_pbar=None,
        return_latents=True, device='cpu')
    save_all8_latents_and_only4_target_RGB(name, samples, latents, target_ids=[20,21,22,23])
```

每次原调用实际解码8槽，科学目标输出仅 `samples[~mask]` 四帧20–23，不把四context槽算新目标视频。可保存全8最终latent用于重复性核和四目标FP32 RGB/原tensor_to_pil量化后的权威uint8；不立刻显示图片或读取实拍目标。原全8 RGB临时返回约31850496 B、四目标15925248 B/臂；三臂输出几十MB，不以保存8槽重复增大科学分母。每臂先写 create-only 目录/输入及RNG身份，原采样/解码输出一旦返回即封存，错误/超时和未完成step不删除。两次 A 是重复性控制，不是独立科学样本；B条件变化包括整个context包，不单归因CLIP或检索。

## 资源、缺口和下一次实际决定

建议沿已成功 S64 的每50步1800秒上限、CPU8/FP32和45 GiB进程树RSS上限；三臂采样总上限5400秒，外部给加载/归档另留120秒，合计5520秒，≥10 GiB磁盘空闲。S64两批完整流程实际约2729秒；按批数粗略外推三臂约68分钟，仅作本机等待量级，去掉几何/CLIP后是否更快尚未实测。新实现不得为压时间减少步数/分辨率/槽数。root长时外控须保留活跃exec会话、周期查看真正进度，超限终止进程组并保留残缺；这里不推断旧SIGTERM来源。

目前明确缺口：①S69最终独立ray/PRE_RUN预测结果和root接受尚待绑定；②上述两组件最小loader、受限模块导入、RNG/采样入口观察器尚未实现和非作者源审；③实际本机资源预查与唯一新输出绑定未做；④三臂生成和A/A重复性尚未执行；⑤配对质量/独立参考评分与顺序规则须另行结果前冻结，不能直接套S42阈值或补旧C2/cohort。已见目标和近似K/未去畸变、GT时刻插值局限继续保留。

本计划不启动模型、不要求新权限流程、不改S64/S69原件或主账。root可据上面的真实资源量级与明确消费边界决定是否实现下一最小生产源包；当前仍 NO_METHOD_SELECTED / novelty_authorization=NONE。

## 本次实读来源小清单

以下 SHA 为此次实际源码/JSON bytes 核对；权重/NPZ hash 仅按上方明确的旧元数据来源引用。

| 项目相对路径 | SHA256 |
|---|---|
| `work/S20_environment/isolated_vmem_source/modeling/network.py` | `9ed21c2d804734d7ca2d81b1e596858835ca70a4a04abb9b5540b872515d4c9b` |
| `work/S20_environment/isolated_vmem_source/modeling/modules/layers.py` | `98f481aa59f8289e430018dbdbe928d8732b08fb977b14c22f6d7cb28bae5c38` |
| `work/S20_environment/isolated_vmem_source/modeling/modules/transformer.py` | `5f0d152a2f6464076cb0ee5aca725b3445420a5f37ac571d3daa77e580e65764` |
| `work/S20_environment/isolated_vmem_source/modeling/modules/autoencoder.py` | `ccb94f107fd07302fa34593f7b840b3066f73548fe800e647eccfd66da473807` |
| `work/S20_environment/isolated_vmem_source/modeling/sampling.py` | `dc07ca0ba571ba5fb48f9856515d2cb7dea25254008a6f8b315538817f352b24` |
| `work/S20_environment/isolated_vmem_source/utils/util.py` | `30a97451f7a895e99ab881e97249f564e6b97eca2b5ea4d8f83953c26c4cf65e` |
| `work/S35_generation_integration/runtime_factory.py` | `a7f812717c053b401433bac423ba0a63028a9dc1874b1cba3c4fbca6c276e3d0` |
| `work/S35_generation_integration/integrate_original.py` | `adf819e1cda3de4f830d2c3e5776664591607a0109d50f59cdc1addeb684b0ec` |
| `work/S64_unit_repaired_generation/runtime_adapter.py` | `711abdb32060b5aa1ba9213e810ca13ab6277db84a0d0984178baf163e836a70` |
| `work/S64_unit_repaired_generation/inference_seed44.yaml` | `90871e1df4d0569f52a8baa7919f66000ec2f1a4f9a9275a2e4fbe384a6a07b9` |
| `work/S69_tum_camera_conditioning/INPUTS.json` | `9b66b2f7b4449e11f400c342068d069e95b96caae84e659dc497123cb5e5238f` |
| `work/S69_tum_camera_conditioning/execution_01/receipt.json` | `9bc6539fed473e85b8cb2058c9f3ca6628c9603b4dd5c0160ce0a7cf71d610c7` |
| `work/S69_tum_camera_conditioning/execution_01/geometry.json` | `7d058f4dbafa9d4ffc914140b57564f51b4432b3171d3e75aa9266b0eae5d111` |
| `work/S69_tum_camera_conditioning/execution_01/pose14.json` | `92aaec59f0aa986ecbe29225850b021ea272288be66ce64ccb2bd73d4f0cbf58` |
