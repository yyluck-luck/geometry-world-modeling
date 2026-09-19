# S80 作者最终源码复查

身份：`s77_science_closure` 是 `run_observer.py` 的原作者。**本文件是作者复查，不能称为不同作者独立验收。** root 同时完整审阅，负责实际执行及另一个实现的保存量复算。本复查不新增审批流程，不修改冻结源码或合同。

实际开始时钟：2026-09-10T15:50:17Z；最后一次来源读取后时钟：2026-09-10T15:52:22Z。本轮只读源码/合同；没有读取原图、权重正文或实验输出，没有运行合成测试、特征提取、匹配或模型。

复查对象：

- `run_observer.py` 全文，SHA `99b65cde2e0604b7179907e9a40e52d6d5240c7c670290ad5232a4e6f44a68cd`。
- `RUN_CONTRACT.json` 全部字段，SHA `ba89adbcdd246e60c02d75a5e1ca29c7db202a607885ccb4f48c0d3b50a14251`。
- 固定官方 commit `eb42fee2d71449efb0aa5c10549752b5d75384d8` 的 `sift.py`、`lightglue.py`：分段读取提取、去重、RootSIFT、配置/权重、归一化、注意力/assignment、接受索引及前向/停止等路径。联合输出曾截断，已对 SIFT 头部、合同末字段及 LightGlue 中段另行补读。没有把这些读取扩大成官方所有文件或权重训练数据审查。

**结论：在当前已冻结的13图/12对条件下，没有发现会使固定 F 方向、N/M 分母、两匹配器特征公平性、权重装载或接受索引语义改变的实质源码错误。** 这是有边界的作者判断，不是“证明没有任何 bug”，也不预告实际执行或科学结果通过。原源码和合同保持不变。

## 逐项检查

| 关键项 | 实际代码与公式核对 | 判断 |
|---|---|---|
| 全输入与顺序 | 合同列13个不同图像ID：anchor19及四目标各real/A0/B；12对始终以anchor19为源。worker先遍历全部图像，再逐pair BF→LG；原图身份按已绑定SHA/字节数核验后，PNG RGB576解码，不因残差/视觉结果改变列表。 | 没有发现漏目标、重复A1作独立样本、只选target22或按结果筛图。 |
| 共享新特征 | 每图仅一次 `extractor.extract(image, resize=None)` 尝试，完成后保存所有keypoints/descriptors/scales/oris/image_size/keypoint_scores并缓存于 `features[id]`。BF读取该缓存的descriptor；LG从同一缓存逐字段复制为batch tensor。之后的几何用原缓存坐标，不使用LG内部归一化坐标。 | BF/LG没有各自重提特征、不同resize或不同描述子预处理。新特征与旧S73不是同一ID/特征集合。 |
| 官方SIFT语义 | 官方默认RootSIFT=True；NMS=0仍进入 `filter_dog_point`；OpenCV入口明确用contrastThreshold、nfeatures、edgeThreshold、nOctaveLayers。scales取KeyPoint.size，oris取deg2rad(angle)。RootSIFT执行L1→clip/sqrt→L2。调用端传合同全部显式参数，未另加归一化。 | 与SIFT-LightGlue官方适配器吻合；不是Gemini所称必须换raw SIFT。num_octaves=4是OpenCV nOctaveLayers=4；first_octave在本backend不用。 |
| BF严格双向规则 | 两向KNN各保存两邻居，少于两项时第二ID为−1、距离NaN，不能通过ratio；严格 `d1 < .75*d2` 后检查反向最近ID互指。没有由几何分数决定接受。 | 与当前合同一致。比较发生于保存FP32距离数组，独立复算不能在临界点默认为FP64乘法。 |
| LG权重 | 构造 `features=None,weights=None,input_dim=128,add_scale_ori=True` 避免内置隐式下载；实际本地bytes核SHA后以weights_only=True读取，按官方两套旧key规则重命名。load_state_dict只允许missing confidence_thresholds、禁止unexpected；每个named_parameter必须存在、为FP32且等于checkpoint。 | 不会因strict=False就把未装入学习参数当成功。confidence_thresholds由官方构造器生成，且−1关闭深度/宽度自适应；本检查没有读取或重新加载权重。 |
| LG前向与索引 | 官方filter做互选和score>.1，可能给被拒绝项保留正分。caller以matches0≥0构造P，检验完整matches1互反与compact matches相同；没有用score>0再次选点。官方非空、禁自适应路径走9层，stop_layer需为9。 | 接受点语义一致；完整分数保留。CPU FP32、flash/mp false无调用端隐式half/compile。 |
| 固定F方向 | `p0@F.T`逐行等价于源点列向量的Fp0，是目标线；`p1@F`等价于Fᵀp1，是源线；分子为abs(p1ᵀFp0)。三列为到目标线、到源线、二者均值，浮点64。 | 没有转置方向、点位交换或误用平方Sampson。F是否符合真实物理标定仍继承S72输入边界，非本复查新证明。 |
| 固定错label | 对同一P/同一x0,x1，correct读Fs[target_id]，wrong读Fs[wrong_target_id]；合同四目标各三臂均固定20↔23/21↔22，source19未改变。 | 没有重配点、交换图像或挑选使残差更低的F。 |
| 分母与缺失 | N/T来自同一封存完整特征，M来自唯一互反P；未匹配=N−M/T−M。有效点数与invalid分别保留，阈值计数分别除valid_count及N。空匹配的分位为null；特征缺失/异常M为null，不伪装成M=0。 | 没有把未匹配误差填0或把各行匹配数当统一分母；不存在将24行当24独立样本的统计代码。 |
| 分位与覆盖 | 全有效值使用linear q25/50/75/95，阈值是≤2/5/10px。配对差先逐点wrong−correct再取分位，两标签共同valid才定义。覆盖分别保留全部接受点与全部特征，4×4 grid及每轴span；不按残差过滤覆盖。 | 与合同描述一致；不是中位数相减，也未把invalid接受点从完整匹配记录抹去。 |
| 运行/失败边界 | 正式入口创建全新execution目录、外部监视600秒及采样RSS8GiB。逐feature和pair保存事件/结果，异常标明missing/PAIR_ERROR；完整循环有24行，错误返回非零；中断保留外部终态和已写增量。 | 无自动重试、调参或覆盖旧S73/S77路径；COMPLETE_DESCRIPTIVE_ONLY仅技术完成，不是科学成功事件。 |

