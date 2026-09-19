# S34 独立保存量与来源票权核算候选

本作者未编写 S34 consumer。核算只使用其未来已封存 map/cache/candidate/render/votes，以及 producer 四个 packet 和已给定 optical c2w；当前仅源码准备，0科学数组读取/GT深度/模型/MST/GA/clean/merge/renderer执行。以后须根先封存全部实际输入身份并冻结本合同，再以已有科学Python、CPU1、120秒、2GiB 外控运行。脚本不导入 torch、原几何或来源投票函数；不存在调用原 consumer 的入口。

## 来源与科学边界

consumer `work/S34_consumer_preparation/run_consumer.py` 与原提取源码 `src/vmem_retrieval_kernel.py:181–242`：原配额181–212、原来源累加214–242；原 VMem fixed commit `39291e4f272f6b4f270691d930926ab5930f942e` 的 `modeling/pipeline.py:411–502` 对应。完整源身份由候选绑定；实际物理 renderer 和 Octree 匹配不被本脚本重算，因此PASS只表示保存量自洽和来源票权另式核算，不叫独立 renderer 物理正确性或独立模型复现。

当前 `k` 仅表示实际参与投票的不同 source 数，不是 S31 的归一化标量。source 只能0–7，所以 **k≤8<14，n=min(context4+10,k)=k**。原 `get_frame_distribution` 在 leftover=0 返回每个源1张；空集合返回空列表。若有原visible像素但cos<0会先跳过；cos=0仍可建立source，原source身份按此保留。因此权重数值变化本身不改此域quota，只有参与来源集合变化会改变候选集合。不能减少14、临时增帧或把候选当最终NMS context，以制造敏感性。余数分配的历史 `result[idx]=1` 路径本域没有执行，不宣称被实测复核。

## 必须核的保存量

1. 固定 consumer 正式 manifest/PASS receipt、全部 outputs和输入SHA先查、写入input seal，再解码；运行后重核。来源不符或总consumer失败就停止，不读部分结果补成功。packet来自四份正式producer PASS，原consumer input封存链原样绑定；没有sensor-depth PNG输入或打分函数。
2. common map非空；三臂旧prefix position/normal/radius 的shape、dtype、raw bytes与common完全一致。source旧前缀完全保留，只新增4–7。对common帧0–3和每臂帧4–7，独立读取每帧valid mask/flat ids/全部candidate几何和最终IDs，核完整C顺序覆盖、candidate来自本帧reduced pointmap、新IDs连续唯一、匹配ID在原有map域。根据这些已记录对应关系独立重建整个最终source列表，核新增数、候选匹配数、不同匹配ID数、source additions及最终map长度。新加入geometry必须逐字等于其对应candidate；不重新求阈值或证明原匹配选择最优。
3. common cache的4focal/depth与old packet逐字同；每臂cache focal=共同old4 focal串接该臂all8 focal，12项全量逐字核；depth cache=该臂all8 depth。相机全8与共同给定pipeline变换逐字一致；old depth log/exp容差沿1e-5。
4. target明确为同输入相机7，target_pipeline数组与保存共同给定相机逐字同。原单相机四元数均值可能产生FP64编码差，平均后optical与given7在atol=rtol=1e-5内；三臂实际平均后的query optical逐字同。原12项focal均值另用math.fsum/12，原FP32均值和*.65允许atol1e-5/rtol1e-6，中心固定(256,144)。不是GT深度标定或未来查询。
5. render shape固定288×512，depth/cos FP32有限、index int32且每个非负ID指向本臂实际map。只核域/对应，不重新渲染。实际source list结合逐像素render值按C顺序建立每源贡献列表，贡献值以Python double `cos/(1+depth)`；每个源额外附上其首次贡献一次，保留原首贡献双加。用 `math.fsum` 取代原逐次 `+=`，按fsum总值独立归一化，核插入顺序、全部源、quota和展开候选。原NumPy1.26.4下render scalar FP32与Python1的表达式提升到双精度，本核不先截回FP32。

预冻容差：rawvotes `abs_tol=1e-8,rel_tol=1e-10`；normalized `abs_tol=rel_tol=1e-10`。它们允许逐次双精度加法与fsum的舍入差，不允许删像素、修首贡献或改变分母。票权/全部端点任一不符保留FAILED，不后看结果放宽。零来源保留empty，不给其虚构归一化分母。

## 报告与停止

输出三臂绝对描述：map新增/匹配/source additions、完整旧geometry门、12K/8depth、visible像素、全部来源raw/normalized/quotas与核算最大差。另给三个固定两两比较：可见域异或、共同可见域渲染depth差、通过各自index解析得到的world点距离、source-list变化、票权L1和候选集合是否同。**不直接比较两臂整数surfel ID作为几何差异，不把虚拟renderdepth与resize后的sensorGT对照，不用差异宣称好坏。** final_context_ids始终null/未执行；完整生成未执行。

保存量或来源不一致、非有限、全量集合缺项、原约定域超出、时间/内存超限均停止留档。不开新的匹配/渲染/优化/科学人工测试，不扩大消费者判别面。独立程序本轮只准备候选，真实数值运行及结论由根冻结后才产生。
