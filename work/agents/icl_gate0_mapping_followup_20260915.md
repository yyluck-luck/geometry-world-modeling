# ICL-NUIM kt0 归档内配对映射审计（2026-09-15）

## 边界与输入

本轮只读取学校服务器上已下载的官方归档中的**文本成员和文件名列表**；没有解码 PNG、没有读取图像/深度像素、没有用未来 GT 数值做候选选择或阈值选择，也没有运行 VMem/GRC。归档下载回执为 `work/S102_gate0/remote_receipts/icl_nuim_download_receipt.txt`：官方 URL、大小 711,444,709 bytes，归档 SHA-256 `4eca8c2e9f77c1bd7436c746d22ea6144b8c01fe9bc29a84e734186823f1f1ad`。

服务器路径（只读）：`/home/yliutz/datasets/icl_nuim/living_room_traj0_frei_png.tar.gz`。

## 可复现命令

以下命令通过显式 SSH key 在服务器执行；`tar -tzf` 只列成员名，`tar -xOzf` 只流出两个文本成员到 awk/shasum，不落地 PNG：

```bash
ssh -i ~/.ssh/id_ed25519_superpod -o IdentitiesOnly=yes yliutz@superpod.ust.hk \
  'A=/home/yliutz/datasets/icl_nuim/living_room_traj0_frei_png.tar.gz
   tar -tzf "$A" | awk -F/ '\''$1=="rgb" && $2 ~ /^[0-9]+\.png$/ {x=$2; sub(/\.png$/, "", x); n++; a[x]++} END{print "rgb_count="n,"..."}'\''
   tar -tzf "$A" | awk -F/ '\''$1=="depth" && $2 ~ /^[0-9]+\.png$/ {x=$2; sub(/\.png$/, "", x); n++; a[x]++} END{print "depth_count="n,"..."}'\''
   tar -xOzf "$A" associations.txt | awk '\''NF && $1 !~ /^#/ {n++; if(n<=2) print "first",$0; last=$0} END{print "rows="n; print "last",last}'\''
   tar -xOzf "$A" livingRoom0.gt.freiburg | awk '\''NF && $1 !~ /^#/ {n++; if(n<=2) print "first",$0; last=$0} END{print "rows="n; print "last",last}'\'''
```

完整映射检查使用临时目录仅保存文本成员，并在 SSH 命令结束时删除；检查每个 ID 的唯一性、范围、交集，以及 association ID 0 与 1…1508 的行数。

## 实测结果

归档目录中有且只有两个相关文本成员：`associations.txt`、`livingRoom0.gt.freiburg`。文件名统计（数字排序逻辑，未读取 PNG 内容）：

```text
rgb_image_entries=1509 min=0 max=1508 duplicate_names=0
depth_image_entries=1509 min=0 max=1508 duplicate_names=0
```

`associations.txt`：

```text
assoc_rows=1509 assoc_unique=1509 assoc_zero_rows=1 assoc_duplicate_ids=0 assoc_bad_fields=0
assoc_id_range=0..1508
assoc_head=0 depth/0.png 0 rgb/0.png
assoc_tail=1508 depth/1508.png 1508 rgb/1508.png
assoc_1_to_1508_rows=1508 assoc_frame0_rows=1 assoc_outofrange_rows=0
associations_sha256=622cd848e5b3d19175b15aabfdd2dd13793e8ecad0055a402dddd93ed0da655d
```

`livingRoom0.gt.freiburg`：

```text
pose_rows=1508 pose_unique=1508 pose_duplicate_ids=0 pose_bad_fields=0
pose_id_range=1..1508
gt_head=1 0 0 -2.25 0 0 0 1
gt_tail=1508 0.0631292 -0.979845 -0.551017 0.0559326 0.731584 0.309945 0.60464
pose_sha256=658bfae1e3118c9f97ad7c99721649e3de65b16e209c1f5271dbc2a84cb67d61
```

跨文件 ID 比较：

```text
assoc_to_pose_intersection=1508 assoc_ids_without_pose=1 pose_ids_without_assoc=0
```

因此，归档内存在一个可审计的、非猜测的剔除规则：

> 保留 association ID 1…1508；丢弃唯一的 association ID 0（`depth/0.png` 与 `rgb/0.png`）。保留后的 1508 条 association 与 pose 文件首列 1…1508 一一对应，且无重复、无缺失、无越界。

这不是把 pose 首列解释成 Unix 时间戳。官方页面只给 kt0 30 Hz/1510 images，官方代码页只说明 pose 文件和坐标语义；因此时间合同仍应写为“固定采样率下的连续帧索引”，而不是绝对时间戳。归档本身的文件名和 association 行提供了可复现的帧索引。

## Gate0 判断

**配对子门可以记为 PASS（`association_pose_index_alignment=PASS`），整体 Gate0 仍不能解除。**

已解决：

- RGB 与 depth 各有 1509 个唯一文件，ID 0…1508；
- association 有 1509 行，ID 0…1508；
- pose 有 1508 行，ID 1…1508；
- 丢弃 association ID 0 后，1508 条 association 与 1508 条 pose 精确一一对应；
- 所有文本成员的首末行、行数和 SHA 已记录。

仍未解决：

1. 该规则是数据归档内的索引对齐规则，不能据此声称官方首列是 Unix timestamp；
2. 还需完成 RGB/depth 图像尺寸、PNG 位深、深度单位、内参和 pose 坐标约定的结构检查（只读元数据即可）；
3. 还需生成方法冻结后的 held-out split、GT 隔离和 prediction seal；
4. ICL-NUIM 是 synthetic 场景，不能单独支撑 proposal 的真实动态遮挡泛化结论。

所以 `work/S102_gate0/GATE0_RESULT.json` 的整体 blocked 状态保持不变，任何正式 GRC 运行仍然禁止。

