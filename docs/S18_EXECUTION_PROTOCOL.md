# S18 执行协议：S17C 场景到原 VMem 地图及来源候选

协议编写于 2026-09-06 12:02 UTC（北京时间20:02；具体冻结时刻以最终manifest为准）。状态：冻结前协议；尚无S18真实数组运行。root负责冻结与主账；producer、独立verifier、第三作者前审分别由不同agent负责。本协议优先于草案中被明确纠正的内容，草案89ee2fffaed97097f3b8f5f8a2a835959050b2367f03d04d516b3ad930b2e423保持原件。

## 研究问题、证据等级与成功含义

问题：S17C两张已经见过的Bonn实拍经原embedded 512 DPT、400步全局对齐、原clean得到的场景，能否进入原Surfel构造、默认Octree来源合并及两个已知相机的render/process候选入口？这是实际模型输出上的新接口计算，不是模型重新推理、人工数据实验或视频生成。人工前审与正式运行分别保存。

S6曾用224 self-Z重建XY、stride与自定义筛选及单叶等价索引；不能代替本轮512最终world XYZ、0.05双线性和默认原Octree的连接。S0–S11既有first-write、首项票权双加、空间索引、NMS与性能结论不重做、不重新包装为创新。原源码的这些设计归原作者。本轮无新方法假说的有效性检验，不给准确率、视频质量或CCF A水平承诺。

成功仅表示这两个已见输入在限定接口上完成可追溯计算并通过独立复核。更多历史、未见相机、几何真值、强基线、机制消融和完整生成仍需另立协议。空地图、空来源和数值退化保留，不能换数据、补点或调阈值换取成功。

## 固定来源、输入与权限边界

原VMem checkout：`/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem`，commit `39291e4f272f6b4f270691d930926ab5930f942e`。绑定并核对三件原源码：

|路径|SHA-256|
|---|---|
|modeling/pipeline.py|90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e|
|utils/util.py|0b71dcf6d4a43109d785f49d9c6def37b1256c4d189ab9438bfb185f3099f013|
|configs/inference/inference.yaml|8d849588016935573a22ef6aaee567f71125ca4d3bdf18f51e3552a64be9fea3|

原函数提取须AST相等，复用既有memory/retrieval kernels；新增normal/pointmap方法与resize/store语句由新kernel提取和核对。不import或实例化完整VMemPipeline，不调用模型。允许观察原函数locals形成审计轨迹，不能以观察器改变其运算。

上游绑定：

|控制件/输入|SHA-256|
|---|---|
|docs/S17C_EXECUTION_MANIFEST.json|a9d74acb5d79e81696a7cb2cb665577071f47e5af19292230e768638f311c885|
|docs/S17C_OUTPUT_SEAL.json|424090fd2e1de5cdcf7cd124ed893b9a1dea380cf772420cbb48e57834f31df8|
|results/S17C_embedded_independent/verification.json|b783a0343f268c601080d3206e1c49670a1485a074d645925ef60879f026efa8|
|results/S17C_embedded_geometry/run_metadata.json|1e11d45013cf18d038a58853a11785889c0d522bdc61e6121de61fbb7451693a|
|results/S17C_embedded_geometry/final_result.npz|0062327c2395236c087a3cfc743a3d82d57167450f552b9b29ba379171efdc9d|

仅读取并哈希上述五件上游文件，核manifest/seal/PASS回执对metadata/final的绑定；不沿旧5761身份递归重读原权重、RGB或环境。数值仅解码final_result的六数组：point_clouds [2,384,512,3]、depths/confidences [2,384,512]、focal [2,1]、R [2,3,3]、t [2,3]，均float32。allow_pickle=False；ZIP成员名可查但不解码colors/pp。无原RGB、深度GT、轨迹GT、新数据下载、模型权重、VAE/CLIP、潜变量或视频文件。原结果不可改写。

## 精确数学与原版本行为

生产环境固定`.venv-cut3r/bin/python`、Torch2.7.0、NumPy1.26.4，CPU8线程、seed0。输入和Torch几何为FP32；原NumPy merge/render/vote含FP32/FP64混合运算，不能笼统称整条流水线纯FP32。seed0沿用组件记录，原这些方法无随机操作，不声称复现全视频seed42。

