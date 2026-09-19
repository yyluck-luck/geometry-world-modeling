"""S35 passive full-output archive. No model calls, RNG draws or pipeline introspection.

Only the integration caller supplies live values. Closing this archive never
certifies generation, trace validity, model identity or scientific success.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import importlib.util
import io
import json
import os
import re
import struct
import sys
import threading

ROOT = Path(__file__).resolve().parents[2]
CODEC_PATH = ROOT / 'src/s20_generation_trace.py'
CODEC_SHA256 = 'daf841dbcb635417865ba8287ad305bbdf6105181fd39e169be2e666e1bfbc57'
SCHEMA = 's35-full-original-output-archive-v1'
HEX = re.compile(r'^[0-9a-f]{64}$')


def _utc():
    return datetime.now(timezone.utc).isoformat()


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def _require(ok, why):
    if not ok:
        raise ValueError(why)


class FullOutputArchive:
    """One fresh, single-process archive; multiple threads serialize on one lock.

    ``required_events`` is a sequence of names (at least once) or a mapping of
    name to minimum count. It checks archived coverage only, never science.
    ``source_identities`` records the caller's frozen identities; large assets
    are not opened or rehashed here. The own file and S20 codec are checked.
    """

    def __init__(self, directory: str | Path, *, evidence_kind: str,
                 source_identities: dict[str, str],
                 manifest_sha256: str | None = None, required_events=()):
        _require(evidence_kind in ('recorded_execution', 'synthetic_test'), 'Explicit evidence kind required')
        _require(bool(source_identities) and all(isinstance(p, str) and isinstance(h, str) and HEX.fullmatch(h)
                     for p, h in source_identities.items()), 'Source identity mapping must contain SHA256 strings')
        _require(manifest_sha256 is None or isinstance(manifest_sha256, str) and HEX.fullmatch(manifest_sha256), 'Invalid caller manifest SHA')
        _require(evidence_kind != 'recorded_execution' or manifest_sha256 is not None, 'Recorded execution requires frozen caller manifest SHA')
        _require(not isinstance(required_events, (str, bytes)), 'Required names must be a sequence or mapping, not one string')
        expected = dict(required_events) if isinstance(required_events, dict) else dict.fromkeys(required_events, 1)
        _require(all(isinstance(n, str) and n and isinstance(k, int) and not isinstance(k, bool) and k > 0
                     for n, k in expected.items()), 'Required event names/counts must be explicit')
        own = str(Path(__file__).resolve())
        _require(_sha(CODEC_PATH) == CODEC_SHA256, 'Frozen S20 canonical codec changed')
        own_sha = _sha(own)
        if evidence_kind == 'recorded_execution':
            _require(source_identities.get(own) == own_sha, 'Archive source must be bound by real caller')
            _require(source_identities.get(str(CODEC_PATH)) == CODEC_SHA256, 'Canonical codec must be bound by real caller')
        self.root = Path(directory).resolve()
        self.root.mkdir(parents=True, exist_ok=False)
        (self.root / 'tensors').mkdir()
        (self.root / 'images').mkdir()
        (self.root / 'bytes').mkdir()
        self.fd = os.open(self.root / 'events.jsonl', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND, 0o600)
        self.lock = threading.RLock()
        self.owner_pid = os.getpid()
        self.seq, self.previous, self.closed = 0, '0' * 64, False
        self.failed_captures = 0
        self.counts = Counter()
        self.required = expected
        self.source_identities = dict(source_identities)
        self.checked_small_sources = {own: own_sha, str(CODEC_PATH): CODEC_SHA256}
        self.caller_manifest_sha256 = manifest_sha256
        self.evidence_kind = evidence_kind
        self.codec = None
        self.descriptors = {}
        self._append('archive_start', dict(source_identities=self.source_identities,
            checked_small_sources=self.checked_small_sources,
            caller_manifest_sha256=manifest_sha256, required_events=expected,
            evidence_kind=evidence_kind, pid=self.owner_pid, python=sys.version,
            claim='Raw-byte preservation only; not technical generation success',
            rng_scope='Only explicitly supplied RNG states; no RNG draws or getters inside archive'))

    def _check_open(self):
        _require(os.getpid() == self.owner_pid, 'Do not share archive across forked processes')
        _require(not self.closed, 'Archive already closed')

    def _append(self, event, payload):
        self._check_open()
        row = dict(schema=SCHEMA, seq=self.seq, previous_sha256=self.previous,
                   utc=_utc(), evidence_kind=self.evidence_kind, event=event, payload=payload)
        row['sha256'] = _digest(_json(row))
        data = memoryview(_json(row) + b'\n')
        while data:
            written = os.write(self.fd, data)
            _require(written > 0, 'Archive event write failed')
            data = data[written:]
        os.fsync(self.fd)
        self.seq += 1
        self.previous = row['sha256']
        return dict(seq=row['seq'], sha256=row['sha256'], event=event)

    def _store(self, relative, raw):
        """Exclusive first write; identical full existing bytes may be referenced."""
        path = self.root / relative
        _require(path.parent in (self.root, self.root/'tensors', self.root/'images', self.root/'bytes'), 'Internal archive path only')
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            _require(path.stat().st_size == len(raw) and _sha(path) == _digest(raw), 'Existing content-addressed payload differs')
        else:
            with os.fdopen(fd, 'wb') as handle:
                view = memoryview(raw)
                while view:
                    written = handle.write(view)
                    _require(written is not None and written > 0, 'Archive payload write failed')
                    view = view[written:]
                handle.flush()
                os.fsync(handle.fileno())
        return dict(path=relative, bytes=len(raw), sha256=_digest(raw))

    def _tensor(self, value):
        if self.codec is None:
            _require(_sha(CODEC_PATH) == CODEC_SHA256, 'Canonical codec changed before first data capture')
            spec = importlib.util.spec_from_file_location('_s35_frozen_s20_archive_codec', CODEC_PATH)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.codec = module._tensor_bytes
        # Existing S20 codec uses detached CPU logical C-order materialization.
        # No in-place write, device assignment, random draw or model invocation.
        desc, raw = self.codec(value)
        identity = desc['sha256']
        relative = 'tensors/' + identity + '.bin'
        full = dict(desc, blob=relative)
        # Sidecar first leaves dtype/shape/expected identity if a later write fails.
        self._store('tensors/' + identity + '.json', _json(full) + b'\n')
        blob = self._store(relative, raw)
        _require(blob['sha256'] == desc['bytes_sha256'] and blob['bytes'] == desc['nbytes'], 'Complete tensor byte contract')
        self.descriptors[relative] = full
        return full

    def _image(self, image):
        from PIL import Image
        import numpy as np
        _require(isinstance(image, Image.Image), 'PIL Image required')
        _require(getattr(image, 'fp', None) is None, 'Refuse lazy file-backed image: caller must supply original already-loaded image')
        _require(image.mode in ('L', 'RGB', 'RGBA'), 'No implicit color or palette conversion')
        detached = image.copy()
        pixels = self._tensor(np.asarray(detached))
        stream = io.BytesIO()
        detached.save(stream, format='PNG')
        raw = stream.getvalue()
        png = self._store('images/' + _digest(raw) + '.png', raw)
        return dict(kind='pil_image', mode=image.mode, size=list(image.size),
                    pixels=pixels, png=png, original_format=image.format,
                    scope='Same loaded pixel values; PNG serialization, not VAE/CLIP encoding or original JPEG container identity')

    def _tree(self, value: Any, active: set[int]):
        # NumPy float64 can also be a Python float subclass; retain its dtype.
        if type(value).__module__.startswith('numpy'):
            return self._tensor(value)
        if value is None or isinstance(value, (str, bool, int)):
            return dict(kind='scalar', type=type(value).__name__, value=value)
        if isinstance(value, float):
            # Retain -0, nonfinite values and NaN payload bits without invalid JSON.
            return dict(kind='python_float64', little_endian_hex=struct.pack('<d', value).hex())
        if isinstance(value, (bytes, bytearray, memoryview)):
            raw = bytes(value)
            return dict(kind='bytes', blob=self._store('bytes/' + _digest(raw) + '.bin', raw))
        if isinstance(value, (dict, list, tuple)):
            _require(id(value) not in active, 'Cyclic containers are not archival payloads')
            active.add(id(value))
            try:
                if isinstance(value, dict):
                    _require(all(isinstance(k, (str, int)) and not isinstance(k, bool) for k in value), 'Only explicit string/integer mapping keys supported')
                    return dict(kind='dict', items=[dict(key=self._tree(k, active), value=self._tree(v, active)) for k,v in value.items()])
                return dict(kind='tuple' if isinstance(value, tuple) else 'list', items=[self._tree(v, active) for v in value])
            finally:
                active.remove(id(value))
        typename, module = type(value).__name__, type(value).__module__
        if module == 'torch' and typename in ('device', 'dtype'):
            return dict(kind='torch_metadata', type=typename, value=str(value))
        if module.startswith('torch'):
            return self._tensor(value)
        if module.startswith('PIL.'):
            return self._image(value)
        raise TypeError('Unsupported payload object; integration must extract explicit values: ' + module + '.' + typename)

    def capture(self, name: str, payload: Any) -> dict:
        """Capture explicit original values and return only an archive reference.

        Repeated names produce distinct ordered events. Never return a modified
        replacement of ``payload`` or of the original producer's return value.
        """
        _require(isinstance(name, str) and bool(name), 'Nonempty event name required')
        with self.lock:
            self._check_open()
            begin = self._append('capture_begin', dict(name=name, occurrence=self.counts[name]))
            try:
                tree = self._tree(payload, set())
                ref = self._append('capture_complete', dict(name=name, occurrence=self.counts[name], begin_seq=begin['seq'], tree=tree))
                self.counts[name] += 1
                return dict(ref, name=name, occurrence=self.counts[name]-1, directory=str(self.root))
            except BaseException as error:
                self.failed_captures += 1
                try:
                    self._append('capture_failed', dict(name=name, begin_seq=begin['seq'], exception_type=type(error).__name__, message=str(error)))
                except BaseException:
                    pass  # Caller retains original exception and outer failure receipt.
                raise

    def _inventory(self):
        return {str(p.relative_to(self.root)): dict(bytes=p.stat().st_size, sha256=_sha(p))
                for p in sorted(self.root.rglob('*')) if p.is_file() and p.name != 'manifest.json'}

    def finalize(self, *, status='COMPLETE', metadata=None) -> dict:
        """COMPLETE means requested archival names exist, never model success."""
        with self.lock:
            self._check_open()
            _require(status in ('COMPLETE', 'PARTIAL'), 'Use COMPLETE or PARTIAL archival status')
            missing = {n: dict(required=k, archived=self.counts[n]) for n,k in self.required.items() if self.counts[n] < k}
            if status == 'COMPLETE':
                _require(not missing and self.failed_captures == 0, 'Archive incomplete or prior capture failed')
            _json(metadata)  # Metadata is plain JSON; tensors belong in capture().
            _require(all(_sha(p) == h for p,h in self.checked_small_sources.items()),
                     'Archive/codec source changed during capture')
            for relative, desc in self.descriptors.items():
                p = self.root / relative
                _require(p.stat().st_size == desc['nbytes'] and _sha(p) == desc['bytes_sha256'], 'Tensor bytes changed before finalization')
            self._append('archive_finalize', dict(requested_status=status, missing_required_names=missing,
                archived_name_counts=dict(self.counts), caller_metadata=metadata, scientific_status='NOT_EVALUATED'))
            files = self._inventory()
            record = dict(schema=SCHEMA, status='ARCHIVE_'+status, completed_utc=_utc(), evidence_kind=self.evidence_kind,
                caller_manifest_sha256=self.caller_manifest_sha256, source_identities=self.source_identities,
                checked_small_sources_before_and_after=self.checked_small_sources,
                codec_path=str(CODEC_PATH), codec_sha256=CODEC_SHA256,
                required_events=self.required, archived_name_counts=dict(self.counts), missing_required_names=missing,
                failed_captures=self.failed_captures, event_count=self.seq, last_event_sha256=self.previous,
                tensor_descriptors=self.descriptors, files=files, caller_metadata=metadata,
                scientific_status='NOT_EVALUATED', scope='Complete raw objects supplied by caller, no inference/encode/RNG generation; no self-certification of loop completeness')
            path = self.root/'manifest.json'
            _require(not path.exists(), 'Never replace existing manifest')
            self._store('manifest.json', _json(record)+b'\n')
            os.close(self.fd)
            self.closed = True
            return dict(path=str(path), sha256=_sha(path), status=record['status'])

    def fail(self, error: BaseException, *, phase: str = 'caller') -> dict:
        """Best-effort failure closure; never suppress/relabel caller's exception.

        Caller must still re-raise its original failure and retain an external
        receipt. Hard termination/disk failure may leave only a durable prefix.
        """
        with self.lock:
            if self.closed:
                return dict(status='ALREADY_CLOSED', directory=str(self.root), scientific_status='NOT_EVALUATED')
            errors = []
            try:
                self._append('caller_failure', dict(phase=str(phase), exception_type=type(error).__name__, message=str(error)))
            except BaseException as archive_error:
                errors.append(type(archive_error).__name__+': '+str(archive_error))
            try:
                return self.finalize(status='PARTIAL', metadata=dict(phase=str(phase), exception_type=type(error).__name__, message=str(error), archive_errors=errors))
            except BaseException as archive_error:
                errors.append(type(archive_error).__name__+': '+str(archive_error))
                try:
                    self._store('failure_prefix.json', _json(dict(schema=SCHEMA, status='ARCHIVE_FAILURE_PREFIX', utc=_utc(),
                        error_type=type(error).__name__, error_message=str(error), archive_errors=errors,
                        archived_name_counts=dict(self.counts), files=self._inventory(), scientific_status='NOT_EVALUATED'))+b'\n')
                except BaseException:
                    pass
                finally:
                    try:
                        os.close(self.fd)
                    except OSError:
                        pass
                    self.closed = True
                return dict(status='ARCHIVE_FAILURE_PREFIX', directory=str(self.root), archive_errors=errors)
