# 当前进行中：S15B/C

更新时间：2026-09-06T10:30:07.225618+00:00。以本节与最新主账为准，下方S15A内容保留历史。新增质量约束RESEARCH_QUALITY_TARGETS.md；并读RESEARCH_QUALITY_TARGETS_ERRATA.md，明确不得无故重跑成功阶段。

S15B真实12 RGB前缀和5次来源ray query已完成，results/S15B_prefix_proposals；提案seal已封存。8见证照片计算已完成，results/S15B_witness_costs；784块，pool399/split202/matched202，照片成本不是准确率。准备scripts/s15b_memory_consumer.py七方法同来源/相机评价，独立前审中；四目标depth尚未在本阶段打开，旧实验已见须标探索。

S15C已取前20匹配depth PNG字节并CRC/SHA核；不含后4。官方观测深度评分不用未知GT轨迹，详见docs/S15B_BONN_POSE_RESOLUTION.md。首4校准正在执行results/S15C_bonn_calibration；成功后先封预测，再score后16。模型沿用S15A，无重跑、无生成视频。

创新更新：docs/S15B_MECHANISM_PRESSURE_TEST.md确认DTAM/DSO直接先例，简单新旧配对决策Reject新方法定位。继续测组件信号，不能把换名或工程校验当PhD/CCFA创新；后续新机制必须与同信息强基线有实质区别。

三个agent并行代码/原文/独立核验；root实际执行、冻结与记录。模型成功不代表完整项目完成。

---

# Research memory — 当前接手入口

更新：2026-09-06T18:08:35+08:00。S15A已完成Bonn新来源20张原生实拍的真实CUT3R历史推理、独立数值完整性复核与实拍索引图。尚未测新来源几何准确率，未验证新机制，未完成完整VMem视频。旧S14E成功结果保持。

## 长期规则与最短接手路径

先读AGENTS.md、RESEARCH_PRINCIPLES.md、最新RESEARCH_LOG.md与docs/RESEARCH_HANDOFF_CURRENT.md第24节。按Supervisor相关技能＋本地Claude科研skills推进，不调用Claude模型。用户新手，中文清楚解释，已授权本机自主研究、不反复问权限；没有远程GPU。时间主账由scripts/research_log.py追加research_events.jsonl；每30分钟七项检查写workflow_checks.jsonl。不要把人工软件检查、真实推理、传感器评分和完整视频混称。

## 最新完成：S15A

- 用户这一轮“好的下一步开始”。入口docs/S15A_RESULTS.md；固定docs/S15A_NATIVE_HISTORY_PROTOCOL.md＋V2补充。新增数据为作者Bonn static_close_far，物理房间与完整预训练暴露未知，不称认证训练未见。
- 元数据获取仅rgb.txt/depth.txt，4次206、21987B；原RGB1752条均存在，depth1765条中15条不存在ZIP。v1实际FAIL保留work/S15A_samples/receipt.json。v2保留所有时间行、不删缺失后重选；原t0+1+0.4*i最近规则不改，所选24RGB/24depth齐全。样本work/S15A_samples_v2/samples.json SHA fdf03dc69ede6e46cf3b9f545c5b6932e8ea6270729bd9f413062b298ff64a6f。
- 只取前20history RGB，后4future target RGB、所有depth PNG及trajectory未获取。四次TLS失败保留data/bonn_s15a_history、resume1、resume2、curl；最后persistent成功原2。组合11+4+3+0+2，46请求尝试/9568993响应B，20完整RGB CRC/SHA通过；不是全ZIP下载。data/bonn_s15a_history_combined/receipt.json SHA5bc3c5c07c16dacea0f5b3a57bf0b1b34e61001357988e773b715b87c28a3d85。
- docs/S15_BONN_CALIBRATION_AUDIT.md：原PNG已否去畸变和GT光学c2w未认证，官网Tm带约1.0593尺度，不能直接作旋转。本轮原生RGB只用官方224 resize/crop；没有GT相机、尺度对齐、重投影或准确率。不能把S14E相机合同直接套过来。
- 真实模型UTC10:04:29.206155—10:04:46.670719；.venv-cut3r CPU8/seed0/FP32、已有固定224权重和99份官方源码。20张640×480原生RGB实际decode；1history forward、1image batch20、1内部乘零dummy ray、0target query。结果results/S15A_bonn_history：120官方预测＋2pose＋5最终state，共127数组。全部有限只是完成门槛，不是准确率。
- caller UTC10:04:27.933795—10:04:48.713190，总20.77924925秒、采样RSS5832261632B；runner峰值6409682944B为另一测量。不是速度对照或加速比。run_s14d_controlled.py是复用通用外部监控器，schema旧名字不等于重跑S14D。
- manifest docs/S15A_HISTORY_EXECUTION_MANIFEST.json SHA bb202b972fbc020ade5b73525e162df1f8493f1da7960c3e380722a081211d7b，151身份。seal docs/S15A_HISTORY_COMBINED_SEAL.json SHA71ac6a264d1a52909f1f8a0ab44e433afc3bb646aea18adb07fdb36f40c093e0，161身份。
- 不同作者在.venv用NumPy/SciPy实际复核UTC10:05:24.557572—10:05:25.987358：161文件、127数组、1053判定PASS，四元数独立矩阵最大差2.906570284455512e-8，tol1e-6/1e-5；平移及逐帧编码精确。results/S15A_bonn_history_independent/verification.json SHA02610c62cba5c45db52f7e7e5ae2b3df02dd88169a6b65bc49d4d5070a8da6bc。没有重跑模型/解码图片或GT；流式hash会读RGB/权重字节，不冒称零字节读。
- work/S15A_reporting/s15a_all_20_real_history_photos.png：全部20实拍、4列5行、无裁切无生成图。报告阶段另decode20张，原图不改，root实际查看；不是模型输入又多20张。原相机朝纸箱移动的照片已暴露，不能未来当未见见证。

