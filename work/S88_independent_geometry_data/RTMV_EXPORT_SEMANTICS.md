# RTMV 导出语义：作者源码已支持的部分与仍未知的部分

**结论：找到作者公开的 NViSII 多视角生成源码，能直接支持 bounce=0、深度在像素中心采样、RGB在整像素内采样，以及相机矩阵逐列写出的解释；EXR真实通道、纵向行顺序和背景无效值仍不能由本次三份文件确定。** 这比从 Wisp 读取后的处理倒猜原始数据更直接，但不能宣称已证明 HF 归档由当前源码提交生成。

本批 UTC 2026-09-11 01:01:32 开始；只新增3个小源码/树请求，均HTTP200，共166,615 B；另1次定向搜索工具调用（2条查询）仅发现作者仓库。未请求图像、深度、NPZ、模型；未导入生成代码、未运行渲染。源码与请求回执在 `alternatives_export/`。读取 root 的 `rtmv_range_02/CAMERA_FIELDS.json` 只作相机字段兼容核对，未打开隔离的完整 JSON 或分析 objects、场景包围盒。

## 来源和身份

- 原论文：[RTMV](https://arxiv.org/html/2205.07058)，已有本地原文 `alternatives/rtmv_paper.body`。
- 作者仓库：[TontonTremblay/nvisii_mvs](https://github.com/TontonTremblay/nvisii_mvs)，作者账号身份已在上一批核过。固定树提交 `e1050ed2b0635890dec00c007ebae2259f1022e2`；本次没有取得将它与 HF `abc.tar` 构建版本绑定的生成回执。因此称“作者公开生成源码”，不把“作者当前版本”写成“归档精确构建版本”。
- [render.py](https://github.com/TontonTremblay/nvisii_mvs/blob/e1050ed2b0635890dec00c007ebae2259f1022e2/render.py)：36,629 B，SHA256 `9f85b8f37b426e741f9d61f3c85724584dd4731eee94abd3b45b8dd63b1e72bd`。
- [utils.py](https://github.com/TontonTremblay/nvisii_mvs/blob/e1050ed2b0635890dec00c007ebae2259f1022e2/utils.py)：123,625 B，SHA256 `97c2763ec392450a7e1c7be5de9d3efd1be2232339c20d08444f9788452cb7c2`。
- API 树6,361 B，SHA256 `f1c1652aec173b3e7476a205a5c6ef7ec6ce63ac11178bf4c985017ddd50173e`。三份均保存原字节；本岗没有再请求第4份源码、README或底层渲染器。

## 可以直接从生成代码确认什么

| 问题 | 原始代码证据 | 可采用的解释与边界 |
|---|---|---|
| depth 的 bounce | render.py 958–966：`render_data_to_file`，`start_frame=0`、`frame_count=1`、`bounce=0`、`options="depth"`。 | 本源码导出相机直接可见路径段的 depth，不是 bounce=1 的反射/折射之后路径段。这个参数不是“RGB只反射0次”；RGB仍由独立渲染调用决定。 |
| 深度采样位置 | render.py 925–928 先设 x/y sample interval 为(.5,.5)，随后写 JSON/depth/seg；978–981 才复原(0,1)。 | 官方 `sample_pixel_area` 文档将(.5,.5)明确称像素中心；深度和分割按该点采样。最后 RGB 用整个像素区域采样，所以几何边缘的 RGB 可为多表面抗锯齿混合，不能要求它严格对应一个中心深度。 |
| range 还是 camera-Z | 上述 `options="depth"` 连同已有 NViSII `render_data` 文档：“相邻路径顶点间的距离”；bounce=0 是直接可见表面。 | 支持把该源码导出的值解释成相机射线距离；不能直接使用 `X=Z K⁻¹p` 而省略射线归一化。相机 aperture/底层光线起点仍由运行配置/实现决定，本批未绑定归档配置。 |
| 文件与帧号配对 | render.py 946–975 写同一个五位编号的 `.json`、`.depth.exr`、`.seg.exr`；最终RGB由同编号加 `cfg.file_format` 写出。 | basename 给出了该源码的配对规则。`i_frame` 是循环编号，`start_frame` 是渲染API的种子起点，均不能冒充物理曝光时间。实际归档成员存在性由 root 单独核。 |
| 相机 view/c2w 来源 | utils.py 1884–1895 取 `get_world_to_local_matrix()`；1909–1912 取 `get_local_to_world_matrix()`；1953–1954 写入 `camera_view_matrix`、`cam2world`。 | 代码逐外层元素再写四个分量，没有显式转置；变量名 `row` 不能证明外层真是数学行。函数前的投影代码用矩阵乘列向量，平移从 `mat_trans[3][0:3]` 取得，说明该接口以外层索引列。JSON按普通二维数组读取时，应将它转置后用于列向量乘法。 |
| 内参与位姿辅助字段 | utils.py 1901 调用 `get_intrinsic_matrix(width,height)`；1965–1972 分别取fx=[0][0]、fy=[1][1]、cx=[2][0]、cy=[2][1]；同时写eye/at/up、location和xyzw quaternion。 | 应读取真实fx/fy/cx/cy，不照搬Wisp将主点偏移置0的包装表示。元数据有多种表示可相互核验；本岗未重算 root 正在独立核的矩阵误差。 |

NViSII API 解释依据本地既有 `alternatives/nvisii_depth_docs.body` 365–404、440–450 行，对应 [官方 depth/bounce 文档](https://nvisii.com/visii.html#nvisii.render_data)及[像素采样文档](https://nvisii.com/visii.html#nvisii.sample_pixel_area)。这里只用API解释实际调用，不把API默认值当作本数据已经使用的参数。

## 实际相机 JSON 提供了怎样的交叉证据

root 已取得 scene `00000` / view `00108` 的相机字段。实际值为 width=height=1600，fx=fy=1931.371337890625，cx=cy=800；`camera_look_at` 的 `up=[0,0,1]`，两矩阵的平移都在 JSON 最后一个外层列表中，`cam2world` 的该位置与 `location_world` 一致。这与作者源码的列表写法相容，也与先前 Wisp 对转置的注释相容。

列向量代码的候选读法是 `C = array(cam2world).T`，`V = array(camera_view_matrix).T`。root和不同作者正在核 C/V逆关系、eye/look-at及坐标轴，本文件不把这项数值核验写成自己已完成。世界up字段不能代替相机局部轴；文件中的巨大 `scene_*_3d_box` 也没有在这里解释为归一化尺度或米制边界。

## 本次不能确定的三项

1. **EXR通道名、dtype和行顺序。** 生成脚本将`options="depth"`直接交给NViSII文件写出，没有定义EXR底层通道名、翻转和量化。不能用Wisp的`default[...,0]`或其读取结果倒推全部归档一定采用同一通道。未读任何EXR头或正文。
2. **背景/未命中的值。** render.py与相关export函数没有显式改写背景深度的分支。本次未读NViSII底层miss shader/EXR写入器，不能写背景必为0、−1、∞或某个极大数；Wisp的±1000筛选只是读取处理，不是原始标签定义。
3. **归档精确生成配置与底层版本。** 当前作者脚本支持可动光源，不能仅凭通用脚本断言所有帧光照固定；循环内没有显式推进物体物理运动，但具体归档的配置/对象静态性不由此自动认证。没有归档生成commit、NViSII版本、aperture/时间采样设置。此处不要求凭空补造历史回执，只如实保存来源强度，并用后续固定数据的必要核对约束解释。

这三项不阻止当前只读相机 JSON 的解析。后续若真要用深度作几何评分，最低必要工作是先确认真实EXR的通道/行序/未命中规则，并固定中心射线与range反投影约定；不要通过新目标RGB的效果调符号、翻转或无效值阈值。读取底层官方实现若需新增请求，应另给一个有界批次，不能把本次三请求预算默默扩展。

**本次状态：SOURCE_SUPPORTED_EXPORT_CONVENTIONS；RAW_EXR_INVALID_AND_LAYOUT_UNVERIFIED。** 没有新生成、没有新评分，也没有创新验收。
