# S40 DRAFT：具名 VAE 变体的原两批生成

准备开始 UTC：2026-09-07T04:21:07Z。当前没有执行模型、测试、照片/GT读取或生成。S39真实加载尚未完成；所有实际路径、回执及批准占位保持空。此草案不能启动。源码准备的实际完成时刻与SHA见preparation_receipt.json；root负责主账。

版本固定为 **VMem + stabilityai/sd-vae-ft-mse (declared VAE component variant)**，官方ft-mse revision `31f26fdeee1355a5c34592e401dd41e45d25a493`、配置与参数身份继承S39。原SD2.1 VAE来源仍UNKNOWN；原VMem/CUT3R/CLIP身份与原数学不变，但本版本不是精确原版复现、新方法或质量提升证据。

## 问题与唯一运行范围

用原changi输入和原导航执行 initialize → turn_left(5) → turn_right(5)，真实观察第二批是否把第一批生成产物作为历史消费。只运行一次新fresh worker，加载一次，后续两批连续使用同一pipeline与RNG，不在两批间重建模型/重置种子。历史必须1→5→9；最终9帧以pipeline.pil_frames为准，Navigator返回列表包含原图或live-list别名，不能拼成重复的“新生成9张”。

原设置不降级：CPU/FP32/8线程、seed42、H=W576、T8、context4/target4、50 steps、默认NMS、原step_size=.1/4插值、原400iter GA/lr=.01。原首批样本槽为8，其中7目标含3padding；保存所有samples/samples_z和7条目标CLIP行，实际保留4新帧。第二批仍8槽/4目标，历史9。原几何首次/后续K历史5→14、depth5→9，按实际原返回保存，不人工“修正”为9个K。不使用S28–34的getter或尺度修复，不做小图/少步/替代小模型来获得成功。

## 可逆的最小复用

`launch_generation.py`读取固定S35 launcher SHA `8744cb8959cded2394c1471c660dd84f929b5ae24ac97e81379304aed0be702e`，只派生：1处HERE保持原S35依赖目录；2处gate路由至本目录generation_gate；1处factory路由至runtime_adapter；7类schema/身份状态文字替换。每次构造派生代码，反向还原后整个AST必须与原源码相等。`__file__`绑定本S40真实入口，保证父回执、自SHA和fresh worker命令都指向新文件。原参数、循环、0.5秒监控、trace边界、kill_tree、异常归档均未改；原源文件不写。

`runtime_adapter.py`按S39方式从原S35 factory派生单一gate import和4处证据标签，再验证全AST反向相等。构造后沿用S39 v2 VAE属性与全部state_dict记录门：每次已记录missing/unexpected为空，strict_requested完整保留（含原CUT False），拒绝吞异常后留下的早先坏记录。新鲜S40加载仍再次核这些条件，不能依赖旧加载结果代替本次检查。无额外前向、编码、采样、随机数读取或模型变更。

S35 integrate_original.py、archive_outputs.py、原S20 trace以及所有真实模型/GA/renderer/NMS函数以原字节复用。原trace只接受`recorded_execution`/`synthetic_test`；本次仍用前者记录真实执行类别。**这个低级schema不声称组件是exact-original**，身份由S40 manifest的variant、source domain、S39资源core及加载回执绑定。worker/parent顶层状态改为具名variant待审，完整资源gate也明确具名身份。

## 实际前置门与冻结接口

generation_gate须先核：

