# S82 原始四历史前向：独立设计源审

记录 UTC：2026-09-10T18:04:58.048716+00:00；北京时间为该时刻加 8 小时。审查者与准备脚本作者不同。

**结论：设计可继续到精确源码/合同前审，没有发现阻止一次有界、仅四张历史 RGB 的 512 DPT 原始 head 前向的设计问题。本文不授权当前尚未审完的新脚本运行。** 此轮只建立四历史预测几何档案，optimizer、known-pose alignment、render、warp 和新生成均为 0。`INPUT_FEASIBILITY.md` 中关于优化器的讨论属于后续路线，不应带入本轮执行。

本次阅读源码、已有 JSON/文字记录及 RGB 的文件 stat；没有读取或解码原 RGB/深度、没有打开 NPZ 科学数组或 checkpoint 正文、没有实例化/运行模型。四图 SHA 依据已存 S68 身份，不称本轮重新核图片字节。应用科学批判技能的方法是区分输入身份、实现行为与可声称结果；不为此短源审新增示意图、框架或额外模型调用。

## 1. 四张图与顺序

已逐项核 S82 清单对 S68 实际 receipt 的路径、已记 SHA 与字节大小，一致。源图当前 stat 尺寸也一致。

| 推理行 | ID | RGB 文件 | 字节 | 对应生成槽 |
|---|---:|---|---:|---:|
| 0 | 12 | 1311868168.963348.png | 513004 | 3 |
| 1 | 13 | 1311868169.363470.png | 505590 | 2 |
| 2 | 18 | 1311868171.299368.png | 538723 | 1 |
| 3 | 19 | 1311868171.663411.png | 530537 | 0 |

新前向按时间 `[12,13,18,19]`；以后生成槽仍 `[19,18,13,12]`，须取推理行 `[3,2,1,0]`。原 `scripts/s21_baseline.py:69–73` 的 original4 是旧 manifest 前四帧，本轮直接从同名路径运行会错用输入。已从旧 manifest 核文件名 1311868164.363181.png, 1311868164.399026.png, 1311868164.430940.png, 1311868164.463055.png，与本四图无交集。因此“沿用 original4 路径”应指同一模型/loader/官方前向，不是调用其旧 CLI。

只四图不代表四个独立场景。既有四历史 selection 已曝光目标信息的限制不消失；本轮只限定这次模型实际读入四张历史，不重新声称在线盲选择。公开 GT 插值得到的源/请求相机原本是共同允许输入，使用它们本身不构成新增评分泄漏。目标 RGB/深度不进入此轮，且本轮原始 head 前向无需读取任何真实相机数组。

## 2. 512/384 与原 K 的最小正确解释

已核原版 `src/dust3r/utils/image.py:65–72,136–201`：长边 resize，640×480 得 512×384；中心裁剪边界恰等于该图全幅，不是512正方形。四帧 `img` 应为 `[1,3,384,512]`，`true_shape=[[384,512]]`。原 K 来自 S68 controls：`fx=fy=525,cx=319.5,cy=239.5`。名义坐标合同 `u512=.8u640,v384=.8v480` 给 K512 `fx=fy=420,cx=255.6,cy=191.6`，已用 Fraction 独立核这三项。

原576路径是 `u576=1.2u640−96,v576=1.2v480`，故到576的名义映射为 `u576=1.5u512−96,v576=1.5v384`。不能把512×384数组拉为576正方形后仍声称坐标未变。此处沿用项目明确的 K 缩放约定，不把 PIL 采样核插值中心当作重新标定，也不无声插入另一个半像素约定。

**本轮存 K512 只能叫已知内参元数据。** RGB-only 原始模型没有接收该 K 的校准约束；保存正确 K 不意味着 learned 点图满足针孔射线、已与该相机对齐或尺度为米。S68/S69已存576 K中的 FP32值后续需保持原身份；本轮不需要打开该 NPZ。近似 ROS K、未去畸变的限制继续保留。

## 3. eval、状态、权重与兼容层

- `s21_baseline.py:78–84` 没有 `.eval()`；旧 original4 收据确为 `training_flag=true`，虽无已列非零 dropout/BatchNorm，也不能把它改述为旧 eval 实验。新脚本应显式 `.eval()` 并读回 false；`no_grad`/inference mode 控制梯度，不替代 eval。
- 旧 `prepare_input` 位于 TTT3R launch 的嵌套函数 `:300–394`，S21以 AST 提取。image-only分支造 NaN ray placeholder、`img_mask=True,ray_mask=False,update=True,reset=False` 和 identity camera placeholder。revisit=1 不复制视图；形状含 NaN 的未使用 ray placeholder 不应错误地被“全部输入必须finite”拒绝。
- 原 `inference_recurrent:266–288` 调用官方 `model.forward_recurrent`。模型 `:1027–1034` 在此次首帧创建 fresh state/mem，`:1048–1109` 每帧按 update 更新；reset=False不等于加载旧状态。四图均 image-only，不输入外部 rays/旧 recurrent state；一次列表前向应产生恰四个 downstream head，而不是将其叫四次独立模型加载。
- 权重应固定 `cut3r_512_dpt_4_64.pth`；旧已验 SHA `45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103`，大小3173761006。当前只 stat 对照旧身份，执行端采用已验身份+size/mtime时须如实记录，而不是声称重算了3.17GB哈希。加载键匹配、head类型/输入尺寸与 eval需实际读回。
- `cut3r_rope_compat.py` 是已存 signed position 兼容层，`install`只作用于 `models.pos_embed` pure PyTorch fallback，处理负索引角度，限定 F0=1，不是新机制。此轮应绑定当前 SHA，复用已有兼容策略；CPU/FP32 外层不应扩写成所有内部张量从无精度转换。没有必要重新跑原多后端 RoPE检查或旧S21模型。

