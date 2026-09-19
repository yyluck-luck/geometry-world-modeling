# S15C 固定20个Bonn深度成员获取记录

生成记录：2026-09-06T10:27:54.950325+00:00。以下是实际下载、ZIP解压与字节完整性检查；本下载器没有解码PNG像素、运行模型或计算准确率。

实际UTC：2026-09-06T10:26:22.205542+00:00 至 2026-09-06T10:26:40.997314+00:00，18.791639秒。状态 **PASS**。

共41次请求尝试：40个HTTP 206成功、1个SSL transport失败；响应体总1,714,929字节，20个解压PNG合计1,870,040字节。中央目录声明20成员压缩数据合计1,712,709字节。网络响应另含40次local-header/name/extra等字节。

## 先冻结的访问范围

来源：https://www.ipb.uni-bonn.de/html/projects/rgbd_dynamic2019/rgbd_bonn_static_close_far.zip。仅取work/S15A_samples_v2/samples.json前20个history的matched depth；后4、RGB和trajectory均不获取。固定ETag `"3dab0a4b-582f1f233c9cc"`、Last-Modified `Thu, 28 Feb 2019 10:42:25 GMT`、ZIP总1,034,619,467B、中央目录起点1,034,191,580。

合同于2026-09-06T10:26:05.406430+00:00冻结，SHA `786352712c7c1940aecf32b192733b09eecdbf0fc10f4756ad4b1a68713f90ce`；精确20成员名和中央目录字段均写入合同。固定下载器、parser、inventory、sample、S15C评分协议共5个SHA；网络执行前后核验一致。

最大60请求尝试、每range最多3次、10 MiB累计响应体、600秒总预算、单成员解压2 MiB。只对SSL/connection transport问题重连；HTTP状态、范围、ETag、长度、编码或ZIP/CRC失败不重试。完成成员不得覆盖或重新获取。本次20个成员各自恰好获得1个有效header和1个有效payload；没有重下完成成员。

## 实际失败与恢复

第一次请求的local header发生SSLEOFError，响应体0字节；按预定规则重连，第2次同range成功。随后40次有效range均完成，没有修改样本、扩大预算或改成全ZIP。共创建2个HTTPSConnection对象，这不是实测TLS连接总数。失败回执和0字节响应文件原样保留。

## 20个成员、实际成功范围与SHA

下表名称前缀均为`rgbd_bonn_static_close_far/depth/`。范围为包含端点的ZIP字节区间；header和payload分请求获取。SHA对应解压后的PNG文件字节。

