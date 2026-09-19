"""Instance-only renderer unit adapter; original observers are installed later."""
from copy import deepcopy
from datetime import datetime, timezone
from functools import wraps
import inspect
from pathlib import Path


def install_unit_renderer(pipeline, adapter, write_receipt, retrieval_variant, source_bindings):
    original = pipeline.render_surfels_to_image
    raw = inspect.unwrap(original)
    if getattr(original, '__self__', None) is not pipeline:
        raise RuntimeError('Expected the original renderer bound to this pipeline instance')
    if str(Path(inspect.getsourcefile(raw)).resolve()) != source_bindings['original_renderer']['path']:
        raise RuntimeError('Renderer source differs from the verified original binding')
    if getattr(original, '_s64_unit_hook', False):
        raise RuntimeError('Unit hook already installed')
    variant, bindings = deepcopy(retrieval_variant), deepcopy(source_bindings)
    sequence = 0

    @wraps(original)
    def renderer(*args, **kwargs):
        nonlocal sequence
        sequence += 1
        record = dict(schema='s64-renderer-unit-call-v1', sequence=sequence,
                      started_utc=datetime.now(timezone.utc).isoformat(),
                      retrieval_variant=deepcopy(variant), source_bindings=deepcopy(bindings),
                      observation_semantics='input_original_coordinates_output_canonical_depth')
        try:
            maps, unit = adapter(original, *args, **kwargs)
        except BaseException as error:
            record.update(status='FAILED_UNIT_RENDERER_CALL', error_type=type(error).__name__,
                          error=str(error), completed_utc=datetime.now(timezone.utc).isoformat())
            write_receipt(sequence, record)
            raise
        record.update(status='RENDERED_IN_CANONICAL_UNITS', unit_receipt=unit,
                      completed_utc=datetime.now(timezone.utc).isoformat())
        write_receipt(sequence, record)
        return maps

    renderer._s64_unit_hook = True
    pipeline.render_surfels_to_image = renderer
    return dict(installed=True, scope='pipeline_instance_only', retrieval_variant=variant,
                source_bindings=bindings, installation_stage='runtime_return_before_original_observers',
                observer_order=['original_input_archive', 'unit_hook', 'original_renderer',
                                'canonical_output_archive'],
                receipt_pattern='retrieval_unit_call_%04d.json', expected_calls_on_two_batch_completion=1,
                inspect_unwrap_proves_original_source_only=True)
