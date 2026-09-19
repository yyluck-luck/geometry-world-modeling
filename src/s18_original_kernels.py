"""S18 minimal original VMem methods, MIT, commit39291e4f272f6b4f270691d930926ab5930f942e.
Pointmap/normal bodies and resize/store statement slices are AST-equal to pinned pipeline.
No original pipeline import, model construction, renderer rewrite or tree repair.
"""
import numpy as np
import torch
import torch.nn.functional as F
from src.vmem_memory_kernel import MemoryKernel, Surfel
from src.vmem_retrieval_kernel import RetrievalKernel

class OriginalGeometryKernel(MemoryKernel, RetrievalKernel):

    def pointmap_to_surfels(self, pointmap: torch.Tensor, focal_lengths: torch.Tensor, depths: torch.Tensor, confs: torch.Tensor, poses: torch.Tensor, radius_scale: float=0.5, estimate_normals: bool=True):
        """
        Vectorized version of pointmap to surfels conversion.
        All operations are performed on the specified device (self.device) until final numpy conversion.
        """
        if isinstance(poses, np.ndarray):
            poses = torch.from_numpy(poses).to(self.device)
        if isinstance(focal_lengths, np.ndarray):
            focal_lengths = torch.from_numpy(focal_lengths).to(self.device)
        if isinstance(depths, np.ndarray):
            depths = torch.from_numpy(depths).to(self.device)
        if isinstance(confs, np.ndarray):
            confs = torch.from_numpy(confs).to(self.device)
        pointmap = pointmap.to(self.device)
        focal_lengths = focal_lengths.to(self.device)
        depths = depths.to(self.device)
        confs = confs.to(self.device)
        poses = poses.to(self.device)
        if len(focal_lengths) == 2:
            focal_lengths = torch.mean(focal_lengths, dim=0)
        if estimate_normals:
            normal_map = self.estimate_normal_from_pointmap(pointmap)
        else:
            normal_map = torch.zeros_like(pointmap)
        depth_threshold = torch.quantile(depths, 0.999)
        valid_mask = (depths <= depth_threshold) & (confs >= self.config.surfel.conf_thresh)
        positions = pointmap[valid_mask]
        normals = normal_map[valid_mask]
        valid_depths = depths[valid_mask]
        camera_pos = poses[0:3, 3]
        view_directions = positions - camera_pos.unsqueeze(0)
        view_directions = F.normalize(view_directions, dim=1)
        dot_products = torch.sum(view_directions * normals, dim=1)
        flip_mask = dot_products < 0
        normals[flip_mask] = -normals[flip_mask]
        dot_products = torch.abs(torch.sum(view_directions * normals, dim=1))
        adjustment_values = 0.2 + 0.8 * dot_products
        radii = radius_scale * valid_depths / focal_lengths / adjustment_values
        positions = positions.detach().cpu().numpy()
        normals = normals.detach().cpu().numpy()
        radii = radii.detach().cpu().numpy()
        surfels = [Surfel(pos, norm, rad) for pos, norm, rad in zip(positions, normals, radii)]
        return surfels

    def estimate_normal_from_pointmap(self, pointmap: torch.Tensor) -> torch.Tensor:
        h, w = pointmap.shape[:2]
        device = pointmap.device
        dtype = pointmap.dtype
        normal_map = torch.zeros((h, w, 3), device=device, dtype=dtype)
        for y in range(h):
            for x in range(w):
                if x + 1 >= w or y + 1 >= h:
                    continue
                p_center = pointmap[y, x]
                p_right = pointmap[y, x + 1]
                p_down = pointmap[y + 1, x]
                v1 = p_right - p_center
                v2 = p_down - p_center
                v1 = v1 / torch.linalg.norm(v1)
                v2 = v2 / torch.linalg.norm(v2)
                n_c = torch.cross(v1, v2)
                norm_len = torch.linalg.norm(n_c)
                if norm_len < 1e-08:
                    continue
                normal_map[y, x] = n_c / norm_len
        return normal_map

    def resize_scene_inputs(self, pointcloud, depths, confs):
        pointcloud = pointcloud.permute(0, 3, 1, 2)
        pointcloud = F.interpolate(pointcloud, scale_factor=self.config.surfel.shrink_factor, mode='bilinear')
        pointcloud = pointcloud.permute(0, 2, 3, 1)
        depths = depths.unsqueeze(1)
        depths = F.interpolate(depths, scale_factor=self.config.surfel.shrink_factor, mode='bilinear')
        depths = depths.squeeze(1)
        confs = confs.unsqueeze(1)
        confs = F.interpolate(confs, scale_factor=self.config.surfel.shrink_factor, mode='bilinear')
        confs = confs.squeeze(1)
        return (pointcloud, depths, confs)

    def store_reduced_scene(self, pointcloud, depths, confs, focal_lengths, c2ws_transformed):
        start_idx = 0 if len(self.surfels) == 0 else len(pointcloud) - self.config.model.target_num_frames
        end_idx = len(pointcloud)
        for frame_idx in range(start_idx, end_idx):
            surfels = self.pointmap_to_surfels(pointmap=pointcloud[frame_idx], focal_lengths=focal_lengths[frame_idx] * self.config.surfel.shrink_factor, depths=depths[frame_idx], confs=confs[frame_idx], poses=c2ws_transformed[frame_idx], estimate_normals=True, radius_scale=self.config.surfel.radius_scale)
            if len(self.surfels) > 0:
                surfels, self.surfel_to_timestep = self.merge_surfels(new_surfels=surfels, current_timestep=frame_idx, existing_surfels=self.surfels, existing_surfel_to_timestep=self.surfel_to_timestep, normal_threshold=self.config.surfel.merge_normal_threshold)
            num_surfels = len(surfels)
            surfel_start_index = len(self.surfels)
            for surfel_index in range(num_surfels):
                self.surfel_to_timestep[surfel_start_index + surfel_index] = [frame_idx]
            self.surfels.extend(surfels)
