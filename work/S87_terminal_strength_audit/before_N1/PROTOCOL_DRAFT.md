# S87 有限末端强度审计草案

状态：**DRAFT_NOT_EXECUTED**。起草实际开始：2026-09-10 22:28:36 UTC。本批只读既有文本/源码/回执；没有读取或哈希真实 NPY/NPZ/权重字节，没有写科学执行器，没有运行模型/评分。未来由 root 按已有用户授权与证据决定实施，不增加用户审批关卡。

## 1. 问题、固定范围与不变项

唯一问题：在 S86 同一已见静态场景，普通末端处理换成另外三个预先列出的强度，能否达到当前 Gguide 的 RGB MSE？这是事后否证对照，不是找新的生成方法，也不识别纯时机或等累计剂量效应。

固定两族 Gpaste、Gterminal，各 λ∈{0.5,0.75,1.0}；一族一强度的四目标共享同一个 λ。共 **6 个新策略、24 个新 frame 行**。仍用历史槽 [19,18,13,12]、目标槽 [20,21,22,23]；8 槽顺序前历史后目标，576×576、CPU FP32、8 线程/1 interop。无 denoiser、无新 warp、无几何/检索/深度优化、无新噪声或回溯修改 S86。不从当前 Gguide 中间状态派生。

旧 S86 的 **16 行原样引用**：G0、Gpaste(.25)、Gterminal(.25)、Gguide(50步.25)。联合呈现是24新行+16旧行，标清来源批次。G0 是原始完整链，**不是本轮 Gterminal(λ=0) 新重演**；本草案不新增 λ=0/.25 解码臂。既有回执曾核无融合末步 Euler 一致，不等于新进程已重演，也不将旧记录重复计为 S87 运行。

## 2. 固定输入身份：均从已接受回执转录，执行时再核字节

本节根目录记为：

- R = /Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling
- E = R/work/S86_fixed_warp_consumer/execution_01

S86 全局 RECEIPT.json SHA 为 2fd8749808c617a5583163e929fa3310e458c029c9b9e7c96cbe7f754efe694a；G0/receipt.json 为 4ab7fb0553bee32b5971c62f89184b6bbcf32b0373a3bb94fcd046a0bffb6f07。S86 ROOT_RESULT_ACCEPTANCE 已于 22:22:37 UTC 接受保存量/描述分数；本次主记忆头部仍有较旧运行文字，以该新接受与主账为准，不改主入口。

### G0 最后七个张量

固定容器 **E/G0/LAST_STEP.npz**：2656062 B，文件 SHA **2dc7eb4cbc23eae7faad3a1e5234319340ae078606e849f9fa91e2c1cd806c8b**。元数据 mode=G0、step=50、complete=true、gamma=0；不得凭文件名补造这些属性。

| 字段 | FP32 shape | 回执中的连续 body SHA-256 |
|---|---|---|
| sigma | [8] | ceb3c4bde54c2bb40719844c68afe749c3a99beb0faa6cf44da78ab70e4339dc |
| next_sigma | [8] | 66687aadf862bd776c8fc18b8e9f8e20089714856ee233b3902a591d0d5f2925 |
| x_tilde | [8,4,72,72] | 8e91aa2efe8afe0e65a42e16409039a3b697fede2e5eeb37494d8a70b09abfe5 |
| sigma_hat | [8] | 96d4358530621da453ae0efde9a2330a9ff4329c1355e88bda1f76b98eb97e0f |
| raw_clean | [8,4,72,72] | 5df172e4cc4e67c15b99fdb78d3bdd0fe06a59b0094defce5fda897335c007cc |
| used_clean | [8,4,72,72] | 5df172e4cc4e67c15b99fdb78d3bdd0fe06a59b0094defce5fda897335c007cc |
| output | [8,4,72,72] | d9aebb4a0fe69731f9b90a6bd7ef8efd45734c69cbed8598ac72598e2f7bd624 |

执行输入核验必须确认所有有限、next_sigma 全零、sigma_hat 正、raw_clean 与 used_clean 字节相同；shape/浮点类型与回执一致。保留 sigma、used_clean、output 作为身份/一致性证据，实际新融合以 raw_clean 为起点，实际 Euler 使用保存 sigma_hat，不能重新近似或删除原 1e−6。

