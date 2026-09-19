# S48 post-selection hook 与 source-support 可行性源码审计 V1

- 审计时间：2026-09-08T14:16:45+08:00
- 审计对象：`vendor/vmem_snapshot/modeling/pipeline.py`
- 对象SHA-256：`90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`
- 证据类型：源码静态审计
- 模型运行：0
- C1/C2 tensor、image、pixel读取：0
- 授权：只定义待审hook和可证伪预测，不授权S48 arm，不授权新颖性或方法主张

## 1. 直接结论

当前源码存在一个可用的post-selection、pre-conditioning边界，但现有返回值不足以执行S48：`get_context_info`返回被选历史帧、latent、embedding、camera/K和`context_time_indices`，没有返回产生选择的surfel map、source-specific target support或多值source归因。因此必须先增加只读观察字段和受控替换点，并重新做源码双审。

同时发现一个可证伪的机制不对称：

- latent/replace路径按历史slot保留来源：`context_latents`在第1145–1155行按slot写入`c_replace`；
- semantic/cross-attention路径在第1124行先对全部`encoder_embeddings`做`torch.mean(..., dim=0)`，再于第1149行把同一个均值token广播到所有camera位置；
- camera geometry在第1135–1178行由Plücker、mask和camera/K单独进入`concat/dense_vector`。

所以“历史被选中”并不自动意味着semantic路径仍能区分是哪条历史来源。该源码事实支持一个实验假设：**slotwise latent influence可能存在，而source-specific semantic localization可能因全局平均而扩散或互相抵消。** 它还不是质量失败、因果结果或创新证明。

## 2. 当前调用链与精确边界

1. 第639–646行把全部surfels渲染到平均target pose，得到`depth`、`surfel_index_map`和`cos_value_map`。
2. 第647、462–502行把每个可见surfel通过`surfel_to_timestep`累加到历史timestep，形成frame relevance/count。
3. 第655–753行按relevance、pose距离和NMS得到`context_time_indices`。
4. 第754–765行按这些indices取出每个slot的c2w、latent、embedding和K并返回；这里未返回support。
5. 第1249行调用`get_context_info`，第1251–1260行解包。
6. 第1262–1267行拼接camera/K并调用`get_cond`。
7. 第1123–1187行把appearance与geometry变为模型condition。
8. 第1269–1284行执行采样；第1286–1310行把生成结果写回latents、embeddings、camera/K、PIL帧和surfel memory。

唯一允许的hook位于第1249行普通选择已经结束之后、第1262–1267行任何conditioning构造之前。F11在这里对冻结目标source RGB副本重新编码，替换该slot的latent和embedding副本；不能改原始state、selection、pose、K、surfel或非目标slot。

## 3. `post_selection_bundle` 必须物化的字段

hook返回的记录至少包含：

| 字段 | 定义 | 失败条件 |
|---|---|---|
| `pipeline_sha256` | 本次实际导入的pipeline源码 | 与G7不一致 |
| `selected_slots` | 有序slot、`context_time_index`、稳定source ID | 长度/顺序与context tensor轴不一致 |
| `retrieval_surfel_index_map` | 同一次普通选择的z-buffer可见surfel索引图 | 重新渲染结果代替同次调用 |
| `surfel_to_all_sources` | 每个可见surfel对应的全部timesteps | 丢弃多值映射或事后选source |
| `source_pixel_weights` | 每个被选source在target pixel上的稀疏权重 | 非有限、shape错或权重和不闭合 |
| `appearance_axes` | latent与embedding中slot/source的轴和shape | 不能唯一定位目标slot |
| `consumer_paths` | `replace`、`crossattn`及静态审计发现的所有appearance后代 | 任一路径未列入F11 |
| `injection_trace` | arm、source、slot、edit、dose及各路径替换前后SHA | F11路径不一致或非目标量变化 |

这些字段必须来自同一次选择调用，不能在选择后重开科学输入路径再估计。

## 4. 多值surfel到source的冻结归因

