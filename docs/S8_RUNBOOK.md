# S8已全部完成：不要重跑成功实验

当前权威结果docs/S8_RESULTS.md；独立结果S8_INDEPENDENT_AUDIT.md；模型/重放分别results/S8_cut3r_cpu_v2与S8_event_replay_v2，均completed；独立results/S8_results_audit_v2一次14253检查passed。照片、五页新PDF、384CSV/96几何与证据包已交付。先读RESEARCH_MEMORY/最新日志；下方早期“未完成”是历史操作准备，不是当前状态。接续应做证据包隔离可复核性检查，再具体创新方向检验；不要重复下载权重/完整fr2或重跑S4–S8。

---

# S8 V2当前操作更新

原V1设计与首次失败保留。下载已03:00完成，无需重下。取样因重复GT时间停止，V2方案见S8_EXTERNAL_SCENE_PROTOCOL_V2.md及S8_TIMESTAMP_AMENDMENT_REVIEW.md。先完成新prepare_tum_timestamp_derivative.py实施/fixture/独立审查，再创建S8_DESIGN_FREEZE_V2.json绑定V2协议、新script、原GT SHA和设计证据，方可生成独立副本。当前还未实际生成V2数据或看新图。

V2运行的新路径（不覆盖V1失败）如下：
- 派生父目录：data/tum/fr2_desk_timestamp_guard；其下rgbd_dataset_freiburg2_desk与derivation_metadata.json。
- 设计：docs/S8_EXTERNAL_SCENE_PROTOCOL_V2.md、docs/S8_DESIGN_FREEZE_V2.json。
- 输入：data/cut3r/S8_fr2desk_inputs_v2/S8_inputs.json及sampling_metadata.json。
- 独立派生审查：results/S8_derivation_audit；必须核所有源与新文件SHA、原GT减声明集合的确切bytes、屏障及冻结，不能只信生产metadata。
- 独立采样：results/S8_sampling_audit_v2。
- 照片QA：results/S8_rgb_qa_v2，照片工作区outputs/独立场景验证/真实照片_72张。
- 执行冻结：docs/S8_EXECUTION_FREEZE_V2.json（含真实frozen_utc、全部执行与审计源码、新manifest、派生metadata/审查/设计冻结、RGBQA和单独视觉回执SHA）。
- 模型：results/S8_cut3r_cpu_v2；重放：results/S8_event_replay_v2；独立结果审查：results/S8_results_audit_v2；分析：results/S8_analysis_v2。

下方是此前V1接续说明的历史副本。运行时以本节V2路径替代；原模型/记忆/采样/评分设置和入口不改。若任何实际目录已存在，先检查成功/失败和进程，成功不重跑、失败不覆盖。

---

# S8接续操作：先读主记忆与最新日志

设计已于北京时间2026-09-06 02:04:06.362327冻结，docs/S8_DESIGN_FREEZE.json绑定协议SHA5b6563643d4deb69dd7f66789ebf0f0620666cac372858831aa96fd376186df6。不能编辑已冻结协议或取样源码来凑够窗口。完整执行源/输入冻结尚未创建。

## 当前下载

根任务已运行scripts/download_tum_sequence.py，首轮session1705已于02:11:10因一个分块6次超时失败；66个已核验分块保留。第二轮工具进程session75841，使用--workers 2，日志在工作区work/s8_fr2_download_workers2.log；原work/s8_fr2_download.log保留。下载器以文件锁防重复，数据主状态data/tum/fr2_desk_download/download_manifest.json，历史runs/request_attempts保留。先查实际进程与status，正在下载则不要重复启动。只有status=complete且gzip/tar核验记录成功，才进入取样。若failed，先读失败与已有chunks，允许同一命令按固定参数重新核缓存并续传，不能变ETag/大小混拼。

解压预定根为data/tum/fr2_desk_download/extracted/rgbd_dataset_freiburg2_desk；包为同下载目录下rgbd_dataset_freiburg2_desk.tgz。尚未证明有足够窗口，不提前说72张新图已完成实验。

## 完整包之后

