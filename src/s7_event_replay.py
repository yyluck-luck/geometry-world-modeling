"""Prediction-only S7 event recording, fixed-path replay, and readout controls.

No measured geometry or scoring imports. Old S6 modules remain unmodified.
"""
from collections import defaultdict
import numpy as np
import torch

from rgbd_memory import Memory
from s6_memory_bridge import make_surfels
from vmem_memory_kernel import Surfel
from rgbd_retrieval import optical_to_vmem
from vmem_retrieval_kernel import average_camera_pose


def clone(s):
    return Surfel(s.position.copy(), s.normal.copy(), float(s.radius), s.color.copy())


def observations(depths, confs, rgbs, poses, stride):
    """Use the unchanged constructor twice to recover original pixel identities."""
    v, u = np.mgrid[:224, :224]
    encoded = np.stack((u, v, np.zeros_like(u)), axis=-1).astype(np.uint8)
    frames, identities, filters = [], [], []
    for f, (d, c, rgb, pose) in enumerate(zip(depths, confs, rgbs, poses)):
        real, counts = make_surfels(d, c, rgb, pose, stride)
        tagged, check_counts = make_surfels(d, c, encoded, pose, stride)
        if counts != check_counts or len(real) != len(tagged):
            raise ValueError('Pixel tagging changed the accepted observations')
        ids = []
        for a, b in zip(real, tagged):
            if not (np.array_equal(a.position, b.position)
                    and np.array_equal(a.normal, b.normal) and a.radius == b.radius):
                raise ValueError('Pixel tagging changed geometry')
            uv = np.rint(b.color[:2] * 255).astype(int)
            if any(uv < 0) or any(uv >= 224) or any(uv % stride):
                raise ValueError('Invalid accepted pixel identity')
            if not np.array_equal(a.color, rgb[uv[1], uv[0]].astype(float) / 255.):
                raise ValueError('Observation RGB/identity mismatch')
            ids.append((f, int(uv[0]), int(uv[1])))
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate observation identity')
        frames.append(real)
        identities.extend(ids)
        filters.append(counts)
    return frames, np.asarray(identities, dtype=np.int64), filters


def record_path(frames, method):
    memory, events = Memory(method), []
    for frame, surfels in enumerate(frames):
        old_n = len(memory.surfels)
        matches = memory.add(surfels, frame, normal_threshold=.6)
        next_id = old_n
        targets = []
        for match in matches:
            if match < 0:
                targets.append(next_id)
                next_id += 1
            else:
                targets.append(match)
        events.append(dict(frame=frame, old_n=old_n, targets=targets,
                           matches=matches, new_n=next_id,
                           threshold=memory.records[-1]['position_threshold_m']))
    return memory, events


def replay(frames, events, position_rule):
    """No matching or tree: replay fixed targets, preserving frame-centroid votes."""
    if position_rule not in ('first_write', 'frame_mean'):
        raise ValueError(position_rule)
    memory = Memory(position_rule)
    if len(frames) != len(events):
        raise ValueError('Frame/event length mismatch')
    for frame, (surfels, event) in enumerate(zip(frames, events)):
        if event['frame'] != frame or event['old_n'] != len(memory.surfels):
            raise ValueError('Invalid event boundary')
        old_n = event['old_n']
        if len(surfels) != len(event['targets']) or len(surfels) != len(event['matches']):
            raise ValueError('Event/observation length mismatch')
        contributions = defaultdict(list)
        newborn = []
        for obs, target, match in zip(surfels, event['targets'], event['matches']):
            if match >= 0:
                if target != match or not 0 <= target < old_n:
                    raise ValueError('Matched target did not exist before this frame')
                contributions[target].append(obs.position)
            else:
                if target != old_n + len(newborn):
                    raise ValueError('Birth IDs do not preserve observation order')
                newborn.append(obs)
        for target, values in contributions.items():
            if frame in memory.mapping[target]:
                raise ValueError('Repeated frame event')
            if position_rule == 'frame_mean':
                c = memory.counts[target]
                memory.surfels[target].position = (
                    memory.surfels[target].position * c + np.mean(values, axis=0)) / (c + 1)
            memory.counts[target] += 1
            memory.mapping[target].append(frame)
        for obs in newborn:
            target = len(memory.surfels)
            memory.surfels.append(clone(obs))
            memory.counts.append(1)
            memory.mapping[target] = [frame]
        if len(memory.surfels) != event['new_n']:
            raise ValueError('Wrong number of points after replay')
    return memory


def arrays(memory):
    return dict(points=memory.points, normals=np.array([s.normal for s in memory.surfels]),
                radii=np.array([s.radius for s in memory.surfels]),
                colors=np.array([s.color for s in memory.surfels]), counts=np.array(memory.counts))


def decision_trace(kernel, optical_query, counts, nms=True):
    """Instrument original expanded-candidate sorting/NMS, or pure no-NMS control.

    nms=False deliberately does NOT call the official false branch, which forces
    the last historical frame. No deduplication before float32 torch.argsort.
    """
    query = torch.tensor(average_camera_pose(torch.tensor(
        optical_to_vmem(optical_query)[None], dtype=torch.float64)), dtype=torch.float64)
    candidate_ids = [int(frame) for frame, count in counts for _ in range(int(count))]
    if not candidate_ids:
        raise ValueError('Empty candidate pool')
    distances = [float(kernel.geodesic_distance(
        query, torch.tensor(kernel.c2ws[f], dtype=torch.float64), .1)) for f in candidate_ids]
    distances32 = torch.tensor(distances, dtype=torch.float32)
    order = torch.argsort(distances32).tolist()
    ranked = [candidate_ids[i] for i in order]
    maximum = min(4, len(candidate_ids), len(kernel.c2ws))
    chosen, steps = [ranked[0]], []
    threshold = float(kernel.initial_threshold)
    if nms:
        while len(chosen) < maximum and threshold >= 1e-5:
            for frame in ranked[1:]:
                if len(chosen) >= maximum:
                    break
                comparisons = []
                rejected = False
                for selected in chosen:
                    d = float(kernel.geodesic_distance(
                        torch.tensor(kernel.c2ws[frame], dtype=torch.float64),
                        torch.tensor(kernel.c2ws[selected], dtype=torch.float64), .1))
                    comparisons.append([selected, d])
                    if d < threshold:
                        rejected = True
                        break
                steps.append(dict(frame=frame, threshold=threshold,
                                  comparisons=comparisons, accepted=not rejected))
                if not rejected:
                    chosen.append(frame)
            if len(chosen) < maximum:
                steps.append(dict(relax_from=threshold, relax_to=threshold/1.2))
                threshold /= 1.2
        if len(chosen) < maximum:
            available = [i for i in ranked if i not in chosen]
            added = available[:maximum-len(chosen)]
            chosen.extend(added)
            steps.append(dict(fallback_added=added))
    else:
        for frame in ranked[1:]:
            if frame not in chosen:
                chosen.append(frame)
            if len(chosen) == maximum:
                break
    if len(chosen) != 4 or len(set(chosen)) != 4 or any(not 0 <= f < 20 for f in chosen):
        raise ValueError('Readout did not produce four unique historical IDs')
    return dict(selected=chosen, expanded_candidates=candidate_ids, sorted_frames=ranked,
                distances_float32=distances32.tolist(), nms=nms,
                expanded_adjacent_pose_ties=int((np.diff(np.sort(distances32.numpy())) == 0).sum()),
                initial_threshold=float(kernel.initial_threshold), steps=steps)
