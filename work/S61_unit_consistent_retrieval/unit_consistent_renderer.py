"""Conventional renderer-boundary length normalization; NumPy only."""
from copy import deepcopy
import numpy as np


class EmptyPositiveGeometryError(ValueError):
    """No finite positive camera depth can define a length unit."""


def _finite_array(value, shape, name):
    raw = np.asarray(value)
    if not np.isrealobj(raw):
        raise ValueError(name + ' must be real')
    out = np.array(raw, dtype=np.float64, copy=True)
    if out.shape != shape or not np.isfinite(out).all():
        raise ValueError(name + ' has invalid shape or nonfinite values')
    return out


def render_in_canonical_units(renderer, surfels, pose, focal_lengths, **renderer_kwargs):
    """Return (original maps, unit receipt), with depth measured in median units.

    renderer is an injected, already-bound original function. Surfel objects must
    expose position[3], normal[3], radius; other attributes/IDs are deep-copied.
    pose is the renderer's existing 4x4 c2w, already in its expected convention.
    No axis conversion, filtering, cache update, retries, or frame fallback occurs.
    """
    if not callable(renderer):
        raise TypeError('renderer must be callable')
    camera = _finite_array(pose, (4, 4), 'pose')
    R = camera[:3, :3]
    if (not np.allclose(camera[3], [0., 0., 0., 1.], rtol=0., atol=1e-8)
        or not np.allclose(R.T @ R, np.eye(3), rtol=0., atol=1e-6)
        or not np.isclose(np.linalg.det(R), 1., rtol=0., atol=1e-6)):
        raise ValueError('pose must contain a proper rotation and homogeneous row')
    focal = _finite_array(np.asarray(focal_lengths).reshape(-1), (2,), 'focal_lengths')
    if np.any(focal <= 0):
        raise ValueError('Expected two finite positive focal lengths')
    _finite_array(np.asarray(renderer_kwargs.get('principal_points')).reshape(-1),
                  (2,), 'principal_points')
    for key in ('image_width', 'image_height'):
        value = renderer_kwargs.get(key)
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value <= 0:
            raise ValueError(key + ' must be a positive integer')
    if 'disk_resolution' in renderer_kwargs:
        value = renderer_kwargs['disk_resolution']
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value < 3:
            raise ValueError('disk_resolution must be an integer >= 3')
    originals = list(surfels)
    if not originals:
        raise EmptyPositiveGeometryError('Empty geometry: no positive camera-depth median')
    positions, radii = [], []
    for surfel in originals:
        positions.append(_finite_array(surfel.position, (3,), 'surfel.position'))
        _finite_array(surfel.normal, (3,), 'surfel.normal')  # Zero normals remain unchanged.
        radius = _finite_array(surfel.radius, (), 'surfel.radius').item()
        if radius < 0:
            raise ValueError('surfel.radius must be nonnegative')
        radii.append(radius)
    positions, radii = np.array(positions), np.array(radii)
    camera_points = np.linalg.solve(R, (positions - camera[:3, 3]).T).T
    depths = camera_points[:, 2]
    if not np.isfinite(depths).all():
        raise ValueError('Camera-depth calculation is nonfinite')
    positive = np.sort(depths[depths > 0])
    if not len(positive):
        raise EmptyPositiveGeometryError('No positive camera depth to define the median unit')
    middle = len(positive) // 2
    unit = float(positive[middle] if len(positive) % 2 else
                 positive[middle-1] + (positive[middle]-positive[middle-1])/2.)
    scale = 1. / unit
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        scaled_positions = positions / unit
        scaled_radii = radii / unit
        scaled_translation = camera[:3, 3] / unit
    if (not np.isfinite(scale) or not np.isfinite(scaled_positions).all()
        or not np.isfinite(scaled_radii).all() or not np.isfinite(scaled_translation).all()):
        raise ValueError('Canonical length conversion is not finite')
    copied = deepcopy(originals)
    for i, surfel in enumerate(copied):
        surfel.position = scaled_positions[i].copy()
        surfel.radius = float(scaled_radii[i])
    camera[:3, 3] = scaled_translation
    receipt = dict(length_unit_rule='median_of_all_strictly_positive_camera_z',
                   length_unit_in_input_coordinates=unit, scale_factor=scale,
                   surfel_count=len(originals), positive_depth_count=len(positive),
                   nonpositive_depth_count=len(depths)-len(positive),
                   input_camera_depth_min=float(depths.min()),
                   input_camera_depth_max=float(depths.max()),
                   depth_unit='dimensionless_camera_depth_in_positive_median_units',
                   physical_length_unit='UNKNOWN', renderer_calls=1,
                   geometry_order_and_IDs_preserved=True,
                   normalized_fields=['surfel.position', 'surfel.radius', 'pose.translation'])
    maps = renderer(copied, camera, deepcopy(focal_lengths), **deepcopy(renderer_kwargs))
    if not isinstance(maps, dict) or set(maps) != {'depth', 'surfel_index_map', 'cos_value_map'}:
        raise ValueError('Expected original depth/index/cos maps')
    return maps, receipt
