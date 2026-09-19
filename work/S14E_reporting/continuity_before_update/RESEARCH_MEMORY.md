# 当前研究记忆

更新：2026-09-06 16:12:44，北京时间。S14D-I已实际在本机跑通无目标RGB的CUT3R direct ray-only查询，并通过独立保存结果复核。它是接口验证，不是新方法/准确率/视频结果。成功阶段不重跑；完整主账research_events.jsonl只追加。

## 接手与授权

- 先读AGENTS.md、本文件、RESEARCH_LOG.md最新事件、docs/RESEARCH_WORKFLOW_CHECKLIST.md；全路线docs/RESEARCH_HANDOFF_CURRENT.md（当前第22节），工作区根同名中文交接。主账优先于outputs日期快照。
- ROOT=/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling；WS=/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip。用户是新手，用简单中文说问题、动作、结果、下一步，尤其分清真实照片/人工条件/模型输出。
- M3 Max 64GB，CPU/MPS，没有远程GPU/CUDA。已有约3GB CUT3R权重与环境，勿重复下载。用Supervisor相关skills、本地Claude技能说明、检索与多agent；不调用Claude模型/CLI，不发导师消息/邮件、不提交个人信息申请、不虚构科研工时/会议/课程提交。
- 保护原proposal、失败目录、冻结文件和旧ZIP；上层Git含家目录，不全量stage/commit。每轮通过scripts/research_log.py记实际发生与补记时间；主记忆保持短，旧长版保存在work/S14D_reporting/continuity_before_update/RESEARCH_MEMORY.md和更早阶段备份。

## 先前已证据化的结果

- S6/S8各3次CPU预训练CUT3R，20history+4query真实RGB，有输出和metadata；S6北京时间09-05 23:44—23:45，S8 09-06 03:43—03:44。旧query仍img_mask=True/ray_mask=False，仅update=False，目标位姿依赖真实query RGB。不得把旧评分前特征说成生成前可用。
- S7/S8位置/来源因素效果依场景变化。S12同14候选/同4输出/相同NMS，来源14减姿态14：S7test -2.3389606843pp，S8test +4.3829196654pp；均有预测几何，信息/计算成本不天然相同，24相关已见查询不是独立场景。见docs/S12_RESULTS.md。
- S10约7.78倍仅固定CPU渲染组件；S13枚举164328组合为借用实测答案且放松NMS的事后oracle，不是可部署收益/纯排序损失/新方法。源冻结/旧回执限制及勘误保留在docs/S13_RESULTS.md、S12_MANUSCRIPT_HASH_ERRATUM_2026-09-06.md。成功不重跑。
- S14A真实整理24×15评分前特征，360值独立通过。S14B实际测量16,164点/88,088历史预测观测；单来源零不等于准确，多来源非零不等于错误。恒等式D=B+A及m=2依赖不能当独立信号。见docs/S14A_RESULTS.md、S14B_RESULTS.md。
- S14C实际在固定24已见query检验四图历史质心分散差：S7 rho=-.3043478261，S8=.0591312396，否定该有限“两场景均正向”假设；S8每块指标恒定但目标效果变，block1优劣变号。不同算法复算/5826成稿检查通过。停止本粗代理调权挽救，不外推全部几何方向无效。见docs/S14C_RESULTS.md。

## 最新S14D-I真实执行与界限

