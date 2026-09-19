# PointOdyssey 已失败分支恢复：场景资产与小同步片段的区别

本次只恢复上一批未读到的官方 issue #7 评论。web接口返回URL处理失败，随后一次有界公开API请求HTTP200；不是评论原先不存在，也不是数据下载。原始4054字节JSON及请求回执保留于root_sources/。

作者身份为OWNER的2024-01-12答复称，多数3D资产由于许可不能发布，只能公开渲染结果。该答复只能解释为何不能默认取得Blender原场景并自行渲染同步视角；不证明所有资产都不公开，不否认已发布渲染序列，也不解决同步场景名单、帧号对应、K/RT/depth字段和sample归属。

另一个2024-01-11评论的作者关联为NONE，只提出Blender文件对多视角有用，不作为数据作者的证据。没有读取新图像、深度、NPZ或归档，没有模型/评分。本轮不继续对同一入口盲目尝试；并行核其它来源的最小可取参照样例。

来源：https://github.com/y-zheng18/point_odyssey/issues/7#issuecomment-1889843258 。这是作者仓库讨论，不是论文实验。更新时间使用原APIcreated_at/updated_at；本次实际访问时间见comments_receipt.json。
