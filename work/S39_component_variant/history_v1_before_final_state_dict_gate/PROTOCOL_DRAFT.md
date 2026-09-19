# S39 DRAFT：具名 VAE 组件变体的资源与加载验收

准备开始 UTC：2026-09-07T03:40:24Z。当前只写源码、核小来源文件与标准库语法/AST；未下载权重、未导入科学库、未加载模型、未读真实图像/GT/预测数组、未跑生成。实际完成时点见 `preparation_receipt.json`。

固定名称：**VMem + stabilityai/sd-vae-ft-mse (declared VAE component variant)**。原 `stabilityai/stable-diffusion-2-1-base/vae` 的历史身份继续是 `UNKNOWN`。此版本不接受 `VERIFIED_ORIGINAL_VAE_IDENTITY`，不修改或绕过 S35 原件门；S35原文件、原wrapper与此前协议原件均保留。

## 身份和唯一组件差别

| 组件 | 完整字节数 | 预期SHA256 |
|---|---:|---|
| 原VMem参数 | 5056346672 | `675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4` |
| 原CUT3R 512 DPT参数 | 3173761006 | `45f7e98a0a64dbeb54901ae2b878cd8cd125f20a4497316483f0bd6f109f8103` |
| 原CLIP ViT-H-14/laion2b_s32b_b79k参数 | 3944517836 | `0084e75319a50ad85ef45377bad5bc38f2f58824459eb690048d51c9f8863be5` |
| 官方ft-mse/config.json | 547 | `92d3dfb746fca211a2c9e019e285f8597412211728dce3c5bcf4eda0f2d62e7e` |
| 官方ft-mse/diffusion_pytorch_model.safetensors | 334643276 | `a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815` |

VAE两文件来自同一官方仓库 `stabilityai/sd-vae-ft-mse`、固定revision `31f26fdeee1355a5c34592e401dd41e45d25a493`。配置用其自身`sample_size=256`，不混入社区配置、不改成768。依据为已有S36官方metadata/config与S38来源报告；上表VAE权重是服务端预期身份，**不是本轮下载后的本机验收**。root另行下载到专用目录，只放这两个文件；清单路径不自动推测、下载或替换。

原VMem构造仍发出原SD2.1 VAE的调用请求，但由明确标记的本地路由接至该官方ft-mse目录；原请求字符串不代表实际加载了原VAE。保留后验均值、0.18215缩放、chunk_size=1。加载后只检查属性：Diffusers0.32.2、latent_channels4、sample_size256、use_tiling=false、use_slicing=false、downsample8。属性检查不是encode/decode数值验证，兼容推断不是原件等价证明。设备/精度仍CPU/FP32；原VMem、CUT3R、CLIP的权重身份与原构造参数不变。

## 最小复用与验收顺序

1. `s39_variant_gate.py`只导入固定SHA的S35标准库辅助函数，沿用原三大权重身份、科学controls、stat/core SHA和原source domain。新variant schema明确区别于S35 schema。新增绑定两文件入口、本文、S38/S36来源报告及3个相关Diffusers源码。先验全组件路径/大小/固定身份、源码域、YAML/初图身份元数据与两份真正审查回执；任何缺件在大权重哈希和科学导入之前停止。
2. root先补实际路径、初图SHA，完成源码审阅及加载冻结。`source_review`必须为`PASS_S39_SOURCE_REVIEW`；`runtime_freeze`必须为`READY_TO_ATTEMPT_DECLARED_VARIANT_LOADING`。两回执都绑定`variant`与整个manifest除`review_receipts`外的规范JSON SHA（沿用S35 core函数）。不能在草案里填写假的PASS。本地full SHA匹配本身不需要假装恢复原VAE来源链。
3. `load_components.py`父进程先metadata check，再启动一次fresh原venv子进程。子进程做一次完整组件内容SHA，随后调用一次从S35工厂派生的构造函数。派生仅改1处gate import与4处日志/证据标签，反向还原AST须与固定原工厂全AST相同。构造、原VAE本地载入参数、严格state_dict/eval/CPU/FP32检查、原初图读取和576裁剪均复用。输入照片只作为原runtime准备，不提交给模型前向。
4. 禁止网络由复用工厂的offline环境与socket拒绝实现；没有额外重新编码、随机采样、模型前向、Navigator初始化/转向、MST、GA或生成调用。模型构造仍会正常分配和初始化参数，不能把“无前向”说成无张量计算。准备阶段没有执行这些构造。
5. 加载结束核VAE路径属性和全部参数载入回执，再重绑组件stat、源码与小输入SHA；不重复哈希GB权重。最终外控状态最多为`VARIANT_LOADING_RETURNED_PENDING_INDEPENDENT_REVIEW`。内部`PASS_DECLARED_VARIANT_COMPONENT_LOADING_ONLY`仅说明加载/属性检查完成；不等于codec已数值验收、生成通过、exact-original或新方法。

