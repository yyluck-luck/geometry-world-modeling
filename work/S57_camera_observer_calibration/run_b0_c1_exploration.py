"""Root may execute only after final S57 source/calibration review. No new model."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib
import json
import sys
import time
import numpy as np
from observer import (PAIRS, PARAMETERS, classify, configure, coverage, features, observe, sha, write_json)

D=Path(__file__).resolve().parent
R=D.parents[1]
OUTPUT=R/'results/S57_B0_C1_camera_observer_exploration'


def main():
    start=datetime.now(timezone.utc).isoformat();timer=time.monotonic();configure()
    frozen=json.loads((D/'FROZEN_DELIVERY.json').read_text())
    for name,digest in frozen['source_and_binding_sha256'].items():
        assert sha(D/name)==digest, 'Frozen source/calibration changed: '+name
    calibration=json.loads((D/'CALIBRATION.json').read_text())
    assert calibration['status']=='CALIBRATED_ON_SINGLE_SYNTHETIC_TEXTURE_ONLY'
    metadata=json.loads((D/'CAMERA_METADATA_BINDING.json').read_text())
    assert sorted(metadata['rows'])==['B0','C1'] and len(PAIRS)==15
    OUTPUT.mkdir()
    all_rows={};pixels_read=0;pixel_bytes=0
    for row in ['B0','C1']:
        binding=metadata['rows'][row]
        if binding['status']!='RECORDED_NOMINAL_CAMERA_CONVENTION_VERIFIED':
            all_rows[row]=dict(status='UNKNOWN_CAMERA_BINDING',pairs=[dict(pair=list(p),verdict='UNKNOWN_CAMERA_BINDING') for p in PAIRS])
            continue
        archive=Path(binding['archive_directory'])
        assert sha(archive/'events.jsonl')==binding['archive_events_sha256']
        assert sha(archive/'manifest.json')==binding['archive_manifest_sha256']
        assert [p['pair'] for p in binding['pairs']]==[list(p) for p in PAIRS]
        frames=[]
        for expected_id,frame in enumerate(binding['frames']):
            assert frame['id']==expected_id
            desc=frame['pixels_descriptor'];assert desc['shape']==[576,576,3] and desc['dtype']=='uint8'
            payload=(archive/desc['blob']).read_bytes()
            assert len(payload)==desc['nbytes']==995328 and hashlib.sha256(payload).hexdigest()==desc['bytes_sha256']
            frames.append(np.frombuffer(payload,np.uint8).reshape(576,576,3).copy())
            pixels_read+=1;pixel_bytes+=len(payload)
        cache=[features(f) for f in frames]
        pairs=[]
        for p in binding['pairs']:
            i,j=p['pair'];H=np.asarray(p['requested_H'],dtype=np.float64)
            m=observe(frames[i],frames[j],H,cache[i],cache[j])
            pairs.append(dict(pair=[i,j],nominal_yaw_difference_degrees=p['nominal_yaw_difference_degrees'],
                              measurement=m,verdict=classify(m,calibration)))
        frame_diagnostics=[dict(id=i,keypoint_count=len(cache[i][0]),
                                full_frame_grid_coverage=coverage(cache[i][0],frames[i].shape)) for i in range(9)]
        all_rows[row]=dict(status='EXPLORATORY_MATCHED_SUPPORT_ONLY',pairs=pairs,frame_diagnostics=frame_diagnostics,
                           physical_intrinsics_status=binding['physical_image_intrinsics_status'])
    result=dict(schema='s57-existing-pixels-exploratory-observer-v1',started_utc=start,
                completed_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.monotonic()-timer,
                rows=all_rows,pair_denominator=30,parameters=PARAMETERS,
                generated_pixel_body_reads=pixels_read,generated_pixel_body_bytes=pixel_bytes,
                new_generations=0,C2_pixels_read=0,calibration_sha256=sha(D/'CALIBRATION.json'),
                frozen_delivery_sha256=sha(D/'FROZEN_DELIVERY.json'),argv=sys.argv,
                outcome='Not a calibrated physical camera reconstruction, quality score, S42 rescore, method or novelty claim')
    write_json(OUTPUT/'ALL_30_PAIRS.json',result)
    summary={}
    for row,value in all_rows.items():
        summary[row]=[]
        for pair in value['pairs']:
            m=pair.get('measurement',{})
            summary[row].append(dict(pair=pair['pair'],verdict=pair['verdict'],match_count=m.get('match_count'),
                                     requested_residual_px=m.get('requested',{}).get('cell_balanced_median_px'),
                                     identity_residual_px=m.get('identity',{}).get('cell_balanced_median_px'),
                                     fitted_residual_px=m.get('fitted',{}).get('cell_balanced_median_px'),
                                     source_supported_cells=m.get('source_coverage',{}).get('supported'),
                                     target_supported_cells=m.get('target_coverage',{}).get('supported')))
    write_json(OUTPUT/'SUMMARY.json',summary)
    print(json.dumps(dict(output=str(OUTPUT),pair_denominator=30,rows=summary),ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
