"""Shared S32 scientific figure style, no experiment execution."""
PALETTE=['#0072B2','#D55E00','#009E73']  # Okabe-Ito colour-blind-safe subset
MARKERS=['o','s','D']
FIGSIZE=(7.2,5.9)  # Intended two-column insertion at native width: minimum font 8.5 pt.
def configure(plt):
    plt.rcParams.update({'font.family':'DejaVu Serif','font.size':9,
        'axes.labelsize':9,'axes.titlesize':10,'xtick.labelsize':8.5,'ytick.labelsize':8.5,
        'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none',
        'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,
        'savefig.dpi':300,'path.simplify':False})
