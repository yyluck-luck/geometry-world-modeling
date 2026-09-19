记录UTC：2026-09-10T20:07:32.646270+00:00。

# 终端latent融合对照：独立数学与DSH答复审查

**结论：root的同一步差公式、最后一步等式和两步人工反例均正确；DSH仅可采纳同一步公式、精确算术限定及最低标量测试思路，其mask方向、终端对照成本和RGB/latent类比应拒绝。** 本审查不涉及S85投影真实运行，也不把普通融合称创新。

## 1. 独立推导与已保存人工值

把已加噪的输入写作 $\tilde x$，令 $a=\sigma_{next}/\hat\sigma$。原Euler步可整理为

$$E(\tilde x,d)=a\tilde x+(1-a)d.$$

在完全相同的当前 $\tilde x,d,g,w,\hat\sigma,\sigma_{next}$ 下，只替换 $d_g=(1-w)d+wg$，即得

$$E(\tilde x,d_g)-E(\tilde x,d)=(1-a)w(g-d).$$

该式要求 $\hat\sigma>0$，不要求重跑或近似denoiser。共享加噪项在两边相消；root人工程序里的x已经代表 $\tilde x$，没有遗漏另一份随机数。若需要把差解释为朝g方向移动，另须按实际日程考虑 $1-a$ 的符号；单有 $\sigma_{next}\ge0$ 不保证其非负。root没有以此额外声称任意日程都改善。

最后 $\sigma_{next}=0$ 时，**每条轨迹自己的最后一步**都满足 $x_{next}=d_g$（精确算术）。此前受过引导的轨迹也满足此式，只是其当前 $\tilde x$ 和由此得到的d通常已不同；所以不能把Gguide的最终 $d_g$ 等同于从G0最终d做的终端混合。FP32的原减法与加法未必逐字节等于d；root要求明确捕获最终CFG后的clean prediction d，而非假设最终保存latent就是d，处理正确。

根脚本与已保存回执的数值逐项吻合：

- $\tilde x=10,d=4,g=8,w=1/4,\hat\sigma=2$：$d_g=5$。next_sigma=1时原步7、引导步7.5、差0.5；next_sigma=0时原步4、引导步5、差1。w=0回到原步。
- 两步人工denoiser $d(x)=x/2$，x=8、g=0、w=1/2、sigma序列2→1→0：G0中间6、末步clean为3，Gterminal=1.5；全程引导中间5、最后 $d=2.5$ 经融合变1.25。故1.25不等于1.5，清楚否定“整条引导轨迹必等于末端一次混合”。

这些是有理数手算与已存结果的静态复核，本次未重跑数学程序。它们不验证真实FP32调用位置、tensor广播、历史mask、RNG调用次数或真实denoiser收益。

## 2. 对DSH原答的取舍

| 原答内容 | 独立判断 |
|---|---|
| 同一步差为 $(1-\sigma_{next}/\hat\sigma)w(g-d)$，同输入限定且精确算术 | 采纳，与独立推导一致。 |
| 终端等式“never for earlier-fused trajectories” | 拒绝这种表述。任何轨迹到next_sigma=0的最后步仍满足自己的 $x_{next}=d_g$；不成立的是把不同轨迹的d当同一个d。 |
| Gterminal要“running a full denoiser”或“rerunning full Gterminal” | 拒绝。已定义方案从G0显式捕获的最终clean d构造同一latent混合，额外需要固定warp编码及一次解码的相关成本；无需为Gterminal单独重跑整条denoiser。若G0未留d，补一次instrumented G0是另一种实际成本记录，不能偷换当前设计。 |
| Gpaste与Gterminal“nearly the same fusion”并提把latent改动直接施于最终RGB | 拒绝。RGB像素合成与latent混合后非线性/非局部VAE解码是不同算子，不应默认等价。即便无早期采样反馈，Gterminal也可能不同于或优于Gpaste。 |
| 对Gterminal先否认必要、再称必要robustness check | 不能照搬。对本研究想归因于“早期采样响应的额外收益”而言，这是具体而便宜的强替代对照，应保留。若只声称某操作改变最终图，是否先做它是另一个更弱问题，不回答root当前问题。 |
| 最小fixture让w仅在history slots非零、其他位置为零 | 明确拒绝，方向与冻结问题相反：**history slots必须w=0**，只对规定生成槽应用mask/strength。不得照此修改实现。 |
| “G”或“β-flip”“rollback”等未定义符号、称能定位driver | 不采纳这些含混解释。应只用已定义G0/Gpaste/Gterminal/Gguide及明确的比较结果，不能凭画面不同确认原因。 |

## 3. Gguide相对Gterminal能识别什么

在相同原条件、实际RNG流、固定g/mask、最后一步融合定义和同一解码设置下，该比较测试：**加入已声明的早期融合步骤，其整个后续传播是否带来额外最终输出差异/独立参考收益。** decoder的非线性是这条干预路径的一部分，不能仅凭两臂把它与各步denoiser响应拆开；也不能定位某一步或证明几何物理真值、长期记忆必要性、稳健泛化或新方法。

要声称“带来收益”仍需独立参考指标；只观察Gguide与Gterminal不同，只能说明响应不同。最后融合若不同、RNG/条件/历史选择重算或参考相机规则变化，比较还混入这些变化。因此root问题中“不重跑get_cond、不改历史、同实际RNG、成本单列”的方向合理；本审查不新增一轮实验或替后续生成合同选强度/步数。

## 实际读取范围

只读取下列四文件，未执行数学程序、读取科学数组或凭据、调用模型/工具给DSH、修改root源码。DSH答复是已存第二意见，不是证明或实验。

- `check_terminal_blend_math.py` SHA `ce92418f3ae6e14f79d418ad90ffc5da22e844f7bcc7d3b0abaddb3db3e49735`
- `TERMINAL_BLEND_MATH_CHECK.json` SHA `e804ab8fb80f7ad1f84e8a0608c588cc42dc1bf08f46b07e1b31ddc0a3069203`
- `DSH_TERMINAL_BLEND_QUESTION.txt` SHA `4835f6a5b532671c5837df0df08fff7bb1f9aad240420637e45558d3f7786230`
- `dsh_terminal_blend_review_01/stdout.md` SHA `87c45a0ae515308e0517accfc23ce9a66e8fe5dc30c270604310c2d980d3b3df`
