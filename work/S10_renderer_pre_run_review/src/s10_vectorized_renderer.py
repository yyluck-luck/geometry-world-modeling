"""Experimental CPU raster-loop batching; not a new retrieval method.

All camera, disk construction, culling, surfel order and output-buffer code is
taken from the immutable VMem extraction. Only its nested pixel loop is replaced.
This prototype is explicitly scoped to the recorded NumPy 2.3.5 environment:
Python-float versus float32 comparison promotion is part of the target behavior.
No cross-query cache, altered geometry, approximate masks, or model is involved.
Original attribution: vendor/provenance.json and vendor/VMEM_LICENSE.
"""
import ast
import copy
import hashlib
import inspect
from pathlib import Path
import textwrap

import numpy as np
if __package__:
    from . import vmem_retrieval_kernel as original
else:
    import vmem_retrieval_kernel as original

BASELINE_SHA256 = '35825a3989f368906cba08808616f0c6922ff08d0a92c7205fddb4822652e2b3'
SUPPORTED_NUMPY = '2.3.5'


def raster_patch(polygon, min_x, max_x, min_y, max_y, avg_depth, idx,
                 cos_value, z_buffer, surfel_index_map, cos_buffer):
    """Batch integer pixels while preserving each edge's arithmetic expression.

    The original short-circuit tests the y straddle before the x intersection.
    We only calculate intersections for those straddling edge/row pairs. XOR
    accumulates the same booleans; repeated rows must use unbuffered xor.at.
    A float64 cast of z_buffer or avg_depth would change the original NumPy 2
    weak-scalar comparison. Retain Python float < float32, then float32 writes.
    """
    if max_x < min_x or max_y < min_y:
        return
    rows = np.arange(min_y, max_y + 1, dtype=np.float64)
    columns = np.arange(min_x, max_x + 1, dtype=np.float64)
    previous = np.roll(polygon, 1, axis=0)
    crosses_y = ((polygon[:, 1, None] > rows[None, :]) !=
                 (previous[:, 1, None] > rows[None, :]))
    edge, row = np.nonzero(crosses_y)
    inside = np.zeros((len(rows), len(columns)), dtype=bool)
    if len(edge):
        # Operation sequence and epsilon match point_in_polygon_2d exactly.
        intersection = ((previous[edge, 0] - polygon[edge, 0]) *
                        (rows[row] - polygon[edge, 1]) /
                        (previous[edge, 1] - polygon[edge, 1] + 1e-15) +
                        polygon[edge, 0])
        crosses_x = columns[None, :] < intersection[:, None]
        np.logical_xor.at(inside, row, crosses_x)
    target_depth = z_buffer[min_y:max_y+1, min_x:max_x+1]
    update = inside & (avg_depth < target_depth)
    target_depth[update] = avg_depth
    surfel_index_map[min_y:max_y+1, min_x:max_x+1][update] = idx
    cos_buffer[min_y:max_y+1, min_x:max_x+1][update] = cos_value


def renderer_function():
    """Return an unbound original-signature function; caller may add an observer."""
    if np.__version__ != SUPPORTED_NUMPY:
        raise RuntimeError('S10 prototype requires the scoped NumPy '+SUPPORTED_NUMPY+' environment')
    path = Path(original.__file__).resolve()
    if hashlib.sha256(path.read_bytes()).hexdigest() != BASELINE_SHA256:
        raise RuntimeError('Original VMem extraction changed; re-evaluate separately')
    source = textwrap.dedent(inspect.getsource(original.RetrievalKernel.render_surfels_to_image))
    tree = ast.parse(source)
    reference = copy.deepcopy(tree)
    expected_loop = ast.parse('''for py_ in range(min_y, max_y + 1):
    for px_ in range(min_x, max_x + 1):
        if point_in_polygon_2d(px_, py_, valid_points):
            if avg_depth < z_buffer[py_, px_]:
                z_buffer[py_, px_] = avg_depth
                surfel_index_map[py_, px_] = idx
                cos_buffer[py_, px_] = cos_value
''').body[0]
    original_dump = ast.dump(expected_loop, include_attributes=False)
    replacement = ast.parse('''_s10_raster_patch(valid_points, min_x, max_x, min_y, max_y,
    avg_depth, idx, cos_value, z_buffer, surfel_index_map, cos_buffer)''').body[0]
    changes = []

    class Replace(ast.NodeTransformer):
        def visit_For(self, node):
            if ast.dump(node, include_attributes=False) == original_dump:
                changes.append(node)
                return copy.deepcopy(replacement)
            return self.generic_visit(node)

    tree = Replace().visit(tree)
    if len(changes) != 1:
        raise RuntimeError('Expected exactly the original nested pixel loop')
    restored = copy.deepcopy(tree)
    replacement_dump = ast.dump(replacement, include_attributes=False)

    class Restore(ast.NodeTransformer):
        def visit_Expr(self, node):
            if ast.dump(node, include_attributes=False) == replacement_dump:
                return copy.deepcopy(changes[0])
            return self.generic_visit(node)

    restored = Restore().visit(restored)
    if ast.dump(restored, include_attributes=False) != ast.dump(reference, include_attributes=False):
        raise RuntimeError('Unexpected modification outside the pixel loop')
    ast.fix_missing_locations(tree)
    namespace = dict(vars(original), _s10_raster_patch=raster_patch)
    exec(compile(tree, '<S10 raster-loop-only transformation>', 'exec'), namespace)
    function = namespace['render_surfels_to_image']
    function.s10_transformation = {
        'original_source_sha256': BASELINE_SHA256,
        'helper_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'numpy': np.__version__, 'replaced_nested_pixel_loops': 1,
        'restored_full_method_ast_identical': True,
        'original_method': source, 'transformed_method': ast.unparse(tree)+'\n',
        'scope': 'Same finite valid inputs in pinned environment; finite regression tests are not a formal all-input proof.'}
    return function
