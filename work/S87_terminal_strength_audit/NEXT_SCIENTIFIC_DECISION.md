# 下一科研决策：复用已完成控制，转向独立几何参考

UTC 2026-09-10 23:52:08–23:52:43 实际核读；SOURCE/METADATA_ONLY。0 数组读取、0 模型/评分、0 新检索。**本页纠正前稿“先做实拍正对照”的重复建议：正对照及固定错相机标签负对照已有实际证据，不重跑。** S87 当前合同/主量不改；此页是下一步决策，不是新增执行结果。

| 我提出的控制 | 已有实际证据 | 决定 |
|---|---|---|
| 实拍应比旧生成更符合请求几何 | S73 复用 S72 四实拍，比较 A0/B；实拍极线中位 1.34–4.22 px，生成 21.65–224.64 px。完整分母/共享点已保存，target23 共享点为 0，四目标事件仍 UNKNOWN。 | 已做，不重跑；只说明接受对应的条件差别。 |
| 同一对应应更适合原标签而非固定错标签 | S74 的 638 条实拍对应，及 S77 对生成扩展的 20↔23、21↔22 交换。实拍四个 wrong−correct 中位均正；A0/B 均只有20/21正，22/23负。 | 已做；不是恢复真实相机，也不能把 S77 说成尚缺负控制。 |
| 结论是否只由一种匹配器造成 | S80 同批 RootSIFT 的 BF/LG：实拍原/错标签差四目标均正；旧生成仍20/21正、22/23负。两匹配器合计5110生成接受记录的原标签≤10 px均为0。 | 已做；完整规则/身份/覆盖一起改变，不识别“匹配数量”的因果。 |
| 加入外部源深度后，实拍具体位置是否仍较近 | S81 已有八条 real×BF/LG 正对照；中位1.875–8.346 px，对旧生成40.674–314.255 px。1313源点、968深度有效点和全部24行保留。 | 已做且有误差尾部，不能再次要求“先证明实拍不是全失败”。 |
| 把源19原图重复当目标20–23，再以 sensor-Z 检查不动视角 | 所核合同只有 real/A0/B 目标；S81 仅按原 target_id 投影，没有此重复源图臂，也没有 sensor-Z 下的错标签交换。 | **在本次有限证据范围内未找到这两个精确操作**；不同于已做的极线标签交换。它们不是推进下一独立场景的必要前置，不因缺一格而补跑。 |

前稿另一要求“匹配不能先按被检验几何筛选”也已有落实：S80 BF 用互相最近邻与比例规则，LG 用互选/分数规则，均无请求 F 过滤；S81 再读取这些冻结对应算距离。仍可能误配，不能据此认证物理身份。

**唯一优先入口：核一个独立、同一时刻多视角小片段是否实际可得。** 复用前批 PointOdyssey 官方证据，下一步只定向核清：①v1.2 中具体同步多视角场景/帧号和可有界取得的文件，不能把3.32 GB sample或26.5 GB test的链接当已取得；②该场景是否独立于当前选参及模型训练，源 RGB/共同请求 K、world→camera RT 与目标评分标签的分离、坐标/单位/可见性对应；③GitHub 数据许可 CC BY-NC-SA 4.0 与作者 HF MIT 声明冲突。未满足则结论为数据可行性 UNKNOWN，不启动新生成。它提供的是**模拟器参考**，不是新真实传感器证据；精确真机相机/同步 RGB-D 的小片段目前仍未落实。

现有 TUM 单锚点的17.126 ms不同步、近似K、无去畸变、目标遮挡UNKNOWN，不能靠重跑旧正负控制消除。真正还缺的是**独立场景及可信参考下，生成点身份/重影/失配的固定处理**；标签给出了应在何处，却不会自动标出生成图的哪个重影是真对象。未来若观察器在新数据无法稳定区分真图与错误相机，停止该几何解释；不要不断换观察器直到出现有利结果。现阶段优先完成 S87 科学闭合，不把追加评价当新方法。

核读依据：S73 `CONTRACT.json`、`measure_v2.py` 相关段、[不同作者结果审查](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S73_generated_fixed_geometry/independent_result_01/REVIEW.md>)及root接受；S74/S77 root接受及 S77 PROTOCOL；[S80结果](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S80_lightglue_observer/S80_RESULTS.md>)与 RUN_CONTRACT 的输入/接受规则；[S81结果](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S81_anchor_depth_reprojection/S81_RESULTS.md>)、root接受、CONTRACT 24行及 `run_reprojection.py` 135–173行。新数据缺项复用 [前批来源核验](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S87_terminal_strength_audit/INDEPENDENT_GEOMETRY_EVALUATION_OPTIONS.md>)，本批不重新访问网络。
