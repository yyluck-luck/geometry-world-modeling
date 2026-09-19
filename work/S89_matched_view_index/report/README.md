# 从重影到可信几何参照：S88 / S89 教学增补

**最终作者稿，8 页。科学状态截点：北京时间 2026-09-11 09:32:50 / UTC 01:32:50。** 同名 PDF 和可编辑 LaTeX 位于本目录，唯一引用图片已原样复制到 `images/target_22_comparison.png`。原 168 页报告未修改、未合并；尚未复制用户交付目录，后续由根任务独立核读和交付。

正文包含低 MSE 与重影的纸面反例、S86/S87 已接受真实数字、S88 官方模拟场景元数据访问及边界、相机/深度基础、S89 两次真实 TLS 失败、proposal 当前位置和五个导师追问。两次失败各 1 个逻辑请求，均 0 新正文、0 新成员头；已扫前缀未配齐不表示数据集中没有配齐文件。两处源码修复属于工程与记录改进，没有伪写为创新。

## 可移植的本机 LaTeX 编译

在含本 README、TeX 与 images 的目录中执行：

```sh
mkdir -p local_build
xelatex -interaction=nonstopmode -halt-on-error -output-directory=local_build S88_S89_从重影到可信几何参照.tex
xelatex -interaction=nonstopmode -halt-on-error -output-directory=local_build S88_S89_从重影到可信几何参照.tex
```

使用 macOS 字体 Arial、Menlo、Songti SC、Heiti SC、Arial Unicode MS，以及本机 XeLaTeX / ctex / TikZ。TeX 与 images 自含，不再依赖项目内 S87 相对目录。

## 原研究目录的证据检查与完整重建

```sh
'/Users/rocket/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3' '/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S89_matched_view_index/report/rebuild.py'
```

此脚本在原研究目录核已封存元数据，编译两遍、提取页数和文字、渲染全部页面，每次新建独立 build/run_NN。它依赖研究证据文件，不是脱离研究目录使用的通用构建器。人工视觉验收须单独做，编译不自动等同验收。

`SOURCE_BUILD_INPUTS.json` 是证据路径与 SHA 清单；`AUTHOR_DOCUMENT_QA.json` 记录实际逐页视觉检查、最终仅封面时间修正及其余 7 页精确文字/像素一致性。最新构建日志与所有 8 页 PNG 在 `build/run_04/`。历史草稿、首轮排版问题及 run_03 时间不一致均保留，不掩盖修订过程。

本报告未新增网络请求、模型运行、科学评分或 RTMV RGB/depth 正文访问。教学示意明确标为人工例；照片全部来自既有 S87 已接受产物。本轮首次写作前 PDF artifact marker 已成功运行一次。
