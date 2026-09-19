"""One terminal-only HTTP Range recovery candidate. Import performs no I/O.

This preserves the source and never treats its apparent size as a verified prefix.
Only a complete, stable file matching the original SHA is promoted in the new output.
No automatic retry, no browser credentials, no modification of an active transfer.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.metadata
import json
import logging
import os
import re
import signal
import stat
import time
from urllib.parse import urlsplit

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
AUTH = ROOT / 'work/S39_auth_recovery'
REPO = 'liguang0115/vmem'
REV = 'ac5921080a57f5a634f4b9acbbc8f3db67c9d113'
FILENAME = 'vmem_weights.pth'
SIZE = 5056346672
SHA = '675dc486a02ea06ecf8b6ab0cf4ef88c92298751b2daacf9f65c59871fcb7fe4'
PROXY = 'http://127.0.0.1:7897'
CHUNK = 1024 * 1024


class StopRecovery(Exception):
    """Contains only an internal, non-secret diagnostic code."""


def utc():
    return datetime.now(timezone.utc).isoformat()


def require(condition, code):
    if not condition:
        raise StopRecovery(code)


def identity(s):
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def read_json_identity(path):
    data = path.read_bytes()
    return json.loads(data), hashlib.sha256(data).hexdigest()


def check_terminal(receipt):
    require(receipt.get('attempt') == 3, 'WRONG_ATTEMPT')
    require(receipt.get('repo') == REPO and receipt.get('revision') == REV,
            'WRONG_REPO_OR_REVISION')
    require(receipt.get('expected_bytes') == SIZE and receipt.get('expected_sha256') == SHA,
            'WRONG_EXPECTED_IDENTITY')
    require(receipt.get('status') in {'TIMED_OUT', 'INTERRUPTED', 'FAILED',
                                    'DOWNLOAD_FAILED', 'FILE_IDENTITY_MISMATCH'},
            'NOT_UNVERIFIED_TERMINAL_STATUS')
    require(bool(receipt.get('finished_utc')), 'MISSING_TERMINAL_TIME')
    require(receipt.get('child_still_alive') is False and
            receipt.get('group_still_alive') is False, 'CHILD_OR_GROUP_NOT_CONFIRMED_DEAD')
    pgid = receipt.get('process_group')
    require(type(pgid) is int and pgid > 1, 'BAD_PROCESS_GROUP')
    # Signal 0 only checks existence; it never stops or changes any process.
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return
    raise StopRecovery('PROCESS_GROUP_CURRENTLY_EXISTS')


def valid_content_range(value, offset):
    m = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', value or '')
    return m is not None and tuple(map(int, m.groups())) == (offset, SIZE - 1, SIZE)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', required=True)
    parser.add_argument('--output', type=Path, required=True,
                        help='New directory under project data/vmem_recovery; must not exist')
    parser.add_argument('--seconds', type=int, required=True,
                        help='Explicit total wall-clock bound, including copying and SHA checks; 1..7200')
    args = parser.parse_args()
    require(1 <= args.seconds <= 7200, 'BAD_TOTAL_BUDGET')
    out = args.output.resolve()
    require(out.is_relative_to((ROOT / 'data/vmem_recovery').resolve()), 'OUTPUT_OUTSIDE_RECOVERY_ROOT')
    out.mkdir(parents=True, exist_ok=False)
    receipt = dict(started_utc=utc(), status='PRECHECK', repo=REPO, revision=REV,
                   filename=FILENAME, expected_bytes=SIZE, expected_sha256=SHA,
                   total_budget_seconds=args.seconds, sdk_version_required='1.30.0',
                   source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   prefix_content_verified=False, automatic_retries=0,
                   metadata_requests=[], range_requests=[], scientific_execution=False,
                   credentials_read_by_official_sdk_only=True,
                   canonical_target_modified=False, source_partial_modified=False)
    begin = time.monotonic()

    def save():
        temp = out / 'receipt.tmp'
        temp.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
        temp.replace(out / 'receipt.json')

    def deadline(signum=None, frame=None):
        raise StopRecovery('TOTAL_DEADLINE' if signum == signal.SIGALRM else 'SIGNAL_INTERRUPTED')

    def tick():
        require(time.monotonic() - begin < args.seconds, 'TOTAL_DEADLINE')

    def full_hash(path):
        h = hashlib.sha256()
        with path.open('rb') as f:
            before = os.fstat(f.fileno())
            for chunk in iter(lambda: f.read(CHUNK), b''):
                tick()
                h.update(chunk)
            after = os.fstat(f.fileno())
        require(identity(before) == identity(after) == identity(path.stat()),
                'CANDIDATE_CHANGED_DURING_HASH')
        return h.hexdigest(), before.st_size

    save()
    signal.signal(signal.SIGALRM, deadline)
    signal.signal(signal.SIGTERM, deadline)
    signal.setitimer(signal.ITIMER_REAL, args.seconds)
    result = 1
    try:
        terminal, terminal_sha = read_json_identity(AUTH / 'vmem_low_concurrency_attempt3/receipt.json')
        check_terminal(terminal)
        receipt['terminal_receipt_sha256'] = terminal_sha
        preservation, preservation_sha = read_json_identity(AUTH / 'partial_preservation.json')
        receipt['preservation_record_sha256'] = preservation_sha
        source = Path(preservation['preserved_live_link'])
        require(source == ROOT / 'data/vmem_recovery/attempt3_live_partial.link', 'WRONG_SOURCE_PATH')
        require(not source.is_symlink(), 'SOURCE_SYMLINK_REJECTED')
        candidate = out / 'candidate.unverified.part'
        with os.fdopen(os.open(source, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as src:
            before = os.fstat(src.fileno())
            require(stat.S_ISREG(before.st_mode), 'SOURCE_NOT_REGULAR')
            require((before.st_dev, before.st_ino) ==
                    (preservation['device'], preservation['inode']), 'PRESERVED_INODE_MISMATCH')
            require(0 < before.st_size <= SIZE, 'SOURCE_SIZE_OUT_OF_BOUNDS')
            receipt.update(status='COPYING_UNVERIFIED_SOURCE', source_path=str(source),
                           apparent_prefix_bytes=before.st_size, source_identity=list(identity(before)))
            save()
            copied = 0
            prefix_hash = hashlib.sha256()
            with candidate.open('xb') as dst:
                for chunk in iter(lambda: src.read(CHUNK), b''):
                    tick()
                    copied += len(chunk)
                    require(copied <= before.st_size, 'SOURCE_GREW_DURING_COPY')
                    prefix_hash.update(chunk)
                    dst.write(chunk)
                dst.flush()
                os.fsync(dst.fileno())
            require(copied == before.st_size and identity(before) == identity(os.fstat(src.fileno()))
                    == identity(source.stat()), 'SOURCE_CHANGED_DURING_COPY')
        receipt['copied_source_sha256'] = prefix_hash.hexdigest()
        receipt['prefix_content_verified'] = False  # A hash without an authoritative prefix hash is not verification.
        # Recheck terminal evidence before any network request. A changed receipt is rejected.
        terminal_again, terminal_sha_again = read_json_identity(AUTH / 'vmem_low_concurrency_attempt3/receipt.json')
        require(terminal_sha_again == terminal_sha, 'TERMINAL_RECEIPT_CHANGED')
        check_terminal(terminal_again)
        if copied < SIZE:
            # All environment is set before importing the official SDK. No credential files are opened here.
            os.environ['HF_HOME'] = '/Users/rocket/.cache/huggingface-research-s39'
            os.environ['HF_DEBUG'] = '0'
            os.environ['HF_HUB_OFFLINE'] = '0'
            os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
            os.environ['HF_HUB_DISABLE_UPDATE_CHECK'] = '1'
            logging.disable(logging.CRITICAL)  # Third-party error logs can contain signed URLs.
            require(importlib.metadata.version('huggingface_hub') == '1.30.0', 'SDK_VERSION_MISMATCH')
            import httpx
            from huggingface_hub import get_hf_file_metadata, hf_hub_url, set_client_factory

            def metadata_guard(request):
                require(request.method == 'HEAD' and request.url.scheme == 'https' and
                        request.url.host == 'huggingface.co' and request.url.port in (None, 443),
                        'METADATA_REQUEST_HOST_OR_METHOD_REJECTED')
                require(len(receipt['metadata_requests']) < 3, 'METADATA_REDIRECT_LIMIT')
                receipt['metadata_requests'].append(dict(time_utc=utc(), host='huggingface.co', method='HEAD'))
                save()

            def metadata_response(response):
                receipt['metadata_requests'][-1]['http_status'] = response.status_code

            # Factory is used by the official SDK; no retries, TLS verification remains enabled.
            metadata_client = httpx.Client(proxy=PROXY, trust_env=False, verify=True,
                timeout=httpx.Timeout(20.0), follow_redirects=False,
                event_hooks={'request': [metadata_guard], 'response': [metadata_response]})
            set_client_factory(lambda: metadata_client)
            receipt.update(status='VERIFYING_OFFICIAL_METADATA', metadata_started_utc=utc())
            save()
            try:
                metadata = get_hf_file_metadata(hf_hub_url(REPO, FILENAME, revision=REV,
                    endpoint='https://huggingface.co'), token=True, timeout=20.0, retry_on_errors=False)
            finally:
                metadata_client.close()
            require(metadata.commit_hash == REV and metadata.size == SIZE and metadata.etag == SHA,
                    'OFFICIAL_METADATA_IDENTITY_MISMATCH')
            location = metadata.location  # Signed URL lives only in process memory.
            u = urlsplit(location)
            require(u.scheme == 'https' and u.hostname and u.hostname != 'huggingface.co' and
                    u.port in (None, 443) and not u.username and not u.password and not u.fragment and u.query,
                    'EXPECTED_SIGNED_HTTPS_CDN_LOCATION_UNAVAILABLE')
            receipt['official_metadata_identity_verified'] = True
            receipt['range_requests'].append(dict(time_utc=utc(), host=u.hostname,
                start=copied, end=SIZE-1, bearer_sent=False, redirects_followed=0))
            receipt.update(status='RANGE_TRANSFER', range_started_utc=utc(), received_range_bytes=0)
            save()
            # A separate client has no SDK Authorization or cookie state. No redirect can forward a bearer.
            with httpx.Client(proxy=PROXY, trust_env=False, verify=True,
                              timeout=httpx.Timeout(30.0), follow_redirects=False) as cdn:
                with cdn.stream('GET', location, headers={'Range': f'bytes={copied}-{SIZE-1}',
                                                         'Accept-Encoding': 'identity'}) as response:
                    receipt['range_requests'][-1]['http_status'] = response.status_code
                    require(response.status_code == 206, 'RANGE_NOT_206_NO_FALLBACK')
                    require(valid_content_range(response.headers.get('Content-Range'), copied),
                            'CONTENT_RANGE_MISMATCH')
                    require(response.headers.get('Content-Encoding', 'identity').lower() == 'identity',
                            'ENCODED_RANGE_REJECTED')
                    if 'Content-Length' in response.headers:
                        require(int(response.headers['Content-Length']) == SIZE-copied, 'CONTENT_LENGTH_MISMATCH')
                    save()
                    with candidate.open('ab') as dst:
                        for chunk in response.iter_raw(chunk_size=CHUNK):
                            tick()
                            total = receipt['received_range_bytes'] + len(chunk)
                            require(total <= SIZE-copied, 'RANGE_BODY_EXCEEDS_DECLARED_REMAINDER')
                            dst.write(chunk)
                            receipt['received_range_bytes'] = total
                        dst.flush()
                        os.fsync(dst.fileno())
                    require(receipt['received_range_bytes'] == SIZE-copied, 'RANGE_BODY_SHORT')
            receipt['range_finished_utc'] = utc()
        else:
            receipt['network_skipped_reason'] = 'Source already full apparent size; verify complete SHA locally first'
        receipt.update(status='VERIFYING_COMPLETE_SHA', hash_started_utc=utc())
        save()
        actual_sha, actual_size = full_hash(candidate)
        receipt.update(actual_sha256=actual_sha, actual_bytes=actual_size, hash_finished_utc=utc())
        require(actual_size == SIZE and actual_sha == SHA, 'FULL_FILE_SHA_OR_SIZE_MISMATCH')
        tick()
        final = out / FILENAME
        require(not final.exists(), 'FINAL_OUTPUT_EXISTS')
        os.link(candidate, final)  # Exclusive creation; never replaces an existing destination.
        candidate.unlink()
        receipt.update(status='VERIFIED_COMPLETE_ORIGINAL_WEIGHT', final_path=str(final),
                       prefix_content_verified=True)
        result = 0
    except BaseException as exc:
        # Do not stringify third-party exceptions: they can include bearer values or signed URLs.
        receipt.update(status='FAILED_RETAIN_UNVERIFIED_CANDIDATE', error_type=type(exc).__name__,
            error_code=str(exc) if isinstance(exc, StopRecovery) else 'EXTERNAL_EXCEPTION_DETAILS_NOT_LOGGED')
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        receipt.update(finished_utc=utc(), elapsed_seconds=time.monotonic()-begin)
        save()
        print(json.dumps({'status': receipt['status'], 'receipt': str(out/'receipt.json')}, ensure_ascii=False))
    return result


if __name__ == '__main__':
    raise SystemExit(main())
