"""Unmodified AST extraction from VMem (MIT), revision in vendor/provenance.json.
Only merge and NumPy-input rendering run here; no model or tensor path is loaded.
The torch sentinel makes upstream isinstance checks false for NumPy inputs.
"""
import math
from typing import Union
from types import SimpleNamespace
import numpy as np

class _UnsupportedTensor:
    pass

torch = SimpleNamespace(Tensor=_UnsupportedTensor)

class Surfel:

    def __init__(self, position, normal, radius=1.0, color=None):
        """
        position: (x, y, z)
        normal:   (nx, ny, nz)
        radius:   scalar
        color:    (r, g, b) or None
        """
        self.position = position
        self.normal = normal
        self.radius = radius
        self.color = color

    def __repr__(self):
        return f'Surfel(position={self.position}, normal={self.normal}, radius={self.radius}, color={self.color})'

class Octree:

    def __init__(self, points, indices=None, bbox=None, max_points=10):
        self.points = points
        if indices is None:
            indices = np.arange(points.shape[0])
        self.indices = indices
        if bbox is None:
            min_bound = points.min(axis=0)
            max_bound = points.max(axis=0)
            center = (min_bound + max_bound) / 2
            half_size = np.max(max_bound - min_bound) / 2
            bbox = (center, half_size)
        self.center, self.half_size = bbox
        self.children = []
        self.max_points = max_points
        if len(self.indices) > self.max_points:
            self.subdivide()

    def subdivide(self):
        cx, cy, cz = self.center
        hs = self.half_size / 2
        offsets = np.array([[dx, dy, dz] for dx in (-hs, hs) for dy in (-hs, hs) for dz in (-hs, hs)])
        for offset in offsets:
            child_center = self.center + offset
            child_indices = []
            for idx in self.indices:
                p = self.points[idx]
                if np.all(np.abs(p - child_center) <= hs):
                    child_indices.append(idx)
            child_indices = np.array(child_indices)
            if len(child_indices) > 0:
                child = Octree(self.points, indices=child_indices, bbox=(child_center, hs), max_points=self.max_points)
                self.children.append(child)
        self.indices = None

    def sphere_intersects_node(self, center, r):
        diff = np.abs(center - self.center)
        max_diff = diff - self.half_size
        max_diff = np.maximum(max_diff, 0)
        dist_sq = np.sum(max_diff ** 2)
        return dist_sq <= r * r

    def query_ball_point(self, point, r):
        results = []
        if not self.sphere_intersects_node(point, r):
            return results
        if len(self.children) == 0:
            if self.indices is not None:
                for idx in self.indices:
                    if np.linalg.norm(self.points[idx] - point) <= r:
                        results.append(idx)
            return results
        else:
            for child in self.children:
                results.extend(child.query_ball_point(point, r))
            return results

