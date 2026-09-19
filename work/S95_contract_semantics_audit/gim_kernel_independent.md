# GIM-World Eq. (16–18) 独立数学审查

- **审查时间**：2026-09-12（Asia/Shanghai）
- **审查角色**：独立数学/实验合同审查，不是 GIM-World 作者代码的复现结果。
- **审查对象**：GIM-World arXiv v1 的 Eq. (16)–(18)，以及作者公开仓库当前 HEAD 中的 `gim/utils/pruning.py`。
- **科学边界**：下面的反例只说明“按论文定义的角度平方高斯核没有普遍的 GP 正定保证”，不能单独推出 GIM-World 的 MIND 结果错误，也不能推出作者的全部实现或实验无效。

## 1. 论文和公开实现核对

论文 Eq. (16) 定义了 pose-time kernel：

```text
k(c_i,c_j) = exp(-||p_i-p_j||^2/(2 sigma_p^2)
                 - angle(f_i,f_j)^2/(2 sigma_r^2)
                 - (t_i-t_j)^2/(2 sigma_t^2)).
```

作者公开仓库的 `gim/utils/pruning.py`（commit `6d9b2090569e7d450d3baedc09ff82f662ad9ea2`）确实计算

```python
d_ang = np.arccos(np.clip(fwd @ fwd.T, -1.0, 1.0))
K = np.exp(-0.5 * (d_pos / sigma_p) ** 2) \
    * np.exp(-0.5 * (d_ang / sigma_r) ** 2)
```

并在矩阵对角线上加 `jitter=1e-4`。源码注释把该矩阵称为 `PSD kernel`，但代码本身没有证明角度平方高斯项在球面上的普遍正定性。源码 URL：

<https://raw.githubusercontent.com/nagara214/GIM-World/6d9b2090569e7d450d3baedc09ff82f662ad9ea2/gim/utils/pruning.py>

项目 README 说明，剪枝采用 pose–time Gaussian-process kernel；论文项目页和仓库都将该剪枝作为推理路径的一部分。该审查没有把“公开代码可下载”误写成“已经在本项目环境成功运行”。

## 2. 四方向反例

取四个单位前向方向（都在同一个大圆上）：

```text
f_0=(1,0,0), f_1=(0,1,0), f_2=(-1,0,0), f_3=(0,-1,0).
```

令四帧的相机位置 `p_i` 完全相同、时间 `t_i` 完全相同，因此位置和时间因子都为 1。令角度带宽 `sigma_r = pi`。相邻方向的球面角是 `pi/2`，相对方向的角是 `pi`，所以

```text
a = exp(-(pi/2)^2/(2*pi^2)) = exp(-1/8) = 0.8824969026,
b = exp(-pi^2/(2*pi^2))       = exp(-1/2) = 0.6065306597.
```

得到 Gram 矩阵

```text
K = [[1, a, b, a],
     [a, 1, a, b],
     [b, a, 1, a],
     [a, b, a, 1]].
```

它是循环矩阵，特征值为

```text
lambda_0 = 1 + 2a + b = 3.37152446,
lambda_1 = lambda_3 = 1 - b = 0.39346934,
lambda_2 = 1 - 2a + b = -0.15846315.
```

因此 `K` 明确不是正半定矩阵。这里不是浮点舍入造成的现象：最小特征值约为 `-0.158`，远大于 `1e-4` 的 jitter 量级。

### Jitter 不能自动修复该反例

加上源码默认的 `1e-4 I` 后，最小特征值仍为约 `-0.15836315`。要把这个四点矩阵整体推到正半定，至少需要约 `0.158464 I` 的对角修正；这已明显改变先验协方差，而不是一个“数值微扰”。

## 3. Schur complement / GP 条件方差

对 `A={0,1,2}`、查询帧 `h=3`，子矩阵 `K_AA` 的特征值约为

```text
0.01890890, 0.39346934, 2.58762175,
```

所以这个三阶主子矩阵本身仍是正定且可逆。但按 Eq. (17) 计算的条件方差是

```text
sigma^2(h|A)
 = K[3,3] - K[3,A] K_AA^{-1} K[A,3]
 = -4.29633675.
```

负的“方差”直接说明：全矩阵不是合法协方差矩阵，GP 后验解释在此集合上失效。等价地，`det(K)<0`，而 `det(K)/det(K_AA)` 正是上述 Schur complement。

