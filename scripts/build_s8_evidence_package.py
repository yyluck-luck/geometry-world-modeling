#!/usr/bin/env python3
"""Build the bounded S8 evidence archive and verify every ZIP member.

This authenticates archived bytes. It is not an end-to-end reproduction on a
new machine and does not execute models, audits, image decoding or experiments.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys
import traceback
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RESULT_ROOTS = ('S8_cut3r_cpu_v2', 'S8_event_replay_v2', 'S8_results_audit_v2',
    'S8_analysis_v2', 'S8_report_audit', 'S8_derivation_audit', 'S8_sampling_audit_v2',
    'S8_rgb_qa_v2', 'S8_timestamp_derivative_preflight')
INPUT_ROOTS = ('data/cut3r/S8_fr2desk_inputs_v2', 'data/cut3r/S8_fr2desk_inputs')
EXCLUDED_DOCUMENT_PREFIXES = ('S8_RESULTS', 'S8_MANUSCRIPT_REVIEW', 'S8_EVIDENCE_PACKAGE')
DERIVATIVE_PARENT = 'data/tum/fr2_desk_timestamp_guard'
DATASET = 'rgbd_dataset_freiburg2_desk'


def now(): return datetime.now(timezone.utc).isoformat()
def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
def require(condition, text):
    if not condition: raise ValueError(text)
def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')


def walk_files(folder):
    require(folder.is_dir() and not folder.is_symlink(), 'Missing or symbolic selected directory: '+str(folder))
    found=[]
    for directory, dirs, files in os.walk(folder, followlinks=False):
        dirs[:]=sorted(d for d in dirs if d != '__pycache__')
        for d in dirs: require(not (Path(directory)/d).is_symlink(), 'Symbolic selected directory: '+d)
        for name in sorted(files):
            if name.endswith(('.pyc','.pyo')) or name == '.DS_Store': continue
            path=Path(directory)/name
            require(path.is_file() and not path.is_symlink(), 'Nonregular or symbolic selected file: '+str(path))
            found.append(path)
    return found


def selected_files():
    paths=set()
    for base in ('scripts','src','tests','vendor'):
        paths.update(walk_files(ROOT/base))
    for path in sorted((ROOT/'docs').glob('S8*')):
        if path.name.startswith(EXCLUDED_DOCUMENT_PREFIXES): continue
        if path.is_dir(): paths.update(walk_files(path))
        else:
            require(path.is_file() and not path.is_symlink(), 'Nonregular selected document: '+str(path))
            paths.add(path)
    for base in INPUT_ROOTS: paths.update(walk_files(ROOT/base))
    for base in RESULT_ROOTS: paths.update(walk_files(ROOT/'results'/base))
    paths.add(ROOT/'results/S8_gt_timestamp_diagnostic.json')
    parent=ROOT/DERIVATIVE_PARENT
    for name in ('derivation_metadata.json','frozen_protocol.md','README.md',
                 'derivation_runner_snapshot.py','design_freeze.json'):
        paths.add(parent/name)
    data=parent/DATASET
    for name in ('rgb.txt','depth.txt','groundtruth.txt'): paths.add(data/name)
    manifest_path=ROOT/'data/cut3r/S8_fr2desk_inputs_v2/S8_inputs.json'
    manifest=json.loads(manifest_path.read_text())
    require(manifest.get('dataset')==DATASET and [b['block'] for b in manifest['blocks']]==[0,1,2],
            'Unexpected S8 manifest dataset/blocks')
    inputs=[]
    for block in manifest['blocks']:
        require(len(block['frames'])==24 and block['split']=='test', 'Unexpected S8 frames or split')
        for frame in block['frames']:
            for kind in ('rgb','depth'):
                name=frame[kind]['path']; relative=PurePosixPath(name)
                require(not relative.is_absolute() and '..' not in relative.parts and str(relative)==name,
                        'Unsafe selected input path')
                path=data/name
                require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(data.resolve()),
                        'Missing or symbolic selected input: '+name)
                expected=frame[kind+'_sha256']
                require(sha(path)==expected, 'Selected input differs from frozen manifest: '+name)
                paths.add(path)
                inputs.append(dict(block=block['block'],frame=frame['frame'],kind=kind,
                    path=str(path.relative_to(ROOT)),sha256=expected))
    require(len(inputs)==144 and len({r['path'] for r in inputs})==144, 'Expected 72 distinct RGB plus 72 depth files')
    for p in paths:
        require(p.is_file() and not p.is_symlink(), 'Missing or symbolic requested source: '+str(p))
        require(p.suffix.lower() not in ('.tgz','.pth','.pt','.safetensors'), 'Raw archive or weight entered selection: '+str(p))
    result=sorted(paths,key=lambda p:str(p.relative_to(ROOT)))
    return result,inputs


def readme(captured_utc, source_count):
    return f'''# S8 科研证据归档包

这是归档证据与已选输入的字节副本，不是已验证的新机完整复现环境。

成员清单捕获时间（UTC）：{captured_utc}。共捕获 {source_count} 个项目源文件，另加本说明；所有payload的字节数与SHA256见MANIFEST.json。ZIP生成后检查全部成员CRC及逐成员SHA，并重查来源文件没有消失或改变。历史JSON内的绝对路径原样保留。

包括S8冻结协议、来源/实施/独立审核材料，全部项目scripts/src/tests和vendor引用源码/许可，V1取样失败记录和V2输入清单，新的模型输出、事件重放、独立结果/派生/取样审计、RGB QA、分析及表格审查证据。运行文件沿用项目相对路径。

派生数据目录只包含父层处理说明/冻结/完整性记录，数据子目录中的rgb.txt、depth.txt、groundtruth.txt，以及V2清单选中的72张RGB原照片和72份depth PNG。RGB/depth副本与清单SHA一致；depth仍是原PNG数值字节，打包时未解码。GT是透明V2时间戳排除后的派生子集，不能称未改官方原GT。原始GT及完整原始解压树没有因此被修改。

**不包含**：完整版原始数据、未选中的其余照片/深度、原TGZ、约3GB模型权重、Python环境、后写/排版中的S8正文与PDF、包生成后的文稿更新。docs/S8_RESULTS.md、S8_MANUSCRIPT_REVIEW及reports/S8故意留给另行交付；包外最终字节核验收据见项目docs/S8_EVIDENCE_PACKAGE.md/json，它们生成于本包之后，故没有递归打入本包。

包内原有元数据或源码可能引用未包含的完整数据、权重、历史S0–S7运行或其他机器路径。这些引用是历史证据，不表示那些外部依赖已在ZIP内，也不保证解包后直接执行所有脚本。此次只核归档字节/CRC及来源身份；没有安装新环境、重跑神经模型、完整VMem、生成视频或进行新机端到端复现。

实际不同S8查询为12张，来自一个新增物理环境的3个相关时间块。24条查询×密度、384图×读出条件不是384个独立样本。研究结论请以另行交付并审核的完整报告为准。

照片/深度来源：TUM RGB-D Benchmark，https://cvg.cit.tum.de/data/datasets/rgbd-dataset 。当前官方网站列CC BY 4.0，2012原论文曾列CC BY 3.0；历史差异与原论文引用详见docs/S8_DATA_SOURCE_REVIEW.md。参考Sturm等，A Benchmark for the Evaluation of RGB-D SLAM Systems，IROS 2012。vendor中的上游源码许可分别原样保留。
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    args=parser.parse_args()
    require(not args.output.exists() and not args.output.is_symlink(), 'Preserve existing ZIP; choose a fresh path')
    require(not args.work.exists() and not args.work.is_symlink(), 'Choose a fresh build evidence directory')
    args.work.mkdir(parents=True)
    started=now(); receipt=dict(status='running',started_utc=started,scope='ZIP member integrity and source stability only',
        model_rerun=False,new_environment_reproduction=False,images_or_depth_decoded=False,output=str(args.output.absolute()))
    partial=args.work/'archive.partial.zip'
    try:
        paths,inputs=selected_files()
        captured=now(); names=[str(p.relative_to(ROOT)) for p in paths]
        require(len(names)==len(set(names)), 'Duplicate project archive paths')
        write(args.work/'selection.json',dict(captured_utc=captured,project=str(ROOT),paths=names,selected_inputs=inputs))
        print(json.dumps(dict(phase='selection_frozen',source_files=len(paths),selected_RGB=72,selected_depth=72,utc=captured)),flush=True)
        items=[]
        with zipfile.ZipFile(partial,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as archive:
            for i,path in enumerate(paths):
                payload=path.read_bytes(); digest=hashlib.sha256(payload).hexdigest()
                name=str(path.relative_to(ROOT))
                archive.writestr(name,payload)
                items.append(dict(path=name,bytes=len(payload),sha256=digest,origin='project_source'))
                if (i+1)%150==0:
                    print(json.dumps(dict(phase='archiving',files=i+1,total=len(paths),utc=now())),flush=True)
            payload=readme(captured,len(paths)).encode('utf-8')
            archive.writestr('PACKAGE_README.md',payload)
            items.append(dict(path='PACKAGE_README.md',bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),origin='generated_package_readme'))
            manifest=dict(schema='s8-evidence-package-v1',selection_captured_utc=captured,source_project=str(ROOT),
                payload_count=len(items),payload_bytes=sum(i['bytes'] for i in items),payloads=items,
                selected_input_count=144,selected_rgb_count=72,selected_depth_count=72,
                omitted_documents=list(EXCLUDED_DOCUMENT_PREFIXES),includes_final_report=False,
                model_weights_included=False,full_original_dataset_included=False,environment_included=False,
                historical_absolute_JSON_paths_preserved=True,validation_scope='CRC and SHA of archive members; not end-to-end execution')
            manifest_bytes=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
            archive.writestr('MANIFEST.json',manifest_bytes)
        receipt.update(selection_captured_utc=captured,source_files=len(paths),payload_count=len(items),
            payload_bytes=manifest['payload_bytes'],archive_members=len(items)+1,
            selected_rgb_images=72,selected_depth_files=72,manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest())
        print(json.dumps(dict(phase='checking_source_stability',utc=now())),flush=True)
        for item in items:
            if item['origin']!='project_source':continue
            source=ROOT/item['path']
            require(source.is_file() and not source.is_symlink() and source.stat().st_size==item['bytes'] and
                    sha(source)==item['sha256'],'Source missing or changed during capture: '+item['path'])
        expected_input={r['path']:r['sha256'] for r in inputs}
        actual={r['path']:r['sha256'] for r in items}
        require(all(actual[name]==digest for name,digest in expected_input.items()),'Archived input differs from frozen manifest')
        receipt.update(source_missing=0,source_changed=0,all_selected_inputs_match_manifest=True,
                       source_stability_verified_utc=now(),zip_verification_started_utc=now())
        print(json.dumps(dict(phase='checking_zip_crc_and_member_sha256',utc=now())),flush=True)
        with zipfile.ZipFile(partial) as archive:
            infos=archive.infolist()
            require(len(infos)==len({i.filename for i in infos})==len(items)+1,'Duplicate or missing ZIP members')
            require(set(archive.namelist())==set(actual)|{'MANIFEST.json'},'ZIP path set differs from snapshot')
            bad=archive.testzip(); require(bad is None,'CRC failure: '+str(bad))
            for item in items:
                payload=archive.read(item['path'])
                require(len(payload)==item['bytes'] and hashlib.sha256(payload).hexdigest()==item['sha256'],
                        'ZIP payload SHA/size differs: '+item['path'])
            require(archive.read('MANIFEST.json')==manifest_bytes,'ZIP manifest bytes differ')
        receipt.update(zip_crc_all_passed=True,member_sha256_all_passed=True,member_byte_sizes_all_passed=True,
                       member_sha256_checks=len(items)+1,zip_verification_completed_utc=now())
        digest=sha(partial); size=partial.stat().st_size
        args.output.parent.mkdir(parents=True,exist_ok=True)
        # Same-workspace atomic exclusive publication. link() refuses an existing
        # target; removing the scratch name afterwards leaves a normal final ZIP.
        os.link(partial,args.output)
        require(sha(args.output)==digest and args.output.stat().st_size==size,'Published ZIP differs')
        partial.unlink()
        receipt.update(status='passed',completed_utc=now(),zip_sha256=digest,zip_bytes=size,
            output=str(args.output.resolve()),excluded_reports=['docs/S8_RESULTS.md','docs/S8_MANUSCRIPT_REVIEW*','reports/S8/*'],
            readme='PACKAGE_README.md',manifest='MANIFEST.json',
            limitation='No new-machine execution, model inference, renderer, measurement audit or environment installation was performed.')
        write(args.work/'verification.json',receipt)
        write(ROOT/'docs/S8_EVIDENCE_PACKAGE.json',receipt)
        text=f'''# S8 科研证据包字节核验

状态：**PASS，仅指ZIP归档完整性与来源未变检查。** 没有重跑模型、建立新环境或验证新机端到端执行。

实际开始UTC：{started}；成员列表捕获：{captured}；实际完成：{receipt['completed_utc']}。这是本次真实打包/核验时间，非原实验时间。

输出：`{receipt['output']}`

ZIP大小：{size}字节；SHA256：`{digest}`。{len(paths)}个原项目文件 + 1份包内说明，共{len(items)}项payload，另有MANIFEST.json，共{len(items)+1}个ZIP成员。全部成员CRC、字节大小和SHA核对通过，来源缺失0、来源变化0；所选72RGB+72depth均与V2冻结清单一致。

内容包括指定S8设计/来源/审核、项目scripts/src/tests/vendor、V1失败与V2输入目录、S8模型/重放/审计/分析/RGB QA证据。派生数据仅含父层5项记录、3个GT/时间表文本以及选定144个PNG；不含其余完整数据、TGZ、权重或环境。

报告正文S8_RESULTS.md、S8_MANUSCRIPT_REVIEW与reports/S8排版文件明确不在此包；最后报告另行交付。本核验文件在包生成之后写入，也没有递归打包。历史JSON绝对路径保留，部分历史引用或完整数据依赖在包外，不保证解包后所有脚本能直接运行。

包内PACKAGE_README.md说明范围与许可；MANIFEST.json列每个payload的SHA/大小。机器收据为S8_EVIDENCE_PACKAGE.json，完整构建成员清单/收据保留于`{args.work.resolve()}`。
'''
        (ROOT/'docs/S8_EVIDENCE_PACKAGE.md').write_text(text)
        print(json.dumps(receipt,ensure_ascii=False),flush=True)
        return 0
    except BaseException:
        receipt.update(status='failed',completed_utc=now(),traceback=traceback.format_exc())
        write(args.work/'verification.json',receipt)
        raise


if __name__=='__main__':sys.exit(main())
