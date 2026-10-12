import tempfile
import unittest
import torch
from p2_intervention import P2Denoiser, capture_initial_noise


class Original:
    def sigma_to_idx(self, s): return torch.zeros_like(s, dtype=torch.long)
    def idx_to_sigma(self, i): return torch.full_like(i, 2, dtype=torch.float32)
    def __call__(self, network, x, s, cond, **kwargs): return x


class InterventionTests(unittest.TestCase):
    def setUp(self):
        self.x = torch.arange(16*4*2*2).float().reshape(16,4,2,2)
        self.context = torch.arange(64).float().reshape(4,4,2,2) / 100
        self.eps = torch.full((8,4,2,2), 0.7)
        self.cond = {'replace': torch.zeros(16,5,2,2)}
        self.cond['replace'][8:12,-1] = 1
    def run_arm(self, arm):
        d = P2Denoiser(Original(), self.context, arm, '/unused')
        d.capture(self.eps)
        before = self.x.clone(); rng = torch.get_rng_state().clone()
        result = d(None, self.x, torch.full((16,),2.1), self.cond)
        self.assertTrue(torch.equal(self.x,before))
        self.assertTrue(torch.equal(torch.get_rng_state(),rng))
        self.assertTrue(torch.equal(result[4:], self.x[4:]))
        return result
    def test_native_identity(self):
        self.assertIs(self.run_arm('native'),self.x)
    def test_real_quantized_not_raw_sigma(self):
        self.assertTrue(torch.equal(self.run_arm('real')[:4], self.context+1.4))
    def test_zero_control(self):
        self.assertTrue(torch.equal(self.run_arm('zero')[:4],torch.full_like(self.context,1.4)))
    def test_permutation_moves_only_source_not_noise(self):
        self.eps = torch.arange(128).float().reshape(8,4,2,2)/10
        self.assertTrue(torch.equal(self.run_arm('permuted')[:4],self.context.roll(1,0)+2*self.eps[:4]))
    def test_capture_precedes_inplace_scaling(self):
        class Sampler:
            def prepare_sampling_loop(self,x): x.mul_(3); return x
        d=P2Denoiser(Original(),self.context,'native','/unused')
        s=capture_initial_noise(Sampler(),d); initial=self.eps.clone();s.prepare_sampling_loop(initial)
        self.assertTrue(torch.equal(d.eps,self.eps[:4]))

if __name__ == '__main__': unittest.main()
