"""One bounded range retrieval of the cataloged calibration NPY; no videos."""
from pathlib import Path
import datetime as dt
import hashlib
import io
import json
import math
import signal
import struct
import time
import traceback
import urllib.request
import zlib
import numpy as np

D = Path(__file__).parent
C = D.parent / 'zip_catalog_01' / 'receipt.json'
EXPECTED_CATALOG_SHA = 'e5ec5c9bb6a62ac26172823d5ab551b6412f4af4c2afb1cd6543d7ab3fa22d65'
BUDGET = 65536

def utc(): return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def write_json(name, value):
    with (D / name).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False); f.write('\n')
def deadline(*_): raise TimeoutError('120-second fixed wall-clock budget')

def main():
    start = time.monotonic()
    receipt = {'status': 'RUNNING', 'started_utc': utc(), 'archive_body_budget_bytes': BUDGET,
               'total_archive_body_bytes': 0, 'requests': [], 'video_body_bytes': 0,
               'model_runs': 0, 'training_camera_rule': 'nearest non-cam00 Euclidean camera center; tie by camera ID; independent of compressed size and pixels'}
    signal.signal(signal.SIGALRM, deadline); signal.setitimer(signal.ITIMER_REAL, 120)
    try:
        cat_b = C.read_bytes(); assert sha(cat_b) == EXPECTED_CATALOG_SHA
        cat = json.loads(cat_b); receipt['catalog_sha256'] = sha(cat_b)
        receipt['url'] = cat['url']; total = cat['expected_archive_bytes']
        member = next(x for x in cat['members'] if x['name'] == 'coffee_martini/poses_bounds.npy')
        receipt['catalog_member'] = member
        def fetch(offset, count, name):
            assert 0 < count <= BUDGET - receipt['total_archive_body_bytes']
            spec = f'bytes={offset}-{offset+count-1}'
            r = {'range': spec, 'started_utc': utc(), 'expected_body_bytes': count, 'observed_body_bytes': 0}
            receipt['requests'].append(r)
            req = urllib.request.Request(cat['url'], headers={'Range': spec, 'Accept-Encoding': 'identity', 'User-Agent': 'bounded-public-calibration-metadata/1.0'})
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    r.update(status=response.status, content_range=response.headers.get('Content-Range'), content_length=response.headers.get('Content-Length'), content_encoding=response.headers.get('Content-Encoding'))
                    # Reject ignored Range before reading a response body.
                    assert response.status == 206, 'Range not honored; body not consumed'
                    assert r['content_range'] == f'bytes {offset}-{offset+count-1}/{total}'
                    assert r['content_encoding'] in (None, 'identity')
                    assert int(r['content_length']) == count
                    body = bytearray()
                    while len(body) < count:
                        chunk = response.read(min(4096, count-len(body)))
                        if not chunk: break
                        body.extend(chunk); r['observed_body_bytes'] += len(chunk)
                        receipt['total_archive_body_bytes'] += len(chunk)
                        assert receipt['total_archive_body_bytes'] <= BUDGET
                    assert len(body) == count
                b = bytes(body); (D / name).open('xb').write(b)
                r.update(sha256=sha(b), saved_file=name)
                return b
            finally:
                r['completed_utc'] = utc()
                with (D / 'requests.jsonl').open('a') as f: f.write(json.dumps(r)+'\n')
        offset = member['local_header_offset']
        header = fetch(offset, 30, 'local_header_fixed.bin')
        sig, ver, flags, method, mtime, mdate, crc, clen, ulen, nlen, xlen = struct.unpack('<4s5H3I2H', header)
        assert sig == b'PK\x03\x04'
        assert flags == member['flags'] == 0 and method == member['method'] == 8
        assert crc == int(member['crc32'], 16)
        assert clen == member['compressed_bytes'] and ulen == member['uncompressed_bytes']
        assert nlen == len(member['name'].encode('utf-8'))
        rest = fetch(offset+30, nlen+xlen, 'local_name_extra.bin')
        assert rest[:nlen].decode('utf-8') == member['name']
        data_start = offset+30+nlen+xlen
        assert data_start+clen <= cat['eocd']['central_directory_offset']
        payload = fetch(data_start, clen, 'poses_bounds.deflate')
        decoder = zlib.decompressobj(-15)
        raw = decoder.decompress(payload, ulen+1)
        assert decoder.eof and not decoder.unconsumed_tail and not decoder.unused_data
        assert len(raw) == ulen and zlib.crc32(raw) == crc
        (D / 'poses_bounds.npy').open('xb').write(raw)
        receipt['local_header'] = {'offset':offset, 'version_needed':ver, 'flags':flags, 'method':method, 'filename_bytes':nlen, 'extra_bytes':xlen, 'compressed_data_start':data_start}
        receipt['member_verification'] = {'compressed_bytes':len(payload), 'uncompressed_bytes':len(raw), 'crc32':f'{zlib.crc32(raw):08x}', 'compressed_sha256':sha(payload), 'npy_sha256':sha(raw), 'raw_deflate_eof':True}
        astart = utc(); arr = np.load(io.BytesIO(raw), allow_pickle=False)
        names = sorted(x['name'] for x in cat['members'] if x['name'].endswith('.mp4'))
        assert arr.shape == (len(names),17) == (18,17) and arr.dtype == np.dtype('<f8')
        assert np.isfinite(arr).all()
        poses = arr[:, :15].reshape(-1,3,5); bounds = arr[:,15:]
        assert np.all(poses[:,:,4] > 0) and np.all(bounds[:,0] > 0) and np.all(bounds[:,1] > bounds[:,0])
        rot = poses[:,:,:3]; centers = poses[:,:,3]
        ortho = np.max(np.abs(np.swapaxes(rot,1,2) @ rot - np.eye(3)),axis=(1,2))
        det = np.linalg.det(rot)
        assert np.max(ortho) < 1e-6 and np.max(np.abs(det-1)) < 1e-6
        reference = names.index('coffee_martini/cam00.mp4')
        distance = np.linalg.norm(centers-centers[reference],axis=1)
        forward = -rot[:,:,2]
        angles = np.degrees(np.arccos(np.clip((forward @ forward[reference])/(np.linalg.norm(forward,axis=1)*np.linalg.norm(forward[reference])),-1,1)))
        rows = []
        for i, name in enumerate(names):
            h,w,f = poses[i,:,4]
            cv = np.eye(4); cv[:3,:3] = rot[i][:,[1,0,2]] * np.array([1,1,-1])[None,:]; cv[:3,3] = centers[i]
            rows.append({'row':i, 'camera':Path(name).stem, 'stream':name, 'center_world':centers[i].tolist(), 'raw_llff_pose_3x5':poses[i].tolist(), 'c2w_opencv_derived':cv.tolist(), 'height':float(h), 'width':float(w), 'focal_px':float(f), 'K_centered_equal_focal_derived':[[float(f),0,float(w/2)],[0,float(f),float(h/2)],[0,0,1]], 'near_far_scene_units':bounds[i].tolist(), 'distance_to_cam00_scene_units':float(distance[i]), 'forward_angle_to_cam00_deg':float(angles[i]), 'raw_rotation_orthogonality_max_abs':float(ortho[i]), 'raw_rotation_determinant':float(det[i])})
        order = sorted((r for r in rows if r['camera']!='cam00'),key=lambda r:(r['distance_to_cam00_scene_units'],r['camera']))
        selected = order[0]
        video_members = [next(m for m in cat['members'] if m['name']==n) for n in [names[reference],selected['stream']]]
        compressed_pair = sum(m['compressed_bytes'] for m in video_members)
        receipt['array_read'] = {'started_utc':astart,'completed_utc':utc(),'npy_file_bytes':len(raw),'array_numeric_bytes':int(arr.nbytes),'shape':list(arr.shape),'dtype':arr.dtype.str,'allow_pickle':False,'numpy_version':np.__version__,'source':'just-decompressed CRC-verified raw bytes'}
        receipt['recommendation'] = {'training_camera':selected['camera'],'heldout_camera':'cam00','distance_scene_units':selected['distance_to_cam00_scene_units'],'forward_angle_deg':selected['forward_angle_to_cam00_deg'],'pair_compressed_bytes':compressed_pair,'pair_compressed_MiB':compressed_pair/(1024**2),'pair_plus_pose_compressed_bytes':compressed_pair+clen,'under_150_MiB_before_local_headers':compressed_pair+clen <= 150*1024**2,'members':video_members,'ranked_training_cameras_by_distance':[r['camera'] for r in order]}
        table = {'interpretation':'Raw LLFF camera-to-world in original scene units; no recenter, scale, or image-resolution overwrite. Derived OpenCV axes right/down/forward; derived K assumes documented centered principal point and equal focal. No metric-scale or per-pixel visibility certificate.','pose_row_order':'lexically sorted existing MP4 filenames, not numeric ID as row','rows':rows}
        write_json('CAMERAS.json',table)
        receipt['status']='PASS_POSE_METADATA_ONLY'
    except BaseException as exc:
        receipt['status']='FAIL_POSE_METADATA'; receipt['exception']={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        receipt['completed_utc']=utc(); receipt['elapsed_seconds']=time.monotonic()-start
        receipt['source_sha256']=sha(Path(__file__).read_bytes())
        write_json('receipt.json',receipt)
    print(json.dumps({'status':receipt['status'],'body_bytes':receipt['total_archive_body_bytes'],'elapsed_seconds':receipt['elapsed_seconds'],'recommendation':receipt.get('recommendation')}))
    return 0 if receipt['status']=='PASS_POSE_METADATA_ONLY' else 1
if __name__=='__main__': raise SystemExit(main())
