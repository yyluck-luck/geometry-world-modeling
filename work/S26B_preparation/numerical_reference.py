"""S26B reference bridge: unchanged S17 pair objective + repaired FP32 clean.

Only validation changes. This module is not imported during draft preparation.
"""
import hashlib
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def load(path,name,expected):
    with path.open('rb') as handle:
        assert hashlib.file_digest(handle,'sha256').hexdigest()==expected
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


old=load(ROOT/'work/S17C_independent_preparation/numerical_reference.py','s26b_original_pair_reference',
         '5d3661d314456a83d47f1e2326c1d3756838445280327a47e86cbe651a8424f7')
revised=load(ROOT/'work/S26_clean_recovery/clean_reference_torch_fp32.py','s26b_revised_clean_reference',
             '1ac18e88d2aec9e121da2d326f91f6a6d7950d7325473eb6e83dc0791a2f0b3e')
pair_objective=old.pair_objective
clean_reference=revised.clean_reference
