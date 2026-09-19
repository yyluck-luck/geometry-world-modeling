# S32 候选：四个时间预选窗口，先生成各自正确参考系的新预测

本文件是执行前计划。当前仅源代码／JSON 元数据准备，未加载模型、读取真实 RGB／NPZ／sensor GT、初始化 GA 或评分。阶段 A 可以单独审后冻结与执行；本目录第一版生产入口只实现 A，不把阶段 B 的准备写成可执行或已完成。

## 研究问题与边界

按照 Supervisor `02_Idea_Generation` 的强基线→真实失败→最少变量判别，以及已读 `work/S31_next_decision/review.md`，结束开发 common4 的调整。新问题是在四个预选时间窗口，“单位尺度零步／修 getter 后原 400 步／同终点加原 S31 公共标量”是否仍呈现相同关系。三个都是普通对照，不是新算法。每个场景曾经使用；具体暴露史保留选择清单原文，不称盲测、未见场景或视频验证。

## 选择与缺失保持

唯一选择源为 `work/S32_selection/selected_windows.json`：每个原 `rgb.txt` 共 N 帧，j=1,2 起点 `floor(j*(N-4)/3)`，取原 RGB 列表中连续四帧。执行入口不依据内容、loss、误差、运动量或缺失重选。

原元数据清单的 `frame.sha256=null` 是选择准备状态。root 已另存 `work/S32_input_freeze/selected_windows_rgb_sealed.json`，SHA `ac2c04437afa62fbaa5f03e5159ba06960131d9a2405afd5f94eef0c2f9ed318`：只读取已选择的 16 个 RGB 文件字节封存，未解码 RGB 或读取 sensor-depth PNG；原选择 SHA `4574c2635851e83f5389da0d099819e7cbfd2ad9b8fe543ddf163e0fbf7e6cc6` 不改。作者准备只读取该 JSON。A 合同逐窗同 id/scene/index/source_rgb_index/path/rgb_time 对上它；所有 16 个 RGB SHA 必填。A 不需要 GT 相机。

当前元数据发现 `fr2_desk_j1` 四个 GT pose 配对均缺失；保留该固定窗口。A 对全四窗各 fresh4，仍是 16 张照片。B 不能伪造相机、插值、扩大阈值或替换窗口：没有完整共同相机条件则整窗三端点 NA，并写原缺失原因。最终设计矩阵仍为 4 窗×3 端点×4 帧=48 行／12 窗端点组；执行成功和有定义的组数分开。

## 源码确认：选择原消费者实际前向

- 固定 VMem commit `39291e4f272f6b4f270691d930926ab5930f942e`，`modeling/pipeline.py:86-90` 加载 CUT3R512DPT 后调用 `.eval()`。A 使用已有隔离副本 `work/S17C_interface_preparation/isolated_vmem_source/extern/CUT3R`；保留已存在的 `weights_only=True` CPU 安全加载兼容，以及 `models.pos_embed.RoPE2D→models.rope_cpu.RoPE2DPyTorch` CPU wrapper。这个 wrapper 已有有符号旋转和FP32计算→恢复输入dtype路径，没有 get_cos_sin，不能套用 S21 的 fallback helper；A 不再安装该 helper。保存实际 CPU impl 调用计数、完整来源与常数。没有改原源或新下载权重。
- `surfel_inference.py:335-341,355` 使用 `prepare_input_from_pil`，随后原 `src.dust3r.inference.inference`，并非 `inference_recurrent`。S21 original4 走过后者，是已有可行性参考，不能声称本次二者数值已验证相等。直接使用原消费者 `inference`，不为比较再运行一轮。
- `src/dust3r/inference.py:225-247` 的原 inference 有 `@torch.no_grad`，`loss_of_one_batch:74-80` 关闭 inference autocast并调 `model(batch,ret_state=True)`。`model.py:813-888` 的 `_forward_impl` 只编码本次 views，在进入循环前新建 `_init_state(feat[0],pos[0])` 和 pose memory；返回初态+四帧状态。全新子进程每窗只调用一次，观察 `_init_state` 恰好一次、head 恰好四次。保持每帧原 `reset=False/update=True`，不逐帧重置。
- `surfel_inference.py:446-539` 的原 PIL 入口生成 identity 输入 camera_pose、空 raymap 和有序 idx。A 原样调用并保存四个预处理 img/true_shape，用于将来 B 同入口逐字核验。不能用相同 shape 代替相同 tensor。
- `surfel_inference.py:355-402` 原组装是 anchor0→j 的有向星形。实际 GA 使用 pred0 的 `pts3d_in_self_view/conf_self`，以及 j=1,2,3 的 `pts3d_in_other_view/conf`。A 保存每帧完整六头而不是只存使用的头，并核原星形 idx 与四类实际消费张量逐字对应。
- `prepare_output:174-236` 与 `cloud_opt/dust3r_opt/base_opt.py` 是 B 实际 GA 入口；不是同目录另一份旧 `cloud_opt/base_opt.py`。源码跟踪与哈希见本目录 `source_read_manifest.json`。

