# S15B consumer 独立代码与人工数值审查

结论：可以由root冻结真实manifest后执行。原投影、目标相机逆变换、按pixel/z/source identity排序的z-buffer、strict delta1和共同GT分母没有发现公式错误。补充了输入一致性与答案隔离门，未修改七个方法的科学规则；原源码保留source_before_review.py。

已修正的具体缺口：

- Manifest核当前Python、4个明确NPZ角色、4个目标depth的固定顺序和不重复；predict身份仅可含这4个NPZ及MD/JSON/Python控制文件，禁止目标depth、图片或其他NPZ。
- 桥接old/new自深度与原proposals数值相同；source IDs固定0/3/6/9；given source c2w逐元素相同；proposals/bridge/target K和正有限尺度一致；source/target光学旋转必须proper。NaN在相同存档中可比对相同，但共同候选域明确排除非有限/非正值。
- 见证三mask必须恰好bool 4x224x224，并且每16x16整块为同一动作，防止广播或逐像素动作静默进入整块规则。model confidence均值仍使用块内全部256个有限值，严格new>old，tie留旧。
- Score必须在首张GT读取之前验证封存的预测阶段PASS、mode=predict、同manifest、零RGB/GT/model计数、原manifest/source快照、七method与4source/target顺序；预测本体正有限或0、provenance与缺失一致。评分完后再核GT/seal字节身份不变。代码入口manifest/runner事后SHA复核保留。

36项人工检查PASS：独立逐点投影和tuple最小值归约；近z碰撞、同z source ordinal/pixel tie；floor(x+.5)两侧边界、零/负target-z；source camera/scale/order/mask反例；confidence整块均值/tie；严格正反1.25边界、缺失计失败、七方法共同交集、空GT null、帧等权与像素加权区分。另直接用人工数组执行七条consumer，核half的0.75、never的0.5、all_new的1.0，以及共同缺失像素与固定出处。

人工render tie有一例故意用非刚性收缩把多个像素放到同一像素，专门测底层tie排序；实际validate_inputs禁止非proper rotation。人工数值输出保存在synthetic_seven_methods，不可当真实实验。最终36项回执receipt.json；最初33项回执保留receipt_first33.json。

本审查不打开真实S15B/S15C NPZ、图像、GT或模型；源代码和协议是实际读入的文本。只作不同作者代码审查与人工数值验证，不称真实数据独立复算。Supervisor小步骤与本地Claude科学批判技能用于控制来源/相机混杂和正确分母；没有调用Claude模型。当前简单photo argmin没有因本代码可用而变成创新。

真实manifest请包含python绝对路径，predict_identities含runner与bridge/proposals/target_cameras/rule_masks四角色；输出仍为root约定的5个预测文件（NPZ、description、run_metadata、frozen_manifest、source_snapshot）。root应在运行结束后再做实际预测seal，不在真实GT解码之前跳过此步骤。

审查完成UTC：2026-09-06T10:32:21.643598+00:00。

最终runner SHA：`4541af96cfba4a2c7770dd5d9c068f2906e2912794bcb943b39ca15501c4f061`。
原runner SHA：`c7aef2f723d01922ba560fb6d82e635a95bd296458e09017052f803c9d3208e9`。
协议SHA：`767b8bc9d8703570a7792f3c74fd26be7fe64b7e87364c764ed88797931b9b2b`（本agent未修改）。
