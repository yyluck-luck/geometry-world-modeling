import contextlib
from copy import deepcopy
import io
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from rgbd_memory import Memory, make_surfels
from vmem_memory_kernel import Surfel, MemoryKernel


def surf(p,n=(0,0,1),r=.02):
    return Surfel(np.asarray(p,dtype=float),np.asarray(n,dtype=float),r)


class TestRealMemory(unittest.TestCase):
    def test_original_single_leaf_equivalence(self):
        rng=np.random.default_rng(513)
        batches=[[surf(p) for p in rng.normal(size=(35,3))*.04] for _ in range(4)]
        fast=Memory()
        old,mapping=[],{}
        for t,batch in enumerate(batches):
            fast.add(batch,t,position_threshold=.03)
            with contextlib.redirect_stdout(io.StringIO()):
                added,mapping=MemoryKernel().merge_surfels(deepcopy(batch),t,old,mapping,
                                  position_threshold=.03,normal_threshold=.6,max_points_per_node=100000)
            for obs in added:
                mapping[len(old)]=[t]
                old.append(obs)
            self.assertEqual(fast.mapping,mapping)
            np.testing.assert_array_equal(fast.points,np.array([s.position for s in old]))

    def test_first_compatible_is_not_nearest(self):
        m=Memory()
        m.add([surf([0,0,1]),surf([.019,0,1])],0)
        self.assertEqual(m.add([surf([.018,0,1])],1,.02),[0])

    def test_frame_weight_and_frozen_index(self):
        m=Memory('frame_mean')
        m.add([surf([0,0,1])],0)
        m.add([surf([0,0,1.02])]*10,1,.1)
        self.assertAlmostEqual(m.points[0,2],1.01)
        m.add([surf([0,0,1.04])],2,.1)
        self.assertAlmostEqual(m.points[0,2],1.02)
        self.assertEqual(m.counts,[3])
        self.assertEqual(m.mapping,{0:[0,1,2]})

    def test_normal_rejection(self):
        m=Memory()
        m.add([surf([0,0,1])],0)
        self.assertEqual(m.add([surf([0,0,1],(0,0,-1))],1),[-1])
        self.assertEqual(len(m.surfels),2)

    def test_surface_normals_and_controlled_bias(self):
        d=np.ones((32,48))*2
        rgb=np.zeros((32,48,3),dtype=np.uint8)
        pose=np.eye(4)
        a=make_surfels(d,rgb,pose,8,(50,50,23.5,15.5))
        b=make_surfels(d,rgb,pose,8,(50,50,23.5,15.5),initial_bias_m=.02)
        self.assertTrue(len(a)>0)
        for x,y in zip(a,b):
            np.testing.assert_allclose(x.normal,[0,0,1])
            np.testing.assert_allclose(y.position-x.position,[0,0,.02],atol=1e-12)
            self.assertEqual(x.radius,y.radius)


if __name__=='__main__':
    unittest.main()