## 阶段 A：本版最小可执行入口

`run_inference.py worker --window ID --contract FILE --sha256 SHA` 在独立进程完成：

1. 核 root 冻结合同、选择身份、16 RGB 中本窗四帧 SHA、203 个已固定几何源身份；权重沿用已封存 SHA 和 size/mtime 身份，不重复读 3 GB 做哈希。
2. 复用 S26 原函数 adapter 的 configure/load_original_views；保持 CPU8、FP32、seed0、原 eval、无外层 autocast。所有 loaded geometry namespace 必须来自同一个已绑定隔离根；加载 checkpoint 所有 keys matched，否则保留失败。
3. 原 `inference` 单次 fresh4，head hook 原样保存 24 个 FP32 finite 张量。两个 confidence 还须正值。六头固定 shape：点图/rgb=(1,384,512,3)，conf=(1,384,512)，camera_pose=(1,7)。保存与返回值全 24 头逐字核验，只观察，不重跑模型。
4. 原 star 组装检查 idx=(0,1),(0,2),(0,3)，以及 pred0 self/conf_self 与 predj other/conf 的 bytes。只组装输出字典，不调用 GA。
5. 完整输入、预处理、四帧头、实际源、训练 flags、计数、资源与 SHA 回执封存。所有失败保留、同输出目录不覆盖／自动重跑。

`dispatch` 顺序启动全部四个 fresh child。每窗 CPU8、180 秒、16 GiB RSS；总最多 4 次 model call、16 个 head forward、0 GA／MST／backward／Adam／sensor GT。外控复用已冻结 S26B `supervised`，继承 10 GiB 空闲磁盘门，不额外构建庞大环境扫描。阶段 A PASS 只证明新推理与存档门通过，不代表深度准确或 B 完成。

## 阶段 B：独立下一冻结合同，本版没有实施

仅共同相机完整的固定窗可进入 B；TUM 相机作为显式 oracle 控制，按选择源原 timestamp 读取原 optical c2w、绝对米制坐标，进入 GA 不再 Y/Z flip。相机字节和控制 tensor 单独封存；相机与 sensor depth 的角色不得混同。

每窗 B 单独 fresh child，使用 A 原六头和逐字匹配的 PIL 张量；没有新模型。复用 S28/S30 原 observer 与 C2a 对齐：原 Sim3 `s0,R0,T0` 计算一次，仅返回 `s=1, R=R0, T=mean(given_C)-R0@mean(pred_C)`。保留原 MST/PnP；只均值匹配，不称整相机对齐，也不在优化中固定 scale。

同一次 MST 后、任何 Adam 前立即 clone 全部 33 参数／buffer 元数据和 raw bytes，保存 depth/world/focal/pp/c2w/objective 作为本窗零步；然后在同一对象状态安装已有 getter 单表达式修复，核 getter/首目标 forward 相等及所有对象、值、flags 不变。旧 S29 的 historical 初态逐字门不适用于新窗，不装作新窗应等于旧 common4。

从该同内存初态执行原 400 Adam、lr=.01、linear、原目标和原 clean。相机与 pp 冻结，depth/focal/pair 参数训练状态按原语义；全部 400 步注册 depth.grad 非 None 且 finite、旧参数约束不变、原目标/clean/backprojection 复用已核参考。每窗预算 120 秒／4 GiB／CPU8。保留原完整 trace、终态与全部负结果，禁止挑步。

按原 S31 唯一公式，每窗全部 4×384×512 预测像素计算 `k=exp(-mean(log D400-log D0))`，没有 GT/pose/conf 输入，保存 FP64 D*=kD400。复用 `decompose` 的完整分解与有效域门；非正/非有限不删点，失败保留。公共平方和比例不是 GT 误差解释率；D* 也没有构造新的完整 world/pair state。

全部预定窗口的三端点输出或明确不可执行记录先完成封存，才能统一读取 sensor depth 评分。沿原完整分母／缺失 NA 规则，48 行／12 组设计矩阵全部保留，另外报告实际有定义数量。score CPU1/120 秒/2 GiB。不得将可评分窗口均值替换原全部窗口均值；零步仍是必须同表的强对照。缺失相机窗口不是算法输赢，A 结果不作为 B 的伪造结果。

## 本轮停止与接手

root 冻结 A 后才允许任何模型/RGB；作者此刻只做源码 AST/help。A source/load/schema/star 任何失败均保留并停止，无自动重复。即便 A 完成，也必须单独完成 B 的最小实现、冻结与执行门，不能将此计划标为全 S32 已跑。当前最重要未证项是新 embedded 原 inference 的实际 CPU4 兼容与四窗资源；不在准备阶段保证成功，也不追加与任务无关的人工或性能测试。
