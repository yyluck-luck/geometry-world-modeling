RGB-D Scenes Dataset v.2

The RGB-D Scenes Dataset v2 consists of 14 scenes containing furniture (chair, coffee table, sofa, table) and a subset of the objects in the RGB-D Object Dataset (bowls, caps, cereal boxes, coffee mugs, and soda cans). Each scene is a point cloud created by aligning a set of video frames using Patch Volumes Mapping*. These 3D reconstructions and ground truth object annotations are exactly those used in our ICRA 2014 paper.

The files are named as follows:
<scene>.ply - A 3D point cloud stored in PLY format ( http://en.wikipedia.org/wiki/PLY_(file_format) ). This can be opened for visualization with, for example, Meshlab ( http://meshlab.sourceforge.net/ ). We have also included third party MATLAB code written by Pascal Getreuer for reading and writing PLY files.
<scene>.pose - The camera poses for each constituent frame estimated by RGB-D Mapping, where each line is the camera pose (a,b,c,d,x,y,z) for one video frame. a,b,c,d is the camera orientation expressed as a quarternion, and x,y,z is the camera position in the global coordinate frame. The camera pose of the first frame of each video is always the origin of the global coordinate frame.
<scene>.label - The object labels of each 3D point in the scene. The first number is the number of points in the scene. This is followed by the labels (bowl=1, cap=2, cereal_box=3, coffee_mug=4, coffee_table=5, office_chair=6, soda_can=7, sofa=9, table=9, background=10) of every point, in the same order as they appear in <scene>.ply.


MATLAB code example for transforming 3D points of a video frame into the global coordinate frame:
Supposing "poses" is a Nx7 matrix storing the camera poses of the N video frames, the following code snippet will transform a set of 3D points from the depth image "depth" of the i-th video frame into the global coordinate frame.

pcloud = depthToCloud(depth);
pts = reshape(pcloud,size(pcloud,1)*size(pcloud,2),3);
pts = bsxfun(@plus,poses(i,5:7),quatrotate([poses(i,1) -poses(i,2:4)],pts));

*Patch Volumes: Segmentation-based Consistent Mapping with RGB-D Cameras
P. Henry, D. Fox, A. Bhowmik, R. Mongia, International Conference on 3D Vision (3DV), 2013.


Please cite the following paper if you use this dataset:

Unsupervised Feature Learning for 3D Scene Labeling 
Kevin Lai, Liefeng Bo, and Dieter Fox 
IEEE International Conference on Robotics and Automation (ICRA), May 2014.


Acknowledgements: Special thanks to Peter Henry for helping with the data collection and 3D reconstruction.


