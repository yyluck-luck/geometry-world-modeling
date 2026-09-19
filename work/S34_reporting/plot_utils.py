"""S34 publication-width plot settings; no scientific computation."""
COLORS=['#6B7280','#0072B2','#D55E00']
LABELS=['Zero step','Free 400 steps','Common-scale 400 steps']
FRAME_MARKERS=['o','s','^','v']
UNOBSERVED='#D9DDE2'
def configure(plt):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':9,
        'axes.titlesize':10,'xtick.labelsize':9,'ytick.labelsize':9,'legend.fontsize':8.5,
        'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,
        'savefig.facecolor':'white','figure.facecolor':'white'})
