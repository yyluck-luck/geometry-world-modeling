"""Root one-shot, 60-second observer for the reviewed CPU conditioning component."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import signal
import subprocess
import sys
import time

D = Path(__file__).resolve().parent
R = D.parents[1]

def utc():
    return datetime.now(timezone.utc).isoformat()

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    binding_path = D / "ROOT_RUN_BINDING.json"
    assert digest(binding_path) == sys.argv[1]
    binding = json.loads(binding_path.read_text())
    for path, expected in binding["reviewed_files"].items():
        assert digest(Path(path)) == expected, path
    argv = binding["argv"]
    assert argv[0] == str(R / ".venv-cut3r/bin/python")
    output = D / "external_01"
    output.mkdir()
    record = {"started_utc": utc(), "argv": argv, "binding_sha256": digest(binding_path),
              "observer_sha256": digest(Path(__file__)), "timeout_seconds": 60,
              "rss_enforcement": "No external RSS cap or RSS measurement in this small component. No model weights permitted by protocol."}
    sys.path.insert(0, str(R / "scripts"))
    from research_log import append_event
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", HF_HUB_OFFLINE="1",
               TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
    begin = time.monotonic()
    with (output / "stdout.txt").open("x") as stdout, (output / "stderr.txt").open("x") as stderr:
        process = subprocess.Popen(argv, cwd=R, stdout=stdout, stderr=stderr,
                                   env=env, start_new_session=True)
        record["pid"] = process.pid
        (output / "started.json").write_text(json.dumps(record, indent=2) + "\n")
        append_event("S69六相机与两组原条件计算实际启动", "原始GT文字、已保存三相机和五历史缓存；无RGB/depth/权重正文，无视频。外部60秒timeout，不硬限RSS。", [str((output / "started.json").relative_to(R))], "等待唯一一次真实返回并独立核验。", occurred_at=record["started_utc"])
        stop = None
        try:
            result = process.wait(timeout=60)
        except subprocess.TimeoutExpired:
            stop = "TIMEOUT_60_SECONDS"
            os.killpg(process.pid, signal.SIGKILL)
            result = process.wait()
    record.update(completed_utc=utc(), elapsed_seconds=time.monotonic() - begin,
                  returncode=result, stop_reason=stop,
                  stdout_sha256=digest(output / "stdout.txt"), stderr_sha256=digest(output / "stderr.txt"))
    worker = D / "execution_01/receipt.json"
    if worker.is_file():
        record["worker_receipt_sha256"] = digest(worker)
        record["worker_status"] = json.loads(worker.read_text()).get("status")
    (output / "receipt.json").write_text(json.dumps(record, indent=2) + "\n")
    append_event("S69原条件计算实际外部返回", f"returncode={result}，外部{record['elapsed_seconds']:.6f}秒，stop_reason={stop}；实际worker状态见回执，不据外部成功宣称物理标定或生成收益。", [str((output / "receipt.json").relative_to(R))], "保留全部结果或失败，执行不同作者相机/射线与条件结果核验。", occurred_at=record["completed_utc"])
    print(json.dumps(record, ensure_ascii=False))

if __name__ == "__main__":
    main()
