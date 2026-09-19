# S8独立场景数据来源审查

记录：2026-09-06，Asia/Shanghai。首次检索批次的时钟锚点为01:45:57；两份压缩包的HEAD请求实际开始于01:46:49.699841/01:46:49.700125；本稿撰写前时钟为01:47:10。精确记录见同名JSON。此项只查原论文和官方文字、链接、响应头；没有下载数据压缩包、读取新RGB/depth图片、运行模型、计算结果或根据结果选场景。

建议将`rgbd_dataset_freiburg2_desk`定为第一候选。在协议冻结后再按固定时间规则取帧。它与旧`freiburg1_xyz`的物理环境和实体相机均不同，证据来自原论文，而非文件名。但它仍属于同一TUM数据集和同类Kinect传感器；不能称跨数据集或跨传感器类型验证。

## 独立性与候选比较

| 项目 | fr2/desk（优先） | fr3/long_office_household（备用） |
|---|---|---|
| 官方场景描述 | 围绕两张办公桌运动并闭环 | 在有丰富纹理和结构的家居、办公布置中绕行并闭环 |
| 物理地点证据 | 原论文§III：fr1是6×6m办公室；fr2是10×12m工业大厅，fr2/desk在动捕区域中央搭建两桌场景 | 下载页文字没有明确写出相对fr1的物理地点；本次不把场景描述差异自动升级为不同建筑/房间 |
| 实体设备证据 | 原论文§IV明确fr1和fr2各用一台不同Kinect | 序列专属官方文字明确Asus Xtion；不可被网站概览笼统的“Kinect”表述覆盖 |
| 总时长 / 官方有GT时长 | 99.36s / 69.15s | 87.09s / 87.10s；二者0.01s差别按原表保留，不解释为完全逐帧有效 |
| 官方轨迹长度 | 18.880m | 21.455m |
| 当前HTTP Content-Length | 1,893,351,095字节 | 1,483,556,251字节 |

