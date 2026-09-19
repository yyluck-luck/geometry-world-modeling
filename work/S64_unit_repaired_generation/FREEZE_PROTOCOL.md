# S64 沿用的冻结与启动合同

此工具保留 V9 已有效的 prepare、attach、authorization 和监督实现；仅更新实际来源 SHA、新输出、新科学 row 和明确单位变体。参数名、行政 schema/status 兼容原工具，不新增流程。候选来源含新 unit_renderer_hook.py 和固定外部 S61 adapter，实际完整集合由 generation_gate.required_sources() 重建；不能只按旧219项验证。

作者交付最终0444源码后，由两个不同作者核本次差异。root 随后执行唯一 prepare：检查固定代码/父证据、seed44 YAML、原 JPEG 完整 SHA（不解码）、资源路径与目录新鲜性；通过固定外部 sentinel、staging 和原 rename-exclusive 发布 `freeze_attempt_01/manifest_core.json` 与 `receipt.json`，不创建执行或授权。失败尝试保留，不能在已消费目录重试。

core 使用新 `row=C2_UNIT_REPAIRED_S64`、完整 exact_retrieval_variant、原 ft-mse variant、原组件/输入/控制和独立 S64 输出；仅 review_receipts 排除在 canonical core hash 外。因此新增科学差异和 wrapper/adapter 身份都被 core hash 绑定。原输入/seed之外只有明确的 renderer 单位行为差异，其余科学控制保持等式核验。

两份 core review 沿用 `schema=s47-c2-generation-core-review-v1`，分别为 `PASS_S47_C2_GENERATION_SOURCE_REVIEW` 和 `READY_TO_ATTEMPT_S47_C2_BASELINE_GENERATION`；两者必须 `row=C2_UNIT_REPAIRED_S64`，保留原 ft-mse variant，并绑定同一 core path/file SHA/canonical SHA/prepare receipt SHA，独立 reviewer_role、author_role=/root、executed=false、model_or_scientific_imports=0、pixels_decoded=0、blocking_findings=[]。状态中的 C2/BASELINE 是兼容标签，不能据此回填原 cohort。

attach 重核成功 prepare 和两 review，保留原固定非PASS preflight及发布方式，仅增加 review_receipts，验证 core hash 不变，输出原合同的 manifest.json、metadata_gate.json、receipt.json 三个只读成功文件。再作两份不同作者的最终 review：`FINAL_ATTACHMENT_REVIEW.json`/`LAUNCH_READINESS_REVIEW.json`，沿用 `s47-c2-final-launch-review-v1` 及原 status，绑定最终 manifest、core file、canonical core、prepare receipt、attach receipt、metadata gate 六个 SHA。时间必须晚于 attachment，零执行/模型/像素/生成，空 blockers；manifest/core 已包含新单位变体。

create_launch_authorization 复核这六项和两review的精确字节身份，沿用唯一 `launch_authorization_attempt_01` 和只读 `launch_authorization_01.json`；prepare/attach 不产生授权。新 row 和独立 output 均参与授权，旧 V9 票没有效力。launcher 保留一次公共入口、私有worker/watchdog、原资源限额和三方终态；root 必须保持外部 live exec，取得实际退出并检查完整终态及无 fallback failure，单独 commit 不算成功。

新 hook 额外单位票从真实调用生成；正常两批只要求一次。worker 和 supervisor terminal 均核并绑定实际票 SHA/内容/variant；缺票、多票、失败票或两层绑定不同，不得返回完整成功。它是已有终态的必要科学输出字段，不是另加授权阶段。准备、核来源和安装不冒充执行；完整生成结果另行核读回/九帧评分/图像QA，原失败及新变体身份始终分开。
