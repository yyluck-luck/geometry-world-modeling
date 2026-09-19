# S85 / S86 零基础教学增补（10页）

主文件是 `S85_S86_从投影到生成强对照_教学增补.pdf`；同名 `.tex` 可编辑，`CONTENT_DRAFT.md` 是中文内容稿，`images/` 为四张已有 S85 图片的原字节副本。旧142页连续汇报未改动。

科学截点固定为北京时间 **2026-09-11 05:34:29**：S85 已完成并通过独立保存量复算；S86 真实启动、G0 已完成9/50步，四臂未完成且无评分。本PDF不随着后续进度改变；后续结果应另作带时点的增补。

内容包含 proposal 主线、相机 Z/投影手算、候选/孔洞、四张真实投影与完整16对表、四臂强对照、融合和MSE手算、可能结果的解释边界、口述和自测。所有教学数值均与实测分开；覆盖不是准确率，当前没有方法创新验证。

作者已将最终PDF全部10页渲染并实际逐页查看；0缺字、0溢出，表格/公式/图注完整。具体SHA、图像来源、真实状态截点和检查记录见 `AUTHOR_DOCUMENT_QA.json`、`SOURCE_BUILD_INPUTS.json`、`STATE_CUTOFF.json`。Root独立科学与视觉验收另行保存。旧11页草稿渲染隔离在 `qa/first_build_11pages/`，最终渲染为 `qa/final-01.png` 至 `final-10.png`，其中第6页由组件身份披露修订后的 `qa/final_component-06.png` 替代；其余九页逐页文本完全相同。前一冻结PDF/TeX与QA保留在 `build/before_component_identity_note/`。

## 重新编译

在本目录运行；只重建文档，不执行科研：

```sh
/opt/homebrew/bin/xelatex -interaction=nonstopmode -halt-on-error -output-directory=build S85_S86_从投影到生成强对照_教学增补.tex
/opt/homebrew/bin/xelatex -interaction=nonstopmode -halt-on-error -output-directory=build S85_S86_从投影到生成强对照_教学增补.tex
/opt/homebrew/bin/pdftoppm -scale-to 1300 -png build/S85_S86_从投影到生成强对照_教学增补.pdf qa/rebuilt
```

本机字体：Arial、Menlo、Songti SC、Heiti SC、Arial Unicode MS。XeLaTeX的两条默认CJK字体族重定义警告来自显式选用本机字体。PDF重编会改变制作时间元数据，内容检查与新的SHA需按新文件记录；不要将旧QA冒用于重编文件。

`prepare_report.py` 可从内容稿和已接受S85摘要重新生成LaTeX，并复制四图；仅在有意重新生成内容时使用。直接编辑LaTeX后不要再运行它覆盖改动。
