# Held-out 场景暴露审计（2026-09-17）

**目的：** Gate0 阻塞项 5 要求"取得并哈希一个**冻结前无元数据暴露**的独立场景"。
本审计逐项核对本项目**已经接触过**哪些数据，并给出仍然合格的候选。

**方法：** 对 `research_events.jsonl`（2000+ 条主账）与 `docs/` 全文做名称匹配计数，
并核对本机与 SuperPOD 上的实际落盘数据。计数为**机器可核**的下限，不依赖记忆。

---

## 1. 已暴露 / 不合格（不得用作 held-out）

| 数据 | 暴露程度 | 判定依据 |
|---|---|---|
| **TUM fr3_long_office_household** | **重度** | 2026-09-15 完成逐项 Gate0 资格复算：归档 SHA-256、RGB 2585 行、depth 2509 行、GT 8710 行、20ms 配对率 0.962476、深度样本 640×480/uint16 全部读取；另追加官方相机与深度证据件。已下载至 `/home/yliutz/datasets/tum_fr3_long_office/` | ❌ 冻结前元数据已暴露 |
| **RGB-D Scenes v2 scene_13** | **重度** | 2026-09-17 全天使用：基线、复放、12 臂、24 臂、256 臂、记忆对照 | ❌ |
| **RGB-D Scenes v2 scene_14** | **重度** | 同上（S108/S109 使用） | ❌ |
| **7-Scenes Chess** | 中度 | 已下载并哈希；官方 RGB/深度未标定 | ❌ 标定不合格 |
| **ICL-NUIM lr0** | 中度 | 冻结前元数据已暴露；合成数据 | ❌ 仅条件可用 |
| **TUM fr1_xyz** | 重度 | S2/S3 真实 RGB-D 实验主数据 | ❌ |
| **TUM fr2_desk** | 重度 | CUT3R/TTT3R/FILT3R 基线 ATE 测量 | ❌ |

## 2. 低暴露（仅在检索汇总中被列过名称与字节数）

| 序列 | 主账提及 | docs 提及 |
|---|---|---|
| fr3_nostructure_texture_near_withloop | 1 | 0 |
| fr3_nostructure_notexture_near_withloop | 1 | 0 |
| fr3_sitting_xyz | 1 | 0 |
| fr1_360 | 1 | 0 |
| fr3_walking_xyz | 3 | 0 |
| fr1_desk | 1 | 0 |

这些只出现在一条"候选数据集清单"事件中（名称 + 字节数），**未下载、未读取任何内容**。
属轻微暴露，若使用须声明。

## 3. ✅ 零暴露候选（推荐）

| 序列 | 主账 | docs | 说明 |
|---|---|---|---|
| **TUM fr1_room** | **0** | **0** | 单房间大闭环，含重访 |
| **TUM fr2_xyz** | **0** | **0** | 结构化运动 |
| **TUM fr3_teddy** | **0** | **0** | 物体中心 |

三者在本项目全部记录中**零次出现**，满足"冻结前无项目元数据暴露"。

---

## 4. 必须同时声明的根本限制

**零项目暴露 ≠ 模型未见过。**

TUM RGB-D 是计算机视觉最常用的公开基准之一，CUT3R、VMem 及其上游模型的训练数据构成
**未公开**，无法排除这些序列已进入预训练。外部审计 P6.1 明确指出："Project exposure is
unknown; pretraining exposure is unknown."

因此任何基于 TUM 的 held-out 主张**只能**表述为：

> "held out from **this project's** design and analysis decisions"

**不得**表述为"模型未见过的数据"或"盲测"。这一限定必须随结果一并出现。

## 5. 许可

TUM RGB-D 数据集默认 CC BY 4.0（除非另有声明）。使用须保留署名与许可信息，
并标明所做修改。

## 6. 建议的冻结流程

1. 在**任何**内容检视之前，先冻结 held-out 协议（窗口构造规则、指标、臂矩阵）并签批
2. 下载并哈希归档，只记录字节数与 SHA-256
3. 按已冻结规则机械地构造窗口，**不得**先看图像再选窗口
4. 运行，封存预测，最后才开评分
5. 报告时附第 4 节的限定

---

`new_method_validated=false`；`novelty_authorization=NONE`。
本审计不构成 held-out 资格通过，只标明哪些候选仍然可用。
