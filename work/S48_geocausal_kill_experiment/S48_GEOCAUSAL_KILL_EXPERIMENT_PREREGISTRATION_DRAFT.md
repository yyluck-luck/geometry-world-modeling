# S48 GeoCausal 最小否证实验预注册草案 V6

- V6 source-only 修订日期：2026-09-08（Asia/Shanghai）
- 状态：`REVISED_DRAFT_V6_SOURCE_ONLY_PENDING_FRESH_INDEPENDENT_REVIEW`
- `execution_authorization=NONE`
- `novelty_authorization=NONE`
- 模型加载：`0`
- S48 arm 启动：`0`
- C1/C2 payload、tensor、图片正文读取：`0 bytes`

## 0. 版本历史和证据边界

V1–V4及其审查原件保持不变。V5主草案 whole-file SHA-256
`b8b98ec99d89abdbb83ae45bded2981ef0e654533f051bb351cf82bf355f767c`
已封存在
`archive/S48_GEOCAUSAL_KILL_EXPERIMENT_PREREGISTRATION_DRAFT_v5_shab8b98ec9.md`。
fresh V5独立统计审查
`INDEPENDENT_STATISTICAL_REVIEW_V5.md` whole-file SHA-256为
`3a213ebaeec5463fe744d3aa8fc47c78edce9f5d4e63cbe6de1d16b1b4da9d93`，
裁决`BLOCKED`（2 CRITICAL、6 MAJOR、3 MINOR）。本版逐项修复这些源码/统计合同问题，
不撤回、不覆盖旧反例和旧裁决。

旧V1 normative三文件保持原字节，仅作失败历史，不能授权V6：

- `S48_NORMATIVE_ANALYSIS_SPEC_V1.md`：`a88efa8f5f3e23da75132c2167fd5bd1f5cb58de5498425df4f7656a402718de`
- `s48_analysis_reference_v1.py`：`2cacc5c312af92dfe823db7c7519cffc4f2f16fc4c9b8d9a34d6aa94a81359c7`
- `test_s48_analysis_reference_v1.py`：`f611e22deb68402ed1b04764f31214d759334679feb5c9514f6a6270abd27bb1`

V6的唯一 source-only normative候选包是：

- `S48_NORMATIVE_ANALYSIS_SPEC_V2.md`：`29014cf8504a5b91040e96074c6d6edf47038814f230cb8d62e5822998d19d2f`
- `s48_analysis_reference_v2.py`：`af6079dcce32af12b6bd0240e73fce2bae2e7aaeb39fa90dfcf1c99e9b7a5189`
- `test_s48_analysis_reference_v2.py`：`d05110ab6665eed6912b1ddfd07a00f99490b29d99cd63322d6326a81187c89c`

它只实现有限NumPy定义和合成反例。任何一字节改变都会使本页的G7绑定失效，必须重新
哈希、测试和fresh review。V2包通过作者测试也不等于通过独立审查，更不等于可以运行模型。

给新手的直观解释：我们现在还没有问“这个创新是否有效”，而是在先保证尺子不会量错。
V5的尺子会把一次RGB差再除以255，也会用另一张图片逐像素扣出一块假的“局部作用区”。
V6把这两条规则改成唯一、可复算且有永久反例测试的合同。

## 1. 研究问题、单位和范围

### RQ0：自然失败是否存在

在严格相机/K和整体画质守卫通过后，C1或C2是否出现预注册的自然严重重访差异？若没有，
停止本路线或只报告baseline negative result。不得为了运行干预而事后放宽失败门。

### RQ1：已选来源是否被真实消费者使用

在普通Select/Address完成之后，对同一来源全部appearance consumer作一致低剂量编辑；相对走
同一路径的matched zero，保存输出是否在每个family、seed、sign、target都超过replay、负控制
全图效应和`delta_I`？这只叫post-selection downstream Influence。

### RQ2：作用是否落在干预前几何支持区

只在raw matched-zero target direct map上计算Localization。真support必须超过自身面积基线，
并在shape/camera两个预先生成的matched mask库各自进入描述性前5%尾部。negative是独立
numeric veto，不参与逐像素扣除。

### RQ3：来源是有益还是有害

只有从未进入memory/conditioning的同步真实观测可作reference。局部编辑与公平未选来源替代
分别给出signed Benefit；每个sign、target、replacement单独过门，不能用平均掩盖失败。