场地与不同Kinect的依据分别为原论文§III、§IV；图2图注也将fr1/room和fr2/desk称为两个不同办公场景。本次只读论文文字，没有查看图像。地点和设备同时改变，后续即便机制重复，也不能单独归因为地点改变。[原论文](https://cvg.cit.tum.de/_media/spezial/bib/sturm12iros.pdf)

序列描述、时长与轨迹长度取自官方序列条目。fr2/desk的GT覆盖不足是已知限制，不能把99.36秒都视作有可靠参考轨迹。fr3的物理地点独立性仍有待单独原始来源确认，因此本轮不为更小文件或更长GT覆盖切换首选。[官方下载页](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/download)

## 下载来源及大小

官方页面的TGZ链接解析为：

- [fr2/desk官方入口](https://cvg.cit.tum.de/rgbd/dataset/freiburg2/rgbd_dataset_freiburg2_desk.tgz)，HEAD重定向至[官方文件服务器](https://webshare.cvg.cit.tum.de/g/rgbd/dataset/freiburg2/rgbd_dataset_freiburg2_desk.tgz)，200。
- [fr3/long_office_household官方入口](https://cvg.cit.tum.de/rgbd/dataset/freiburg3/rgbd_dataset_freiburg3_long_office_household.tgz)，HEAD重定向至[官方文件服务器](https://webshare.cvg.cit.tum.de/g/rgbd/dataset/freiburg3/rgbd_dataset_freiburg3_long_office_household.tgz)，200。

下载页概要表标2.01GB/1.58GB，序列详情标1.76GB/1.38GB；这些显示口径不一致。下载完整性应以当前HTTP字节数、下载后实际字节数和新算SHA256记录为准，不能拿四舍五入的GB文字代替完整性检查。HEAD只核对响应头，不证明压缩包内容完整，也未获得官方SHA256。官方Last-Modified分别为2011-09-30 15:17:05 GMT、2012-08-07 18:51:42 GMT；这是服务端文件时间，不是本次实验时间。

## 相机与深度：建议冻结的实现约定

官方PNG为640×480；RGB为8位三通道，depth为16位单通道。OpenNI已把depth注册到RGB坐标，空间像素一一对应；这不表示两路拍摄时间完全相同。PNG深度`Z = raw / 5000.0`米，0为缺失；`Z`按官方反投影代码是相机坐标的轴向深度。fr2原深度尺度修正1.031已由数据提供方应用，不能再乘或除一次。[文件格式与标定](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats)

| 用途 | fx | fy | cx | cy | 畸变d0…d4 |
|---|---:|---:|---:|---:|---|
| 本轮建议：官方推荐ROS默认近似 | 525.0 | 525.0 | 319.5 | 239.5 | 0, 0, 0, 0, 0 |
| fr2 RGB的独立标定记录，保留元数据 | 520.9 | 521.0 | 325.1 | 249.7 | 0.2312, −0.7849, −0.0033, −0.0001, 0.9172 |
| fr3 RGB的官方已去畸变参数，备用信息 | 535.4 | 539.2 | 320.1 | 247.6 | 0, 0, 0, 0, 0 |

官方明确推荐对预注册数据使用ROS默认参数且不另行去畸变，因为对已注册depth进行去畸变并不简单。默认525是官方推荐的近似，不应称精确真内参；fr2标定表也不能被当作“只换四个数即可完成完整校正”。不要用IR内参反投影已注册depth，或只对RGB去畸变而保留原depth位置。fr3另有已去畸变说明；若日后选择fr3，应单独冻结内参约定，不照搬fr2方案。[官方标定说明](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats)

代码建议属于本审查的实现判断：原尺寸先使用上述默认K，预测几何和测量评分共用同一个已记录的图像坐标约定；resize/crop后按实际像素变换A更新`K' = A K`。不要只缩放焦距而忘记主点和裁剪偏移；沿用已验证的resize/crop实现，并在输入清单保存原K、实际变换和最终K。测量深度的重采样沿用冻结的有效值/遮挡规则，避免临时改变边界处理。旧S4–S7保持原记录，不为本轮改动而重写。

## 时间、位姿与许可

数据集名义RGB-D采集率30Hz，动捕GT为100Hz。GT文件每行格式为`timestamp tx ty tz qx qy qz qw`；时间戳是Unix秒，位置及单位四元数描述RGB相机光心相对动捕世界坐标系的位姿。因此解释为相机到世界变换；具体时间间隔和缺口必须下载后按数值核查，100Hz不是“无缺失”的保证。[数据集主页](https://cvg.cit.tum.de/data/datasets/rgbd-dataset)、[位姿格式](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats)

官方提供按时间戳匹配RGB/depth的工具，印证两路列表需要关联。建议在看任何模型输出之前冻结：配对容差、GT相邻样本最大允许缺口、边界排除规则、插值方式、按时间而非效果选块的规则。不要跨大段GT缺失做插值，也不要失败后改挑“更好看”的另一段；fr2实际足够多少完整窗口本次未知。[官方关联工具说明](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/tools)

当前官方网站写数据默认CC BY 4.0、配套代码BSD-2-Clause，并要求引用Sturm等2012论文。2012原论文写当时为CC BY 3.0；两者是时间不同的来源记录，不抹掉历史差异。本轮来源清单按当前官网许可说明记录，并保留作者/论文/数据链接；如压缩包内出现更具体许可，归档时另行记录。[当前许可](https://cvg.cit.tum.de/data/datasets/rgbd-dataset#license)、[2012论文](https://cvg.cit.tum.de/_media/spezial/bib/sturm12iros.pdf)

## 未核实边界与下一步

未下载，因此实际RGB/depth数量、配对数、有效GT窗口、深度缺失率、包SHA256、包内README/许可均未知。没有新图片QA，也没有任何新场景实验或视频生成结果。新的场景只增加一个环境，不构成广泛泛化证据；Kinect深度、标定和动捕轨迹仍带测量误差。

下一步由父任务在查看新图片/输出前冻结S8协议；协议应明确首选fr2/desk、元数据失败处理、固定采样与评分规则，然后下载并做文件/时间戳层面检查。若fr2无法满足预先规定的可评估条件，记录失败并另立修订，不能按新结果改选备用序列。
