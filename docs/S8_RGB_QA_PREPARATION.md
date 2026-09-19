# S8 已冻结真实照片的QA准备

新增 `scripts/qa_s8_rgb.py`。本准备阶段仅实现程序、检查帮助入口与小型合成边界，不读取新TUM数据，不执行真实72图QA、下载、模型或实验。运行和图表人工查看由根任务衔接。

## 调用与根任务字段合同

建议使用本项目分析环境 `.venv/bin/python`，六个参数全部必填：

```text
scripts/qa_s8_rgb.py --manifest S8_inputs.json --protocol S8_EXTERNAL_SCENE_PROTOCOL.md --design-freeze S8_DESIGN_FREEZE.json --data DATASET_DIRECTORY --output FRESH_QA_DIRECTORY --photo-output FRESH_PHOTO_DIRECTORY
```

两个输出目录必须同时不存在，悬空符号链接同样拒绝；两者不得相同或嵌套。先核全部目录条件再创建，不覆盖既有尝试。程序内失败会保留新目录已产生的照片/记录，run_metadata.json写failed、失败阶段、traceback和实际结束时点；照片README与先看这里始终标“尚未完成”，只有整轮成功后才改成完成。若根目录尚无法创建，自然不存在可写失败记录的位置。

完成的 `run_metadata.json` 提供根任务约定：status=completed；manifest_sha256、protocol_sha256；input_manifest_sealed_utc、first_rgb_decode_utc、completed_utc；checked_rgb_images=72；depth_decoded=false；gt_pose_values_parsed=false；images每项path/rgb_sha256/copied_path/copy_sha256；source_sha256含本脚本及run_s8_sequence.py。图片path和copied_path为绝对路径，另保留manifest_relative_path、block/frame、历史/查询、时间戳、PNG模式/尺寸、CRC和完整解码标志、字节大小与核验时点。

## 先保存固定清单，再看图片

核设计冻结的协议哈希及未读新图/未跑新模型声明，检查三个块全test，使用新controller的纯输入验证函数核72个RGB和72个depth字节哈希、路径、唯一性与合同。此调用不解码depth，不解析GT位姿。

将manifest、protocol、design freeze的原始字节复制到QA目录并逐哈希核对；保存两份实施源快照及哈希。写input_manifest_sealed_utc并持久化metadata后，才允许任何Pillow图片打开。first_rgb_decode_utc在第一次PNG格式/CRC/像素检查调用前即时记录。没有选新样本的分支，失败不换图。

## 原照片与浏览联系表

每个原RGB必须PNG、单帧、RGB模式、640×480；Pillow verify检查PNG校验，再重新打开并load完整解码。通过后把同一份已核SHA的原字节写入全新PNG，不重新编码或修改像素。再次核原件/manifest/副本SHA一致。

照片目录分为片段1_B0_外部测试、片段2_B1_外部测试、片段3_B2_外部测试；每段01–20为“历史”，21–24为“查询”，保留原文件名后缀。原路径、时间、用途与SHA写入带UTF-8 BOM的照片来源清单.csv及JSON，便于Finder/表格软件查看。

全部72张复制后，用matplotlib创建3张4×6联系表，每幅标顺序、history/query、RGB时间戳；英文图注避免依赖未确认中文字体。联系表单独缩小显示照片和加标签，是浏览辅助；72张原PNG仍逐字节不变。联系表在QA目录及照片目录各保存字节相同的一份，元数据记录两处路径与SHA。程序验证联系表PNG可读，`contact_sheets_visually_reviewed=false`明确尚未人工查看，不能把自动生成当作视觉审查完成。

README明确这些是TUM原相机实拍，非AI生成/新视角结果；保留当前官方网站CC BY 4.0说明、数据链接、Sturm等IROS2012论文引用与2012历史CC BY 3.0差异。依据已完成docs/S8_DATA_SOURCE_REVIEW.md/json，不另作未核法律判断。

## 轻量验证

新增 `tests/test_s8_rgb_qa.py` 四项临时合成检查：PNG CRC和完整解码/不重新编码复制；坏CRC、灰度或尺寸错误拒绝；两个输出同时新鲜及不嵌套；预检失败留下未完成照片说明且没有触发解码。帮助入口与编译检查通过。未读取任何新场景图片或进行真实QA；执行源码应进入根任务最终执行冻结。
