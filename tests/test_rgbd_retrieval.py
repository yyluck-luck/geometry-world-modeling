from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from rgbd_retrieval import initial_nms_threshold, optical_to_vmem, make_selector, select
from retrieval_diagnostic import build_fixture, warm_threshold
from rgbd_memory import Memory
from vmem_memory_kernel import Surfel

class TestRealRetrieval(unittest.TestCase):
    def test_nms_threshold_equals_official_five_frame_path(self):
        cfg=dict(base_width=192,base_height=128,base_effective_focal=160,
                 context_num_frames=4,translation_distance_weight=.1)
        fixture=build_fixture('shared_history_8',3,1,cfg)
        optical=[optical_to_vmem(p) for p in fixture['poses']]
        self.assertAlmostEqual(initial_nms_threshold(optical),warm_threshold(fixture,cfg),places=12)

    def test_optical_roundtrip_and_context_indices(self):
        poses=[]
        for i in range(20):
            p=np.eye(4);p[0,3]=i*.004;p[1,3]=i*.001
            poses.append(p)
        m=Memory()
        for x in np.linspace(-.6,.6,5):
            for y in np.linspace(-.4,.4,4):
                m.surfels.append(Surfel(np.array([x,y,2.]),np.array([0.,0.,1.]),.04))
        m.mapping={i:list(range(20)) for i in range(len(m.surfels))}
        obj=make_selector(m,poses)
        np.testing.assert_array_equal(obj.get_transformed_c2ws(),np.asarray(poses))
        out=select(obj,poses[-1])
        self.assertEqual(len(set(out['selected'])),4)
        self.assertTrue(all(0<=i<20 for i in out['selected']))

if __name__=='__main__': unittest.main()
