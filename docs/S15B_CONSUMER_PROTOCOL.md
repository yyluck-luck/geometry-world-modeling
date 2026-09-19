# S15B 固定来源显式记忆的真实深度评价

本协议是S15B_PREFIX_PROTOCOL的下游实现补充，在目标depth像素读取前固定。旧TUM block0及目标以前被S14E使用过，本次是探索，不能称独立留出确认。照片证据也不是可见性认证，简单两候选成本不是新方法。

七种方法共同使用来源0、3、6、9，同一224像素身份、K、given source c2w、12帧A/s/c与目标20至23的given depth时刻相机。共同来源候选域为old/new都有限且正。只改变source self-z：never=old；all_new=new；half_blend=(old+new)/2；pool/split/matched按固定整块mask选择；model_confidence逐16块比较new conf_self均值>old conf_self均值，tie留旧。confidence不是校准可靠性概率，其跨首写/查询标度可有偏差；这只是共同提案的组件控制。

模型单位z按标准pinhole构source点并以共同source c2w变world，变换到目标相机；有限、正target-z且floor(pixel+0.5)落在0至223时才投影。每目标像素z-buffer取最小target-z，完全相等按来源序号0/3/6/9，再row*224+col取小者。输出除共同s成米，缺失0，保存获胜source_pixel身份。无孔洞填补、splat扩张、confidence删点、按GT调尺度或选择帧。

先封存七方法四目标全部预测和出处、输入/程序/协议身份，再读4张已固定target sensor depth。GT uint16/5000，以PIL NEAREST resize299×224后crop(37,0,261,224)。全部正有限GT作主分母；预测缺失计δ1失败，严格max(p/g,g/p)<1.25。每目标记录coverage、δ1全GT分母，以及自己的有效交集MAE/AbsRel/RMSE；另记录七方法共同交集的同指标。主结果四帧等权，不用像素访问数假称独立样本量；补充像素加权δ1。

root实现，另一个作者审代码并用人工碰撞/边界检查或标量参考核算后执行。预测输出必须先封存才允许score模式读4depth。不存在新RGB解码、模型重跑或训练；真评分是保存模型提案的外部几何消费者测量，不是完整VMem视频。

可继续的最低信号：选择性修改至少在本段超过never与all_new，且与matched同改写量比较有正差；否则不能把该规则包装成新方法。即使通过也只有单段探索信号，尚缺完整同信息MVS基线、多序列/运动难例、预算/延迟匹配及未见确认。
