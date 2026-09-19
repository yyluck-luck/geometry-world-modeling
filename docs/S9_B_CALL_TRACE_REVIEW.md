# S9 B 调用轨迹独立只读核对

完成时间：2026-09-05T20:33:13.496263+00:00。状态：**PASS，须在适用性报告补齐桩替换范围**。完成 94 项静态/保存记录检查；没有重跑原函数、轨迹脚本、模型、渲染或重建。

## 核查结论

原脚本将唯一匹配的 FunctionDef 节点直接编译，未变更生成循环 AST。原生成函数 1195–1316 行及平均函数 601–637 行、635 行的完整切片表达式均与记录一致；pre_run、verification 和当前四份来源 SHA 全匹配，工作副本 pipeline 与固定 vendor 快照相同。

| 人工输入 | context 调用前历史数 | 重建桩调用时历史数 | 填充后目标帧数 | 实际追加帧数 |
|---|---|---|---|---|
| 初始 1 帧，目标 13；平移/静止各一例 | 1, 8, 12 | 8, 12, 14 | 7, 4, 4 | 7, 4, 2 |
| 初始 9 帧，目标 12；平移/静止各一例 | 9, 13, 17 | 13, 17, 21 | 4, 4, 4 | 4, 4, 4 |

四例均每批 context→追加帧→重建桩，共 12 次 context/12 次重建桩；初始单帧的两例首批绕过检索，留下 10 个“需要检索”的桩标签。默认切片仅取末位姿；逐项核全部 float32 人工坐标、保存均值矩阵和相邻相等标志。平移 3 个相邻比较全不同，静止 3 个全相同，这些是构造输入的结果。

## 适用性报告必须明确的范围

1. List all substituted operations: get_context_info, get_translation_scaling_factor, get_cond, do_sample, tensor_to_pil, encode_image, construct_and_store_scene. The saved scope shorthand names only sampling/reconstruction. Preserve original records; disclose the full boundary in the applicability report.
2. query_pose is the averaged pose before get_transformed_c2ws. No renderer K, geometry, source voting, candidate expansion, sorting or NMS ran. retrieval_needed is a fixture branch label, not observed renderer execution.
3. Stationary equal poses are imposed by input construction; moving inequalities are properties of these fixtures. Neither measures real navigation frequency, cache eligibility/hit rate nor acceleration. Run wall-clock metadata is not real VMem latency.

## 固定查询/固定组假设的源码核对

| 固定来源行号 | 结论 |
|---|---|
| 950–955 | get_transformed_c2ws deep-copies and flips columns 1/2; a fixed axis-convention transform, independent of map contents. Same raw average pose has same transformed pose. |
| 635–645, 995 | Default context_num_frames=4 makes the exact slice select only the last padded target pose. target_K is the mean of accumulating surfel_Ks and render receives mean×0.65; identical camera pose alone does not freeze intrinsics. |
| 820–827 | The active merge path appends a new source timestep on a matching existing surfel; unmatched surfels are returned. It does not assign an old surfel position, normal or radius. |
| 1026–1056, 1082 | Construction converts initial/all or last target_num_frames point maps into surfels, merges memberships, assigns sources to unmatched births and extends the global surfel list. Ordinary writes need not preserve group/source/candidate identities even if an old position is unchanged. |
| 1337–1401 | The separate undo branch removes frames, source memberships and surfels, then reindexes survivors. Not executed in this synthetic trace; another explicit invalidation case for any later cache. |
| 1195–1316 | Every nonempty generation batch calls context once, appends generated frame state, then calls reconstruction once. This is the original AST body; its external operations were stubbed. |

原点没有在该合并路径中移动，不等于记忆不变；来源追加、新点、内参均值和导航相机变化足以破坏第一版证书条件。S7/S8 对同一查询的多次离线干预不是官方正常导航的重复消费证据。

## SHA 绑定

- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/scripts/audit_s9_b_call_trace.py`：`75de10b617e4b60168bab1e83a185c4633e11e85ede53ca60dca857aa6994210`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S9_B_call_trace/pre_run.json`：`a4093009d63c4cc826adecfa3f493044645e34d57d67504af0d5c274a47fcdd7`
- `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S9_B_call_trace/verification.json`：`d42f12e314e8f7fef543c6401bbeac0af9d771ed693d0057b11b8f2fe4cd7db6`
- `/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/modeling/pipeline.py`：`90a45f452a4f734b3371fb526c566162026e5d900e0c8204709dd57f44ef1d7e`
- `/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/utils/util.py`：`0b71dcf6d4a43109d785f49d9c6def37b1256c4d189ab9438bfb185f3099f013`
- `/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/vmem/configs/inference/inference.yaml`：`8d849588016935573a22ef6aaee567f71125ca4d3bdf18f51e3552a64be9fea3`

以上要求只需在新适用性报告说明，不应回写修改已保存的 pre_run/verification。未发现需重跑本次人工调用轨迹的数值或抽取错误。
