"""Bounded declared-variant two-batch entry, derived from the unchanged S35 supervisor."""
from __future__ import annotations
import ast
import copy
import hashlib
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
S35=ROOT/'work/S35_generation_integration'
PARENT=S35/'launch_original.py'
PARENT_SHA='8744cb8959cded2394c1471c660dd84f929b5ae24ac97e81379304aed0be702e'
LABELS={
    's35-original-generation-run-v1':'s40-declared-variant-two-batch-v1',
    'FROZEN_REAL_EXECUTION':'FROZEN_DECLARED_VARIANT_TWO_BATCH_EXECUTION',
    's35-original-worker-v1':'s40-declared-variant-worker-v1',
    's35-original-launch-v1':'s40-declared-variant-launch-v1',
    'ORIGINAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW':'DECLARED_VARIANT_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW',
    'COMPLETED_EXTERNAL_RUN_PENDING_INDEPENDENT_REVIEW':'DECLARED_VARIANT_EXTERNAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW',
    'FAILED_OR_PARTIAL_ORIGINAL_RUN':'FAILED_OR_PARTIAL_DECLARED_VARIANT_RUN',
}


def derive_launcher(*, compile_only=False):
    original_bytes=PARENT.read_bytes()
    if hashlib.sha256(original_bytes).hexdigest()!=PARENT_SHA: raise RuntimeError('Original S35 launcher changed')
    original=ast.parse(original_bytes,filename=str(PARENT))
    changes={}; counts={k:0 for k in LABELS}; routes={'resource_gate.py':0,'runtime_factory.py':0}; here_count=0
    def changed(old,new):
        new=ast.copy_location(new,old)
        key=(type(new).__name__,new.lineno,new.col_offset)
        if key in changes: raise RuntimeError('Overlapping launcher edits')
        changes[key]=(copy.deepcopy(old),ast.dump(new,include_attributes=False))
        return new
    class Route(ast.NodeTransformer):
        def visit_Assign(self,node):
            nonlocal here_count
            if len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='HERE':
                here_count+=1
                replacement=copy.deepcopy(node)
                replacement.value=ast.Call(func=ast.Name(id='Path',ctx=ast.Load()),args=[ast.Constant(str(S35))],keywords=[])
                return changed(node,replacement)
            return self.generic_visit(node)
        def visit_BinOp(self,node):
            if (isinstance(node.op,ast.Div) and isinstance(node.left,ast.Name) and node.left.id=='HERE' and
                    isinstance(node.right,ast.Constant) and node.right.value in routes):
                name=node.right.value;routes[name]+=1
                target='generation_gate.py' if name=='resource_gate.py' else 'runtime_adapter.py'
                return changed(node,ast.Call(func=ast.Name(id='Path',ctx=ast.Load()),
                    args=[ast.Constant(str(HERE/target))],keywords=[]))
            return self.generic_visit(node)
        def visit_Constant(self,node):
            if isinstance(node.value,str) and node.value in LABELS:
                counts[node.value]+=1
                return changed(node,ast.Constant(LABELS[node.value]))
            return node
    derived=Route().visit(copy.deepcopy(original));ast.fix_missing_locations(derived)
    expected={k:1 for k in LABELS}
    expected['ORIGINAL_RUN_RETURNED_PENDING_INDEPENDENT_REVIEW']=3
    expected['COMPLETED_EXTERNAL_RUN_PENDING_INDEPENDENT_REVIEW']=2
    expected['FAILED_OR_PARTIAL_ORIGINAL_RUN']=2
    if counts!=expected or routes!={'resource_gate.py':2,'runtime_factory.py':1} or here_count!=1:
        raise RuntimeError('Unexpected original routing/label locations: '+str((counts,routes,here_count)))
    restored_keys=set()
    class Restore(ast.NodeTransformer):
        def generic_visit(self,node):
            key=(type(node).__name__,getattr(node,'lineno',None),getattr(node,'col_offset',None))
            if key in changes:
                old,new_dump=changes[key]
                if ast.dump(node,include_attributes=False)!=new_dump: raise RuntimeError('Changed derivation subtree')
                restored_keys.add(key);return copy.deepcopy(old)
            return super().generic_visit(node)
    restored=Restore().visit(copy.deepcopy(derived))
    if len(restored_keys)!=len(changes) or ast.dump(restored,include_attributes=False)!=ast.dump(original,include_attributes=False):
        raise RuntimeError('Launcher differs beyond listed route/identity edits')
    code=compile(derived,str(PARENT)+'[S40 route/labels]','exec')
    proof=dict(parent_sha256=PARENT_SHA,label_counts=counts,route_counts=routes,here_assignments=here_count,
        reversible_full_AST_equal=True,original_budget_and_trace_boundary_math_unchanged=True)
    if compile_only: return proof
    # __file__ is the real S40 entry for source binding and fresh child dispatch.
    ns=dict(__file__=str(Path(__file__).resolve()),__name__='_s40_derived_supervisor')
    exec(code,ns)
    return ns


if __name__=='__main__':
    raise SystemExit(derive_launcher()['main']())
