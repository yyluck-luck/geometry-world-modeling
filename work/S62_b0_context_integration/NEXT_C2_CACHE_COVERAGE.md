# C2 V9 第二动作缓存覆盖：仅元数据核查

实际核查完成：2026-09-08T19:31:13.018485+00:00（北京时间 2026-09-09T03:31:13.018485+08:00）。**必要输入的描述与文件大小齐全，可另立输入声明做一次保存缓存接线；无需为取得这些输入重跑第一批。** 本次只读源代码、事件和descriptor，并检查文件存在/大小；数值载荷读取0 B，RGB、模型与renderer执行均为0。

| 最小来源 | 已保存字段／尺寸 | 唯一数值文件字节 |
|---|---|---:|
| seq50 map_commit.cache | 5 c2w：[4,4]，首份float64、其余float32 | 384 |
| 同上 | 5 K：float32[3,3]，五项共用一个blob | 36 |
| 同上 | 5 latent：float32[4,72,72] | 414,720 |
| 同上 | 5 encoder embedding：float32[1024] | 20,480 |
| 同上 | 5 surfel_K：float32[1] | 20 |
| seq56 context_input.args[0] | 4个目标c2w：float32[4,4,4]；args[1]=None | 256 |
| seq58 render_input | 515 surfel的位置/法线/半径/来源ID；query pose、focal与512×288参数 | 15,712（既有几何输入） |
| seq64 nms_threshold | is_second_step=true、NMS=true、原始threshold | 内联元数据 |

以上22个缓存/目标blob合计**435,896 B（约0.416 MiB）**，与既有几何blob无重叠；共同最小数值输入为1,494个唯一blob、451,608 B。若沿用S62原路径先重现旧三图，seq60另需2个唯一blob共1,179,648 B；连同最小输入共1,631,256 B。以上是按descriptor去重的拟读字节，不是本次实际读取，也不是新增独立数据。所有列出的blob均存在、大小匹配、descriptor与archive manifest一致；本次未验证blob内容SHA或有限性。

seq44与seq50四类历史缓存descriptor逐项相同，seq50与seq58的surfel_Ks也相同；seq50在第二动作seq54/56之前。原捕获器在commit_map后保存完整cache；原导航与生成源码在下一次get_context_info前不追加/删除这四类cache。pil_frames只需保存的长度5，可按S62放5个占位值；不需要解码图片、surfel_depths或目标K。后者不属于get_context_info实参，焦距由surfel_Ks求均值产生；seq58可核实际渲染query。

**缺失边界：** seq65是turn_right的IndexError，seq66仅archive_finalize；没有第二次nms_selection/context_output/batch_input，不能伪造成功参考。seq62保留空检索结果。可复用S62的六个原数值方法及average_camera_pose提取、显式Decoder、输入指纹、query拦截、选中ID对真实缓存四类行的精确检查。其load_inputs/run_arm的B0事件序号、567点、固定ID与成功context参考必须针对C2独立声明，输出另建目录，不能重跑S62目录。原路径的预期是保留已知异常；组件路径能否返回、所选ID是否索引到seq50真缓存，仍须实际有限接线与独立复核。本检查不证明get_cond/生成可用，不是完整C2、尺度生产修复或创新证据。

来源范围与SHA见同目录 `NEXT_C2_CACHE_COVERAGE_SOURCE_RECEIPT.json`；档案为 `results/S47B_C2_confirmation_generation_v9/archive`，原get_context_info见pipeline.py:505–765，捕获器integrate_original.py:161–170、214–225、334–342。
