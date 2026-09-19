# GIM-World Eq.16 kernel diagnostic

This is a mathematical audit of the formula as written in the GIM-World arXiv HTML (arXiv:2606.02436v1, Eq.16), not a reproduction of the paper's code or empirical results.

For four equally spaced directions on a great circle, with identical positions/times and `sigma_r = pi`, the squared geodesic angular Gaussian has a negative Gram-matrix eigenvalue. This is consistent with the known CVPR 2015 result that a geodesic Gaussian is not generally positive definite on curved manifolds. The result means a GP implementation needs a PSD-safe kernel or an explicit numerical repair; it does not prove that GIM-World's actual code fails or invalidate its reported experiments.
