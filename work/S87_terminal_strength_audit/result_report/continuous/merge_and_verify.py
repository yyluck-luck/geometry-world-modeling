"""Merge fixed156+12 PDF sources; preserve pages/outlines and verify content.

Document packaging only. No scientific inputs, models, scores or source edits.
Artifact-operation marker already succeeded once in root for both PDF outputs.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback
import pypdf
from pypdf import PdfReader, PdfWriter
from PIL import Image, ImageChops

HERE=Path(__file__).resolve().parent
PDF=HERE/'完整汇报_含S87实际结果_168页.pdf'
SOURCES=[
    dict(path='/Users/rocket/Documents/Codex/2026-09-05/users-rocket-desktop-hkust-it-ip/outputs/导师汇报_深入讲解第二版_2026-09-10/最新连续阅读版/完整汇报_含S86实际结果_156页.pdf',
         sha256='069c45b2974cc7bdb0c722609795d1b3be4d28f7a200668c11dcf4f813a8052d',pages=156,first_merged_page=1),
    dict(path='/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/work/S87_terminal_strength_audit/result_report/S87_有限末端对照_实际结果与零基础讲解.pdf',
         sha256='53c9c339ca90cb04e647da6d9490f8dd1c3a5d4dfcdae3c45f885f6957de85d1',pages=12,first_merged_page=157)]
BOOKMARK='第四部分：S87有限末端对照实际结果、完整数据与解释（12页）'
POPPLER='/opt/homebrew/bin/pdftoppm'


def sha(data):return hashlib.sha256(data).hexdigest()
def file_sha(path):return sha(Path(path).read_bytes())
def utc():return datetime.now(timezone.utc).isoformat()
def save(path,value):
    with path.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def require(ok,why):
    if not ok:raise AssertionError(why)
def normalize(text):return re.sub(r'\s+',' ',text).strip()
def dimensions(page):
    return {**{name:[str(x) for x in getattr(page,name)] for name in
        ('mediabox','cropbox','bleedbox','trimbox','artbox')},
        'rotation':int(page.get('/Rotate',0)),'user_unit':str(page.get('/UserUnit',1))}
def outlines(reader,items=None,depth=0):
    result=[]
    for item in reader.outline if items is None else items:
        if isinstance(item,list):result.extend(outlines(reader,item,depth+1))
        else:result.append(dict(depth=depth,title=str(item.title),page1=reader.get_destination_page_number(item)+1))
    return result
def contents(page):
    stream=page.get_contents()
    return b'' if stream is None else stream.get_data()


started=time.monotonic()
report=dict(status='STARTED',started_utc=utc(),source_files=SOURCES,page_checks=[],pixel_checks=[],
    pypdf_version=pypdf.__version__,python=sys.executable,
    artifact_marker='Already succeeded once in root with expected-output-count2; not repeated here.',
    final_delivery_accepted=False,scientific_arrays_read=0,models_run=0)
require(not PDF.exists() and not (HERE/'MERGE_REVIEW.json').exists(),'create-only document build')
try:
    readers=[]
    for item in SOURCES:
        p=Path(item['path']);require(file_sha(p)==item['sha256'],'source SHA '+str(p))
        reader=PdfReader(p);require(len(reader.pages)==item['pages'],'source page count')
        item.update(bytes=p.stat().st_size,outlines=outlines(reader));readers.append(reader)
    save(HERE/'MERGE_INPUTS.json',dict(sources=SOURCES,new_bookmark=dict(title=BOOKMARK,page1=157),
        physical_page_mapping='1-156 = old156;157-168 = S87 source1-12',
        semantic_status='Merge preparation only; root performs final content/visual acceptance.'))
    writer=PdfWriter()
    writer.append(readers[0],import_outline=True)
    writer.append(readers[1],outline_item=BOOKMARK,import_outline=True)
    writer.add_metadata({'/Title':'完整汇报：既有156页与S87实际结果12页（连续168页）',
                         '/Subject':'Preserved source pages; S87 begins at physical page157.',
                         '/Creator':'pypdf fixed-input merge'})
    with PDF.open('xb') as f:writer.write(f)
    merged=PdfReader(PDF);require(len(merged.pages)==168,'merged168 pages')
    expected_outlines=SOURCES[0]['outlines']+[dict(depth=0,title=BOOKMARK,page1=157)]
    expected_outlines += [dict(depth=x['depth']+1,title=x['title'],page1=x['page1']+156)
                         for x in SOURCES[1]['outlines']]
    report['outlines']=outlines(merged)
    require(report['outlines']==expected_outlines,'all original bookmarks and new S87 destination')
    offset=0
    for source,reader in zip(SOURCES,readers):
        for index,page in enumerate(reader.pages):
            target=merged.pages[offset+index]
            raw=page.extract_text() or '';actual=target.extract_text() or ''
            text,want=normalize(actual),normalize(raw)
            row=dict(source_path=source['path'],source_page1=index+1,merged_page1=offset+index+1,
                source_normalized_text_sha256=sha(want.encode()),merged_normalized_text_sha256=sha(text.encode()),
                whitespace_normalized_text_equal=want==text,raw_extracted_text_equal=raw==actual,
                source_text_characters=len(raw),merged_text_characters=len(actual),
                text_empty=not bool(want),source_dimensions=dimensions(page),merged_dimensions=dimensions(target),
                dimensions_equal=dimensions(page)==dimensions(target),
                decoded_page_content_equal=contents(page)==contents(target))
            report['page_checks'].append(row)
            require(row['whitespace_normalized_text_equal'],'page text differs '+str(offset+index+1))
            require(row['dimensions_equal'],'page dimensions differ '+str(offset+index+1))
            require(row['decoded_page_content_equal'],'decoded page graphics content differs '+str(offset+index+1))
        offset+=len(reader.pages)
    qa=HERE/'qa';qa.mkdir()
    commands=[]
    for source_page,kind in [(1,'first'),(5,'full_data'),(8,'target22_figure'),(12,'last')]:
        merged_page=156+source_page
        source_prefix=qa/f'source_s87_{source_page:02d}'
        merged_prefix=qa/f'merged_{merged_page:03d}'
        for path,page,prefix in [(Path(SOURCES[1]['path']),source_page,source_prefix),(PDF,merged_page,merged_prefix)]:
            command=[POPPLER,'-f',str(page),'-l',str(page),'-singlefile','-r','150','-png',str(path),str(prefix)]
            result=subprocess.run(command,capture_output=True,text=True)
            commands.append(dict(argv=command,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr))
            require(result.returncode==0,'render failed '+str(prefix))
        source_png=source_prefix.with_suffix('.png');merged_png=merged_prefix.with_suffix('.png')
        with Image.open(source_png) as a,Image.open(merged_png) as b:
            rgb_a=a.convert('RGB');rgb_b=b.convert('RGB')
            same=a.size==b.size and rgb_a.tobytes()==rgb_b.tobytes()
            delta_box=None if a.size!=b.size else ImageChops.difference(rgb_a,rgb_b).getbbox()
            check=dict(kind=kind,source_page1=source_page,merged_page1=merged_page,dpi=150,
                source_png=str(source_png),merged_png=str(merged_png),source_png_sha256=file_sha(source_png),
                merged_png_sha256=file_sha(merged_png),pixel_dimensions=list(a.size),
                source_rgb_bytes_sha256=sha(rgb_a.tobytes()),merged_rgb_bytes_sha256=sha(rgb_b.tobytes()),
                exact_RGB_pixels_equal=same,difference_bbox=delta_box)
        report['pixel_checks'].append(check);require(same,'rendered pixels differ '+str(merged_page))
    report['render_commands']=commands
    for item in SOURCES:require(file_sha(item['path'])==item['sha256'],'source changed during merge')
    report.update(status='PASS_MERGE_PRESERVATION_PENDING_ROOT_ACCEPTANCE',merged_pdf=str(PDF),
        merged_pdf_sha256=file_sha(PDF),merged_pdf_bytes=PDF.stat().st_size,merged_pages=168,
        all_168_text_and_dimensions_equal=True,all_168_decoded_graphics_content_equal=True,
        text_empty_pages=[x['merged_page1'] for x in report['page_checks'] if x['text_empty']],
        differing_pages=[],four_new_key_pages_exact_pixels=True,
        scope='All168 pages text extraction (only whitespace normalized), five page boxes/rotation/userunit, decoded page content and bookmark destinations checked against sources. Only S87source1/5/8/12 versus merged157/161/164/168 rendered here at150dpi. Other164 pages not rendered here. Text equality cannot independently assess glyph layout/image content; empty or nonextractable pages are explicitly listed. Root separately reviews all12 new pages; no final acceptance or user-directory copy by this script.')
except BaseException as error:
    report.update(status='FAILED_PRESERVED',error=repr(error),traceback=traceback.format_exc())
finally:
    report.update(completed_utc=utc(),elapsed_seconds=time.monotonic()-started)
    save(HERE/'MERGE_REVIEW.json',report)
print(json.dumps({k:report.get(k) for k in ('status','merged_pages','merged_pdf_sha256','elapsed_seconds')},ensure_ascii=False))
raise SystemExit(0 if report['status']=='PASS_MERGE_PRESERVATION_PENDING_ROOT_ACCEPTANCE' else 1)
