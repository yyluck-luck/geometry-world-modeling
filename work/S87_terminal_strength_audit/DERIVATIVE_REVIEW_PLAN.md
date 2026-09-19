# S87 独立保存量复核计划

状态：源码/数值规则已准备，等待 root 最终回执绑定后唯一运行。执行器 SHA `fea09f959f9ecfe86407fabc57408f95eb7a6fa7652322f06f172c24e8eca5d6`，合同 SHA `337982b200182b50ade46aee4625c5c7ff3d87f5acce01bd48343451015c2538`，生成源审已 GO。本文不代表已运行检查，不读真实数组或参考图。复核作者与生成实现作者不同；只写 S87 自有复核文件，不修改 S86 或主账。初版本计划 SHA `27a7f6d6a55fbba256520afdd8de2c2c8e2104ae7023e2feda38bf22d5f45e8a`；本次只明确最终接口与已人工核出的跨库语义，数值容差仍为零。

## 输入绑定与运行条件

将交付 `check_saved_derivatives.py`，仅在 root 明确绑定最终生成合同、执行器、生成 RECEIPT、监督回执（若有）、本核器及本计划的精确 SHA 后运行一次。使用未解析符号链接的 `R/.venv-cut3r/bin/python`，NumPy 1.26.4，不导入作者执行器、Torch、VAE 或 denoiser。核验回执新建写入，失败保留，不覆盖、不自动重试。

输入是封存的 S86 G0 七字段 LAST_STEP、ENCODED_WARP、G0 raw RGB/all8 latent、原 RGB warp 和 bool image_mask，以及最终合同列出的元数据/源码/权重身份和 S87 六组产物。按合同核路径、文件 SHA、大小、dtype、shape、连续 body SHA。权重若需核当前文件身份只流式 SHA，不加载或执行。参考 RGB、S70 transformed target 和科学评分文件不属于本核器的输入。旧 S85 大型投影档案不重复读取。

固定六组顺序：`Gpaste_l050, Gterminal_l050, Gpaste_l075, Gterminal_l075, Gpaste_l100, Gterminal_l100`；强度依次 .5/.75/1，各组完整四目标 `[20,21,22,23]`，历史槽 `[19,18,13,12]`，前四历史后四目标。本核器接受完整六组封存的派生结果；发生部分失败时保留原运行失败信息，不把剩余组当作完整六组 PASS。

## 执行前声明的数值比较规则

1. **确定性 FP32 算术按字节精确比较。** NumPy 每个操作保持 FP32，逐语句与已审实现相同顺序执行，分别产生中间数组，不用重排、融合乘加或 `allclose`。`.5/.75/1` 都精确二进制可表示。融合、Euler、RGB 处理的期望数值不使用宽松相对误差，绝对容差为 0；发生差异先 FAIL，列实际非零差数/最大差，不能看结果后放宽标准。
2. **保护位置严格比较原字节。** 包括 history 和 mask=0 的 clean、最终 latent，以及 bool image_mask 为假的 Gpaste RGB。保留 `where` 的回退语义并检查有符号零，不仅比较数值相等。
3. **uint8、bool、整数及身份严格相等。** 全 24 张 raw→uint8 独立转换逐字节比较；计数、槽序、字段集合、文件和 body hash 精确匹配。浮点范围元数据应是保存 FP32 的 Python float 精确转换，本身也精确比较。
4. 如静态源审发现作者实际使用不同但合理的算术顺序，必须在任何真实检查前报告并明确修订依据；本计划不预留事后 eps 通道。评分显示值的舍入容差属于之后另一个统计核器，不能用于本派生核器。

## 最少充分的重算内容

