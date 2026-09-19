def listify(elems):
    return [x for e in elems for x in e]

def collate_with_cat(whatever, lists=False):
    if isinstance(whatever, dict):
        return {k: collate_with_cat(vals, lists=lists) for k, vals in whatever.items()}
    elif isinstance(whatever, (tuple, list)):
        if len(whatever) == 0:
            return whatever
        elem = whatever[0]
        T = type(whatever)
        if elem is None:
            return None
        if isinstance(elem, (bool, float, int, str)):
            return whatever
        if isinstance(elem, tuple):
            return T((collate_with_cat(x, lists=lists) for x in zip(*whatever)))
        if isinstance(elem, dict):
            return {k: collate_with_cat([e[k] for e in whatever], lists=lists) for k in elem}
        if isinstance(elem, torch.Tensor):
            return listify(whatever) if lists else torch.cat(whatever)
        if isinstance(elem, np.ndarray):
            return listify(whatever) if lists else torch.cat([torch.from_numpy(x) for x in whatever])
        return sum(whatever, T())

def prepare_input_from_pil(pil_images, size, square_ok=False, raymaps=None, raymap_mask=None, revisit=1, update=True):
    """
    Prepare input views for inference from a list of PIL images.

    Args:
        pil_images (list): List of PIL image objects.
        size (int): Target image size.
        raymaps (list, optional): List of ray maps.
        raymap_mask (list, optional): Flags indicating valid ray maps.
        revisit (int): How many times to revisit each view.
        update (bool): Whether to update the state on revisits.

    Returns:
        list: A list of view dictionaries.
    """
    from src.dust3r.utils.image import _resize_pil_image, ImgNorm, exif_transpose
    import PIL
    imgs = []
    for i, img in enumerate(pil_images):
        img = exif_transpose(img).convert('RGB')
        W1, H1 = img.size
        if size == 224:
            img = _resize_pil_image(img, round(size * max(W1 / H1, H1 / W1)))
        else:
            img = _resize_pil_image(img, size)
        W, H = img.size
        cx, cy = (W // 2, H // 2)
        if size == 224:
            half = min(cx, cy)
            img = img.crop((cx - half, cy - half, cx + half, cy + half))
        else:
            halfw, halfh = (2 * cx // 16 * 8, 2 * cy // 16 * 8)
            if not square_ok and W == H:
                halfh = 3 * halfw / 4
            img = img.crop((cx - halfw, cy - halfh, cx + halfw, cy + halfh))
        imgs.append({'img': ImgNorm(img)[None], 'true_shape': np.int32([img.size[::-1]]), 'idx': i, 'instance': str(i)})
    views = []
    num_views = len(imgs)
    for i in range(num_views):
        view = {'img': imgs[i]['img'], 'ray_map': torch.full((imgs[i]['img'].shape[0], 6, imgs[i]['img'].shape[-2], imgs[i]['img'].shape[-1]), torch.nan), 'true_shape': torch.from_numpy(imgs[i]['true_shape']), 'idx': i, 'instance': str(i), 'camera_pose': torch.from_numpy(np.eye(4).astype(np.float32)).unsqueeze(0), 'img_mask': torch.tensor(True).unsqueeze(0), 'ray_mask': torch.tensor(False).unsqueeze(0), 'update': torch.tensor(True).unsqueeze(0), 'reset': torch.tensor(False).unsqueeze(0)}
        views.append(view)
    return views

def prepare_output(output, poses, depths, lr, niter, outdir, device, save_flag=False):
    from cloud_opt.dust3r_opt import global_aligner, GlobalAlignerMode
    with torch.enable_grad():
        mode = GlobalAlignerMode.PointCloudOptimizer
        scene = global_aligner(output, device=device, mode=mode, verbose=True)
        if depths is not None:
            scene.preset_depth(depths)
        if poses is not None:
            scene.preset_pose(poses)
        loss = scene.compute_global_alignment(init='mst', niter=niter, schedule='linear', lr=lr)
    scene.clean_pointcloud()
    pts3d = scene.get_pts3d()
    depths = scene.get_depthmaps()
    poses = scene.get_im_poses()
    focals = scene.get_focals()
    pps = scene.get_principal_points()
    confs = scene.get_conf(mode='none')
    pts3ds_other = [pts.detach().cpu().unsqueeze(0) for pts in pts3d]
    depths = [d.detach().cpu().unsqueeze(0) for d in depths]
    colors = [torch.from_numpy(img).unsqueeze(0) for img in scene.imgs]
    confs = [conf.detach().cpu().unsqueeze(0) for conf in confs]
    cam_dict = {'focal': focals.detach().cpu().numpy(), 'pp': pps.detach().cpu().numpy(), 'R': poses.detach().cpu().numpy()[..., :3, :3], 't': poses.detach().cpu().numpy()[..., :3, 3]}
    if save_flag:
        depths_tosave = torch.cat(depths)
        pts3ds_other_tosave = torch.cat(pts3ds_other)
        conf_self_tosave = torch.cat(confs)
        colors_tosave = torch.cat(colors)
        cam2world_tosave = poses.detach().cpu()
        intrinsics_tosave = torch.eye(3).unsqueeze(0).repeat(cam2world_tosave.shape[0], 1, 1)
        intrinsics_tosave[:, 0, 0] = focals[:, 0].detach().cpu()
        intrinsics_tosave[:, 1, 1] = focals[:, 0].detach().cpu()
        intrinsics_tosave[:, 0, 2] = pps[:, 0].detach().cpu()
        intrinsics_tosave[:, 1, 2] = pps[:, 1].detach().cpu()
        os.makedirs(os.path.join(outdir, 'depth'), exist_ok=True)
        os.makedirs(os.path.join(outdir, 'conf'), exist_ok=True)
        os.makedirs(os.path.join(outdir, 'color'), exist_ok=True)
        os.makedirs(os.path.join(outdir, 'camera'), exist_ok=True)
        for f_id in range(len(depths_tosave)):
            depth = depths_tosave[f_id].cpu().numpy()
            conf = conf_self_tosave[f_id].cpu().numpy()
            color = colors_tosave[f_id].cpu().numpy()
            c2w = cam2world_tosave[f_id].cpu().numpy()
            intrins = intrinsics_tosave[f_id].cpu().numpy()
            np.save(os.path.join(outdir, 'depth', f'{f_id:06d}.npy'), depth)
            np.save(os.path.join(outdir, 'conf', f'{f_id:06d}.npy'), conf)
            iio.imwrite(os.path.join(outdir, 'color', f'{f_id:06d}.png'), (color * 255).astype(np.uint8))
            np.savez(os.path.join(outdir, 'camera', f'{f_id:06d}.npz'), pose=c2w, intrinsics=intrins)
    return (pts3ds_other, colors, depths, confs, cam_dict)

def build_original_output(outputs):
    output = {'view1': [], 'view2': [], 'pred1': [], 'pred2': []}
    edges = []
    for view_id in range(1, len(outputs['views'])):
        output['view1'].append(outputs['views'][0])
        output['view2'].append(outputs['views'][view_id])
        output['pred1'].append(outputs['pred'][0])
        output['pred2'].append(outputs['pred'][view_id])
        edges.append((outputs['views'][0]['idx'], outputs['views'][view_id]['idx']))
    list_of_tuples = edges
    sorted_indices = sorted(range(len(list_of_tuples)), key=lambda x: (list_of_tuples[x][0] > list_of_tuples[x][1], list_of_tuples[x][1] if list_of_tuples[x][0] > list_of_tuples[x][1] else list_of_tuples[x][0], list_of_tuples[x][0] if list_of_tuples[x][0] > list_of_tuples[x][1] else list_of_tuples[x][1]))
    new_output = {'view1': [], 'view2': [], 'pred1': [], 'pred2': []}
    for i in sorted_indices:
        new_output['view1'].append(output['view1'][i])
        new_output['view2'].append(output['view2'][i])
        new_output['pred1'].append(output['pred1'][i])
        new_output['pred2'].append(output['pred2'][i])
    output['view1'] = collate_with_cat(new_output['view1'])
    output['view2'] = collate_with_cat(new_output['view2'])
    output['pred1'] = collate_with_cat(new_output['pred1'])
    output['pred2'] = collate_with_cat(new_output['pred2'])
    return output