class MemoryKernel:

    def render_surfels_to_image(self, surfels, poses, focal_lengths, principal_points, image_width, image_height, disk_resolution=16):
        """
        Renders oriented surfels into a 2D RGB image with a simple z-buffer.
        Each surfel is treated as a 2D disk in 3D, oriented by its normal.
        The disk is approximated by a polygon of 'disk_resolution' segments.

        Args:
            surfels (list): List of Surfel objects, each having:
                - position: (x, y, z) in world coords
                - normal:   (nx, ny, nz)
                - radius:   float, radius in world units
            poses (torch.Tensor): Tensor of poses, shape [4, 4]
            focal_lengths (torch.Tensor): Tensor of focal lengths, shape [2]
            principal_points (torch.Tensor): Tensor of principal points, shape [2]
            image_width, image_height (int): output image size
            disk_resolution (int): number of segments for approximating each disk

        Returns:
            Dictionary containing:
            - depth: depth map
            - surfel_index_map: map of surfel indices
            - cos_value_map: map of cosine values between view and normal directions
        """
        if isinstance(focal_lengths, torch.Tensor):
            focal_lengths = focal_lengths.detach().cpu().numpy()
        if isinstance(principal_points, torch.Tensor):
            principal_points = principal_points.detach().cpu().numpy()
        if isinstance(poses, torch.Tensor):
            poses = poses.detach().cpu().numpy()
        surfel_index_map = np.full((image_height, image_width), -1, dtype=np.int32)
        z_buffer = np.full((image_height, image_width), np.inf, dtype=np.float32)
        cos_buffer = np.zeros((image_height, image_width), dtype=np.float32)
        fx, fy, cx, cy = (focal_lengths[0], focal_lengths[1], principal_points[0], principal_points[1])
        R = poses[0:3, 0:3]
        t = poses[0:3, 3]
        near_z = 0.1
        far_z = 1000.0
        positions = np.array([s.position for s in surfels])
        positions_h = np.concatenate([positions, np.ones((len(positions), 1))], axis=1)
        extrinsics = np.zeros((4, 4))
        extrinsics[0:3, 0:3] = np.linalg.inv(R)
        extrinsics[0:3, 3] = -np.linalg.inv(R) @ t
        extrinsics[3, 3] = 1
        cam_points = (extrinsics @ positions_h.T).T
        cam_points = cam_points[:, :3] / cam_points[:, 3:]
        in_front = cam_points[:, 2] > near_z
        behind_far = cam_points[:, 2] < far_z
        screen_x = fx * (cam_points[:, 0] / cam_points[:, 2]) + cx
        screen_y = fy * (cam_points[:, 1] / cam_points[:, 2]) + cy
        margin = 50
        in_screen_x = (screen_x >= -margin) & (screen_x < image_width + margin)
        in_screen_y = (screen_y >= -margin) & (screen_y < image_height + margin)
        visible_mask = in_front & behind_far & in_screen_x & in_screen_y
        visible_indices = np.where(visible_mask)[0]

        def point_in_polygon_2d(px, py, polygon):
            """Fast point-in-polygon test using ray casting"""
            inside = False
            n = len(polygon)
            j = n - 1
            for i in range(n):
                if (polygon[i][1] > py) != (polygon[j][1] > py) and px < (polygon[j][0] - polygon[i][0]) * (py - polygon[i][1]) / (polygon[j][1] - polygon[i][1] + 1e-15) + polygon[i][0]:
                    inside = not inside
                j = i
            return inside
        angles = np.linspace(0, 2 * math.pi, disk_resolution, endpoint=False)
        cos_angles = np.cos(angles)
        sin_angles = np.sin(angles)
        for idx in visible_indices:
            surfel = surfels[idx]
            px, py, pz = surfel.position
            nx, ny, nz = surfel.normal
            radius = surfel.radius
            normal = np.array([nx, ny, nz], dtype=float)
            norm_len = np.linalg.norm(normal)
            if norm_len < 1e-12:
                continue
            normal /= norm_len
            point_direction = (px, py, pz) - t
            point_direction = point_direction / np.linalg.norm(point_direction)
            cos_value = np.dot(point_direction, normal)
            if cos_value < 0:
                continue
            up = np.array([0, 0, 1], dtype=float)
            if abs(np.dot(normal, up)) > 0.9:
                up = np.array([0, 1, 0], dtype=float)
            xAxis = np.cross(normal, up)
            xAxis /= np.linalg.norm(xAxis)
            yAxis = np.cross(normal, xAxis)
            yAxis /= np.linalg.norm(yAxis)
            offsets = radius * (cos_angles[:, None] * xAxis + sin_angles[:, None] * yAxis)
            circle_points = positions[idx] + offsets
            circle_points_h = np.concatenate([circle_points, np.ones((len(circle_points), 1))], axis=1)
            cam_circle = (extrinsics @ circle_points_h.T).T
            depths = cam_circle[:, 2]
            valid_mask = depths > 0
            if not np.any(valid_mask):
                continue
            screen_points = np.zeros((len(circle_points), 2))
            screen_points[:, 0] = fx * (cam_circle[:, 0] / depths) + cx
            screen_points[:, 1] = fy * (cam_circle[:, 1] / depths) + cy
            valid_points = screen_points[valid_mask]
            if len(valid_points) < 3:
                continue
            min_x = max(0, int(np.floor(np.min(valid_points[:, 0]))))
            max_x = min(image_width - 1, int(np.ceil(np.max(valid_points[:, 0]))))
            min_y = max(0, int(np.floor(np.min(valid_points[:, 1]))))
            max_y = min(image_height - 1, int(np.ceil(np.max(valid_points[:, 1]))))
            avg_depth = float(np.mean(depths[valid_mask]))
            for py_ in range(min_y, max_y + 1):
                for px_ in range(min_x, max_x + 1):
                    if point_in_polygon_2d(px_, py_, valid_points):
                        if avg_depth < z_buffer[py_, px_]:
                            z_buffer[py_, px_] = avg_depth
                            surfel_index_map[py_, px_] = idx
                            cos_buffer[py_, px_] = cos_value
        depth = z_buffer
        depth[depth == np.inf] = 0
        return {'depth': depth, 'surfel_index_map': surfel_index_map, 'cos_value_map': cos_buffer}

    def merge_surfels(self, new_surfels: list, current_timestep: str, existing_surfels: list, existing_surfel_to_timestep: dict, position_threshold: Union[float, None]=None, normal_threshold: float=0.7, max_points_per_node: int=10):
        assert len(existing_surfels) == len(existing_surfel_to_timestep), 'existing_surfels and existing_surfel_to_timestep should have the same length'
        if position_threshold is None:
            all_radii = np.array([s.radius for s in existing_surfels + new_surfels])
            if len(all_radii) > 0:
                mean_radius = np.mean(all_radii)
                std_radius = np.std(all_radii)
                position_threshold = mean_radius + 0.5 * std_radius
            else:
                position_threshold = 0.025
        positions = np.array([s.position for s in existing_surfels])
        normals = np.array([s.normal for s in existing_surfels])
        if len(positions) > 0:
            octree = Octree(positions, max_points=max_points_per_node)
        else:
            octree = None
        filtered_surfels = []
        merge_count = 0
        for new_surfel in new_surfels:
            is_merged = False
            if octree is not None:
                neighbor_indices = octree.query_ball_point(new_surfel.position, position_threshold)
            else:
                neighbor_indices = []
            for idx in neighbor_indices:
                if np.dot(normals[idx], new_surfel.normal) > normal_threshold:
                    if current_timestep not in existing_surfel_to_timestep[idx]:
                        existing_surfel_to_timestep[idx].append(current_timestep)
                    is_merged = True
                    merge_count += 1
                    break
            if not is_merged:
                filtered_surfels.append(new_surfel)
        print(f'merge_count: {merge_count}')
        return (filtered_surfels, existing_surfel_to_timestep)
