# S15B consumer 真实独立数值复算

状态：PASS。实际UTC 2026-09-06T10:36:35.353248+00:00 至 2026-09-06T10:36:37.509975+00:00，耗时2.156740秒，进程峰值RSS 229,097,472字节；这不是速度对照。

仅在生产predict和score均PASS后读取允许的封存输入。固定32个文件身份，24个NPZ数组读取、4个原目标GT深度图解码、0 RGB解码、0模型调用；身份均在核验前后相同。

直接以原四来源proposal、共同given camera/K/s和三条见证mask重算七方法×四目标。采用分量pinhole与光学相机变换，np.minimum.at先取最小z、再仅在完全同z候选中取最小来源ID，没有使用producer render、confidence或score函数。重算28幅完整pixel ID与producer精确相同；最大深度差3.5527136788005009e-15米，低于冻结atol/rtol 1e-10。

4个GT使用整数索引x=((2*(u+37)+1)*640)//598、y=((2*v+1)*480)//448；所获GT栅格与producer PIL nearest/crop逐元素精确一致。strict delta1采用浮点除法、误差与跨帧统计用math.fsum。28行逐目标指标和七组四帧等权均值/像素加权辅助值均通过1e-10比较。总706条核验条件不是706次独立实验。

独立性范围：本agent参与了producer输入绑定和答案隔离守卫修订，但未写原始投影/统计core。本次没有导入producer函数，使用不同数学运算路径重算；这是团队内不同路径数值核验，不是外部独立团队、新机器重跑或新场景确认。

verification.json SHA `d1a328681a354fa2f1bdd23060d2c2c0dadfd9e3d53352cfd8f3599543cd197c`；verifier脚本SHA `184ecc344be8bf58741ee9c7d6182909fcdd6786f3bb877a43ab21e2990beee5`。

原始独立prediction/出处保存在results/S15B_consumer_independent/independent_predictions.npz，独立统计保存在independent_scores.json，所有检查/输入身份/时间保存在verification.json。本报告验证计算一致性，不自动改变root对创新、效果或单段探索的判断。
