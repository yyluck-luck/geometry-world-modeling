#!/usr/bin/env python3
"""Stage stable S33 records/photos only; final report and review arrive later."""
from pathlib import Path
import hashlib,importlib.util,json
ROOT=Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
WORK=ROOT/'work/S33_delivery'
WS=Path('/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip')
OUT=WS/'outputs/S33_尺度约束四条件与真实照片_2026-09-07'
PREVIOUS=WS/'outputs/S32_新片段三对照与真实照片_2026-09-07'
BASE=ROOT/'work/S32_A_delivery/build_snapshot.py'
spec=importlib.util.spec_from_file_location('snapshot_copy_helper',BASE);a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
a.OUT=OUT;a.WORK=WORK
sha=a.sha;read=a.load;copy=a.copy;write=a.put_json
def savejson(name,d):return a.save(name,(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
def main():
    started=a.utc();assert not OUT.exists(),'No existing snapshot overwrite';OUT.mkdir(parents=True)
    previous_sha='df7087cb58a1cf01e071c1861ad794ffe80143e58d023e01b4425d71548f081a'
    assert sha(PREVIOUS/'manifest.json')==previous_sha
    old=read(PREVIOUS/'manifest.json');payloads={x['relative_path']:x for x in old['payloads']}
    sel=ROOT/'work/S32_input_freeze/selected_windows_rgb_sealed.json';assert sha(sel)=='ac2c04437afa62fbaa5f03e5159ba06960131d9a2405afd5f94eef0c2f9ed318'
    selected={f['sha256']:f for w in read(sel)['windows'] for f in w['frames']}
    photos=[]
    for p in sorted((PREVIOUS/'真实照片').rglob('*.png')):
        rel=p.relative_to(PREVIOUS);h=sha(p);assert h==payloads[str(rel)]['destination_sha256'] and h in selected
        q=copy(p,rel,expected=h);f=selected[h]
        photos.append(dict(window_id=rel.parts[1],frame_index=f['index'],source_rgb_index=f['source_rgb_index'],rgb_time=f['rgb_time_string'],original_RGB_path=f['path'],source_snapshot=str(p),snapshot_path=str(q),sha256=h))
    assert len(photos)==16
    copy(PREVIOUS/'manifest.json',Path('证据/S32_snapshot_manifest.json'),expected=previous_sha)
    copy(sel);copy(ROOT/'work/S32_selection/selected_windows.json')
    for directory in ['work/S33_preparation','work/S33_root_preparation','work/S33_independent_review','work/S33_launch','work/S33_execution','work/S33_scoring_freeze','work/S33_scoring_execution']:
        for p in sorted((ROOT/directory).rglob('*')):
            if p.is_file() and p.suffix in {'.json','.jsonl','.txt','.md','.py','.diff'} and '__pycache__' not in p.parts:copy(p)
    for n in ['score_s33.py','protocol.md','manifest.json','manifest_candidate.json','preparation_receipt.json']:
        copy(ROOT/'work/S33_scoring_preparation'/n)
    for p in sorted((ROOT/'results/S33_pair_scale_scoring').iterdir()):
        if p.is_file() and p.suffix in {'.json','.csv'}:copy(p)
    # No copies of S32 old large arrays/logs; retain links and exact old48 imported scoring bytes above.
    links=[];traces=[]
    for wid in ['fr2_desk_j1','fr2_desk_j2','fr1_xyz_j1','fr1_xyz_j2']:
        rp=ROOT/'results/S33_pair_scale_control'/wid/'receipt.json';r=read(rp);copy(rp)
        assert r['status']==('UNAVAILABLE' if wid=='fr2_desk_j1' else 'PASS')
        assert r['contract_sha256']=='44a817a74afe10a16b758cc8fa6f7a17781d34d41ac575dd24e73b1ac1101400'
        for name,h in r['outputs'].items():
            p=rp.parent/name;assert p.is_file()
            if p.suffix in {'.npz','.npy'}:
                links.append(dict(window_id=wid,path=str(p),bytes=p.stat().st_size,sha256=h,source_receipt=str(rp),copied=False,identity_scope='Producer/score sealed SHA inherited; snapshot only stat/existence, no archive bytes read'))
            else:
                copy(p,expected=h)
                if p.name in ['optimization_trace.jsonl','gradient_depth_trace.jsonl','s33_scale_trace.jsonl']:
                    count=sum(bool(line.strip()) for line in p.read_text().splitlines());assert count==400
                    traces.append(dict(window_id=wid,kind=p.name,records=count,path=str(p),sha256=h))
    assert len(traces)==9
    for name in ['optimization_trace.jsonl','gradient_depth_trace.jsonl','s33_scale_trace.jsonl']:
        assert sum(x['records'] for x in traces if x['kind']==name)==1200
    for p in [ROOT/'work/S33_mechanism_analysis/conditional_scale_path.md',ROOT/'work/S33_mechanism_analysis/receipt.json',
        ROOT/'work/S33_mechanism_analysis/review/review.md',ROOT/'work/S33_mechanism_analysis/review/review.json',ROOT/'work/S33_mechanism_analysis/review/revision_closure.json']:copy(p)
    savejson('照片清单.json',dict(previous_snapshot_manifest_sha256=previous_sha,photos=photos))
    savejson('本轮大数组链接清单.json',links)
    savejson('本轮完整日志清单.json',dict(traces=traces,optimization_records=1200,gradient_records=1200,pair_scale_records=1200,scope='Saved log copies and line counts; no new gradient/scale arithmetic'))
    copy(Path(__file__),Path('证据/stage_snapshot.py'));copy(BASE,Path('证据/copy_helper_A.py'))
    for x in a.payloads:assert sha(OUT/x['relative_path'])==x['destination_sha256']
    for p,h in a.sources.items():assert sha(p)==h
    state=dict(status='STAGED_REPORT_AND_INDEPENDENT_REVIEW_PENDING',started_utc=started,staged_utc=a.utc(),snapshot=str(OUT),payloads=a.payloads,sources=a.sources,rewrites=a.rewrites,
        photos=photos,large_links=links,traces=traces,previous_snapshot=str(PREVIOUS),previous_manifest_sha256=previous_sha,scientific_execution=0)
    write(WORK/'stage_state.json',state);print(json.dumps(dict(status=state['status'],payloads=len(a.payloads),photos=len(photos),large_files_linked_only=len(links),complete_trace_records=len(traces)*400),indent=2))
if __name__=='__main__':main()
