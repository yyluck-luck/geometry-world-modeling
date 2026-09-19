# S94 ALT-3RSCAN-01结果（3RScan资格检查）

## 结论摘要

3RScan比当前S93 TUM候选更贴合本项目的“长期/重访几何一致性”问题：官方资料明确提供**校准RGB-D序列、6DoF相机位姿、内参K、同场景reference/rescan及全局对齐变换**，并且官方示例归档的中央目录确实包含每个scan的51个color、51个depth和51个pose成员。因此它是**值得继续作为TUM替代候选**的数据源。

但本轮不能宣称正式Gate0通过。原因是：完整数据需要Terms of Use流程，当前只取得3RScan.json和ZIP头/尾部；没有取得任何解压后的完整RGB图、16-bit depth正文、pose正文或`_info.txt`正文，尚未验证帧级同步、K的具体数值、单位在本机解析、完整下载许可和正式split冻结。因此当前状态是：

> **S94_STATUS = CONDITIONAL_CANDIDATE / GATE0_NOT_PASSED**

## 逐项结果

| 资格项 | 结果 | 证据 | 解释 |
|---|---|---|---|
| RGB-D序列 | `PASS_METADATA / CONDITIONAL_BODY` | 官方README、官方文档、中央目录摘要 | 官方称calibrated RGB-D且depth-color aligned；本机只证实成员存在，未解压正文 |
| 帧配对 | `CONDITIONAL` | 每个示例scan各51 color/51 depth/51 pose，文件名共享frame编号 | 需要完整下载后逐帧枚举，不能只凭计数通过 |
| 6DoF pose | `PASS_METADATA / CONDITIONAL_BODY` | README与FAQ；`.pose.txt`成员存在 | 官方说明为RGB camera→world；正文和异常pose率尚未测 |
| K/intrinsics | `PASS_METADATA / CONDITIONAL_BODY` | README、FAQ、`_info.txt`成员存在 | K在`_info.txt`；具体K、分辨率和单位尚未本机读取 |
| depth单位/尺寸 | `PASS_METADATA / CONDITIONAL_BODY` | FAQ说明16-bit、millimeter且RGB/depth尺寸可能不同 | 需要正文核验PGM位深、零值、尺寸和resize规则 |
| reference/rescan分组 | `PASS` | `3RScan.json`解析：478 groups、385 train/47 validation/46 test、1004 rescans | 3RScan提供跨重访/变化场景；两个样例同属train group |
| 跨scan对齐 | `PASS_METADATA` | 样例rescan含4×4 transform；FAQ说明translation为mm而mesh为m | 需在正式实验前固定方向、单位和变换组合 |
| 官方split与使用政策 | `PASS_POLICY` | 官方documentation、仓库splits | 只能在train调参；test只做最终报告；不得用test反复选择参数 |
| 下载/许可 | `CONDITIONAL` | Terms of Use表单；代码仓库MIT LICENSE | MIT只覆盖工具代码，不能替代数据许可；本轮未提交表单 |
| 最小可达片段 | `PASS_HEADER_ONLY` | ZIP 39,949,975B；512B头+65,536B尾；EOCD 322 entries | 证明归档可达且含帧成员；不等于已有可用RGB-D正文 |

## 元数据统计

- `3RScan.json`：478个场景组；385 train、47 validation、46 test；1004个rescan条目。
- 示例ZIP中央目录：322 entries，总体为两个scan，每个161 entries；每个scan 51 color、51 depth、51 pose、1 `_info.txt`、1 mesh和6项其他文件。
- 示例reference/rescan组：reference `4acaebcc-6c10-2a2a-858b-29c7e4fb410d`，rescan `754e884c-ea24-2175-8b34-cead19d4198d`，两者同属train，并在JSON中有对齐transform。

## 是否替代TUM

**建议：保留3RScan为优先替代候选，但暂不切换正式实验。**

相对S93 TUM，它的优势是：

1. 直接提供同一场景多次scan，天然支持“历史reference→未来rescan”的几何重访问题；
2. 官方同时提供RGB-D、pose、K和跨scan变换，字段比当前TUM小探针更完整；
3. 官方示例ZIP已有小规模可达归档，可在合规后做低成本pilot，不必先拿全量1482 scans。

尚未满足正式替代的原因是：

1. 完整帧正文和`_info.txt`未取得；
2. 下载需Terms of Use，不应由agent代填；
3. 3RScan的“未来”主要是跨时间重扫/场景变化，不等同于连续视频未来帧；正式S91需把研究问题写成“重访/变化条件下的未来几何风险”，或另行证明连续序列设置；
4. 尚未确认示例scan的时间戳粒度、相机轨迹缺失率、RGB/depth有效像素率和单位转换。

## Gate0下一步（需外部授权或用户明确同意后）

1. 由用户自行完成官方Terms of Use流程，下载官方允许的小型示例包；agent不代填、不提交个人信息。
2. 只取一个train reference/rescan组，完整解压其中`sequence/`，核验每个frame的color/depth/pose三元组、`_info.txt`的K/宽高和depth单位。
3. 计算帧缺失率、pose有效率、depth非零率、RGB-depth分辨率关系，并保存SHA与完整manifest。
4. 冻结“reference历史→rescan未来”的输入/答案边界；只用train开发，不触碰test。
5. 如果核验通过，再建立S95（3RScan单组帧级RGB-D资格与几何真值试验）协议；在此之前不启动S91。

## 2026-09-12 19:06 证据纠正：示例 ZIP 的访问条件不能写成已确定阻塞

后续对官方仓库 `setup.sh` 和数据说明的独立检查发现：脚本把 `3RScan.v2.zip` 标为 example data，并直接执行公开下载；项目页/文档对完整数据又有 Terms of Use 总规则，但没有明确说明示例 ZIP 是否例外。因此原先把“示例完整帧必须先由用户完成 Terms”写得过强，现纠正为：**示例访问的许可适用范围仍未完全核实，不能断言必需注册，也不能断言完全无需许可。** 本轮仍未下载完整帧或提交任何表单。

另外，FAQ把 reference 描述为 initial scan（通常最完整或 first scan），rescan 是其余扫描；论文使用 later point in time 的语义，但当前JSON检查没有逐scan精确时间戳。因此3RScan适合先表述为“重访/变化目标”，不能直接当作连续视频 next-frame 数据。
