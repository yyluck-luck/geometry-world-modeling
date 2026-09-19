#!/usr/bin/env python3
"""Bounded mathematical diagnostic of the GIM-World Eq.16 angular Gaussian kernel.

This is not a reproduction of GIM-World code or a criticism of its reported results.
It checks whether the equation as written is PSD on a simple curved camera-direction set.
"""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

OUT = Path(__file__).with_name('RESULTS.json')
# Four directions on one great circle; p and t are identical so only angular term remains.
theta = np.array([0.0, np.pi/2, np.pi, 3*np.pi/2])
sigma_r = np.pi
ang = np.abs(theta[:, None] - theta[None, :])
ang = np.minimum(ang, 2*np.pi-ang)
K = np.exp(-(ang**2)/(2*sigma_r**2))
evals = np.linalg.eigvalsh(K)
# GP posterior variance expression from Eq.17 for h=pi with A={0, pi/2}.
A = [0, 1]; h = 2
K_AA = K[np.ix_(A,A)]
k_hA = K[h, A]
posterior = float(K[h,h] - k_hA @ np.linalg.solve(K_AA, k_hA))
# Valid chordal RBF comparator on unit-circle directions, same sigma.
v = np.stack([np.cos(theta), np.sin(theta)], axis=1)
d2 = ((v[:,None,:]-v[None,:,:])**2).sum(axis=-1)
K_chord = np.exp(-d2/(2*sigma_r**2))
obj = {
 'created_utc': datetime.now(timezone.utc).isoformat(),
 'status': 'DIAGNOSTIC_ONLY_NOT_GIM_REPRODUCTION',
 'source_formula': 'GIM-World arXiv:2606.02436v1 Eq.16 geodesic angular squared exponential and Eq.17 posterior variance',
 'directions_radians': theta.tolist(), 'sigma_r': sigma_r,
 'angular_kernel': K.tolist(), 'angular_eigenvalues': evals.tolist(),
 'angular_min_eigenvalue': float(evals[0]), 'eq17_subset_A':[0,1], 'eq17_query_h':2,
 'eq17_posterior_variance': posterior,
 'chordal_kernel_eigenvalues': np.linalg.eigvalsh(K_chord).tolist(),
 'assertions': {
   'angular_kernel_indefinite': bool(evals[0] < -1e-12),
   'angular_eq17_posterior_nonnegative_in_this_subset': bool(posterior >= -1e-12),
   'chordal_kernel_psd_here': bool(np.linalg.eigvalsh(K_chord)[0] >= -1e-12),
 },
 'interpretation': 'The written geodesic angular Gaussian can be indefinite on this curved direction set; this is a kernel-formula diagnostic. It does not establish that the authors used this exact configuration in code, that their implementation fails, or that their reported method is invalid. A valid implementation must document PSD handling or use a valid kernel/approximation.',
}
if not obj['assertions']['angular_kernel_indefinite']:
    raise AssertionError(obj['assertions'])
OUT.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'output':str(OUT),'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'angular_min_eigenvalue':obj['angular_min_eigenvalue'],'eq17_posterior_variance':posterior,'assertions':obj['assertions']},ensure_ascii=False))
