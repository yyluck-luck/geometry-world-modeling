"""Controlled synthetic fixtures around VMem's unmodified context selector."""
from copy import deepcopy
from types import SimpleNamespace as NS
import numpy as np
import torch
from vmem_memory_kernel import Surfel
from vmem_retrieval_kernel import RetrievalKernel


class ObservedKernel(RetrievalKernel):
    """Capture return values without altering the official calculation."""
    def render_surfels_to_image(self, *args, **kwargs):
        result = super().render_surfels_to_image(*args, **kwargs)
        self.last_render = result
        return result

    def process_retrieved_spatial_information(self, value):
        result = super().process_retrieved_spatial_information(value)
        self.last_weights, self.last_counts = result
        return result


def camera(x=0, y=0, z=0):
    pose = np.diag([1., -1., -1., 1.])
    pose[:3, 3] = [x, y, z]
    return pose


def build_fixture(scenario, seed, scale, cfg):
    rng = np.random.default_rng(seed)
    centers = np.array([[x, y, 4.] for y in np.linspace(-.54, .54, 4)
                        for x in np.linspace(-.9, .9, 5)])
    centers[:, :2] += rng.uniform(-.008, .008, (20, 2))
    points, radii, blocks = [], [], []
    for i, center in enumerate(centers):
        size = .85 + .3 * ((i * 7) % 20) / 19
        for dy in [-.045, 0, .045]:
            for dx in [-.045, 0, .045]:
                points.append(center + [dx*size, dy*size, 0])
                radii.append(.028 * size)
                blocks.append(i)
    points, radii, blocks = np.array(points), np.array(radii), np.array(blocks)
    if scenario == "shared_history_8":
        poses = [camera(-.11+i*.027, .009+i*.0013, -.015*i) for i in range(8)]
    elif scenario == "patch_history_20":
        poses = [camera(c[0]+.001*i, c[1]+.0003*i, 3.70+.002*i)
                 for i,c in enumerate(centers)]
    else:
        raise ValueError(scenario)
    width, height = cfg['base_width']*scale, cfg['base_height']*scale
    effective_focal = cfg['base_effective_focal']*scale
    source_focal = effective_focal/.65
    mapping = {i: [] for i in range(len(points))}
    for frame, pose in enumerate(poses):
        # All cameras look along world +z; points are coplanar, without occlusion.
        p = points-pose[:3, 3]
        uv = p[:, :2] / p[:, 2:3] * source_focal + [width/2, height/2]
        visible = (p[:, 2]>0) & (uv[:, 0]>=0) & (uv[:, 0]<width) & (uv[:, 1]>=0) & (uv[:, 1]<height)
        for i in np.flatnonzero(visible):
            mapping[int(i)].append(frame)
    if not all(mapping.values()):
        raise ValueError('Unobserved surfel in fixture')
    return dict(scenario=scenario, seed=seed, scale=scale, points=points, radii=radii,
                blocks=blocks, poses=poses, mapping=mapping, width=width, height=height,
                source_focal=source_focal)


def instantiate(fixture, cfg, points=None, frame_limit=None, threshold=None):
    p = fixture['points'] if points is None else points
    poses = fixture['poses'][:frame_limit]
    n = len(poses)
    obj = ObservedKernel()
    obj.config = NS(model=NS(context_num_frames=cfg['context_num_frames'],
                            translation_distance_weight=cfg['translation_distance_weight']),
                    surfel=NS(width=fixture['width'], height=fixture['height']),
                    inference=NS(visualize=False))
    obj.device, obj.dtype = 'cpu', torch.float64
    obj.use_non_maximum_suppression = True
    if threshold is not None:
        obj.initial_threshold = threshold
    obj.pil_frames = [None]*n
    obj.c2ws = deepcopy(poses)
    obj.latents = [np.array([i], dtype=np.float64) for i in range(n)]
    obj.encoder_embeddings = [np.array([i+.25], dtype=np.float64) for i in range(n)]
    intrinsic = np.array([[fixture['source_focal'],0,fixture['width']/2],
                          [0,fixture['source_focal'],fixture['height']/2],[0,0,1.]])
    obj.Ks = [intrinsic.copy() for _ in poses]
    obj.surfel_Ks = [fixture['source_focal']]*n
    obj.surfels, obj.surfel_to_timestep = [], {}
    for i, point in enumerate(p):
        ids = [j for j in fixture['mapping'][i] if j<n]
        if ids:
            obj.surfel_to_timestep[len(obj.surfels)] = ids
            obj.surfels.append(Surfel(point.copy(), np.array([0.,0.,1.]), fixture['radii'][i]))
    return obj


def warm_threshold(fixture, cfg):
    obj = instantiate(fixture, cfg, frame_limit=5)
    obj.get_context_info(torch.tensor(np.array([fixture['poses'][2]]),dtype=torch.float64))
    return float(obj.initial_threshold)


def evaluate(fixture, cfg, points, query, threshold):
    obj = instantiate(fixture, cfg, points=points, threshold=threshold)
    output = obj.get_context_info(torch.tensor(np.array([query]),dtype=torch.float64))
    selected = [int(x) for x in output['context_time_indices'].tolist()]
    ranked = sorted(obj.last_weights, key=lambda v:v[1], reverse=True)
    candidates = [int(k) for k,n in obj.last_counts if n>0]
    distances = [float(obj.geodesic_distance(torch.tensor(query),torch.tensor(obj.c2ws[k]),
                               weight_translation=cfg['translation_distance_weight'])) for k in candidates]
    # Match the original torch.tensor(distances) used for sorting (default float32).
    sort_values = torch.tensor(distances)
    gaps = np.diff(np.sort(sort_values.numpy()))
    trace = dict(selected=selected, candidates=candidates,
                 visible_sources=[int(i) for i,_ in obj.last_weights],
                 weights=[[int(i),float(w)] for i,w in obj.last_weights],
                 candidate_counts=[[int(i),int(n)] for i,n in obj.last_counts],
                 cutoff_gap_14_15=float(ranked[13][1]-ranked[14][1]) if len(ranked)>14 else None,
                 minimum_candidate_pose_distance_gap=float(gaps.min()) if len(gaps) else None,
                 candidate_pose_tie_count=int((gaps==0).sum()),
                 distance_sort_dtype=str(sort_values.dtype),
                 rendered_coverage=float((obj.last_render['surfel_index_map']>=0).mean()),
                 nms_initial_threshold=threshold)
    return trace, obj.last_render


def perturb(fixture, kind, magnitude, cfg):
    points = fixture['points'].copy()
    affected = np.ones(len(points), dtype=bool) if fixture['scenario']=='shared_history_8' else np.isin(fixture['blocks'],cfg['corrupted_patch_ids'])
    if kind=='translation_x':
        points[affected, 0] += magnitude
    elif kind=='depth_scale':
        points[affected] *= 1+magnitude
    else:
        raise ValueError(kind)
    return points


def reference_coverage(selected, clean_render, fixture):
    visible = clean_render['surfel_index_map']
    valid = visible>=0
    if not valid.any():
        return None
    supported = np.array([bool(set(selected).intersection(fixture['mapping'][int(i)]))
                          for i in visible[valid]])
    return float(supported.mean())