## 必须保留的解释与复核细节

1. **“共享特征”控制提取器，不是相同信息消费方式。** BF只消费描述子；官方LG还消费同一提取器的keypoints、image_size、scales、oris，并使用学习的上下文匹配。差异属于此次完整matcher替换的定义。可以说同一封存特征下两匹配规则的观察结果不同，不能进一步单独归因于“神经assignment”或某一个输入字段。没有给LG额外图像、真值相机或几何筛选。
2. **独立checker的浮点口径。** BF ratio及LG阈值有FP32语义；`source_all_feature_coverage/target_all_feature_coverage`直接用FP32特征计算span，而接受点在几何前转FP64，其coverage用FP64。另式复算应记录这些精度差，不把小舍入差当成匹配公平性失败，也不为配合数值而改科学阈值。
3. **官方空特征路径未必正常返回空数组。** OpenCV detectAndCompute可能返回None描述子，官方包装在后续阶段报错；当前catch会如实保存EXTRACTION_ERROR与未知N、关联missing行，不自动重提特征或臆测实际0个点。此种情况不能宣称两匹配器都已运行但零匹配。
4. **一处非阻断的故障保存范围说明。** 正常LG输出的raw NPZ在索引验证/几何前保存，但`stop_layer!=9`检查更早。若发生这种与冻结禁自适应设置冲突的反常返回，会先记录PAIR_ERROR，未必有该行raw matcher NPZ。不能在该异常情形声称完整原始匹配已保存；正常9层路径、科学分数和输入公平性不受这项说明影响。本轮不为该异常诊断细节改已冻代码。
5. **8GiB是采样停限。** 不是瞬时硬内存上界；监视器ps开销、采样间隔和退出清理也写在合同。root判实际预算应看外部终态与真实耗时，不能只看worker返回。

本复查没有发现需要暂停当前已授权探索测量来改变科学设计的问题；不要求新增审批工程。root的源码判断与随后实际输出的另式复算仍需如实独立记录。即使程序和算术通过，也没有证明物理对应真值、绝对相机正确或新方法有效。