科学外推最高单位是scene。观测单位是
`scene x episode x revisit target x ordinary-run selected source`；seed、edit、replay、frame、
placebo和source candidate都是嵌套技术重复，不能虚增样本量。S48只是一条开发unit的低成本
kill experiment；若存活，S49另行冻结跨scene confirmation。

开发unit固定为C1后C2中第一个通过RQ0的行；source固定为该行普通slot顺序中第一个满足
可寻址、provenance完整、全部consumer可枚举且不是reference的来源。不能看F11、Localization
或Benefit后换unit/source。

## 2. 执行前硬门

| Gate | 必须在任何S48 arm前有的实物 | 失败动作 |
|---|---|---|
| G0 baseline | C1/C2真实生成、保存量readback、相机/K、盲态评分和独立复算均闭合 | 不启动S48 |
| G1 natural failure | 至少一个预注册严重事件，且不是相机失从/整体崩溃 | 停止或改写negative result |
| G2 exact replay | 每seed四个实例、精确六pair、typed receipts和稳定floors | 调试确定性 |
| G3 addressability | ordinary selected source ID、slot、duplicate map、trace完整 | 不作来源干预 |
| G4 consumer completeness | post-selection hook、全部appearance descendants和positive trace双审PASS | 不作Influence |
| G5 support | arm前真实camera/K、surfel/provenance、fractional support和placebo feasibility封存 | 不作Localization |
| G6 reference | 同步/相机/identity/view-pair/common-valid/hole规则均有实物PASS | 不作Benefit |
| G7 frozen V6 manifest | 本协议、V2三文件、hook/launcher/renderer/weights/data及所有SHA获fresh独立前审PASS | 不启动任何arm |

任何较早版本的PASS都不能替代V6 fresh review。自然失败G0/G1优先；即使G7未来PASS，没有
自然失败也不得启动干预。

## 3. 因果对象和干预边界

普通运行中Select/Address已经发生，因此处理量只识别“条件于已选集合的post-selection
downstream total effect”。不能外推Store或Select的端到端总效应。

唯一处理时点是普通`get_context_info`完成选择后、`get_cond`构造任何appearance input前。
当前 `vendor/vmem_snapshot/modeling/pipeline.py` SHA
`90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`
的返回值没有target support，所以当前hook仍不可执行。未来`post_selection_bundle`必须在同一次
ordinary selection调用物化source ID/slot/order、semantic bytes、latent/VAE bytes、geometry、
surfel/provenance与全部consumer trace。缺一个consumer就fail closed。

每个arm只冻结prompt、target camera/K、实际initial noise、完整RNG初态、base snapshot、
非目标来源和其他干预前外生状态。目标来源改变后的attention、fusion、semantic conditioning、
latent、denoising trajectory及输出都是后代，必须重算。冻结后代只能叫路径诊断。

四格保持：F00原/原；F10编辑semantic；F01编辑latent；F11两条及任何新增appearance path
全部编辑同一来源。唯一主处理是`F11-edit - matched F11-zero`；F10/F01只诊断路径冲突。

## 4. 唯一数值域和同路径zero

所有保存输出必须是原生`576x576x3 np.uint8` sRGB。每个公开output API拒绝float、list、
uint16、灰度、alpha或隐式cast；内部唯一转换是

`x = u.astype(np.float64) / 255.0`。

后续绝不再除以255。Influence、RGB/chroma守卫和Benefit的RGB量都在`[0,1]`归一化域；
MSE在其平方域。一个像素三个通道各差1 code的direct effect恰为`1/255`，MSE恰为
`1/255^2`。`delta_I=0.5/255`，`delta_B=0.001`，`delta_out=0.0005`。

两个编辑族和dose ladder固定：

1. `exposure_log_gain`：`x_pre=x*2^(sign*dose)`，dose为`1/64,1/32,1/16,1/8`；
2. `texture_highpass`：`x_pre=x+sign*dose*(x-B5(x))`，dose为`.05,.10,.20,.30`；
   `B5`是两轴separable `[1,4,6,4,1]/16` reflect-101 blur。