- docs/S14D_RAY_ONLY_RESULTS.md为本轮结果入口。S14D_TARGET_VIEW_DESIGN_DRAFT.md的普通旧缓存覆盖仅设计，未执行；优先解决合法目标输入域。S14D_TARGET_VIEW_NEAREST_METHODS.md核4近邻：COVRAG any-hit不等于实测遮挡，MVS参考图已存在，I3DM推理目标只有camera/rays，VMem也已有目标渲染。新机制尚未定义/认证。
- 实际生效docs/S14D_RAY_ONLY_EXECUTION_MANIFEST_V2.json SHA6aa1dd58f2c7651aacdc5382811412005500266ec338d55a5c351727cc1700cc，UTC08:02:49；138身份含20history图、99上游py、已有权重/源码/控制。V1比最终准备文稿早约4秒，仅2控制文稿SHA变，最终门拦下且V1未执行。原V1/阻断回执保留，输入/代码/数值合同未改。
- 新模型运行UTC08:04:50.174239—08:05:09.825945（北京时间16:04—16:05），results/S14D_ray_only_probe。只S8block0前20张真实历史RGB；目标RGB、GT、旧NPZ读取0。原latent未存，本次新ray-only条件必须重建history。
- 4人工目标：最后新history预测c2w原位及local +x/-x/+z，d=.05*median(||t_i-t0||>1e-6)=.03645174472083342模型单位；不是米/真实待评分轨迹。K用官方pseudo，f=sqrt(224²+224²)、pp112。
- 官方viewer ray为ro=t、rd=normalize(R K^-1[u,v,1]+t)，含平移，不是标准纯方向。以AST原样复用；direct接口与mixed路径不默认等价，没有新增shape适配，仅旧signed RoPE兼容。实现scripts/run_s14d_ray_only_probe.py SHA859b0eb55da5751b72d9b65956cdbff1b19c9cb959c5c542687500a5bcef049a。
- 5 calls=Q0NaN占位、Q0zero占位、Q1、Q2、Q3；每次6tensor全部finite。Q0所有输出字节相同；5state字段×5calls前后完全相同；query image encoder batch0、ray encoder5。三位移最大pts3d差4.3098335/3.8044477/2.4422059，仅条件响应，不证明质量。
- 外部caller22.792299秒、RSS采样峰6,364,905,472B；模型自报峰6,409,420,800B；history前向7.652037秒。不同计时/内存定义分别保存，不是视频耗时/加速。资源监测600s/32GiB通过。
- 独立核验UTC08:05:45.742134—08:05:48.503971 PASS，results/S14D_ray_only_independent；9NPZ/75数组、200704条ray、652组核查。独立ray/四元数/target公式，无模型重跑；atol1e-6/rtol1e-5预定不变，ray maxdiff3.509282475722131e-8，K FP32/FP64最大差6.022567333729967e-6。核验源码SHA34d56c25bbd49ab7fd349d57cae6c960a23c22bce056f3ed836ad5c26a1f5d5d。
- work/S14D_reporting有全部5调用CSV和共享完整色域z图；图不是照片/GT/视频。运行前67独立人工例和核验16数学例/398人工runtime检查仅代码准备。失败计数/dummy字节/caller清理修订旧版都保留。

## 下一项实质工作与场景缺口

1. 不重跑已成功S14D-I。先制定相机坐标/尺度与合法输入合同：若给定轨迹位姿/标定属于目标条件，所有方法必须共享并显式声明；历史对齐与目标评分分开，目标RGB/深度只能在预测封存后评分。不能再从query RGB估姿后宣称没有目标图依赖。
2. 普通覆盖、历史之间MVS式一致性与相机基线均已有先例。明确新信息及可推翻预测后，才定义新冲突/选图方法；旧24seen只作探索，不继续无穷调特征求正相关。
3. docs/S14_NEW_SCENE_IDENTITY_AUDIT.md：fr3房间关系未知，7-Scenes原版未配准不能直接接旧像素评分；Bonn static_close_far为新采集候选。仅HTTP范围读493422B目录并独立核3508成员，没有新图像/GT内容/整包下载；下一步可按冻结采样/标定协议推进公开数据本地使用，缺独立license命名文件不自动等于禁止本地研究。真实房间/训练接触仍未知，新增严格独立测试组0。
4. 保持完整VMem生成、未见场景真实质量、新方法效果、导师活动/课程工时/最终提交为未完成。docs/PROJECT_DELIVERY_TRACKER.md仍为真实验收边界，不能把本接口成功写成整个项目完成。

## 定时和交付

- automation每30分钟本聊天检查与接续已授权；七项状态写workflow_checks.jsonl，重要实质结果通知，普通检查只留本地记录。电脑/应用需运行，不能把计划频率当历史准点完成。
- 最新全量路线见当前handoff和主账；outputs旧S13/S14A/B/C快照保留不改。新S14D增量交付回执完成后见docs/S14D_DELIVERY_RECEIPT.json。本轮交付WS/outputs/S14D无目标照片模型实验_2026-09-06_161427已完成：286载荷77,102,109字节，manifest SHA f9b682e78ccbc0a16ac13c43c4b93fb81faac8370d86447609ccb31370a5d084；复制逐项通过，已有权重不重复打包。
- 真实照片入口WS/outputs/独立场景验证/真实照片_72张（72单帧+3拼图）及早期实验用的真实照片_72张；模型预测可视化必须明确标注，不能混作实拍。

- S14D独立成稿审读PASS：369项身份/记录/转写和实际PNG检查，见docs/S14D_COMPLETION_REVIEW.md。

## S14E准备接续（2026-09-06T17:00:35+08:00）

- 方案docs/S14E_KNOWN_CAMERA_DESIGN_DRAFT.md、坐标审计docs/S14E_CALIBRATION_AND_COORDINATES_AUDIT.md和入口scripts/run_s14e_state_reuse_queries.py已准备，仍待根整合/独立前审/冻结；S14E真实数组、模型、深度评分未执行。
- 必须同时读work/S14E_calibration_audit/scale_definition_clarification.md：原审计反向OLS未采用，最终s为模型单位/米，target平移s*A*GT+c、评分self_z/s。原稿保留，不可混用。
- 下一步完成只读历史预测和允许轨迹的相机准备/基线，恢复旧state先做Q0一致性检查再4个真实深度时间相机查询；预测封存后才读取4目标深度评分。当前只完成方案和程序自检，不是新的质量实验。
