# S14E 封存后评分接口

评分程序 `scripts/score_s14e_depth.py` 不运行模型、不拟合尺度、不读目标 RGB。尺度唯一采用 `work/S14E_calibration_audit/scale_definition_clarification.md` 的 `s_model_per_metric`，主预测为新调用1—4的 self-z/s。调用0为旧 Q0 zero 恢复控制，不计质量样本。

## 静态合同与动态封存

静态 JSON manifest 必须在 prepare/model 真实执行之前写好。示意结构（所有路径必须绝对且 resolve 后不变；真实值由根冻结）：

```json
{
  "schema": "s14e-score-manifest-v1",
  "frozen_utc": "UTC ISO timestamp with timezone",
  "runner": "/absolute/scripts/score_s14e_depth.py",
  "python": "/absolute/.venv-cut3r/bin/python",
  "identities": {"/absolute/scripts/score_s14e_depth.py": "SHA256", "/absolute/target_depth.png": "SHA256"},
  "model_result_dir": "/absolute/new_model_result",
  "prepare_result_dir": "/absolute/new_prepare_result",
  "targets": [
    {"query_index": 20, "depth_path": "/absolute/depth20.png", "depth_sha256": "SHA256"},
    {"query_index": 21, "depth_path": "/absolute/depth21.png", "depth_sha256": "SHA256"},
    {"query_index": 22, "depth_path": "/absolute/depth22.png", "depth_sha256": "SHA256"},
    {"query_index": 23, "depth_path": "/absolute/depth23.png", "depth_sha256": "SHA256"}
  ]
}
```

identities 至少包含 scorer 自身和全部4张GT PNG；其余审查/控制源码可以一并冻结。不向 scorer 提供目标 RGB 路径。固定数值合同内置源码：uint16 PNG 480×640 /5000，nearest resize 299×224，crop[37,0,261,224]，224²全部非零GT，不腐蚀/裁深度/拟合/置信过滤。

根在两阶段成功后生成动态组合 seal：

```json
{
  "schema": "s14e-combined-prediction-seal-v1",
  "sealed_utc": "UTC ISO timestamp with timezone",
  "identities": {"/absolute/every_prediction_payload_or_metadata": "SHA256"}
}
```

组合 seal 要包含 model/prepare 两结果目录中当前的全部文件，尤其各自run_metadata、模型5次调用/合并输出/状态、condition.npz、alignment、baselines和prepare seal。GT不属于预测seal。scorer核外部传入seal SHA、全部预测文件SHA、目录完整覆盖、两阶段SUCCESS与各自payload输出hash、parity通过，再核时间 `static frozen < prepare started ≤ prepare completed < seal < scoring started` 及model对应顺序。

任何GT hash/read前还核跨阶段消费关系：model的sealed frozen_manifest中condition_npz/condition_seal路径必须指向该prepare目录，身份等于组合seal；prepare condition_seal完整payload与组合seal一致，含成功metadata/原prepare manifest身份；`prepare completed ≤ condition sealed ≤ model started`。两个目录各自成功不能替代同相机/同尺度的绑定。

```text
python score_s14e_depth.py --manifest STATIC.json \
  --prediction-seal COMBINED.json --prediction-seal-sha256 ROOT_VERIFIED_SHA \
  --output FRESH_DIRECTORY
```

预测seal与时间检查通过以前，scorer不会打开GT文件（包括GT hash）。验证完成后核静态身份（含4GT hash），读取全部预测/尺度，再首次解码4GT。记录seal_verified_utc、first_target_depth_hash_utc、first_depth_open_attempt_utc、各读取尝试/成功、异常与前后SHA。后验SHA改变会使整个评分状态FAILED，保留已输出数组和失败时间。

## 消费与输出

prepare：`alignment.json["s_model_per_metric"]` 为有限正float；`baselines.npz`严格两个float64(4,224,224)数组：`history_zbuffer_m`、`history_constant_m`。空洞可为NaN；非正/非有限预测按缺失计。模型：`query_call_1.npz`至`query_call_4.npz`各只解码`pts3d_in_self_view`，要求float32(1,224,224,3)。模型metadata schema `s14e-state-reuse-queries-v1`；prepare schema `s14e-known-camera-prepare-v1`。

`arrays.npz`：`gt_depth_m`(4,H,W)，`prediction_depth_m`(4,3,H,W)，`gt_valid_mask`(4,H,W)，`prediction_positive_finite_mask`/`own_valid_mask`/`delta1_success_mask`(4,3,H,W)，`common_valid_mask`(4,H,W)。方法顺序固定 ray、history_zbuffer、history_constant。每张GT完成即保存对应`per_query_arrays/query20..23.npz`，保证中途失败仍有实际完成产物。

`metrics.json/csv`保存4×3全部12行：query/call/method、GT有效数、预测正有限数、own/common像素数、δ1成功数、全GT域δ1、coverage、own与common的MAE(m)/AbsRel/RMSE(m)。δ1严格`max(p/g,g/p)<1.25`，缺预测为失败。own误差只在该方法/GT交集；common误差只在3方法/GT共同交集。空域为null并明确status；极端非有限算术也返回null/status，不能写虚假零误差。每种方法附四query等权均值和每个均值实际可用query数，不把像素或query当独立场景。

所有约定的参数、完整12行、封存时间、读取记录及输出SHA写入run_metadata和metrics。score没有读取query0恢复控制数组，不把它混入4质量query。schema或完整性失败会保留FAILED目录，不覆盖旧输出。人工边界检查在独立`work/S14E_score_preparation/`，不读取真实数组/PNG。
