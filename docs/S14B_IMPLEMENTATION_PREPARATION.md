# S14B测量器实现准备

状态：程序与人工反例已完成；等待不同作者最终执行前审查和根任务冻结。此文不是实际测量结果。

## 实际工作与边界

准备记录时点：2026-09-06T05:47:42.056600+00:00（UTC）；人工检查精确起止见回执。使用现有 .venv Python 3.12.14 / NumPy 2.3.5，没有安装依赖、调用Claude模型、解码真实NPZ或运行真实测量。仅为核结构解码 S7/block0 的 A0_events.json 与 A0P0_sources.json 各一份；其余输入格式来自旧inventory。原record_path/replay、observations和保存代码已静态核对。

本地Claude scientific-critical-thinking/SKILL.md用于测量有效性与混杂检查。W/B/A/D只是固定筛选关联内的预测分散；不能称真实误差、算法胜出、新颖性或视频收益。帧是该测量的等权贡献单位，6块仍只有2个已见物理场景。

## 执行入口与输入合同

入口 `scripts/measure_s14b_observation_disagreement.py --manifest PATH --output NEWDIR`，`--root`默认主项目根目录。manifest.schema固定 `s14b-observation-disagreement-v1`；inputs必须精确24条 `{path,sha256}`，只允许S7_event_replay/S8_event_replay_v2各block0..2_stride8，每块observations.npz、A0_events.json、A0P0.npz、A0P0_sources.json。source_sha256为最终生产脚本SHA字符串；controls由调用者冻结和前后核对。

全部24输入先读字节、核SHA、缓存，之后只从缓存解码。NPZ必须allow_pickle=False，显式读取观测ids/points/radii/offsets及地图points/radii/counts共7成员每块；normals/colors不解码。成员目录必须精确匹配旧schema且无重复。所有使用到的整数、shape、域、有限数值、20帧、stride8像素栅格与raster顺序均核查。

events必须保留old_n、新出生顺序、matches/targets以及逐帧边界；出生点不能被同帧再匹配；所有flat index恰用一次。每点来源frame集合和地图counts精确一致；地图位置、半径与出生观测精确一致。半径及平方有限正值，不加epsilon。D直接计算，原值及半径归一化值均以预定atol=1e-12、rtol=1e-10核D=B+A，不能事后改门。single_source写0/1；m=1只有出生观测，四量为零。

## 输出schema（已与独立核验者协调）

- points.csv字段顺序：phase,block,stride,point_id,m,n_obs,single_source,birth_frame,birth_flat_index,birth_u,birth_v,mem_x,mem_y,mem_z,radius,W,B,A,D,W_over_radius2,B_over_radius2,A_over_radius2,D_over_radius2。
- frame_centroids.csv：phase,block,stride,point_id,frame,n_obs,c_x,c_y,c_z,within_variance。
- association_indices.json：schema；blocks数组，每块含phase/block/stride，groups按point_id、frame排序，每项point_id/frame/flat_indices。flat_indices为原观测数组行号。
- summary.json：schema、quantile_method=linear、blocks。每块有phase/block/stride、n_points、n_observations、n_frame_groups、single_source_points、multi_source_points；by_m只按精确m分层，每层m、n_points、metrics，每8个量各mean/median/p90。不跨块合并统计。
- metadata.json记录实际时点、环境、读取/解码/输出计数、峰值RSS、源码/manifest/输入前后SHA、状态与失败。source_snapshot.py及execution_manifest.json保留执行字节快照。摘要中的观测和连接组数是审计计数。

已有目录在任何写入前拒绝；新目录内启动即保存RUNNING metadata、缓存后/每块后更新；正常异常和SIGTERM保存FAILED与错误。无法捕获SIGKILL或掉电，此时只能保留最近RUNNING记录，由调用者记录外部终止。失败目录保留；不改旧结果。

## 人工检查与待做

35项人工检查通过；帧像素不均衡例为frame0一个位置0、frame1三个位置1/3/5，半径2，预期W=4/3、B=A=2.25、D=4.5；按全像素加权会得到不同结果。另核零分散、纯帧间变化、single-source、连接全覆盖、错误半径/身份/整数/JSON等。它们仅证明这些人工输入上的软件行为，不是效果证据。初版与最终版源码及回执均保留。

最终源码SHA：`60c5fe173ef1c0dea213ec4cb3cf2c79fd7963b50782c0ed825fdbef2ad5145b`。

证据：`work/S14B_implementation/artificial_checks.py`、`artificial_receipt_v1.json`、`artificial_receipt_v2.json`、`preparation_receipt.json`。根任务须获不同作者最终预审后冻结执行manifest；真实运行和独立真实核验由根负责。本作者未运行真实数据。
