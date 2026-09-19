# S34：实现完成，等待最终身份核对后执行

记录UTC：2026-09-06T21:35:08.289795+00:00。状态：SOURCE_IMPLEMENTED_PRE_REVIEW_CLOSING；尚无S34科学执行。

固定已有fr2首8帧，共用S29较强old4预测；比较old_fixed_zero/free400/common_scale400。GA producer、原地图追加/渲染/来源票权consumer、固定12行评分源码均完成；consumer与scorer不同作者源审PASS，producer全文审无阻断，最后23来源身份与AST核对中。

正式运行将新增2MST/14PnP/800Adam与4次clean、0模型。之后原kernel建立共同旧图一次、三次深拷贝仅追加新4，并原512×288自查询渲染/来源票权。最终默认context与视频仍未运行，不称创新或检索质量。

输入/机制完整设计见[已接受设计](../work/S33_next_decision/review.md)，源码入口[producer](../work/S34_preparation/produce_geometry.py)、[consumer](../work/S34_consumer_preparation/run_consumer.py)、[scorer](../work/S34_scoring_preparation/score_s34.py)。共同旧来源与8头不作假等价，旧depth冻结但focal保持原trainable，原cache4→12和投票算术不改。

预算CPU8顺序：common packet120秒4GiB、各400臂240秒8GiB、共同map与三次append/render合计120秒4GiB；评分CPU1 120秒2GiB，启动空盘10GiB。只有根冻结正式contract后执行，失败保留。
