# S32 元数据选择与暴露记录

实际元数据选择 UTC：2026-09-06T19:16:27.746289+00:00 至 2026-09-06T19:16:29.406784+00:00。规则在 2026-09-06T19:13:16.817126+00:00 先固定。

四个预定窗口保留：一个因相机时间配对缺失而阻断，未换窗或删帧；另三个只通过元数据资格，尚无图像字节封存、推理或消费者结果。

| 场景/窗口 | 原 RGB 总 N | 零基起点及四帧 | pose配对 | sensor时间配对 | 当前状态 |
|---|---:|---|---:|---:|---|
| fr2_desk_j1 | 2965 | [987, 988, 989, 990] | 0/4 | 4/4 | 阻断，保留缺失 |
| fr2_desk_j2 | 2965 | [1974, 1975, 1976, 1977] | 4/4 | 4/4 | 仅元数据可用 |
| fr1_xyz_j1 | 798 | [264, 265, 266, 267] | 4/4 | 4/4 | 仅元数据可用 |
| fr1_xyz_j2 | 798 | [529, 530, 531, 532] | 4/4 | 4/4 | 仅元数据可用 |

fr2_desk_j1 的 987–990 四帧全部没有原全序列 strict <20ms 的一对一 pose 配对；不能改用插值、放宽门限或从成功关联列表重新选起点。四个窗口都有 sensor 时间配对，不代表深度 PNG 已读或有足够有效像素。

两场景的曝光史必须分开：

- fr2_desk：已核 S21/S22 实际处理的300个配对RGB与S23实际278张sensor-depth读取回执。这次987/1974起点的8张RGB不在这份300帧清单、其sensor配对也不在该278张列表；其他早期阶段是否读过它们未知，不能称未见。
- fr1_xyz：已核S24三个实际796帧推理回执，本次两个窗口的8张RGB全部在该清单，原轨迹也已评分。S24的轨迹GT不等于sensor-depth PNG；这些深度图片的其他历史曝光仍未知。
- 两个 groundtruth.txt 的完整文本字节既往已被读取，本轮也实际读取；本轮仅选中且有配对的12行允许相机坐标被数值解析。该姿态是共同optical-c2w/oracle条件，不是纯RGB实验。
- 具体照片是否曾被人显示，以及其他协议的窗口级深度分数是否曾看过，未知。S32 尚无本轮窗口分数，不用于选择。

本轮实际读取限制：RGB图片字节0，sensor-depth PNG字节0，预测NPZ字节0，图像解码0，模型/GA0。只读取六份数据txt与历史JSON/源码/文档；图片仅检查文件是否存在，不计算内容SHA。frame.sha256 与 sensor.sha256 保持null，待后续真实字节封存。

后续接口：windows[].id/scene/frames；每帧含index(0..3)、source_rgb_index、path、rgb_time、gt_time、pose_association、sensor_depth_association、exposure；given_pose_condition给出当前实际GT文本SHA。所有路径绝对。fresh指各窗口在i=0新建状态，窗内沿原递推，不能每帧reset=True；不能复用全序列anchor的other头。

已保留一次窗口摘要标签修正：最初blocked窗口的窗口级“pose坐标已解析”字段被无条件置true，帧级字段和总计12一直正确；现改为false，原JSON/回执保存在history_before_pose_flag_annotation。未重选、未改任何帧或新增数据读取。

主清单：[selected_windows.json](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S32_selection/selected_windows.json>)；规则：[selection_rule.md](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S32_selection/selection_rule.md>)；实际回执：[selection_receipt.json](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S32_selection/selection_receipt.json>)。
