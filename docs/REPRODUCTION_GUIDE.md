# 复现范围与新电脑设置

这是S0-S7的代码、冻结协议、已保存输出、报告和审查快照。包内不含原始TUM归档/图像、约2.99GB模型权重、完整CUT3R源码或Python环境。它支持先检查保存证据；重新推理需要另外准备这些公开资源。当前原电脑均已准备完成，无需重下。

## 先检查已有结果

在解包后的geometry-world-modeling目录中，按README创建Python 3.12环境并安装requirements-rgbd.txt。执行：

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/validate_rgbd_outputs.py
```

不传--data只核对已保存的S2/S3证据，明确不核原始图像。验证器会写指定实验副本的verification.json；要保留原文件，请先复制整个解包目录再执行。原含数据4544检查与离线4444检查不是同一范围。

S4和S5已保存原预测NPZ、测量对照NPZ和逐帧结果。独立核验源码/记录分别在results/S4_independent_audit、results/S5_independent_audit。历史审查脚本中记录的绝对路径是原执行位置，不要求在新电脑伪造该位置；实际搬迁验证见新包独立审查。包内Markdown导航已转为相对项目路径，历史JSON来源信息保持原样。

## 新机器重新运行真实数据与模型

以下是实际已使用入口的移植说明，不代表在一台全新的机器上完整测试了下载/安装。使用一个新的解包工作副本，保留另一份原始证据。进入项目根目录，下载TUM：

```bash
.venv/bin/python scripts/download_tum.py
```

建立独立模型环境（与RGB-D分析环境分开）：

```bash
python3.12 -m venv .venv-cut3r
.venv-cut3r/bin/python -m pip install -r results/CUT3R_readiness/requirements_frozen.txt
.venv-cut3r/bin/python -m pip check
```

获取固定官方源码；目录名CUT3R是新工作副本下的示例路径：

```bash
git clone https://github.com/CUT3R/CUT3R.git CUT3R
git -C CUT3R checkout 8bc15dc92a6d7fd92920b4ec81540d3dec7d3ecf
.venv-cut3r/bin/python scripts/cut3r_local_smoke.py --repo CUT3R --output results/new_machine_import_check
.venv-cut3r/bin/python scripts/download_cut3r.py
```

下载器保存续传段并核对归档，完整模型SHA256应为7a7d83e47f822e040980c8f5aff4c15aa94366d469d3ceae51fa30cc2f62327d。该SHA是本次完整下载的本地身份，并非发布者提供的签名。CUT3R官方代码/模型的非商业许可见vendor与官方仓库，TUM数据为CC BY 4.0。

先做本机兼容部件检查，输出用新目录：

```bash
.venv-cut3r/bin/python scripts/cut3r_rope_compat.py --repo CUT3R --output results/new_machine_rope_check
```

原机器检查包含CPU和MPS；其他平台是否可用由实际检查决定。S5使用CPU，没有要求CUDA。参数、输入、保存输出FP32，保留官方encoder内部FP16 RoPE。新平台依赖可获得性和算子行为需要实测，不能仅凭本次Mac成功宣称所有平台已验证。

新的S5入口显式接收源码、数据和权重路径，不依赖历史输入JSON中的绝对路径。相对路径与全部RGB/depth哈希会核对冻结清单：

```bash
.venv-cut3r/bin/python scripts/run_cut3r_sequence.py --repo CUT3R --data data/tum/rgbd_dataset_freiburg1_xyz --checkpoint data/cut3r/cut3r_224_linear_4.pth --signed-rope-check results/new_machine_rope_check/check.json --output results/rerun_S5_cpu
```

这个命令使用原逐块runner和三个独立CPU进程。每块24张RGB，保留官方递归状态更新，16GiB软RSS预算、每块900秒超时；任何失败保留。所有示例目录必须尚未存在。

在当前原环境重新评分已保存推理可用：

```bash
.venv/bin/python scripts/evaluate_cut3r_sequence.py --output results/rerun_S5_evaluation
.venv/bin/python scripts/plot_cut3r_sequence.py --result results/rerun_S5_evaluation
```

评分器对原实验适配器/核验报告/运行身份实施严格哈希守卫。新的机器部件核验会产生新时间和哈希，不能直接冒充原实验身份通过此守卫；应保留新运行并记录对应版本与审查，再给它单独的评测身份。不能修改旧metadata来蒙混过关。原始固定结果及其独立复算仍可在包内检查。

## 证据解释

S0/S1合成诊断、S2/S3相机测量、S4/S5学习几何、演示回放、完整视频生成是不同事项。36秒演示只回放已观察的72张照片和几何对照，没有生成新视角。S6完成学习几何到参考选择并通过3453独立检查，S7完成固定事件四臂与四读出并通过9827独立检查。完整VMem生成、跨场景验证与课程真实活动仍未完成。

## S6–S7新增证据与运行范围

S6原始选择、地图与测量在results/S6_memory_bridge，独立复算在results/S6_independent_audit。S7在results/S7_event_replay记录原观测(frame,u,v)、12条关联路径、24地图、96份渲染输出及384读出，results/S7_independent_audit独立重算匹配、地图、投票、排序/NMS与支持。全程仍只有12个不同查询，主测试8个；多种设置不增加独立样本数。

当前原电脑可用以下入口，输出必须是新目录：

```bash
.venv/bin/python scripts/run_s6_memory.py --output results/rerun_S6_memory
.venv/bin/python scripts/run_s7_replay.py --output results/rerun_S7_event_replay
```

S7入口固定读取原S6模型、测量及冻结清单，不能随意替换为另一模型运行身份；新场景或新设备要单独制定协议和输入清单。S6的外部--runs/--data在结束归档处仍有项目内relative_to约束；这些入口不等于任意目录或任意新机器都已通过。S7独立审查会核原始预测/GT等包外资源，缺失时报错；包内仍可在禁止网络和原项目读取的条件下复算保存的支持、重放事件、核验文件，但应明确这个离线范围。

分析图表入口analyze_s6_memory.py与analyze_s7_replay.py读取保存records，不训练或修改实验；默认写分析目录，若要保留包内逐字节证据请在解包副本中执行。原S5下载器忽略--help的问题已修入新快照；旧S5.zip不覆盖。冻结执行源码的任何修改都会被守卫拒绝，切勿为了重跑修改旧哈希或旧metadata。

补充范围说明：正常data/tum路径的groundtruth.txt未作为独立文件打入包内，但历史S6 experiment_source.zip内保留了轨迹副本及哈希。离线新包审查可以核该嵌套副本的哈希；如使用归档S5位姿复算投影，应明确没有解析该副本重新做GT插值。不要写成包内完全不存在轨迹信息。
