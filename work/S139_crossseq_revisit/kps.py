"""KPS: known-pose dense scale initialisation for VMem's CUT3R global alignment (S135).

VMem presets every camera pose, but dust3r's MST init still recovers views 1..N-1 by PnP and fixes the metric scale
by similarity-registering those PnP camera centres to the known ones. On short baselines (a few cm) that is badly
conditioned, and on low-confidence frames PnP fails and falls back to identity (S133).

KPS uses the known relative poses directly. View j's CUT3R points P, expressed in view 0's frame in CUT3R units,
satisfy x_j ∝ R_j0 P + σ t_j0, where σ (CUT3R units per metre) is the only unknown. Projection is invariant to
positive scaling, so σ is identified by the dense reprojection of P into view j: one scalar over ~10^5 points
instead of a similarity transform over 5 noisy camera centres. Focal length is solved in closed form per σ.
"""
import numpy as np
import torch

SIGMA_GRID = np.geomspace(1e-3, 1e3, 241)


def _proj_residual(P, pix, R, t, sigma, pp, f_fixed=None):
    """Median reprojection residual (px) and focal for one view at scale sigma (focal solved unless f_fixed)."""
    X = P @ R.T + sigma * t
    z = X[:, 2]
    ok = z > 1e-6
    if ok.sum() < 50:
        return np.inf, np.nan
    a = (pix[ok] - pp)                      # pixel offsets
    b = X[ok, :2] / z[ok, None]             # normalised coordinates
    f = float(f_fixed) if f_fixed is not None else float((a * b).sum() / max((b * b).sum(), 1e-12))
    if f <= 0:
        return np.inf, np.nan
    r = np.linalg.norm(a - f * b, axis=1)
    # points behind the camera count as maximal error so a sigma cannot win by discarding them
    frac_bad = 1.0 - ok.mean()
    return float(np.median(r) + 1e3 * frac_bad), f


def estimate_sigma(views, sigma_grid=SIGMA_GRID, refine=True):
    """views: list of dicts with P (N,3) points of view j in view-0 frame (CUT3R units), pix (N,2) their pixels in
    view j, R (3,3), t (3,) known metric transform view0 -> view j, pp (2,). Returns sigma, per-view focals, curve."""
    def total(sig):
        res = [_proj_residual(v['P'], v['pix'], v['R'], v['t'], sig, v['pp'], v.get('f')) for v in views]
        return float(np.mean([r for r, _ in res])), [f for _, f in res]
    curve = np.array([total(s)[0] for s in sigma_grid])
    k = int(np.argmin(curve))
    best = sigma_grid[k]
    if refine:
        lo, hi = sigma_grid[max(k - 1, 0)], sigma_grid[min(k + 1, len(sigma_grid) - 1)]
        for _ in range(40):  # golden-section in log space
            a, b = np.log(lo), np.log(hi)
            m1, m2 = np.exp(a + 0.382 * (b - a)), np.exp(a + 0.618 * (b - a))
            if total(m1)[0] <= total(m2)[0]:
                hi = m2
            else:
                lo = m1
        best = float(np.sqrt(lo * hi))
    err, focals = total(best)
    return float(best), focals, err, curve


def pixel_grid(H, W):
    u, v = np.meshgrid(np.arange(W, dtype=np.float64), np.arange(H, dtype=np.float64))
    return np.stack([u, v], -1)


def install(IIP, log=None, max_points=20000, seed=0, known_K=None):
    """Monkeypatch dust3r's init_minimum_spanning_tree with KPS when all poses are known and edges form a star
    rooted at view 0 (VMem's construction). Otherwise fall back to the original init. `log` collects diagnostics.
    known_K: optional 3x3 intrinsics on the CUT3R image grid (KPS-K); then focal and principal point are fixed."""
    orig_init = IIP.init_minimum_spanning_tree

    @torch.no_grad()
    def kps_init(self, **kw):
        nkp, known_msk, known = IIP.get_known_poses(self)
        star = all(i == 0 for i, _ in self.edges)
        if not (int(nkp) == self.n_imgs and star):
            if log is not None:
                log.append({'kps': 'FALLBACK', 'nkp': int(nkp), 'star': bool(star)})
            return orig_init(self, **kw)
        device = self.device
        pts3d, _, im_focals, _ = IIP.minimum_spanning_tree(
            self.imshapes, self.edges, self.pred_i, self.pred_j, self.conf_i, self.conf_j, self.im_conf,
            self.min_conf_thr, device, has_im_poses=self.has_im_poses, verbose=self.verbose, **kw)
        T = known.detach().cpu().double().numpy()            # c2w, metric, VMem-transformed convention
        rng = np.random.default_rng(seed)
        views = []
        for j in range(1, self.n_imgs):
            H, W = self.imshapes[j]
            P = pts3d[j].detach().cpu().double().numpy().reshape(-1, 3)
            conf = self.im_conf[j].detach().cpu().double().numpy().ravel()
            thr = min(3.0, float(np.median(conf)))
            idx = np.flatnonzero(conf > thr)
            if len(idx) > max_points:
                idx = rng.choice(idx, max_points, replace=False)
            Tj0 = np.linalg.inv(T[j]) @ T[0]
            v = {'P': P[idx], 'pix': pixel_grid(H, W).reshape(-1, 2)[idx], 'R': Tj0[:3, :3],
                 't': Tj0[:3, 3], 'pp': np.array([W / 2, H / 2])}
            if known_K is not None:
                v['pp'] = np.array([known_K[0, 2], known_K[1, 2]]); v['f'] = 0.5 * (known_K[0, 0] + known_K[1, 1])
            views.append(v)
        sigma, focals, err, _ = estimate_sigma(views)
        # metric world points from the root frame, depths w.r.t. the KNOWN poses
        T0 = torch.tensor(T[0], dtype=torch.float32, device=device)
        world = []
        for i in range(self.n_imgs):
            Pi = pts3d[i] / sigma
            world.append(Pi @ T0[:3, :3].T + T0[:3, 3])
        for e, (i, j) in enumerate(self.edges):
            i_j = IIP.edge_str(i, j)
            s, R, Tt = IIP.rigid_points_registration(self.pred_i[i_j], world[i], conf=self.conf_i[i_j])
            self._set_pose(self.pw_poses, e, R, Tt, scale=s)
        for i in range(self.n_imgs):
            Ti = torch.tensor(T[i], dtype=torch.float32, device=device)
            depth = IIP.geotrf(IIP.inv(Ti), world[i])[..., 2]
            self._set_depthmap(i, depth)
            f = (0.5 * (known_K[0, 0] + known_K[1, 1]) if known_K is not None
                 else (im_focals[0] if i == 0 else focals[i - 1]))
            if f is not None and np.isfinite(f):
                self._set_focal(i, float(f))
        if log is not None:
            log.append({'kps': 'OK', 'known_K': known_K is not None, 'sigma': sigma, 'metres_per_unit': 1.0 / sigma, 'median_reproj_px': err,
                        'focals': [None if f is None else float(f) for f in [im_focals[0]] + list(focals)]})

    IIP.init_minimum_spanning_tree = kps_init
    return kps_init
