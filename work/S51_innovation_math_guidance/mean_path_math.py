"""Exact linear-algebra diagnostic, not a VMem/model execution."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sympy as s

ROOT = Path('/Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling')
D = Path(__file__).resolve().parent
pipeline = ROOT / 'vendor/vmem_snapshot/modeling/pipeline.py'
source = pipeline.read_text()
assert 'context_encoder_embeddings = torch.mean(encoder_embeddings, dim=0)' in source
assert 'c_replace[input_masks] = context_latents' in source
rows = []
for k in range(1, 5):
    for d in range(1, 5):
        A = s.kronecker_product(s.ones(1, k) / k, s.eye(d))
        basis = A.nullspace()
        assert A.rank() == d
        assert len(basis) == (k - 1) * d
        assert all(A * v == s.zeros(d, 1) for v in basis)
        rows.append(dict(K=k, d=d, rank=A.rank(), nullity=len(basis)))
# An exact witness: two distinct source assignments share a semantic average.
A = s.kronecker_product(s.ones(1, 2) / 2, s.eye(2))
x = s.Matrix([1, 0, 0, 1])
delta = s.Matrix([2, -3, -2, 3])
assert A * delta == s.zeros(2, 1)
assert A * x == A * (x + delta)
# Other conditioning paths can distinguish x. Counterexample to the invalid
# inference that an invariant semantic average forces the whole generator
# invariant: a hypothetical output using the first latent/source changes.
other_path = s.Matrix([[1, 0, 0, 0], [0, 1, 0, 0]])
assert other_path * x != other_path * (x + delta)
receipt = dict(
    completed_utc=datetime.now(timezone.utc).isoformat(),
    status='EXACT_MATH_DIAGNOSTIC_COMPLETED_NOT_MODEL_EXPERIMENT',
    python_version=platform.python_version(), sympy_version=s.__version__,
    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    pipeline_sha256=hashlib.sha256(pipeline.read_bytes()).hexdigest(),
    formula='A=(ones(1,K)/K) tensor I_d; rank=d, nullity=(K-1)d',
    exact_cases=rows,
    witness=dict(x=list(map(str,x)), delta=list(map(str,delta)),
                 mean=list(map(str,A*x)), perturbed_mean=list(map(str,A*(x+delta))),
                 other_path_before=list(map(str,other_path*x)),
                 other_path_after=list(map(str,other_path*(x+delta)))),
    general_proof='A maps to R^d and is surjective: set e1=K*y and remaining ej=0. Thus rank d and rank-nullity gives (K-1)d. Nullspace consists exactly of source changes summing to zero.',
    limits=['Exact-real-arithmetic statement; machine reductions can round differently.',
            'Constructed features need not correspond to actual image encoder outputs.',
            'The source-specific latent path is still present; no whole-model invariance or quality-loss conclusion.',
            'Ordinary linear algebra, not a new theorem or validated method.'],
    model_runs=0, real_tensor_bodies_read=0, pixels_decoded=0,
    novelty_authorization='NONE', new_method_validated=False)
with (D/'MATH_RECEIPT.json').open('x') as f:
    json.dump(receipt,f,ensure_ascii=False,indent=2); f.write('\n')
print(json.dumps(dict(status=receipt['status'], exact_cases=len(rows), sympy=s.__version__, pipeline_sha256=receipt['pipeline_sha256'])))