### S86 固定 warp 与两种 mask

**E/ENCODED_WARP.npz**：830240 B，文件 SHA **170159f1d87544f60823ec5149cdf323d7a150de2f440c25f3d160aa08dd8f86**，包含：

| 字段 | 类型/shape | 回执 body SHA-256 |
|---|---|---|
| W = warp_latents | FP32 [8,4,72,72] | 4d6113676ee7a63e028b91793405c83a7c9102390deba06a4ff7de688effbde3 |
| m = support_mask | FP32 [8,1,72,72] | 4ed52bc2aaec43e1f61b9f69a1e97af5287b5a3a5f76e99212ae9e223e28687a |
| history_slots | bool [8] | 4feae453a4b5733973a12e53d140b0a32cdfc624351168d693b6083f7a74d646 |

W 是已编码/已乘 .18215 的固定 latent；m 是 576 bool 支持的非重叠 avg8 分数覆盖，非置信度。前4 history 槽保护且 W/m 为零；不得换 min-pool、阈值/形态学、孔洞填色或重新编码。

| 其他直接输入 | shape / bytes | 文件 SHA-256 |
|---|---|---|
| E/warp_rgb01.npy | FP32 [4,3,576,576] / 15925376 B | aa8bd7de61135d8235600c8edba186404333f8664ca4ba55e24ca9a303c64ed8 |
| E/image_mask.npy | bool [4,1,576,576] / 1327232 B | 7b568a61a70136df3f88a84d5d5bdc76d4eba9e0b37e3ed892384da4fce30209 |
| E/G0/targets_fp32.npy | FP32 [4,3,576,576] / 15925376 B | b3776a65159b2989a00c5299d8e77811b0b144eb776dcab0ecd49553a1d0ec41 |
| E/G0/all8_latents.npy | FP32 [8,4,72,72] / 663680 B | 85772cd3fda7d8f0121f7e04ec5a315ee1de17c145027864408aa7b90113c286 |

image_mask 的 shape 已从 S86 RECEIPT.image_mask 核得 [4,1,576,576]，bool body 为1327104 B，body SHA 为 5e2db43e1737ad7b2aec1ac181ec79032d326c060ef0d8c43bd8c71ebbac1cdf；不是根据文件体积推断。本草案区域规则对应四目标的 576×576 bool 平面。G0 all8_latents 用于核保护位置的末态；本批只取得文件身份，未读其值。原 S85 大型几何 NPZ 不作为 S87 必需输入，避免为了重复已接受 warp 来源而再读取全部投影档案。

## 3. 两个末端族的唯一变化

**Gterminal(λ)。** 复用 S86 sampler_hooks.py 的 replay_last 和 S82 融合函数；先用同 m/history 规则得到 d′=(1−λm)d+λmW，零权重/历史槽保留原 clean 字节。继而逐语句复用原 sampling.to_d 与 Euler：

derivative = to_d(x_tilde, sigma_hat, d′)；
dt = append_dims(next_sigma − sigma_hat, x_tilde.ndim)；
latents = x_tilde + dt × derivative。

必须保持原 FP32 运算顺序，不以“最终等于 d′”替代真实算术；零干预位置的新末态核原 G0 output/all8_latents。每强度保留 clean_used、all8_latents，再 **完整8槽、chunk_size=1 解码（8 decoder chunks）**，最后取后4目标；不能只解4目标冒充同原流程。λ=1 时，只有 m=1 的相应 latent 位置是全量融合，不能推断某块 RGB 完全等于 warp。

**Gpaste(λ)。** 完全复用 S86 次序：从 G0 raw FP32 逐帧判断 min<−.1，成立则 (x+1)/2，否则原值；先 clamp 到 [0,1]；令 w=λ×image_mask，以原 torch.where(w>0,(1−w)×G0_RGB01+w×warp_RGB01,G0_RGB01) 形成结果。不能从 G0 uint8 做混合、先量化后再贴，或去掉原 clamp。m 不用于 RGB 族；两族同 λ 不代表同实际图像剂量。

