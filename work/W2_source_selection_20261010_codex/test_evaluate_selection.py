import unittest

import numpy as np
import evaluate_selection as e


def panel(selected=.9, c0=1., fusion=1.):
    return [{'window_id': f's{s}_w{w}', 'scene': f's{s}',
             'arms': {'primary': {'selected': selected, 'c0': c0, 'fusion': fusion}}}
            for s in range(4) for w in range(4)]


class EvaluationTests(unittest.TestCase):
    def test_uniform_improvement_passes(self):
        rows = panel()
        comparisons = {k: e.comparison(rows, k) for k in ['c0', 'fusion']}
        verdict, failures = e.decide(comparisons, 0)
        self.assertEqual(verdict, 'GO_TO_NEXT_SMALL_PILOT')
        self.assertEqual(failures, [])
        self.assertAlmostEqual(comparisons['c0']['top_two_share_of_net_gain'], .125)
        self.assertAlmostEqual(comparisons['c0']['leave_top_two']['relative_gain'], .1)

    def test_two_windows_cannot_carry_success(self):
        rows = panel(selected=1.)
        rows[0]['arms']['primary']['selected'] = .1
        rows[1]['arms']['primary']['selected'] = .1
        comparisons = {k: e.comparison(rows, k) for k in ['c0', 'fusion']}
        verdict, failures = e.decide(comparisons, 0)
        self.assertEqual(verdict, 'STOP_TESTED_SELECTOR')
        self.assertGreater(comparisons['c0']['relative_gain'], .05)
        self.assertEqual(comparisons['c0']['top_two_share_of_net_gain'], 1.)
        self.assertEqual(comparisons['c0']['leave_top_two']['relative_gain'], 0.)
        self.assertIn('c0:top_two_dominate_net_gain_or_nonpositive_net', failures)

    def test_fusion_must_be_beaten_too(self):
        rows = panel(fusion=.8)
        comparisons = {k: e.comparison(rows, k) for k in ['c0', 'fusion']}
        verdict, failures = e.decide(comparisons, 0)
        self.assertEqual(verdict, 'STOP_TESTED_SELECTOR')
        self.assertIn('fusion:aggregate_gain_below_5_percent', failures)

    def test_negative_total_has_no_fake_concentration_success(self):
        rows = panel(selected=1.1)
        result = e.comparison(rows, 'c0')
        self.assertIsNone(result['top_two_share_of_net_gain'])
        self.assertLess(result['relative_gain'], 0)

    def test_leave_two_preserves_equal_scene_weighting(self):
        rows = panel()
        for r in rows:
            if r['scene'] == 's0':
                r['arms']['primary']['c0'] = 2.
        result = e.comparison(rows, 'c0')
        self.assertEqual(result['leave_top_two']['excluded_window_ids'], ['s0_w0', 's0_w1'])
        self.assertAlmostEqual(result['leave_top_two']['comparator_error'], 1.25)
        self.assertAlmostEqual(result['leave_top_two']['selected_error'], .9)

    def test_fallbacks_count_against_coverage_gate(self):
        rows = panel()
        comparisons = {k: e.comparison(rows, k) for k in ['c0', 'fusion']}
        self.assertEqual(e.decide(comparisons, .25)[0], 'GO_TO_NEXT_SMALL_PILOT')
        self.assertIn('abstention_above_25_percent', e.decide(comparisons, 5/16)[1])

    def test_no_scene_may_be_hidden_by_overall_gain(self):
        rows = panel(selected=.7)
        for row in rows:
            if row['scene'] == 's3':
                row['arms']['primary']['selected'] = 1.05
        comparisons = {k: e.comparison(rows, k) for k in ['c0', 'fusion']}
        self.assertGreater(comparisons['c0']['relative_gain'], .05)
        self.assertIn('c0:nonpositive_gain_in_a_scene', e.decide(comparisons, 0)[1])


if __name__ == '__main__':
    unittest.main()
