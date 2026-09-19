"""Launch only the new synthetic wiring checks using the existing bounded runner."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract', required=True)
    parser.add_argument('--contract-sha256', required=True)
    args = parser.parse_args()
    assert sha(args.contract) == args.contract_sha256
    contract = json.loads(Path(args.contract).read_text())
    assert contract['status'] == 'FROZEN_SYNTHETIC_TEST'
    assert contract['evidence_kind'] == 'synthetic_test'
    assert contract['external_supervisor']['wrapper_sha256'] == sha(__file__)
    base = ROOT/'scripts/s26b_consumer_baseline.py'
    assert contract['external_supervisor']['base_sha256'] == sha(base)
    assert contract['limits'] == dict(cpu_threads=1, seconds=120, rss_bytes=2*1024**3)
    spec = importlib.util.spec_from_file_location('s35_existing_external_supervisor', base)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # Standard-library definitions only.
    module.WORK = HERE
    for key in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS',
                'VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:
        os.environ[key] = '1'
    os.environ.update(PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1',
                      TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_IMPLICIT_TOKEN='1')
    command = [str(ROOT/'.venv-cut3r/bin/python'), '-B',
               str(HERE/'artificial_wiring_checks.py'), '--contract',
               str(Path(args.contract).resolve()), '--contract-sha256', args.contract_sha256]
    module.supervised(command, contract['external_supervisor']['execution_name'], 120, 2*1024**3)


if __name__ == '__main__':
    main()
