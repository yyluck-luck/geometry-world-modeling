#!/usr/bin/env python3
"""用已配置的本地 DSH 做一次只读科研审查；不重试、不升级模型。"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
ROUTE = ROOT / 'work/S76_relative_camera_response/dsh_protocol_review_01'
RUNTIME = ROOT / 'tools/deepseek-harness/runtime'
DSH_HOME = ROOT / 'tools/deepseek-harness/state'
NODE = Path('/Users/rocket/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
CLI = RUNTIME / 'node_modules/@deepseek-ai/dsh/lib/bin.js'
MODEL = 'deepseek/deepseek-v4-flash-0731'
PROVIDER = 'openrouter'
SECONDS = 180
MAX_WORDS = 900  # Prompt request only: neither a token limit nor a price cap.
OLD_SETTINGS_SHA = 'fe02e2308c90e52765f0dc2e767261bea41ce4f7b500688f0fe6f05ee0a193a8'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def write_new(path, value, mode=0o600):
    body = value if isinstance(value, bytes) else value.encode('utf-8')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(fd, 'wb') as handle:
        handle.write(body)


def write_json(path, value):
    write_new(path, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog='固定 OpenRouter DeepSeek V4 Flash；180秒外部上限。900词仅提示软约束；费用和实际模型身份仍需回执核验。')
    parser.add_argument('--prompt', type=Path, required=True, help='现有 UTF-8 科研问题文本；自行包含必要材料')
    parser.add_argument('--output', type=Path, required=True, help='本项目内尚不存在的新输出目录')
    args = parser.parse_args()
    prompt_path = args.prompt.expanduser().resolve(strict=True)
    output = args.output.expanduser().resolve()
    if (not output.is_relative_to(ROOT) or output.is_relative_to(DSH_HOME)
            or output.exists() or not output.parent.is_dir()):
        parser.error('输出必须是项目内、私有state之外、父目录已存在的新目录。')
    if (not prompt_path.is_file() or prompt_path.is_relative_to(DSH_HOME)
            or prompt_path.name == '.credentials.yaml'):
        parser.error('只接受现有科研文本，不读取私有state或凭据文件。')
    if prompt_path.stat().st_size > 48_000:
        parser.error('文本超过48000字节，请收束成一个具体问题再运行。')
    prompt_body = prompt_path.read_bytes()
    prompt = prompt_body.decode('utf-8')
    if not prompt.strip():
        parser.error('科研问题文本不能为空。')
    # The already successful dedicated settings contain only the environment-name reference.
    # Never open DSH_HOME/settings.yaml or .credentials.yaml, or inspect an API key value.
    old_settings = ROUTE / 'review.settings.yaml'
    if sha(old_settings) != OLD_SETTINGS_SHA:
        parser.error('原成功路线的专用settings已变，需先检查；不会回退到其他模型。')
    matches = re.findall(r'^\s+apiKeyEnv:\s*([A-Za-z_][A-Za-z0-9_]*)\s*$', old_settings.read_text(), re.M)
    if len(matches) != 1:
        parser.error('原专用settings没有唯一apiKeyEnv引用。')
    api_ref = matches[0]
    if not NODE.is_file() or not CLI.is_file() or not DSH_HOME.is_dir():
        parser.error('原Node24、已安装DSH或原DSH_HOME缺失；不自动安装。')
    package = RUNTIME / 'node_modules/@deepseek-ai/dsh/package.json'
    if json.loads(package.read_text()).get('version') != '0.1.2-rc.1':
        parser.error('已安装DSH版本变化，需检查原路线；不会自动升级。')
    version = subprocess.run([str(NODE), '--version'], capture_output=True, text=True, timeout=5, check=True).stdout.strip()
    if not version.startswith('v24.'):
        parser.error('已固定Node路径不再是Node24；停止。')
    os.umask(0o077)
    output.mkdir(mode=0o700, exist_ok=False)
    write_new(output / 'PROMPT.original.txt', prompt_body)
    task = ('Give a concise research second opinion in English. Use only the material in this prompt; '
            'do not execute code, edit files, inspect credentials, or contact people. '
            f'Aim for at most {MAX_WORDS} words; this is a soft instruction, not an enforced output/token/cost cap. '
            'Separate supported facts, assumptions, counterexamples, and the next cheapest falsifiable check. '
            'Do not claim model execution, independent scientific validation, or established novelty.\n\n' + prompt)
    write_new(output / 'PROMPT.sent.txt', task)
    settings = {'agent-default-model': {'provider': PROVIDER, 'model': MODEL},
                'llm-pi-ai': {'providers': {PROVIDER: {'apiKeyEnv': api_ref}}},
                'permission': {'defaultPreset': 'read-only'}}
    # JSON is valid YAML; the dedicated files use the same effective patch keys as the successful run.
    write_json(output / 'review.settings.yaml', settings)
    patch = [dict(id='settings', config=dict(path=str(output / 'review.settings.yaml'), watch=False)),
             dict(id='tools', config=dict(mode='native')),
             dict(id='sandbox-policy', config=dict(mode='read-only', workspaceRoot=str(output))),
             dict(id='approval', config=dict(policy='never')),
             dict(id='permission', config=dict(presets={'read-only': dict(sandbox='read-only', approval='never')}, defaultPreset='read-only'))]
    write_json(output / 'review.patch.yml', patch)
    env = os.environ.copy()
    env.update(DSH_HOME=str(DSH_HOME), DSH_PERMISSION_MODE='read-only',
               PATH=str(NODE.parent) + os.pathsep + env.get('PATH', ''))
    argv = [str(NODE), str(CLI), '--profile', 'headless', '--patch', str(output / 'review.patch.yml'), task]
    started = utc(); begin = time.monotonic(); child = None; reason = None; error_type = None
    receipt = dict(schema='dsh-readonly-research-review-v1', started_utc=started,
                   requested_provider=PROVIDER, requested_model=MODEL, actual_model_verified=False,
                   node_version=version, installed_dsh_version='0.1.2-rc.1', profile='headless',
                   cwd=str(output), external_timeout_seconds=SECONDS, requested_max_words=MAX_WORDS,
                   word_limit_is_soft=True, cost_cap_enforced=False, permission_mode='read-only',
                   approval='never', tools='native', no_tools_is_prompt_only=True,
                   original_prompt_path=str(prompt_path), api_key_env_reference=api_ref,
                   source_sha256=sha(__file__), cli_sha256=sha(CLI), package_sha256=sha(package),
                   old_settings_sha256=OLD_SETTINGS_SHA,
                   input_sha256={n: sha(output / n) for n in ['PROMPT.original.txt', 'PROMPT.sent.txt', 'review.settings.yaml', 'review.patch.yml']},
                   retries_by_wrapper=0, model_fallback_by_wrapper=False,
                   credentials_file_read_by_wrapper=False,
                   private_stderr_not_for_public_delivery=True)
    sys.path.insert(0, str(ROOT / 'scripts'))
    from research_log import append_event
    evidence = [str((output / 'RECEIPT.json').relative_to(ROOT))]
    try:
        with (output / 'stdout.md').open('x') as stdout, (output / 'stderr.private.log').open('x') as stderr:
            child = subprocess.Popen(argv, cwd=output, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
            receipt.update(pid=child.pid, pgid=child.pid)
            write_json(output / 'STARTED.json', receipt)
            append_event('低成本DSH科研审查实际启动',
                         f'请求固定{PROVIDER}/{MODEL}，只读/native、approval never，180秒外部上限；900词为软约束，不代表费用上限。',
                         [str((output / 'STARTED.json').relative_to(ROOT))],
                         '保存真实返回后核对建议和原始来源，不据模型回答宣称创新。', occurred_at=started)
            child.wait(timeout=max(0.01, SECONDS - (time.monotonic() - begin)))
    except subprocess.TimeoutExpired:
        reason = 'EXTERNAL_180_SECOND_LIMIT'
    except BaseException as error:
        reason = 'WRAPPER_OR_START_ERROR'; error_type = type(error).__name__
    finally:
        if child is not None and child.poll() is None:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                reason = 'PROCESS_GROUP_REAP_TIMEOUT'
        receipt.update(completed_utc=utc(), elapsed_seconds=time.monotonic() - begin,
                       returncode=None if child is None else child.returncode,
                       stop_reason=reason, wrapper_error_type=error_type,
                       status='RETURNED' if child is not None and child.returncode == 0 and reason is None else 'FAILED_PRESERVED')
        receipt['outputs'] = {n: dict(bytes=(output / n).stat().st_size, sha256=sha(output / n))
                              for n in ['stdout.md', 'stderr.private.log'] if (output / n).is_file()}
        write_json(output / 'RECEIPT.json', receipt)
        append_event('低成本DSH科研审查实际返回',
                     f"外部{receipt['elapsed_seconds']:.6f}秒，return{receipt['returncode']}，停止原因{reason}。输出属于外部模型意见，实际模型身份和费用未由包装器独立验证。",
                     evidence, '检查正文、核原文与实际证据；不自动重试、升级模型或改正在运行的实验。', occurred_at=receipt['completed_utc'])
    print(json.dumps(dict(status=receipt['status'], receipt=str(output / 'RECEIPT.json')), ensure_ascii=False))
    return 0 if receipt['status'] == 'RETURNED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
