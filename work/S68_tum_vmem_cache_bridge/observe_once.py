"""Observe one reviewed, bounded encoder run; never interpret return 0 as novelty."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
import psutil

D = Path(__file__).resolve().parent
R = D.parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert len(sys.argv) == 2, 'Expected exact root binding SHA'
binding_path = D/'ROOT_RUN_BINDING.json'
assert sha(binding_path) == sys.argv[1]
binding = json.loads(binding_path.read_text())
for name, expected in binding['reviewed_files_sha256'].items():
    assert sha(Path(name)) == expected, name
review = json.loads((D/'SOURCE_REVIEW.json').read_text())
assert review['status'].startswith('PASS') and not review.get('blockers')
assert binding['body_history_ids'] == [12, 13, 14, 18, 19]
assert not Path(binding['worker_output_directory']).exists()
out = D/'external_01'
out.mkdir(exist_ok=False)
env = os.environ.copy()
env.update({'HF_HUB_OFFLINE':'1', 'TRANSFORMERS_OFFLINE':'1', 'HF_DATASETS_OFFLINE':'1',
            'TOKENIZERS_PARALLELISM':'false', 'PYTHONDONTWRITEBYTECODE':'1',
            'OMP_NUM_THREADS':'8', 'MKL_NUM_THREADS':'8', 'OPENBLAS_NUM_THREADS':'8'})
sys.path.insert(0, str(R/'scripts'))
from research_log import append_event
started = datetime.now(timezone.utc).isoformat()
t0 = time.monotonic()
stop_reason = None
observer_error = None
peak_sampled_rss = 0
samples = 0
def signal_group(pid, sig):
    try:
        os.killpg(pid, sig)
    except ProcessLookupError:
        pass
with (out/'stdout.txt').open('xb') as stdout, (out/'stderr.txt').open('xb') as stderr:
    child = subprocess.Popen(binding['argv'], cwd=R, env=env, stdout=stdout, stderr=stderr,
                             start_new_session=True)
    start = {'started_utc': started, 'argv': binding['argv'], 'pid': child.pid,
             'binding_sha256': sys.argv[1], 'observer_sha256': sha(Path(__file__)),
             'timeout_seconds':960, 'rss_limit_bytes':20*1024**3,
             'rss_scope':'sampled sum of child and discovered descendants; 0.5 second sampling',
             'offline_environment_flags_set':True, 'body_history_ids':binding['body_history_ids']}
    (out/'started.json').write_text(json.dumps(start, ensure_ascii=False, indent=2)+'\n')
    append_event('S68五张历史照片的真实编码实际启动',
                 '只用原VAE/CLIP编码固定历史12/13/14/18/19，CPU8 FP32，已有本地权重；外部960秒与20GiB采样RSS上限。0目标正文、0视频/renderer/get_cond。',
                 [str((out/'started.json').relative_to(R))],
                 '保存全部5来源输出或实际失败；依外部返回和不同作者有限核验判断接口是否完成。')
    with (out/'monitor.jsonl').open('x') as monitor:
        try:
            while child.poll() is None:
                elapsed = time.monotonic()-t0
                try:
                    process = psutil.Process(child.pid)
                    tree = [process]+process.children(recursive=True)
                    rss = 0
                    for item in tree:
                        try:
                            rss += item.memory_info().rss
                        except (psutil.NoSuchProcess, psutil.ZombieProcess):
                            pass
                    peak_sampled_rss = max(peak_sampled_rss, rss)
                    samples += 1
                    if samples == 1 or samples % 10 == 0:
                        monitor.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),
                                                 'elapsed_seconds':elapsed, 'rss_bytes':rss})+'\n')
                        monitor.flush()
                    if rss > 20*1024**3:
                        stop_reason = 'sampled_process_tree_rss_limit'
                except psutil.NoSuchProcess:
                    pass
                if elapsed > 960:
                    stop_reason = 'external_timeout'
                if stop_reason:
                    signal_group(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        signal_group(child.pid, signal.SIGKILL)
                    break
                time.sleep(0.5)
            code = child.wait(timeout=10)
        except BaseException as exc:
            observer_error = f'{type(exc).__name__}: {exc}'
            if child.poll() is None:
                signal_group(child.pid, signal.SIGKILL)
            code = child.wait(timeout=10)
receipt = dict(start, completed_utc=datetime.now(timezone.utc).isoformat(),
               elapsed_seconds=time.monotonic()-t0, returncode=code, stop_reason=stop_reason,
               observer_error=observer_error,
               peak_sampled_process_tree_rss_bytes=peak_sampled_rss, rss_samples=samples,
               stdout_sha256=sha(out/'stdout.txt'), stderr_sha256=sha(out/'stderr.txt'))
worker_receipt = Path(binding['worker_receipt_path'])
if worker_receipt.is_file():
    receipt['worker_receipt_sha256'] = sha(worker_receipt)
    receipt['worker_status'] = json.loads(worker_receipt.read_text()).get('status')
with (out/'receipt.json').open('x') as f:
    json.dump(receipt, f, ensure_ascii=False, indent=2)
    f.write('\n')
(out/'receipt.json').chmod(0o444)
append_event('S68历史编码实际外部返回',
             f'returncode={code}，stop_reason={stop_reason}，外部耗时{receipt["elapsed_seconds"]:.6f}秒，采样峰RSS={peak_sampled_rss}B，worker状态={receipt.get("worker_status","missing")}。结果只关编码接口，不是生成收益。',
             [str((out/'receipt.json').relative_to(R))],
             '核实际来源、预处理、权重加载与完整输出，进行不同作者结果核验；保留任何失败和缺失。')
print(json.dumps(receipt, ensure_ascii=False))
