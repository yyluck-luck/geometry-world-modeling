# 固定上下文与幅度匹配的几何块替换诊断（S100）

类型：已见S15B真实模型输出的探索性几何消费者重渲染，0新神经网络推理。沿S99负结果研究一个新问题：相同改写数量与近似改写幅度下，把一个低D专属候选换为confidence专属候选，收益是否依赖其它已更新的块？不是恢复S99已拒绝的lowD优势主张，也不是校准/GRC方法验证。

## 预测前固定规则

原数据与原renderer绑定S99 FREEZE全部身份。4来源×196个16²块。两候选池取S99 low_D前39和confidence前39的差集；交集排除，两类均为历史确定。禁止读未来深度/RGB/GT mask筛选候选。

每块在米单位计算mean(abs(new-old))与RMS(new-old)。同source候选对要求两者均为正，mean幅度比max/min≤1.10，RMS幅度比≤1.25。合法边按(abs(log(mean比)),lowBlockID,confBlockID)排序，贪心无放回匹配，最多4对/source。保存候选池、全部历史幅度、合法边和最终配对；未选原因可由冻结规则重建为幅度不合格、候选已占用或达到4对上限。无匹配不能改caliper；全零停止，部分source缺失则只做受限资格探索，不泛化到全部来源。此规则先保存协议、源码SHA再扫描历史幅度；不是事后放宽阈值。

每对固定2背景，seed=2026091400+100*source+2*localPairRank+contextIndex。用NumPy default_rng/PCG64，按source0..3依次无放回选择：焦点source从排除两个候选的194块取38，其它source取39。背景155块；加任一候选后156块，每source39。两臂只有焦点source两个不同块的old/new互换，所有后代投影/z-buffer/source身份重算。每对最多16 renders，总≤256；另加首个条件target20精确重放1次。给定query相机/K/尺度完整继承旧合同，非预测的未来相机。

在选择阶段封存全部候选mask、背景、配对与历史特征；再冻结不同作者前审与代码；执行完成封存全部预测后，独立score invocation才读已见GT。输入暴露不因本轮隔离而消失。

## 评分域和决策（执行前冻结）

每target全部finite positive GT像素为同一固定分母。主损失为capped AbsRel：预测有效则min(abs(z-g)/g,1)，无预测则1。缺失不能通过丢弃困难像素降低这一损失。它是自定义有界诊断损失，不冒称标准AbsRel；cap0.5和2全部报告敏感性，不按结果择cap。附coverage、delta1_all_gt、有效预测自身未截断AbsRel、fractional worst5有界损失（取最高5%质量，边界小数权重）。保留每target分母、缺失数和极端误差数。

成对收益B=L(low)-L(conf)，正表示该固定背景下confidence候选替换有利。先每对平均两个背景，再每source等权平均其实际匹配对，最后对可匹配source等权平均；四target等权。背景/像素/四target不当独立场景，不报显著性。全样本平均、每source、每target和每对两个背景的B均报告；容差1e-10，只表示数值分辨阈值，不是实用显著性。

明确分开两项：替换收益方向（mean B）；上下文交互（相同pair/target在两个背景B一个>1e-10且另一个<-1e-10的数量）。所有cap均报告，不用一项成功代替另一项。若出现符号反转，只支持“该pair在该消费者和两个背景中有交互”，不证明新颖性或普遍规律；若未出现，只表示本覆盖中未发现，不能证明可加性。若mean B不正，停止“匹配幅度后confidence替换平均更好”的本地解释。即便正，空间位置、几何内容、置信度含义仍未全部控制，不能把它解释为信息增益或风险校准。不是单块绝对效用，更非任意集合最优上界。

## 验收与停止

同数量只是source-block改写预算，不是k记忆容量；mean/RMS caliper是近似幅度控制，不保证分布/位置匹配。全部原结果保留。每阶段600秒、8GiB，CPU单BLAS线程。新目录拒绝覆盖，非有限/身份变更/精确重放失败则停止评分。独立作者重算选择和至少一个新条件投影、全部主要聚合。候选匹配本身不是模型收益；没有新颖性授权：new_method_validated=false，novelty_authorization=NONE。
