# S81 真实深度评分增补

本目录交付单独 5 页中文增补，供零基础阅读；不改已有 125 页报告。实际实验时间为北京时间 2026-09-11 01:11。计算和团队内不同作者数值复算已通过，作者与 root 已检查增补内容及前一版全部页面；最后三处措辞修改后的第 1、4、5 页由作者重新检查，供 root 最终回读。

- `S81_真实深度评分增补.pdf`：最终阅读版，SHA-256 `6c513e8aaa8cbde1a3a448e0aa22f1feacea34c3924cccbf7dbf410fbcf5f89b`。
- `S81_真实深度评分增补.tex` 与 `review_status.tex`：可编辑源文件，需放在同一目录。
- `S81_全部24行.csv`：从本次实际运行 `../execution_01/ROWS.json` 转录的全精度表；PDF 保留全部 24 行，误差显示三位小数。`全部24行表.tex` 为同值表片段备份，最终主文直接包含表格行。
- `AUTHOR_PDF_QA.json`：页数、源文件与图片哈希、24 行转录检查、编译和逐页检查记录。`BUILD_SOURCE_RECEIPT.json` 保留实际引用文件与阅读范围。
- `archive_before_root_final_wording/`：最后三处措辞修正前的 PDF 与源文件，保留原稿。

## 如何重编

在本目录使用已有本机 XeLaTeX。两次编译后，将 `build` 中的 PDF 复制到本目录。该操作只构建报告，不运行科研实验。

```bash
mkdir -p build
/opt/homebrew/bin/xelatex -interaction=nonstopmode -halt-on-error -output-directory=build S81_真实深度评分增补.tex
/opt/homebrew/bin/xelatex -interaction=nonstopmode -halt-on-error -output-directory=build S81_真实深度评分增补.tex
cp build/S81_真实深度评分增补.pdf S81_真实深度评分增补.pdf
```

所用字体：Arial、Menlo、Songti SC、Heiti SC 与 Arial Unicode MS。TikZ 教学图由主文直接绘制，不依赖外部图片；教学数字已明确标为人工示意。重编可能改变 PDF 元数据及文件哈希，修改后需重新渲染检查，不应沿用本次 PDF 哈希或 QA 状态。

```bash
pdftoppm -png -scale-to 1500 S81_真实深度评分增补.pdf qa/rebuilt
```

本报告作者没有重新运行评分、解码原始 RGB/深度或新增网络读取。文献链接的读取范围见项目同层的两份 `SOURCE_SCOPE.json`；生成引导只是一条尚未执行的候选路线。所有真实记录、无效值、配对比较及独立复算仍以原实验目录为准。
