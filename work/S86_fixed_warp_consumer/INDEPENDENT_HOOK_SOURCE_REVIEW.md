# S86 挂钩与人工回执独立源审

**PASS（有限范围），没有阻断接线的实质问题。** 本审查只接受已冻结局部挂钩与其作者人工证据；完整生成入口、实际回调和合同仍由下一次精确源码审查覆盖。没有重跑人工批次、导入真实模型或读取科学数组。

审查 UTC：2026-09-10T21:24:13.886206+00:00。

## 精确版本

- `sampler_hooks.py`：`2521dac2e07d0809eaecf23c37e6f41a5d157435ef7e5d010eec8ce840933ae4`。
- `check_hooks_synthetic.py`：`32cb9b3be881cb375f688d3e96353c5ec67764a97f3d8c4738b57b942a857942`。
- `HOOK_SYNTHETIC_CONTRACT.json`：`f250d368d4dbd5b8c859b3b25660fce6d67b86e5b91632b6bb8fcaaa895e206b`。
- `synthetic_hooks_01/RECEIPT.json`：`c42c469ae73e7f14989db98fc9045cc48c37ccec0efac7528c4e3f57f93c36f8`。

全文核读189行hooks、209行人工checker、完整合同和483行实际回执；对照原MultiviewCFG、Euler step/loop、to_d以及原S82融合函数。三个依赖源码的SHA均匹配。

## 为什么通过

挂钩保存原绑定的 sampler_step，原样传递参数；没有重写原噪声、sigma_hat、网络调用、CFG或Euler计算。prepare_inputs委托一次，CFG合并后才融合。G0原样返回raw对象；Gguide调用固定纯融合，历史mask方向与原input_frame_mask核对。第50步的真实x_tilde在已加噪、尚未CFG双倍batch的位置捕获，不能与网络离散sigma混淆。

末步重演只用G0保存的x_tilde/raw_clean/sigma_hat/next_sigma，按原to_d→dt→x+dt*d顺序计算，不调用sampler_step、denoiser或随机函数。作者零融合重演与原返回字节一致，非零融合的历史/零mask clean值一致。这些是小张量实施检查，不是实际视频收益。

on_clean在融合后返回前调用一次；作者故意抛出RuntimeError时，异常传播，唯一已进入步骤标FAILED并保留callback_calls=1和错误，finally清除当前步。失败和缺步不能通过assert_complete。真实写盘失败需要由root实际回调/外层入口保存，本人工错误不冒称已经测过磁盘故障或OOM。

## 26项实际证据与不得扩大的口径

实际一次批次UTC21:16:18.889047–21:16:19.384404，0.495365167秒；原3步、G0 3步、Gguide 3步和故意失败1步，合计10次确定性stub调用，0学习模型或真实数组。26个命名断言均通过，包含版本/源码身份/RSS及重复逐步保护，不是26个独立实验。

- 裸原采样器与G0逐步Euler返回字节、初始noise和Torch RNG轨迹相同；G0回调中raw/used为同一对象。原裸CFG中间raw_clean未单独保存，不能说已经逐项比对所有原模型中间量。
- Gguide实际3步的Torch RNG前后身份与原轨迹一致，第1步λ0返回原对象，第2/3步λ0.25引起非零输出改变；改变不是改善。
- 末步实际有 **7个tensor字段**：sigma、next_sigma、x_tilde、sigma_hat、raw_clean、used_clean、output。作者通信中的“8字段”应按实际schema纠正；mode/step/gamma/complete是元数据。
- 人工RNG断言针对Torch CPU；Python/NumPy完整状态及真实callback不改RNG仍须在实际入口源码/记录确认。人工shape[8,2,2,3]与3步不替代真实[8,4,72,72]/50步/VAE验证。

## 留给完整生成入口的两点

on_clean收到活tensor引用，hooks本身没有强制阻止原位修改或抽随机数；这是明确的调用者约定。因此root回调应只读保存raw/used、记录不变性，并由保存量逐步复算。不能因hooks文件没有random调用就预先宣布任意callback都透明。

hooks捕获Exception；KeyboardInterrupt/SystemExit或外部终止可留ENTERED，不能写成COMPLETED。外层真实runner负责保留实际终态/部分输出。Guider这里只核类名，完整入口需用已冻结原构造器和依赖身份。这些是下一入口审查中的已有职责，不要求改hooks、重跑成功人工批次或加一条完整G0。

## 给零基础用户的简短解释

多步引导会在生成过程中反复加入历史参考。即使结果变好，也可能只是最后一次融合再解码起了作用。Gterminal复用同一份G0，只在最后一个步骤加入相同历史信息，再解码成图，成本比重新跑整条生成链低。只有多步引导在独立参考评分上还胜过它，才有理由继续研究“较早介入有什么额外作用”；即使胜出，也还不能说证明了新机制或创新。
