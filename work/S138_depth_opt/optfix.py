"""S138: make VMem's CUT3R global alignment actually optimise depth.

VMem's fork re-stacks im_depthmaps with ParameterStack(is_param=False), which detaches them, so they never get gradients.
This keeps the graph: preset (requires_grad=False) depths stay constant; the others are optimised.
"""
import torch


def install():
    from cloud_opt.dust3r_opt import optimizer as OPT

    def get_depthmaps(self, raw=False):
        res = torch.stack(list(self.im_depthmaps)).float().exp()
        if not raw:
            res = [dm[: h * w].view(h, w) for dm, (h, w) in zip(res, self.imshapes)]
        return res

    OPT.PointCloudOptimizer.get_depthmaps = get_depthmaps
    return get_depthmaps
