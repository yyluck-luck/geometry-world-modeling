# S17B 独立验证器的状态坐标规则勘误

S17B 两图真实模型运行已经完成；原独立核验器 v1 在读取19个保存数组后因自身规则错误返回 FAIL。**保留原失败，不重跑模型，不修改原冻结的验证器、协议、manifest、output seal 或结果。** 本文件及补充 JSON 合同只授权另外一版核验器检查同一批保存输出；实际补充核验尚须 root 前审后执行。

错误属于独立审查者：原验证器只用了 `floor(sqrt(768))=27`，漏读官方 `model.py` 下一行“若 width 为奇数则加1”。官方实际规则是偶数宽度网格。已封存 `checkpoint_load.txt` 明确 constructor 为 `state_size=768,state_pe='2d'`；不能套用默认324或自行猜1d。故本配置 width=28，每个 i 的位置为 `[i//28,i%28]`，最后一个是 `[27,11]`。

诊断阶段只重开 `state.npz` 的 `state_pos` 一个保存数组：形状 `[1,768,2]`、int64，全部768项符合 width28。另读取了原加载文本、原失败JSON和官方源码。这是已保存结果的检查，不是再次模型前向；未读取新实拍、GT或反序列化权重。此前人工准备也跟着错误的27网格构造，所以原人工通过不能为该规则背书。

更正版 [verify_s17b_dpt_history_v2.py](../scripts/verify_s17b_dpt_history_v2.py) 保留 v1 的全部来源、19数组、状态及 SciPy pose 检查。唯一数值规则修正用独立整数方法 `math.isqrt(n); width += width % 2` 构造全部坐标；还从实际加载文本以 AST 读取明确的 `state_size/state_pe`，不 eval 该表达式、不删掉状态检查。

新 [补充鉴权合同](S17B_STATE_POSITION_VERIFIER_AMENDMENT.json) 绑定原 v1、原 FAIL、原 manifest/seal、官方源码、加载文本与 v2 SHA。CLI 另外要求 `--verifier-sha256`、`--amendment` 和 `--amendment-sha256`；历史 manifest 仍绑定原 v1，不被悄悄改写成 v2。补充检查在新的结果目录执行。

人工修正检查 [check_even_grid.py](../work/S17B_verifier_correction/check_even_grid.py) 从原源码仅提取 `_encode_state`，用一个返回单特征零值的 callback，分别检验768→28、324→18、25→6、16→4；覆盖非平方奇宽、偶平方根与奇平方根。原27规则和缺失显式state_pe都会被拒绝。实际回执 [artificial_receipt.json](../work/S17B_verifier_correction/artificial_receipt.json) 标为 PASS_ARTIFICIAL_ONLY，没有模型实例、实拍、权重或GT读取。

S17C 尚未冻结的独立核验器也曾沿用27假设，必须同步改为这个官方规则并保留修正记录。两阶段 producer 的实际 state 保存不受此审查错误影响。无论补充核验是否通过，结论仍只限公开512 DPT组件的保存完整性，不能变成几何精度或视频质量声明。
