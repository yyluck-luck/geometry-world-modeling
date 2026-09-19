# 仅准备期解释器路径修正

Root 源读发现 command_template 把虚拟环境可执行文件 resolve 到了底层 bundled Python，可能绕开 NumPy 1.26.4 环境。仅将合同 command_template[0] 改回未解析的 `.venv-cut3r/bin/python` 原路径；源码不变，无执行、无重新测试、无真实数组读取。

旧值：`/Users/rocket/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12`。

旧合同完整字节保留于 `OUTPUT_REVIEW_CONTRACT_before_venv_path_fix.json`，SHA `bd49d3862d74ade535990d1e93603e32c6e94fe23954e21776a6304875cbaa4f`。
