# S76 ROOT_RUN_BINDING 启动核对说明

实际核查：2026-09-09T09:18:23.350351+00:00（UTC）；作者 `/root/next_control_feasibility`。范围是源码、JSON元数据和文件stat；本说明没有创建实际绑定、没有启动模型、没有读取权重、NPY/NPZ或RNG状态正文。没有访问DeepSeek私有state。主账由root维护。

## 1. 准确消费关系

`observe_single_yaw.py` 的 `main()` 读取同目录 `ROOT_RUN_BINDING.json`，要求命令行唯一参数等于该文件**完整字节**SHA256，然后直接使用：

- `status`：必须严格为 `ACCEPTED_S76_SOURCE_SET`。
- `reviewed_files_sha256`：绝对路径到文件SHA256的映射。逐个实际读取并校验该映射中的文件。
- `argv`：必须与下方四项列表逐项、逐字相等。解释器保持venv词法路径，不解析成基础Python。

**清单完整性由root负责**：observer不检查必备成员是否齐全。依据不同作者 `SOURCE_REVIEW_01.json` 的限制，应至少绑定三个程序、合同、固定规则、运行协议共六文件，加这份独立审查JSON。下面的范式已包含全部七项。可增加实际验收时间、root说明和审查MD，额外字段不会改变现有消费逻辑。

worker `run_single_yaw.py` 自己不读取ROOT_RUN_BINDING；它只要求单个合同SHA参数，然后按合同/S70清单核验源码和输入。因此实际运行走observer，不能以直接worker调用替代资源监视。

## 2. 最小且完整的JSON范式

以下是**供root独立读代码后创建**的内容，不是已发生的root验收。本说明文件不充当ROOT_RUN_BINDING。

```json
{
  "status": "ACCEPTED_S76_SOURCE_SET",
  "reviewed_files_sha256": {
    "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S76_relative_camera_response/run_single_yaw.py": "a3a049c6a42ac05cb830379c6e1c6b2a096e24a24f887f9c367094c23957821c",
    "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S76_relative_camera_response/score_single_yaw.py": "5236e28c3c2ed15dceb538ee34b481d8cbe1a4eb751e5b121c9f00b68405c469",
    "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S76_relative_camera_response/observe_single_yaw.py": "88e481a0b06aec34a4b0c9332215957693cff9636a0af2a80740f2e29eebd43a",
    "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S76_relative_camera_response/RUN_CONTRACT.json": "7b0216596bd3c8859d5a0c3a864c47efa28c1c37b9fbf2beef3a50ee2de23d54",
    "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S76_relative_camera_response/pilot_rules.py": "1da603e68a1c427231f491309a412c7cb005e2b460c4eccad436318b9484a326",
    "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S76_relative_camera_response/PROTOCOL_RUN_V1.md": "eb0bfefe1b5c17025d8ff33f15f524703db3f873a690d65a83a8bdbce65b335d",
    "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S76_relative_camera_response/SOURCE_REVIEW_01.json": "4290a2831894637f5e91021af87e8de1597026a57ef17288317805af13c0a73f"
  },
  "argv": [
    "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/.venv-cut3r/bin/python",
    "-B",
    "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S76_relative_camera_response/run_single_yaw.py",
    "7b0216596bd3c8859d5a0c3a864c47efa28c1c37b9fbf2beef3a50ee2de23d54"
  ]
}
```

root最终写定后计算绑定文件SHA；SHA通过observer参数传入，不在JSON内设置自引用SHA。记录真正的验收时间，不复用本说明作者核查时间冒充root验收时间。实际绑定宜设0444。

## 3. 启动前清单

1. root完整读最终源码和独立review，确认所接受的七文件SHA仍等于上述值。不同作者review状态是 `PASS_S76_SOURCE_REVIEW`、blockers为空；这不是已运行验收。
2. 确认仅新生成一个+5度yaw臂，目标20–23、历史顺序19/18/13/12、同相机中心/K/外观输入；复用旧A0，不重跑成功基线。固定图像网格随机流，不搬运/插值噪声；相机修改传入原完整condition和MultiviewCFG。
3. 保留解释器 `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/.venv-cut3r/bin/python`，工作目录 `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling`。合同Python3.12.14，S70包版本在INPUTS.json中、运行时由原load_code核验；本次没有导入数值库或检查运行时版本。observer依赖psutil，root可仅查发行包元数据。
4. 此次stat观察ROOT_RUN_BINDING、execution_01、external_01、scoring_01存在状态为 `{"ROOT_RUN_BINDING.json": true, "execution_01": true, "external_01": true, "scoring_01": false}`。启动前再次检查。execution_01和external_01都必须不存在；如果已出现，不删除、不覆盖、不自动重试。scoring_01须留给之后的一次评分。
5. 合同必须原值：worker3540秒、observer3600秒；RSS48318382080字节（45GiB）；最少空闲磁盘10737418240字节（10GiB）。这是**空闲空间下限**，不是输出大小上限。本次可用磁盘1323201273856字节，属瞬时观察。
6. observer预设离线环境，每0.5秒监测子进程树RSS/空闲磁盘。RSS是采样限额，不能声称瞬时硬上限。进程组kill/reap已编写但尚未本次实际验证；不将S75的180秒预算套到本轮。
7. root用最终绑定SHA启动observer，保留实际运行时间与PID/资源监视。启动命令形状如下，`ACTUAL_BINDING_SHA256`由root替换成实际新绑定文件SHA；本说明未执行此命令。

