# 研究想法汇总(汇报用)

**日期:** 2026-09-19 → 09-20 · **算力消耗:** 0 GPU-hours · **外部复核:** 12+ 轮 GPT-6 Astra(ultra)

本文件汇总本阶段提出并检验的全部想法,**包括被推翻的**。技术名词与引用保留英文。
配套材料:`docs/LIFECYCLE_AUDIT_CLOSEOUT_20260919.md`(技术收口)、`RESEARCH_MEMORY.md`(逐条账本)。

---

## 一、出发点:方法方向为何全部关闭

固定约束:**consumer 冻结**(VMem,arXiv:2506.18903)——不训练、不微调、不加新权重、不改上游源码。

把"可能的干预位置"穷举为八条轴,逐条做占据性检索:

| 轴 | 内容 | 状态 |
|---|---|---|
| (a) | 证据读取 / 检索 | **OCCUPIED** + 额外代数受限 |
| (b) | 条件化表示 | OCCUPIED(EscherNet 2402.03908、PRoPE 2507.10496) |
| (c) | 持久状态表示与写入 | OCCUPIED(VMem、GEN3C) |
| (d) | 请求视图分解 | OCCUPIED(2205.11495、SEVA 2503.14489) |
| (e) | 跨调用转移动力学 | OCCUPIED(Self Forcing 2506.08009、Steady-Forcing 2606.14732) |
| (f) | 几何—生成耦合 | OCCUPIED(GEN3C 2503.03751、Voyager 2506.04225) |
| (h) | 调用内推理动力学 | OCCUPIED(Diffusion Forcing 2407.01392) |
| **(g)** | **测量与评价** | **从未评估** —— 被 owner 贡献类型要求排除,**不是被文献占据排除** |

**代数结果一(数值验证,误差 4.4e-16):** 在"共同目标平方误差"融合目标下,
误差矩阵项对最优权重**零额外信息**(`M + c·11ᵀ` 不改变最优解)。
轴 (a) 上一大类加权融合方案**数学上先天退化**,与工程实现无关。

**代数结果二(同样数值验证):** 跨调用目标**不能**约化为单步风险之和。
`A₁=diag(2,¼)` 下 `‖A₂ᴬA₁‖₂ = 4.0` vs `‖A₂ᴮA₁‖₂ = 0.5`,而**单步奇异值谱完全相同**。
这是轴 (e) 未被同一代数杀死的原因。

**结论:** 松开 C1–C5 也够不着未被占据的方向;且最小 pilot 约 800 GPU-hours、
原型级约 3000,需独立 held-out 数据,**本学期不可完成**。

---

## 二、转向:一个新的研究对象

> **已发布的有状态视频/世界模型系统,其 reset 与状态隔离语义不完整:
> 一条调用路径写入的实例状态,在另一条路径被读取,而公开的重置路径不清除它。**

### 核心产物:审计四元组(四项必须属于同一案例)

```
(writer on call A, public sequence A→B, exact consumer on B,
 dominance check showing no recompute/overwrite/reset covers it)
```

**两个方向的错误都真实:**
- "字段没出现在 `reset()` 里" **⇏** 缺陷 —— CausVid 每次调用重算位置;
- "存在显式重置" **⇏** 干净 —— GEN3C 清了内层标志,外层准入标志从不清除。

该规则经实战检验:正确地把 CausVid 从 HIT 重分类为 CLEAN。

---

## 三、检验结果(审计框 N = 20)

| 判定 | 计数 |
|---|---|
| 静态 HIT | **2** — VMem、GEN3C |
| NEAR | 2 |
| CLEAN | 15 |
| SUSPECT-UNTRACED | 1(Matrix-Game 1) |
| **冻结权重下已测** | **0** |

**便利样本,不是抽样框;不支持任何 prevalence 主张。**

### 两个案例互补而不重叠

| | oracle | 实测后果 |
|---|---|---|
| **GEN3C**(CVPR 2025 Highlight,NVIDIA) | ✅ 公共准入不变量 `model_seeded ⇒ usable cache`;**单向就绪闩锁守卫可清空资源** | ❌ 无 |
| **VMem** | ❌ 无可辩护公共 oracle | ✅ `+0.245 dB`(14 窗口 × 2 seed) |

**不能拼接:** `(oracle, 无后果) + (后果, 无 oracle) ≠ (oracle 且 后果)`。

### GEN3C 机制(逐行核实)

```python
# gui/api/server_cosmos_base.py:46-71
if self.pose_history_w2c:
    self.model.clear_cache()          # :53  缓存已清
model_result = seeding_method(...)    # :62-70  可抛异常
self.model_seeded = True              # :71  仅成功后才写
```

异常一抛:缓存已空、标志仍为上次的 `True`,`/request-inference` 照常放行。
全仓库 grep:`model_seeded = False` **仅在 `__init__`**。
最有说服力的细节:`clear_cache()` **清了模型的 `model_was_seeded`,没清服务端的 `model_seeded`**。

**两个系统在上游均无人报告**(独立检索两次,零匹配)。

---

## 四、被推翻的想法(7 条)

| 想法 | 为何被推翻 |
|---|---|
| CausVid 是 HIT | KV cache 无索引字段,位置每次调用重算 |
| 构造器等价 oracle | "字段不在 `reset()`"只是信号不是证据 |
| 跨层近名字段 oracle | oracle 强度排序仅列第 4,不能单独定罪 |
| 后继实现声明 oracle | Self-Forcing 补的重置管的是 CausVid 从未有过的字段 |
| "Choose New Image" oracle | 带标签的会话控件是审计者推断,不是被陈述的合同 |
| "retrieval 路线零 GPU" | 构造器加载 VMem/VAE/CLIP/CUT3R,档案脚本硬编码 `device='cuda'` |
| PlayGen 可升级 HIT | 键是每连接新生成的 SID,残留条目无路径可读 |

**撤回多于留存,但没有一条是被外部拆穿的。**

---

## 五、方法论产出(可迁移)

1. **执行前对抗审查** —— 两次拦截:一次拦下"你证明的是自己桩的行为";一次拦下为有限增量搭重依赖环境。
2. **外部复核必须直接访问原始对象** —— 让其在仓库内自行算哈希、检索,而非读转述。
3. **数字必须随身携带估计量** —— 相差 0.003 dB 的两个对比,错配无法被直觉察觉。
4. **"提交成功" ≠ "提交了我以为的内容"** —— 发生过真实记录丢失;已加并发写入者守卫与强制回读验证。

---

## 六、当前状态与下一步

**owner 已松开 C6** —— 贡献不再必须是 method。解锁了:

> **轴 (g) 是八条轴中唯一占据状态未知的一条。**
> 它被标为"排除"的原因是**贡献类型要求**,不是文献占据。

项目已有的 order-invariance gate(11/11 含非空性)、pre-scoring census、byte-identity gate、
pre-declared discard、审计四元组,**全部属于 (g3) 实验有效性机制**
——当初作为基础设施建造,**从未被当作贡献呈现**。

**如实说明的限制:** 即便 C6 松开,现有材料仍未达可发表诊断贡献门槛。
区分"能发"与"发不出去"的三项是:**结论影响 · 跨系统外部效度 · 可被他人采用的 artifact**。
本项目:静态 2/20、实测 0/20、无 conclusion impact、artifact 无外部采用。

**未变更:** `new_method_validated=false` · `novelty_authorization=NONE` ·
800 GPU-hour 维持撤回 · 禁止对外联系 maintainer。
