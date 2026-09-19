# S26B 第二次启动调用器审查

结论：当前调用器与候选合同通过执行前审查；root可另行冻结启动。旧冻结S26B runner/scorer、旧dispatcher和import的FAILED回执保持不变。此回执不表示真实import或GA已执行。

旧失败在UTC16:11:01，phases为空，import子进程在调用导入函数的首句取 `importlib.util` 时失败。原WORK只有dispatcher回执和失败import日志目录，结果OUT不存在；未产生任何共享/科学输出。本次不是重启旧dispatcher，而是有独立外控目录和回执的新执行尝试。

已全文审 `continue.py` 与 `contract_candidate.json`。候选SHA为 `f5f02d45a461c1d9448aad517a760c9550214676ded121f7cac0c553d5014598`，父冻结S26B SHA为 `147357aa1b24caeb813c01fd822cb96f754c2573437d0db6ac8a05b7cbd4d90c`。

调用器显式导入标准库 `importlib.util`，使用固定bootstrap通过runpy执行同一份冻结runner。bootstrap把Python -c的argv移除，留下原runner路径和原worker参数；原runner不被改写。父进程只复用原resource supervisor，并将该模块的WORK改为新attempt外控目录。每个子进程重新从磁盘执行原runner，其WORK/OUT仍为原S26B路径，进程间不共享父模块的WORK改动。

启动前核合同代码/父manifest/原失败记录身份，确认旧phases为空、输出目录尚不存在、S24已PASS。新attempt目录必须不存在，禁止重复启动。依次import→CUT→TTT→FILT→score，沿用原CPU/步数/种子/数学、资源上限与scorer；没有重跑任何已成功阶段。末尾重新核合同身份，旧失败不得被覆盖。每个子worker继续执行原父manifest的全部源/输入身份门。

唯一新增的实际执行检查为：使用相同目标Python、相同bootstrap，在全新进程运行原runner `--help`。退出码0、stderr为空，正确显示worker/manifest参数，耗时约0.039秒；详情见 `bootstrap_help_receipt.json`。该入口在argparse帮助后即退出，没有进入manifest读数组、真正import、GT、模型或GA。它验证启动与参数路由；不宣称真正导入或数值流程通过。既有S26B对importer人工文件和数学的前审继续适用。

未发现剩余阻断。建议冻结当前合同并由root实际执行这一新尝试；失败保留，不修改原科学阈值或历史FAILED。Supervisor强baseline优先与本地科学批判技能的证据边界在此体现为：把启动错误明确记录为技术失败，不冒充实验结果，不用重复400步替代修正入口。
