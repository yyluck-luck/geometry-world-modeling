"""Reproducible local verification for ALT-TUM-01; never upgrades partial media to Gate0."""
import hashlib, json
from pathlib import Path
root=Path(__file__).parent
p=root/'downloads/freiburg1_xyz-groundtruth.txt'
b=p.read_bytes()
rows=[ln.split() for ln in b.decode(errors='replace').splitlines() if ln.strip() and not ln.lstrip().startswith('#')]
checks={
 'gt_sha256': hashlib.sha256(b).hexdigest()=='aac0319a6ef4e1cdf61e779d2152b95aa7e9f7b1749d6d18717b43ddabffede2',
 'gt_eight_columns': len(rows)==3000 and all(len(r)==8 for r in rows),
 'gt_monotonic_timestamps': all(float(rows[i][0])<float(rows[i+1][0]) for i in range(len(rows)-1)),
 'rgb_prefix_budget': (root/'downloads/rgb_movie.part').stat().st_size==65536,
 'depth_prefix_budget': (root/'downloads/depth_movie.part').stat().st_size==65536,
 'no_full_archive': (root/'downloads/sequence_archive.part').stat().st_size==65536,
 'timestamped_rgb_depth_pair': False,
 'license_confirmed': False,
 'scene_split_frozen': False,
}
result={'checks':checks,'all_local_checks_pass':all(checks.values()),'full_gate0':'FAIL','status':'GATE0_NOT_PASSED'}
(root/'verify_result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
raise SystemExit(0)
