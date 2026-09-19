# S76 展示脚本独立源码审查

通过本次有限源码审查，没有阻塞项。实际审查时间为 2026-09-09T09:40:49Z 至 2026-09-09T09:41:15.345176+00:00。源码 `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S76_relative_camera_response/prepare_visuals.py` 的 SHA256 为 `2fe978f0df91c2a9351551be41a145ed2506f4491b0d8de45c6818bc5b52a8bf`。

脚本只接受本轮封存评分回执的精确路径与调用方提供的 SHA，要求全部四目标 20–23、无未运行目标。每目标固定读取 A0/yaw_plus5 两张 576×576 RGB PNG，核原文件 SHA 与解码像素 SHA；不根据匹配结果选择图片。图片原尺寸粘贴，四张配对图为 1152×640，全四图为 1152×2560。代码中的 crop 仅用于回切粘贴区域检查原像素相等，不裁切展示内容。无缩放、增强、warp、重匹配或模型调用。

每幅图明确写有 MODEL-GENERATED / not a real photograph，A0 标明 reused baseline。输出使用 create-only，记录来源及输出文件/像素 SHA；渲染阶段异常保留 FAILED_PRESERVED。实际图片、字体渲染和输出尚未被本审查者读取或执行，不能预先认定视觉 QA 通过。

两个有限记录边界：输入/字体读取在创建输出目录和内部 try/finally 之前，若此时失败应由 root 外部进程回执保留；内部开始时间也不含这些读取。输出像素 SHA 来自内存 canvas，文件 SHA 来自保存 PNG，脚本没有再解码最终 PNG。这些不改变本次原像素展示实现，不新增一轮审批或实验。

本次只读完整源码与固定合同尾段，0 科学数组/图像正文、0 模型、0 scorer/verifier/visual 执行。展示成功不能说明相机符合、生成质量或方法成立。