1. S40正式manifest SHA、明确FROZEN状态、所有原controls与预算、原S35 import顺序；完整S39源码域加本目录4文件的精确身份。
2. **实际**S39正式加载manifest与其排除review_receipts的resource core SHA。S40五组件/原YAML/原changi输入须逐值等于该实际manifest，不能换来源后沿用加载成功。
3. S39实际launch、worker、runtime_loading、full_resource_gate四份文件的完整SHA和交叉引用：同manifest/source、一次factory、零生成/codec请求、无超限/残留子进程、returncode0、最终全部state_dict与VAE载入信息完整；实际full gate的文件stat和小输入/源码仍一致。
4. 另一作者真实S39加载证据审查，接口status=`PASS_S39_LOADING_EVIDENCE_REVIEW`，含variant、loading_manifest_sha256、resource_core_sha256、evidence_sha256（launch/worker/runtime_loading/full_resource_gate四键→SHA）。当前无此实际回执，工具不生成。
5. 两份实际S40批准，status分别`PASS_S40_GENERATION_SOURCE_REVIEW`和`READY_TO_ATTEMPT_S40_DECLARED_GENERATION`，均含variant及S40 core_sha256。core沿原函数排除review_receipts，源码审通过但未绑定实际core的旧文不能当运行批准。

父进程这些条件都满足后才导入psutil/启动fresh worker。S40元数据门会读**已知原changi小输入字节以重新核SHA**，因为复用S39 validate_gate；不会解码像素、读GT或hash GB组件。不能误称父门零照片字节。worker再完整读五组件SHA一次（S39已有加载验收并不替代本次内容门），然后归档/trace工厂→新模型构造→原初始化/两批。gate复核只读stat/小来源，不重复GB哈希。

## 保留真实历史消费证据

原接线记录context_output的实际context_time_indices、完整被选cache，condition_input/output、sampler原noise/c/uc/RNG前后、全部samples/samples_z、target CLIP embedding、cache/map提交、完整dense几何/Surfel/source/K/depth、renderer和NMS阈值/选择。按原同步捕获保留get_cond原地相机修改前后，不重新encode、采样或造缓存。

原run_original要求第二批selected_context_ids中实际有ID>0；当时合法生成历史是ID1–4，输出summary保留具体IDs，并与原trace/完整archive核其实际缓存内容。单凭“ID>0”、history9、退出0或有PNG仍不能独立证明所有张量来源及视频质量；之后另一作者须核第二批所用缓存与第一批提交的对应完整数组一致。未消费生成ID则保留失败，不能重新选图来通过。原NMS阈值来自len5真实相机，不能预填人为阈值。

## 预算、产物及失败

完整复用原1800秒/批、累计3600秒、45GiB进程树RSS、CPU8、磁盘至少10GiB、目标0.5秒轮询。第一批包含完整哈希和加载；实际第一批trace batch_complete须绑定ID1–4/history5，第二阶段按原保守monotonic起点计算，第二批为ID5–8/history9。第二批完成后的封存仍计第二阶段和累计预算。该预算尚未实测可行；超限终止整树并保留部分产物，不扩大预算/自动重试/降分辨率。

输出独立 `results/S40_declared_variant_generation`，外控目录另建且不可覆写。保存full resource gate、runtime_loading、两批trace、archive全部原张量与PIL、observation_summary、监控/返回码/失败。正常父状态最多`DECLARED_VARIANT_EXTERNAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW`，科学状态NOT_EVALUATED。没有后续实际原始产物核验之前不称technicalPASS；更不代表视频质量、长程一致性、创新或完成项目。

## 未执行的使用命令

root在S39实际加载与独立验收后填写candidate中的真实资源链，实际核源码、冻结core并附两份批准。保持DRAFT现状时命令应拒绝，不为测试而运行一次。

```sh
S40_ROOT='/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling'
S40_MANIFEST="$S40_ROOT/work/S40_declared_variant_generation/manifest.json"
S40_SHA='<正式manifest文件实际SHA>'
"$S40_ROOT/.venv-cut3r/bin/python" -B "$S40_ROOT/work/S40_declared_variant_generation/launch_generation.py" --manifest "$S40_MANIFEST" --manifest-sha256 "$S40_SHA" --execution-directory "$S40_ROOT/work/S40_declared_variant_generation/execution_01"
```

当前只标准库parse/compile/AST派生来源核，无科学模块/模型/人工场景执行，不重做S35已经成功的人工接线检查。沿用本地Claude科学批判的证据分级：源码可用、真实加载、完整生成、缓存消费、质量对照各有自己的实际证据，不能互相替代。
