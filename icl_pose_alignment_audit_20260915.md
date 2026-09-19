# ICL-NUIM `livingRoom0.gt.freiburg` 轨迹对齐审计（2026-09-15）

## 审计边界

本次只读 ICL 官方公开的 `livingRoom0.gt.freiburg` 轨迹文本，并检查本地是否已经存在 `associations.txt`。没有下载 ICL 图像/压缩包，没有打开任何未来 RGB/depth 图像，没有将 GT 用于候选选择、阈值选择或方法训练，也没有运行 VMem/GRC。该审计只回答“官方 pose 文件实际有多少行、首列是什么、在数据包尚未取得时能否确认 association 对齐”。

## 官方来源与可复现命令

- 数据页：[ICL-NUIM RGB-D Benchmark](https://www.doc.ic.ac.uk/~ahanda/VaFRIC/iclnuim.html)，页面给 `lr kt0` 1510 images、30 Hz，并链接 `TrajectoryGT`。
- 轨迹文件（官方 `TrajectoryGT` 锚点）：<https://www.doc.ic.ac.uk/~ahanda/VaFRIC/livingRoom0.gt.freiburg>
- 官方代码说明：[ICL-NUIM Codes/Scripts](https://www.doc.ic.ac.uk/~ahanda/VaFRIC/codes.html)，说明 ICL 原生 pose 是包含 3×4 ground-truth pose 的 txt；同时给出相机标定和 POVRay world pose 语义。

在 macOS/zsh 中执行的命令（网络读取到 stdout/临时审计文件，未保存数据包）：

```bash
curl -fsSL https://www.doc.ic.ac.uk/~ahanda/VaFRIC/livingRoom0.gt.freiburg \
  | tee /tmp/livingRoom0.gt.freiburg.audit >/dev/null
shasum -a 256 /tmp/livingRoom0.gt.freiburg.audit
awk 'NF && $1 !~ /^#/ {rows++; if(rows==1) first=$1; last=$1; if(NF!=8) bad_nf++} END{print "rows="rows,"first_col_min="first,"first_col_max="last,"bad_field_count="bad_nf+0}' \
  /tmp/livingRoom0.gt.freiburg.audit
awk 'NF && $1 !~ /^#/ {idx=$1+0; if(idx != int(idx)) nonint++; if(prev!="" && idx != prev+1) gaps++; prev=idx; if(NF==8) rows8++} END{print "rows_8_fields="rows8,"noninteger_first_col="nonint+0,"nonconsecutive_gaps="gaps+0}' \
  /tmp/livingRoom0.gt.freiburg.audit
find /Users/rocket/Desktop/HKUST\\ IT/ip- /Users/rocket/Documents/Codex \
  -type f -name 'associations.txt' -print 2>/dev/null | head -50
```

## 实际输出摘要

官方文件响应头为 HTTP 200，`Content-Length=108786`，ETag=`"1a8f2-4e66f342d8780"`，`Last-Modified=Sun, 15 Sep 2013 17:13:18 GMT`。下载到临时审计文件的 SHA-256 为：

`658bfae1e3118c9f97ad7c99721649e3de65b16e209c1f5271dbc2a84cb67d61`

文件逐行检查结果：

```text
rows=1508 first_col_min=1 first_col_max=1508 bad_field_count=0
rows_8_fields=1508 noninteger_first_col=0 nonconsecutive_gaps=0
```

也就是说，官方 `livingRoom0.gt.freiburg` 共有 **1508 行**；每行正好 8 个字段；首列是连续整数 **1 到 1508**，不是带小数点的时间戳。官方数据页另报 `lr kt0` 有 1510 images，因此在未取得包内配对清单前，不能把这 1508 行直接当成 1510 帧的一一对应 pose。

本地 `find` 没有发现任何 `associations.txt`。因此本轮 **无法给出 associations 行数**，也不能声称 association 与 pose 已对齐。官方 ICL 页面只明确给出帧率、图像数量和 `TrajectoryGT` 链接；官方 Codes/Scripts 页说明 pose txt 与 POVRay world frame，但没有提供 `associations.txt` 的公开独立文件或“首列即 Unix timestamp”的声明。

## 对“时间戳/帧索引”的严格判断

1. `livingRoom0.gt.freiburg` 实际首列是连续整数 1…1508，可作为该文件内部的帧/pose 序号候选；这不是官方明文命名的 timestamp 字段。
2. 官方数据页给出 30 Hz 和总时长，但没有把 `livingRoom0.gt.freiburg` 首列定义为 Unix 时间戳，也没有证明 association 文本采用同一索引。
3. 官方 Codes/Scripts 页说原生 pose 文件包含 3×4 ground-truth pose；当前 `livingRoom0.gt.freiburg` 每行 8 字段的 TUM-compatible 形式与链接内容一致，但页面没有说明这 8 字段的第一列时间语义。
4. 因而只能写成：`pose_rows=1508`、`pose_index_range=1..1508`、`timestamp_semantics=UNSPECIFIED_BY_OFFICIAL_TEXT`、`associations_rows=NOT_AVAILABLE_BEFORE_ARCHIVE_ACQUISITION`。

## 是否解除 Gate0

**不能解除。状态保持 `BLOCKED_UNTIL_RECEIPT_AND_STRUCTURE_CHECK`。** 原因不是 pose 文件坏，而是关键的 RGB/depth association 未取得、未计数、未验证与 1508 pose 行的映射。ICL 官方页面声明 1510 images 与当前 1508 pose 行存在数量差异，必须在方法冻结后取得官方包，读取包内 `rgb.txt`/`depth.txt`/`associations` 结构并先生成哈希 manifest；若有缺少 GT 的头帧，应显式列出剔除规则，不能静默截断。

Gate0 下一步（仍不运行 GRC）：

1. 取得已冻结的官方 `living_room_traj0_frei_png.tar.gz`，记录 URL、HTTP 响应、字节数与完整包 SHA；
2. 只解包目录文本和文件名，统计 `rgb.txt`、`depth.txt`、`associations.txt` 行数及首/末索引；
3. 将 association 的 RGB、depth 文件名与 pose 首列建立显式映射，输出缺帧/重复帧/无法解释的索引清单并哈希；
4. 完成配对与时间合同后，才可生成 held-out split；在 prediction seal 前禁止打开未来 GT。

本审计没有产生任何新实验结果，也没有改变 `work/S102_gate0/GATE0_RESULT.json` 的 blocked 状态。

