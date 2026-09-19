# S17C 离线点云查看器：设计、固定规则与交接

2026-09-06 UTC 11:36 代码准备记录。只读了原则/记忆/日志、S17C producer/verifier
源码和 figure-designer 技能；**没有读取真实结果 NPZ、运行 metadata、GT 或照片，
没有生成 HTML，没有启动浏览器，也没有运行模型**。

生成器：`scripts/build_s17c_pointcloud_viewer.py`。
准备版本 SHA-256：`e2a6ab25a5b4c08e1dc008f719850db07856c40619de4f526e180ec0e9412247`。
静态检查回执：`work/S17C_viewer_preparation/static_checks.json`。

## Figure type / 图的角色

这是给初学者理解真实模型几何的**交互补充材料**，使用 experimental-results
指导中的来源、诚实坐标范围、自包含注释要求。它不是论文中的方法对比图，也不
负责证明新方法效果。数据本身为三维，3D呈现有科学用途，不是3D柱形图装饰。

应用技能 `/Users/rocket/.codex/skills/figure-designer/SKILL.md`，已读其
`experimental-results.md`、`design-rules.md`、`tools.md`。按用户/root明确要求
采用无外部依赖的 Canvas；本交互辅助页面不满足论文矢量图输出规则，不能直接
当作 camera-ready figure。后续如需投稿图，应另用科学绘图库产生矢量文件。

## Paradigm / 表达方式

原始点云、真实输入颜色、两个估计相机放在同一模型坐标系中。单一正交投影，
统一比例，用户可以旋转、缩放、平移。没有修补平面、去噪、重估坐标、删异常点
或重新对齐相机。只对视图进行整体变换，原位置以little-endian FP32逐字节嵌入。

固定像素网格从 `(行0,列0)` 起，stride=4。384×512每图得到96×128=12,288点，
两图合计24,576点，均来自完整两图；原393,216稠密点仍在封存NPZ中。初始视图
范围按**全部稠密点与两个估计相机中心**共同计算，不能按置信度/好区域裁范围。

默认以原wrapper返回的`colors`着色；它对应处理后输入照片，不能用模型`rgb`
预测头替代。另提供“来源编号”模式：图0蓝色圆形、图1橙色方形，颜色加形状。
置信度滑块仅改显示，初始下限是全部采样点的最小值，包含所有零置信度点。
UI分别写筛选保留数和两图数量；视角遮挡/视窗裁剪不伪装成数据筛选。

## Layout / 布局

- 主区域：可交互点云占左侧；右侧是置信下限、着色、屏幕点大小、相机标记、
  恢复与完整范围按钮。窄屏按上下排列。
- 顶部：明确“模型推断、任意尺度、非传感器真值、非完整Surfel/视频”，列2张
  已见输入、实际采样点与档案点数、独立核验状态及其数值完整性边界。
- 点云下方：两张同stride的处理后输入颜色预览，始终保留两图，明确不是原始
  分辨率原图；无需再次打开原RGB。
- 底部：固定采样规则、坐标单位与可展开完整来源JSON、实际运行时间、SHA和
  全部显示参数。点数不称独立实验数。

屏幕正文15px、主要提示13px、标题23–28px；背景纯色，未加梯度或点的阴影。
世界X/Y/Z都有字母标记；相机C0/C1用标签加颜色。照片RGB无法保证色盲区分，
所以提供编号着色模式及两图文字信息。没有“ours领先”或先验成功突出处理。

## Integrity gate / 生成前的身份门

必须由 root 在S17C封存并独立核验PASS后提供以下8项CLI参数：

| 参数 | 含义 |
|---|---|
| `--manifest` / `--manifest-sha256` | root冻结的S17C执行manifest及准确SHA |
| `--seal` / `--seal-sha256` | root输出封存文件及准确SHA |
| `--verification` / `--verification-sha256` | 真正PASS的独立核验回执及root提供SHA |
| `--run-dir` | 包含封存final_result.npz/run_metadata.json的目录 |
| `--output-dir` | 位于封存run目录外、尚不存在的新目录 |

可用项目现有NumPy Python环境运行，不使用模型环境或overlay中的模型代码。
生成器先读取四个控制JSON（manifest/seal/verification/run_metadata），核验：

1. manifest/输出seal/独立回执与输入SHA完全一致；source commit和S17C schema符合。
2. 独立回执status PASS、inputs_unchanged真、所有checks通过、独立验证源码身份
   被manifest绑定；其file_hashes明确核过这份manifest、seal、metadata与final NPZ。
3. producer SUCCESS且相同manifest；没有训练、GT prior、accuracy/video/Surfel
   对象声明；两图索引0/1、400步无先验协议保持一致。
4. final NPZ与seal及producer文件身份都相同，然后才允许解码数组。

只解码final_result.npz中的5数组：point_clouds/colors/confidences/R/t；不打开
其它NPZ、RGB、深度、GT或权重。先核zip成员域/大小，再核固定形状/FP32/有限值/
逐数组SHA；非有限数据直接保存失败，不静默删除难点。colors要求0..1，conf
要求非负。完整8个结果成员仍需存在，未用成员不会被解码。

输出是单文件`viewer.html`及`viewer_receipt.json`。HTML嵌入所有采样数据，
没有fetch、外部JS、网络字体或远程资源；CSP禁止网络连接。元数据作为转义JSON
嵌入，文本用textContent呈现。生成后重新核全部实际读取的输入SHA，成功状态
仅为`GENERATED_FROM_VERIFIED_ARCHIVE_BROWSER_QA_PENDING`，不会伪称浏览QA通过。

## 已完成的检查与待做的真实QA

实际执行Python AST解析和Node `--check`，检查单一内联脚本、无外部脚本/网络
API、固定stride及默认全部显示等静态条件。9项静态项通过；这些不是实验、
不是HTML实际可视检查，也不代表真实数据PASS。没有加载或生成假点云来冒充
模型结果。`viewer_script.js`只是从模板抽出的JS语法检查副本。

根任务释放已核数据之后：

1. 用准确root绑定SHA执行生成器，核生成回执中的5数组读取及24,576采样数。
2. 实际浏览离线HTML，检查两图颜色、初始全范围、零confidence默认保留、滑块
   筛选数、恢复按钮、旋转/缩放/平移/双指/键盘、窄屏排版及无网络依赖。
3. 对比页面内来源与实际封存档案，确认所有两个来源保留、不误标GT或完整视频。
4. 如果几何明显歪斜、重影或不完整，按实际展示；如只有显示实现错误，可修
   viewer并新记代码/页面版本，不修改真实数组或重新挑选点。

Universal rule审查：来源/坐标范围/不装饰数据可由代码审核；真实字体、交互、
颜色可辨认度要等浏览QA。矢量投稿要求在本辅助HTML范围之外，3D因数据本身三维
适用。没有把技能的“需要视觉核验”写成已通过，也不要求用户重复批准已经授权
的本地浏览检查。

root维护主账，本任务仅写新生成器与本准备目录；未改C producer、verifier、
overlay或已封存实验结果。
