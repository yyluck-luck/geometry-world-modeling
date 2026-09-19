def forward_recurrent_lighter(self, views, device='cuda', ret_state=False):
    ress = []
    all_state_args = []
    prev_reset = False
    prev_candidate_state_feat = None
    prev_feat_i = None
    state_cov = None
    kalman_stats = None
    update_type = self._resolve_model_update_type()
    need_attn_for_update = self._requires_attn_for_update()
    for i, _view in enumerate(views):
        view = to_gpu(_view, device)
        device = view['img'].device
        batch_size = view['img'].shape[0]
        img_mask = view['img_mask'].reshape(-1, batch_size)
        ray_mask = view['ray_mask'].reshape(-1, batch_size)
        imgs = view['img'].unsqueeze(0)
        ray_maps = view['ray_map'].unsqueeze(0)
        shapes = view['true_shape'].unsqueeze(0) if 'true_shape' in view else torch.tensor(view['img'].shape[-2:], device=device).unsqueeze(0).repeat(batch_size, 1).unsqueeze(0)
        imgs = imgs.view(-1, *imgs.shape[2:])
        ray_maps = ray_maps.view(-1, *ray_maps.shape[2:])
        shapes = shapes.view(-1, 2).to(imgs.device)
        img_masks_flat = img_mask.view(-1)
        ray_masks_flat = ray_mask.view(-1)
        selected_imgs = imgs[img_masks_flat]
        selected_shapes = shapes[img_masks_flat]
        if selected_imgs.size(0) > 0:
            img_out, img_pos, _ = self._encode_image(selected_imgs, selected_shapes)
        else:
            img_out, img_pos = (None, None)
        ray_maps = ray_maps.permute(0, 3, 1, 2)
        selected_ray_maps = ray_maps[ray_masks_flat]
        selected_shapes_ray = shapes[ray_masks_flat]
        if selected_ray_maps.size(0) > 0:
            ray_out, ray_pos, _ = self._encode_ray_map(selected_ray_maps, selected_shapes_ray)
        else:
            ray_out, ray_pos = (None, None)
        shape = shapes
        if img_out is not None and ray_out is None:
            feat_i = img_out[-1]
            pos_i = img_pos
        elif img_out is None and ray_out is not None:
            feat_i = ray_out[-1]
            pos_i = ray_pos
        elif img_out is not None and ray_out is not None:
            feat_i = img_out[-1] + ray_out[-1]
            pos_i = img_pos
        else:
            raise NotImplementedError
        if i == 0:
            state_feat, state_pos = self._init_state(feat_i, pos_i)
            mem = self.pose_retriever.mem.expand(feat_i.shape[0], -1, -1)
            init_state_feat = state_feat.clone()
            init_mem = mem.clone()
        if self.pose_head_flag:
            global_img_feat_i = self._get_img_level_feat(feat_i)
            if i == 0 or prev_reset:
                pose_feat_i = self.pose_token.expand(feat_i.shape[0], -1, -1)
            else:
                pose_feat_i = self.pose_retriever.inquire(global_img_feat_i, mem)
            pose_pos_i = -torch.ones(feat_i.shape[0], 1, 2, device=feat_i.device, dtype=pos_i.dtype)
        else:
            pose_feat_i = None
            pose_pos_i = None
        new_state_feat, dec, self_attn_state, cross_attn_state, self_attn_img, cross_attn_img = self._recurrent_rollout(state_feat, state_pos, feat_i, pos_i, pose_feat_i, pose_pos_i, init_state_feat, img_mask=view['img_mask'], reset_mask=view['reset'], update=view.get('update', None), return_attn=need_attn_for_update)
        out_pose_feat_i = dec[-1][:, 0:1]
        new_mem = self.pose_retriever.update_mem(mem, global_img_feat_i, out_pose_feat_i)
        assert len(dec) == self.dec_depth + 1
        head_input = [dec[0].float(), dec[self.dec_depth * 2 // 4][:, 1:].float(), dec[self.dec_depth * 3 // 4][:, 1:].float(), dec[self.dec_depth].float()]
        res = self._downstream_head(head_input, shape, pos=pos_i)
        res_cpu = to_cpu(res)
        ress.append(res_cpu)
        img_mask = view['img_mask']
        update = view.get('update', None)
        if update is not None:
            update_mask = img_mask & update
        else:
            update_mask = img_mask
        update_mask = update_mask[:, None, None].float()
        if update_type == 'filt3r':
            if i == 0 or prev_reset:
                update_mask1 = update_mask
                state_feat = new_state_feat * update_mask + state_feat * (1 - update_mask)
                state_cov = torch.full_like(new_state_feat[..., 0], self._get_hparam('kalman_p_init', 1.5))
                kalman_stats = None
            else:
                update_mask1, state_cov, kalman_stats = self._compute_kalman_ema_gain_and_cov(update_mask=update_mask, state_cov=state_cov, state_feat=state_feat, new_state_feat=new_state_feat, prev_candidate_state_feat=prev_candidate_state_feat, cross_attn_state=None, feat_i=feat_i, prev_feat_i=None, kalman_stats=kalman_stats, use_nis_correction=False, use_ttt3r_r=False, fixed_r_t=float(self._get_hparam('kalman_fixed_r', 1.0)), kalman_diag_stats=None)
                state_feat = new_state_feat * update_mask1 + state_feat * (1 - update_mask1)
        else:
            update_mask1, state_cov = self._compute_state_update_gain(update_mask=update_mask, new_state_feat=new_state_feat, cross_attn_state=cross_attn_state if need_attn_for_update else None, feat_i=feat_i, prev_candidate_state_feat=prev_candidate_state_feat, prev_feat_i=prev_feat_i, state_cov=state_cov, force_full_update=i == 0 or prev_reset, kalman_diag_stats=None)
            state_feat = new_state_feat * update_mask1 + state_feat * (1 - update_mask1)
        mem = new_mem * update_mask + mem * (1 - update_mask)
        state_feat, mem, state_cov, hard_reset_now = self._apply_stream_reset(state_feat=state_feat, mem=mem, init_state_feat=init_state_feat, init_mem=init_mem, state_cov=state_cov, reset_mask=view['reset'], update_type=update_type)
        prev_reset = hard_reset_now
        if hard_reset_now:
            prev_candidate_state_feat = None
            prev_feat_i = None
            state_cov = None
            kalman_stats = None
        else:
            prev_candidate_state_feat, prev_feat_i = self._advance_prev_buffers(prev_candidate_state_feat, prev_feat_i, new_state_feat, feat_i, update_mask)
    if ret_state:
        return (ress, views, all_state_args)
    return (ress, views)
