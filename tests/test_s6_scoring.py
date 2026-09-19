import sys
from pathlib import Path
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from run_s6_memory import measured_support,project_depth


class S6ScoringTest(unittest.TestCase):
    def setUp(self):
        self.k=(100.,100.,111.5,111.5)
        self.depth=[np.ones((224,224)) for _ in range(24)]
        self.mask=[np.ones((224,224),bool) for _ in range(24)]
        self.poses=[np.eye(4) for _ in range(24)]

    def test_same_measured_plane_supported_by_all_history(self):
        support,valid,target=measured_support(self.depth,self.mask,self.poses,20,self.k)
        self.assertEqual(support.shape,(20,112,112))
        self.assertTrue(support.all());self.assertTrue(valid.all())
        np.testing.assert_array_equal(target,np.ones((112,112)))

    def test_occlusion_and_missing_history_measurement_are_not_support(self):
        self.depth[0][:]=.5
        self.depth[1][:]=1.5
        self.mask[2][:]=False
        support,_,_=measured_support(self.depth,self.mask,self.poses,20,self.k)
        self.assertFalse(support[:3].any());self.assertTrue(support[3:].all())

    def test_target_mask_applies_to_all_support(self):
        self.mask[20][:112,:112]=False
        support,valid,_=measured_support(self.depth,self.mask,self.poses,20,self.k)
        self.assertFalse(support[:,:56,:56].any())
        self.assertEqual(int(valid.sum()),112*112-56*56)

    def test_point_zbuffer_uses_nearer_positive_surface(self):
        # Both front-facing points lie on the central ray; one behind is rejected.
        k=(100.,100.,112.,112.)
        out=project_depth(np.array([[0,0,2.],[0,0,1.],[0,0,-1.]]),np.eye(4),k)
        self.assertEqual(out[56,56],1.)
        self.assertEqual(np.isfinite(out).sum(),1)


if __name__=='__main__':unittest.main()
