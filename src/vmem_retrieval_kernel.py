"""Unmodified AST extraction of VMem's entire context selection path.
No model constructor is included. CPU torch tensors package dummy context arrays.
See vendor/provenance.json and vendor/VMEM_LICENSE for revision and attribution.
"""
import math
from copy import deepcopy
import numpy as np
import torch

def average_camera_pose(camera_poses):
    """
    Compute a better average of camera poses in SE(3).
    
    Args:
        camera_poses: List or array of camera poses, each a 4x4 matrix
        
    Returns:
        Average camera pose as a 4x4 matrix
    """
    rotations = camera_poses[:, :3, :3].detach().cpu().numpy()
    translations = camera_poses[:, :3, 3].detach().cpu().numpy()
    avg_translation = np.mean(translations, axis=0)
    import scipy.spatial.transform as transform
    quats = [transform.Rotation.from_matrix(R).as_quat() for R in rotations]
    for i in range(1, len(quats)):
        if np.dot(quats[0], quats[i]) < 0:
            quats[i] = -quats[i]
    avg_quat = np.mean(quats, axis=0)
    avg_quat = avg_quat / np.linalg.norm(avg_quat)
    avg_rotation = transform.Rotation.from_quat(avg_quat).as_matrix()
    avg_pose = np.eye(4)
    avg_pose[:3, :3] = avg_rotation
    avg_pose[:3, 3] = avg_translation
    return avg_pose

