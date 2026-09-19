"""Typeset the reviewed teaching draft and accepted S85 metadata, no experiments."""
from pathlib import Path
import hashlib
import json
import re
import shutil

B = Path(__file__).resolve().parent
R = B.parents[2]
S85 = R / 'work/S85_fixed_geometry_warp'
source = (B / 'CONTENT_DRAFT.md').read_text()
cutoff = json.loads((B / 'STATE_CUTOFF.json').read_text())
summary = json.loads((S85 / 'execution_01/SUMMARY.json').read_text())
(B / 'images').mkdir(exist_ok=True)
(B / 'build').mkdir(exist_ok=True)
(B / 'qa').mkdir(exist_ok=True)
copied = []
for target in (20, 21, 22, 23):
    original = S85 / 'visuals_01' / f'target_{target}_holes_marked.png'
    dest = B / 'images' / original.name
    shutil.copyfile(original, dest)
    copied.append(dict(path=str(original), local=str(dest.relative_to(B)),
                       sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),
                       bytes=dest.stat().st_size))


def esc(text):
    text = text.replace('−', '-').replace('–', '-').replace('—', '-')
    table = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$',
             '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}',
             '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
    return ''.join(table.get(c, c) for c in text)


def table(lines):
    rows = [[x.strip() for x in line.strip('|').split('|')] for line in lines]
    rows = [row for row in rows if not all(re.fullmatch('[-:]+', x) for x in row)]
    n = len(rows[0])
    result = [r'\begin{center}\small\begin{tabular}{' + 'l' + 'r' * (n-1) + r'}\toprule']
    for i, row in enumerate(rows):
        result.append(' & '.join(esc(x) for x in row) + r'\\')
        if i == 0:
            result.append(r'\midrule')
    result.append(r'\bottomrule\end{tabular}\end{center}')
    return '\n'.join(result)


def prose(block):
    if block.startswith('【'):
        return r'\noindent\textbf{' + esc(block.split('】')[0] + '】') + '}' + esc(block.split('】',1)[1]) + '\n\\par\n'
    if block.startswith('自测'):
        before, after = block.split('答：', 1)
        return r'\noindent\textbf{' + esc(before) + '}\\ ' + esc('答：' + after) + '\n\\par\n'
    if block.startswith('证据入口：'):
        for name in ['INDEPENDENT_OUTPUT_REVIEW.json', 'supervision_01/SUPERVISION.json']:
            block = block.replace(name, '<PATH>' + name + '</PATH>')
        chunks = re.split(r'(<PATH>.*?</PATH>)', block)
        return ''.join(r'\path{' + x[6:-7] + '}' if x.startswith('<PATH>') else esc(x) for x in chunks) + '\n\\par\n'
    return esc(block) + '\n\\par\n'


