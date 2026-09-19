"""RGB-D component experiment; this is not the full VMem model pipeline.

The matching order equals the upstream single-leaf control, using cKDTree only
to accelerate exact candidate enumeration. frame_mean is a simple comparator.
"""
from dataclasses import dataclass, field
import time
import numpy as np
from scipy.spatial import cKDTree
from vmem_memory_kernel import Surfel


def make_surfels(depth_m, rgb, c2w, stride=16, intrinsics=(525.,525.,319.5,239.5),
                 edge_threshold=.05, initial_bias_m=0.):
    """Estimate normal at adjacent original pixels, then sample the grid.

    Bias is an injected shift along the source camera's +z axis, applied AFTER
    normals/radii have been computed; it is not a learned depth prediction.
    """
    fx, fy, cx, cy = intrinsics
    h,w = depth_m.shape
    vv,uu = np.mgrid[0:h:stride, 0:w:stride]
    u,v = uu.ravel(),vv.ravel()
    u,v = u[(u<w-1)&(v<h-1)],v[(u<w-1)&(v<h-1)]
    z, zr, zd = depth_m[v,u], depth_m[v,u+1],depth_m[v+1,u]
    valid = (z>0)&(zr>0)&(zd>0)&np.isfinite(z+zr+zd)
    valid &= (np.abs(zr-z)<=edge_threshold)&(np.abs(zd-z)<=edge_threshold)
    u,v,z,zr,zd = [a[valid] for a in (u,v,z,zr,zd)]
    p = np.column_stack(((u-cx)*z/fx,(v-cy)*z/fy,z))
    pr = np.column_stack(((u+1-cx)*zr/fx,(v-cy)*zr/fy,zr))
    pd = np.column_stack(((u-cx)*zd/fx,(v+1-cy)*zd/fy,zd))
    n = np.cross(pr-p,pd-p)
    length = np.linalg.norm(n,axis=1)
    valid = length>1e-12
    p,n,z,u,v = [a[valid] for a in (p,n,z,u,v)]
    n /= length[valid,None]
    rays = p/np.linalg.norm(p,axis=1)[:,None]
    cosine = (rays*n).sum(axis=1)
    n[cosine<0] *= -1
    radii = .5*z / ((fx+fy)/2/stride) / (.2+.8*np.abs(cosine))
    p[:,2] += initial_bias_m
    world = p@c2w[:3,:3].T + c2w[:3,3]
    nw = n@c2w[:3,:3].T
    return [Surfel(a,b,float(r),c.astype(float)/255.)
            for a,b,r,c in zip(world,nw,radii,rgb[v,u])]


@dataclass
class Memory:
    method: str = 'first_write'
    surfels: list = field(default_factory=list)
    mapping: dict = field(default_factory=dict)
    counts: list = field(default_factory=list)
    records: list = field(default_factory=list)

    def add(self, new_surfels, frame_id, position_threshold=None, normal_threshold=.6):
        if self.method not in ('first_write','frame_mean'):
            raise ValueError(self.method)
        started = time.perf_counter()
        old_n = len(self.surfels)
        radii = np.asarray([s.radius for s in self.surfels+new_surfels])
        threshold = position_threshold
        if threshold is None:
            threshold = float(radii.mean()+.5*radii.std()) if len(radii) else .025
        if threshold<0:
            raise ValueError('Negative position threshold')
        p = np.asarray([s.position for s in self.surfels],dtype=float).reshape(-1,3)
        n = np.asarray([s.normal for s in self.surfels],dtype=float).reshape(-1,3)
        tree = cKDTree(p) if old_n else None
        matches, pending, contributions = [], [], {}
        for obs in new_surfels:
            candidates = sorted(tree.query_ball_point(obs.position,np.nextafter(threshold,np.inf))) if tree else []
            match = -1
            for idx in candidates:
                # Explicit comparison mirrors the official norm and strict normal test.
                if np.linalg.norm(p[idx]-obs.position)<=threshold and np.dot(n[idx],obs.normal)>normal_threshold:
                    match = int(idx)
                    break
            matches.append(match)
            if match<0:
                pending.append(obs)
            else:
                if frame_id not in self.mapping[match]:
                    self.mapping[match].append(frame_id)
                contributions.setdefault(match,[]).append(np.asarray(obs.position))
        # Frozen old positions for the whole frame; never mutate under a stale tree.
        for idx, observations in contributions.items():
            if self.method=='frame_mean':
                frame_centroid = np.mean(observations,axis=0)
                count = self.counts[idx]
                self.surfels[idx].position = (p[idx]*count+frame_centroid)/(count+1)
            self.counts[idx] += 1
        for obs in pending:
            idx = len(self.surfels)
            self.mapping[idx] = [int(frame_id)]
            self.surfels.append(Surfel(np.array(obs.position).copy(),np.array(obs.normal).copy(),
                                       float(obs.radius),np.array(obs.color).copy() if obs.color is not None else None))
            self.counts.append(1)
        record = dict(frame_id=int(frame_id),input_points=len(new_surfels),old_points=old_n,
                      merged_points=sum(i>=0 for i in matches),new_points=len(pending),
                      total_points=len(self.surfels),position_threshold_m=threshold,
                      radius_m_quantiles=np.quantile(radii,[0,.5,.9,1]).tolist() if len(radii) else [],
                      elapsed_seconds=time.perf_counter()-started,
                      updated_existing_points=len(contributions) if self.method=='frame_mean' else 0)
        self.records.append(record)
        return matches

    @property
    def points(self):
        return np.asarray([s.position for s in self.surfels],dtype=float).reshape(-1,3)

    def save(self,path):
        # Ragged provenance is written separately by the caller as JSON.
        np.savez_compressed(path,points=self.points,
                            normals=np.asarray([s.normal for s in self.surfels]),
                            radii=np.asarray([s.radius for s in self.surfels]),
                            counts=np.asarray(self.counts))
