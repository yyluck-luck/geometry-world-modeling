# S82 consumer 架构稿路径与 raw 尝试状态勘误

记录 UTC：2026-09-10T18:24:47.694319+00:00。保留 `GEOMETRY_CACHE_CONSUMER_PLAN.md` 原字节（SHA `bc04f4f4893505ce92dc6b2603d45497fbd32193e434e8e57bccd591d832d11b`）；不覆盖当时方案。

原稿第1节以 `execution_geometry_01` 指代当时尚未封存的未来四 heads 输入。该第一次实际尝试后来 **FAILED**：收据记录4图解码、1次模型加载、0次 recurrent 前向、0个head。作者原 runner 检查 `model.config.head_type` 时触发 `AttributeError: 'CrocoConfig' object has no attribute 'head_type'`。这属于加载后属性检查错误；原作者源码/语法预检未覆盖该真实接口，不能把那次预检当实际加载验证。失败归档保留，不能从01目录读取或冒称存在4个新heads。

root另行冻结 V2：`FOUR_HISTORY_CONTRACT_V2.json` SHA `4a065747329578ac13340510d938ccd24a6a2e7614d77a32b3553fdaf212d50a`，runner SHA `71ca5a3002cef34c423a6729deb2d80e076795aa268eb5009f55bab97f75621c`，计划输出为 `execution_geometry_02`。本次只读了该合同与第一次失败 JSON，**未读取02输出或执行状态**；因此这里不声称 V2 已成功。后续 consumer 必须以 root 实际接受的 raw 批次及其文件SHA为准，预期候选路径更新为02；没有验收就不得代填heads身份。

01失败收据 SHA `43a5d8eea3f307ac7a2863a16c8926b281538b7b05ea8709b9c99a527a2007d3`。本勘误不更改 raw runner/合同，也不改变原稿关于同次四历史、3 star edges、固定相机/K、MST、局部梯度修复和科学范围的限制。新适配器的人工检查独立记录于 `GRADIENT_ADAPTER_NOTE.md`，不是02运行或真实优化证据。