唯一API是`apply_source_bundle(uint8,family,sign,dose)`，dose可为精确0或该family ladder值。
每个处理与matched zero均走：decode → family edit → clip[0,1] → 乘255 → IEEE/NumPy
round-half-to-even → uint8 reencode → decode → semantic consumer → latent consumer。zero不能旁路。
V2有限adapter的semantic tensor为float32 CHW `[0,1]`，latent tensor为float32 CHW `[-1,1]`；
两者各有带domain/dtype/shape/bytes的SHA和固定调用顺序。真实CLIP/VAE preprocessor尚未实现，
未来必须另冻真实tensor、两SHA及完整consumer count。相同输入重复zero必须字节与两SHA一致。

source-only dose只能在任何生成输出前，按上面升序找到`+/-`两侧同时满足的第一个：
MAD在`[0.5/255,8/255]`，clipped-channel fraction `<=.005`，edge IoU `>=.95`，
冻结CLIP cosine `>=.995`，冻结LPIPS `<=.05`。真实CLIP/LPIPS architecture、weights、预处理、
device/determinism仍缺，故当前不能正式选dose。

## 5. A0、控制和进程

每seed固定F00原实例加三次replay，共实例`0,1,2,3`。每个target恰有六个typed receipt，
canonical pair为`(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)`；每份绑定seed、target、i、j。
重复、缺失、额外、倒序、混seed/target一律invalid。所有方向性guard改为对称量后才取六pair逐分量最大；
floors必须全finite、在定义域内且每个P95 `>=`同域median。

每个`family x seed x sign`包含独立fresh-process的：F11 edit/zero、negative edit/zero、
positive edit/zero；F10/F01及zero在Pilot-B加入。每pair相同source/slot/snapshot/noise/RNG/target
roster/adapter/trace，唯一差别是dose。正负sign不能共享一次随机输出。negative来源是完整普通
pre-selection roster按`(exact nonnegative insertion integer, source ID UTF-8 bytes, file SHA)`排序
的第一个合格未选来源；不得用float/timestamp近似event，也不要求P与target同步。

每arm使用fresh process并从同一只读snapshot重建；PID/PGID、UTC、return code、峰值资源、
RNG/noise/snapshot/trace和终态receipt进入manifest。当前没有已审launcher/hook，故arm数仍为0。

## 6. 统计量和继续门

### 6.1 Influence

对严格uint8 matched pair：

`e_target(p)=mean_c |x_edit(p,c)-x_zero(p,c)|`，

`e_negative(p)=mean_c |x_neg-edit(p,c)-x_neg-zero(p,c)|`。

`tau_output=max(1e-6, 同seed/target六个A0 pair的全图mean direct effect)`，

`I=mean(e_target)-max(tau_output,mean(e_negative))`。

每个预注册family、seed、sign、target都必须`I>=0.5/255`，positive direct pair也须超过
`tau_output+0.5/255`并命中预注册consumer trace。没有任何控制图逐像素扣入target map。

### 6.2 Localization

主map唯一为上面的raw `e_target`。对arm前support `W=S_t`：

`area=sum(W)/|Omega|`，

`mass=sum(W*e_target)/(sum(e_target)+1e-12)`，

`L_area=mass-area`，`ER=mass/area`。

support必须非空非全屏，effect总mass必须`>1e-12`。均匀direct effect必回到area baseline，
不得因为negative只作用于support外而形成假富集。V5审查给出的实际8-bit 576网格反例永久
进入V2测试：target在全图恒差`(8,-5,4)` codes，negative只在86行support外差
`(1,-1,1)` codes；V6必须因raw target `L_area=0`而FAIL Localization。

negative只作同一support上的独立veto，全部预注册：

- `mean(e_negative)/mean(e_target)<=0.25`；
- `L_area(e_negative,W)<=0.01`；
- 不修改、不校准、不扣除target map。

shape和camera placebo各自至少199个，经V2 topology/caliper和预先冻结generator筛选；
真support mass必须严格高于lower median，描述性tail rank
`[1+#(M:mass(M)>=mass(S))]/(K+1)<=.05`。主门还需`ER>1`、`L_area>=.02`。
source masks有至少19个才可用同规则作source-specific语言，否则只报告序位并记
`NOT_IDENTIFIABLE`。三个family绝不pool，rank不叫p值或显著性。

### 6.3 有限输出guard

