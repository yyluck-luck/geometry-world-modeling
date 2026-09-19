# S95 数据访问与 reference/rescan 语义审查

**记录时间：** 2026-09-12（Asia/Shanghai）  
**任务边界：** 只审查公开官方页面、仓库源码和论文；没有提交 Terms 表单，没有提交个人信息，没有下载新的数据媒体。

## 结论

此前将“3RScan.v2.zip 的示例包也一定需要 Terms 注册”写成确定事实，证据不足，已纠正为：**完整数据访问明确要求填写 Terms of Use；官方仓库的 `setup.sh` 又把 `3RScan.v2.zip` 标为 example data，并直接给出公开 URL。当前不能从官方文字确定该公开示例包是否是 Terms 规则的例外。** 因而 Gate 0 的数据资格仍未通过，但阻断原因应写成“完整帧正文、许可适用范围和本地逐帧资格尚未确认”，不能写成已经证明示例包必然需要注册。

## 一手来源证据

### 1. 官方 3RScan 仓库的下载脚本

来源：<https://raw.githubusercontent.com/WaldJohannaU/3RScan/master/setup.sh>

`setup.sh` 在第 6 行附近注释为 `download example data`，随后以公开地址下载 `3RScan.v2.zip`，再解压到 `data/3RScan`。这说明官方代码至少曾把该 ZIP 当作示例数据，并提供了无需脚本内表单交互的下载路径。该脚本本身没有说明数据许可，也没有证明当前服务器策略仍允许无条件使用。

### 2. 官方项目页与文档的总规则

来源：<https://waldjohannau.github.io/RIO/>；<https://vmnavab26.in.tum.de/3RScan/documentation.php>

项目页写明下载 3RScan 数据需要填写 `3RScan Terms of Use` 表单。文档页同样说明下载数据应填写该表单。因此，对完整数据集或当前受控下载流程，Terms 是明确要求。两页没有明确写出 `3RScan.v2.zip` 这个示例 ZIP 是否豁免。

### 3. 官方 FAQ 的 reference/rescan 定义

来源：<https://raw.githubusercontent.com/WaldJohannaU/3RScan/master/FAQ.md>

FAQ 说明每个室内场景包含多个 scan，其中一个被选为 reference/initial scan，通常是最完整或第一 个 scan；其余为 rescans，标注相对于 reference。官方 README/FAQ 因而支持“reference 是初始扫描、rescan 是后续重访”的数据语义，但没有给出每个 rescan 的精确采集时间戳，也没有保证它们形成均匀的时间序列。

### 4. 官方 RIO 论文

来源：<https://arxiv.org/pdf/1908.06109.pdf>

论文将任务描述为：从一个 RGB-D scan 中的对象，估计同一环境中另一个、在较晚时间取得的 scan 中对应对象的 6DoF 位姿。这个定义支持把 reference→rescan 作为“重访/变化条件下的目标”，但不能直接等价为连续视频中的下一帧预测。

### 5. 代码许可与数据许可的区分

来源：<https://github.com/WaldJohannaU/3RScan/blob/master/LICENSE>

仓库 LICENSE 是 MIT，针对仓库中的软件代码。它没有在该文件中授权数据集媒体；项目页和文档另行要求 Terms。因此不能用“代码 MIT”推出“数据可以任意下载或再分发”。这只是证据边界说明，不构成法律意见。

## 对研究协议的影响

1. **数据访问状态：** `CONDITIONAL / GATE0_NOT_PASSED` 仍然正确，因为本地没有任何完整解压的 RGB、16-bit depth、pose 和 `_info.txt` 正文，也没有完成帧级配对、K、单位和有效像素核验。
2. **阻断措辞：** 使用“完整帧级资格与适用许可未确认”，不要使用“公开 sample 已证明必须注册”。
3. **时间语义：** 可把 reference→rescan 定义为“初始扫描到较晚重访扫描”的候选未来目标；不能称为连续视频未来帧，也不能假设多个 rescans 的精确时间顺序，除非完整 metadata 或原始采集记录提供证据。
4. **下一步：** 若用户自行完成官方 Terms 流程，或确认公开示例包的合法适用范围，只取一个 train reference/rescan 组，保存来源和许可回执，然后才进行 S95 帧级 Gate 0。agent 不代填表、不提交个人信息。

## 尚未解决的问题

- `3RScan.v2.zip` 的“example data”是否被 Terms 页面明确豁免；公开页面之间没有给出清晰例外条款。
- 示例 ZIP 当前能否稳定、完整地下载并合法用于本项目。
- 完整样本中的文件名同步、RGB/depth 尺寸、`_info.txt` 内参、depth 单位、pose 缺失率和 rescan 采集时间信息。
- reference→rescan 是否足以支持 proposal 的“未来世界状态预测”，还是应把论文问题明确改写为“长期重访/场景变化下的几何一致性”。

**状态：** 本文件是来源审查和语义纠正，不是 Gate 0 通过，也不是方法实验结果。
