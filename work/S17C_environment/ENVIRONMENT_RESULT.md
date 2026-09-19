# S17C 隔离几何环境：实际安装与导入结果

记录时间 UTC 2026-09-06 11:26；本地 Asia/Shanghai 19:26。

**PASS_IMPORT_ONLY_NO_MODEL。** 实际安装和几何栈导入已完成；没有实例化 CUT3R/
VMem 模型、读取权重、打开真实图片、运行几何优化或生成视频。

本报告更新 `../S17C_interface_preparation/INTERFACE_PLAN.md` 的依赖准备部分：
其初稿是源码与元数据计划，本报告是实际结果；真实运行合同应绑定最终回执。

## 最终交接路径

| 角色 | 文件或目录 |
|---|---|
| 隔离安装目录 | `work/S17C_environment/site-packages` |
| 环境汇总回执 | `work/S17C_environment/environment_ready.json` |
| 成功导入回执 | `work/S17C_environment/import_smoke_v2.json` |
| 实装逐文件清单 | `work/S17C_environment/overlay_files.json` |
| 原始源码与3处差异 | `work/S17C_interface_preparation/source_plan.json` |
| 实际隔离源码 | `work/S17C_interface_preparation/isolated_vmem_source` |
| 初始依赖与增补 | `work/S17C_interface_preparation/dependency_plan.json`、`dependency_plan_v2.json` |
| 两批固定wheel身份 | 同准备目录 `overlay_wheel_plan.json`、`overlay_wheel_addendum.json` |

`environment_ready.json` SHA-256：
`a3247a14945d224d291b1aa0d3d32a7efc593f897b6b6289fdabd3d3f14783ca`。

`import_smoke_v2.json` SHA-256：
`86ec27d37f040c01358a6e7b3621c9ccc821f91add36aaed27072fa096672c24`。

完整环境包含 **34 个新增 wheel**、**5,523 个实装非 bytecode 文件**。
`overlay_files.json` 每个条目是绝对路径、字节数与 SHA；未来 manifest 的
`overlay_files` 可由其 `files.keys()` 得到，不能只绑定依赖包名称。

## 实际获取、安装和保留失败

34 个不同 wheel 的实际完整文件总量 **45,573,119 字节**，全部逐个匹配冻结
PyPI文件的 SHA-256。wheel 请求累计 **43 次**，实际累计响应 **49,783,798
字节**，包含初始超时造成的重复/partial字节。这些数字只统计 wheel HTTP
请求；文献/包元数据查询另有准备目录的查询回执。

安装完成耗时自首轮开始 **478.550872 秒**，在冻结的 600 秒、100 MiB 响应、
60 次 wheel 请求界内。全部安装只写本目录的 `site-packages`，使用离线
wheelhouse、`--no-index --no-deps --no-compile --require-hashes`，没有让 pip
修改或升级旧 venv 的 torch/NumPy。

首轮完整 wheel 请求25秒限制太短：evo成功，matplotlib经历SSL失败与两次超时。
`install_receipt.json` 保留该真实失败；没有覆盖原失败合同。之后 root 授权的
`continuation_contract.json` 保留已完成wheel与最长partial，以固定URL续传，
要求206和最终完整SHA；新合同仍累计先前请求/字节/时间。前22包成功记录在
`continuation_receipt.json`。

第一次实际几何导入在 18.757179 秒后失败，原因是我此前的静态依赖清单漏读了
`dust3r/viz.py` 文件后半部：第844行仍在顶层导入 `viser`，第1056行顶层导入
`sklearn.decomposition.PCA`。`visualize=False` 不会跳过这些模块导入。
`import_smoke.json` 原样保留失败及 traceback；未用假模块或源码改写绕过它。

按 root 已授予的“真实缺项增补”授权，新增固定12wheel共16,059,230字节，
记录在 `addendum_contract.json`、`addendum_receipt.json`。新依赖是
viser 1.1.0、scikit-learn 1.9.0、msgspec 0.21.1、rich 14.3.4、trimesh 4.12.2、
websockets 16.1.1、joblib 1.6.0、narwhals 2.25.0、threadpoolctl 3.6.0、
markdown-it-py 4.2.0、cloudpickle 3.1.2、mdurl 0.1.2。

初次仅取最新版元数据时，rich15/trimesh5/websockets17违反 viser 的明确上界；
这一冲突保存在 `dependency_plan_v2.conflicts.json`。之后按上界选择对应最新
相容稳定版本并冻结准确wheel，才执行安装。基础NumPy1.26.4等版本没有改变。
源依据为 [viser发布元数据](https://pypi.org/pypi/viser/1.1.0/json) 和
[scikit-learn发布元数据](https://pypi.org/pypi/scikit-learn/1.9.0/json)，完整
传递依赖边与原始元数据SHA在准备目录。没有引入 dev/examples/GUI/ROS extras。

## 导入烟检实际证据

成功测试 UTC **11:24:54.275197–11:25:52.581005**，耗时 **58.305821 秒**，
**156 项检查 PASS**，状态明确为 `PASS_IMPORT_ONLY_NO_MODEL`。

只导入并核验原始 callable：ARCroco3DStereo类、原run_inference_from_pil、
prepare_input_from_pil、prepare_output、inference、global_aligner、
global_alignment_iter、clean_pointcloud、fast_pnp。没有调用模型构造器或这些
前向/优化函数。烟检期间 torch.load、PIL.Image.open 和网络connect被显式
拒绝；实际尝试次数均为0。

36 个加载的几何模块，包括 `dust3r.*`、`src.dust3r.*`、`models.*`、
`croco.*`、`cloud_opt.*`，均解析到当前隔离 `extern/CUT3R` 下并保存了绝对路径
与SHA；同一源码的包别名未被隐藏。原wrapper与冻结作者源码逐字节相同。
CPU RoPE候选按预期导入；未加载modeling.pipeline、diffusers或open_clip。

此前3处源码差异仍限于signed CPU RoPE的两个文件，以及embedded model.py
显式weights_only=True。这个烟检没有实际执行checkpoint安全加载；safe_globals/
完整checkpoint身份和真实前向仍由后续S17C模型运行合同验证。

Matplotlib缓存只写本目录 `matplotlib-config`；首轮创建缓存不是模型实验。
原始代码出现的CUDA autocast弃用警告来自enabled=False装饰器，导入成功，
没有因此静默重写优化数学或声称验证了CUDA。

## 原环境保持情况与限制

`.venv-cut3r` 与 `.venv` 在安装前、安装后以及成功导入后均检查一致：
全部非bytecode文件的路径/大小/mtime/符号链接状态，以及发行包METADATA/
RECORD和bin可执行文件字节SHA相同。比对排除 `.pyc/__pycache__`，不声称
对旧环境全部数GB模型库源文件重新做过字节哈希。

成功导入回执逐项记录了34新增包和复用包的版本/发行元数据位置。
核心实际 torch2.7.0、torchvision0.22.0、NumPy1.26.4、SciPy1.16.2、
transformers4.48.3、accelerate1.4.0从原 `.venv-cut3r` 解析；新增包从新overlay
解析。标准依赖存在和几何栈导入成功不等于所有34包的每个可选功能都已测试。

本阶段没有真实RGB/深度/轨迹/GT读取，也没有权重下载或模型初始化，故不能
产生两图建图、512 DPT输出、优化质量或视频生成结论。下一步是由另一agent
完成真实observer runner和独立前审，root以本最终环境回执及源/输入身份冻结
S17C manifest，在S17B释放资源后执行受600秒/32GiB外监控的真实两图实验。
