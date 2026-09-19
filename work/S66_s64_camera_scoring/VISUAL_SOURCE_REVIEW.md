# S66九帧展示脚本：有限源码审查

**PASS，限辅助展示源码；不是数值结果、可视化结果或运行/创新授权。** 审查者`/root/negative_result_question_triage`。实际完成UTC：2026-09-08T23:17:13.304838+00:00。仅全文读取新旧两个源码并核diff/SHA；未import或运行脚本，0新增科学正文读取、0看图、0模型。`diff`返回1表示预期源码不同，不是执行实验失败。

新源码`export_s64_visual_qa.py`：SHA `952479cdf812ef1bc0b79233e46fd864dcb04b259694c9a29c1abda2e645a9a6`。旧源码`scripts/export_c1_visual_qa.py`：SHA `f0f3e792b6fe5f2f702b7f0e87df337745aad6b62cceef61852c64dec45a1aa5`，与新文件记录的parent pin一致。

- **独立身份与输出。** 新根目录定位适合work下的位置，输出唯一指向`results/S64_unit_repaired_generation/visual_qa_all9`；要求显式binding路径及SHA、S64 row、评分和独立复算已接受的stage、原cohort资格false，并核binding列出的证据SHA。像素路径限定在新S64 archive中，不再读取旧C1评分目录。
- **完整顺序。** 恰好9个身份，逐项要求`id==0…8`；不排序挑图，不按分数跳帧。九个原尺寸576×576面板全部进入固定3×3接触表；输出目录已存在即停止，不覆盖旧展示。
- **标签准确。** ID0标为固定预处理输入，ID1–8均为MODEL GENERATED；不称真实场景照片。标题明确unit-repaired variant、ft-mse VAE、seed44；角度写Requested yaw，页脚明确请求不证明画面相机服从。
- **保留字节检查。** 每张实际读取时核普通文件、读前后身份、576×576×3字节数及正文SHA；PNG写出后重新打开，要求RGB模式、原尺寸和`tobytes()==raw`。单帧不裁切、调色或重采样；文字位于面板外。manifest记录原正文/descriptor身份、PNG SHA及展示用途。上述是将来实际执行的检查逻辑，本轮没有证明PNG已生成或往返通过。

**输入绑定的信任边界须保留。** 此展示器核binding中的stage字符串和所列文件身份，不自行解析评分/独立复算票的成功语义，也不把九项像素身份再与评分报告逐项交叉核。因此实际使用应由root先核收真实评分与不同作者复算，将其对应的九项权威像素身份写入并封存具体binding；本轮尚未审该未来文件。展示器不能用来替代这些数值检查。父源码SHA在运行中仅作为谱系记录，此次已由源审核对。

无阻塞源码差异。后续仍需真实导出返回、9项往返记录及人工查看全部面板才能报告展示完成；这些都不构成画质优胜、几何正确、长期记忆有效或新方法证据。不新增实验框架或数值门，root另记主账。
