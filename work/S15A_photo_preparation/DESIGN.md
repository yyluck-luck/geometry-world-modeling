# S15A真实历史照片索引图：代码准备

本任务仅编写 `scripts/plot_s15a_real_photos.py`，没有执行真实照片读取。使用 `/opt/homebrew/bin/python3`，已确认Pillow 12.2.0和Matplotlib 3.10.9可导入。

## 已应用figure-designer的适用部分

实际读取 `/Users/rocket/.codex/skills/figure-designer/SKILL.md` 与 `references/experimental-results.md`、`references/tools.md`、`references/design-rules.md`。图属于数据来源说明的支持图，不是效果对比图；使用可复现的PIL/Matplotlib脚本。4列×5行按history 0…19顺序显示全部原生RGB，保持原比例和完整视野，每格11pt文字标记history index与相对第一张入选RGB的时间，顶部18pt标题写明 `Bonn real RGB | history only | no accuracy result`。footer说明时间原点与完整视野。

不设“获胜”配色、几何热图、效果数字或精选好图。照片本身是栅格，按父任务要求输出PNG索引图；不因技能通用的矢量建议而把照片冒称矢量。本图是供原尺寸查看的照片目录，不预设可缩成论文单栏；正式论文排版需重新审字号。真实PNG尚未生成，视觉排版与照片内容必须由根在实际生成后查看，当前不宣称视觉检查PASS。

## 输入合同

CLI：`--manifest --samples --seal --seal-sha256 --output`，输出必须新目录。兼容既有 `s15a-history-combined-seal-v1`，不要求给该seal新增plotter键，避免破坏独立verifier的精确集合。

读取图片前依次核：外部SHA绑定seal；seal绑定manifest与samples；model manifest也绑定同一samples；20history/0query及target禁止合同；run_metadata的SUCCESS/complete、caller PASS及实际时间先后；actual opened paths与20history相同；samples成员路径/时间/顺序与history身份相同。只读取这些允许JSON，不遍历seal的其他文件，不打开或哈希预测NPZ、权重、轨迹、GT和target图片。samples元数据含future/depth名字，但程序不打开它们。

通过以上门槛后，将20份PNG原始字节读入内存并核SHA，再逐张仅解码一次，不覆盖源文件。要求原生PNG/RGB/单帧，防止静默颜色转换。Matplotlib只改变索引图的显示尺寸，完整原图不裁切、不改色。成图后再次核源文件和控制JSON身份，记录两轮原图字节读取与20次真实解码。输出PNG与receipt；若失败，写FAIL/traceback/实际计数并保留已有部分产物。

## 运行方式（由根在实际完成+seal后调用）

```text
/opt/homebrew/bin/python3 scripts/plot_s15a_real_photos.py 
  --manifest docs/S15A_HISTORY_EXECUTION_MANIFEST.json 
  --samples work/S15A_samples_v2/samples.json 
  --seal <实际combined seal绝对路径> 
  --seal-sha256 <实际事前封存SHA> 
  --output <新的报告目录>
```

执行后根必须实际查看 `s15a_all_20_real_history_photos.png` 并另记视觉检查；运行器不把图生成成功写成已目视核验。
