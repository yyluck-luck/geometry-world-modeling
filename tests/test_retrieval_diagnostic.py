import ast
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from retrieval_diagnostic import build_fixture, warm_threshold, evaluate, camera, perturb, instantiate
import torch


def definitions(path):
    return {n.name:n for n in ast.walk(ast.parse(path.read_text())) if isinstance(n,ast.FunctionDef)}


class RetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=json.loads((ROOT/'configs/retrieval_sensitivity.json').read_text())

    def test_complete_official_path_ast(self):
        new=definitions(ROOT/'src/vmem_retrieval_kernel.py')
        original=definitions(ROOT/'vendor/vmem_snapshot/modeling/pipeline.py')
        for name in ['geodesic_distance','render_surfels_to_image','get_frame_distribution',
                     'process_retrieved_spatial_information','get_context_info','get_transformed_c2ws']:
            self.assertEqual(ast.dump(new[name]),ast.dump(original[name]))
        util=definitions(ROOT/'vendor/vmem_snapshot/utils/util.py')
        self.assertEqual(ast.dump(new['average_camera_pose']),ast.dump(util['average_camera_pose']))

    def test_shared_views_have_visibility_derived_common_provenance(self):
        f=build_fixture('shared_history_8',0,1,self.cfg)
        self.assertTrue(all(ids==list(range(8)) for ids in f['mapping'].values()))

    def test_patch_views_observe_their_own_region(self):
        f=build_fixture('patch_history_20',0,1,self.cfg)
        self.assertTrue(all(ids==[int(f['blocks'][i])] for i,ids in f['mapping'].items()))

    def test_zero_intervention_preserves_points(self):
        f=build_fixture('patch_history_20',0,1,self.cfg)
        np.testing.assert_array_equal(perturb(f,'translation_x',0,self.cfg),f['points'])

    def test_correct_camera_convention_produces_visible_memory(self):
        f=build_fixture('shared_history_8',0,1,self.cfg)
        result,render=evaluate(f,self.cfg,f['points'],camera(x=-.06,y=.013),warm_threshold(f,self.cfg))
        self.assertGreater(result['rendered_coverage'],0)
        self.assertEqual(len(result['selected']),4)
        self.assertTrue(np.allclose(render['depth'][render['depth']>0],4))

    def test_output_packaging_values_cannot_influence_selection(self):
        f=build_fixture('patch_history_20',1,1,self.cfg)
        threshold=warm_threshold(f,self.cfg)
        a,b=instantiate(f,self.cfg,threshold=threshold),instantiate(f,self.cfg,threshold=threshold)
        b.latents=[x+1000 for x in b.latents]
        b.encoder_embeddings=[x-2000 for x in b.encoder_embeddings]
        query=torch.tensor(np.array([camera()]),dtype=torch.float64)
        self.assertEqual(a.get_context_info(query)['context_time_indices'].tolist(),
                         b.get_context_info(query)['context_time_indices'].tolist())

    def test_resolutions_preserve_source_view_geometry(self):
        a=build_fixture('patch_history_20',2,1,self.cfg)
        b=build_fixture('patch_history_20',2,2,self.cfg)
        np.testing.assert_array_equal(a['points'],b['points'])
        self.assertEqual(a['mapping'],b['mapping'])
        self.assertEqual(2*a['source_focal'],b['source_focal'])
