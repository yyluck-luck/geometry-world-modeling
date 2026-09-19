# 从重影到可信几何参照：S88 / S89 教学增补

当前为 **8 页、等待 S89 最终实际回执的教学草稿**。正文截点为北京时间 2026-09-11 09:17:31，不能作为此后 S89 的最新运行状态。原 168 页报告未修改、未合并。

主源文件是 `S88_S89_从重影到可信几何参照.tex`。已检查的当前 PDF 位于 `build/run_02/S88_S89_从重影到可信几何参照.pdf`。`AUTHOR_DOCUMENT_QA_DRAFT.json` 记录作者实际逐页查看全部 8 页后的检查；`SOURCE_BUILD_INPUTS.json` 记录引用证据及原文件身份。首轮构建中的缺字和长路径排版问题已经修复，首轮源稿和日志保留在 `build/run_01/`。

正文包含低 MSE 与重影的纸面反例、S86/S87 已接受真实数字、S88 官方模拟场景元数据访问及边界、相机/深度基础、同视角三件套的必要性、proposal 当前位置和五个导师追问。纸面图均明确为教学示意；唯一实验图复用 S87 已接受的目标 22 对照图。

## 本机重建

```sh
'/Users/rocket/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3' '/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S89_matched_view_index/report/rebuild.py'
```

重建使用本机 XeLaTeX 编译两遍、pypdf 提取页数和文字、Poppler 渲染全部页面，每次新建独立 `build/run_NN/` 并留下真实日志。重建本身不包含人工视觉验收；内容修改后必须查看对应的新页面。本轮已在首次写作前成功调用 PDF artifact marker 一次。

## 待定稿内容

S89 真实运行及恢复结果只在收到父任务给出的已接受回执后填写。首次失败与恢复批次应分别记录，不能删去失败或预写成功。最终内容和版面还需父任务独立核读；不自动复制用户输出目录。
