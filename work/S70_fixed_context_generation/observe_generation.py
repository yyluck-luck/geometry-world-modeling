"""One reviewed S70 execution with sampled resource and per-arm time limits."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time

import psutil

D = Path(__file__).resolve().parent
R = D.parents[1]
MAX_SECONDS = 5520
ARM_SECONDS = 1800
RSS_LIMIT = 45 * 1024**3
FREE_MIN = 10 * 1024**3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, data):
    with path.open('x') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def stop_group(child):
    try:
        os.killpg(child.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        child.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        child.wait(timeout=10)


def main():
    if sys.argv[1:] == ['--compile-only']:
        compile(Path(__file__).read_bytes(), str(Path(__file__)), 'exec')
        print('COMPILE_ONLY_NO_SCIENTIFIC_EXECUTION')
        return 0
    assert len(sys.argv) == 2, 'Expected exact root run binding SHA'
    binding_path = D / 'ROOT_RUN_BINDING.json'
    assert sha(binding_path) == sys.argv[1]
    binding = json.loads(binding_path.read_text())
    for path, expected in binding['reviewed_files_sha256'].items():
        assert sha(path) == expected, path
    review = json.loads((D / 'SOURCE_REVIEW.json').read_text())
    assert review['status'].startswith('PASS') and not review.get('blockers')
    argv = [str(R / '.venv-cut3r/bin/python'), '-B', str(D / 'generate_fixed_contexts.py')]
    assert binding['argv'] == argv
    assert not (D / 'execution_01').exists()
    assert shutil.disk_usage(D).free >= FREE_MIN
    out = D / 'external_01'
    out.mkdir(exist_ok=False)
    env = os.environ.copy()
    env.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_DATASETS_OFFLINE='1',
               HF_HUB_DISABLE_IMPLICIT_TOKEN='1', TOKENIZERS_PARALLELISM='false',
               KORNIA_CHECK_VERSION='0', PYTHONDONTWRITEBYTECODE='1',
               OMP_NUM_THREADS='8', MKL_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8')
    sys.path.insert(0, str(R / 'scripts'))
    from research_log import append_event
    start = utc()
    t0 = time.monotonic()
    peak = 0
    count = 0
    reason = None
    error = None
    active_arm = None
    arm_t0 = None
    progress_offset = 0
    latest = None
    code = None
    progress_path = D / 'execution_01/progress.jsonl'
    with (out / 'stdout.txt').open('xb') as stdout, (out / 'stderr.txt').open('xb') as stderr:
        child = subprocess.Popen(argv, cwd=R, env=env, stdout=stdout, stderr=stderr,
                                 start_new_session=True)
        started = dict(started_utc=start, pid=child.pid, argv=argv,
                       binding_sha256=sys.argv[1], observer_sha256=sha(__file__),
                       total_seconds_limit=MAX_SECONDS, per_arm_seconds_limit=ARM_SECONDS,
                       arm_timer_scope='external first observation of arm_start; 0.5s polling',
                       rss_limit_bytes=RSS_LIMIT, free_disk_min_bytes=FREE_MIN,
                       rss_scope='sampled sum of child and discovered descendants every0.5s',
                       disk_free_at_start=shutil.disk_usage(D).free)
        write_json(out / 'started.json', started)
        append_event('S70三臂完整生成实际启动',
                     'CPU8 FP32，固定A0/A1/B各50步，四真实目标；同输入重放与实际RNG记录。外部总5520秒、每臂1800秒、采样RSS45GiB与空闲磁盘10GiB。',
                     [str((out / 'started.json').relative_to(R))],
                     '保留全部三臂结果或实际失败，真实返回后独立核输出/随机状态，再执行固定RGB评分。',
                     occurred_at=start)
        with (out / 'monitor.jsonl').open('x') as monitor:
            try:
                while child.poll() is None:
                    tick = time.monotonic()
                    elapsed = tick - t0
                    if progress_path.exists():
                        with progress_path.open('rb') as f:
                            f.seek(progress_offset)
                            for line in f:
                                if not line.endswith(b'\n'):
                                    break
                                row = json.loads(line)
                                progress_offset += len(line)
                                latest = row
                                if row.get('phase') == 'arm_start':
                                    active_arm, arm_t0 = row['arm'], tick
                                elif row.get('phase') in ('arm_complete', 'failure', 'complete'):
                                    active_arm, arm_t0 = None, None
                    rss = 0
                    try:
                        root = psutil.Process(child.pid)
                        for proc in [root] + root.children(recursive=True):
                            try:
                                rss += proc.memory_info().rss
                            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                                pass
                    except psutil.NoSuchProcess:
                        pass
                    peak = max(peak, rss)
                    free = shutil.disk_usage(D).free
                    arm_elapsed = tick - arm_t0 if arm_t0 is not None else None
                    count += 1
                    if count == 1 or count % 10 == 0:
                        monitor.write(json.dumps(dict(utc=utc(), elapsed_seconds=elapsed,
                                                      rss_bytes=rss, disk_free_bytes=free,
                                                      active_arm=active_arm, arm_seconds=arm_elapsed,
                                                      latest_worker_progress=latest)) + '\n')
                        monitor.flush()
                    if elapsed > MAX_SECONDS:
                        reason = 'total_time_limit'
                    elif arm_elapsed is not None and arm_elapsed > ARM_SECONDS:
                        reason = 'per_arm_time_limit'
                    elif rss > RSS_LIMIT:
                        reason = 'sampled_process_tree_rss_limit'
                    elif free < FREE_MIN:
                        reason = 'disk_free_limit'
                    if reason:
                        stop_group(child)
                        break
                    time.sleep(0.5)
                code = child.wait(timeout=10)
            except BaseException as exc:
                error = f'{type(exc).__name__}: {exc}'
                stop_group(child)
                code = child.returncode
    receipt = dict(started, completed_utc=utc(), elapsed_seconds=time.monotonic() - t0,
                   returncode=code, stop_reason=reason, observer_error=error,
                   sampled_peak_process_tree_rss_bytes=peak, rss_samples=count,
                   stdout_sha256=sha(out / 'stdout.txt'), stderr_sha256=sha(out / 'stderr.txt'))
    worker = D / 'execution_01/receipt.json'
    if worker.exists():
        receipt['worker_receipt_sha256'] = sha(worker)
        receipt['worker_status'] = json.loads(worker.read_text()).get('status')
    write_json(out / 'receipt.json', receipt)
    (out / 'receipt.json').chmod(0o444)
    append_event('S70完整生成实际外部返回',
                 f'returncode={code}，stop_reason={reason}，外部{receipt["elapsed_seconds"]:.6f}秒，采样峰RSS={peak}B，worker={receipt.get("worker_status", "missing")}。此记录不解释为创新或画质收益。',
                 [str((out / 'receipt.json').relative_to(R))],
                 '核全部实际输出与同输入重放/随机状态，再执行已冻结全部目标评分；任何失败原样保留。',
                 occurred_at=receipt['completed_utc'])
    print(json.dumps(receipt, ensure_ascii=False))
    return 0 if code == 0 and reason is None and error is None else 1


if __name__ == '__main__':
    raise SystemExit(main())
