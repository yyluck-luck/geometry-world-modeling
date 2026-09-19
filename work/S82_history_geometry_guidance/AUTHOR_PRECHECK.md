# S82 四历史原始几何入口：作者源码预检

实际预检记录：2026-09-10T18:11:38.036955+00:00。代码作者检查，不是独立验收；没有运行本入口，没有导入 Torch/NumPy/PIL 或加载模型，没有打开原 RGB/深度/NPZ/权重正文。仅运行 Python 标准库的源码 compile、合同 JSON/字段一致性及现有包的 distribution 元数据读取。

交付版本：

- `build_four_history_geometry.py`：20013 字节，SHA `5f4c76b2ea475d66d3556b8a044f5f9a5f04972d1de12856d26d102d1eb6e49e`。
- `FOUR_HISTORY_CONTRACT.json`：39726 字节，SHA `cb60e53793942e9356eb1935544f490dc4a86be3be330bfdb2fe5abf285b0f46`。
- 当前 execution_geometry_01 不存在，真实执行次数 0。

作者已核：固定四图 [12,13,18,19]，生成槽仍 [19,18,13,12]；原图 SHA 继承 S68，运行时先重新哈希再走原 PIL loader（每图两个文件读取入口）；checkpoint SHA 继承 S17/S21，精确 size/mtime 检查，原 unsafe-global 扫描加 safe_globals/from_pretrained 受限加载，模型加载一次。没有内存 I/O 替换，没有额外图片、目标、深度、旧 state、optimizer 或 render。当前冻结源码文件 98 份，运行前逐份核 SHA；官方实际路径为工作区 W/work/cut3r-local。

沿用 S21 的原 prepare_input 定义、load_images_for_eval、inference_recurrent、signed RoPE 和官方 pose decoder；本次显式 eval，全部模型参数/输入 CPU float32。保留 original image-only 的 NaN ray placeholders，因为 ray_mask=False；对输入图像和输出 heads 才检查 finite。K 只保存为近似坐标元数据，不喂 raw predictor、不声明米制。self/cross 六字段原样完整保存；完整配置中 ±inf 哨兵显式编码为严格 JSON 对象，不把配置哨兵当预测 NaN。

输出接口见合同 output_schema；四个 heads 按预测时增量归档，并在验证前保存原字节，官方 decoded c2w 同时记录于逐 head 收据，全部结束另存 PREDICTED_CAMERAS.npz。PREPROCESSED_INPUTS.npz 保留实际归一化图像，以及从它反变换的 RGB01（明确不是另一次原图解码）。所有产物含文件 SHA、tensor shape/dtype/body SHA；实际科学输入 file-open 清单不冒充内核逐字节 I/O 追踪。

内置简短 watcher，300 秒 / 20 GiB，0.1 秒采样并检查退出后的 worker ru_maxrss；超限 TERM，最多 5 秒后 KILL，失败目录保留，无自动重试。采样 RSS 不是瞬时硬内存封顶。完整四图和成功技术字段只表示“原始预测归档完成”，不表示几何正确、对齐完成或创新成立。

root 完成不同作者源码前审后唯一运行命令（作者未执行）：

```sh
'/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/.venv-cut3r/bin/python' -I '/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S82_history_geometry_guidance/build_four_history_geometry.py'
```

不要手动调用内部 --worker，不要删除失败目录重试。新运行若报错，先保留原始 traceback/STDERR/RECEIPT/SUPERVISION，依实际错误再决定；不需要在此阶段另加几何优化或质量阈值。独立前审仍需实际核本版源码的输入边界、模型调用次数、输出字段/四元数和监督器失败路径；本作者不能自己宣布 root 验收。
