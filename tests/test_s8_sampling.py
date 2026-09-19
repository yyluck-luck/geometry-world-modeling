import sys
import tempfile
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'src')]
from prepare_s8_inputs import gt_time_intervals, plan_windows
from tum_rgbd import TimestampEntry, RGBDMatch


def pairs(n, offset=0.):
    return [RGBDMatch(TimestampEntry(i/30, f'rgb/{i}.png'),
                      TimestampEntry(i/30+offset, f'depth/{i}.png')) for i in range(n)]


class SamplingTests(unittest.TestCase):
    def test_fixed_duration_disjoint_all_test_candidates(self):
        plan=plan_windows(pairs(1801), [[0.,60.]])
        windows=plan['accepted_windows']
        self.assertGreaterEqual(len(windows),3)
        self.assertEqual(plan['selected_window_indices'],[0,(len(windows)-1)//2,len(windows)-1])
        all_ids=[]
        for w in windows:
            self.assertAlmostEqual(w['nominal_end']-w['nominal_start'],8.840)
            self.assertEqual(len(set(w['match_indices'])),24)
            self.assertLessEqual(max(w['snap_errors_seconds']),.05)
            all_ids+=w['match_indices']
        self.assertEqual(len(all_ids),len(set(all_ids)))

    def test_gt_gaps_and_both_sensor_times(self):
        plan=plan_windows(pairs(1201,offset=.01),[[0.,9.],[20.,29.],[31.,40.]])
        self.assertEqual(len(plan['accepted_windows']),3)
        self.assertEqual(len(plan['selected_window_indices']),3)
        self.assertTrue(plan['excluded_pairs'])
        for w in plan['accepted_windows']:
            a,b=[[0.,9.],[20.,29.],[31.,40.]][w['gt_interval']]
            self.assertTrue(all(a<=t<=b and a<=t+.01<=b for t in w['rgb_timestamps']))

    def test_short_metadata_does_not_expand_window_or_sample_count(self):
        plan=plan_windows(pairs(500),[[0.,20.]])
        self.assertFalse(plan['selected_window_indices'])
        self.assertEqual(len(plan['accepted_windows']),1)

    def test_gt_time_reader_does_not_parse_pose_values(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'groundtruth.txt'
            p.write_text('0 ignored pose values are intentionally not parsed\n0.05 ignored pose values are intentionally not parsed\n1 ignored pose values are intentionally not parsed\n')
            times,intervals=gt_time_intervals(p)
            self.assertEqual(times,[0.,.05,1.])
            self.assertEqual(intervals,[[0.,.05],[1.,1.]])
            p.write_text('0 x x x x x x x\n0 x x x x x x x\n')
            with self.assertRaises(ValueError): gt_time_intervals(p)


if __name__=='__main__': unittest.main()
