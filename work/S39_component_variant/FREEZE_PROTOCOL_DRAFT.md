# S39 资源清单冻结工具：准备稿

准备开始 UTC：2026-09-07T04:08:39Z。仅编写与标准库语法审查；本作者没有运行冻结、读取权重/照片字节、加载模型或创建审查批准。root通报的下载状态不是本工具已验收的结果。

`freeze_manifest.py`固定复用v2 gate、原draft、214项源码身份和全部原设置，仅新增本目录文件。原S35、S39 v2 gate/loader/protocol/draft均不修改。具名版本仍为 `VMem + stabilityai/sd-vae-ft-mse`；原SD2.1 VAE来源仍UNKNOWN。新工具不是原版复现或创新。

## 两个步骤

1. `prepare`只接受显式VMem和CLIP绝对路径、ft-mse专用目录；CUT路径来自固定draft。先核五组件完整大小、全部小文件存在、固定YAML、运行环境路径及输出新目录，然后才读任何大组件内容。缺件保留NOT_READY回执，不按部分下载补齐或替换。每组件一次流式SHA256，匹配固定已发布身份；用打开文件描述符和路径的size/mtime/ctime/device/inode在读取前后核变动，每项完成立即追加/fsync证据。固定changi原路径全字节哈希，不解码像素、不构造新照片。源码、YAML和两份新增工具来源也保存SHA。
2. 全部通过后写只读、不可覆写的`manifest_core.json`。`status`使用原gate要求的FROZEN值，保证批准后不再改core；`review_receipts`保持空，所以该core**不能通过原gate或启动模型**。回执状态是`CORE_FROZEN_AWAITING_REAL_REVIEWS`。两个外部作者实际写审查回执后，`attach-reviews`只添加其路径/SHA，核两者status、variant和`core_sha256`，保证除review_receipts外的规范JSON完全不变，生成另一个新目录的只读`manifest.json`，再调用原metadata gate。此工具不编写、代签或判断审查作者身份；root安排不同作者真正阅读并批准。

整个core SHA沿原`core_sha256`函数，排除review_receipts以免循环；core文件自身SHA与最终manifest文件SHA是另外两个身份，命令参数不能混用。新增工具SHA放在core的`freeze_preparation.tool_sources`，不改变原gate要求完全相等的214项`source_identities`域。批准者需要将这些额外工具一起审查。只读权限是防误写，不是不可修改的安全证明；之后每一步仍查SHA。

## 签名复用的准确范围

冻结保存五组件真实完整内容SHA，以及size/mtime/ctime/device/inode。attach只查这些签名没有变化并核小文件，不重读GB权重；若变化则失败，保留记录。该签名用于证明当前冻结链的文件一致性，不是密码学签名，也不允许越过runtime完整内容门。

**现有worker仍在其自身进程执行一次完整五组件SHA，然后才构造原模型。** 本轮没有为了节省第二次完整读盘而改gate/loader，或信任跨进程旧stat当内容证明。prepare与worker是两个不同时点的全量核验，回执必须如实计这两次；不得声称从下载到加载总共只读一次。未来若需要将它们合并成同一进程的即时验收/加载，必须另审接口与授权生命周期，本工具不做此扩展。

## 命令（尚未执行）

所有下载退出且五文件齐全后，root用实际完整路径替换示例变量。每次`--out`必须新建，失败不能覆写。模板仍固定v2 SHA；原draft变动时须另存修订，而不是静默吸收。

```sh
S39_ROOT='/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling'
S39_TOOL="$S39_ROOT/work/S39_component_variant/freeze_manifest.py"
S39_VMEM='<完整原VMem文件绝对路径>'
S39_CLIP='<完整原CLIP文件绝对路径>'
python3 -B "$S39_TOOL" prepare --vmem "$S39_VMEM" --clip "$S39_CLIP" --vae-directory "$S39_ROOT/data/vae_official_ft_mse" --out "$S39_ROOT/work/S39_component_variant/freeze_attempt_01"
```

读取实际prepare receipt的`core_sha256`交给两名真正审查者；他们的回执必须分别为`PASS_S39_SOURCE_REVIEW`和`READY_TO_ATTEMPT_DECLARED_VARIANT_LOADING`，都含同一core_sha256与完整variant对象。下列SHA必须来自实际文件，不可预填假的PASS。

```sh
python3 -B "$S39_TOOL" attach-reviews --core "$S39_ROOT/work/S39_component_variant/freeze_attempt_01/manifest_core.json" --core-sha256 '<core文件实际SHA>' --source-review '<源码审查实际JSON绝对路径>' --source-review-sha256 '<实际SHA>' --runtime-freeze '<冻结审查实际JSON绝对路径>' --runtime-freeze-sha256 '<实际SHA>' --out "$S39_ROOT/work/S39_component_variant/review_attachment_01"
```

两步实际成功后，root取第二个receipt中的`manifest_path`和`manifest_sha256`，按既有PROTOCOL_DRAFT的原loading命令启动。仍限CPU8、1800秒、45GiB、磁盘至少10GiB，工厂/加载记录与不同作者事后验收门均保留。工具只hash本地bytes，内存按8MiB块，不下载/导入科学库/运行任何模型；冻结耗时单独记录，不算模型预算消耗或科学实验。

## 当前未完成

本稿交付时尚未执行prepare/attach或模型加载；VMem/CLIP最终本地身份由root正在执行的下载与后续冻结确定。已有ft-mse下载通过是root报告，未由本次工具重复验收。独立源码审阅、正式core内容核、两份实际批准和加载仍待进行。失败目录、已完成hash行与异常回执全部保留，不重试、不自动扩预算。

沿用本地Claude科学批判skill的证据边界：来源预期值、实际文件SHA、metadata通过、加载返回、codec数值与视频质量分开陈述；本步骤不产生后四类结果。
