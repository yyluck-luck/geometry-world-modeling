# S34 共同旧图与八帧几何 producer：待审候选

本文件只约定 common-old 与 GA producer；原 map append/render/来源票权由独立 consumer 负责，GT 评分由独立 scorer 负责。原 proposal/默认 context/生成范围不扩写。决策依据为 `docs/S34_NEXT_STEP.md` 和 `work/S33_next_decision/review.md`。只有另行审查冻结的合同及显式 SHA 能执行；本轮不读取科学数组或 GT，不运行模型/MST/GA。

输入固定为 S26B 原 fr2_desk 首八配对帧：S21 cut3r 完整前八头、原八张 PIL 和同一光学 c2w 文件。共同旧图固定取 S29 C2a `initial_decoded/raw`，原四头来源为 S21 original4。两来源的 archive SHA 不同，既有 S26B 兼容仅证明各自保存头与原消费者拼装，不能称跨源逐字相等或新的 embedded 模型等价。S29/S30 同起点实际 gate 和八相机文件共同 SHA 继承封存回执；运行前实际核 bytes，旧 decoded camera 与光学前缀按 1e-5 容差核。

`common` 阶段只恢复 S29 四帧 depth/world/focal/pp/c2w 与 raw im_conf，完整33旧源 raw metadata/bytes及原目标独立公式核对；不重建 optimizer、不跑 MST/Adam。它原本没有 clean；本阶段调用一次原 FP32 clean 函数于副本，全像素独立 clean 与反投影核验后封存。provenance 为 `S29_C2a_saved_MST_zero_step_plus_new_original_clean`，不伪造原400。地图不在此阶段构建，由 consumer 单次构建共享 old4 图。

两个新八图 GA 仍复用原 S26B prepare_output、7边 star、C2a单位 Sim3尺度/原R/中心均值平移、原初始化、修 getter、400 Adam/.01/linear 和原 clean。只显式替换原 worker 的条件名字、cut3r archive 路由、给旧 depth 的真实 provenance 入口；原优化/输出/独立目标/clean/backprojection/实际模块核对语句保留。原 S26B manifest 用于继承 control/兼容/源码身份；每个新回执另带权威 `contract_sha256`，不可将父 manifest 字段当本次独立合同。

- 旧 0–3 log-depth、全部相机和 pp 在 preset/MST/400/clean 保持同名、同对象、原始值、grad=None。MST 会调用旧 setter，但原 `requires_grad or force` guard 禁止覆写；本轮实核，不凭源码假定。米制 old depth 的 log→exp 与相机编码解码采用 `atol=rtol=1e-5`，记录最大差，不覆写返回值。focal 全8继续训练。
- 新 4–7 每一实际 Adam 前 grad 有限且非 None；零范数合法。全部参数/buffer身份、flags、有限性与冻结值继承 S28 observer，每一实际 Tensor.backward 计数与 Adam 一致。完整八图初态注册集合由结构明确生成：5个全局参数+7×4个消费头/conf+8×2个im_conf/depth+8个buffer=57；不搬33或全四叶检查。
- 自由臂先保存完整原始初态、decoded值、objective、alignment。约束臂重做原MST仅为创建实例，必须在第一步前对自由臂已封存初态的57项 raw name/shape/dtype/flags/bytes、完整decoded/objective/alignment逐字匹配。零步来自自由臂这份同内存快照，在其400成功后只对保存副本执行一次原clean；不重新MST，不污染训练实例。
- 约束仅在已匹配MST后保存七个 `ell` 的初态均值 m0，factor=`exp(m0-current_ell.mean())`；当前 mean 不 detach，初态 factor=1，norm_pw_scale=False、adaptors及原整个3×4有效变换路由保持。有效log均值/相对尺度比 1e-5 门逐步记录；自由臂factor保持原1。不得追加k、freeze focal、旧地图重积分等第四个对照。

每个400臂403次objective=原400+getter两次no-update+原clean前一次postfinal；实际400 backward/Adam、1MST/7PnP/1alignment/1clean。零步和common各一次新clean，不调用scene目标：总2MST/14PnP/800Adam/800backward/4clean/806objective/0model。独立原公式和clean参考属于保存量核验，不额外优化。

输出根 `results/S34_geometry_producer`：`common_old/packet.npz` N4，`old_fixed_zero/packet.npz`、`old_fixed_free_400/packet.npz`、`old_fixed_common_scale_400/packet.npz` N8。每个packet六字段全部FP32：depth/conf `(N,384,512)`；point_cloud `(N,384,512,3)`；focal `(N,1)`；pp `(N,2)`；c2w `(N,4,4)` optical。conf已经原clean；consumer不再次clean。`output.npz` 保留原完整 producer 接口，packet是其逐字副本。PASS回执含 `contract_sha256`、`outputs` 相对路径SHA、provenance/实际次数/共同old seal；old depth始终预测值而非GT。新源码封存、原S26B绑定、输入assets、运行实际loaded模块均核；数组SHA仅从旧回执继承至候选，未来实际worker检查，不能称准备时已读bytes。

资源：顺序 CPU8；common 120s/4GiB；free和constraint各240s/8GiB；启动空盘10GiB。producer budget合计600s；consumer整段120s/4GiB、score120s/2GiB归独立模块，共总840s。三个独立CLI worker可供根外控，也有仅producer的受监督dispatch。错误或资源超限保留旧文件及FAILED；无自动重复/减步/改容差。全部4packet输出封存前consumer不得开始，最终3条件预测封存前scorer不得读GT。partial PASS仍不能越过失败的总barrier。

默认 NMS/latent 历史不存在，最终 context IDs/视频不执行。真实 map/render/来源票权变化也不等于质量改善。只有新四帧原规则的评分及实际consumer差异用于这一个pilot；普通尺度约束不称创新，不继续三个短窗调参。
