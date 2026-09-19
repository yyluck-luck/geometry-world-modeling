# S71数据集适用性勘误

实际记录UTC：2026-09-09T06:34:51.501477+00:00。

S69冻结INPUTS.json全部9条RGB路径与GT路径均属于TUM Freiburg2 desk。S71检索的Freiburg1官方参数本身有来源，但将fr1标定讨论延伸为本项目当前输入前提是错误的；相关当前入口与S71报告须以本勘误为准。原S71来源文件和交付快照保留。

实际Freiburg2 RGB官方640×480参数为fx=520.9, fy=521.0, cx=325.1, cy=249.7；畸变=(0.2312,-0.7849,-0.0033,-0.0001,0.9172)。S70实际生成仍采用既有近似ROS K及原裁剪；本轮不会偷偷替换参数。官方值不是本机实测标定，也不证明旧生成错误由K造成。[TUM官方参数表](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats)

此勘误修正来源对本地数据的适用性，不改变S70生成/评分或S71特征位移数值。这些计算没有使用fr1标定。S72先检验既有近似K在真实fr2照片上的固定几何残差。

独立来源核查：innovation_sources_02/FR2_AND_EPIPOLAR_BOUNDARY.md及SOURCE_READ_RECEIPT.json；root实际复读S69路径和TUM官方参数行，未从模型答复猜测数据集。
