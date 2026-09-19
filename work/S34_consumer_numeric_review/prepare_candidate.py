"""Metadata/source-only independent S34 consumer audit preparation."""
from pathlib import Path
import ast
import importlib.util
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def main():
    path=HERE/'review_saved_consumer.py'
    spec=importlib.util.spec_from_file_location('s34_saved_audit_source',path);run=importlib.util.module_from_spec(spec);spec.loader.exec_module(run)
    for p in HERE.glob('*.py'):compile(p.read_text(),str(p),'exec')
    sources=[path,HERE/'protocol.md',Path(__file__).resolve(),ROOT/'work/S34_consumer_preparation/run_consumer.py',
        ROOT/'work/S34_consumer_preparation/protocol.md',ROOT/'src/vmem_retrieval_kernel.py',ROOT/'src/s18_original_kernels.py',ROOT/'src/vmem_memory_kernel.py',
        ROOT/'work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py']
    bindings={str(p):run.sha(p) for p in sources}
    origins=[]
    for path,names in [(ROOT/'src/vmem_retrieval_kernel.py',['get_frame_distribution','process_retrieved_spatial_information','average_camera_pose']),
                       (ROOT/'work/S17C_interface_preparation/isolated_vmem_source/modeling/pipeline.py',['get_frame_distribution','process_retrieved_spatial_information','construct_and_store_scene'])]:
        tree=ast.parse(path.read_text())
        for name in names:
            nodes=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name];run.require(len(nodes)==1,'Unique original function '+name)
            n=nodes[0];origins.append(dict(path=str(path),sha256=run.sha(path),function=name,lines=[n.lineno,n.end_lineno]))
    run.write(HERE/'source_read_manifest.json',dict(recorded_utc=run.utc(),sources=bindings,original_vote_and_consumer_locations=origins,
        evidence_scope='Source+static compile only; no arrays/GT/numerical imports',source_commit='39291e4f272f6b4f270691d930926ab5930f942e'))
    bindings[str(HERE/'source_read_manifest.json')]=run.sha(HERE/'source_read_manifest.json')
    c=dict(schema='s34-independent-saved-consumer-review-v1',status='CANDIDATE_NOT_EXECUTABLE',prepared_utc=run.utc(),
        python=str(ROOT/'.venv-cut3r/bin/python'),runner=str(HERE/'review_saved_consumer.py'),output=str(HERE/'executed'),policy=run.POLICY,
        consumer_manifest=str(ROOT/'work/S34_consumer_preparation/manifest.json'),consumer_manifest_sha256=None,
        consumer_receipt=str(ROOT/'results/S34_original_consumer/receipt.json'),consumer_receipt_sha256=None,source_sha256=bindings,
        pending='Root binds actual future complete consumer manifest and PASS receipt, reviews source and freezes; no outputs read now',
        protocol='Only saved map/cache/candidate/render quantities and fsum votes; no independent renderer/merge or GT score')
    run.write(HERE/'manifest_candidate.json',c)
    run.write(HERE/'preparation_receipt.json',dict(status='PREPARED_NOT_EXECUTED',recorded_utc=run.utc(),candidate_sha256=run.sha(HERE/'manifest_candidate.json'),
        runner_sha256=run.sha(HERE/'review_saved_consumer.py'),source_identity_count=len(bindings),static_compile=True,
        array_byte_reads=0,GT_byte_reads=0,numerical_library_imports=0,model_GA_MST_clean_merge_renderer=0,
        resource='CPU1/120s/2GiB with root external supervisor; no automatic retries'))
    print(json.dumps(dict(candidate_sha256=run.sha(HERE/'manifest_candidate.json'),runner_sha256=run.sha(HERE/'review_saved_consumer.py'),preparation_receipt_sha256=run.sha(HERE/'preparation_receipt.json'))))

if __name__=='__main__':main()