## 创新结论与具体下一步

读docs/S15_MECHANISM_AND_NEAREST_WORK.md：Mostegel2016、Poggi2020、ConfidentSplat、Merrell2007、COVRAG及CUT3R原文约束下，普通一致性／在线置信／角度去重／混合版本Reject新方法定位。

仅条件保留：固定source_frame/source_pixel身份，提前封存旧几何和新几何，用后到实拍对这次改写作配对验证，再延迟改显式记忆。它仍可能等价旧融合；必须与同信息、同提案、同见证、同预算的绝对置信/MVS/角度桶/混合比较，暂无新方法效果。

下一实质步骤：先解决可用于光学投影的标定与pose接口，或在已知标定旧TUM上明确标为探索的最小前缀诊断；需冻结提案前缀、source身份、后到见证、相同信息强基线、拒绝条件与答案隔离。Bonn若做严格未见见证，另选只凭元数据固定的新时间段，不把本轮已处理20history重新称未见。当前四个future target仍封闭，不能先开答案决定算法。成功S14E/S15A不无故重跑。

## 继承的重要结果

S14E：已有CUT3R在已见S8 block0四目标等权δ1 93.0974%，历史重投影85.8008%，差7.2966pp；共同域MAE .2021953/.2432205米。是真实传感器评分，但仅已有组件单段结果。docs/S14E_RESULTS.md和旧777载荷快照保持。S14C粗分散特征失败、S12方向相反、S13 oracle上限不可当部署算法，均不抹去。

## 工具与资源

模型用.venv-cut3r（Torch2.7/NumPy1.26），独立用.venv（NumPy2.3/SciPy），照片图用现有/opt/homebrew/bin/python3（PIL/Matplotlib）。CUT3R checkout在工作区work/cut3r-local，commit8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf。已有data/cut3r/cut3r_224_linear_4.pth SHA7a7d83e47f822e040980c8f5aff4c15aa94366d469d3ceae51fa30cc2f62327d，不重复下载。祖先Git覆盖HOME，不全量git add/commit。完整项目未完成，见docs/PROJECT_DELIVERY_TRACKER.md。

最新交付：/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/S15A_Bonn真实照片与推理_2026-09-06_180933，636载荷文件、124693916字节；manifest SHA a1731cc1b8ee5ba1a8375dcee0fa7c96b62b264dedf366ec4cf7448ebd26eebb，全部复制字节核验通过。含20真实照片、实际127数组、99源码/技能/原文/失败/记录；约3GB权重仅索引，不是新机复跑，主账后续优先。