1. 核设计冻结中源SHA仍相同；分析环境.venv/bin/python运行prepare_s8_inputs.py，参数--data/--protocol/--design-freeze/--archive/--output，新输出data/cut3r/S8_fr2desk_inputs。输出S8_inputs.json与sampling_metadata.json；程序不解码图片或GT位姿。少于3窗时停止并保留，不改采样。
2. 先用.venv/bin/python scripts/verify_s8_sampling.py，传--manifest/--protocol/--design-freeze/--data、--sampling=data/cut3r/S8_fr2desk_inputs/sampling_metadata.json、--output=新results/S8_sampling_audit。它用独立数学仅解析GT时间列，核所有接受窗口/首中末/每图时间和SHA，不解码图片或GT位姿；须status=passed。再运行scripts/qa_s8_rgb.py，传同manifest/protocol/design-freeze/data、--output=新results/S8_rgb_qa、--photo-output=工作区outputs/独立场景验证/真实照片_72张；两个输出必须全新。该程序先封存清单，后核72张PNG/RGB/640×480及CRC/full decode，按原字节复制全部照片，另生成3张联系表。须metadata completed/72和原图SHA通过；根任务逐张查看3张联系表并另存视觉QA记录，不能将自动生成当作人工查看。此阶段不解码depth、不按照片换样。
3. 创建新的docs/S8_EXECUTION_FREEZE.json：protocol_sha256、manifest_sha256、execution_source_sha256至少run_s8_replay.REQUIRED_SOURCES的20项，另加入prepare_s8_inputs/verify_s8_sampling/qa_s8_rgb/analyze_s8_results和实际审计源；measurement_file_sha256绑定新GT/rgb.txt/depth.txt；记录真实时间、设计冻结SHA和QA证据。审计脚本若仍在开发，先完成再冻结，不把源码冻结补记成更早时间。
4. .venv-cut3r/bin/python运行scripts/run_s8_sequence.py，固定repo=工作区work/cut3r-local、data=新解包根、checkpoint=data/cut3r/cut3r_224_linear_4.pth、manifest=新S8_inputs、protocol=S8新协议、signed-rope-check=results/CUT3R_signed_rope_compat/check.json（已从S6 metadata实际核得，SHA84a30132c2cfb9c31720771b76bb068ad6edf7f9ea77cd75d39c4b3512f4fc78），output=新results/S8_cut3r_cpu。先从旧S6/runner记录查真实check路径，不猜。不下载权重、不重跑旧S4–S7。
5. 只有controller complete/ok/504通过，才用.venv/bin/python运行scripts/run_s8_replay.py，传相同manifest/protocol/freeze/data、runs=新S8_cut3r_cpu、output=新results/S8_event_replay。代码自己全选择封存后测量评分。所有失败新目录保存，成功不能写覆盖失败结果。
6. 独立审计scripts/verify_s8_results.py已完成，SHA6ae1ee6fa5373a378cacb53babb1475a12b669419d8ebe96529aab079ba72878，4组准备检查通过及静态同行复核。说明docs/S8_AUDIT_PREPARATION.md，根任务可直接执行；新run complete后才允许它从新PNG/GT重算。固定原容差1e-9/1e-10；闭GT端点用新独立wrapper，旧verify_s6_scores不改。不要把未跑检查标通过。
7. scripts/analyze_s8_results.py --results 新S8结果 --output 新results/S8_analysis，输出全部384CSV、逐块/全12查询支持与预定对比、S7具体符号模式/固定抵消判据及2图。与独立汇总逐值核对后，写中文结果和新PDF，逐页视觉QA，再同步outputs。旧S7 PDF/ZIP/运行前假设文件维持历史快照。

## 报告时必须说清

一个新增物理环境、同类另一实体Kinect、12个相关查询、384读出条件。没有跨数据集验证，也未核模型训练是否接触TUM。一般条件效应存在与S7具体符号/抵消模式重复分开报告。无变化/反号/下降全部保留。参考支持及几何代理不是生成视频质量；完整VMem与课程真实活动仍未完成。
