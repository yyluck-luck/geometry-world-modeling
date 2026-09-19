# S86 独立生成入口前审

**GO：允许 root 按以下精确合同启动一次“两条完整链＋两条派生对照”；未发现实质阻断。** 这是源审通过，实际生成、后验数值复核和评分尚未发生。

审查 UTC：2026-09-10T21:29:15.993650+00:00

## 精确身份

- `generate_with_fixed_warp.py`：`98c5f2f409c88817851f1b3ff74f987879d6274c27b36995bbb69bb76f1bdbd9`（21011 B）。
- `supervise_generation.py`：`d4ad436f30cd204488165812c03e5358d38bde1163e8d30485457d3bf5038d44`（4933 B）。
- `CONTRACT.json`：`954c4353745280d5d3f48ac9db124b8a23aa877e1c59e9ecdd13f399416e844f`（8083 B）。
- `sampler_hooks.py`：`2521dac2e07d0809eaecf23c37e6f41a5d157435ef7e5d010eec8ce840933ae4`（9502 B）。
- `INDEPENDENT_HOOK_SOURCE_REVIEW.json`：`0fa48b6fb5c91b70dbc517b15ad931ac62fc10dd9e90a457d446fe0feb06c217`（5152 B）。

## 实际核查

- **source_and_inherited_interface**：Full353-line runner,99-line supervisor,206-line contract read; invoked S70 helpers load_code/load_models/read_conditions/model_snapshot/RNG/save functions read, original AutoEncoder full read. Six inherited Python-source hashes and all source/acceptance metadata bindings match.
- **fixed_input_identity**：Only fixedS69 geometry condition is decoded; order19/18/13/12/20/21/22/23 and input maskTTTTFFFF checked. Four acceptedS85 whole archive identities in20..23 order, only warp_rgb/mask decoded. Actual target reference path is metadata only and never opened by generation.
- **fixed_components_runtime**：Inherited original VMem weights and declared ft-mse VAE are hash-bound and loaded once, strict weight keys; offline helper blocks network. Original constructors/do_sample/Euler/CFG/quantizer and CPUFP32/8threads/50steps/576 preserved. Supervisor uses un-resolved scientific venv path.
- **encoding_and_masks**：One shared VAE encode call with chunk1 across4target warpRGB*2-1, original deterministic mean*.18215. Black holes encode-1; avg_pool8x8 support fraction, history prefix zero. Exact same tensors and final.25 used by Gguide/Gterminal; no reference-derived tuning.
- **two_chains_and_two_derived**：Only G0 and Gguide invoke original do_sample/sampler. Gpaste derivesfrom G0 rawRGB, original branch conversion/clamp then fixed image-mask*.25 blend; Gterminal derivesfrom G0 actual last state and original Euler arithmetic then one full8 VAE decode, no denoiser or fresh random draw.
- **actual_random_stream**：Common Python/NumPy/Torch RNG captured after shared encode and restored before each complete chain. Initialnoise captured before original in-place scaling, actual entry/50steps/terminal RNG identities recorded and compared. Callback verifies its full RNG signature unchanged; final derivations check RNG unchanged.
- **post_cfg_and_history_protection**：Hooks delegate raw originalCFG first then fuse. Callback checks G0 raw is used and identical descriptors; both modes verify current-step protected history/zero-support clean bytes. It performs only metadata reads, hashing, NumPy serialization and no in-place tensor mutation or RNG call beyond capture.
- **complete_saved_replay_inputs**：All50Gguide raw_clean/used_clean pairs saved create-only, about66MB raw payload. Full8 final latents,4raw+emittedtargets, actual quantizer branches,7last-step tensors and metadata saved for each chain. Zero-strength replay must exactly reproduceG0 saved latents before derived controls. Every50step count and hook count checked.
- **model_state_and_failure**：Actual model value/identity/mode snapshots before/after encode and each arm, eval/frozen enforced. Exception paths retain chain/derived/root errors, hook rows and partial last capture; unrun arms explicit. Abrupt missing receipt is external supervisor failure, not fabricated completion.
- **external_limits**：One fresh worker and new execution/supervision directories, no retry. Supervisor bindscontract/source/selfSHA; monitors process-treeRSS,disk,total/armtime every5s.5400s total/2400s perarm/45GiB RSS/10GiB free, sends actual loggedSIGTERM then after20sSIGKILL if needed. SourceSIGTERM handler raises into error preservation.
- **frozen_scoring_boundary**：Scoringcontract retains full4 emittedRGB MSE with995328scalar/frame and3981312total, exactint64 SSE direction; guide-terminal primary and guide-G0/paste always. Fixedsupport/hole secondary, emptyNA, incompletearm notaveragedaway. Knownreference reuse only after generation sealed; no metric computation inside runner.

## 审查范围和结论边界

全文读取353行生成器、99行监督器、206行合同及所调用继承助手；对Python源作AST解析并核元数据身份。没有启动任何入口、重跑人工批次、读取权重/NPZ/参考RGB或导入模型。实际输入数组与运行软件版本仍由冻结入口在运行中检查，不能把本前审说成已验证真实输出。

没有为达到通过而要求新增完整G0或修改科学阈值。后验利用50步实际raw/used、两条末步保存量、发图原始值、RNG/模型身份和完整输出重演即可；真实VAE网络不另作一遍完整解码来冒称独立实现。

错误的参考几何仍可被正确执行。预测mask的平均覆盖不是已学置信度；RGB与latent同λ不等于相同RGB干预强度；50步累积剂量与VAE非局部作用仍是竞争解释。Gguide胜Gterminal也仅支持这个固定探索设置下较早干预及其传播的附加作用，若仍输G0不能报总体改善。四个相关目标和一次共同噪声不是跨场景或统计确认。

资源为5秒采样监督与实际信号终止，非操作系统硬内存限额。失败、部分产物、真实发送的信号和退出码必须保留；不能因源审GO或人工26项通过预写实际运行成功。下一步只按冻结版本唯一启动，完整运行后的评分与接受另行据实处理。
