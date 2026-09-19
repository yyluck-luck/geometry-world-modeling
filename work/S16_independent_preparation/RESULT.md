# S16 真实存档独立数值复算

状态：PASS。实际UTC 2026-09-06T10:45:14.731070+00:00 至 2026-09-06T10:45:17.243856+00:00；耗时2.512796秒、进程峰值RSS 376,389,632字节。不是模型速度测试。

只在S16生产阶段PASS后读取固定存档，25个文件身份前后相同，读取62个NPZ数组，0 RGB、0 PNG、0模型调用。GT来自已评分的S15B evaluation_gt.npz，不是未见答案。

以S15B独立核验过的分量pinhole/相机运算和np.minimum.at重做七方法x四来源x四目标共112个来源层；各winner ID精确相同，model-z最大差3.5527136788005009e-15，低于atol/rtol 1e-10。再以跨来源两次minimum归约重建28个S15B合成图，来源身份精确、深度在容差内。

对六policy的10个指定子集独立重算正确数量、coverage、四帧等权值；三互斥完备空间类及I=full-sum(singles)+3base的逐像素整数图精确相同。所有frozen-owner子集实际counts/mean、每source solo old/new/delta/mean，以及single/joint-marginal的target/mean聚合符号均核对通过。6 policy每像素frozen-owner I为0；另核4来源的逐像素边际符号反转计数全部0，与MATH_REVIEW.md的区间解释一致。总3622项核验不是3622个独立研究样本。

解释边界：10子集不是完整16格析因；I合计二阶及以上交互；空间类分摊不是物理原因的独立因果干预；冻结owner的零值是代数检查。聚合边际可翻转，不能说同像素由正转负。

独立性范围：团队内部不同实现；本agent此前改进S15B输入绑定，但不导入S16生产函数，原投影/统计core由root编写。既非外部团队复现，也非新场景验证、新算法收益或新模型推理。

verification.json SHA `8c1aaad618c0358ec3bba4ff40cf6e8ab602ad57cfb10298fcdef8431c5a6c67`。新verifier SHA `3d41363aa093b445d8935fd493adde271acb2bb2bdf633b20afee51f4d76cc96`，固定helper SHA `184ecc344be8bf58741ee9c7d6182909fcdd6786f3bb877a43ab21e2990beee5`。独立来源层、诊断JSON与interaction maps均留在results/S16_interference_independent/。
