# S87 源码交付

记录：2026-09-10T23:32:22.084001+00:00。这是实现作者自检，不是不同作者验收或真实生成结果。

固定入口 `generate_terminal_controls.py`：fea09f959f9ecfe86407fabc57408f95eb7a6fa7652322f06f172c24e8eca5d6。正式合同 `GENERATION_CONTRACT.json`：337982b200182b50ade46aee4625c5c7ff3d87f5acce01bd48343451015c2538。协议实际 SHA 仍 bdd5bb25b39cf810711ad91a9035cadc68b6a33aa010fc1defecbedcbada370d，无漂移。

只做一次人工检查：38 项通过，0.577298333 秒，原 wrapper 对小张量及显式 stub 共 24 chunks；0 真实数组/权重读取、0 VAE 实例或真实解码。人工过程未另测峰值 RSS。`author_synthetic_01/RECEIPT.json` 保留当时精确源码和合同身份；准备期缺 diffusers metadata 与 schema 修正如实列在 PREPARATION_SOURCE_RECEIPT。

root 按合同 SHA 启动固定入口；入口自己 create-only 新建 execution_01。root 外层监督负责正在执行的 C++ chunk 卡住时的实际停止；入口在边界检查 600 秒总限、120 秒 terminal、16 GiB 自进程峰值、1 GiB 新文件和初始 2 GiB 空间。无自动加时、重试、改强度或评分。

6 顺序为 Gpaste_l050 / Gterminal_l050 / Gpaste_l075 / Gterminal_l075 / Gpaste_l100 / Gterminal_l100。top counts 记录调用计数，arms[name] 与独立 receipt.json 内容相同，文件描述符另放 arm_receipts[name]。targets_fp32/uint8 在 arrays；terminal.clean_used/all8_latents 全 8 槽独立 NPY。3 组完整 8 槽 chunk1 VAE 解码，0 encoder/denoiser。Python/NumPy 完整 RNG JSON、Torch CPU 完整 RNG NPY 在加载后和结束保存。仅生成全部封存之后，root 的另一入口方可读固定目标参考。

模型只使用同 ft-mse VAE 与原 wrapper，不导入 VMem 网络/完整 pipeline；原 to_d/append_dims 直接编译固定 sampling 源中的函数 AST。原模型 helper、S70 加载路由和输入 body 身份均在合同绑定，执行时核实原数组/权重字节。没有冒称当前已经读过它们。

不同作者正在精确源审。两份冻结入口文件已交 root 后不再编辑；真实执行、独立保存量核验、评分及科学接受由 root 接续。旧实验和主账未修改。
