# 后续生成对照补强：全过程引导需要面对最后一步融合

记录UTC：2026-09-10T20:11:37.851513+00:00。当前只是后续生成方案的源码、数学与强对照决策；S85真实投影尚未执行，本文件不改其设计或参数。

## 研究问题

普通Gguide如果优于最后RGB贴图，收益是否只是VAE里的一次融合/解码，而不需要较早去噪步骤？要区分这个解释，保留G0、Gpaste，并加入Gterminal。只有全过程Gguide在独立参考上胜过最后一步Gterminal，才支持本次固定条件下“较早融合连同后续传播带来额外收益”。这不是某一步、某条内部路径或长期记忆机制的独立识别，也尚无真实收益结果。

## 实际源码与可核推导

已读原 `modeling/sampling.py` 的CFG prepare_inputs/MultiviewCFG及Euler完整步骤250–441行；`utils/util.py` do_sample673–735、tensor_to_pil951–967；AutoEncoder全文；S70 runner55–117、300–395和协议；S82普通融合函数全文。原文件未改，源码身份见附带ROOT_CONSUMER_SOURCE_REVIEW.json。

原Euler在CFG后、to_d前得到clean预测d。令已加噪状态为x_tilde，a=sigma_next/sigma_hat，则原步E=a*x_tilde+(1-a)*d。将d换为d_g=(1-w)*d+w*g，同一步相同输入下：

`E(x_tilde,d_g)-E(x_tilde,d)=(1-sigma_next/sigma_hat)*w*(g-d)`。

sigma_hat严格正；若讨论朝g方向还需日程系数非负，任意非负next_sigma本身不保证这一点。最后next_sigma=0时，每条轨迹自己的最后步在精确算术下等于自己的d_g。引导已改变此前状态与当前d，不能把全程轨迹等同于从G0末步d才融合。

已执行纯有理数人工核对：同一步原7、引导7.5、差0.5；末步原4、引导5；两步人工d(x)=x/2例中G0=3、Gterminal=1.5、Gguide=1.25。另一个作者静态独立推导与读回通过。这些不是训练模型结果，也未验证真实FP32挂钩。

## 精确且便宜的后续实现

- 复用原S69 geometry条件身份及历史槽19/18/13/12、目标20–23；不重算get_cond、不改变检索/坐标归一化。
- 使用同一S85固定warp，RGB洞值、图像mask、latent mask、VAE均值编码和最终强度/步数规则要在后续生成合同一次定清。S85不承担这些后续参数选择。
- G0与Gguide各做一次真实生成，保留原50步及实际共同随机流；Gpaste来自G0的末端RGB算术；Gterminal来自同一G0最后步骤的保存量，不需要另跑全denoiser。
- 为避免FP32末步相消误差被当作效应，G0显式保留最后一次加噪后的x_tilde、CFG后的d、sigma_hat和next_sigma。Gterminal复用同一最后Euler算术，只替换d为d_g，再同VAE解码。直接解码融合d_g是精确算术等价但未必字节等价的简化，不将两者偷换。最后一步零融合应回到原末步算术结果。
- 旧S70只保存最终返回latent，没有显式最后clean d及x_tilde，因此不能声称旧结果已满足该额外对照。为新的因果问题增加一次有记录的G0是有科学目的的运行，不是无理由重跑。
- 融合只能作用规定目标槽，history slots的w必须0；不把历史缓存与当前denoised历史值混为一谈。原Euler在churn0仍有randn_like和1e-6，实际噪声/RNG流需记录，不能只比较seed。
- sampler.guider的可调用代理可以先委托原MultiviewCFG，再应用普通融合，同时原样转发prepare_inputs；不在CFG之前改变双倍batch，不替换原Euler数学。正式代码和人工调用/RNG检查尚待实施。
- 原quantizer按min<−0.1选择从[-1,1]转RGB01。Gpaste必须明确先按G0原规则取得RGB01、再与同范围warp合成，保存浮点和量化值；不能把RGB01直接塞入未经转换的VAE原输出。Gterminal/Gguide使用同一解码/量化规则并记实际分支。
- 独立参考评价另立合同：全四目标完整保留，全图以及预定mask支持/洞/边界，空集NA。几何投影支持不是GT，旧TUM是已见探索集。内部warp吻合、图像改变、像素数量都不代替独立收益/场景数。

Gguide若只胜Gpaste而不胜Gterminal，应否决“较早采样反馈更有益”的本次主张。即使胜Gterminal，若仍劣于G0也不报整体改善。还须经其他简单规则、独立场景与消融，才可能形成新方法；本轮没有选择新方法。

## DSH实际调用及拒绝项

一次本机DSH headless请求，实际2026-09-10T20:04:00.490869至20:04:11.975107 UTC，11.484110秒return0；session读回确认OpenRouter/deepseek/deepseek-v4-flash-0731，报告10903输入/1099输出tokens，0工具事件。费用为未知实扣，提示350词并未成为硬token限制，wrapper自身还有900词软提示。没有再次请求或升级模型。

只采纳经独立推导吻合的公式和精确算术限定。拒绝其history mask方向反转、Gterminal需要全denoiser、RGB与latent近似等同、较早引导轨迹末步不满足自己的等式，以及未定义driver/beta-flip等表述。完整不同作者审查见TERMINAL_CONTROL_INDEPENDENT_REVIEW.md。

模型响应与UI归组分开：新session-7821f25d-ace9-4b20-b191-d242e924ea00的cwd正确，但官方归组请求HTTPError，仍未归组。只读端口进程已观察监听；CUA第一次策略读取错误、一次重试成功，后续本地页面被客户端ERR_BLOCKED_BY_CLIENT拒绝，未换路绕过或重发模型。原PRIVATE stderr不进入用户交付包；没有读取或记录API key。


## 后续成本估计补记（实际记录UTC 2026-09-10T20:22:29.943214+00:00）

本次已实际完成S85投影，运行2.293416秒、全进程2.378199秒，尚待独立结果核验；它是保存数据上的投影计算，不含模型前向。后续VMem生成不能据此估为几秒。root只读S70实际回执：原A0/A1/B三次50步CPU8生成分别1475.498261、1478.356200、1473.845816秒，合计监督4438.423214秒，峰值自进程RSS17842339840字节。已有完整原设置在本机可跑，但新的G0与Gguide两条完整链应按约50分钟量级估计，再加新warp编码、Gterminal解码、记录和复核；这只是基于旧运行的计划估计，不是新实际耗时或保证。

新生成仍应采用冻结的约束、逐步进度和外部资源监测。G0捕获最后CFG clean预测和Euler加噪状态有明确科学用途；Gterminal/Gpaste复用该G0，不多跑完整生成链。旧S70的精确重放成功不代替新instrumentation数值不变性核查。不得为快速出结果默减50步或576分辨率；若需改变实验规模，应作为明确变体单列。