所有生成arm相对同seed F00使用相同strict uint8 guard。matcher固定为原生576网格、9x9
z-normalized灰度patch、中心`16+32k`、+/-8搜索、确定tie和双向mutual；A→B和B→A距离
合并得到对称统计。分别保存global、support内、support的32px邻域的expected grid count、
matched count、coverage、median/P95。support及邻域各必须包含至少一个grid center。

固定门与对应replay floor取较大者：global matches `>=50`、global coverage `>=.75`、
support/邻域coverage各`>=.50`；三域median `<=1 px`、P95 `<=3 px`；support外全RGB
mean absolute difference `<=2/255`；chroma用
`0.5*mean(|Δ(R-G)|,|Δ(B-G)|)`归一到`[0,1]`并要求`<=2/255`；sharpness用
`|v_A-v_B|/max(v_A,v_B,1e-12)<=.10`；饱和channel-sample比例绝对差`<=1 percentage point`；
行/列tear score绝对差`<=2/255`。

永久synthetic tests覆盖periodic tile、support局部shift、pure-chroma outside和low texture。
这些门只能排除注册的gross displacement、局部coverage、RGB/chroma、sharpness、saturation和
tear解释；不能排除所有artifact，也不能证明requested camera/K、geometry或Localization。
camera/K数值门与盲态人工检查保持独立。

## 7. Reference和Benefit

当前C1/C2没有合格独立reference，RQ3仍BLOCKED。本节只冻结未来有限规则。

### 7.1 同步与reference roster

`SyncCalibration`含整数`t0_sensor_ns,offset_ns,drift_ppb`和非空实测residual：

`t_cal=t_sensor+offset+round_half_even((t_sensor-t0)*drift_ppb/10^9)`。

用整数有理数实现round-half-to-even。`max|residual|<=10,000,000 ns`，且R与target的
`|t_cal,R-t_cal,target|<=10,000,000 ns`。时间来自原sensor capture，不用视频PTS、生成wall-clock
或文件mtime。

camera rotation必须是det+1的正交3x3。令`b_O=||c_O-c_target||>1e-6`。R资格是同scene、
target rotation geodesic `<=2°`、`||c_R-c_target||/b_O<=.10`、FoV差`<=1°`，因此exact
target-camera通过。所有非负binary64角度转microdegree、ratio转ppm时，用`as_integer_ratio`
和整数round-half-to-even；排序键固定为
`(|dt|ns,angle_udeg,ratio_ppm,FoV_udeg,fileSHA,candidateID_UTF8)`。等号通过，多R tie由SHA后ID
唯一决定，完整纳入/排除flow保存。

### 7.2 identity、view pairs、valid/hole

局部Benefit用O/R pair；replacement用O/R/P三方。每个identity是非负整数图，valid必须strict
bool；invalid绝不冒充background 0。在`W>0`上：

`valid coverage=sum W[all roles valid]/sum W`，

`agreement=sum W[all valid and all IDs equal]/sum W[all valid]`。

coverage需`>=.70`、agreement需`>=.95`，且共同valid域中O/R或O/R/P各自非背景ID集合精确相同。
分子、分母、invalid weight和集合全部入receipt。

非动态warp RGB receipts必须精确包含`O_R,R_PREV_R,R_R_NEXT`；replacement再加`P_R`。
每pair在strict bool valid域计算三个通道各自normalized absolute RGB median且都`<=2/255`；
重复/缺失/额外pair均失败。

对每个support或outside域D和指定view集合，
`common=intersection(valid_X)`；receipt保存
`domain_denominator=count(D)`、`common_valid_numerator=count(D&common)`、
`hole_numerator=count(D&~common)`、`hole_denominator=count(D)`、coverage与hole ratio。
域不能为空；coverage `>=.70`且hole ratio`<=.10`。outside为空直接invalid，不跳过；validity/
hole在任何RGB bilinear warp前决定，depth/identity不插值填洞。

### 7.3 RGB loss和signed Benefit

对strict uint8 output/reference仅转换一次，pixel loss为三通道normalized squared error均值，
spatial loss为valid且可选support weight上的归一化pixel mean。无曝光归一化。

`B_local=loss(Y_edit,R)-loss(Y_zero,R)`；每个`f,s,sign,target`需`>=.001`。

`B_matched=loss(Y_P,R)-loss(Y_O-reinsert,R)`；每个`s,target,P`需`>=.001`。

