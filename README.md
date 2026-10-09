# Geometry-aware World Modeling

> **当前状态请先读 [`CURRENT_STATUS.md`](CURRENT_STATUS.md)**（2026-10-09 更新）。下文为早期 S0–S7 阶段说明，保留作历史。

本机可复现的几何记忆部件研究。当前已完成固定源码审计、S0/S0b人工记忆诊断、S1人工最终选图诊断、S2真实RGB-D接口检查、S3真实测量对照、S4真实模型两图检查与S5真实模型三段72图检查、S6学习几何选帧与S7固定观测事件重放。完整视频生成仍是后续独立验收项。

先读 `docs/START_HERE_CN.md`、`docs/S7_RESULTS.md`、`docs/S6_RESULTS.md`，此前阶段见S3/S4/S5_RESULTS。S0-S3英文正文见 `docs/TECHNICAL_REPORT.md`，学习几何补充见 `docs/LEARNED_GEOMETRY_REPORT.md`，原proposal交付跟踪见 `docs/PROJECT_DELIVERY_TRACKER.md`。持续状态以 `RESEARCH_MEMORY.md` 为准，按实际时间记录的行动在 `RESEARCH_LOG.md`；原始事件账本是只追加的 `research_events.jsonl`。

## 当前结果

S3包含18案例、36地图、72配对查询条件及144个查询条件×检索宽度记录，来自一个环境的12个实际查询。原始测量主测试使用其中8查询，两档分辨率都0/8换图。每帧平均位置没有带来主条件的最终选图收益。中位深度差略低，但大残差和低共同覆盖仍存在。完整负结果、控制和误差分布全部保存。

S0/S0b各216配置，另12空间索引诊断；S1有192个合成配对配置并重复验证。合成配置不能算真实场景，Kinect测量不能算无噪三维真值，检索支持不能算视频质量。

S4独立CUT3R两图适配运行CPU/MPS成功，首图尺度校准后第二图MAE32.324mm；S5三块各24图CPU完成，主测试8图平均逐图MAE72.121mm，误差曲线非单调。这些是不同图像/口径，不直接与S3比较精度。参数/输入/保存输出FP32，保留官方内部RoPE FP16转换。模型成功不代表完整VMem或新视频生成。

## 本机复现

确切环境为Python3.12.14，依赖固定在 `requirements-rgbd.txt`。现有 `.venv` 已完成依赖安装。新机器解包后进入项目目录：

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-rgbd.txt
.venv/bin/python -m unittest discover -s tests -v
```

只核对保存结果，无需下载大模型或原始数据：

```bash
.venv/bin/python scripts/validate_rgbd_outputs.py
```

官方TUM归档为448,204,271字节，解包与完整哈希记录在 `data/tum/download_manifest.json`。复现包包含清单，不包含原始数据归档；当前电脑项目目录中已有完整数据，请勿重复下载。新机器可用以下入口从官方源下载，网络中断时续传：

```bash
.venv/bin/python scripts/download_tum.py
```

从真实数据重新建图和评分，**必须用新输出目录**。下列名字仅供首次重跑使用；已有同名目录时换新名字，不删除已有结果：

```bash
.venv/bin/python scripts/run_rgbd_qa.py --output results/rerun_S2
.venv/bin/python scripts/run_rgbd_experiment.py --output results/rerun_S3 --workers 2
.venv/bin/python scripts/validate_rgbd_outputs.py --qa results/rerun_S2 --experiment results/rerun_S3 --data data/tum/rgbd_dataset_freiburg1_xyz
.venv/bin/python scripts/analyze_rgbd_experiment.py --input results/rerun_S3
```

S0/S1重跑入口：

```bash
.venv/bin/python scripts/run_memory_pilot.py --out results/rerun_S0
.venv/bin/python scripts/run_memory_pilot.py --config configs/memory_recovery_leaf_control.json --out results/rerun_S0b
.venv/bin/python scripts/run_retrieval_pilot.py --out results/rerun_S1
```

每次运行会保存代码哈希、源码快照、参数、依赖版本、平台和实际起止时间。分析数字是描述性结果，代码测试数量不代表研究贡献大小。首轮源代码和当前维护版本有已记录的差异，严格复现首轮时使用对应结果目录里的源码快照。

## 文件与证据

- `docs/S2_S3_PROTOCOL.md`：查看数据前冻结的真实实验设计。
- `results/S3_rgbd_memory/`：每例原始记录、地图、来源、深度、独立验证、完整表格图表。
- `results/S3_rgbd_memory/posthoc_residuals/`：看到结果后追加的尾部诊断，保留所有误差，不更改主指标。
- `docs/S3_INDEPENDENT_AUDIT.md`：独立重算与解释边界。
- `docs/LITERATURE_VERIFIED.md`、`docs/REPORT_CITATION_AUDIT.md`：官方文献与独立引用核验。
- `vendor/`：固定VMem来源和MIT许可。S3使用官方单叶合并语义的加速对照，不复现默认八叉树分区。
- `data/cut3r/`、`docs/CUT3R_LOCAL_READINESS.md`：独立CUT3R准备和真实运行状态，始终与S0–S3证据分开。

没有授权给导师或他人发送消息。课程真实学习时间、导师会议和最终提交由实际活动记录，不能由程序运行补填。

## 最新S6–S7

S6独立3453项核验通过，S7独立9827项核验通过。S7显示本设置下位置效果依赖关联轨迹，B2稀疏条件中总效应为零也存在条件效应抵消；NMS与候选限制需分开。两档密度及同房间8查询不能证明一般化或视频改善。25篇问题导向综述见docs/LITERATURE_SYNTHESIS_V2.md，引用独立复核和两处限定修正已完成。