class RetrievalKernel:

    def geodesic_distance(self, camera_pose1, camera_pose2, weight_translation=1):
        """
        Computes the geodesic distance between two camera poses in SE(3).
        
        Parameters:
            extrinsic1 (torch.Tensor): 4x4 extrinsic matrix of the first pose.
            extrinsic2 (torch.Tensor): 4x4 extrinsic matrix of the second pose.

        Returns:
            float: Geodesic distance between the two poses.
        """
        R1 = camera_pose1[:3, :3]
        t1 = camera_pose1[:3, 3]
        R2 = camera_pose2[:3, :3]
        t2 = camera_pose2[:3, 3]
        translation_distance = torch.norm(t1 - t2)
        R_relative = torch.matmul(R1.T, R2)
        trace_value = torch.trace(R_relative)
        trace_value = torch.clamp(trace_value, -1.0, 3.0)
        angular_distance = torch.acos((trace_value - 1) / 2)
        geodesic_dist = translation_distance * weight_translation + angular_distance
        return geodesic_dist

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

    def get_frame_distribution(self, n, ratios):
        """
        Given:
        - an integer n,
        - a list of k ratios whose sum is 1 (k <= n),
        return a list of k integers [x1, x2, ..., xk],
        such that each xi >= 1, sum(xi) = n, and
        the xi are as proportional to ratios as possible.
        """
        k = len(ratios)
        if k > n:
            result = [0] * k
            sort_indices = np.argsort(ratios)[::-1]
            for sort_index in sort_indices[:n]:
                result[sort_index] = 1
            return result
        result = [1] * k
        leftover = n - k
        if leftover == 0:
            return result
        products = [r * leftover for r in ratios]
        floored = [int(p // 1) for p in products]
        sum_floors = sum(floored)
        leftover2 = leftover - sum_floors
        for i in range(k):
            result[i] += floored[i]
        remainders = [(p - f, i) for i, (p, f) in enumerate(zip(products, floored))]
        remainders.sort(key=lambda x: x[0], reverse=True)
        for j in range(leftover2):
            _, idx = remainders[j]
            result[idx] = 1
        return result

    def process_retrieved_spatial_information(self, retrieved_spatial_information):
        timestep_count = {}
        surfel_index_map = retrieved_spatial_information['surfel_index_map']
        cos_value_map = retrieved_spatial_information['cos_value_map']
        depth_map = retrieved_spatial_information['depth']
        filtered_cos_value = cos_value_map[surfel_index_map >= 0]
        filtered_surfel_index = surfel_index_map[surfel_index_map >= 0]
        filtered_depth = depth_map[surfel_index_map >= 0]
        assert len(filtered_cos_value) == len(filtered_surfel_index), 'filtered_cos_value and filtered_surfel_index should have the same length'
        for j in range(len(filtered_surfel_index)):
            cos_value = filtered_cos_value[j]
            depth_value = filtered_depth[j]
            if cos_value < 0:
                continue
            surfel_index = filtered_surfel_index[j]
            timesteps = self.surfel_to_timestep[surfel_index]
            for timestep in timesteps:
                if timestep not in timestep_count:
                    timestep_count[timestep] = cos_value / (1 + depth_value)
                timestep_count[timestep] += cos_value / (1 + depth_value)
        timestep_count_values = np.array(list(timestep_count.values()))
        timestep_count_ratios = timestep_count_values / np.sum(timestep_count_values)
        timestep_weights = {k: timestep_count_ratios[i] for i, k in enumerate(timestep_count)}
        num_retrieved_frames = min(self.config.model.context_num_frames + 10, len(timestep_weights))
        frame_count = self.get_frame_distribution(num_retrieved_frames, list(timestep_weights.values()))
        frame_count = {k: int(v) for k, v in zip(timestep_count.keys(), frame_count)}
        timestep_weights = sorted(timestep_weights.items(), key=lambda x: x[0])
        frame_count = sorted(frame_count.items(), key=lambda x: x[0])
        return (timestep_weights, frame_count)

    def get_context_info(self, target_c2ws, use_non_maximum_suppression=None):
        """Get context information for novel view synthesis.
        
        Args:
            target_c2ws: Target camera-to-world matrices
            Ks: Camera intrinsic matrices
            current_timestep: Current timestep (used in temporal mode)
            
        Returns:
            Dictionary containing context information for the target view
        """

        def prepare_context_data(indices):
            c2ws = [self.c2ws[i] for i in indices]
            latents = [torch.from_numpy(self.latents[i]).to(self.device, self.dtype) for i in indices]
            embeddings = [torch.from_numpy(self.encoder_embeddings[i]).to(self.device, self.dtype) for i in indices]
            intrinsics = [self.Ks[i] for i in indices]
            return (c2ws, latents, embeddings, intrinsics, indices)
        if len(self.pil_frames) == 1:
            context_time_indices = [0]
        else:
            average_c2w = average_camera_pose(target_c2ws[-self.config.model.context_num_frames // 4:])
            transformed_average_c2w = self.get_transformed_c2ws(average_c2w)
            target_K = np.mean(self.surfel_Ks, axis=0)
            retrieved_info = self.render_surfels_to_image(self.surfels, transformed_average_c2w, [target_K * 0.65] * 2, principal_points=(int(self.config.surfel.width / 2), int(self.config.surfel.height / 2)), image_width=int(self.config.surfel.width), image_height=int(self.config.surfel.height))
            _, frame_count = self.process_retrieved_spatial_information(retrieved_info)
            if self.config.inference.visualize:
                visualize_depth(retrieved_info['depth'], visualization_dir=self.visualize_dir, file_name=f'retrieved_depth_surfels.png', size=(self.width, self.height))
            candidates = []
            for frame, count in frame_count:
                candidates.extend([frame] * count)
                indices_to_frame = {i: frame for i, frame in enumerate(candidates)}
            distances = [self.geodesic_distance(torch.from_numpy(average_c2w).to(self.device, self.dtype), torch.from_numpy(self.c2ws[frame]).to(self.device, self.dtype), weight_translation=self.config.model.translation_distance_weight).item() for frame in candidates]
            sorted_indices = torch.argsort(torch.tensor(distances))
            sorted_frames = [indices_to_frame[int(i.item())] for i in sorted_indices]
            max_frames = min(self.config.model.context_num_frames, len(candidates), len(self.latents))
            is_second_step = len(self.pil_frames) == 5
            if use_non_maximum_suppression is None:
                use_non_maximum_suppression = self.use_non_maximum_suppression
            if use_non_maximum_suppression:
                if is_second_step:
                    pairwise_distances = []
                    for i in range(len(self.c2ws)):
                        for j in range(i + 1, len(self.c2ws)):
                            sim = self.geodesic_distance(torch.from_numpy(np.array(self.c2ws[i])).to(self.device, self.dtype), torch.from_numpy(np.array(self.c2ws[j])).to(self.device, self.dtype), weight_translation=self.config.model.translation_distance_weight)
                            pairwise_distances.append(sim.item())
                    if pairwise_distances:
                        pairwise_distances.sort()
                        percentile_idx = int(len(pairwise_distances) * 0.5)
                        self.initial_threshold = pairwise_distances[percentile_idx]
                    else:
                        self.initial_threshold = 1
            else:
                self.initial_threshold = 100000000.0
            selected_indices = []
            current_threshold = self.initial_threshold
            selected_indices.append(sorted_frames[0])
            if not use_non_maximum_suppression:
                selected_indices.append(len(self.c2ws) - 1)
            while len(selected_indices) < max_frames and current_threshold >= 1e-05 and use_non_maximum_suppression:
                for idx in sorted_frames[1:]:
                    if len(selected_indices) >= max_frames:
                        break
                    is_too_similar = False
                    for selected_idx in selected_indices:
                        similarity = self.geodesic_distance(torch.from_numpy(np.array(self.c2ws[idx])).to(self.device, self.dtype), torch.from_numpy(np.array(self.c2ws[selected_idx])).to(self.device, self.dtype), weight_translation=self.config.model.translation_distance_weight)
                        if similarity < current_threshold:
                            is_too_similar = True
                            break
                    if not is_too_similar:
                        selected_indices.append(idx)
                if len(selected_indices) < max_frames:
                    current_threshold /= 1.2
                else:
                    break
            if len(selected_indices) < max_frames:
                available_indices = []
                for idx in sorted_frames:
                    if idx not in selected_indices:
                        available_indices.append(idx)
                selected_indices.extend(available_indices[:max_frames - len(selected_indices)])
            context_time_indices = torch.from_numpy(np.array(selected_indices))
        context_data = prepare_context_data(context_time_indices)
        context_c2ws, context_latents, context_encoder_embeddings, context_Ks, context_time_indices = context_data
        return {'context_c2ws': torch.from_numpy(np.array(context_c2ws)).to(self.device, self.dtype), 'context_latents': torch.stack(context_latents).to(self.device, self.dtype), 'context_encoder_embeddings': torch.stack(context_encoder_embeddings).to(self.device, self.dtype), 'context_Ks': torch.from_numpy(np.array(context_Ks)).to(self.device, self.dtype), 'context_time_indices': context_time_indices}

    def get_transformed_c2ws(self, c2ws=None):
        if c2ws is None:
            c2ws = self.c2ws
        c2ws_transformed = deepcopy(np.array(c2ws))
        c2ws_transformed[..., :, [1, 2]] *= -1
        return c2ws_transformed
