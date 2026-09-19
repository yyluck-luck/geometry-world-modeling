"""Finite source/metadata and fake installation check; no scientific payload or renderer."""
import ast
from copy import deepcopy
from functools import wraps
import hashlib
import inspect
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType

HERE = Path(__file__).resolve().parent


def load(name, filename):
    path = HERE / filename
    module = ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module


class FakePipeline:
    def render_surfels_to_image(self, *args, **kwargs):
        self.called.append((args, kwargs))
        return self.maps


def main():
    gate = load('generation_gate', 'generation_gate.py')
    runtime = load('_s64_runtime_author_check', 'runtime_adapter.py')
    launcher = load('_s64_launcher_author_check', 'launch_generation.py')
    hook = gate.execute_verified_module('_s64_hook_author_check', gate.UNIT_HOOK, gate.sha(gate.UNIT_HOOK))
    identities = gate.required_sources()
    assert identities[str(gate.UNIT_ADAPTER)] == gate.UNIT_ADAPTER_SHA256
    assert identities[str(gate.UNIT_HOOK)] == gate.sha(gate.UNIT_HOOK)
    assert len(identities) == 221
    variant = gate.exact_retrieval_variant()
    assert gate.RUN_ROW == 'C2_UNIT_REPAIRED_S64'
    assert gate.exact_derivation_policy()['allowed_scientific_differences']['retrieval_variant'] == variant
    assert gate.C2_OUTPUT.name == 'S64_unit_repaired_generation'
    gate.require_single_seed_config_derivation(gate.read_base_s40())
    factory_proof = runtime.derive_factory(compile_only=True)
    launcher_proof = launcher.derive_launcher(compile_only=True)
    production = ['generation_gate.py', 'runtime_adapter.py', 'launch_generation.py',
                  'freeze_c2_manifest.py', 'create_launch_authorization.py', 'unit_renderer_hook.py']
    for filename in production:
        compile(ast.parse((HERE/filename).read_bytes()), filename, 'exec')
    assert not any(name in sys.modules for name in ('numpy', 'torch', 'diffusers', 'PIL', 'modeling.pipeline'))

    pipeline, other = FakePipeline(), FakePipeline()
    pipeline.called, pipeline.maps = [], {'depth': 'fake', 'surfel_index_map': 'fake', 'cos_value_map': 'fake'}
    original_class_method = FakePipeline.render_surfels_to_image
    original = pipeline.render_surfels_to_image
    events, receipts = [], []
    bindings = dict(hook=variant['hook'], adapter=variant['adapter'],
                    original_renderer={'path': str(Path(__file__).resolve()), 'sha256': 'local_fake_only'})

    def fake_adapter(renderer, *args, **kwargs):
        events.append('adapter')
        assert renderer.__self__ is pipeline and renderer.__func__ is original.__func__
        maps = renderer(*args, **kwargs)
        return maps, {'renderer_calls': 1, 'length_unit_rule': variant['length_unit_rule'],
                      'depth_unit': variant['depth_unit'], 'normalized_fields': variant['scaled_fields'],
                      'length_unit_in_input_coordinates': 2.0, 'scale_factor': 0.5}

    def save(sequence, record):
        receipts.append((sequence, deepcopy(record)))

    installation = hook.install_unit_renderer(pipeline, fake_adapter, save, variant, bindings)
    installed = pipeline.render_surfels_to_image
    assert inspect.unwrap(installed).__func__ is original.__func__
    assert FakePipeline.render_surfels_to_image is original_class_method
    assert other.render_surfels_to_image.__func__ is original_class_method

    @wraps(installed)
    def later_observer(*args, **kwargs):
        events.append('observer_input')
        result = installed(*args, **kwargs)
        events.append('observer_output')
        return result

    pipeline.render_surfels_to_image = later_observer
    returned = pipeline.render_surfels_to_image('surfels', 'pose', 'focal', image_width=512)
    assert returned is pipeline.maps
    assert pipeline.called == [(('surfels', 'pose', 'focal'), {'image_width': 512})]
    assert events == ['observer_input', 'adapter', 'observer_output']
    assert len(receipts) == 1 and receipts[0][0] == 1
    assert receipts[0][1]['status'] == 'RENDERED_IN_CANONICAL_UNITS'

    # Exercise only the actual terminal-binding helper on this fake local receipt.
    manifest = dict(row=gate.RUN_ROW, retrieval_variant=variant, source_identities=identities,
                    output_root='set_below')
    with tempfile.TemporaryDirectory(prefix='s64_installation_only_') as temporary:
        canonical_temporary = Path(temporary).resolve()
        manifest['output_root'] = str(canonical_temporary)
        output = launcher.HeldDirectory.open(canonical_temporary)
        try:
            empty = launcher.collect_unit_receipts(output, manifest, 'a'*64)
            assert empty['complete'] is False and empty['calls'] == []
            record = receipts[0][1]
            record.update(row=gate.RUN_ROW, manifest_sha256='a'*64)
            original_path = str(gate.ROOT/'work/S20_environment/isolated_vmem_source/modeling/pipeline.py')
            record['source_bindings']['original_renderer'] = {'path': original_path, 'sha256': identities[original_path]}
            digest = launcher.write_new_json_at(output.fd, 'retrieval_unit_call_0001.json', record)
            bound = launcher.collect_unit_receipts(output, manifest, 'a'*64)
            assert bound['complete'] is True and bound['calls'][0]['sha256'] == digest
            assert bound == launcher.collect_unit_receipts(output, manifest, 'a'*64)
        finally:
            output.close()
    result = dict(status='PASS_LOCAL_SOURCE_INSTALLATION_CHECK_ONLY', source_count=len(identities),
                  retrieval_variant=variant, installation=installation,
                  factory_derivation=factory_proof, launcher_derivation=launcher_proof,
                  fake_adapter_calls=1, actual_renderer_calls=0, model_loads=0, image_reads=0,
                  scientific_payload_reads=0, formal_prepare_attach_authorization_launch_calls=0,
                  actual_unit_component_retested=False)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
