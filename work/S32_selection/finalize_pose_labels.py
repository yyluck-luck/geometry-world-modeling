"""Correct only a window-level metadata flag; never rerun selection or data reads."""
from copy import deepcopy
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

def main():
    old=HERE/'history_before_pose_flag_annotation';assert not old.exists()
    path=HERE/'selected_windows.json';receipt=HERE/'selection_receipt.json'
    original=path.read_bytes();original_receipt=receipt.read_bytes();d=json.loads(original);r=json.loads(original_receipt)
    before=deepcopy(d['windows']);changes=[]
    for w in d['windows']:
        actual=any(f['pose_association']['coordinates_parsed_now'] for f in w['frames'])
        previous=w['given_pose_condition']['selected_pose_coordinates_parsed_now']
        if previous != actual:
            changes.append(dict(window=w['id'],field='given_pose_condition.selected_pose_coordinates_parsed_now',previous=previous,corrected=actual))
            w['given_pose_condition']['selected_pose_coordinates_parsed_now']=actual
    assert len(changes)==1 and changes[0]['window']=='fr2_desk_j1'
    for previous,current in zip(before,d['windows']):
        previous['given_pose_condition']['selected_pose_coordinates_parsed_now']=current['given_pose_condition']['selected_pose_coordinates_parsed_now']
        assert previous==current,'Selection and every frame-level record must be unchanged'
    now=datetime.now(timezone.utc).isoformat();old.mkdir()
    (old/'selected_windows.json').write_bytes(original);(old/'selection_receipt.json').write_bytes(original_receipt)
    d['metadata_annotation_correction']=dict(utc=now,changes=changes,selection_rerun=False,original_selected_sha256=hashlib.sha256(original).hexdigest(),
        reason='The initial window summary unconditionally said pose coordinates parsed; blocked fr2 j1 actually parsed zero. Frame-level fields and total12 were already correct.')
    d['source_and_metadata_sha256'][str(Path(__file__).resolve())]=sha(Path(__file__).resolve())
    write(path,d)
    r.update(selected_windows_sha256=sha(path),metadata_annotation_corrected_utc=now,
        original_selection_receipt_sha256=hashlib.sha256(original_receipt).hexdigest(),selection_rerun=False)
    write(receipt,r)
    write(HERE/'metadata_label_correction_receipt.json',dict(status='PASS_METADATA_LABEL_CORRECTION_ONLY',utc=now,changes=changes,
        original_selected_sha256=hashlib.sha256(original).hexdigest(),corrected_selected_sha256=sha(path),
        original_receipt_sha256=hashlib.sha256(original_receipt).hexdigest(),current_receipt_sha256=sha(receipt),
        finalizer_sha256=sha(Path(__file__).resolve()),selection_indices_timestamps_paths_and_frame_records_unchanged=True,
        new_data_table_reads=0,new_image_or_array_reads=0,new_pose_parses=0,selection_reruns=0))
    print(json.dumps(dict(status='PASS_METADATA_LABEL_CORRECTION_ONLY',sha256=sha(path))))

if __name__=='__main__':main()
