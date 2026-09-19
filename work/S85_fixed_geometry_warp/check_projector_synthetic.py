"""One bounded artificial arithmetic run; no scientific input archives."""
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import time
import traceback

HERE = Path(__file__).resolve().parent
OUTPUT = HERE/"AUTHOR_SYNTHETIC_01.json"


def main():
    if OUTPUT.exists():
        raise FileExistsError("Do not overwrite an already executed test receipt")
    start = time.perf_counter()
    rec = dict(started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
               status="STARTED", real_array_reads=0, model_calls=0,
               real_projection_batches=0, checks=[])
    rec["runner_sha256"] = hashlib.sha256((HERE/"project_fixed_geometry.py").read_bytes()).hexdigest()
    rec["checker_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    try:
        spec = importlib.util.spec_from_file_location("s85_projector", HERE/"project_fixed_geometry.py")
        p = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(p)
        np = p.np
        I = np.eye(4)
        Ki = np.array([[420., 0, 255.6], [0, 420., 191.6], [0, 0, 1.]])
        Kt = np.array([[630., 0, 287.4], [0, 630., 287.4], [0, 0, 1.]])
        def close(actual, expected, tol=1e-10):
            np.testing.assert_allclose(actual, expected, atol=tol, rtol=0)
        def note(name, **kw):
            rec["checks"].append(dict(name=name, **kw))

        # Fixture 1: computed FP64 projection and literal-footprint math are separate.
        status, xyz, uv = p.project_points([[200, 129]], [2.], Ki, I, I, Kt, (576, 576))
        assert status.tolist() == [0]
        close(uv, [[204, 193.5]]); close(xyz[:, 2], [2])
        computed_idx, computed_weight = p.footprints(uv, status == 0, (576, 576))
        idx, weight = p.footprints(np.array([[204., 193.5]]), np.array([True]), (576, 576))
        assert idx.tolist() == [[193*576+204, -1, 194*576+204, -1]]
        close(weight, [[.5, 0, .5, 0]], 0)
        note("same_camera_and_literal_half_pixel", projected_uv=uv.tolist(),
             computed_positive_footprints=int((computed_idx >= 0).sum()),
             computed_weights=computed_weight.tolist(), literal_positive_footprints=2,
             note="No epsilon or snapping; FP64 arithmetic may produce extra tiny positive footprints.")
        # Preserve an artificial FP32-origin principal point instead of snapping.
        Ktf = Kt.astype(np.float32).astype(np.float64)
        _, _, uvf = p.project_points([[200, 129]], [2.], Ki, I, I, Ktf, (576, 576))
        close(uvf-uv, [[float(Ktf[0, 2])-287.4, float(Ktf[1, 2])-287.4]])
        assert not np.array_equal(uv, uvf)
        note("fp32_origin_K_preserved", delta_uv=(uvf-uv).tolist())

        # Fixture 2: all source depths positive, but only one positive target depth.
        Pt = I.copy(); Pt[2, 3] = 2
        st, xyz, uv = p.project_points([[200, 128]]*3, [1., 2., 3.], Ki, I, Pt, Kt, (576, 576))
        assert st.tolist() == [4, 4, 0]
        close(xyz[:, 2], [-1, 0, 1])
        assert np.isnan(uv[:2]).all()
        close(uv[2], [37.2, 1.2])
        idx, wt = p.footprints(uv, st == 0, (576, 576))
        assert (idx[:2] == -1).all()
        assert idx[2].tolist() == [1*576+37, 1*576+38, 2*576+37, 2*576+38]
        close(wt[2], [.64, .16, .16, .04])
        note("target_positive_zero_negative", statuses=st.tolist(), target_Z=xyz[:, 2].tolist())

        # Fixture 3: exact depth ties, history priority, source-pixel priority and RGB.
        color = np.zeros((4, 10, 3), np.float32)
        color[0, 0] = [1, 0, 0]; color[2, 9] = [0, 1, 0]
        color[3, 8] = [0, 0, 1]; color[3, 3] = [1, 1, 0]
        tgt = np.full(4, 100*576+100, np.int32)
        buf = p.hard_buffer(tgt, np.array([2., 1, 1, 1]),
                            np.array([0, 2, 3, 3], np.int8),
                            np.array([0, 9, 8, 3], np.int32),
                            np.zeros(4, np.uint8), np.array([.1, .4, .2, .3]),
                            np.array([12, 13, 18, 19]), color, (576, 576))
        assert buf["winner_history_id"][100, 100] == 19
        assert buf["winner_pixel_id"][100, 100] == 3
        assert buf["winner_Z"][100, 100] == buf["second_candidate_Z"][100, 100] == 1
        assert buf["second_candidate_pixel_id"][100, 100] == 8
        assert buf["candidate_rank"].tolist() == [0, 1, 2, 3]
        assert buf["candidate_count"][100, 100] == 4
        assert buf["candidate_winner"].tolist() == [True, False, False, False]
        np.testing.assert_array_equal(buf["warp_rgb"][100, 100], [1, 1, 0])
        assert not buf["mask"][0, 0] and (buf["warp_rgb"][0, 0] == 0).all()
        assert buf["winner_history_id"][0, 0] == -1 and np.isnan(buf["winner_Z"][0, 0])
        note("hard_zbuffer_full_tie_order_direct_RGB", winner_history=19, winner_pixel=3,
             second_pixel=8, second_Z=1, candidate_count=4)

        # Necessary boundaries: endpoint footprint, continuous outside, rotation direction.
        idx, wt = p.footprints(np.array([[575., 575.], [0., 0.]]),
                              np.array([True, True]), (576, 576))
        assert idx.tolist() == [[331775, -1, -1, -1], [0, -1, -1, -1]]
        close(wt, [[1, 0, 0, 0], [1, 0, 0, 0]], 0)
        Pt = I.copy(); Pt[0, 3] = .0001
        st, _, _ = p.project_points([[0, 0]], [1.], np.eye(3), I, Pt, np.eye(3), (2, 2))
        assert st.tolist() == [5]  # A kernel could touch x=0, but center-domain policy rejects it.
        Pt = I.copy(); Pt[:3, :3] = [[0, 0, 1], [0, 1, 0], [-1, 0, 0]]
        KR = np.array([[1., 0, 2], [0, 1, 2], [0, 0, 1]])
        st, xyz, uv = p.project_points([[2, 0]], [1.], np.eye(3), I, Pt, KR, (5, 5))
        assert st.tolist() == [0]; close(xyz, [[-1, 0, 2]], 0); close(uv, [[1.5, 2]], 0)
        note("endpoints_continuous_outside_rotation", passed=True)
        st, _, _ = p.project_points([[0, 0]]*5, [np.nan, np.inf, 0., -1., 1.],
                                     np.eye(3), I, I, np.eye(3), (2, 2))
        assert st.tolist() == [1, 1, 2, 2, 0]
        st, _, _ = p.project_points([[2, 1]], [1e308], np.eye(3), I, I, np.eye(3), (2, 2))
        assert st.tolist() == [3]
        note("invalid_sources_and_nonfinite_transform", passed=True)

        # Tiny full-target integration, including all-hole output and invalid RGB failure.
        depth = np.ones((4, 1, 1), np.float32)
        colors = np.array([[[[1., 0, 0]]], [[[0., 1, 0]]],
                           [[[0., 0, 1]]], [[[1., 1, 0]]]], np.float32)
        Ks = np.tile(np.eye(3), (4, 1, 1))
        Ps = np.tile(I, (4, 1, 1))
        ids = np.array([12, 13, 18, 19])
        out, summary = p.project_target(depth, colors, Ks, Ps, ids, I, np.eye(3), (2, 2))
        assert summary["source_points"] == 4 and len(summary["pairs"]) == 4
        assert summary["valid_footprints"] == 4 and summary["winners"] == 1
        assert summary["losers"] == 3 and summary["holes"] == 3
        assert int(out["footprint_winner"].sum()) == 1
        assert out["footprint_winner"][3, 0, 0]
        np.testing.assert_array_equal(out["warp_rgb"][0, 0], [1, 1, 0])
        Pt = I.copy(); Pt[2, 3] = 2
        out, summary = p.project_target(depth, colors, Ks, Ps, ids, Pt, np.eye(3), (2, 2))
        assert summary["valid_footprints"] == 0 and summary["holes"] == 4
        assert out["candidate_Z"].size == 0 and (out["source_status"] == 4).all()
        assert np.isnan(out["second_candidate_Z"]).all() and (out["warp_rgb"] == 0).all()
        bad = colors.copy(); bad[0, 0, 0, 0] = 1.01
        try:
            p.project_target(depth, bad, Ks, Ps, ids, I, np.eye(3), (2, 2))
            raise AssertionError("out-of-range color accepted")
        except ValueError as exc:
            assert str(exc) == "color values"
        note("tiny_full_target_collisions_holes_invalid_RGB", passed=True)
        rec["status"] = "PASS_ARTIFICIAL_ONLY"
        rec["numpy_version"] = np.__version__
        rec["numerical_tolerance"] = dict(atol=1e-10, rtol=0, meaning="Artificial arithmetic only")
    except BaseException as exc:
        rec["status"] = "FAILED"
        rec["error"] = dict(type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc())
        raise
    finally:
        rec["completed_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        rec["elapsed_seconds"] = time.perf_counter()-start
        OUTPUT.write_text(json.dumps(rec, ensure_ascii=False, indent=2, allow_nan=False)+"\n")


if __name__ == "__main__":
    main()
