"""Numerical and leakage-related fixtures, independent optimizer reference."""
import unittest
import numpy as np
from scipy.optimize import lsq_linear
import pilot


class PilotChecks(unittest.TestCase):
    def test_box_solver_against_independent_optimizer(self):
        rng = np.random.default_rng(811)
        for dimension in (1, 2, 3, 6):
            for repeat in range(4):
                x = rng.normal(size=(80, dimension))
                y = x @ rng.uniform(-1, 2, dimension) + rng.normal(size=80)
                a = pilot.box_solve(x.T @ x / 80, x.T @ y / 80)
                ref = lsq_linear(x, y, bounds=(0, 1), tol=1e-12)
                self.assertLess(abs(np.mean((x @ a-y)**2) - np.mean((x @ ref.x-y)**2)), 1e-9)

    def test_rank_deficiency_and_zero(self):
        for x in (np.zeros((20, 3)), np.ones((20, 3))):
            y = np.ones(20)*0.4
            a = pilot.box_solve(x.T@x/20, x.T@y/20)
            self.assertTrue(np.all((a >= 0) & (a <= 1)))
            self.assertLessEqual(np.mean((x@a-y)**2), 0.16000001)

    def test_region_cross_terms_and_weighting(self):
        rng = np.random.default_rng(12)
        phi = rng.normal(size=(3, 4, 9, 11, 3))
        mask = rng.random((4, 9, 11)) > .3
        y = rng.normal(size=(4, 9, 11, 3))
        q, b = pilot.accumulate(phi, mask, y)
        full = np.concatenate([phi*mask[None, ..., None], phi*(~mask)[None, ..., None]]).reshape(6, -1).T
        np.testing.assert_allclose(q, full.T@full/y.size, atol=1e-13)
        np.testing.assert_allclose(b, full.T@y.flatten()/y.size, atol=1e-13)
        for n in ('constant', 'region', 'bands', 'candidate'):
            t = pilot.mapping(n)
            xx = full @ t
            np.testing.assert_allclose(t.T@q@t, xx.T@xx/y.size, atol=1e-13)

    def test_frequency_reconstruction_no_time_mixing(self):
        rng = np.random.default_rng(6)
        w = rng.random((4, 16, 20, 3)); g = rng.random(w.shape)
        p = pilot.features(w, g)
        np.testing.assert_allclose(p.sum(axis=0), g-w, atol=1e-15)
        reversed_p = pilot.features(w[::-1], g[::-1])
        np.testing.assert_array_equal(reversed_p, p[:, ::-1])


if __name__ == '__main__':
    unittest.main()
