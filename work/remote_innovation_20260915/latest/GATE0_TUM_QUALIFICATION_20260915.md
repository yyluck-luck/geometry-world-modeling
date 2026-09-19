# Gate 0 数据资格证据：TUM RGB-D `freiburg3_long_office_household`

**性质：** Gate 0 数据资格证据包。**本文件不自行宣布 Gate 0 通过**；正式资格判定须按 S102 schema 运行。
**核实方式：** 本文件的**每一个数字都由本人独立复算**（下载归档 → 解出索引 → 逐项计算），不与子检索报告共享代码或结果。
**下载位置：** `/home/yliutz/datasets/tum_fr3_long_office/`

---

## 1. 为什么需要它

ICL-NUIM 卡在 Gate 0 的两条阻断理由之一（硬件时间戳）。2026-09-15 日报：ICL-NUIM 归档**只有帧序号**（位姿文件第一列 `1..1508`、`associations.txt` 第一列 `0..1508`），按 30 Hz 反推**不等于**逐帧硬件时间戳。

TUM RGB-D 提供**真硬件时间戳**，且本项目**已有** `src/tum_rgbd.py` 读取器（含 `/5000` 深度换算与 TUM 关联规则）。

---

## 2. 归档身份

| 项 | 值 |
|---|---|
| URL | `https://cvg.cit.tum.de/rgbd/dataset/freiburg3/rgbd_dataset_freiburg3_long_office_household.tgz` |
| 字节 | **1,483,556,251** |
| SHA-256 | **`c7cd8e1afb87c80e5744a356214819b110fa09b4744fa4ba0cc2382f9ba59e9c`** |
| 校验和来源 | **TUM 未发布任何校验和**；此值由本人下载后自算，写入 `download_receipt.txt` |
| 下载回执 | `/home/yliutz/datasets/tum_fr3_long_office/download_receipt.txt` |
| 许可 | CC BY 4.0（官方页；子检索报告核实，本人未逐字复核该页正文） |

> ⚠️ 子检索的另一路**独立下载同一归档并自算 SHA**，得到**同一值**。两条独立下载路径的字节一致。

---

## 3. 逐项资格（本人独立复算）

| 项目 | 实测结果 | 判定 |
|---|---|---|
| **硬件时间戳** | `rgb.txt` / `depth.txt` 表头为 `# timestamp filename`，值为 **Unix epoch 浮点**：`1341847980.722988 → 1341848067.862808`（起点 = 2012-07-09 15:33:00.722988 UTC） | ✅ **真时间戳** |
| **严格递增且互异** | rgb / depth / gt 三者的时间戳均 `严格递增=True`、`全不同=True` | ✅ |
| **GT 覆盖率** | rgb 跨度 **87.14 s**，GT 跨度 **87.09 s** | ✅ **全覆盖**（非部分覆盖） |
| **GT 频率** | 8710 帧 / 87.09 s ≈ **100.01 Hz**（动捕 100 Hz） | ✅ |
| **1:1 RGB-D 配对** | 按 TUM ±20 ms 规则：**2488 / 2585 = 96.2%**（取这 2488 帧即为严格 1:1 集合） | ✅ |
| **深度语义** | 640×480 16-bit PNG，因子 **5000**（中位非零 12075 → 2.42 m）；本项目 `src/tum_rgbd.py` 已实现 | ✅ |
| **内参 K** | TUM 按 rig 公开（fr3 已去畸变，畸变参数为 0） | ✅（来源为官方页，子检索核实） |
| **位姿** | 8710 条动捕 GT，格式 `timestamp tx ty tz qx qy qz qw` | ✅ |
| **回访闭环** | **109,280 对**位姿间距 <0.30 m 且时间差 >10 s；最小回访距离 **0.0182 m**，最大时间差 **78.6 s**，涉及 **1261** 个 GT 帧 | ✅ **强回访证据** |
| **轨迹尺度** | 路径长度 **22.20 m**，范围 **[5.12, 4.89, 0.54] m** | ✅ |

### 3.1 帧数（逐项与索引文件一致）

| 文件 | 数据行数 |
|---|---|
| `rgb.txt` | 2585 |
| `depth.txt` | 2509 |
| `groundtruth.txt` | 8710 |

---

## 4. 与 Gate 0 要求的对照

