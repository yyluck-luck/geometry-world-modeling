# 下一阶段数据候选：TUM freiburg1_xyz

2026-09-05 由独立审查核查官方资料，尚未下载数据。

选择理由：序列约30秒，主要是相机平移，官方推荐用来初次调试；RGB、深度和相机轨迹可支撑CPU回投与坐标验证。[官方序列说明](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/download#freiburg1_xyz)

体积需明确：完整压缩包 HTTP HEAD 返回 448,204,271 字节（约427.44 MiB）。这是完整包体积，不能把“只分析24帧”误写成只需下载几MB。[下载入口](https://cvg.cit.tum.de/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_xyz.tgz)、[实际文件地址](https://webshare.cvg.cit.tum.de/g/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_xyz.tgz)。下一轮先确定提取和存储方式，再记录下载时间、体积及文件哈希。

## 坐标与时间检查

- 640×480 的RGB与已配准深度；16位深度PNG除以5000得到米，0为缺测。
- Freiburg1深度尺度1.035修正已经应用，不可再次乘。
- 初次回投参考官方建议的ROS default参数：fx=fy=525，cx=319.5，cy=239.5；不额外去畸变。官方亦提供相机标定表，使用哪套参数和处理路径必须记录。
- 位姿按 `timestamp tx ty tz qx qy qz qw`；彩色相机光心相对mocap世界系。回投使用光学相机x向右、y向下、z向前，接VMem需遵循其翻轴约定。
- RGB、深度、轨迹时间戳不能靠文件序号配对。保存匹配误差和插值策略；官方工具的RGB-D关联默认最大间隔20ms。

依据：[官方格式与标定](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats)、[官方处理工具](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/tools)。

## 最小下一步与证据边界

先抽24个时间匹配观测，降采样深度，验证回投、相机变换和重投影；再用这些观测构建小型记忆，比较干净记录与人工扰动。先处理无效深度、时间不同步和遮挡，不能把这些实现误差归因于研究机制。

深度是Kinect测量，有噪声与缺失；mocap轨迹是数据集提供的位姿ground truth。回投出来的点云不是无误差的几何真值。[官方数据集介绍](https://cvg.cit.tum.de/data/datasets/rgbd-dataset)

这仍不能替代CUT3R自然误差穿过原版清理的实验：Kinect深度没有CUT3R置信度。因此S2的第一目标应是“真实测量上的几何/坐标/记忆接口验证”，之后另接CUT3R导出或完整上游回放，再评价门控。
