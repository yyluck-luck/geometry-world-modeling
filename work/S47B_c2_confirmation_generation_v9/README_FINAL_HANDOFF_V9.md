# C2 V9 最小恢复源码交接

V9 已完成源码准备与原有自检；尚未执行正式 prepare、attach、授权、启动、模型或真实 C2 像素读取。

V8 的第一批到 23/50 后收到 SIGTERM，完整批次 0；信号发送者和原因未知。V8 原目录全部 66 个文件的字节、权限、修改时间在本作者工作前后均一致。该中断不是算法质量失败。

本版只改新尝试/输出路径、说明文字与对应 SHA 绑定。五份生产 Python 文件的所有函数、类与 V8 完全相同；将已声明路径和 SHA 变化反转后，五份文件整体恢复 V8 原文。runtime_adapter.py 与 seed44 YAML 逐字节不变。CPU8、FP32、ft-mse VAE、living_room、seed44、两批各 50 步、400 次几何迭代、原资源上限和后续独立评分均保持。

原有 source-only 自检在 Python 3.12.14、3.13.0 各实际执行一次、returncode 0。没有新增测试矩阵；临时合成数据不是真实模型生成。

冻结源码清单：`FROZEN_SOURCE_SET_V9.json`，SHA `33e2a733735e959b8e912f18e3476b521fa7ee15f4d893f763ecb87a436afa6f`。
最终作者回执：`SOURCE_ONLY_AUTHOR_RECEIPT_V9.json`，SHA `9ad5123790d469a5cdbca807210e0aecacf00816025a0db4e65dc9660f669f4b`。
查看 `SOURCE_DIFF_FROM_V8.patch` 和 `SCIENTIFIC_DELTA_AUDIT_V9.json` 可逐项核差异。

主任务接手后先重算上述冻结 SHA，再取得两份不同非作者新源码审查，沿既有 prepare → core reviews → attach → final reviews → authorization → 单次监督启动推进。旧 V8 票据不授权 V9。

B0 与 C1 已有 MSE 均小于 0.01，使原至少 2/3 事件假说不可达；C2 仍须按 S42 完成，不改阈值挽救假说。没有新方法或创新结论。

真正启动时保留外部观测器所在的活动执行会话，直到获得真实返回码与完整终态；这是为了保留实际退出证据。V8 外部最终回执缺失，但不能由此断言会话结束、休眠、超时或任何指定进程导致了 SIGTERM，也不能保证下次不受中断。
