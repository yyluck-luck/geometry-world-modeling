"""Seal the already-selected 16 RGB files; do not open sensor-depth PNGs."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
OUT = ROOT / 'work/S32_input_freeze'
SOURCE = ROOT / 'work/S32_selection/selected_windows.json'
EXPECTED = '4574c2635851e83f5389da0d099819e7cbfd2ad9b8fe543ddf163e0fbf7e6cc6'

def now():
    return datetime.now(timezone.utc).isoformat()

def sha(data):
    return hashlib.sha256(data).hexdigest()

started = now()
raw = SOURCE.read_bytes()
assert sha(raw) == EXPECTED
data = json.loads(raw)
OUT.mkdir(exist_ok=False)
assert len(data['windows']) == 4
rgb_receipts = []
for window in data['windows']:
    assert len(window['frames']) == 4
    for frame in window['frames']:
        path = Path(frame['path'])
        assert path.parent.name == 'rgb' and path.suffix == '.png'
        content = path.read_bytes()
        assert content[:8] == b'\x89PNG\r\n\x1a\n'
        frame['sha256'] = sha(content)
        frame['RGB_byte_identity_status'] = 'ACTUAL_BYTES_SEALED_NO_PIXEL_DECODE'
        rgb_receipts.append(dict(window=window['id'], index=frame['index'], path=str(path), bytes=len(content), sha256=frame['sha256']))
        assert frame['sensor_depth_association']['sha256'] is None
data['parent_selection_sha256'] = EXPECTED
data['RGB_byte_seal'] = dict(started_utc=started, completed_utc=now(), RGB_files_read=16, RGB_pixels_decoded=0, sensor_depth_PNG_files_read=0, prediction_NPZ_files_read=0, model_forward_calls=0, GA_runs=0, original_window_metadata_status_retained=True)
target = OUT / 'selected_windows_rgb_sealed.json'
target.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
receipt = dict(status='RGB_INPUTS_SEALED_ONLY_NOT_RUN_APPROVAL', started_utc=started, completed_utc=now(), source=str(SOURCE), source_sha256=EXPECTED, artifact=str(target), artifact_sha256=sha(target.read_bytes()), script_sha256=sha(Path(__file__).read_bytes()), RGB_files=rgb_receipts, sensor_depth_PNG_files_read=0, missing_pose_window='fr2_desk_j1', missing_pose_policy='A_RGB_inference_allowed_B_all_three_endpoints_NA_no_replacement')
(OUT/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
sys.path.insert(0,str(ROOT/'scripts'))
from research_log import append_event
append_event('S32 固定窗口与16张RGB实际字节封存', '按预先时间索引规则选定 fr2_desk 987–990/1974–1977 与 fr1_xyz 264–267/529–532。fr2_desk_j1 无严格20ms相机配对，保留A推理、B三端点NA，不替换窗口。根代理实际读取并SHA封存16张RGB字节，未解码像素、未读sensor深度PNG或预测数组，未运行模型/GA。原选择记录保持不变；两场景已使用，不能称盲测。', evidence=[str(SOURCE),str(target),str(OUT/'receipt.json')], next_step='冻结原VMem入口的A脚本，经独立源代码检查后，对每窗一次真实CPU推理。', occurred_at=receipt['completed_utc'], time_source='actual local UTC clock and input read receipt')
print(json.dumps({k:v for k,v in receipt.items() if k!='RGB_files'},ensure_ascii=False))
