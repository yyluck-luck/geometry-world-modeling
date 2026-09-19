# 当前研究记忆

更新：2026-09-06T17:34:13+08:00。S14E已完成真实模型查询、4目标传感器深度评分及不同公式复核；93.0974%对85.8008%仅是已有CUT3R组件在已见单段的结果。新方法、未见场景与完整视频仍未完成。

## 接手原则与资源

- 先读AGENTS.md、RESEARCH_PRINCIPLES.md、本文件、最新RESEARCH_LOG.md、docs/RESEARCH_WORKFLOW_CHECKLIST.md。当前完整路线docs/RESEARCH_HANDOFF_CURRENT.md第23节；主账research_events.jsonl优先于outputs日期快照。
- ROOT=/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling；WS=/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip。用户新手，简单中文解释问题/动作/证据/下一步；已授权自主本机研究、相关skills、检索和多agent，无须重复确认常规步骤。
- M3 Max64GB，无远程GPU；已有约3GB CUT3R权重和环境。.venv-cut3r用于模型/prepare/score，.venv用于独立NumPy/SciPy，/opt/homebrew/bin/python3有Matplotlib。优先复用，不重复下载。Claude指本地skills，不调用Claude模型/CLI。
- 不发送导师消息/邮件、不提交个人信息申请、不虚构阅读/会议/课程工时。保护原proposal、冻结文件、失败目录与旧ZIP；上层Git含家目录，不全量stage/commit。
- 每步通过scripts/research_log.py写实际/明确补记时间、动作、结果、证据和下一步；每30分钟七项流程检查写workflow_checks.jsonl。正常检查不是科学结果，运行频率不是历史准点完成证明。

## 保留的历史发现

- S6/S8各3次20history+4query真实RGB模型推理；旧query仍img_mask=True，目标pose来自真实query RGB，不能声称生成前已可用。
- S12同14候选/4输出/NMS，来源14减姿态14：S7 test -2.3389606843pp、S8 +4.3829196654pp；依场景变化，信息/计算成本不天然相同，24相关已见查询不是独立场景。S10约7.78x仅固定CPU渲染组件。S13事后oracle164328组合借用实测答案，不能部署。
- S14A整理24×15特征，S14B测16164点/88088历史观测；分散非零不等于几何错误。S14C粗历史分散假设两场景未同正向，rho分别-.3043478261与.0591312396；停止调权挽救此有限设想，不能外推全部几何研究失败。
- S14D在09-06 16:04—16:05实际用20历史实拍重建state并做5次ray-only查询，4相机人工设定，只是接口验证；旧Q0NaN/zero输出相同、状态不变、独立652组复核。其存档与图完整保留，不重跑成功阶段。

## 最新S14E实际完成

- 入口docs/S14E_RESULTS.md；固定协议docs/S14E_FINAL_PROTOCOL.md。新增RESEARCH_PRINCIPLES.md并加入AGENTS必读，WS根科研原则.md是链接入口。成稿审查380项PASS，见docs/S14E_COMPLETION_REVIEW.md；交付回执见docs/S14E_DELIVERY_RECEIPT.json。
- 数据仅已有TUM fr2_desk的S8 block0。history0..19取RGB时间，target20..23取depth时间；已知GT轨迹/K是共享允许输入。GT深度在全部预测seal后读，目标RGB直到报告图阶段才读。没有新采集/新场景。
- prepare实际UTC09:29:25.343400—09:29:27.035410：仅40旧S8历史self/pose数组+1旧S14D history_poses，字节pose和两个可核state锚一致；轨迹20926行允许读取。20history拟合正向s=1.1146619883400035模型单位/米，主depth=self_z/s；RMS=.04417737652322564模型单位。原反向OLS审计未采用，必须读work/S14E_calibration_audit/scale_definition_clarification.md。
- 新模型UTC09:29:44.905865—09:29:55.198147：恢复五state，不重跑history；call0旧Q0zero与旧call1全部6tensor byte一致，随后call1..4四真实相机query成功。17数组、5ray、图像encoder0、图像打开0、state不变。caller12.996054秒/RSS5935628288B不是加速或视频耗时。
- score UTC09:30:19.420146—09:30:19.853587：combined预测seal核后才hash/open4实测深度，PNG/5000、nearest299×224 crop[37,0,261,224]，全部GT正有效域，无stable-mask/置信过滤/逐目标尺度拟合。
- 等query δ1（缺预测失败）：ray .9309740087065843、history_zbuffer .8580083776636267、history_constant .6981274131235827；ray比warp +7.2965631043pp。三方法共同域MAE：.20219529707686087/.24322050547756957/.4296066311429834米。四query均ray主指标更高，仅167400相关像素访问，不算独立样本。
- 基线是全部20history预测self-z标准pinhole重投影、原预测history pose与共享全局对齐，未逐history GT纠正；常数=全历史正有限z中位数/s。没有四图选择/NMS，不同路线计算成本分别记录。
- 独立UTC09:30:28.550915—09:30:31.873059 PASS：166身份/106数组/4GT/868检查，不重跑模型。不同实现SciPy SLERP、fsum、连续分量投影+固定量化+scatter、整数GT映射、标量评分；团队内复核，不称第三方复现。
- work/S14E_reporting：真实4×5图PNG/SVG+12行CSV，所有16深度图同完整色域.947522688243398—10.068619415887262米；4RGB仅报告时读取，根实际查看无裁切。它含实拍、传感器测量和模型输出，分别标注。
- 准备阶段的跨condition/scale封存绑定、δ1浮点边界、半像素离散量化和不可覆盖预期SHA均在真实运行前修正，旧稿/人工反例保留；最终前审218通过后才冻结。人工检查不计真实样本，真实阶段一次成功。

## 冻结入口与下一步

- docs/S14E_PREPARE_EXECUTION_MANIFEST.json SHA ecf06af25ec093a020b8820aedaac1c413bfd1ca3f0d4d4f945871778a63cbd3。
- docs/S14E_SCORE_EXECUTION_MANIFEST.json SHA 7b11230721d9225ed962f96ddb672165b68de00b4e448133b94e3a694417e900。
- docs/S14E_MODEL_EXECUTION_MANIFEST.json SHA a5c040fed44603821bf65aa12fb2b6546be9f261dd427800397e99d49153da62。
- docs/S14E_COMBINED_PREDICTION_SEAL.json SHA f26981965b30ebdd7609088eab7a84a509aabcfd03f83bd3eff5c01e8ba671eb。
- 不重跑S14E。把“模型补出的几何何时可靠、何时应优先保留实拍历史证据”变成明确机制与可推翻预测；需对照已知MVS一致性/置信融合/目标视角覆盖近邻，普通组合不能当创新。当前是后续问题草案，未验证新方法。
- 新数据Bonn static_close_far仍只范围读493422B目录/3508成员，未下载图像或新GT；先固定采样/标定与身份后推进真实新场景验证。fr3场景关系、训练接触与真正独立性仍未知，新增严格独立测试组0。
- 完整验收docs/PROJECT_DELIVERY_TRACKER.md：新机制有效性、未见场景效果、完整VMem视频与最终提交仍未完成。旧记忆全稿在work/S14E_reporting/continuity_before_update/及此前备份。

最新交付：/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/S14E真实深度实验_2026-09-06_173755，777载荷、141383378字节；manifest SHA efb1d5753f616aeb50e2a16fff0409e5e63e4fe639235e112995573417d60800，全部复制字节通过，旧两ZIP不变。快照反映打包时刻，后续主账以原项目为准。
