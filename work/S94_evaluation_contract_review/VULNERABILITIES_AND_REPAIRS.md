# S94 独立架构审查：当前 S91 协议的漏洞与修复

本审查只检查评价协议，不把漏洞修复误写成实验结果。

## 漏洞 1：未来答案隔离写了原则，但没有可审计的执行边界

S91 已经规定选择器不能读取 future RGB/depth/pose/mask/误差，但仅写成输入约束。若所有数组在同一 Python 进程或缓存目录中可见，读取 future-valid mask、目标尺寸或提前生成的 future 特征仍可能发生，而且事后日志难以证明没有发生。

**修复：** 把选择与评分拆成两个进程和挂载阶段；`select/` 只能看到历史 manifest，请求相机和冻结模型状态，输出后先写 SHA 封存；`score/` 才挂载 future manifest。保存系统调用/文件访问审计。任何 future 路径访问直接作废 query，而不是只删一行结果。

## 漏洞 2：固定槽位数不等于固定总内存和计算成本

S91 固定 `k`，但 WorldTrace-Field 的 canonical key、MemRoPE 的不同层 cache、候选风险计算和 host 索引可能随历史长度增长。若只比较槽位数，GRC 可能以更大的 host 状态或额外前向换取优势，审稿人会认为比较不公平。

**修复：** 固定 GPU cache、CPU/host memory、读取字节、选择时间、选择前向次数和消费者 denoising 预算；逐项记录峰值。超过任一上限记 `OVER_BUDGET`，不能藏在 GPU 统计之外。WorldTrace/MemRoPE 若只报告 GPU 使用，按合同缺失成本。

## 漏洞 3：source identity 可能在融合后消失

S91 说选择历史候选，但没有强制消费者保留原始 source ID。融合后的 latent、平均深度或 KV cache 可能无法知道哪条记忆真正影响未来输出，因此 S91R-C 已出现的低 source identity 情形会再次出现；此时只能说系统有效，不能说风险校准选择了安全的记忆。

**修复：** 每槽位保留 source ID 或组成集合与权重，报告 traceability、identity match 和 collision。低于 95% 时降级为系统级比较，禁止单条记忆因果解释。

## 漏洞 4：S91 没有规定足够的独立 test 轨迹数量和统计单位

“至少 3 个未来查询”不等于 3 个独立场景；像素数巨大也不能增加独立样本量。单条轨迹的相关性可能制造稳定但不可泛化的相关性。

**修复：** 确认集至少 5 条独立 test trajectories、每条至少 3 queries；少于 5 条只能标为 `PILOT_ONLY`。先按 query、再按 trajectory 聚合，使用 trajectory-level bootstrap，不把像素当独立实验。

## 漏洞 5：只报告平均误差会掩盖 S92 已观察到的灾难性尾部

S92 显示四个目标中平均 AbsRel 变差，但约 0.595–0.647 的像素局部改善；恶化总量最高 5% 像素贡献约 0.835–0.855。若正式协议只看 mean AbsRel，方法可能在少数区域发生几何灾难却被平均值掩盖，或反过来被少数异常点误导。

**修复：** 预注册 mean AbsRel 与 worst-5%/CVaR95 同时为主报告；补充 3D/重投影误差、覆盖率和失败率，按 query/trajectory 配对。尾部指标仍是评价指标，不自动构成 GRC 因果证据。

## 漏洞 6：数据资格和单位绑定不完整

S93 的 TUM 检查已经显示，能下载 GT 文本和 AVI 前缀并不代表已取得同步 PNG 帧、相机内参、深度单位和冻结 split。若直接进入 S91，可能把格式页说明误写成实际配对数据。

**修复：** Gate0 必须保存真实 RGB PNG、Depth PNG、原始时间戳、pose、intrinsics、units、SHA 和许可记录；任何一项缺失均不评分、不启动 S91。

## 总体审查结论

当前 S91 的科学问题仍可保留，但必须采用 `EVALUATION_CONTRACT.md` 的更严格版本。合同通过只意味着“以后若取得合格数据，实验可公平执行”；当前没有新的 GRC 模型结果，也没有方法有效性或新颖性结论。
