"""Read existing retrieval geometry/numeric maps; never RGB/model tensors."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import struct
import time
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
ARCHIVE = ROOT / 'results/S47B_C2_confirmation_generation_v9/archive'


def tree(node):
    kind = node['kind']
    if kind == 'dict':
        return {tree(p['key']): tree(p['value']) for p in node['items']}
    if kind in ('tuple', 'list'):
        return [tree(p) for p in node['items']]
    if kind == 'scalar':
        return node['value']
    if kind == 'python_float64':
        return struct.unpack('<d', bytes.fromhex(node['little_endian_hex']))[0]
    assert kind == 'tensor'
    return node


def main():
    start = datetime.now(timezone.utc).isoformat(); timer = time.monotonic()
    paths = [ARCHIVE/'events.jsonl',
             ROOT/'results/S47B_C2_confirmation_generation_v9/trace/events.jsonl',
             ROOT/'work/S47B_c2_confirmation_generation_v9/execution_01/worker_receipt.json',
             ROOT/'work/S47B_c2_confirmation_generation_v9/review_attachment_01/manifest.json',
             ROOT/'work/resumption_20260909/C2_V9_EXTERNAL_LAUNCH/receipt.json',
             ROOT/'work/S20_environment/isolated_vmem_source/modeling/pipeline.py',
             ROOT/'work/S20_environment/isolated_vmem_source/navigation.py',
             ROOT/'work/S35_generation_integration/integrate_original.py']
    source_hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in paths}
    manifest = json.loads(paths[3].read_text())
    for p in paths[5:]:
        assert manifest['source_identities'][str(p)] == source_hashes[str(p.relative_to(ROOT))]
    captures = {e['seq']: e for e in map(json.loads, paths[0].read_text().splitlines())}
    assert captures[58]['payload']['name'] == 'render_input'
    assert captures[60]['payload']['name'] == 'render_output'
    assert captures[62]['payload']['name'] == 'retrieval_output'
    ri = tree(captures[58]['payload']['tree'])
    ro = tree(captures[60]['payload']['tree'])
    retrieved = tree(captures[62]['payload']['tree'])
    nms = tree(captures[64]['payload']['tree'])
    numeric_reads = {}; cache = {}
    def numeric(d, label):
        assert d['kind'] == 'tensor' and d['dtype'] in ('float32', 'float64', 'int32')
        assert d['shape'] in ([3], [], [4, 4], [1], [288, 512])
        path = ARCHIVE / d['blob']
        if d['blob'] not in cache:
            payload = path.read_bytes()
            digest = hashlib.sha256(payload).hexdigest()
            assert digest == d['bytes_sha256'] and len(payload) == d['nbytes']
            cache[d['blob']] = np.frombuffer(payload, np.dtype(d['dtype']).newbyteorder('<')).reshape(d['shape']).copy()
            numeric_reads[d['blob']] = dict(nbytes=len(payload), sha256=digest, labels=[])
        numeric_reads[d['blob']]['labels'].append(label)
        return cache[d['blob']]
    surfels = ri['map']['surfels']
    positions = np.array([numeric(s['position'], 'surfel_position') for s in surfels])
    normals = np.array([numeric(s['normal'], 'surfel_normal') for s in surfels])
    radii = np.array([numeric(s['radius'], 'surfel_radius') for s in surfels])
    poses = numeric(ri['args_after_surfels'][0], 'actual_render_pose')
    focal = [float(numeric(d, 'actual_render_focal').item())
             for d in ri['args_after_surfels'][1]]
    output_maps = {k: numeric(v, 'render_output_'+k) for k, v in ro['result'].items()}
    # Exact algebra of pipeline.py:290–318, applied to the actual saved inputs.
    extrinsics = np.zeros((4, 4)); R, t = poses[:3, :3], poses[:3, 3]
    extrinsics[:3, :3] = np.linalg.inv(R)
    extrinsics[:3, 3] = -np.linalg.inv(R) @ t; extrinsics[3, 3] = 1
    cam = (extrinsics @ np.column_stack([positions, np.ones(len(positions))]).T).T
    cam = cam[:, :3] / cam[:, 3:]
    z = cam[:, 2]; fx, fy = focal; cx, cy = ri['kwargs']['principal_points']
    screen_x = fx * cam[:, 0] / z + cx; screen_y = fy * cam[:, 1] / z + cy
    front = z > .1; far = z < 1000.
    sx = (screen_x >= -50) & (screen_x < ri['kwargs']['image_width']+50)
    sy = (screen_y >= -50) & (screen_y < ri['kwargs']['image_height']+50)
    visible = front & far & sx & sy
    normal_len = np.linalg.norm(normals, axis=1)
    rays = positions - t; ray_len = np.linalg.norm(rays, axis=1)
    cosine = np.full(len(normals), np.nan)
    valid_normal_ray = (normal_len >= 1e-12) & (ray_len > 0)
    cosine[valid_normal_ray] = np.sum((rays[valid_normal_ray]/ray_len[valid_normal_ray, None]) * (normals[valid_normal_ray]/normal_len[valid_normal_ray, None]), axis=1)
    # Finite list/index counterexample with actual saved empty frame_count.
    candidates = [frame for frame, count in retrieved['result'][1] for _ in range(count)]
    sorted_frames = list(candidates); nms_loop_entered = False
    try:
        first = sorted_frames[0]
    except IndexError as exc:
        counterexample = dict(exception_type=type(exc).__name__, message=str(exc),
                              candidates=candidates, nms_loop_entered=nms_loop_entered)
    else:
        raise AssertionError('Expected the saved empty case to reproduce the index failure')
    for p in paths:
        assert hashlib.sha256(p.read_bytes()).hexdigest() == source_hashes[str(p.relative_to(ROOT))]
    for blob, v in numeric_reads.items():
        assert hashlib.sha256((ARCHIVE/blob).read_bytes()).hexdigest() == v['sha256']
    def stats(a):
        finite = a[np.isfinite(a)]
        return dict(min=float(np.min(finite)) if len(finite) else None,
                    median=float(np.median(finite)) if len(finite) else None,
                    max=float(np.max(finite)) if len(finite) else None,
                    finite=len(finite), nonfinite=int(a.size-len(finite)))
    receipt = dict(status='ACTUAL_SAVED_NUMERIC_RETRIEVAL_DIAGNOSIS_ONLY',
                   started_utc=start, completed_utc=datetime.now(timezone.utc).isoformat(),
                   elapsed_seconds=time.monotonic()-timer, numpy=np.__version__,
                   source_sha256=source_hashes, source_bindings_match_actual_C2_manifest=True,
                   archive_sequences=[58, 60, 62, 64], surfel_count=len(surfels),
                   surfels_with_empty_source_ids=sum(not s['source_ids'] for s in surfels),
                   actual_render_pose=poses.tolist(), focal=focal, render_kwargs=ri['kwargs'],
                   camera_z=stats(z), radii=stats(radii), normal_length=stats(normal_len), cosine=stats(cosine),
                   culling_counts=dict(positive_z=int((z>0).sum()), z_over_near_point1=int(front.sum()),
                       z_below_far1000=int(far.sum()), screen_x_margin50=int(sx.sum()),
                       screen_y_margin50=int(sy.sum()), positive_z_and_screen=int(((z>0)&far&sx&sy).sum()),
                       combined_visible=int(visible.sum()),
                       visible_nondegenerate_normal=int((visible&(normal_len>=1e-12)).sum()),
                       visible_frontfacing=int((visible&(normal_len>=1e-12)&(cosine>=0)).sum())),
                   saved_render_maps={k:dict(shape=list(v.shape),unique_values=np.unique(v).tolist())
                                      for k,v in output_maps.items()},
                   saved_retrieval_result=retrieved['result'], saved_nms_threshold=nms,
                   list_counterexample=counterexample,
                   numeric_unique_blob_count=len(numeric_reads),
                   numeric_unique_bytes=sum(v['nbytes'] for v in numeric_reads.values()),
                   numeric_reads=numeric_reads, existing_inputs_unchanged=True,
                   RGB_pixel_reads=0, model_loads=0, inference_calls=0, rerasterizations=0,
                   generation_sources_edited=False)
    with (OUT/'NUMERIC_DIAGNOSIS_FINITE_RECEIPT.json').open('x') as f:
        json.dump(receipt,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('numeric_reads','source_sha256')},indent=2))


if __name__ == '__main__':
    main()
