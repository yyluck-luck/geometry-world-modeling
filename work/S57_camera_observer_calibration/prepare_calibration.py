"""Authorized S57 preparation: camera metadata plus one predesignated TUM RGB."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import platform
import sys
import time
import cv2
import numpy as np
from observer import (PARAMETERS, PAIRS, classify, configure, features, observe,
                      normalized_K_to_index, requested_homography, rotation_y, sha, write_json)

D = Path(__file__).resolve().parent
R = D.parents[1]
SOURCE = R/'data/tum/fr2_desk_timestamp_guard/rgbd_dataset_freiburg2_desk/rgb/1311868171.663411.png'
SOURCE_SHA = 'c7127660fd25468f35db330cc3200bf68451cec4e13adef640ee7b16c27f32ee'
ROWS = {'B0': ('S40_declared_variant_generation', 'S40_declared_variant_generation'),
        'C1': ('S44_c1_confirmation_generation', 'S44_C1_confirmation_generation')}
SOURCE_PATHS = ['work/S35_generation_integration/runtime_factory.py',
                'work/S20_environment/isolated_vmem_source/navigation.py',
                'work/S20_environment/isolated_vmem_source/utils/util.py']
YAW = [0., 1.25, 2.5, 3.75, 5., 3.75, 2.5, 1.25, 0.]


def now():
    return datetime.now(timezone.utc).isoformat()


def decode_structure(node):
    kind = node['kind']
    if kind == 'scalar':
        return node['value']
    if kind == 'dict':
        return {decode_structure(i['key']): decode_structure(i['value']) for i in node['items']}
    if kind in ('list', 'tuple'):
        return [decode_structure(i) for i in node['items']]
    return node


def collect_camera_metadata():
    rows, reads = {}, {}
    for row, (workname, resultname) in ROWS.items():
        manifest_path = R/'work'/workname/'review_attachment_01/manifest.json'
        archive = R/'results'/resultname/'archive'
        manifest = json.loads(manifest_path.read_text())
        source_checks = {}
        for name in SOURCE_PATHS:
            p = R/name
            source_checks[name] = dict(actual_sha256=sha(p), frozen_sha256=manifest['source_identities'][str(p)])
            assert source_checks[name]['actual_sha256'] == source_checks[name]['frozen_sha256']
        events = [json.loads(line) for line in (archive/'events.jsonl').read_text().splitlines()]
        commits = [e for e in events if e['event']=='capture_complete' and e['payload']['name']=='cache_commit']
        assert len(commits)==2 and commits[1]['payload']['occurrence']==1
        cache = decode_structure(commits[1]['payload']['tree'])['cache']
        assert all(len(cache[n])==9 for n in ['pil_frames','c2ws','Ks'])
        def read_camera(descriptor, shape):
            assert descriptor['kind']=='tensor' and descriptor['shape']==shape
            assert descriptor['dtype'] in ('float32','float64') and descriptor['byteorder']=='little'
            assert descriptor['nbytes'] <= 128
            p = archive/descriptor['blob']
            payload = p.read_bytes()
            assert len(payload)==descriptor['nbytes'] and hashlib.sha256(payload).hexdigest()==descriptor['bytes_sha256']
            reads[str(p)] = dict(bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
            a = np.frombuffer(payload, dtype='<f4' if descriptor['dtype']=='float32' else '<f8').reshape(shape).astype(np.float64)
            assert np.all(np.isfinite(a))
            return a
        frames = []
        for i in range(9):
            pose = read_camera(cache['c2ws'][i], [4,4]); K = read_camera(cache['Ks'][i], [3,3])
            image = cache['pil_frames'][i]
            assert image['mode']=='RGB' and image['size']==[576,576]
            assert image['pixels']['shape']==[576,576,3] and image['pixels']['dtype']=='uint8'
            frames.append(dict(id=i, c2w=pose.tolist(), K_normalized=K.tolist(),
                               K_opencv_index=normalized_K_to_index(K,576,576).tolist(),
                               pixels_descriptor=image['pixels'], image_png_descriptor=image['png'],
                               pose_descriptor=cache['c2ws'][i], K_descriptor=cache['Ks'][i]))
        poses = np.array([f['c2w'] for f in frames]); Ks=np.array([f['K_normalized'] for f in frames])
        expected = np.repeat(np.eye(4)[None],9,axis=0)
        for i, angle in enumerate(YAW): expected[i,:3,:3] = rotation_y(angle)
        errors = dict(max_plan_pose_error=float(np.max(np.abs(poses-expected))),
                      max_translation=float(np.max(np.abs(poses[:,:3,3]))),
                      max_K_change=float(np.max(np.abs(Ks-Ks[0]))),
                      max_homogeneous_row_error=float(np.max(np.abs(poses[:,3]-[0,0,0,1]))),
                      max_rotation_orthogonality_error=float(np.max(np.abs(poses[:,:3,:3].transpose(0,2,1) @ poses[:,:3,:3]-np.eye(3)))))
        default=np.array([[.5/np.tan(.9424777960769379/2),0,.5],[0,.5/np.tan(.9424777960769379/2),.5],[0,0,1.]])
        errors['max_recorded_K_vs_default_error']=float(np.max(np.abs(Ks-default)))
        valid=all(v<=1e-6 for v in errors.values())
        pair_records=[]
        for i,j in PAIRS:
            H=requested_homography(np.array(frames[i]['K_opencv_index']),np.array(frames[j]['K_opencv_index']),poses[i],poses[j]) if valid else None
            pair_records.append(dict(pair=[i,j], nominal_yaw_difference_degrees=YAW[j]-YAW[i], requested_H=None if H is None else H.tolist()))
        rows[row]=dict(status='RECORDED_NOMINAL_CAMERA_CONVENTION_VERIFIED' if valid else 'UNKNOWN_CAMERA_CONVENTION_OR_NONROTATION',
                       archive_directory=str(archive), generation_manifest_path=str(manifest_path), generation_manifest_sha256=sha(manifest_path),
                       archive_manifest_sha256=sha(archive/'manifest.json'), archive_events_sha256=sha(archive/'events.jsonl'),
                       final_cache_commit_event_sha256=commits[1]['sha256'], source_checks=source_checks, errors=errors,
                       source_image_metadata=manifest['input_image'], frames=frames, pairs=pair_records,
                       physical_image_intrinsics_status='UNKNOWN_UNCALIBRATED_ORIGINAL_PHOTO',
                       declared_K_status='ACTUAL_ARCHIVED_MODEL_DEFAULT_NORMALIZED_K_NOT_PHYSICAL_CALIBRATION',
                       coordinate_convention='index+0.5 VMem grid mapped to index OpenCV coordinates',
                       crop_convention='runtime loads original, area resize cover and centered 576 crop with K=None, then assigns default K to cropped image',
                       generated_pixel_body_reads=0)
    return dict(observed_utc=now(),rows=rows,camera_body_reads_unique=reads,
                unique_camera_body_bytes=sum(v['bytes'] for v in reads.values()),
                generated_pixel_body_reads=0,generated_pixel_bytes_read=0,
                prior_review_scope='Independent new metadata extraction; does not replace existing generation/camera reviews')


def main():
    started=now();timer=time.monotonic();configure()
    out=D/'controls';out.mkdir()
    write_json(D/'PRE_CONTROL_FREEZE.json',dict(created_utc=started,author_role='/root/c2_v9_recovery_author',
              protocol_sha256=sha(D/'PROTOCOL.md'),observer_sha256=sha(D/'observer.py'),
              preparation_sha256=sha(Path(__file__)),parameters=PARAMETERS,pairs=PAIRS,
              source_path=str(SOURCE),source_sha256=SOURCE_SHA,control_source_pixels_read_yet=False))
    metadata=collect_camera_metadata();write_json(D/'CAMERA_METADATA_BINDING.json',metadata)
    payload=SOURCE.read_bytes();assert hashlib.sha256(payload).hexdigest()==SOURCE_SHA
    bgr=cv2.imdecode(np.frombuffer(payload,np.uint8),cv2.IMREAD_COLOR)
    assert bgr is not None and bgr.shape==(480,640,3)
    original=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)
    base=cv2.resize(original[:,80:560],(576,576),interpolation=cv2.INTER_AREA)
    K=np.array([[565.,0.,287.5],[0.,565.,287.5],[0.,0.,1.]])
    angles=[-5.,-1.25,1.25,5.]
    images={'static':base,'blurred_static':cv2.GaussianBlur(base,(13,13),2.)}
    transforms={'static':np.eye(3),'blurred_static':np.eye(3)}
    for angle in angles:
        name=f'yaw_{angle:+g}'
        H=K @ rotation_y(-angle) @ np.linalg.inv(K);H/=H[2,2]
        transforms[name]=H
        images[name]=cv2.warpPerspective(base,H,(576,576),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
    image_files={}
    for name,rgb in images.items():
        p=out/(name+'.png')
        ok,encoded=cv2.imencode('.png',cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR));assert ok
        with p.open('xb') as f:f.write(encoded.tobytes())
        image_files[name]=dict(path=str(p),sha256=sha(p),rgb_sha256=hashlib.sha256(rgb.tobytes()).hexdigest(),
                               actual_H=transforms[name].tolist(),kind='SYNTHETIC_2D_CONTROL_FROM_ONE_REAL_TEXTURE')
    features_by_name={name:features(rgb) for name,rgb in images.items()}
    def measure(name,H):
        return observe(base,images[name],H,features_by_name['static'],features_by_name[name])
    known_correct={name:measure(name,transforms[name]) for name in images}
    write_json(out/'KNOWN_CORRECT_MAPPING_MEASUREMENTS.json',known_correct)
    failures=[]
    eligible=all(m['status']=='MEASURED_UNCLASSIFIED' for m in known_correct.values())
    if not eligible:failures.append('A known mapping cannot be fitted')
    if eligible and any(min(m['source_coverage']['supported'],m['target_coverage']['supported'])<8 for m in known_correct.values()):
        failures.append('A known mapping covers fewer than half of the 4x4 full-frame cells')
    thresholds=None
    if eligible:
        tau=3*max(m['requested']['cell_balanced_median_px'] for m in known_correct.values())
        margin=min(known_correct[f'yaw_{a:+g}']['identity']['cell_balanced_median_px']-known_correct[f'yaw_{a:+g}']['requested']['cell_balanced_median_px'] for a in angles)/4.
        thresholds=dict(residual_limit_px=tau,separation_margin_px=margin,
                        min_matches=max(4,min(m['match_count'] for m in known_correct.values())//2),
                        min_supported_source_cells=min(m['source_coverage']['supported'] for m in known_correct.values()),
                        min_supported_target_cells=min(m['target_coverage']['supported'] for m in known_correct.values()),
                        min_fitted_inlier_fraction=min(m['fitted_forward_inlier_fraction'] for m in known_correct.values())/2.)
        if tau<=0 or margin<=tau:failures.append('Correct motion is not reliably separated from identity')
    calibration=dict(status='CALIBRATED_ON_SINGLE_SYNTHETIC_TEXTURE_ONLY' if not failures else 'CALIBRATION_FAILED',
                     created_utc=now(),thresholds=thresholds,failures=failures,
                     control_K=K.tolist(),control_K_is_synthetic_choice=True,control_K_is_TUM_calibration=False,
                     control_angles=angles,control_images=image_files,source_path=str(SOURCE),source_sha256=SOURCE_SHA,
                     source_preprocessing='640x480 crop[:,80:560] -> 480x480 -> INTER_AREA 576x576',
                     source_image_body_read_count=1,source_image_body_bytes=len(payload),
                     calibration_and_validation_same_texture=True,independent_generalization_validated=False,
                     parameters=PARAMETERS,protocol_sha256=sha(D/'PROTOCOL.md'),observer_sha256=sha(D/'observer.py'))
    cases=[]
    for angle in angles:
        H=transforms[f'yaw_{angle:+g}']
        for kind,name in [('correct',f'yaw_{angle:+g}'),('opposite',f'yaw_{-angle:+g}'),('static','static'),('blurred_static','blurred_static')]:
            m=known_correct[name] if kind=='correct' else measure(name,H)
            verdict=classify(m,calibration)
            case=dict(requested_yaw_degrees=angle,kind=kind,target=name,measurement=m,verdict=verdict)
            cases.append(case)
            if kind=='correct' and verdict!='CONSISTENT_WITH_RECORDED_NOMINAL_REQUEST':failures.append(f'Correct control {angle} failed: {verdict}')
            if kind!='correct' and verdict=='CONSISTENT_WITH_RECORDED_NOMINAL_REQUEST':failures.append(f'Negative control {kind}/{angle} passed incorrectly')
    if failures:calibration['status']='CALIBRATION_FAILED'
    calibration['control_case_verdicts']=[{k:c[k] for k in ['requested_yaw_degrees','kind','target','verdict']} for c in cases]
    calibration['failures']=failures
    write_json(out/'ALL_16_CONTROL_CASES.json',cases)
    write_json(D/'CALIBRATION.json',calibration)
    receipt=dict(started_utc=started,completed_utc=now(),elapsed_seconds=time.monotonic()-timer,
                 argv=sys.argv,python=sys.version,python_executable=sys.executable,opencv=cv2.__version__,numpy=np.__version__,
                 platform=platform.platform(),status=calibration['status'],control_cases=len(cases),thresholds=thresholds,
                 source_photo_body_reads=1,generated_B0_C1_pixel_body_reads=0,C2_pixel_body_reads=0,model_calls=0,
                 metadata_sha256=sha(D/'CAMERA_METADATA_BINDING.json'),calibration_sha256=sha(D/'CALIBRATION.json'),
                 deadline_budget_seconds=3600,budget_exceeded=time.monotonic()-timer>3600,
                 source_sha256=sha(Path(__file__)),observer_sha256=sha(D/'observer.py'))
    write_json(D/'CALIBRATION_RUN_RECEIPT.json',receipt)
    print(json.dumps(receipt,ensure_ascii=False,indent=2))
    return 0 if not failures else 2


if __name__=='__main__':
    raise SystemExit(main())
