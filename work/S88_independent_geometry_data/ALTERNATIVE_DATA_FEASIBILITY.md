# S88 两种替代数据的最小访问可行性

**本岗结论：优先保留 RTMV，等待有界归档元数据探针；不把 TinyNeRF 的小体积当作几何评分资格。** 本批仅核 RTMV 和原作者 NeRF synthetic/TinyNeRF 两种来源，未取得任何目标 RGB、深度或模型，未做新实验。RTMV 的发布元数据与参考读取代码已取得；相机 JSON 的实际小样例仍由 root 的独立 Range 探针核实，本文件不提前宣称可用。

本批先读项目 AGENTS、原则、当前 memory/log、S88/SCOPE 和 S87/NEXT_DATA_ACCESS_CHECK_02；在 work/docs/data 的 Markdown 中定向查 RTMV、NeRF synthetic、DTU、TinyNeRF，未发现可复用记录。PointOdyssey #7 恢复由 root 负责，本岗未重复访问。网络明细、HTTP 失败与原字节保存在 `alternatives/`；截止时间及字节统计见该目录 MANIFEST.json。没有打开网页图片、图片链接、EXR、NPZ 或大包，也未显示任何新目标。

## 1. RTMV：几何内容最贴合，最小单文件入口尚待证实

**来源身份。** [论文](https://arxiv.org/html/2205.07058)第一作者为 Jonathan Tremblay；[HF 作者页](https://huggingface.co/TontonTremblay)指向其个人网站，[同名 GitHub 公共资料](https://api.github.com/users/TontonTremblay)列名 Jonathan Tremblay/NVIDIA。其 [RTMV 数据卡](https://huggingface.co/datasets/TontonTremblay/RTMV/blob/main/README.md)明确说明旧站失效后的重新上传。这构成作者账号重发布的来源链；没有拿第三方格式转换包冒充原始数据。

| 核验项 | 已有证据与尚未知的边界 |
|---|---|
| 数据性质 | 论文描述 NViSII 光线追踪、固定场景的多视角渲染；各场景先归一化至单位立方体。它是模拟器参考，不是实拍传感器标定，也不是 SfM 位姿估计。原始资产可能来自实物扫描，但渲染相机仍属于模拟器。 |
| 标签 | 论文列 depth/distance、alpha、segmentation、场景点云、相机及实体位姿等；同一场景的不同视角可用于静态几何问题。**具体归档的对象不变性、帧号配对、实体/点 ID schema 尚未读到。** 静态场景不要求物理多相机同时曝光，但不能由文件名编造同步时间戳。 |
| 深度与单位 | 论文只称 depth/distance。NViSII 官方 `render_data` 定义 depth 为相邻路径顶点间距离；bounce=0 对应直接可见表面。因此它提示射线 range 语义，**尚须核归档导出时的 bounce、采样中心、通道与空背景值，不能直接认定为 camera-Z**。归一化场景单位不能写成米。 |
| 相机 schema | NVIDIA Kaolin Wisp 的 RTMV 读取器使用 `camera_data.camera_look_at.{eye,at,up}`、`width/height`、`intrinsics.fx/fy`；其注释说明 JSON `cam2world` 与 Kaolin 的列向量变换须转置对应。它说明世界使用 Blender 的 Z-up；这不表示相机局部也以 Z 朝上。具体 JSON 的 `cx/cy`、矩阵方向、像素原点还需实际核对。 |
| 划分 | 论文的单场景方案为 150 视角中 100 train、5 val、45 test；另有跨场景划分。Wisp 按排序文件及比例切分。**未取得本包的精确场景名单/视角清单，不把论文比例冒充本次已冻结划分。** 当前 VMem/CUT3R 等是否训练见过这些场景未知。 |
| 数据许可 | 重发布 README 明列 CC BY-NC 4.0。它是本次发布者明示的数据许可；未审归档内可能附带的其他条款或资产许可。论文的 arXiv 许可、Wisp 软件许可都不能替代数据许可。 |

上表的论文信息来自 [RTMV 第3、5节](https://arxiv.org/html/2205.07058)；depth 的 API 含义来自 [NViSII 官方说明](https://nvisii.com/visii.html#nvisii.render_data)；schema/转换来自 [固定提交的 Wisp 读取器](https://github.com/NVIDIAGameWorks/kaolin-wisp/blob/931707e50f1511fdb4af55eeb4aed4df23b7c2b1/wisp/datasets/formats/rtmv_dataset.py#L452)。**读取器是官方实现证据，不代替本包实际导出器。** 不照搬它按深度重新中心化/缩放、固定主点偏移、深度筛选或颜色转换作为本研究的默认处理。

### 已取得的精确发布接口

[HF 仓库元数据](https://huggingface.co/api/datasets/TontonTremblay/RTMV)实际 HTTP200：commit `855627f73a6fdd4db7fa150097a576f6e890c569`，57个 sibling；全部为 README、gitattributes、tar或tar分片，没有独立相机 JSON/EXR 路径。`all/` 下也有子目录，但 repo 的全 sibling 列表已列其中归档。两次单独子目录请求发生 TLS 错误并保留，不能将失败说成空目录。

根级 [tree API](https://huggingface.co/api/datasets/TontonTremblay/RTMV/tree/main?recursive=false&expand=false)列出：

| 文件 | 发布大小（B） |
|---|---:|
| abc.tar | 12,064,450,560 |
| amazon_berkeley.tar | 32,552,171,520 |
| bricks.tar | 16,453,795,840 |
| google_scanned.tar | 16,223,395,840 |

`abc.tar` 的发布 LFS SHA256 为 `7340c023e0e2d15c557ab8f80b40fc557ee00aa91f1454e8d556d2944c73de28`，Git blob ID 为 `d36b6cf21d95aaae448d50c7726175e3cc2465ec`。这是发布元数据的内容标识，**未对整个归档重新下载计算 SHA**。

可按 HF 公开接口构造固定版本地址：

`https://huggingface.co/datasets/TontonTremblay/RTMV/resolve/855627f73a6fdd4db7fa150097a576f6e890c569/abc.tar`

本岗没有请求这个大归档地址。root 已接手独立的最小 Range 探针：先验证206及偏移，再有限读取成员头、跳过 EXR 数据，寻找小 JSON；拒绝服务器返回200整包。本岗只交付候选及身份，不声称已经找到 JSON；`.tar` 扩展名也不替代未压缩 tar 魔数/头格式核验。该路径若成功，可避开为一个样例下载12 GB；若失败，保留阻断，不扩大整包下载。

**实际小样例进入评分前最少还缺：** 同一场景两个固定视角的相机 JSON、同 basename 的 RGB/depth 成员身份；相机与 ray-range 的投影定义、像素中心及无效值；静态实体身份一致和划分。只先做元数据闭合，不据新目标画面挑“看起来好”的场景。

## 2. 原 NeRF synthetic / TinyNeRF：小入口确认，几何真值不充分

[NeRF 原作者仓库](https://github.com/bmild/nerf)提供 [download_example_data.sh](https://github.com/bmild/nerf/blob/master/download_example_data.sh)，脚本首项是 UCSD 托管的 `tiny_nerf_data.npz`；后面的完整示例 zip 不属于本次下载对象。脚本首项使用 HTTP，本岗只对同主机路径的 HTTPS 发了 **HEAD**。

实际响应 HTTP200，`Content-Length: 12727482`、`Accept-Ranges: bytes`、`Last-Modified: Thu, 21 Jan 2021 15:40:04 GMT`，即 12,727,482 B。文件地址：

`https://cseweb.ucsd.edu/~viscomp/projects/LF/papers/ECCV20/nerf/tiny_nerf_data.npz`

HEAD 的 curl 因预设1 MiB `--max-filesize`看到较大的声明长度后返回63；这是**已收到头、正文未下载**，不是成功下载文件。保留原头/返回码；不把服务器 ETag 当文件 SHA。作者入口成立，但实际 NPZ schema、字段形状、每帧身份及文件内容 SHA 都未读，不能宣称已验证106帧或具体100px形状。本批不引用第三方 TinyNeRF 实例的形状来替代原文件核验。

原始 [NeRF synthetic 论文第6.1节](https://arxiv.org/html/2003.08934)描述8个静态物体的路径追踪图像及100输入/200测试视角；这是标准全分辨率数据的论文设置，**不是已核 TinyNeRF 小包划分**。[原 README](https://github.com/bmild/nerf#already-have-poses)明确相机局部 OpenGL：x向右、y向上、z向后，矩阵是 camera-to-world。`run_nerf_helpers.py` 的射线方向为 `[(u-W/2)/f, -(v-H/2)/f, -1]`，中心约定是 `W/2,H/2`。原 [Blender loader](https://github.com/bmild/nerf/blob/master/load_blender.py)由 `camera_angle_x` 和宽度计算焦距，并读取各 split 的 `transform_matrix`。这些说明可支持相机接口设计，不能把 NeRF 针对实拍的 COLMAP/LLFF 路线混成精确模拟器相机。

**不足。** 本次没有证实 Tiny 包带有参考深度、表面点身份、分割或米制尺度；原 loader 也未读取这些几何评分字段。单一熟知场景与现有模型训练的重合未知。仓库 LICENSE 是 MIT 软件许可，未核到独立的数据/Blend Swap 资产授权，不宣称下载后可任意再分发。因此仅记为“小规模相机/RGB接口候选”，不作为本次需要可信几何评价的替代终点；root 已明确暂不下载。

## 本批实际产物和决定

原响应见 `alternatives/*.body`；每次请求保留 `*.headers` 与 `*.receipt.json`，包括3次 TLS失败和 HEAD 返回63。Wisp固定源码 SHA为 `8ea3153554c5d246d4132c2272a66772f1ae8dc74ed27e96ed7d1316fcb5ac23`，仅阅读，未导入/执行。网页检索用于定向发现和原文核读，下载预算审计以实际保存HTTP响应为准，搜索服务内部传输字节不可见、不伪造计量。受控获取远低于20 MiB；0新RGB/深度/模型正文，0训练/生成/评分。

下一步只等待 RTMV 的归档元数据能力结论。即使得到可靠相机/深度，也只是建立独立评价资料的条件；没有选择新方法、没有创新验收，也不将数据访问成功当科研贡献。
