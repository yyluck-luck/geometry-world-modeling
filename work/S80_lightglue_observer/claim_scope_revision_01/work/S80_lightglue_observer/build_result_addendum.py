from pathlib import Path
import json, csv, hashlib, datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

p=Path(__file__).resolve().parent
out=p/'advisor_addendum'
out.mkdir(exist_ok=True)
rows=json.loads((p/'execution_01/ROWS.json').read_text())
lookup={(r['arm'],r['matcher'],r['target_id']):r for r in rows}
plt.rcParams.update({'font.size':12,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(2,3,figsize=(9.4,5.8),layout='constrained')
for j,arm in enumerate(['real','A0','B']):
    axs[0,j].set_title({'real':'Real photographs','A0':'Generated A0','B':'Generated B'}[arm])
    for method,color,marker,ls in [('BF','#0072B2','s','--'),('LG','#D55E00','o','-')]:
        rr=[lookup[arm,method,t] for t in [20,21,22,23]]
        axs[0,j].plot([20,21,22,23],[r['M'] for r in rr],color=color,marker=marker,ls=ls,label=method,lw=1.5)
        axs[1,j].plot([20,21,22,23],[r['correct']['quantiles_q25_q50_q75_q95_px'][1] for r in rr],color=color,marker=marker,ls=ls,label=method,lw=1.5)
    axs[0,j].set_ylim(0,750)
    axs[0,j].set_ylabel('Accepted matches (count)')
    axs[1,j].set_ylim(0,11 if arm=='real' else 270)
    axs[1,j].set_ylabel('Median fixed-F error (px)')
    axs[1,j].axhline(10,color='#444444',ls=':',lw=1)
    for ax in axs[:,j]:
        ax.set_xticks([20,21,22,23]);ax.set_xlabel('Target frame ID');ax.grid(axis='y',alpha=.2);ax.legend(frameon=False)
fig.savefig(out/'S80_support_and_geometry.pdf')
fig.savefig(out/'S80_support_and_geometry.png',dpi=160)
plt.close(fig)
with (out/'S80_全部24行数据.csv').open('w') as f:
    writer=csv.writer(f);writer.writerow(['target','arm','matcher','N_source','N_target','M','median_px','q95_px','count_le10','median_wrong_minus_correct_px'])
    for r in rows: writer.writerow([r['target_id'],r['arm'],r['matcher'],r['N_source'],r['N_target'],r['M'],r['correct']['quantiles_q25_q50_q75_q95_px'][1],r['correct']['quantiles_q25_q50_q75_q95_px'][3],r['correct']['counts_le_px']['10'],r['paired_wrong_minus_correct_quantiles_px'][1]])
table='\n'.join(f"{r['target_id']} & {r['arm']} & {r['matcher']} & {r['M']} & {r['correct']['quantiles_q25_q50_q75_q95_px'][1]:.3f} & {r['correct']['quantiles_q25_q50_q75_q95_px'][3]:.3f} & {r['correct']['counts_le_px']['10']} \\\\" for r in rows)
tex=r'''\documentclass[UTF8,11pt,a4paper]{ctexart}
\usepackage[margin=2cm]{geometry}
\usepackage{booktabs,longtable,graphicx,amsmath,xcolor,hyperref,xurl,fancyhdr}
\setmainfont{Arial}
\setmonofont{Menlo}
\setlength{\parskip}{.4em}
\setlength{\headheight}{14pt}
\pagestyle{fancy}\fancyhf{}\lhead{CSIT 6910：S80 真实实验增补}\rhead{2026-09-10 23:54 证据}\cfoot{\thepage}
\hypersetup{colorlinks=true,urlcolor=blue}
\begin{document}
\begin{center}{\LARGE\bfseries 真实实验更新：换匹配器以后，\\几何不一致还在吗？}\end{center}
\noindent\textbf{时间边界。}本增补晚于第二版主报告23:37的科研截点。它单独记录23:51的新模型计算与23:54的独立保存量复算。主报告旧截点及历史输出保留，不把后续结果写成此前已完成。
\section{先用普通话讲清楚}
我们正在研究：模型换一个视角画出同一个世界时，空间关系能不能保持一致。此前发现，生成图中的一些对应点不符合我们要求的相机几何。但是，这也可能跟用来找对应点的方法有关。于是这次用两种方法读取同一份特征，看问题会不会随匹配方式改变而消失。

BF按局部外观描述子的距离找相似点；LightGlue还使用同批点的位置、尺度、方向和学习到的关联规则。两者都没有得到未来真值来挑选匹配，也没有用几何误差过滤掉不合要求的点。它们接受的点数不同，不意味着某一种必然更准确。

\textbf{结果：}生成目标中，新BF共接受1171个匹配，LightGlue接受3939个。但这两组全部5110个接受匹配，在当前固定请求相机约束下的残差都大于10像素。因此，增加接受匹配没有消除这个场景中的几何不一致。它削弱了“现象完全只是旧匹配器找不到足够匹配”的狭窄解释。它还不能证明唯一原因是相机、3D表示、记忆或归一化。

\section{这次是真的运行了什么}
\begin{itemize}
\item 13张已有原评分RGB576图片：1张真实源图、4张真实对照、A0/B各4张模型生成图。没有重画或重新挑选图片。
\item 13次官方RootSIFT特征提取，每张只提一次；每个匹配器处理全部12对，得到24行。LightGlue是12次真实神经网络前向，不是模拟或仅加载组件。
\item 外部运行时间：23:51:06.059896至23:51:15.574014，9.513932583秒。CPU FP32，9层，无自适应删点或提前退出。采样进程树RSS峰值约0.853GiB；这不是瞬时硬峰值保证。
\item 没有重新训练模型，没有新的视频生成。这是对已有实拍/生成图的新观察器测量。
\end{itemize}
\clearpage
\section{把两个数字放在一起读}
\begin{figure}[h!]
\centering\includegraphics[width=\textwidth]{S80_support_and_geometry.pdf}
\caption{LightGlue增加了接受匹配数量，但生成图的固定相机几何残差仍然很大。上排为完整接受数，下排为所有接受点的中位双向点线距离；同一新特征数组同时提供给BF和LG。实拍与生成图的下排纵轴范围不同，均从0开始；虚线10px只是描述界线，不是科学验收阈值。各点来自同一场景及相关图像，没有独立重复，因此不画置信区间。}
\end{figure}
读图步骤：先看上排，确认我们没有只统计少数成功匹配；再看下排，确认匹配增多是否让请求相机约束更合理。实拍四目标的LG中位误差约1.40、2.84、1.22、2.48px，而生成图的LG中位误差约21.86至236.34px。不能只看“有多少点”，也不能只看误差而忽略有多少点、在哪些区域有点。

源图本次有1313个新特征。例如目标20的A0，BF接受252个，比例为$252/1313\approx19.19\%$；LG接受642个，比例为$642/1313\approx48.90\%$。这些是\textbf{接受比例}，不是准确率。判断准确率需要知道这些像素是否确实属于同一个物理点，当前没有这样的完整真值。
\clearpage
\section{全部24行，保留尾部误差}
所有行源特征数为1313。完整目标特征数、两个标签、覆盖和逐点量在随附CSV及项目NPZ中。中位数表示一半有效匹配不超过该值；95\%分位表示约95\%不超过该值，不是95\%置信区间。
\small
\begin{longtable}{rrrrrrr}
\toprule 目标 & 图片 & 匹配器 & 接受数 & 中位px & 95\%分位px & $\le10$px数\\\midrule\endhead
''' + table + r'''
\bottomrule\end{longtable}\normalsize
\clearpage
\section{公式、独立复算和不能说的话}
固定基础矩阵$F$把源点$p=(x,y,1)^T$对应到目标极线$Fp$。目标点$q$对应的另一条线为$F^Tq$。我们计算：
\[
e(p,q;F)=\frac12\left(\frac{|q^TFp|}{\sqrt{(Fp)_1^2+(Fp)_2^2}}+\frac{|q^TFp|}{\sqrt{(F^Tq)_1^2+(F^Tq)_2^2}}\right).
\]
它是两边的像素点到直线距离的平均，不是深度误差或相机旋转角误差。大距离意味着该像素对应不符合当前$F$；小距离仍可对应另一个沿极线的错误物体。因此，低残差不是完整3D正确性的证明。

root另写标量求和与手工分位数程序，没有导入原评分函数。对7757个接受匹配的原标签和固定错标签逐点复算，3655项程序断言通过；最大数值差$2.274\times10^{-13}$，固定绝对容差$10^{-8}$。断言数量不是实验样本量。第一次检查发现全特征覆盖计算保留FP32、检查器却用了FP64；保留失败记录后修正检查器口径，原实验和几何容差没有改。

不能说的话：LG更准；所有生成匹配都是错的；生成器完全不响应相机；已经发现唯一根因；已验证一种新记忆方法。正确说法是：同一已看过的场景，在两种新匹配器及固定近似相机约束下，不一致现象仍然存在。

原相机矩阵沿用S72的近似ROS内参、插值位姿和无去畸变配置。本次没有独立物理标定。新提取器和旧S73的预处理、检测、去重、描述子有差别，所以不能把旧S73对新LG称作只换匹配器。旧1150个生成匹配仍属于旧记录。

\section{导师可能追问}
\textbf{既然换工具没解决，下一步是什么？}先用事先约定的尺度检查少量具体对应，并分开检查对应可信度与请求相机几何。若需要估计新F或单应，那是新的解释性诊断，不能用拟合后的低误差替代原请求相机指标。

\textbf{创新在哪里？}目前还没有验证的新机制。新证据收窄了失败解释；创新线同时检查普通状态和后验是否已经能解决所谓旧线索遗忘。只有强基线留下真实、可复现的失败，才值得提出额外机制。

\textbf{和proposal如何对应？}本次属于基线失败刻画和测量可靠性，帮助决定第6--9周机制工作的方向。它不能替代跨场景、长序列、动态遮挡、消融和算力成本评价，也不能兑换成完整项目完成百分比。

\section{怎么回查}
项目证据目录：\path{work/S80_lightglue_observer/}。先看\path{S80_RESULTS.md}，再看\path{execution_01/ROWS.json}与运行回执，最后看\path{ROOT_RECOMPUTATION.json}。完整CSV在本增补目录。\textbf{当前没有经验证的新方法；PhD深度与CCF A要求是研究目标，尚非已取得的结论。}
\end{document}
'''
(out/'S80_真实实验增补.tex').write_text(tex)
(out/'BUILD_SOURCE_RECEIPT.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'input_sha256':hashlib.sha256((p/'execution_01/ROWS.json').read_bytes()).hexdigest(),'figure':'Vector scientific chart from all24 actual rows; no generated image data.','scope':'Later addendum; original report cutoff retained.'},indent=2)+'\n')
print(out)