**VAE 只加载既有 ft-mse 变体。** 固定来源 stabilityai/sd-vae-ft-mse，revision 31f26fdeee1355a5c34592e401dd41e45d25a493；原 SD2.1 VAE 身份仍 UNKNOWN。本地 config R/data/vae_official_ft_mse/config.json：547 B，SHA 92d3dfb746fca211a2c9e019e285f8597412211728dce3c5bcf4eda0f2d62e7e；同目录 diffusion_pytorch_model.safetensors：334643276 B，SHA a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815。使用原 wrapper 的 decode(z/.18215).sample，eval/frozen/inference，原 chunk1；不下载或偷换回原构造器所写 SD2.1 权重。S87 不需加载 VMem 去噪网络。

源审锚点：S86 generate_with_fixed_warp.py 179–184、300–322；sampler_hooks.py 168–189（SHA 2521dac2e07d0809eaecf23c37e6f41a5d157435ef7e5d010eec8ce840933ae4）；S82 fusion SHA 11f9f53c3ce40d0d040deb8e08fa042f5fafe8c477dc43de166c94fc416d5c2f；原 sampling.py SHA dc07ca0ba571ba5fb48f9856515d2cb7dea25254008a6f8b315538817f352b24；autoencoder.py SHA ccb94f107fd07302fa34593f7b840b3066f73548fe800e647eccfd66da473807。新执行器还不存在，不能把这些旧 SHA 当作未来执行器已冻结。

## 4. 量化、完整分母与参考读取顺序

沿用 S86 SCORING_CONTRACT.json（SHA 7cebfeb86b3e86b68fede211c5da496367746227eeddfc709b19ad060a25c787）和原发图转换：CHW→HWC；逐帧 min<−.1 分支时 (x+1)/2；乘255、clip[0,255]、astype uint8 截断，**不四舍五入**。保存全部 raw FP32、uint8、分支/范围元数据；先核二者逐字节相符，再打开固定参考。raw 非有限、shape错误或转换不符都使该策略不完整。

固定参考仅为 R/work/S70_fixed_context_generation/scoring_01/transformed_targets_uint8.npy：3981440 B，SHA e144e842fc36c795baa05841761670555a21bc7b9c36e0a56b8440b6a2324442。这是已见参考。生成侧不读参考；6策略全封存并绑定 SHA 后，评分侧才读。虽然研究者已经见过旧分数/图片，仍保持执行器输入隔离，不谎称恢复盲评。

每目标 full=331776 像素/995328 通道；每策略四目标总通道3981312。SSE 用整数累计，MSE=SSE/(通道数×65025)，full 主量四帧等权。

| 目标 | support 像素/通道 | hole 像素/通道 |
|---|---:|---:|
| 20 | 312396 / 937188 | 19380 / 58140 |
| 21 | 292217 / 876651 | 39559 / 118677 |
| 22 | 267572 / 802716 | 64204 / 192612 |
| 23 | 263594 / 790782 | 68182 / 204546 |

区域固定为旧 bool image_mask 及补集，不随新图重算。逐帧空区 NA；任何缺失帧不缩减平均、不填零、不筛好点。区域并报完整四帧等权均值和按像素合并均值，标清不同权重。无配准、曝光/尺度拟合、边界修剪、新边缘指标或临时选主指标。

必出24新行×full/support/hole，6策略摘要，6个相对 Gguide 的完整四帧差及24个逐目标差；旧16行只引用其已封存 FRAME_SCORES.csv（SHA 58aca1dd8e734819c4695c4d2aeda97bccc750fb5407fc32d0d49c45280b99a5）。每行含 batch/family/λ/target、完整分母、SSE/MSE、status/缺失原因。独立结果视图显示“24新+16旧”，不能统计成40次新生成或新独立样本。

## 5. 主停标准、重影保留与不再细扫

S86 Gguide 四目标总 SSE = **13571317266**，mean MSE=.05242222252907684。对每个完整普通策略 c 定义 ΔSSE_c=SSE_c−13571317266：

- 任一 ΔSSE_c≤0，只是否证“取得当前 MSE 需要多步引导”；不抹去 Gguide 胜旧 .25 对照，不把普通末端说成感知冠军，也不宣称跨场景替代。
- 若六个完整策略都 ΔSSE_c>0，只说明这个有限族没有达到当前 MSE；不证明胜连续最优 λ、剂量解释消失、几何正确或新方法成立。
- 有失败时逐项报 INCOMPLETE。已完成的反例若达到≤0仍可报告该反例，但不能声称已完成全六族/整个包络；不能因已有一个反例就丢弃其余预定结果。若资源或程序失败触发停止，保留未运行策略状态，不自动重试。

