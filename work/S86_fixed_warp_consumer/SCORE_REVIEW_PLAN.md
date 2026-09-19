# S86 不同作者保存量统计复核：执行前计划

`check_saved_scores.py` 属于与 `score_outputs.py` 不同的作者。当前只准备源码及纯人工边界检查，没有读取当前生成数组、评分数组或目标参考，没有执行正式评分/复核。科学结果仍以实际正式终态为准。

## 何时执行、如何绑定

必须等四臂生成和 `scoring_01` 全部完成并封存，root全文核读源码后，才新建 `SCORE_REVIEW_BINDING.json`。绑定以下六个实际完整SHA：

- `checker_sha256`：本复核器最终源。
- `scorer_sha256`：固定评分作者源 `1ec930bf6f3bb24265efbae3c5095a563d74a14d9451bb23c628625b803ac055`。
- `scoring_contract_sha256`：`7cebfeb86b3e86b68fede211c5da496367746227eeddfc709b19ad060a25c787`。
- `generation_receipt_sha256`：本轮 `execution_01/RECEIPT.json`。
- `scoring_receipt_sha256`：本轮 `scoring_01/RECEIPT.json`。
- `scoring_input_binding_sha256`：评分作者在数组读取前写入的 `scoring_01/INPUT_BINDING.json`。

运行命令只允许一次，不自动重试：

```text
R/.venv-cut3r/bin/python -I R/work/S86_fixed_warp_consumer/check_saved_scores.py --binding-sha256 <实际SCORE_REVIEW_BINDING.json的SHA>
```

保留venv解释器的原路径，不resolve到base解释器。本机固定NumPy1.26.4。结果排他新建 `INDEPENDENT_SCORE_REVIEW.json`；异常保留错误与此前已检查项，不改输入、指标或容差。120秒SIGALRM、自进程峰值1GiB采样限制；不是操作系统硬内存隔离。没有模型、几何、优化、图像选择或新增训练。

## 固定读取范围与身份

读取精确绑定的评分源码（仅hash，不import）、两个协议、两个终态回执、评分INPUT_BINDING，以及其中绑定的各臂小回执、4份uint8目标数组、原保存image_mask和已接受S70变换后uint8参考。先核完所有预测身份，后读参考一次。最后重核生成与评分终态SHA仍相同。

评分回执必须绑定全部5个产物：FRAME_SCORES.csv/json、ARM_SUMMARY.json、CONTRASTS.json、INPUT_BINDING.json。逐个核路径、完整文件SHA与大小，固定全部4臂×4目标；不读“最新”或其他执行目录。数组逐档案与C字节体SHA/shape/dtype核。评分作者的16项原raw→uint8一致记录作为已封存前置证据读取，本核器不重复读raw或声称另做一次量化复算；原发图规则不改变。

## 不同实现的统计路线

逐帧逐颜色通道，把uint8预测和参考升到int16求差；差值只可能是−255至255。对full、原mask的support、其补集hole分别构造511格整数直方图，用Python任意精度整数累计 `计数×差值²`。没有uint8相减/平方溢出，也没有复用作者的int64平方数组再求和实现。

- 全部16行、每行full/support/hole共48组：pixels、channels、SSE、empty严格相等，MSE由 `Fraction(SSE, channels*65025)` 得到。full固定331776像素、995328通道；4帧总3981312通道。独立核full SSE等于support+hole。
- JSON逐字段核完整schema；CSV严格17列表头/16行顺序，所有整数/布尔字符串精确，MSE空值必须为空字符串；不允许用0代替NA。
- 4臂×3区域：总SSE/通道、是否四帧均有区域严格核；等权mean为四个精确分数之和除4，任一空帧即None；pooled为总SSE/总通道，只有总通道为0才None。不会丢空帧算3帧mean。
- 3组guide−control整体对比（Gterminal/G0/Gpaste）和全部12个逐目标对比：SSE有符号差精确；mean/pooled分别用Fraction计算。逐条输出精确方向与浮点显示方向，不以区域总SSE的方向冒充等帧mean方向。

## 展示数值容差与方向

整数、布尔、顺序、NA和所有身份没有容差。浮点展示与精确Fraction转成binary64后的数值比较：

`允许绝对差 = 16 * epsilon(binary64) * scale + 16 * 最小正subnormal(binary64)`。

普通MSE和直接SSE比分差的scale取精确值绝对值；区域整体等帧差来自两组四项浮点均值相减，scale取两组精确均值绝对值之和，以覆盖加总/相减舍入及相消。不是科学显著性或质量阈值，也不根据结果调整。

每项记录精确分子/分母、实际显示值、绝对差和允许界。所有方向以Fraction为准：负值表示Gguide此项误差更低，正值更高，精确0为相等，空区域NA。如果区域mean差小到浮点显示不能解析其符号，明确记录显示方向是否一致及其不能解析，不将浮点相消变成收益。超出上述舍入界的方向错误直接FAIL；主全图差和逐帧差使用共同整数分母，不借区域相消解释逃避方向检查。

## 最窄接受范围

PASS仅接受一组封存图片上的统计与保存一致，保留全部目标和区域分母。它不接受新模型生成质量、物理几何精度、视觉偏好、统计显著性或创新；四目标属于一个已见场景，不能将像素/通道数当独立样本数。正式消费链核验、评分作者量化核验和root结果解释各自保持边界。
