# S8 V2 派生数据独立完整性审计

结论：**PASS**。本次真实审计在北京时间 2026-09-06 03:40:27.849865–03:40:32.231457 完成，共 23,803 条检查：14 项整组时间/行字节重算，17,847 条完整性检查，5,942 条记录检查。检查次数主要反映文件和记录核对数量，不是独立研究样本数。

入口 `scripts/verify_s8_derivation.py` 为新独立实现，未导入或调用生产 `derive_gt`、模型或评分代码。它只解析原 GT 每行第一个时间 token，其余位姿字段保持不解释的原始字节。原图文件仅进行字节哈希及文件身份核查，没有图像解码、位姿数值运算、新取样或推理。

## 核实结果

原树为 `data/tum/fr2_desk_download/extracted/rgbd_dataset_freiburg2_desk`；派生父目录为 `data/tum/fr2_desk_timestamp_guard`，其数据子根同名。审计先确认派生 `status=completed`、`phase=complete`，然后才读取两棵树。

- 独立从整个原 GT 重找所有有限 float 重复时间键，按固定 `abs(t-d)<=0.051` 重算排除集合。20,957 条原 GT 中排除 31 条，保留 20,926 条。排除行恰为原行 10848–10878；没有择优保留重复组中的任何一行。
- 派生 GT 的完整字节精确等于独立推导的保留原行拼接。全部排除行/覆盖重复键、保留行映射、原行 SHA、原/新行数和屏障记录均与生产保存内容逐项相同；注释/空白/行尾也保留原字节与顺序。
- 唯一重复时间为 `1311868229.576`，原行 10862/10863。最近保留左行 10847、时间 `1311868229.5227`；右行 10879、时间 `1311868229.6294`。两侧间隔 `0.10669994354248047` 秒，严格超过原 0.100 秒上限。派生时间非空、严格递增、唯一。
- 两树均有 5,933 个文件，目录/文件成员完全一致。全部 5,932 个非 GT 文件与对应原件 SHA/大小相同；所有 5,933 个派生文件均与对应原件 inode 不同。核查拒绝符号或特殊文件。
- 原树当前完整 inventory 与处理器保存的处理前/后 inventory 相同；新树当前 inventory 与保存记录相同。独立审计末尾再次遍历并哈希两树，均未发生变化。
- V2 设计冻结、协议、执行源和保存副本 SHA 一致，冻结/开始/验证/完成时点有序；处理器声明的未读像素、未解析位姿、未选窗、未运行模型等状态按记录核查。该时序证据属于元数据与源码/字节核验，不是历史文件访问轨迹的恢复。

原 GT SHA：`0d8e0119a4e9592b886c5ca954472c3270c01814dd2059fbe196d5c24c8f3d17`。

派生 GT SHA：`f19dc674dc43b6c4957038e1a22906122c19c60893e664dafb0e0abe537906ca`。

## 文件与可复核身份

| 文件 | SHA256 |
|---|---|
| `scripts/verify_s8_derivation.py` | `3260be9362c53236622b87cb29b061a81d22089abf6c628181359deb9ae30766` |
| `results/S8_derivation_audit/verifier_snapshot.py` | `3260be9362c53236622b87cb29b061a81d22089abf6c628181359deb9ae30766` |
| `results/S8_derivation_audit/verification.json` | `d92562f0e2eebdc97eb64201cbbec934894ea2236f9d42ba80c7b62d2991543d` |
| `results/S8_derivation_audit/independent_gt_derivation.json` | `c07dd1ab37a8c8ed442a2faea7766d36c7c14ef22144eb4019611df6f1130424` |
| `docs/S8_EXTERNAL_SCENE_PROTOCOL_V2.md` | `d4ae1781696f4918b65129b82f52698ab07b1642fdf744f74501187a96984431` |
| `docs/S8_DESIGN_FREEZE_V2.json` | `ffb38a8bcb31cebf3fb9106b730acd7ce6ccc9c630a3cddd6fae56f63a872302` |
| `scripts/prepare_tum_timestamp_derivative.py` | `05eb236982b6eaca47156fc09066e996e9d894dd702be52310f3af4e36609583` |

两树的独立完整 inventory 另存于审计目录的 `source_inventory.json` / `derived_inventory.json`。审计源在真实运行前完成编译、帮助入口、人工 opaque-GT/全重复并集/行字节/屏障，以及未完成拒读入口检查，记录于 `work/s8_timestamp_amendment_review/independent_derivation_preflight.json`。本次真实审计一次通过，没有重试或放宽条件。

实际运行参数：

```text
.venv/bin/python scripts/verify_s8_derivation.py \
  --source data/tum/fr2_desk_download/extracted/rgbd_dataset_freiburg2_desk \
  --derivation data/tum/fr2_desk_timestamp_guard \
  --protocol docs/S8_EXTERNAL_SCENE_PROTOCOL_V2.md \
  --freeze docs/S8_DESIGN_FREEZE_V2.json \
  --output results/S8_derivation_audit
```

既有输出不能覆盖；复查须另设新目录。后续最终执行冻结应绑定这份审计源、实际审计结果和派生 metadata。

## 未做及解释限制

没有重新验证 TGZ 的 gzip/tar 内容；本次核的是完整解压原树与派生树。没有判断位姿数值是否正确，也没有证实重复记录代表物理位姿冲突。排除邻域是透明保守的时间键处理，不是官方真值修复。尚未由本审计选择新的 72 帧、验证足够窗口、解码新图或计算模型/几何结果。V1 失败仍保留；本结论仅允许继续 V2 的实际取样及后续审查。