仍保留 S86 非盲人工看到的重影/形状模糊。新导出使用相同固定目标顺序、全图同尺度同时呈现6新策略与旧图；不挑最清晰裁剪替代原图。原 MSE 不变；人工观察单独记录为有/无可见现象及范围，不升级成新的定量“感知分数”。即使 MSE 最低，双边缘/涂抹都必须展示。若只完成缩略图查看，写清分辨率，不冒称原图逐页验收。

全四目标共享 λ；严禁逐目标/区域挑 λ。可以列两族各自及合并后的最低均值，**必须标记为已见参考上的事后有限包络**，不能当验证集/跨场景成绩。无论成功或失败，{.5,.75,1} 之外不自动插点、二分/连续优化、不扩 mask/孔洞色/采样日程；不得看曲线再补一个“刚好更好”的强度。本批收束后由 root 根据明确未解问题决定下一有界任务，不以继续追最低 MSE 替代形状与相机问题。

## 6. 明确资源草案与保存

原 S86 Gterminal(.25) 回执记一组8槽解码及派生保存 16.73506 s（已加载模型）；不能把该时长当新冷启动保证。拟定资源如下，正式冻结前由实现者核本地可行性：

| 项 | 本草案固定建议 |
|---|---|
| 设备/版本 | CPU FP32，8线程/1interop；复用 .venv-cut3r 的 torch2.7.0、NumPy1.26.4、diffusers0.32.2、Pillow10.3.0；只加载一次既有VAE |
| 科学调用 | 0 denoiser/0 geometry/0 encoder；3组全8 decode，共24个chunk1 decoder forward；3组RGB处理；不创建新随机样本 |
| 派生阶段上限 | 总600 s；单个terminal120 s；RSS16 GiB；开始可用磁盘≥2 GiB；新产物≤1 GiB |
| 评分/复核 | 沿用独立算术思路；评分120 s/RSS1 GiB，独立复核同量级上限；不再运行VAE/原模型来冒充统计复核 |
| 超限 | 停止并记录失败/未运行项；不自动加大上限、改chunk/精度/设备、续扫或重试 |

这些是**草案预算，不是测得成本或已冻结可执行合同**。正式执行前一位实现者将选择顺序明确为按 λ=.5,.75,1，每档 Gpaste 后 Gterminal；记录加载、各策略、全部解码chunks、量化、保存、评分、复核的实际起止与峰值资源。只测实际派生阶段 RNG 是否变化，不把模型随机初始化消耗误算成新生成噪声；初始化完成后存 RNG 快照，eval/inference 派生应不抽样。

每策略保存 raw/uint8、输入与输出文件/body SHA、实际转换分支；terminal 额外保存 clean_used、全8 latents、实际decode计数。保护历史/零mask的 clean 与 latent逐字节核，不能从latent保护推RGB局部不变。保存各λ成功/失败/未运行状态、异常、资源及输出字节，旧档案只读。所有新产物在 S87 独占目录，不能覆盖 S86。

## 7. 执行前只需完成的独立审查

1. **实现者准备短执行器与正式合同。** 绑定 image_mask 的上述真实回执 shape，确定 VAE-only 本地加载方式、原helper依赖及禁联网，锁新源码/环境/输入身份；避免导入旧完整runner触发VMem加载或运行。
2. **不同作者做一次实质前审。** 核7tensor/W/m/槽序、三档两族、FP32 Euler/量化顺序、全部8解码与24行范围；用人工小张量检查zero/history保护、λ=1分数mask及uint8边界，不重跑旧成功实验或读参考挑例。
3. **独立保存量检查与评分计划。** 新派生封存后，另一实现复算三档clean/Euler、RGB混合、raw→uint8与整数SSE/分母/差号；未来若只复算算术而未重跑VAE，清楚标该边界。冻结容差沿原同顺序FP32算术要求精确；展示浮点分数容差复用S86规则，主停用精确整数符号。

前审/正式合同/执行器均待完成，不能将本草案描述为“已准备开跑”。本批唯一写入为此设计文件，科学与 canonical entrypoints 未改。