head = r'''\documentclass[UTF8,11pt,a4paper]{ctexart}
\usepackage[margin=1.9cm,headheight=15pt]{geometry}
\usepackage{amsmath,amssymb,booktabs,array,graphicx,tikz,xcolor,hyperref,xurl,fancyhdr,enumitem}
\usetikzlibrary{arrows.meta,positioning}
\setmainfont{Arial}\setsansfont{Arial}\setmonofont{Menlo}
\setCJKmainfont{Songti SC}\setCJKsansfont{Heiti SC}
\definecolor{ink}{HTML}{163C50}\definecolor{accent}{HTML}{007C91}
\hypersetup{colorlinks=true,urlcolor=accent,linkcolor=ink,pdftitle={S85与S86：从历史投影到生成强对照},pdfauthor={AI辅助整理；依据项目实际记录}}
\renewcommand{\UrlFont}{\fontspec{Arial Unicode MS}\small}
\setlength{\parskip}{.48em}\setlength{\parindent}{1.5em}\linespread{1.06}
\setlength{\emergencystretch}{2em}\renewcommand{\arraystretch}{1.13}
\pagestyle{fancy}\fancyhf{}\lhead{\small S85 / S86：零基础教学增补}\rhead{\small 科学截点 09-11 05:34}\cfoot{\small\thepage}
\ctexset{section={format=\Large\bfseries\sffamily\color{ink},beforeskip=0pt,afterskip=.7em}}
\newcommand{\teaching}[1]{\begin{center}\fcolorbox{accent}{accent!5}{\parbox{.91\linewidth}{\small #1}}\end{center}}
\begin{document}
'''
pages = re.split(r'^## 第\d+页：', source, flags=re.M)[1:]
require_pages = len(pages)
assert require_pages == 10
parts = [head]
equations = {
    2: r'''\teaching{\textbf{针孔公式教学表达：}
    \[\mathbf{X}_s=Z\begin{bmatrix}(u-c_x)/f_x\\(v-c_y)/f_y\\1\end{bmatrix},\quad
    \mathbf{X}_t=R_t^T(R_s\mathbf{X}_s+c_s-c_t),\quad
    u'=f'_x (\mathbf{X}_t)_x/(\mathbf{X}_t)_z+c'_x.\]
    Z单位是米，焦距单位是像素；坐标方向与每个变换的输入输出必须对应。}''',
    3: r'''\begin{center}\small
    \begin{tabular}{lrrrr}\toprule
    人工目标格点&(10,20)&(11,20)&(10,21)&(11,21)\\\midrule
    正权重&0.56&0.14&0.24&0.06\\
    作用&候选资格&候选资格&候选资格&候选资格\\\bottomrule
    \end{tabular}\end{center}''',
    7: r'''\teaching{\textbf{人工教学，非实验数值：}
    \[w=\lambda m(1-h),\qquad d_g=(1-w)d+wg.\]
    \[0.75\times0.2+0.25\times0.8=0.35,\qquad
      0.875\times0.2+0.125\times0.8=0.275.\]
    第一式覆盖比例为1；第二式为0.5。历史保护或无支持时，直接保留原值。}''',
    8: r'''\teaching{\textbf{正式主指标的分母固定，下面不是实测分数：}
    \[L_a=\frac14\sum_{t=20}^{23}\frac{1}{995328}
      \sum_{p,c}\left(\frac{U_{a,t,p,c}-U_{{\rm ref},t,p,c}}{255}\right)^2.\]
    差值 $\Delta=L_{\rm guide}-L_{\rm terminal}$；负号表示该MSE更低，不表示统计显著。}'''
}
for number, page in enumerate(pages, 1):
    title, rest = page.split('\n', 1)
    if number > 1:
        parts.append(r'\clearpage')
    parts.append(r'\section*{' + f'{number}. ' + esc(title) + '}')
    if number == 1:
        parts.append(r'\begin{center}{\large\bfseries 从历史照片投影，到真正影响生成}\end{center}')
        parts.append(r'\teaching{\textbf{科学状态截点：北京时间2026-09-11 05:34:29。}S85已完成并通过不同作者复算；S86已正式启动，监督回执仅确认G0完成9/50步、仍在运行。四臂尚未完成、未评分。本增补不覆盖旧142页汇报，也不预写成功。}')
    blocks = rest.strip().split('\n\n')
    for idx, block in enumerate(blocks):
        if number == 4 and idx == 0:
            block = '以下是S85已导出并验收的四个目标投影。颜色来自历史实拍照片，位置由预测几何决定。灰格是标注的孔洞，不是原场景纹理。这些图不是目标视角实拍，也不是S86新生成。'
        if number == 5 and block.startswith('正式PDF'):
            block = '下表保留全部16对，每行源点分母均为196608；数值直接整理自已接受的SUMMARY。本批源/目标非有限与非正四类状态均为0，出画源点保留。足迹数与源点数不是同一分母。'
        if block.startswith('|'):
            parts.append(table(block.splitlines()))
        else:
            parts.append(prose(block))
        if number == 1 and idx == 2:
            parts.append(r'''\begin{center}\begin{tikzpicture}[>=Latex,font=\small,box/.style={draw=accent,fill=accent!5,rounded corners=2pt,align=center,text width=2.55cm,minimum height=1.2cm}]
            \node[box](a){历史照片\\S82预测几何};\node[box,right=4mm of a](b){固定相机\\S83拟合深度};
            \node[box,right=4mm of b](c){搬到目标视角\\S85已核投影};\node[box,right=4mm of c](d){四种生成对照\\S86运行中};
            \draw[->](a)--(b);\draw[->](b)--(c);\draw[->](c)--(d);\end{tikzpicture}\end{center}
            \noindent\small\textcolor{accent}{流程教学图；末框按本报告截点仍未完成。}\normalsize''')
        if number == 4 and idx == 0:
            images = [r'\begin{center}']
            for ti, t in enumerate((20, 21, 22, 23)):
                images.append(r'\begin{minipage}{.46\linewidth}\centering\includegraphics[width=6.2cm]{images/target_' + str(t) + r'_holes_marked.png}\\{\small 目标 ' + str(t) + r'：历史颜色投影}\end{minipage}' + (r'\hfill' if ti % 2 == 0 else r'\\[3mm]'))
            images.append(r'\end{center}')
            parts.append('\n'.join(images))
        if number == 5 and idx == 1:
            rows = [r'\begin{center}\small\begin{tabular}{rrrrrr}\toprule',
                    r'目标&历史&有效源点&出画源点&合格足迹&赢家足迹\\\midrule']
            for target in summary['targets']:
                for pair in target['pairs']:
                    values = (target['target_id'], pair['history_id'], pair['status_counts']['VALID'],
                              pair['status_counts']['OUTSIDE'], pair['eligible_footprints'], pair['winning_footprints'])
                    rows.append(' & '.join(f'{v:,}' for v in values) + r'\\')
                if target['target_id'] != 23:
                    rows.append(r'\addlinespace[.3em]')
            rows.append(r'\bottomrule\end{tabular}\end{center}')
            parts.append('\n'.join(rows))
        if number in equations and idx == 1:
            parts.append(equations[number])
    if number == 10:
        parts.append(r'\vfill\noindent\small\textcolor{accent}{内容依据本地冻结协议与实际回执；人工教学单独标注。作者排版核验与root独立科学/视觉验收另见报告目录回执。}')
parts.append(r'\end{document}')
tex = B / 'S85_S86_从投影到生成强对照_教学增补.tex'
tex.write_text('\n\n'.join(parts) + '\n')
receipt = dict(scope='Document production only; no scientific execution or new result scoring.',
               draft_sha256=hashlib.sha256((B / 'CONTENT_DRAFT.md').read_bytes()).hexdigest(),
               state_cutoff=cutoff, source_images=copied,
               summary_sha256=hashlib.sha256((S85 / 'execution_01/SUMMARY.json').read_bytes()).hexdigest(),
               tex_path=str(tex), tex_sha256=hashlib.sha256(tex.read_bytes()).hexdigest(),
               requested_logical_pages=10, actual_pdf_pages='pending compile',
               artifact_marker='PDF skill mark_artifact_operation_started.mjs create pdf count1 completed successfully exactly once before CONTENT_DRAFT creation.')
(B / 'SOURCE_BUILD_INPUTS.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print(tex)
