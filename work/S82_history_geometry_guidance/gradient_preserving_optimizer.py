"""Local S82 depth-access adapter; the original VMem fork is unchanged.

This fixes only homogeneous 2-D ParameterList depth access. It does not preset
cameras/K, initialize a scene, change the loss, or run any optimization.
"""


def with_gradient_preserving_depths(base_class):
    """Return a local subclass; accepts the real class or a tiny test double."""
    class GradientPreservingPointCloudOptimizer(base_class):
        def get_depthmaps(self, raw=False):
            import torch

            depths = list(self.im_depthmaps)
            if not depths or len(depths) != len(self.imshapes):
                raise ValueError("depth count must match nonempty imshapes")
            shape = tuple(depths[0].shape)
            if len(shape) != 2 or any(tuple(p.shape) != shape for p in depths):
                raise ValueError("S82 adapter requires equal-sized 2-D depth maps")
            if any(tuple(hw) != shape for hw in self.imshapes):
                raise ValueError("stored depth shape must equal each declared image shape")
            if any(p.dtype != depths[0].dtype or p.device != depths[0].device for p in depths):
                raise ValueError("depth dtype/device must match")
            # Unlike ParameterStack(...), this retains the path to registered
            # ParameterList leaves; no detach and no new nn.Parameter.
            res = torch.stack(depths, dim=0).exp()
            if not raw:
                res = [dm[:h * w].view(h, w) for dm, (h, w) in zip(res, self.imshapes)]
            return res

    return GradientPreservingPointCloudOptimizer
