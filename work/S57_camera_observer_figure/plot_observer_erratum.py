from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent
source=R/'work/S57_coordinate_convention_audit/ALL_30_SOURCE_D_CORRECTION.json'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='31e937ae4a3b6ed8b4569db5459e7fc71c830402c1ae457b7eee994a2914c9c5'
data=json.loads(source.read_text());tau=data['thresholds_unchanged']['residual_limit_px']
OUT=R/'results/S57_observer_erratum_figure';OUT.mkdir()
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9,'axes.labelsize':8,'xtick.labelsize':8,'ytick.labelsize':8,'svg.fonttype':'none','pdf.fonttype':42})
fig,axs=plt.subplots(2,2,figsize=(7.1,5.9),gridspec_kw={'height_ratios':[1.1,1]},sharex='col')
handles=None
for col,row in enumerate(['B0','C1']):
    pairs=data['rows'][row];x=np.arange(15);labels=[f'{p["pair"][0]}–{p["pair"][1]}' for p in pairs]
    old=np.array([p['old_requested_residual_px'] for p in pairs]);identity=np.array([p['identity_residual_px'] for p in pairs]);new=np.array([p['corrected_requested_residual']['cell_balanced_median_px'] for p in pairs])
    assert max(new)<6
    for ax in axs[:,col]:
        ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',color='#e5e5e5',lw=.6);ax.set_axisbelow(True);ax.set_xlim(-.6,14.6)
        for idx,p in enumerate(pairs):
            if p['corrected_verdict'].startswith('UNKNOWN'):ax.axvspan(idx-.43,idx+.43,color='#eeeeee',zorder=-1)
        ax.set_xticks(x,labels,rotation=90)
    a=axs[0,col]
    h1=a.scatter(x,old,c='#777777',marker='x',s=22,label='Old observer: missing axis conversion',zorder=4)
    h2=a.scatter(x,identity,c='#D55E00',marker='s',s=15,facecolors='none',label='Identity / static reference',zorder=3)
    h3=a.scatter(x,new,c='#0072B2',marker='o',s=14,label='Source-derived corrected request',zorder=5)
    handles=[h1,h2,h3];a.set_ylim(0,115);a.set_yticks([0,25,50,75,100]);a.set_title(f'{row} · all 15 fixed pairs',loc='left',fontweight='bold')
    b=axs[1,col];b.scatter(x,new,c='#0072B2',marker='o',s=18,zorder=4)
    b.axhline(tau,color='#222222',ls='--',lw=1);b.set_ylim(0,6);b.set_yticks([0,1.5,3,4.5,6]);b.set_title('Corrected request · enlarged 0–6 px scale',loc='left')
    for idx,p in enumerate(pairs):
        flag='U' if p['corrected_verdict'].startswith('UNKNOWN') else ('E' if p['corrected_verdict']=='IDENTITY_ENDPOINT_ONLY' else 'C')
        b.text(idx,5.62,flag,ha='center',va='center',fontsize=8,color='#444444')
    b.set_xlabel('Fixed frame pair (all retained)')
axs[0,0].set_ylabel('Balanced symmetric residual (px)')
axs[1,0].set_ylabel('Balanced symmetric residual (px)')
fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.51,1),ncol=1,frameon=False,fontsize=8)
fig.subplots_adjust(top=.83,bottom=.23,hspace=.3,wspace=.24,left=.10,right=.98)
fig.text(.10,.12,f'Dashed line: frozen single-texture threshold τ = {tau:.3f} px.\nC = nominal consistency on matched support; U = unknown; E = return endpoint only.\nGrey bands retain every unknown. Residual alone does not override coverage checks.',fontsize=8,va='top')
for extension in ['png','svg','pdf']:fig.savefig(OUT/f'observer_coordinate_erratum.{extension}',dpi=200,facecolor='white')
caption='''相机坐标转换的漏项造成了旧观察器的方向异常。上排保留两个视频的全部30个固定帧对，比较旧请求残差、静止参考和按生成源码修正后的请求残差；下排使用明确标出的0–6px放大尺度，并保留所有无法判断的帧对。B0修正后13对在单纹理阈值及匹配区域内一致、1对不确定、1个返回端点；C1为14对不确定、1个端点。误差为全部相互匹配点双向传输误差的源网格均衡中位数，单位像素；这属于结果暴露后的保存对应点复算，未改生成模型、原始MSE、配对或阈值，不是独立相机标定、三维正确性或新方法收益。'''
(OUT/'图注与解释.md').write_text('# 相机观察器勘误图\n\n'+caption+'\n\n灰色背景和U都表示无法判断；不能因修正后残差较低就删除这些结果。原始结果与全部9350个保存对应点的修正记录均保留。C/E也不是整段视频或整个三维场景正确的判定。图中没有新拍摄或新生成图片。\n')
receipt=dict(created_utc=datetime.now(timezone.utc).isoformat(),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),pairs_plotted=30,
 generated_pixel_reads=0,new_model_calls=0,all_unknowns_retained=True,dimensions_inches=[7.1,5.9],minimum_font_pt=8,
 top_axis_limits=[0,115],lower_axis_limits=[0,6],lower_scale_explicitly_labelled=True,
 outputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir()},visual_review='PENDING_ROOT_IMAGE_INSPECTION')
(OUT/'PLOT_RECEIPT.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'output':str(OUT),'created_utc':receipt['created_utc'],'pairs':30},ensure_ascii=False))
