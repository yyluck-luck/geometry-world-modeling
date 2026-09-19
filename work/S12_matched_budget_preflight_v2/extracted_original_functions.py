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

def optical_to_vmem(pose):
    return np.asarray(pose) @ np.diag([1.0, -1.0, -1.0, 1.0])

def initial_nms_threshold(optical_poses, weight=0.1):
    obj = ObservedKernel()
    poses = [optical_to_vmem(p) for p in optical_poses[:5]]
    values = [float(obj.geodesic_distance(torch.tensor(poses[i]), torch.tensor(poses[j]), weight)) for i in range(len(poses)) for j in range(i + 1, len(poses))]
    values.sort()
    return values[int(len(values) * 0.5)] if values else 1.0

def decision_trace(kernel, optical_query, counts, nms=True):
    """Instrument original expanded-candidate sorting/NMS, or pure no-NMS control.

    nms=False deliberately does NOT call the official false branch, which forces
    the last historical frame. No deduplication before float32 torch.argsort.
    """
    query = torch.tensor(average_camera_pose(torch.tensor(optical_to_vmem(optical_query)[None], dtype=torch.float64)), dtype=torch.float64)
    candidate_ids = [int(frame) for frame, count in counts for _ in range(int(count))]
    if not candidate_ids:
        raise ValueError('Empty candidate pool')
    distances = [float(kernel.geodesic_distance(query, torch.tensor(kernel.c2ws[f], dtype=torch.float64), 0.1)) for f in candidate_ids]
    distances32 = torch.tensor(distances, dtype=torch.float32)
    order = torch.argsort(distances32).tolist()
    ranked = [candidate_ids[i] for i in order]
    maximum = min(4, len(candidate_ids), len(kernel.c2ws))
    chosen, steps = ([ranked[0]], [])
    threshold = float(kernel.initial_threshold)
    if nms:
        while len(chosen) < maximum and threshold >= 1e-05:
            for frame in ranked[1:]:
                if len(chosen) >= maximum:
                    break
                comparisons = []
                rejected = False
                for selected in chosen:
                    d = float(kernel.geodesic_distance(torch.tensor(kernel.c2ws[frame], dtype=torch.float64), torch.tensor(kernel.c2ws[selected], dtype=torch.float64), 0.1))
                    comparisons.append([selected, d])
                    if d < threshold:
                        rejected = True
                        break
                steps.append(dict(frame=frame, threshold=threshold, comparisons=comparisons, accepted=not rejected))
                if not rejected:
                    chosen.append(frame)
            if len(chosen) < maximum:
                steps.append(dict(relax_from=threshold, relax_to=threshold / 1.2))
                threshold /= 1.2
        if len(chosen) < maximum:
            available = [i for i in ranked if i not in chosen]
            added = available[:maximum - len(chosen)]
            chosen.extend(added)
            steps.append(dict(fallback_added=added))
    else:
        for frame in ranked[1:]:
            if frame not in chosen:
                chosen.append(frame)
            if len(chosen) == maximum:
                break
    if len(chosen) != 4 or len(set(chosen)) != 4 or any((not 0 <= f < 20 for f in chosen)):
        raise ValueError('Readout did not produce four unique historical IDs')
    return dict(selected=chosen, expanded_candidates=candidate_ids, sorted_frames=ranked, distances_float32=distances32.tolist(), nms=nms, expanded_adjacent_pose_ties=int((np.diff(np.sort(distances32.numpy())) == 0).sum()), initial_threshold=float(kernel.initial_threshold), steps=steps)
