class OfficialRayFactory:

    @staticmethod
    def generate_pseudo_intrinsics(h, w):
        focal = (h ** 2 + w ** 2) ** 0.5
        return np.array([[focal, 0, w // 2], [0, focal, h // 2], [0, 0, 1]]).astype(np.float32)

    def get_ray_map(self, c2w, h, w, intrinsics=None):
        if intrinsics is None:
            intrinsics = self.generate_pseudo_intrinsics(h, w)
        i, j = np.meshgrid(np.arange(w), np.arange(h), indexing='xy')
        grid = np.stack([i, j, np.ones_like(i)], axis=-1)
        ro = c2w[:3, 3]
        rd = np.linalg.inv(intrinsics) @ grid.reshape(-1, 3).T
        rd = (c2w @ np.vstack([rd, np.ones_like(rd[0])])).T[:, :3].reshape(h, w, 3)
        rd = rd / np.linalg.norm(rd, axis=-1, keepdims=True)
        ro = np.broadcast_to(ro, (h, w, 3))
        ray_map = np.concatenate([ro, rd], axis=-1)
        return ray_map
