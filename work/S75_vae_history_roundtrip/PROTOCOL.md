# S75：五张既有历史照片的 VAE 回环组件对照（执行前）

本轮只回答：将S68已经保存的真实照片latent送回同一个ft-mse VAE解码器，是否产生类似已观察到的大取景偏移？固定来源为12、13、14、18、19，全部属于已见历史，顺序固定。主程序作者为 `/root/next_control_feasibility`，必须由root对最终源码/合同另作独立审查后决定实际启动。本文件不代表已经运行。

## 原始证据与新增工作

S68已实际完成这五张照片的VAE mean编码并通过不同作者核验；重编码不增加所需信息。因此复用 `history_ID.npz` 的 `latent`，读取整个NPZ以核SHA、只解码latent成员，不解码embedding或K成员。原latent是 `[4,72,72]` FP32、posterior mean×0.18215，原wrapper的decode自然除以0.18215一次。

S70确实曾解码全部8槽，但最终只保存4个目标RGB和全部latent；没有可供直接比较的历史重建RGB。新增工作只包括一次334,643,276B本地ft-mse VAE权重载入和五次decode，不重跑S68 encoder、CLIP、VMem或50步生成，也不加载其他权重。组件标识为 `stabilityai/sd-vae-ft-mse` revision `31f26fdeee1355a5c34592e401dd41e45d25a493`，原SD2.1 VAE身份仍UNKNOWN。

## 冻结输入与原实现

`CONTRACT.json`绑定S68 root接受回执、执行回执、五份逐来源JSON、五NPZ与五真实PNG的路径/SHA；另绑定原utils四helper、原AutoEncoder及Diffusers loader源码与软件版本。协议准备时只读取源码、JSON和包版本元数据，未读取PNG/NPZ/NPY/权重正文。

运行时逐来源核其JSON与已接受S68回执行全等，再校验实际NPZ/latent shape、dtype、finite和body SHA。参考照片以原 `load_img_and_K` + `transform_img_and_K` 得到CPU FP32 `[1,3,576,576]`，采用既有近似ROS K、原area覆盖缩放与中心裁剪；五份参考tensor SHA必须和S68记录完全相同。无需新目标图、目标深度、相机拟合、去畸变或任何新检索。

通过原AutoEncoder类路由已绑定本地配置与safetensors字节，设置local_files_only、离线环境并拒绝socket连接。保持CPU8线程、FP32、eval/inference、冻结参数、chunk1，无tiling/slicing。类的encode和底层module.encode在五图阶段显式替换为拒绝函数；所有decode起止写时间和输入latent SHA。原类forward虽存在但不会调用。

## 全量评分与展示

每张保存精确预处理 `reference_fp32.npy` 与未裁范围的 `reconstruction_raw_fp32.npy`，均为 `[3,576,576]` FP32。

- 原始MSE/MAE：两者先转FP64再相减，在声明的[-1,1]尺度上用全部3×576×576元素计算；不clamp、不配准、不拟合、无mask。保存解码raw最小/最大、超出[-1,1]的计数。该MSE与[0,1]尺度数值相差4倍，不可混用。
- PNG采用固定 `floor((clip(value,-1,1)+1)*127.5+0.5)` → uint8；参考/重建完全同规则。它仅是展示及特征匹配输入，不回写raw评分。没有按frame.min选单位的分支。
- 在两幅PNG像素上用cv2 RGB2GRAY、同SIFT参数（nfeatures1500等）、BF L2双向k2、严格ratio<0.75和互惠ID；保留全部接受匹配，按源ID排序。不用RANSAC、单应性、F拟合或配准过滤。
- 位移是每对接受匹配的二维坐标欧氏距离。保存所有ID、两组坐标、位移、q25/50/75/95、最大值；保存源图及重建特征数、匹配/缺失数量与源图分母比例、两幅匹配覆盖范围及4×4格占用数。
- 固定2/5/10px为描述性展示，不是正确性阈值。小位移分数同时报告相对于原源图特征总数和已接受匹配数的分母。空源图或空匹配保留null，不补0误差，不去掉该照片。错误匹配仍可能出现，因此SIFT不是对应点真值。

## 运行预算、失败和验收

拟定worker内部170秒、root外部180秒；30GiB内存上限，至少2GiB磁盘。worker仅在加载/帧边界检查时间与macOS self peak RSS，**需要root外部supervisor执行180秒墙钟及进程树RSS硬停止**。旧S68外部18.644秒包含CLIP加载/五次编码，是不同工作；不能当本轮decode实测时间或完成保证。

命令保留venv词法路径，不能resolve成基础Python：

```
.venv-cut3r/bin/python -B work/S75_vae_history_roundtrip/decode_history.py <CONTRACT_SHA256>
```

只能创建新 `execution_01`。启动、加载、每图decode时间写 `started.json` / `progress.jsonl`，每个完成图立即保存其receipt，完整终态receipt保留全部完成和未完成行。异常返回失败，原输出不删、不自动重试。正常完成必须全部五图且五次decode；源码编译或作者自查不等于真实运行。

root接收后先独立源审，再单次运行、保存退出码/时间/资源。结果评分由不同作者对保存的FP32图与坐标单独复算，必要视觉QA查看所有五图，才能发表这项有限组件诊断结果。

## 解释边界

回环良好仅削弱该ft-mse VAE在这五个真实编码latent上制造大偏移的解释。模型生成latent可能不在同一分布，且同VAE自洽编码/解码不证明与VMem训练期latent坐标兼容，**更不证明原SD2.1组件相同**。回环不好需先检查单位、scale、crop、loader绑定等链路，不能直接归因权重。全部为一个已见场景，不作显著性、跨场景、创新成立或PhD层级声明；一次诊断完成后用于决定下一项更具区分力的模型对照。