```sh
"/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/.venv-cut3r/bin/python" -B "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S76_relative_camera_response/observe_single_yaw.py" ACTUAL_BINDING_SHA256
```

## 4. S70资源在盘核查

22个源码/元数据引用逐项实际读回SHA一致（其中同一路径可能被不同清单重复绑定，不能当22个独立实验）。具体路径/哈希见伴随receipt。旧receipt记载A0完整50步、旧exact replay与共同实际随机流通过；本次只核该元数据绑定，没有重放。

以下全部文件存在、可读且为普通文件；有已记录文件大小的项目均相符。**这些权重/数组/状态文件只有stat；其内容SHA本次没有重新计算，更未加载。** 真实worker随后会按冻结路径读取所需输入并验内容，不能把stat当作实际加载成功。

| 资源 | 精确路径 | 实际文件字节 | 与旧文件大小一致 |
|---|---|---:|---|
| vmem | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/data/vmem_recovery/xet_attempt4_01/vmem_weights.pth` | 5056346672 | True |
| vae_config | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/data/vae_official_ft_mse/config.json` | 547 | True |
| vae_weight | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/data/vae_official_ft_mse/diffusion_pytorch_model.safetensors` | 334643276 | True |
| S69_geometry | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S69_tum_camera_conditioning/execution_01/geometry.npz` | 6392766 | True |
| common_rng | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S70_fixed_context_generation/execution_01/common_rng.json` | 61653 | True |
| model_baseline | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S70_fixed_context_generation/execution_01/model_baseline.json` | 829809 | True |
| A0_noise | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S70_fixed_context_generation/execution_01/A0/noise.npy` | 663680 | 未给文件大小 |
| A0_sampler_entry_rng | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S70_fixed_context_generation/execution_01/A0/sampler_entry_rng.json` | 61643 | True |
| A0_terminal_rng | `/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S70_fixed_context_generation/execution_01/A0/terminal_rng.json` | 61641 | True |

A0 `noise.npy` 元数据只给body字节/文件SHA，没有文件size字段；本次stat663680字节，不能把663552个body字节当文件大小。同理bodySHA与fileSHA不可混用。

旧元数据中的目标签名：

- common RNG canonical state：`fdeb6b7bff4162a76a083c00479f649f4dc24e5e34325766dee33d360341ad71`。
- A0 initial noise body：`19a3d567421dd5c088f4a254dcd9c8c7effb2d02773d520830b12e9bae1d86b7`。
- sampler entry canonical state：`f6be7cccc05e6826d371fbe8c53ac19d99028f6a0f985a9f060fa59b0f70e98b`。
- terminal canonical state：`90c571ab6fbb02431b9575c6c6d843b73a0e146d0554299e6f9de321b3c04b7a`。

worker恢复的是旧common_rng真实状态；入口noise body/entry状态、全部50步before/after状态与terminal状态须实际一致。A0没有保存每步epsilon正文，因此不能声称做了逐epsilon字节比较。模型value/modes哈希可跨进程核，指针/id仅在新进程内前后核。

## 5. 返回后的必要分界

先检查external返回码0、stop_reason为null、worker状态 `COMPLETE_SINGLE_YAW_FIXED_STREAM`，实际stream_identity_pass/model_unchanged成立，再由不同作者核所存条件/H/随机流/模型值。失败与局部输出完整保留，失败不送评分器冒充完成。

之后评分参数依次为合同SHA、实际生成receipt SHA、实际external receipt SHA；root在外部施加60秒期限，内置55秒只在代码边界检查。评分器创建scoring_01，保留全部四目标、匹配可用率、无定义值以及同一匹配点上的identity对H残差；不得看结果后换角度、阈值或删困难目标。

```sh
"/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/.venv-cut3r/bin/python" -B "/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S76_relative_camera_response/score_single_yaw.py" 7b0216596bd3c8859d5a0c3a864c47efa28c1c37b9fbf2beef3a50ee2de23d54 ACTUAL_GENERATION_RECEIPT_SHA256 ACTUAL_EXTERNAL_RECEIPT_SHA256
```

任何方向性正结果只属于一个已见场景、一个固定随机实现的全系统相机干预诊断；不证明噪声严格H等变、不证明全局相机校准、不改变S73 UNKNOWN，也不成立新方法。本说明只解决启动绑定接线与已有资源位置，实际运行和科学结果仍待root完成。
