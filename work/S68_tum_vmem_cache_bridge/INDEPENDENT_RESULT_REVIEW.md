# S68 实际五来源编码：不同作者有限结果核验

**结论：PASS_S68_INDEPENDENT_APPEARANCE_RESULT_REVIEW。** 138 项身份/结构/有限数值条件中 138 项通过；阻塞项：[]。这确认实际编码产物与来源绑定、FP32结构及K算术，不是独立重跑神经网络或生成收益证明。

独立实际执行：2026-09-09T01:17:21.195516+00:00—2026-09-09T01:17:21.254543+00:00，0.058924秒；使用Python 3.12.14 / NumPy 1.26.4，未导入Torch、CLIP、Diffusers或原函数。作者为`/root/c2_v9_recovery_author`，核验者为`/root/negative_result_question_triage`，属于团队内不同作者核验。

外控真实01:12:53.263956—01:13:11.908300Z，return0、18.644266958秒，无stop_reason/observer_error；worker17.870114959秒。self峰RSS **12969394176 B** 与外部采样进程树峰 **10275667968 B** 是不同测量，未混称。ARGV_CORRECTION、源审、root binding和实际argv一致，保留`.venv-cut3r/bin/python`；原交付误写base解释器的字段没有被改写。

五个原来源 **12/13/14/18/19** 对应存储行 **0/1/2/3/4**。全部20条历史元数据与S8 block0旧时间/路径/SHA对应；真正正文只允许五份。本人实际读取并重哈希五份PNG共 **2625997 B**，检查IHDR为640×480、8-bit RGB，未解码/观看图片；另读五份新NPZ共 **440740 B**，解码20数组、数组正文 **435560 B**。本次实际科学文件字节共 **3066737 B**；0目标RGB、0depth、0大权重正文。不能称本人0RGB读取。

每来源均有且仅有：latent `[4,72,72]` FP32 **82944 B**；embedding `[1024]` FP32 **4096 B**；pixel K与normalized K各 `[3,3]` FP32 **36 B**，合计 **87112 B**。实际shape/dtype/finite、每字段bytes/SHA、整个NPZ SHA及逐来源JSON均与实际worker行一致；完整逐源身份在配套JSON。

K独立由640×480覆盖到768×576、左裁96/上裁0计算。理想像素K为`[[630,0,287.4],[0,630,287.4],[0,0,1]]`；按原声明FP32运算得到主点 **287.4000244140625**，理想差最大 **2.4414062522737368e-05**，为已保留的舍入。五份实际K与独立FP32结果全字节相同，前两行只除576一次得到normalized K，后行保持`[0,0,1]`；实际与独立算术差0。没有调用原crop/ray函数，也未把此数值一致称完整物理标定或half-pixel约定已验证。

实际readlist为1输入元数据＋10来源文件＋5旧文本元数据＋1VAE配置＋2权重＋5历史PNG。两份权重记录共4279161112 B，SHA和decoder路径与既有pins一致；VAE missing/unexpected/mismatched/error为空，CLIP state_dict missing/unexpected为空。原AutoEncoder明确取posterior mean×0.18215，原CLIP保持逐来源编码；worker成功经过冻结/eval/CPU FP32等检查。本人未重读权重、重编码、重算预处理tensor SHA或单独恢复posterior mean，因此**不把结构与代码路径一致说成全部latent数学独立复现**。

0目标/深度的证据来自已核源码与实际readlist，硬编码零字段本身不作证明；没有扩展成OS全文件访问审计。五个完成行与固定循环支持每来源各一次编码helper，但无独立逐层调用探针。输出属于已见数据及声明ft-mse组件变体，原SD2.1 VAE身份仍UNKNOWN；缺c2ws、完整20历史/几何/生成状态，也没有gather/get_cond/renderer/视频或质量评分。旧目标曝光、原C2失败和NO_METHOD_SELECTED保持。

绑定：worker SHA `ed56948f0c80e5d607bbe9061b29d4d0da5592225cadf6700b759edd1b3a92b7`；external SHA `75d8304e2f7cfeecf8d7f4b8d84eb237481cbe91cab8b2c64ef4ce90bcff1197`；源码 SHA `52c51abe34ff7911c89951788cf5253e6c14ddb87a9a34b0e28223e61c21d3a9`；本核验JSON SHA `c68af438a7a8693604bf05e2a9ed3ef62621c426c92edd93e8903fe41291c000`。最终报告均只读0444，无主账/旧产物修改。