### 缩小与Surfel构造

1. 按帧0、1原顺序。`np.eye(4,dtype=np.float32)`填入S17C R/t，得到FP32 optical c2w；不再翻Y/Z，不混用旧raw pose或GT。S17C无先验优化相机区别于原完整pipeline传相机与冻结历史depth的状态。
2. 原三路`F.interpolate(scale_factor=.05,mode='bilinear')`：align_corners默认False、recompute_scale_factor默认None、antialias默认False。384×512→19×25，每帧475格；按显式scale的源坐标20*i+9.5取四邻域，各权重.25，不改为输出尺寸比、不随机采样。逐格保存四像素来源索引和权重；身份是(frame,reduced_row,reduced_col)，不是唯一原像素。
3. 原法向：右/下差向量各除自身norm（不加epsilon），叉积再归一；norm<1e-8时保持零，末行/列为零。NaN/Inf保留并判失败，不能加额外邻域过滤或补法向。
4. 原整张reduced depth上`torch.quantile(...,.999)`与mask `(depth<=threshold)&(conf>=1)`，不先conf过滤。保存每种通过/拒绝/交集计数；离散mask必须exact。
5. 对被mask保留的点执行原normal翻向，view direction用F.normalize默认eps1e-12；dot<0才翻。半径原顺序`.5*depth/(focal*.05)/(.2+.8*abs(dot))`。输入每帧focal shape(1,)，不触发len==2分支。只有masked原radius控制Surfel。额外全格radius只是独立标记的诊断，不反馈到地图。Surfel color=None。

### 默认原记忆写入

第0帧候选全部首写，来源[0]。第1帧若旧记忆非空，调用原merge：normal_threshold=.6、position_threshold不传（原配置.2调用已注释）；实际radius threshold为old+new radii的mean+.5*std，population std；空集合原fallback .025。NumPy1.26 mean/std为FP32、乘Python .5后及总阈值为FP64。np.float32点积与Python .6为原标量比较，不能在NumPy2环境直接假设相同promotion。

原Octree max_points_per_node=10，按dx/dy/dz子节点顺序，边界可以多孩子收同一个旧ID；保留候选重复、遍历顺序和既有浮点漏查，不能换成cKDTree、最近邻或修复树。root center FP32、half-size标量FP64，root边界操作保留NumPy1.26 array/scalar语义；子center FP64。查询只针对旧树；遇第一个严格normal dot>.6才合并。新点不与同帧新点比较，未匹配者最后按序追加。旧geometry/color不变，只增来源；时间来源0/1。保存全部候选到最终ID关系、原树查询轨迹及最终first-writer身份。若栈深或原算法失败，保存失败而非修代码重跑冒充同一实验。

### 已知相机可见性与来源候选

两次query就是上述optical c2w0/1，不是未见视图。原renderer W512 H288、principal point(256,144)、disk_resolution16；`target_K=np.mean(focal,axis=0)`保留(1,)FP32，原`[target_K*.65]*2`保留数组舍入，记录render_focal shape[2,1] FP32，不能先转Python float。该宽视场近似与S17C的H384/pp_y192不同，不是校准相机准确率评估。

原near .1、far1000、margin50、背面/零normal剔除、16边形整数像素射线判内、顶点valid z>0、平均有效顶点depth与FP32 z-buffer均不改。c2w R求逆为原FP32，然后写入FP64 extrinsics，保持原positions/normal其它提升行为。所有像素仍执行原**Python float avg_depth < NumPy1.26 np.float32标量buffer**。

**草案更正：删除“同深度原顺序先占位保留”的推断。** 人工例 `avg_depth=1.0000000894069672` 写入FP32后变成1.0000001192092896，下一相同avg_depth仍严格小于已存buffer，因此原scalar renderer可让后来的同深度disk覆盖。是否保留取决于原严格比较结果；不能转成数组比较或更高精度buffer。这个细节是原版本语义核验，不是本轮新算法或新科学发现。人工证据见`work/S18_review/original_probe_receipt.json`与独立数值合同。

