# S104：CUT3R × ICL-NUIM 单次 RGB 前向（SuperPOD）

> 实验编号说明：S104 = 「CUT3R 在 HKUST SuperPOD 上对 ICL-NUIM 四帧真实 RGB 的单次前向」。
> 编号不表示实验成功，也不表示产生了科学结论。本批次实际结论见 [`RESULTS.md`](RESULTS.md)。

## 这个批次是什么

2026-09-15 全天在 HKUST SuperPOD 集群上做的工作：接上学校超算 → 建 conda 环境 → 让原 VMem 源码可导入 → 下载并审查 ICL-NUIM 数据集 → 编译 cuRoPE CUDA 扩展 → 让 CUT3R 在 H800 上跑通一次前向。

这些工作的脚本、SLURM 输出和回执当时**散落在集群家目录 `/home/yliutz/`**,没有进入项目树,项目主账也停在当天 02:33:48。本批次把它们**逐字节归档并建立清单**,并补记入账。

## 目录

```
S104_cut3r_icl_rgb_calibration/
├── README.md                  ← 本文件
├── RESULTS.md                 ← 实际发生了什么（主文档）
├── MANIFEST.json              ← 69 个归档文件：源路径 / 字节 / sha256 / mtime
├── EXTERNAL_ASSETS.json       ← 7 项未复制的大文件，路径 + sha256
├── consolidate_s104.py        ← 生成上述清单的脚本（可重跑，幂等）
└── artifacts/
    ├── scripts/               ← 10 个当时实际执行的脚本
    ├── jobs/                  ← 6 个作业输出目录（含封存的 raw_outputs.pt）
    ├── slurm_logs/            ← 18 个 sbatch stdout
    ├── env_bootstrap/         ← 17 个环境构建日志 + pip freeze
    └── data_receipts/         ← 数据回执 / 归档审查 / 抽样解码 / 导入探针
```

## 来源与 provenance

- **源位置**：`/home/yliutz/`（SuperPOD 共享 NFS 家目录）
- **归档策略**：`shutil.copy2` 逐字节复制，**源文件一律未改动、未移动、未删除**
- **完整性**：69/69 文件 `sha256_matches_source == True`；封存预测 `raw_outputs.pt` 的 sha256 与作业回执内记录值一致
- **不复制的大文件**：4 个模型权重（约 9.5 GB）、ICL-NUIM 数据归档（678 MB）、Vmem 源码快照，改以绝对路径 + SHA 记录于 `EXTERNAL_ASSETS.json`
- **重跑归档**：`python3 consolidate_s104.py`（幂等）

> 家目录中的松散原件仍保留在原处。**本项目树内的副本是这 69 个文件的归档正本**；若两者出现分歧，以 `MANIFEST.json` 记录的 sha256 判定。

## 状态

| 项 | 状态 |
|---|---|
| 归位与清单 | ✅ 完成（69 文件，sha 全对） |
| 补记入账 | ✅ 完成（见 `research_events.jsonl` 两条补记事件） |
| 独立复算（不同作者） | ❌ **未完成** |
| 标定评分 | ❌ **未执行**（只保存了原始预测） |
| Gate 0 数据资格 | ❌ **仍为 `BLOCKED_TIMESTAMP_AND_EXPOSURE_AUDIT_PENDING`** |
| 科学结论 | ❌ **无** |

## 不做的事

- 不把 GPU 分配算作模型前向
- 不把 `IMPORT_OK` 算作前向可运行
- 不把编译成功算作科学结果
- 不把 4 帧同轨迹画面算作 4 个独立实验
- 不因日志写 `SUCCESS` 就认为结果已被验证
