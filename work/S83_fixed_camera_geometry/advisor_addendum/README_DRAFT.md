# S82 / S83 汇报增补源稿

五页 LaTeX 源稿，沿用 S81 增补字体和版式。第1页解释流程与输入；第2页只报告已接受的 S82；第3页解释冻结的 S83 方法；第4页 `S83_actual_results.tex` 等待 root 提供真实执行及接受证据；第5页说明未来普通生成对照及创新边界。

当前只交源稿。不得在待补页仍存在时交付为完成版 PDF。源稿中的教学图与算例明确不是实际点云或实验数据。原125页汇报、S80/S81文件和所有实验文件不改。

完成结果页后，从本目录用本机 XeLaTeX 编译两遍，输出到单独 build；用 pdftoppm 渲染全部页、逐页检查后，再交 root 最终视觉验收。允许 3–5 页，当前用四个 clearpage 固定为五页设计，实际页数仍须编译核实。

来源：S82_RESULTS.md、ROOT_GEOMETRY_RESULT_ACCEPTANCE.json；S83 已冻结 CONTRACT.json / run_fixed_geometry.py；S81 原增补版式。本源稿未重新读取真实 RGB / 点图 / 相机科学数组，未运行模型或优化器。