| index | PNG成员 | header范围 | payload范围 | PNG字节 | SHA256 |
|---|---|---|---|---:|---|
| 0 | 1548340550.98251.png | `bytes=3841527-3841556` | `bytes=3841557-3974475` | 143825 | `6ae43130d2503a8cb6b7176e3f6439779cc1427e49e69444d38ca80d2b6c26a7` |
| 1 | 1548340551.41628.png | `bytes=5307527-5307556` | `bytes=5307557-5442232` | 146058 | `1e37d4e412a55610cb24d976c9a988904ac9c3f5515e47a9da19dec762031548` |
| 2 | 1548340551.81667.png | `bytes=6806512-6806541` | `bytes=6806542-6944127` | 149044 | `220f8cb2f2b4a917c7115acfbd01bfd00df6d450cddf6f2d78793569ca3ae20a` |
| 3 | 1548340552.21714.png | `bytes=9495115-9495144` | `bytes=9495145-9638111` | 155641 | `cf240d6a9356185d16f78cfc035609cec3b9ffa135ecfb01b3baf17638c079a9` |
| 4 | 1548340552.61753.png | `bytes=11256486-11256515` | `bytes=11256516-11406832` | 163376 | `f6270ec7376d007306026626a447d100d4bf5d255386a8928850f58dd9eafdde` |
| 5 | 1548340553.01796.png | `bytes=12930945-12930974` | `bytes=12930975-13084500` | 165629 | `59c67882ee8e3bfbe38873dbe6693bef0b34ace4fed1a385e3ccc6aa96b43f99` |
| 6 | 1548340553.41838.png | `bytes=14585521-14585550` | `bytes=14585551-14717139` | 142882 | `4eda806e253e9fa377e85a9fd1df8e6d14fe1b8301df81498074f65590c45e69` |
| 7 | 1548340553.78542.png | `bytes=15775636-15775665` | `bytes=15775666-15876051` | 110337 | `f8ea5c862c9169be4a08bd380d74fa8c685abb14bd0dc89c0ec34de75f8352eb` |
| 8 | 1548340554.18583.png | `bytes=16825060-16825089` | `bytes=16825090-16893199` | 74507 | `ce116f4b800d279d0cc6cd630b8c3b5b5ecf7c7c66ea19c8375df277385d6f9a` |
| 9 | 1548340554.58633.png | `bytes=17167591-17167620` | `bytes=17167621-17174128` | 8309 | `b641030b00b3d6ad7b982bfcb4aefeb1a143980979faad6b250f3f8c20126ffa` |
| 10 | 1548340554.98674.png | `bytes=17195425-17195454` | `bytes=17195455-17196123` | 1829 | `95aad8d91b111e857329021331578f33fd079b6a27b105e88f450ad2d94f845c` |
| 11 | 1548340555.38711.png | `bytes=17204160-17204189` | `bytes=17204190-17204810` | 1791 | `a16f728c8484b15dbd0ed99b4683d9db09cbe81cdad42a2e6a5086b1781ece49` |
| 12 | 1548340555.78753.png | `bytes=17208071-17208100` | `bytes=17208101-17208294` | 1457 | `6ef65fbded4a588fe098030b5a317b7b2686c2b0c005ad7fa536455bfe49d9ea` |
| 13 | 1548340556.18789.png | `bytes=17211117-17211146` | `bytes=17211147-17212416` | 2410 | `f4c9dc7245e18cc6ae569300690fde10ede9bf1fb889f529a566f7f06b1c897b` |
| 14 | 1548340556.58829.png | `bytes=17219088-17219117` | `bytes=17219118-17221964` | 4091 | `e3ddb4881107b60a6a59e8b04857b558092bff21fda76b5e04ab68a3960184df` |
| 15 | 1548340556.98880.png | `bytes=17324773-17324802` | `bytes=17324803-17355336` | 34228 | `2265ae2260a43cc9ee9670101e4724c386b8d3dc4b6f5678d5b3742620f49048` |
| 16 | 1548340557.38920.png | `bytes=18134369-18134398` | `bytes=18134399-18226911` | 103450 | `5a70141e1d564fe990c7745459e350af3bd30fa460675e20846d01c92555d32d` |
| 17 | 1548340557.78959.png | `bytes=19320621-19320650` | `bytes=19320651-19453479` | 143921 | `800a9841a9be8ebb835823a788834c8b79621ff3ae69fcde874b61d27100a12b` |
| 18 | 1548340558.18998.png | `bytes=20941737-20941766` | `bytes=20941767-21092164` | 161946 | `fe3eba5a0edcc6b383a2c5ad91e89dceddce31af7c582c11920e61a06310dd19` |
| 19 | 1548340558.59040.png | `bytes=22570647-22570676` | `bytes=22570677-22714546` | 155309 | `2719d71516bb8e1ccdfa0266ebe6135f97c81c062a035854fb5f383fe9238672` |

## 证据与检查

下载回执：`data/bonn_s15c_depth/receipt.json`，SHA `7795b64d637175532c82e9fce2deecc603005ca8a01685554220d6cfcb85c04c`。每次HTTP头、时间、尝试号、响应SHA、成员CRC和实际文件路径均保留。原range响应在`responses/`，PNG在`members/`。

软件准备：`scripts/fetch_s15c_depth_members.py` SHA `888cdab6ba5881be02951f8738f0449026bff750aeb086940946492eaccd8c4a`；复用旧`fetch_s15_zip_members.py::parse_header/unpack_member`。21项人工transport/parser检查PASS，见`work/S15C_depth_access/artificial/receipt.json`。人工fake连接从未发实际网络请求，没有真实图像效果。

下载完成后再次逐文件读取20个PNG字节核对SHA、CRC和长度，且核对全部响应bytes之和，见`work/S15C_depth_access/byte_verification.json`；这是同一作者的字节自检，不称不同作者或新机器独立复现。

本阶段按Supervisor vibe-research-workflow的输入输出先定/小步骤/失败保留执行；按本地Claude scientific-critical-thinking分开获取、解码、传感器评分与算法效果。不调用Claude模型或CLI，不将压缩解包称图像推理。下一阶段由另行协议隔离4帧尺度校准与16帧评分，本报告不代替其实际运行和数值复核。