空像素depth0、surfelID−1、cos0；每次query前后整个地图数组、几何首写身份和source lists需相等且哈希不变。原process按C-order像素累积cos/(1+depth)，NumPy1.26分母/权重提升FP64；每来源首项双加照原保留。保存原normalized weights、counts、有序来源。n=min(context4+10,k)，本例k≤2，因此每个可见来源只出现一次；检查的是可见来源集合，不能证明权重截断的检索收益。

不调用get_context_info。原默认NMS阈值在第5历史才初始化，且完整选择消费真实latent/embedding/K/c2w缓存；本轮2历史不伪造额外历史或占位特征。地图空写NO_SURFELS并不调用形状不兼容renderer；query空来源写NO_VISIBLE_SOURCE并保留空候选；非空但非有限/零总权重按失败保存。进程完成状态、数值验证状态与科学是否有非空支持分开报告。

## 冻结、独立验证及输出

CLI `run_s18_memory_bridge.py --manifest ABS --output FRESH`。manifest schema `s18-memory-bridge-manifest-v1`；绑定roles python、runner、source_root、source_commit、pipeline_source、util_source、config_source、kernels、memory_kernel、retrieval_kernel、s17c_manifest/seal/verification/metadata/final、control_files、contract。身份含原三源码、所有实际使用新/旧kernel、runner、independent verifier/数值helper、最终协议/数值合同/第三作者前审、外控脚本及五件上游输入。最终具体输出schema与精度合同在冻结的`S18_NUMERICAL_VERIFICATION_CONTRACT.md`；若冲突先修正文档代码再freeze，不能看真实结果后改标准。

外控复用`run_s14d_controlled.py`，限600s/32GiB并核before/after identities；stdout/stderr/caller receipt与输出保留。每次只用新的空目录。成功阶段不无故复跑；失败保留原目录及原因，修正需新合同/新manifest/新版本。seal覆盖全部输出、manifest及caller回执/日志。manifest冻结前不打开真实NPZ数组。

独立作者在`.venv` NumPy2.3.5环境用NumPy/标量公式复算六输入到插值、法向、mask、radius；不调用producer数学、不import Torch/PIL。连续值预定atol=rtol=1e-5，经人工前审固定，实测后不放宽；所有mask/sourceID/候选集合和来源列表exact。NumPy1.26标量提升须明确模拟。

离散下游可消费**已先独立通过上述连续值验证**的producer FP32输入，以隔离算术重排导致的临界比较差异；独立重建原树路由、遍历、首个匹配、projection、逐像素写入及票权。该验证域不等于跨库逐位重算所有连续浮点。新人工测试只覆盖新接口和版本边界；不重跑S0–S11。报告应给每个实际条件、错误最大值、离散差异数和执行计数，不能用单独PASS代替证据。

最小交付：run metadata，reduced点/depth/conf/normal/mask/诊断及原候选radius，候选到地图ID，树查询/merge事件，最终几何/来源/first-writer，两个render与source-voting，caller、seal、独立回执和中文结果。图表若有仅从封存输出产生，使用科学绘图，不生成虚构照片。

## Skills与检索执行

本轮已读并应用Supervisor `vibe-research-workflow`（小步代码和审查、清楚输入/输出/停止条件、学术判断归用户）及本地Claude `sci-scientific-critical-thinking`（信息边界、替代解释、旧设计与创新分离）。三个agents独立分工，root冻结与记账；未调用Claude模型。用户逐项阅读、导师认可和投稿披露审阅均未被写作已完成。

本轮网页检索核固定[原VMem pipeline](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py)与[Torch2.7 interpolate官方文档](https://docs.pytorch.org/docs/2.7/generated/torch.nn.functional.interpolate.html)：显式scale与由floor后的output size重算scale并非同一行为，默认不启用antialias。本地原源码和所绑定版本才是执行依据。本阶段无需外部学术服务、Claude CLI或额外安装。

每次关键动作追加真实时间、行动、发现和下一步到主ledger；持续阶段每30分钟实查skill、创新证据、记录、检索/工具、独立核验、数据边界及下一动作。创新仍ACTION_REQUIRED，不能把检查完成写成创新达标。
