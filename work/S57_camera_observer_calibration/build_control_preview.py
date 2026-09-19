"""Contact sheet from already-generated S57 mathematical controls only."""
from pathlib import Path
import cv2
import numpy as np

D=Path(__file__).resolve().parent
names=['yaw_-5','yaw_-1.25','static','yaw_+5','yaw_+1.25','blurred_static']
canvas=np.full((740,936,3),245,np.uint8)
cv2.putText(canvas,'S57: synthetic 2D camera controls from ONE TUM texture',(12,30),cv2.FONT_HERSHEY_SIMPLEX,.7,(20,20,20),2)
cv2.putText(canvas,'Known artificial K; not real novel views or model outputs',(12,57),cv2.FONT_HERSHEY_SIMPLEX,.58,(40,40,40),1)
for i,name in enumerate(names):
    rgb=cv2.imread(str(D/'controls'/(name+'.png')))
    assert rgb is not None and rgb.shape==(576,576,3)
    thumb=cv2.resize(rgb,(288,288),interpolation=cv2.INTER_AREA)
    x=12+(i%3)*312;y=85+(i//3)*325
    canvas[y:y+288,x:x+288]=thumb
    cv2.putText(canvas,name,(x,y+310),cv2.FONT_HERSHEY_SIMPLEX,.65,(20,20,20),1)
cv2.imwrite(str(D/'CONTROL_PREVIEW.png'),canvas)
