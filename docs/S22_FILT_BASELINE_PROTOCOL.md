# S22：补入FILT3R强基线

本协议在S21的300帧TTT3R尚运行、S21实测GT评分尚未执行时形成。不是新方法；不因S21哪个方法获胜而选择更弱配置。原草案保留，最终执行身份由同目录准备后的run_manifest.json冻结；冻结也不代表运行完成。

## 目的与输入

在S21相同前300对TUM fr2_desk帧、同一512 DPT权重、CPU8 FP32、crop=True、revisit=1、无GT相机/深度输入下，运行FILT3R官方公开配置。固定源码`6cf6d28b6ec7fbcc985187a0f099ccbc90224392`，124文件身份在`work/S22_filt_preparation/source_manifest_v2.json`。输入直接继承S21 run_manifest的顺序与哈希，不另选容易子段。此序列已见，且不是完整TUM-dynamics基准。

## 真实入口与对照

使用官方`inference_recurrent_lighter`，model_update_type=filt3r；按官方launch.py实际装载FILT3R_DEFAULT_HPARAMS到model.hparams与config，不只改model类型。公开参数为p_init=1.5、gamma_p=1、q_min=.02、q_max=.5、alpha_q=20、tau_q=3、beta_delta=.05、delta_floor=.01、fixed_r=1；k_min=.01、k_max=.99来自完整Config。没有新增调参或训练。

先在FILT树cut3r模式跑相同前4帧，与S21已存原CUT3R4帧的六头结果检查；兼容容差继承S21，pose 1e-4/1e-4、其余5e-4/1e-4。通过才运行FILT300。检查是新源码迁移验证，不重新声称旧基线重复带来科研进展。若不兼容，保留并调查，不自动放宽阈值。

资源上限继承每次1800秒、32GiB进程树RSS，顺序运行以减少与S21模型计算竞争。全部300帧预测保存和封存，再评分。即使S21的GT已先用于评分，FILT仍使用这里预先固定的公开配置，不根据结果调参；仍保持已见探索标签。

## 评价与解释

继承S21官方evo全序列Sim(3) ATE、相邻RPE translation和rotation，原evo与同作者独立矩阵实现对照。所有300帧、299相邻对、五个固定60帧段均报告。跨实现计算耗时含保存且attention路径不同，不能作最优速度基准。

比较回答FILT是否已解决TTT在这条序列的剩余误差。结果若已被已有方法解释，应收束对应候选；若仍有问题，下一步先找受控反例和最接近修复方法。单序列胜出、曲线相似或“更保守”均不足以说明新颖性。

独立作者前审当前缺席（三agent额度中断），须明确同作者自审范围；不得虚构评审。Supervisor vibe/idea-evaluator及Claude本地科学批判技能继续适用。新方法和完整生成结果本阶段仍未承诺。

观察范围：新增纯记录包装器统计原Kalman函数的实际调用次数和gain/cov均值范围，返回原对象不改变更新；预期首帧后299次。记录的第i帧gain在第i帧输出之后计算，影响后续状态，不能反过来解释该帧已经产生的输出。4帧cut3r模式调用数应为0。原始4帧兼容门前不改状态公式。