## 4. 原始 self/cross/pose/rgb 的保存含义

已核 `heads/dpt_head.py:185–259`：`dpt_self`与`dpt_cross`各有独立网络，cross 经 pose-token 条件变换后解码；不是显式刚体变换 self 的程序。因此下游若用 self深度就必须单独声明重建与对齐过程，不能把 `predicted_c2w × self == cross` 当硬成立关系。

| 原始字段 | 可保留的解释 | 不能直接声称 |
|---|---|---|
| pts3d_in_self_view / conf_self | self head点图及配套学习置信值 | GT深度、已校准公制、概率覆盖保证 |
| pts3d_in_other_view / conf | cross head点图及它自己的学习置信值 | 与self完全刚体一致、已对齐TUM世界 |
| camera_pose | 3平移+wxyz四元数的 learned pose编码 | TUM的xyzw、已知真值pose或米制认证 |
| rgb | 模型RGB head输出，postprocess后约在[-1,1] | 原始输入RGB字节或新视频生成 |

`utils/camera.py:364–420`明确 quaternion实部在前，并把旋转和平移放入4×4 c2w；只能用对应官方 helper解码，不倒置成w2c。`postprocess.py:23–27`证实rgb为独立head产物。建议六字段全部原样归档，另外保存解码预测pose，不丢掉异常/负Z或按未来评分挑点。有限数值/形状检查是档案可读性检查；它不是几何质量通过门。

## 5. 下一次精确前审只核四项

1. 输入边界：四个身份、顺序、RGB hash/stat、512×384形状和槽映射；无额外历史/target RGB/depth。
2. 真实调用：固定权重/源文件/RoPE、显式eval、image-only、fresh state、update全True、revisit1，恰一次四历史recurrent前向；零optimizer/render/generation。
3. 输出语义：六head各自形状/有限数/身份保留、官方pose解码、K仅元数据、状态失败如实留存；不伪称TUM米制或warp已完成。
4. 执行边界：唯一新目录、明确时间/资源上限及实际回执；必要的无真实数据导入与形状/字段边界检查即可，不新增整套框架。精确代码/合同冻结后另外写源码结论。

## 所读当前文本 SHA

- `scripts/s21_baseline.py`：`04ad82230ae3cadd78dfc84f51f2322dadd159bc5a3deb3e8fc1e2b4ced81c92`
- `scripts/cut3r_rope_compat.py`：`6939dcead1b87e920eafce9aae47c1cc9a46b7a651ef816b3f521c779582152e`
- `work/S82_history_geometry_guidance/INPUT_FEASIBILITY.md`：`3ef439fedd2eafc2df80f968132cdf9e0c81f13dc356772d7fd4aca28c623cb9`
- `work/S82_history_geometry_guidance/SOURCE_PATHS_AND_HASHES.json`：`68c83b3b8d1f71496789506ba2f8c8b58fd8e91053626a130ac2278acecabd11`
- `work/S68_tum_vmem_cache_bridge/INPUTS.json`：`f14621d1988566f0fb09d314e02e0736e352fbe0a49c1055249c0011a34454bc`
- `work/S68_tum_vmem_cache_bridge/execution_01/receipt.json`：`ed56948f0c80e5d607bbe9061b29d4d0da5592225cadf6700b759edd1b3a92b7`
- `work/S21_baseline_preparation/run_manifest.json`：`c67f4ad5d4a4c5d74bbced9bfe60b0f06fae090446d9bf689a1b459c2b614944`
- `results/S21_baseline/original4/receipt.json`：`0993b199b78e1009b84758d941923527dffe40b86d19713835464d4eb74086fe`
- `work/S21_baseline_preparation/ttt3r_original/eval/relpose/launch.py`：`db6143b8c9a9a13ebdba52c5c1d8bdc26b511d590599111c836f249cbc907d49`
- `/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/cut3r-local/src/dust3r/inference.py`：`989349373427a234aeba0bd9460346008b8cdd236aed6c019c38e5ba0dd1f161`
- `/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/cut3r-local/src/dust3r/model.py`：`31ed5633c5a01015026fc350a370a6e4f8735f9c8179258a2b17ed70edbc5b62`
- `/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/cut3r-local/src/dust3r/utils/image.py`：`a2738085cdf0f713289a3a42dbd49a1f39325eb3ad590af65970fe4609209d96`
- `/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/cut3r-local/src/dust3r/utils/camera.py`：`f18a3ecc54492ae2878f285ad756fb1d26dbc0c4146bcf76d3f7ed2665c35d73`
- `/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/cut3r-local/src/dust3r/heads/dpt_head.py`：`7368f698a66711f5ac3ce8e6c4a51c9b0fbda12f9ebda1499cd45595ec600310`
- `/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/cut3r-local/src/dust3r/heads/postprocess.py`：`1053c35f0962f91ad8b985a702dd5c2cff4fd94ff92d96340ff7a8dbabe81384`

本次未穷尽全仓库、未检查模型真实输出，也未新增网络访问。历史 RGB/权重 SHA 不在上述“当前文本 SHA”范围内。本文件为独立设计审查，原报告与主科学记录均未改。
