# S14E 评分后对照图准备

当前仅完成绘图程序、人工输入运行和人工PNG视觉检查，未读取真实S14E评分、真实目标RGB/深度，未运行模型。程序不更改已冻结prepare/predictor/scorer。

## 根任务调用

使用已有带Matplotlib的系统Python，不用模型专用venv：

```text
/opt/homebrew/bin/python3 scripts/plot_s14e_depth.py \
  --score-dir /absolute/successful_score_dir \
  --score-manifest /absolute/static_score_manifest.json \
  --score-metadata-sha256 ROOT_CHECKED_SUCCESS_METADATA_SHA \
  --rgb-manifest /absolute/report_only_rgb_manifest.json \
  --output /absolute/fresh_reporting_dir
```

报告专用RGB manifest（不将这些照片路径加入模型或score静态manifest）：

```json
{
  "schema": "s14e-report-rgb-manifest-v1",
  "scope": "real_research_report",
  "frozen_inputs": "/absolute/results/S8_cut3r_cpu_v2/frozen_inputs.json",
  "frozen_inputs_sha256": "SHA256",
  "dataset_root": "/absolute/TUM_dataset_directory",
  "targets": [
    {"query_index":20,"rgb_path":"/absolute/rgb20.png","rgb_sha256":"SHA256"},
    {"query_index":21,"rgb_path":"/absolute/rgb21.png","rgb_sha256":"SHA256"},
    {"query_index":22,"rgb_path":"/absolute/rgb22.png","rgb_sha256":"SHA256"},
    {"query_index":23,"rgb_path":"/absolute/rgb23.png","rgb_sha256":"SHA256"}
  ]
}
```

程序首先核外部绑定的score run_metadata SHA、SUCCESS、4深度/12行/0RGB边界、前后身份门和完成时间，再核所有score payload SHA、原score manifest绑定。此后才能读RGB manifest并从原S8 block0核4个RGB/depth配对路径及SHA，最后hash/open对应4张照片。评分只消费已评分arrays.npz的gt_depth_m和prediction_depth_m两个字段；读取metrics.json全部12行，不重复计算分数。所有尝试、打开、解码、SHA、时间、范围及依赖版本见figure_receipt.json；失败保留。

## 图与输出

每行query20—23，五列依次：事后真实RGB参照、传感器GT光轴深度、CUT3R ray-only、20history z-buffer、history常数。RGB未在模型/评分时提供，只有本报告阶段读取；RGB/depth仍有原配对时间差。RGB按固定LANCZOS resize299×224再crop[37,0,261,224]显示；GT/预测数组已经评分，绘图阶段不重采样、平滑、截断、补洞或筛query。

4GT+12预测共16张深度图的全部有限正深度联合确定唯一完整线性色域；NaN、inf、非正深度灰色并逐图计数。不用分位数剪裁，不按方法/每图调色域；原值保留在score。极端值也纳入最大最小。只有全部有效深度完全相同时才扩展显示上下限以让colorbar合法，原始唯一值及display范围分别记录；没有删除数据。

输出 `s14e_all_four_targets.png`、同名SVG、`all_12_scores.csv`（原始12行完整转写）、`图注.md`、plot源码和RGB manifest快照、`figure_receipt.json`。SVG内标签/轴为矢量，照片和测量网格仍是实际栅格，不冒称位图被转换成纯矢量。

## figure-designer实际执行

- 选择实验支持图：固定网格同时比较场景外观、测量与预测；条形图/流程图不能表达像素结构，故用图像矩阵。
- 13.2×11.7英寸独立阅读画布，4×5等尺寸方图、标签8—12pt、Viridis连续深度，灰缺失；方法由固定列位及文字双重区分，不突出未经证实的赢家。
- 核自包含图注、米制色标、像素坐标、全部查询、相同时刻/非相同时刻说明。图注用“评分后读取”而不是“预测封存后测量”，避免暗示传感器当时才采集。
- 已实际查看人工PNG，未见重叠/裁切，灰洞和联合色标清楚。当前只核独立电子阅读尺寸；没有宣称缩为论文单栏后字体仍≥8pt，也没有进行真实图的视觉核验。
- 读取技能：`/Users/rocket/.codex/skills/figure-designer/SKILL.md`及references/experimental-results.md、design-rules.md、tools.md。原始照片/传感器图天然为栅格；按用户要求同时保留PNG预览与SVG文字/轴结构，不伪造纯矢量测量。

## 人工检查、失败与纠正

`artificial_v3/receipt.json` 13项通过：全16深度图、完整finite-positive范围、极端深度不剪裁、恒定值扩展说明、2数组读取、4人工RGB、完整12行CSV、SVG/PNG、产物SHA、FAILED score阻断，以及阻断前RGB hash/open/decode和数组decode均为0。额外object数组未读取。人工照片是彩色网格，图标题明确“ARTIFICIAL LAYOUT CHECK”，不能作科研证据。

artificial_v1在模型venv中因Matplotlib未安装而失败，保留其FAILED报告、stdout/stderr和读取计数；此前只读4张人工照片，无真实图片。切换本机已存在的/opt/homebrew/bin/python3，未安装依赖，artificial_v2通过。人工视觉检查后将图中字样Measured改为Read，补依赖版本记录；原源码保留before_caption_wording.py，artificial_v3重新通过并实际查看。原v1/v2目录和script保留，没有覆盖失败。

## RESEARCH_PRINCIPLES.md快速核对（未修改主文）

已覆盖用户自主持续推进、新手中文、Supervisor与本地Claude技能、本机检索工具、多agent、可证伪创新、老师汇报目标、逐步时间主账、30分钟检查、接手材料，以及证据分级/失败保留/答案隔离。无实质用户要求遗漏。

可增强两点操作性：链接docs/PROJECT_DELIVERY_TRACKER.md明确完整项目验收（本轮完成不等于项目完成）；写明全部可自主工作完成且无值得继续检查事项时停止接续并列剩余外部证据。还可把“不调用Claude模型或CLI、不提交个人信息申请”逐字写明，与当前memory约束更一致。未据这些建议新增审批或暂停研究。