正值表示原来源appearance较好。support外相同loss定义并要求
`loss(treatment)-loss(comparator)<=.0005`；等号通过。full-support unweighted敏感性全部报告。

### 7.4 O-reinsert公平合同与P时间

普通F00只作诊断，不能当`Y_O-reinsert`。O-reinsert和P必须在两个不同fresh process中使用
同一process-isolation spec、source-adapter SHA、snapshot、injection point、slot、tensor/token shape、position/
source-ID interface、context length、clip/round/uint8次序、semantic→latent consumer顺序、
initial noise SHA、RNG-state SHA、target roster SHA和trace schema SHA；两者都恰有一次semantic
和一次latent消费。attempt/PID必须不同。唯一允许的科学差别是source ID/content及由内容产生的
encoded/consumer tensor SHA。typed receipt逐字段拒绝不公平比较。

P无需target同步；删除V5含混的“逐P时间门”。P唯一时间规则是memory recency：
`|insertion_event_P-insertion_event_O|<=2`，使用精确非负整数。target同步只要求独立reference R。
其余P资格保持：scene/identity、target转角`<=2°`、baseline ratio差`<=.10`、FoV差`<=1°`、
support IoU `>=.80`、weighted area ratio `[.90,1.10]`、source-quality同CAL四分位以及上述
common-valid/hole/view-pair规则；全部合格P按完整roster使用，空集停止。

## 8. G7唯一绑定

G7必须绑定：本V6 whole SHA；V2 spec/reference/test的完整SHA；实际import模块；hook patch、
准确行号、consumer inventory及positive trace；weights/config/environment/device/driver；source/
target/data manifest；camera/K、surfel/provenance/support；三个placebo generator与完整mask flow；
edit ladder、选定dose、zero/treatment两consumer SHA；四replay实例与六typed pair；全部guard；
reference sync/camera/identity/view/domain/hole flow；fresh-process launcher、noise/RNG/snapshot、
arm order和终态规则；所有threshold、invalid/missing和kill action。

normative implementation行必须唯一绑定：

- `S48_NORMATIVE_ANALYSIS_SPEC_V2.md` `29014cf8504a5b91040e96074c6d6edf47038814f230cb8d62e5822998d19d2f`
- `s48_analysis_reference_v2.py` `af6079dcce32af12b6bd0240e73fce2bae2e7aaeb39fa90dfcf1c99e9b7a5189`
- `test_s48_analysis_reference_v2.py` `d05110ab6665eed6912b1ddfd07a00f99490b29d99cd63322d6326a81187c89c`

V1不得出现在授权source set中。V2当前仍未实现真实model hook、CLIP/LPIPS、renderer、
placebo generator、camera/source reprojection、optical flow、真实warp或supervised launcher；这些
不是执行者可补的自由度。必须分别实现、冻结、测试并由不同作者fresh review。

## 9. V5审查逐项关闭表

| V5 finding | V6 source-only处理 | 当前状态 |
|---|---|---|
| C-V5-1 RGB二次/255 | strict uint8，内部唯一`float64/255`，direct effect无额外除法；Influence/guard/Benefit统一域并有one-code tests | `CLOSED_IN_V2_CANDIDATE_PENDING_REVIEW` |
| C-V5-2跨source逐像素扣除假定位 | Localization只用raw target direct map；negative为独立same-support/full-ratio veto；永久8-bit反例必须FAIL | `CLOSED_IN_V2_CANDIDATE_PENDING_REVIEW` |
| M-V5-1 zero路径缺失 | 同一`apply_source_bundle`接收0；固定clip、ties-to-even、uint8、两consumer tensor SHA和repeat determinism | `CLOSED_IN_V2_CANDIDATE_PENDING_REVIEW` |
| M-V5-2 replay身份/方向/floor | typed seed/target/i/j receipt，精确六pair；guard全对称；finite/domain/P95门 | `CLOSED_IN_V2_CANDIDATE_PENDING_REVIEW` |
| M-V5-3 guard接受float | public output与Benefit API只收真实np.uint8；valid只收strict bool | `CLOSED_IN_V2_CANDIDATE_PENDING_REVIEW` |
| M-V5-4周期/局移/chroma/低纹理 | support与邻域coverage/displacement、RGB/chroma outside及四类永久攻击测试；收窄解释 | `CLOSED_IN_V2_CANDIDATE_PENDING_REVIEW` |
| M-V5-5 Benefit/reference不唯一 | 有限sync、camera、roster、identity、view pairs、hole/domain、RGB loss实现及exact/partial/swap/empty/boundary/tie tests | `CLOSED_IN_V2_CANDIDATE_PENDING_REVIEW` |
| M-V5-6 O/P路径与P时间含混 | O-reinsert/P typed invariants；ordinary F00禁止；P只用integer recency，不要求target同步 | `CLOSED_IN_V2_CANDIDATE_PENDING_REVIEW` |
| N-V5-1 histogram binary边界 | 唯一`min(floor(10W),9)`且逐`.1..9,1.0`测试 | `CLOSED_IN_V2_CANDIDATE_PENDING_REVIEW` |
| N-V5-2 validity静默cast | strict `np.ndarray[np.bool_]`，NaN/float/int/list拒绝 | `CLOSED_IN_V2_CANDIDATE_PENDING_REVIEW` |
| N-V5-3 roster整数换算/tie | camera用binary64 ratio→exact rational half-even整数；memory event为exact int；SHA/UTF8末级tie | `CLOSED_IN_V2_CANDIDATE_PENDING_REVIEW` |

