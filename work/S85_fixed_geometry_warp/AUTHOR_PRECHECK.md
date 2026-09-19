# S85 作者交付与人工前检

记录UTC：2026-09-10T20:12:09.446440+00:00。状态：源码/合同与一次人工检查完成，真实投影尚未运行，等待不同作者前审与root启动。

- `project_fixed_geometry.py`：359行，SHA `344ad059365bc775af0c8336eeffdaf0b44c073626aca3a4c3a10e138c2d3019`。
- `CONTRACT.json`：SHA `bcf4801ff1619ec74e5714e2ba90c556a6abb6c45f48b2f3185b2eb9925a333b`；四输入历史与四目标/固定状态、原字节和所消费字段body SHA、全部输出schema、控制边界均明确。
- `check_projector_synthetic.py`：SHA `269163f28752cb963949eba05d4773237f68a5d849e9fb868c41b36939c98fcd`；一次实际人工运行UTC 2026-09-10T20:08:45.544304+00:00至2026-09-10T20:08:45.594433+00:00，0.050139166秒，`PASS_ARTIFICIAL_ONLY`。回执 `AUTHOR_SYNTHETIC_01.json`，SHA `c694a8778ec69a68121f439f850c67c929bce9653d80145d092cb0c1ec3d96d6`。

人工检查落实三手算夹具，以及端点/中心略域外拒绝/非单位旋转方向/非有限源和变换/严格RGB域/全hole/微型四源整合。实际同P坐标本次恰(204,193.5)；测试仍把浮点投影误差与literal精确两足迹分开，不新增snap或近似零阈值。第二候选允许等Z；赢家直接取RGB，0.3足迹不会把黄色变暗。空候选保留NaN深度和−1身份。容差仅人工FP64算术，不是物理质量门。

只读既有4设计文件、当前原则/记忆/最新主账与S83/S69/S72文本回执身份；没有解码科学NPZ值或打开图像。实际K576直接取S72 receipt的K_pixels_576字段，不用float32(287.4)替代保存的287.4000244140625。原S83源K/P在真实读取时按保存值仅升FP64。此阶段不需要NPZ头部读取，因为回执已有完整shape/dtype/body身份。第一次尝试ROOT_DESIGN_REVIEW.md不存在后已读正确.json，未用不存在文件作依据。

运行入口：项目 `.venv-cut3r/bin/python -I work/S85_fixed_geometry_warp/project_fixed_geometry.py`（完整argv在合同）。无CLI调参。runner自己创建唯一 `execution_01`，拒绝覆盖；root不要预建该目录。内部SIGALRM300秒、采样10GiB峰值RSS、写前严格估算2GiB输出。单CPU线程环境在NumPy导入前置1，几何不用BLAS。RSS不是内核强制地址空间保证；root可直接记录外部退出/耗时，无需新增监督框架。四目标最坏原始数值输出757088416字节，另加输入副本和少量ZIP/JSON开销；这是尺寸算术上界，不是实际消耗。

输出：一份 `INPUT_GEOMETRY.npz`保存本次实际消费的数组，四份 `TARGET_20/21/22/23.npz`各覆盖4来源及完整致密源状态/四槽足迹/排序候选与败者/硬赢家RGB-mask/来源及第二候选，`SUMMARY.json`逐目标增量，`RECEIPT.json`实际读入/时长/RSS/文件SHA；失败保留traceback及部分产物，不自动重跑。源/目标数组身份到实际执行时才验证，人工PASS不能替代该检查或真实结果验收。

限制：作者实现与作者人工测试不是独立复现，尚无真实覆盖率/warp/生成收益。保持 `NO_METHOD_SELECTED / new_method_validated=false`。没有修改其他作者设计、旧结果或主账。