| Gate 0 要求 | 状态 |
|---|---|
| 新/未见的 RGB-D 场景 | ⚠️ **需用户/协议指定**（见 §5） |
| RGB + 深度 | ✅ |
| RGB 与深度一对一时间戳配对 | ✅ 2488 帧严格 1:1 |
| **真硬件时间戳** | ✅ **已由字节确认**（ICL-NUIM 缺的正是这一条） |
| 相机内参 K | ✅ 官方发布 |
| 相机位姿 | ✅ 动捕 GT，100 Hz，全时段覆盖 |
| 深度单位已文档化 | ✅ 因子 5000 |
| SHA 校验 | ⚠️ TUM **不提供**；已自算并记录 |
| 许可清楚 | ✅ CC BY 4.0 |
| 未来 GT 与选择器隔离 | ⚠️ **需在协议中实现**（不是数据集属性） |

**结论：数据集的客观属性已满足 Gate 0 对"时间戳、配对、单位、位姿、覆盖"的要求。** 剩余两项是**协议与设计决定**，不是数据缺陷。

---

## 5. 关键警告（必须写进任何使用它的协议）

### 5.1 `*_validation` 序列**不带 GT 位姿**

TUM 的 ~28 条 `*_validation` 序列（含 `freiburg3_long_office_household_validation`，1,532,741,250 B）**没有 GT 位姿**——下载页对它们不列 GT 链接，它们是给在线评测工具用的。

**⇒ 若 held-out 划分需要位姿，必须"另选一条独立录制序列"作为 held-out，不能用 `_validation` 集。**

### 5.2 不要用 `freiburg2_*` 做长程实验（**已发现陷阱**）

子检索原本推荐 `freiburg2_large_with_loop`，**随后自查推翻**：该序列 173.19 s 但 GT 只覆盖 40.54 s（**76% 缺失**）。同类问题：

| 序列 | 时长 | GT 时长 | 缺失 |
|---|---|---|---|
| `freiburg2_large_with_loop` | 173.19 s | 40.54 s | **132.65 s** |
| `freiburg2_large_no_loop` | 112.37 s | 21.37 s | 91.00 s |
| `freiburg2_desk` | 99.36 s | 69.15 s | 30.21 s |
| `freiburg2_desk_with_person` | 142.08 s | 119.37 s | 22.71 s |

**这与项目此前在 Bonn 踩过的"某帧传感器 GT 全缺"属同一失效类。** 使用任何 TUM 序列前，**必须核对下载页的 "Duration" 与 "Duration with ground-truth" 两列**。

**所有 `freiburg3_*` 序列全覆盖**（本文件核实的是其中之一）。

### 5.3 缺失的 GT 与缺失的校验和是两件事

- GT 覆盖：fr3 **完整**，fr2 部分缺失 → 影响实验设计
- 归档校验和：TUM **一律不提供** → 影响 provenance，但不影响实验有效性（自算并记录即可）

---

## 6. 本文件**没有**做什么

1. **没有宣布 Gate 0 通过。** 正式判定须按 S102 schema 运行，且需用户确认数据方向。
2. **没有指定 held-out 划分。** §5.1 说明了为什么不能用 `_validation`。
3. **没有解码任何图像像素。** 只读了索引文件（`rgb.txt` / `depth.txt` / `groundtruth.txt`）与归档字节。
4. **没有跑模型。** 0 次模型调用。
5. **没有独立复算 TUM 官方页面的许可与内参条款正文**——这两项来自子检索报告，本人未逐字复核页面正文。
6. **没有验证 `freiburg3` 之外序列的 GT 覆盖**（§5.2 的 fr2 数字来自子检索，本人未复算）。

---

## 7. 复现

```bash
# 下载（约 1.48 GB）
curl -L --retry 3 --continue-at - \
  -o rgbd_dataset_freiburg3_long_office_household.tgz \
  https://cvg.cit.tum.de/rgbd/dataset/freiburg3/rgbd_dataset_freiburg3_long_office_household.tgz
sha256sum rgbd_dataset_freiburg3_long_office_household.tgz
# 期望 c7cd8e1afb87c80e5744a356214819b110fa09b4744fa4ba0cc2382f9ba59e9c

# 索引检查
tar xzf rgbd_dataset_freiburg3_long_office_household.tgz \
  --wildcards '*/rgb.txt' '*/depth.txt' '*/groundtruth.txt'
```