这里的“closed”只表示候选源码已经有明确规则和测试；fresh不同作者若找到反例，V6仍应
`BLOCKED`，不能以作者自检覆盖审查。

## 10. 顺序统计、kill conditions和创新边界

S48只做顺序继续/停止：Influence → Localization → Benefit。所有比较用同seed/noise/state；
逐family/seed/sign/target/replacement合取，任何技术重复平均只作描述。不给pilot总体p值或CI。

以下任一成立就停止或降级：无稳定自然失败；camera/K或blind guard失败；exact replay不稳定；
source不可寻址/consumer不完整；任一Influence不过门；raw Localization不超area或shape/camera
任一家不在尾部；negative独立veto失败；reference/identity/view/domain/hole不合格；任何单侧/
target/P Benefit或outside门失败；普通attention/pose/retrieval/source-quality gate解释同样现象；
只能在一scene/source/edit/consumer成立；或新公开工作已完成同一联合协议。

若pilot存活，S49须在任何confirmation输出前另冻CAL/CONF scene隔离、唯一scene-level estimator、
样本量/power、familywise alpha、固定10,000次cluster bootstrap或exact test（二选一）、多重性、
invalid/worst-case和no optional stopping。S48技术重复不得进入S49 scientific n。

PC-DPM仍只是条件式方向：仅当F10/F01证明semantic与latent消费者有跨scene稳定来源冲突，且
confirmation得到稳定signed Benefit，才考虑共享provenance weights和离线因果教师。per-source
token、geometry attention、memory gate、utility surrogate或这些常规模块组合都不自动构成创新。

## 11. 当前允许和禁止的结论

当前只允许写：V5的单位歧义和假Localization反例推动了一个更严格的V6 source-only候选；
41项合成测试与不少于200个随机性质样例若通过，只说明这些有限实现与测试一致。

继续禁止写：已发现自然失败、已证明来源被使用、已证明geometry-localized causal effect、
已证明Benefit、PC-DPM有效或新颖、S48已运行、已达到PhD/CCF A或任何录用水平。

## 12. 强基线和近邻范围

未来若进入真实实验，至少比较exact replay、attention mass、retrieval score、pose overlap、
source selection、WorldTrace addressability、I3DM/WorldStereo/Spatia式几何检索/注入、LongDiff
context控制、I2AM/AGRA空间干预、TetherCache、CUE-R REMOVE/REPLACE/DUPLICATE、identity
reencode sham、negative/positive controls、普通pose/retrieval/source-quality gate、容量匹配
per-source tokens、source-agnostic ablation和更长context。已有组件连接或baseline修复不算新方法。

近邻原文入口保持V5已冻结清单，包括VMem、SPMEM、WorldModelBench、WorldStereo、Spatia、
PlenopticDreamer、LongDiff、WorldTrace、I3DM、TetherCache、CUE-R、I2AM、AGRA和SelectiveNet；
本次源码修订没有重新认证文献新颖性，`novelty_authorization=NONE`。
