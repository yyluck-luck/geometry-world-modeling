# DeepSeek Harness 本地科研辅助

更新UTC：2026-09-09T09:45:31.627619+00:00。官方0.1.2-rc.1，已有Node24.19，OpenRouter已配置，默认低价`deepseek/deepseek-v4-flash-0731`。凭据和私有state已Git排除，不复制到报告。

**以后所有新科研会话统一归入左侧geometry-world-modeling专栏。** 使用项目根目录下的`scripts/run_dsh_review.py --prompt 已核材料.txt --output 新目录`入口；实际headless cwd和sandbox根目录均为项目根，输出单独留在新目录。仅设置cwd还不够，包装器结束后用唯一新会话的完整session ID显式附加到项目workspace。归组失败单独写`GROUPING.json`，不能将模型return0称作已经归组，也不为归组重跑模型。

此入口v2已实际运行一次：新事件记忆审查32.455113秒return0，官方接口确认归组成功；root本轮已在UI确认并命名“创新审查 01｜事件记忆与固定预算”。模型请求和UI显示Flash0731，此次请求/响应身份与usage独立审计仍待完成。旧V3方案审查23.33秒的真实响应与已核usage继续保留；旧会话从子目录启动、cwd不可变，仍在Ungrouped，不篡改历史。

服务停止时可双击[启动DeepSeek](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/tools/deepseek-harness/启动DeepSeek.command>)；已运行时无需重启。模型任务180秒外控、900词软提示，只读/native和approval never；只读不等于没有工具或网络，费用没有硬上限。

[具体用法与验收](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/HARNESS_GUIDE.md>)。DSH负责文献比较、候选空白和方案反驳意见，所有引用、建议和创新判断由主agent回到原文、代码及实际实验核实。