- S86 最后七字段全部核身份/有限/schema；`next_sigma=0`、`sigma_hat>0`、G0 raw/used clean 原字节相同，`sigma_hat` 保留原 `sigma+1e-6`。从保存 `x_tilde/sigma_hat/next_sigma/raw_clean` 重演无融合 Euler，核保存 G0 output/all8 latent。此项只是旧保存量算术复算，不是一条新 λ=0 解码臂。
- 每个 λ：按 `weight = mask * (~history) * float32(lambda)`；先 `(1-weight)*raw_clean`，再 `weight*warp_latents`，求和后 `where(weight>0,mixed,raw_clean)`。随后先 `(x-clean)/sigma_hat`，再 `next_sigma-sigma_hat`，最后 `x+dt*derivative`。逐个核三组保存的 clean_used/all8_latents 与保护位置。
- 原 mask/RGB 的 shape、范围、黑孔洞、history 零 mask/warp 及固定槽序；用整数 8×8 支持数除 64 核保存软覆盖 mask（不是学习的置信度，不改它）。
- 三组 RGB：对 G0 raw **逐帧**按 min<−.1 决定 `(x+1)/2`，先 clamp[0,1]，再原 bool mask×λ 的乘加与 `where`。不用 G0 uint8 混合，不把 latent mask 用于 RGB。
- 六组全部 raw FP32 和 uint8：原 CHW→HWC、逐帧 min<−.1 分支、乘 255、clip[0,255]、astype uint8 截断。核四项 target_id/raw_min/raw_max/maps_minus1_plus1 元数据，不能四舍五入或先量化再合成。
- 核六组状态/顺序/成功和未运行集合，top 与各组 receipt 一致；恰好一次既有 ft-mse VAE 加载、3 次 full8 wrapper decode、24 次 chunk1 decoder forward，0 denoiser/encoder/新噪声/GT/几何/优化；各 terminal 8 chunks、各 paste 0 chunks。无 λ=0/.25 新解码。具体键名以冻结合同为准。
- 核初始化完成后与全部派生结束的完整 Python/NumPy/Torch CPU RNG 状态及组合 SHA，无逐组状态档案，不能宣称核过每个调用的 RNG 历程。各组共享同一个固定 G0 来源，不重新抽噪声；源码无其他抽样与真实计数是补充证据。

最终 NumPy 复算严格保留两条已有路径的差别：Gpaste 的 Torch `min<-.1` 将阈值转换为 FP32，因此独立核器使用 `np.float32(-.1)`；原 NumPy发图仍比较 Python `-.1`。Torch clamp 保留负零，独立核器用 `<0`/`>1` 的 `where` 复现，而不用会改变负零的 `np.clip`。两份准备期人工记录 `SYNTHETIC_NUMPY_CLAMP_NOTE.json` / `SYNTHETIC_THRESHOLD_NOTE.json` 均为0真实数据，未改变生成器或评分器。

root 未来新建的 `DERIVATIVE_REVIEW_BINDING.json` 必须含 `accepted=true`、`checker_sha256`、`review_plan_sha256`、`runner_sha256`、`generation_contract_sha256`、`generation_receipt_sha256`；若绑定监督记录，使用 `supervision={path,sha256}`，路径固定本目录 `supervision_01/SUPERVISION.json`。启动参数只接该绑定的精确 SHA，不自动查找新回执。命令解释器保持 `R/.venv-cut3r/bin/python` 原路径，不 resolve。

## 报告边界与资源

复核只确认六组封存产物、算术与身份记录一致，不重跑 VAE，不证明解码器数值正确、参考图质量、几何准确、跨场景推广或创新成立。新24图是同一已见场景四相关目标的六种处理，非24独立场景；旧 S86 16 行不是本轮新运行。

计划上限：120 秒、进程 RSS 1 GiB；遇到超限/缺键/NaN/错哈希/字节差立即保留 FAIL，绝不临时调阈。准备期可做少量人工 FP32/有符号零/量化边界用例，清楚标合成，不能据此代替真实保存量核验。最终绑定与输出 schema 收齐后提交完整源码及不可变 SHA 给 root 读审；本计划本身不会发起真实核验。
