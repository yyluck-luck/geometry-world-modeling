# C1 独立复算最薄 I/O：source-only

记录UTC：2026-09-08T15:25:57.773535+00:00。当前作者`/root/execution_resumption_audit`；独立数学kernel作者`/root/c1_blind_score_builder`。本程序作者也是主评分wrapper作者，因此这里只能称独立数学实现复算与作者I/O自检；后续仍需不同作者对exact kernel、I/O source、bound binding静态审查。本作者不是本包独立审查者。

依据原`PREPARATION_REPORT.md`第6节第9项，不修改独立kernel、主scorer、原模板或binder。仅新增`recompute_c1_io.py`与一次合成I/O验证。独立kernel保持SHA`9373fd035b18ccc81dc848e18612f906a7d32a44cd1c7d2903eb67b7627e9b8f`；不导入主scorer/主wrapper，不新增数学或阈值。

身份链：caller-bound recompute binding → sealed primary receipt/report → report内exact execution binding → exact bound contract →按ID0–8排序的九个descriptor/body身份。程序只读上述JSON、固定模板与独立kernel源码，再用每个body的同一个O_RDONLY FD读取、SHA核验、不可写uint8视图；FD保留至数学结束、同FD复hash及path/fstat核验并关闭后才发布。不打开sidecar、PNG、相机数组、模型或其他frame候选。本程序不重新审查主评分之前的全部source/盲态治理，只依赖封存主receipt/report；这一步的独立结论仅限算术一致性。

比较原定全部primary、R1–R4、full-frame、1_7/2_6/3_5九个metric record。MSE数字必须与自身floathex一致并与复算floathex逐位相等；有限PSNR也以floathex比对，零分数保留null/+inf；整数分母、strict event、equality flag和row_status精确一致。没有另设容差/指标。全部一致return0，完成但不一致return1；读取、身份、review或I/O失败return2。

固定输出`/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S46_c1_blind_scoring_preparation/C1_independent_recompute/execution_01`，固定同目录`.independent_recompute.lock`的非阻塞flock。任何已有execution/staging条目阻止重跑。JSON create-only写入同目录`.execution_01.staging`并fsync，然后沿既有B0模式用macOS renamex_np(RENAME_EXCL)原子不覆盖发布。失败保留staging；数字PASS只能在外部确认为return0且固定published目录齐全时接受，不能把失败/残留staging的候选记录当终态。一次成功读9份快照8,957,952B，并在最初及结束各从同FD复hash，实际pread累计26,873,856B。失败构造Snapshot时可能已读部分字节而未计入成功handle计数，失败计数不能作为零body访问证明。

**现阶段未绑定、未读取真实主评分或body、未执行正式复算。** 主评分report/receipt实际封存后，才用原`bind_identity_only.py --kind recompute`创建一个新的直接子文件候选。输入保留既有schema/status，填actual sealed score paths/SHA、attempt1；`recompute_source_path`设本I/O source、SHA设其finalSHA；`authorized_output_path`保持上述execution_01。原binder会逐字保留数学，输出的`recompute_source_review_path`和`recompute_source_review_sha256`保持null。null只表示尚未内嵌review，绝不是已审或通配。

为避免exact binding与review的哈希自循环，bound候选不回改；不同作者审查交付一个单独review，CLI以真实path/SHA绑定。沿用原schema `s46-c1-independent-recompute-source-review-v1`、status `PASS_S46_C1_INDEPENDENT_RECOMPUTE_SOURCE_REVIEW`。程序要求字段：

- `row=C1`；`source_path/source_sha256`精确指本I/O source；`kernel_path/kernel_sha256`精确指封存独立kernel；`bound_binding_path/bound_binding_sha256`精确指实际bound候选。
- `source_author_role=/root/execution_resumption_audit`、`kernel_author_role=/root/c1_blind_score_builder`；`reviewer_role`非空且不同于这两名作者。
- `executed=false`、`images_viewed=false`、`tensor_or_image_payload_bodies_read=false`、`blocking_findings=[]`；`completed_utc`为实际UTC，晚于binding且早于执行。

没有这份实际review时，在打开任何body之前失败；本目录未附造出的审查PASS。后续已有CLI如下（本次未运行；变量须设实际已封存path/SHA）：

```sh
cd "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling"
: "${s46_recompute_input:?Set the real identity-only input path}"
: "${s46_recompute_binding:?Set a fresh direct child of the preparation directory}"
/opt/homebrew/opt/python@3.13/bin/python3.13 -I -B -S \
  work/S46_c1_blind_scoring_preparation/bind_identity_only.py \
  --kind recompute --binding "$s46_recompute_input" --out "$s46_recompute_binding"
```

得到不同作者review后，执行唯一正式复算：

```sh
: "${s46_recompute_binding_sha:?Set actual binding SHA}"
: "${s46_recompute_review:?Set actual different-author review path}"
: "${s46_recompute_review_sha:?Set actual review SHA}"
.venv-cut3r/bin/python -I -B \
  work/S46_c1_blind_scoring_preparation/C1_independent_recompute/recompute_c1_io.py \
  --binding "$s46_recompute_binding" --binding-sha256 "$s46_recompute_binding_sha" \
  --source-sha256 37b5f837b1c2b7645cc4420a9d498a57bf070668936c5c3eb84147094ba4aaeb \
  --source-review "$s46_recompute_review" --source-review-sha256 "$s46_recompute_review_sha"
```

唯一作者验证记录在`author_validation/RUN.json`：现有kernel数学自检一次 + 临时目录完整I/O衔接一次，Python3.12.14/NumPy1.26.4，return0/stderr空。测试调用实际main/run，仅替换临时路径常量；使用原binder纯渲染函数生成临时synthetic绑定与假review，全部随临时目录销毁。预期synthetic报告由同一独立kernel构建，因此该检查仅证明接口/比较/发布连接，不是再次独立数学验证，也没有覆盖攻击矩阵。保留原跨实现数学检查的证据边界。

C1独立数值一致也不能证明画质、画面相机服从、cohort、因果、方法增益或创新；C2仍强制。正式主分数及未来review所有SHA在本作者回执中保留null，不凭准备状态造PASS。