另一个较小集合 `A={0,2}` 对 `h=1` 给出 `sigma^2=0.03045637`，说明某些局部主子矩阵仍可能产生看似正常的值；这不能恢复全局正定性，也说明只检查一次局部方差不足以给出理论保证。

源码的 `_greedy_mi` 还直接求 `np.linalg.inv(K)`。在上述四点矩阵中，`diag(K^{-1})=-0.23275643`。代码随后使用

```python
var_r = 1.0 / np.maximum(np.diag(M), 1e-12)
```

于是负对角元素会被截到 `1e-12`，产生约 `1e12` 的数值，而不是合法的 GP 条件方差。这是实现行为的审计提示，不是作者 MIND 运行日志，也不应被报告为作者实际实验已经出现了该数值。

## 4. 与有效 chordal RBF 的比较

把方向向量直接视为欧氏空间中的点，使用 chordal distance：

```text
k_dir_chordal(f_i,f_j)
 = exp(-||f_i-f_j||_2^2/(2 ell_f^2)).
```

因为 `f_i` 已嵌入 `R^3`，这是标准欧氏 RBF 核，必为正定。位置和时间也使用欧氏 RBF，三者相乘仍由 Schur product theorem 保持正定：

```text
k_valid = k_pos * k_dir_chordal * k_time.
```

若希望让反向视角 `theta=pi` 的指数衰减与 Eq. (16) 一致，可取 `ell_f = 2 sigma_r/pi`，因为 `||f_i-f_j||^2=4 sin^2(theta/2)` 且反向时距离平方为 4。对于本反例 `sigma_r=pi`，即 `ell_f=2`，四点 chordal Gram 矩阵的特征值约为

```text
0.04892909, 0.39346934, 0.39346934, 3.16413223,
```

全部为正。这个替代核保留了方向相似性和固定预算剪枝思路，同时恢复了 GP 协方差和 Schur complement 所需的数学基础。

另一种可选路线是使用球面上的已知正定 heat kernel；若采用 Laplacian/geodesic 指数核，则必须明确其参数和正定条件，不能把“角度距离平方的 Gaussian”直接当成同等合法的球面 GP 核。

## 5. 审稿式结论和后续判别实验

1. **已确认**：Eq. (16) 的角度平方高斯核在一般球面方向集合上没有普遍 PSD 保证；四方向反例给出一个明确负特征值，且默认 jitter 不足以修复。
2. **已确认**：在同一反例上，Eq. (17) 可产生负条件方差；因此 Eq. (18) 的 GP 互信息/次模最优性论证不能无条件套用。
3. **尚未确认**：作者 MIND 数据的实际相机方向、带宽和剪枝池是否触发负特征值；也没有确认作者报告的长视频结果因此受到影响。
4. **不应声称**：不能据此声称“GIM-World 实验错误”“GIM-World 代码必然崩溃”或“GIM-World 结果无效”。这需要在作者公开数据/可运行环境中完成数据级 Gram 谱审计，并把原始核与有效替代核在相同权重、相同预算和相同随机性下比较。
5. **建议的最小审计**：对每个真实 pruning pool 保存 `min_eig(K)`, `min_eig(K+jitter I)`, 负特征值个数、`diag(inv(K))`、Schur variance 最小值和选中帧；若出现负谱或负 Schur variance，再运行 chordal RBF 对照。该审计属于 GIM-World 近邻/实验合同审查，不是本项目 GRC-Memory 的方法验证。

## 原文依据

- GIM-World arXiv HTML（Eq. 15–18）：<https://arxiv.org/html/2606.02436v1>
- GIM-World 官方项目页：<https://gim-world.github.io/>
- GIM-World 官方代码（当前公开仓库）：<https://github.com/nagara214/GIM-World>
- Feragen, Lauze & Hauberg, *Geodesic Exponential Kernels: When Curvature and Linearity Conflict*, CVPR 2015：<https://openaccess.thecvf.com/content_cvpr_2015/html/Feragen_Geodesic_Exponential_Kernels_2015_CVPR_paper.html>

Feragen 等人的结论边界是：对一般 geodesic metric，平方距离的 geodesic Gaussian 只有在平坦情形才有“所有带宽都正定”的普遍保证；球面属于弯曲流形。该定理支持“不能默认 PSD”，而本文件的四点矩阵则提供了当前参数下的具体有限反例。
