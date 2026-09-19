# S94 ALT-3RSCAN-01（3RScan官方资格门）

- **实验名称**：S94 ALT-3RSCAN-01（3RScan官方元数据、最小归档片段与RGB-D资格检查）
- **目的**：判断3RScan能否替代S93 ALT-TUM-01，作为后续S91（GRC-Pilot）或其缩小版的真实RGB-D来源。
- **执行时间**：2026-09-12（Asia/Shanghai；网络探测与文件落盘时间见 `receipts/`）。
- **执行范围**：只读官方 GitHub 仓库、官方3RScan/TUM文档和官方元数据；只下载3RScan.json（3.0 MiB）以及3RScan.v2.zip的512字节头部和65,536字节中央目录尾部。没有下载完整数据、没有填Terms of Use表格、没有运行模型。
- **证据边界**：网页/README中“提供了某字段”不等于本机已经取得并解析了每个帧；本门只验证资格和可达性，不能称为正式模型实验。

## 冻结资格问题

1. 是否有按帧组织的RGB、depth、pose，并且官方声明颜色/深度对齐？
2. 是否有6DoF相机位姿和相机内参K，及可解释的单位/坐标系？
3. 是否有同一室内环境的reference/rescan分组和场景间变换，可表达长期/重访状态？
4. 是否存在官方train/validation/test划分及测试使用限制？
5. 下载入口、许可/Terms of Use和最小可达片段是否清楚？
6. 在不下载大数据的条件下，是否至少可以证明归档内有配对帧成员，而不是只有宣传页？

## 资格判定规则

- **PASS（字段资格）**：官方原文明确提供字段，且官方元数据/仓库结构支持；
- **CONDITIONAL**：字段存在但本机还没有取得完整正文、许可或同步细节；
- **FAIL**：官方证据缺失或与需求冲突；
- **Gate0正式通过**还要求：获得合规访问授权，取得至少一个完整sequence的RGB、depth、pose、`_info.txt`，核验帧一一对应、K和单位，并冻结train/validation用途。仅有ZIP头部、目录或网页说明不能通过正式Gate0。

## 固定官方来源

1. 官方仓库（固定HEAD）：`https://github.com/WaldJohannaU/3RScan`，本次HEAD为 `12f040d3dc849e394ed366acd7b54e63acb49205`。
2. 官方README：说明1482个3D重建/快照、478个室内环境，并列出calibrated RGB-D、6DoF camera poses、K、跨扫描全局变换T和数据目录结构。
3. 官方FAQ：说明RGB-D颜色/深度已校准，深度为16-bit millimeter，pose是RGB camera到world的变换，内参位于`_info.txt`；reference/rescan由`3RScan.json`组织。
4. 官方文档：`https://vmnavab26.in.tum.de/3RScan/documentation.php`，要求通过3RScan Terms of Use表单申请下载；明确RGB-D video sequences为depth-color aligned；训练参数只能用train，test只用于最终报告。
5. 官方论文/原文入口：README引用 `https://arxiv.org/pdf/1908.06109.pdf`（RIO/3RScan）。

## 最小本机取样

- `downloads/3RScan.json`：3,155,995 bytes；SHA-256 `674a00f50f76b198b9de44efd86c390fea3da37ba8f12cf8ccd00045e265fa64`。
- 官方`3RScan.v2.zip` HEAD：HTTPS 200，`Content-Length: 39,949,975` bytes，`Content-Type: application/zip`，`Accept-Ranges: bytes`。没有下载完整压缩包。
- `downloads/3RScan.v2.prefix512.bin`：512 bytes；ZIP local header可见，首个归档根目录为`4acaebcc-6c10-2a2a-858b-29c7e4fb410d/`；SHA-256 `0e467da764ce0a01a1204137345e3d199419df49e41dc3c574d55eaa127117fd`。
- `downloads/3RScan.v2.tail64k.bin`：65,536 bytes；从归档尾部解析EOCD和中央目录；SHA-256 `7ed3e33906a22eef8b11327a61adb6465f759a8e3ccf8d37d397cfd2669f0008`。
- 中央目录显示两个scan根目录，每个161个成员：51 color、51 depth、51 pose、1 `_info.txt`、1 mesh以及其他标注/纹理文件。示例scan为`4acaebcc-6c10-2a2a-858b-29c7e4fb410d`和`754e884c-ea24-2175-8b34-cead19d4198d`。这证明归档中存在成套帧成员，但尚未解压正文。
- `3RScan.json`中两个scan属于同一个`train`场景：reference `4acaebcc-6c10-2a2a-858b-29c7e4fb410d`，rescan `754e884c-ea24-2175-8b34-cead19d4198d`，带跨扫描transform；完整场景共1个reference加7个rescan。

## 预先禁止的动作

- 不填表、不代用户接受Terms of Use、不下载完整3RScan.v2.zip。
- 不把中央目录计数当作已得到的RGB-D帧，不运行S91、不读test split用于调参。
- 不把MIT代码LICENSE当作数据集许可；数据下载与使用仍受官方Terms of Use和benchmark政策约束。
