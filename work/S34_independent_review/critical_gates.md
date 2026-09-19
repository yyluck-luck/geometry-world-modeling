# S34 独立前审：实现前的必要门

当前仅完成已选协议与原源码审查，**不是 producer/consumer 可执行代码 PASS**。待两位作者交稳定文件后只做一次完整 source/contract 前审；无数组、RGB/GT 字节读取、模型或优化执行。

本轮沿用 Supervisor 2.2 的强 baseline→失败→根因，以及本地 Claude scientific-critical-thinking 的对照、混杂、构念效度检查。首先公平检验“冻结旧深度已经足够”，不把共同尺度归一化包装成创新。本文件只列会影响这项判断的门。

| 门 | 稳定代码和合同必须证明 |
|---|---|
| 1. 混合来源真实 | old4 来自 S29 C2a `initial_decoded/initial_raw` 的零步预测；8 图头为 S26B 指定 CUT 前缀。各自完整 SHA/六头/原 PIL/star 来源明确，不能要求或声称两种前缀逐字相同。新 adapter 使用真实 `S29_C2a_saved_MST_zero_step`，不冒用旧400 provenance。S29 原输出尚未 clean；common packet 只在副本新 clean 一次，保存原 raw conf 与新 conf。 |
| 2. 共同相机/初態/消费量 | 已封存同一 optical c2w 八帧共同输入，旧4 prefix 实际核对；pipeline 表示仅在需要时翻一次 Y/Z。两个新8图/7edge scene 的完整非空 raw 名/shape/dtype/flags/bytes、decoded/objective、实际 consumed heads/weights 在首步前一致。零步来自自由臂同一内存初态，clean 深拷贝不能改变训练实例、conf 或消费权重。不得沿用四图33项/三边硬断言。 |
| 3. 旧深度确实冻结 | preset/MST/400/clean 每阶段核旧0–3注册参数同对象、同名、同 raw bytes，requires_grad=False，梯度 None；新4–7保持训练、全部400步 grad finite/non-None（0 norm合法）。给定相机/pp冻结；全部8 focal仍按原语义训练。输入 depth 与 log→exp decoded 仅按预定 atol/rtol=1e-5核，不覆写输出伪过门。旧 focal 变化导致 decoded world 变化与旧depth冻结分别记录。 |
| 4. 七边约束与真实计数 | 仅受控臂在共同 MST 后固定七条 raw log scale 均值 m0，current mean 不 detach，factor初態=1，norm_pw_scale=False，原有效 scale 乘完整3×4。七边相对比例可训练，每步 mean/factor/相对比例记录完整；不只约束新4边。两臂各原400 Adam/.01/linear、403 objective、1MST/7PnP/1clean；总2MST/14PnP/800Adam，common/zero各1clean，总4clean。 |
| 5. 同一已提交旧图 | common old map 只构建一次、封存。每条件完整深拷贝 Surfel位置/normal/radius/color、每个可变source列表、c2ws与4项focal历史，不能浅拷贝列表。old图非空是只新增4帧的前提；原`.05`降采样、置信阈值/分位数、normal/radius/Octree合并保持。实际旧几何完整不变，匹配只追加source，未匹配才append。 |
| 6. 原缓存与票权公平 | 原all8 focal追加旧4→12，depth cache替换为all8；不同时修焦距缓存。start_idx=8−4=4只消费新4，source IDs保持0…7。固定第8给定相机自查询，原512×288渲染及自身历史平均focal×.65。三条件保留完整world/source/index/depth/cosine对应、合并/新增数及来源票权/候选配额，不用不同地图的整数ID差异直接解释几何优劣。 |
| 7. 消费边界不越界 | 原`process_retrieved_spatial_information`首次source赋值后又`+=`、`get_frame_distribution`余数分配`result[idx]=1`均保持原算术；本轮不修成另一票权算法。不能为满足理想的配额求和/唯一次贡献额外改代码。空图/无有效票权如出现，保留实际状态与失败/NA，不造候选。4→8缺len5 NMS初始阈值和真实latent/embedding，默认最终context IDs与生成明确NA。 |
| 8. 封存、评分和预算 | 完整三端点及实际consumer输出封存后才读新4 sensor GT；旧GT相机是允许输入，不称完全无GT。评分完整3×新4、原尺度/有效GT分母，失败和NA保留；不追加k、best step、GT renderer准确率。CPU8顺序：common120s/4GiB、两GA各240s/8GiB、三端点consumer合计120s/4GiB；评分CPU1/120s/2GiB，启动空盘≥10GiB。超预算保留失败，不自动降分辨率/换旧图/重跑。 |

原源码已经支持第3门的预期：`optimizer.py:227–242`只在 `requires_grad or force` 时写 depth，原 MST 未传 force；但这是源码预期，不代替未来实际冻结门。原 `ParameterStack` 会 detach 且由第一个叶子决定 grad，因此必须保留已验证的 torch.stack 注册叶 getter 修复，不能仅把最后返回 tensor 的 requires_grad 改 True。

最需要保持的解释边界：本次是一个已见约0.236秒的 4→8 consumer pilot。旧地图来自事后选定的较强普通零步，所有条件公平共享；结果只支持该 old packet 下的比较。冻结旧 depth 本身可能消除 S33 all-trainable 失败；若自由400已足够，接受该反例。地图/渲染/票权变化仍不等于更好选图或视频，不添加第四臂或继续在已见短窗调参。

精确阅读路径、范围、SHA与时间见同目录 `source_preparation_receipt.json`。作者源尚未交付时本文件不签发执行 PASS。