令`q(p)`为同次`surfel_index_map`在target pixel `p`上的可见surfel，`T(q)`为其`surfel_to_timestep`列表，`U`为普通运行被选中的唯一source IDs。定义：

`A(p)=T(q(p)) ∩ U`。

对source `i`的权重冻结为：

- 若`i∈A(p)`，`w_i(p)=1/|A(p)|`；
- 否则`w_i(p)=0`；
- `q(p)=-1`或`A(p)`为空时，该pixel不属于任何被选source support。

`S_i={p:w_i(p)>0}`。同一pixel由多个source共享时保留分数权重，不复制成多个独立pixel。重复slot引用同一source时保留slot列表，但support只按唯一source计一次。若目标source没有非空support，或任何`T(q)`包含越界source ID，G3停止。

这是VMem当前surfel合并语义下的确定性操作规则，不等同真实物体分割或唯一物理所有权；论文只能称“VMem retrieval geometry implied support”。

## 5. F00/F10/F01/F11 的实现合同

- `F00`：原slot latent与原slot embedding副本。
- `F10`：只替换目标slot embedding，随后仍经过第1124行全局mean；latent保持原值。
- `F01`：只替换目标slot latent；embedding保持原值。
- `F11`：同一个edited RGB副本分别经过冻结image encoder和VAE，替换目标slot的embedding与latent。

所有arm必须从同一只读state snapshot启动fresh process。第135–146行的现有`reset()`没有清空实际使用的`latents`、`encoder_embeddings`、`c2ws`和`pil_frames`，禁止用它恢复arm初态。

F11之后第1123行开始的`get_cond`、第1269行开始的sampler、以及被保留的writeback后代全部自然重算。若为了方便复用F00的`cond`、attention、denoising state、latents或输出，估计量被切断，结果只能叫工程诊断。

## 6. 预注册的源码级预测

### P1：consumer asymmetry

在合成shape/trace测试中，编辑一个slot必须只改变该slot的`c_replace`输入；同一编辑会改变全局mean后的`c_crossattn`，而其他slot无法保留独立semantic token。若trace不满足，hook无效。

### P2：path conflict

若真实pilot中F01稳定响应、F10很弱或空间扩散，而F11不等于简单数值相加，这支持“slotwise latent与global semantic路径不对称”的架构诊断。它不自动说明哪条路径提高质量。

### P3：geometry localization

只有F11的每个预定family/seed效应都超过replay与面积门，并进入预冻结matched-placebo library描述性前5%尾部，才保留geometry-localized influence。attention图或retrieval count不能替代输出干预。

### P4：signed benefit

即使P1–P3成立，也必须用独立reference和双向common-visible support得到稳定`B_local/B_matched`符号，才能讨论接受或拒绝某条memory source。

## 7. 可能的方法路线与最近工作边界

若P1–P4在跨scene confirmation中成立，才允许评估一种source-preserving conditioning：保留每个source的semantic token，用其VMem-implied geometry support约束token到target区域的作用，并用离线signed-benefit标签训练轻量accept/re-observe决策器。

这条路线的单独组成均已有强近邻：I3DM已有3D-aware retrieval与reliable-region injection，I²AM已有reference↔generated双向attribution，TetherCache已有选择/修复/gate，CUE-R已有逐item干预和signed utility，SelectiveNet已有risk–coverage。因此潜在贡献只能来自经过确认的联合机制与强基线无法解释的规律，不能把source token、geometry mask或gate本身称新。

## 8. 下一步与停止条件

1. 为上述字段写最小observer/controlled-replacement patch，只做静态和合成测试。
2. 双审精确源码、所有consumer路径、snapshot隔离和fail-closed行为。
3. 完成C1盲评分和强制C2；没有合格自然失败则S48停止，不运行arm。
4. 若有失败，再做无生成输出的support/matched-placebo feasibility；不能得到稳定source support或199个placebo则停止。
5. 只有V3与完整G7 fresh review均PASS，才允许单个CAL unit的最小Pilot-A。

