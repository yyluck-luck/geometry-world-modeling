# S17B不同作者前审与独立验证入口

本文件记录代码/人工层面的前审，**不代表512 DPT真实前向已经完成**。最终身份由 `work/S17B_review/review_receipt.json` 和root执行清单绑定；只有下载完整、LFS SHA核对、root封存且真实run SUCCESS后，才能执行保存数组的独立核验。

## 前审范围与结论

独立阅读新 `scripts/run_s17b_dpt_history.py`、既有32GiB/600秒外caller、官方pinned DPT head、预处理、相机解码、模型加载器、patch embedding和训练config。没有import官方模型、读取任何checkpoint payload/真实RGB/GT或运行前向。旧224 runner、99份上游Python、signed RoPE adapter保持不改。

核心实现满足固定两图512 DPT组件范围。两处非数学问题已向作者提出并要求在最终身份前改正：有效ray帧数从实际view flags求和，不能只依赖预填0；协议中224参考峰值不应误称既有两帧运行。修正完成、最终人工回执绑定后，本前审结论为**可进入root下载完成后的封存执行**，不是模型运行PASS。

## 已由原代码核实的关键布局

| 项目 | 独立核实的依据与判定 |
|---|---|
| 原图/预处理 | 官方 `src/dust3r/utils/image.py` 的 `load_images(size=512)`长边缩放640×480→宽512高384；非224路径，非方图不触发方图4:3改裁。输入 `[1,3,384,512]`，true_shape `[[384,512]]`。 |
| 真实DPT输出 | `src/dust3r/heads/dpt_head.py`的DPTPts3dPose经postprocess返回点图/RGB `[1,384,512,3]`、conf/conf_self `[1,384,512]`、pose `[1,7]`，每帧六tensor，不沿用224空间尺寸。 |
| 训练配置与运行类区别 | `config/dpt_512_vary_4_64.yaml`写ManyAR_PatchEmbed；官方model.py/load_model主动替换为PatchEmbedDust3R并强制landscape_only=False。运行时核后者、head_type=dpt、patch图片配置512²、DPTPts3dPose，不能误拒绝官方转换。 |
| 编码器实际观测 | 384×512与16像素patch对应768 tokens；两图image patch输入 `[2,3,384,512]`，首尾24层encoder边界 `[2,768,1024]`。记录真实hook结构，不能用预定数冒称实际经过backbone。 |
| 无射线查询不等于无ray hook | 官方 `_encode_views` 在所有ray_mask为false时仍构造 `[1,6,384,512]`全零dummy，执行一次ray encoder后贡献乘0。该次为内部dummy，0 supplied rays、0 query；不冒称真实射线观测。 |
| 状态布局 | 512训练配置仍state_size768、dec维768；官方local_mem默认256，值宽为2×768。五state形状与旧224相同有源码依据，不能仅凭文件名“4_64”猜state是64。 |
| 位姿独立路径 | 官方编码为xyz平移+wxyz四元数，用Torch二次多项式转旋转。独立验证器重排到SciPy xyzw并自行规范化，比较2个4×4矩阵；平移和底行另作exact检查。 |

这些判断来自当前checkout的原代码文本，未把下载摘要当完成模型构建。源码路径、SHA和实际记录时刻保存在前审回执，配置YAML仅用于此只读论证，不冒称模型运行会额外读取它。

## I/O和执行边界核对

`validate_contract`固定两张S15A原Bonn index0/1 SHA、顺序、640×480原图属性、512 DPT权重完整3,173,761,006字节及SHA、99上游文件和明确control白名单。完整大小与SHA在任何Torch/权重加载前检查；原Python默认weights-only路径使用受限safe_globals并禁止不安全加载环境覆盖。若checkpoint globals或key不兼容，应保留FAILED，不通过取消安全检查或换224权重凑成功。

`make_views`固定CPU FP32、两帧输入尺寸、true_shape、顺序和img/ray/update/reset标志。单位camera与masked NaN ray是占位输入，不是GT位姿。PIL打开路径逐次受固定两图白名单约束，没有后续帧、轨迹、GT或视频输入。

输出先保存实际返回的tensor和五state，再核有限值、形状、dtype等门；无论成功或失败均用fresh目录保留。正式执行使用现有外caller的真实pid/RSS/退出码记录，0.5秒采样加600秒超时，不把worker末尾资源检查称为外部监控；这也不是操作系统硬隔离。独立核验会读取caller回执证明正式执行经过该壳。

## 独立验证器

脚本：`scripts/verify_s17b_dpt_history.py`，只import NumPy/SciPy和标准库，不import新runner、官方model、Torch、PIL或图像解码器。命令接口为：

```text
.venv/bin/python scripts/verify_s17b_dpt_history.py \
  --manifest ABS_S17B_MANIFEST --manifest-sha256 HASH \
  --seal ABS_ROOT_OUTPUT_SEAL --seal-sha256 HASH \
  --run-dir ABS_SUCCESSFUL_RUN --caller-receipt ABS_CALLER_RECEIPT \
  --output ABS_FRESH_VERIFICATION_DIRECTORY
```

root输出seal需含`identities`，覆盖全部run文件、manifest与caller；独立验证器先核外部给定seal SHA、所有文件SHA、SUCCESS和caller实际完成，再解码NPZ。它会流式读已完成checkpoint和两张图的字节以核身份，**不反序列化权重、不解码图片**；不能把“不解码”写成“没有读过字节”。

核验内容：12个DPT预测tensor、5个final state、2个pose数组共19；NPZ精确成员、解压大小上界、shape/dtype/finite及各数组连续字节SHA；两pose经SciPy独立计算；state_pos按`floor(sqrt(768))=27`的2d位置规则独立构造；两张图实际打开记录、所有processed shapes/flags；DPT实际架构与四条encoder观测；单次两图history、一次零dummy、无query；全部源/输出身份和前后记录；600秒/32GiB外监控。

不评估深度准确率，不对传感器尺度作拟合，不把有限值、正规旋转或组件成功当成泛化、创新或完整视频结果。若当前未产生SUCCESS及root seal，这个脚本处于准备状态，不能生成预写PASS回执。

## 人工证据与后续复核

独立 `work/S17B_review/check_independent_schema_v2.py` 使用本地人工数组，验证384×512布局及拒绝宽高转置/224、已知非单位四元数的90°Z旋转及拒绝零四元数/NaN、NPZ成员与SHA，以及actual runtime schema拒绝linear head和非零dummy。`artificial_verifier_v2/receipt.json`为实际回执；这些人工数据不是真实512输出。

新runner作者的人工边界检查单独保存在 `work/S17B_preparation/`，是作者自检；本文件是不同作者对代码与官方实现的审查。后续SciPy验证才是实际保存输出的不同数学路径核验，仍是团队内核验，不能写成外部团队复现。最终root封存身份后再运行；本报告不修改研究主账或记忆。
