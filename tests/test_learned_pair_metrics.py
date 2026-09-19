import sys
from pathlib import Path
import unittest
import tempfile
import subprocess
import json
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from learned_pair_metrics import crop_geometry, measured_target, first_frame_scale, depth_metrics, relative_pose_metrics


class PairMetricsTests(unittest.TestCase):
    def test_tum_crop_and_missing_measurements(self):
        self.assertEqual(crop_geometry(640,480), {'original':[640,480], 'resized':[299,224], 'crop':[37,0,261,224]})
        d=np.ones((480,640));d[200:280,300:340]=0
        target, mask, _ = measured_target(d)
        self.assertEqual(target.shape,(224,224))
        self.assertFalse(mask[112,112])
        self.assertTrue(mask[30,30])
        self.assertTrue(np.all(target[mask]==1))

    def test_calibration_is_frozen_for_second_frame(self):
        pred0=np.ones((20,20)); mask=np.ones_like(pred0,dtype=bool)
        scale,n=first_frame_scale(pred0,pred0*2,mask)
        self.assertEqual((scale,n),(2,400))
        result=depth_metrics(pred0*3,pred0*7,mask,scale)
        self.assertAlmostEqual(result['mae_mm'],1000)
        self.assertAlmostEqual(result['signed_mean_mm'],-1000)

    def test_no_broadcast_or_tiny_calibration(self):
        x=np.ones((20,20)); mask=x.astype(bool)
        with self.assertRaises(ValueError):depth_metrics(x[0],x,mask,1)
        with self.assertRaises(ValueError):first_frame_scale(x[:2],x[:2],mask[:2])

    def test_relative_pose_removes_world_gauge(self):
        p0=np.eye(4); p0[:3,3]=[4,5,6]
        p1=p0.copy();p1[0,3]+=1
        g0=np.eye(4);g1=np.eye(4);g1[0,3]=2
        result=relative_pose_metrics(p0,p1,g0,g1,2)
        self.assertAlmostEqual(result['rotation_error_deg'],0)
        self.assertAlmostEqual(result['translation_vector_error_mm'],0)
        self.assertAlmostEqual(result['ground_truth_translation_mm'],2000)

    def test_precondition_failure_is_recorded_and_never_overwritten(self):
        script=Path(__file__).resolve().parents[1]/'scripts/evaluate_cut3r_pair.py'
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'failed'
            command=[sys.executable,str(script),'--cpu',str(Path(tmp)/'missing_cpu'),'--output',str(output)]
            first=subprocess.run(command,capture_output=True)
            self.assertNotEqual(first.returncode,0)
            raw=(output/'failure.json').read_bytes()
            self.assertEqual(json.loads(raw)['status'],'failed')
            second=subprocess.run(command,capture_output=True)
            self.assertNotEqual(second.returncode,0)
            self.assertEqual(raw,(output/'failure.json').read_bytes())


if __name__=='__main__':unittest.main()
