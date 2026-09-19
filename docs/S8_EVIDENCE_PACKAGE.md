# S8 科研证据包字节核验

状态：**PASS，仅指ZIP归档完整性与来源未变检查。** 没有重跑模型、建立新环境或验证新机端到端执行。

实际开始UTC：2026-09-05T19:59:13.641827+00:00；成员列表捕获：2026-09-05T19:59:13.695442+00:00；实际完成：2026-09-05T19:59:20.361487+00:00。这是本次真实打包/核验时间，非原实验时间。

输出：`/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/独立场景验证/科研证据包_S8.zip`

ZIP大小：325899547字节；SHA256：`afae809a350cb8565674f1326443db11ee5c9a4a7b12f0bdb7ea0ebf9d2c05d3`。690个原项目文件 + 1份包内说明，共691项payload，另有MANIFEST.json，共692个ZIP成员。全部成员CRC、字节大小和SHA核对通过，来源缺失0、来源变化0；所选72RGB+72depth均与V2冻结清单一致。

内容包括指定S8设计/来源/审核、项目scripts/src/tests/vendor、V1失败与V2输入目录、S8模型/重放/审计/分析/RGB QA证据。派生数据仅含父层5项记录、3个GT/时间表文本以及选定144个PNG；不含其余完整数据、TGZ、权重或环境。

报告正文S8_RESULTS.md、S8_MANUSCRIPT_REVIEW与reports/S8排版文件明确不在此包；最后报告另行交付。本核验文件在包生成之后写入，也没有递归打包。历史JSON绝对路径保留，部分历史引用或完整数据依赖在包外，不保证解包后所有脚本能直接运行。

包内PACKAGE_README.md说明范围与许可；MANIFEST.json列每个payload的SHA/大小。机器收据为S8_EVIDENCE_PACKAGE.json，完整构建成员清单/收据保留于`/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/work/S8_evidence_package_build`。
