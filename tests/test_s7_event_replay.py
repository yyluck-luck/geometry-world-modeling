"""Small artificial correctness fixtures, not real-data experiment samples."""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from s7_event_replay import record_path, replay, decision_trace
from s6_memory_bridge import memory_digest
from vmem_memory_kernel import Surfel
from rgbd_retrieval import make_selector


def obs(x):
    return Surfel(np.array([x, 0., 3.]), np.array([0., 0., 1.]), .5, np.array([1., 0., 0.]))


class TestS7Replay(unittest.TestCase):
    def test_same_frame_newborns_do_not_merge(self):
        frames = [[obs(0.), obs(.01)], [obs(.02)]]
        m, events = record_path(frames, 'first_write')
        self.assertEqual(events[0]['targets'], [0, 1])
        self.assertEqual(events[0]['matches'], [-1, -1])
        self.assertEqual(events[1]['targets'], [0])
        self.assertEqual(len(m.surfels), 2)

    def test_frame_centroid_counts_once_and_replay_does_not_match(self):
        frames = [[obs(0.)], [obs(.1), obs(.2), obs(.3)], [obs(.4)]]
        recorded, events = record_path(frames, 'frame_mean')
        with patch('rgbd_memory.Memory.add', side_effect=AssertionError('Replayed a match search')):
            mean = replay(frames, events, 'frame_mean')
            first = replay(frames, events, 'first_write')
        self.assertEqual(memory_digest(mean), memory_digest(recorded))
        self.assertAlmostEqual(mean.points[0, 0], .2)
        self.assertEqual(mean.counts, [3])
        self.assertEqual(mean.mapping, {0: [0, 1, 2]})
        self.assertEqual(first.mapping, mean.mapping)
        self.assertEqual(first.points[0, 0], 0.)

    def test_invalid_event_cannot_match_newborn(self):
        frames = [[obs(0.)]]
        events = [dict(frame=0, old_n=0, targets=[0], matches=[0], new_n=1)]
        with self.assertRaises(ValueError):
            replay(frames, events, 'first_write')

    def test_no_nms_has_no_forced_last_and_deduplicates_after_sort(self):
        m, _ = record_path([[obs(0.)]], 'first_write')
        poses = [np.eye(4) for _ in range(20)]
        for i, p in enumerate(poses): p[0, 3] = i*.1
        k = make_selector(m, poses, threshold=.025)
        counts = [[0, 3], [1, 1], [2, 1], [3, 1], [19, 1]]
        out = decision_trace(k, poses[0], counts, nms=False)
        self.assertEqual(out['selected'], [0, 1, 2, 3])
        self.assertEqual(out['expanded_candidates'].count(0), 3)
        self.assertNotIn(19, out['selected'])

    def test_insufficient_unique_candidates_is_reported(self):
        m, _ = record_path([[obs(0.)]], 'first_write')
        k = make_selector(m, [np.eye(4)]*20, threshold=.025)
        with self.assertRaises(ValueError):
            decision_trace(k, np.eye(4), [[0, 4]], False)


if __name__ == '__main__': unittest.main()
