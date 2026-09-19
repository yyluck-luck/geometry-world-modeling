"""Finite artificial numeric tests. No original renderer or saved data imports."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import pickle
import sys
import time
import unittest
import numpy as np
from unit_consistent_renderer import render_in_canonical_units, EmptyPositiveGeometryError

HERE = Path(__file__).resolve().parent
METRICS = {}


def fixture():
    y, p = np.deg2rad([17., -11.])
    Ry = np.array([[np.cos(y), 0., np.sin(y)], [0., 1., 0.], [-np.sin(y), 0., np.cos(y)]])
    Rx = np.array([[1., 0., 0.], [0., np.cos(p), -np.sin(p)], [0., np.sin(p), np.cos(p)]])
    pose = np.eye(4); pose[:3, :3] = Ry @ Rx; pose[:3, 3] = [2., -3., 4.]
    camera_points = np.array([[-.3, .4, 2.], [.5, -.2, 4.], [1., .2, 6.],
                              [-.5, -.4, 8.], [0., 0., -2.]])
    world = camera_points @ pose[:3, :3].T + pose[:3, 3]
    surfels = [SimpleNamespace(position=x.copy(), normal=pose[:3, 2].copy(),
                              radius=.05*(i+1), source_ids=[27-i, i % 2],
                              metadata={'unchanged': [i]}) for i,x in enumerate(world)]
    return surfels, pose, np.array([430., 510.]), dict(principal_points=np.array([123., 97.]),
                                                      image_width=256, image_height=192)


def projection(points, pose, focal, principal):
    camera = np.linalg.solve(pose[:3, :3], (points-pose[:3, 3]).T).T
    return camera[:, :2]/camera[:, 2:] * focal + principal


class NumericSpy:
    """Sample-index maps only; deliberately does not rasterize polygons."""
    def __init__(self):
        self.calls = []

    def __call__(self, surfels, pose, focal, **kwargs):
        self.calls.append((surfels, pose, focal, kwargs))
        z = np.linalg.solve(pose[:3, :3],
                            (np.array([s.position for s in surfels])-pose[:3, 3]).T)[2]
        self.maps = dict(depth=z[None, :],
                         surfel_index_map=np.arange(len(surfels), dtype=np.int32)[None, :],
                         cos_value_map=np.ones((1, len(surfels))))
        return self.maps


class FiniteTests(unittest.TestCase):
    def test_shared_positive_length_scales_and_radius_projection(self):
        base, camera, focal, kwargs = fixture()
        comparisons = []; reference = None
        for factor in (1e-9, 1., 1e9):
            surfels, pose = deepcopy(base), camera.copy()
            pose[:3, 3] *= factor
            for s in surfels:
                s.position *= factor; s.radius *= factor
            original = pickle.dumps((surfels, pose, focal, kwargs))
            spy = NumericSpy()
            maps, receipt = render_in_canonical_units(spy, surfels, pose, focal, **kwargs)
            self.assertEqual(len(spy.calls), 1); self.assertIs(maps, spy.maps)
            self.assertEqual(pickle.dumps((surfels, pose, focal, kwargs)), original)
            normalized, ncamera, nfocal, nkw = spy.calls[0]
            self.assertEqual(receipt['positive_depth_count'], 4)
            self.assertEqual(receipt['nonpositive_depth_count'], 1)
            self.assertAlmostEqual(receipt['length_unit_in_input_coordinates']/factor, 5., places=12)
            self.assertIn('dimensionless', receipt['depth_unit'])
            np.testing.assert_array_equal(ncamera[:3, :3], pose[:3, :3])
            np.testing.assert_array_equal(nfocal, focal)
            for original_s, copied_s in zip(surfels, normalized):
                np.testing.assert_array_equal(copied_s.normal, original_s.normal)
                self.assertEqual(copied_s.source_ids, original_s.source_ids)
                self.assertEqual(copied_s.metadata, original_s.metadata)
            # Two radius endpoints as well as each center, including off-axis views.
            points = np.array([s.position + sign*s.radius*camera[:3, 0]
                               for s in surfels for sign in (-1., 0., 1.)])
            normalized_points = np.array([s.position + sign*s.radius*camera[:3, 0]
                                          for s in normalized for sign in (-1., 0., 1.)])
            pixels = projection(points, pose, focal, kwargs['principal_points'])
            normalized_pixels = projection(normalized_points, ncamera, nfocal, nkw['principal_points'])
            np.testing.assert_allclose(pixels, normalized_pixels, rtol=1e-12, atol=1e-9)
            apparent_radii = np.linalg.norm(pixels[2::3]-pixels[1::3], axis=1)
            normalized_radii = np.linalg.norm(normalized_pixels[2::3]-normalized_pixels[1::3], axis=1)
            np.testing.assert_allclose(apparent_radii, normalized_radii, rtol=1e-12, atol=1e-9)
            numeric = (np.array([s.position for s in normalized]), ncamera,
                       np.array([s.radius for s in normalized]), maps['depth'])
            if reference is None:
                reference = numeric
            else:
                for actual, expected in zip(numeric, reference):
                    np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12)
            comparisons.append(dict(input_scale=factor,
                                    length_unit=receipt['length_unit_in_input_coordinates'],
                                    maximum_projection_error_px=float(np.max(np.abs(pixels-normalized_pixels))),
                                    maximum_apparent_radius_error_px=float(np.max(np.abs(apparent_radii-normalized_radii)))))
        METRICS['shared_scale_cases'] = comparisons

    def test_mutating_renderer_receives_only_copies(self):
        surfels, pose, focal, kwargs = fixture()
        surfels[0].normal[:] = 0.; surfels[0].radius = 0.
        before = pickle.dumps((surfels, pose, focal, kwargs)); calls = []
        maps = dict(depth=np.array([[1.]]), surfel_index_map=np.array([[4]]), cos_value_map=np.array([[.8]]))
        def mutate(ss, pp, ff, **kk):
            calls.append(1)
            ss[0].position[:] = 99.; ss[0].normal[:] = 7.; ss[0].source_ids.append(999)
            ss[0].metadata['unchanged'].append(8); pp[:] = 8.; ff[:] = 3.
            kk['principal_points'][:] = 9.
            return maps
        returned, receipt = render_in_canonical_units(mutate, surfels, pose, focal, **kwargs)
        self.assertIs(returned, maps); self.assertEqual(len(calls), 1)
        self.assertEqual(pickle.dumps((surfels, pose, focal, kwargs)), before)
        self.assertAlmostEqual(receipt['length_unit_in_input_coordinates'], 5., places=12)

    def test_invalid_numeric_inputs_never_call_renderer(self):
        def change_nan_position(s,p,f,k): s[0].position.__setitem__(0, np.nan)
        def change_negative_radius(s,p,f,k): setattr(s[0], 'radius', -1.)
        def change_inf_normal(s,p,f,k): s[0].normal.__setitem__(0, np.inf)
        def change_bad_rotation(s,p,f,k): p.__setitem__((0,0), 0.)
        def change_bad_focal(s,p,f,k): f.__setitem__(0, np.inf)
        def change_bad_size(s,p,f,k): k.__setitem__('image_width', 0)
        cases = [change_nan_position, change_negative_radius, change_inf_normal,
                 change_bad_rotation, change_bad_focal, change_bad_size]
        for change in cases:
            with self.subTest(change=change.__name__):
                s,p,f,k = fixture(); change(s,p,f,k); spy = NumericSpy()
                with self.assertRaises(ValueError):
                    render_in_canonical_units(spy,s,p,f,**k)
                self.assertEqual(len(spy.calls),0)
        METRICS['invalid_cases'] = [c.__name__ for c in cases]

    def test_empty_positive_geometry_is_explicit(self):
        s,p,f,k = fixture()
        for candidates in ([], s[-1:]):
            spy = NumericSpy()
            with self.assertRaises(EmptyPositiveGeometryError):
                render_in_canonical_units(spy,candidates,p,f,**k)
            self.assertEqual(len(spy.calls),0)

    def test_renderer_failure_propagates_once(self):
        s,p,f,k = fixture(); calls = []
        class RendererFailure(RuntimeError): pass
        def fail(*args, **kwargs):
            calls.append(1); raise RendererFailure('finite injected error')
        with self.assertRaisesRegex(RendererFailure, 'finite injected error'):
            render_in_canonical_units(fail,s,p,f,**k)
        self.assertEqual(len(calls),1)


if __name__ == '__main__':
    started = datetime.now(timezone.utc).isoformat(); timer = time.monotonic()
    paths = [HERE/'unit_consistent_renderer.py', Path(__file__), HERE/'PROTOCOL.md']
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(FiniteTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    assert before == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    receipt = dict(status='PASS_SYNTHETIC_NUMERIC_ONLY' if result.wasSuccessful() else 'FAIL_PRESERVED',
                   started_utc=started, completed_utc=datetime.now(timezone.utc).isoformat(),
                   elapsed_seconds=time.monotonic()-timer, python=sys.version, numpy=np.__version__,
                   source_sha256=before, tests_run=result.testsRun,
                   failure_count=len(result.failures), error_count=len(result.errors),
                   metrics=METRICS, original_renderer_calls=0, model_loads=0,
                   saved_S60_payload_reads=0, RGB_reads=0, production_integration=False)
    with (HERE/'FINITE_TEST_RECEIPT.json').open('x') as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps(receipt,indent=2)); sys.exit(0 if result.wasSuccessful() else 1)