加载草案预算：CPU8、每0.5秒采样全进程树RSS，单次1800秒（包括完整哈希、加载和属性检查）、45GiB，磁盘持续至少10GiB。采用S35已有`kill_tree`处理整会话与已跟踪后代，记录实际signal/exit/survivors；不复制两批trace调度，也不允许超限后自动扩额/重试。此为未实测预算，不保证本机完成。载荷和外控各用新目录，失败/超限保留前缀。不同作者随后按实际风险验收即可，不重跑S35旧人工套件。

## 当前阻断项和精确接口

真正阻断此加载版本的是：原VMem/CLIP等任一完整本地文件缺失或SHA错误；ft-mse两个固定文件未齐；原初图身份未封；实际依赖/源码变化；源码及冻结回执尚无批准；或机器超出预算。**原SD2.1 VAE身份未知阻断exact-original结论，但不是这个已明确替换版本的伪装后门。** Draft本身也不能执行加载。root取得原件新证据后，可独立回到S35原件方案，不能把本变体结果追认为原版。

以下命令只写接口，尚未运行。将`$S39_MANIFEST_SHA`设置为root正式冻结后产生的64位SHA；路径含空格须保留引号。

```sh
S39_ROOT='/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling'
S39_MANIFEST="$S39_ROOT/work/S39_component_variant/manifest.json"
S39_MANIFEST_SHA='<正式冻结后SHA>'
"$S39_ROOT/.venv-cut3r/bin/python" -B "$S39_ROOT/work/S39_component_variant/s39_variant_gate.py" --manifest "$S39_MANIFEST" --manifest-sha256 "$S39_MANIFEST_SHA" --metadata-only --receipt "$S39_ROOT/work/S39_component_variant/metadata_check_01.json"
"$S39_ROOT/.venv-cut3r/bin/python" -B "$S39_ROOT/work/S39_component_variant/load_components.py" --manifest "$S39_MANIFEST" --manifest-sha256 "$S39_MANIFEST_SHA" --execution-directory "$S39_ROOT/work/S39_component_variant/loading_attempt_01"
```

不要先单独执行full gate再启动loading，否则会无意义地重读大权重；启动器的子进程已包含一次full gate。root也可单独调用full gate做资源验收，但这不生成可供跨进程信任的加载令牌，之后真正加载仍须其自身检查。`manifest_draft.json`是填充模板，不是正式manifest。

对proposal的作用：如果此具名变体随后实际加载并跑通原两批流程，可为真实视频基线和自然失败定位提供一个透明可复现的工程版本。它不能完成原版数值复现、新机制、跨场景验证或论文演示。后续任何方法比较必须共用同一个VAE组件版本，不能把替代VAE导致的变化算成方法收益。完整两批运行需另立协议，不能直接把当前加载入口改成生成成功。

实际应用本地Claude scientific-critical-thinking的证据分级与Claim Evaluation：把发布元数据→本地bytes核验→严格加载→codec数值→生成/消费者效果分开；不以同形状、同参数指纹候选或相近输出逆推历史来源。未调用Claude模型。
