"""Artificial codec component check: four 32x32 frames, no model or dataset."""
from pathlib import Path
import ast, datetime, hashlib, importlib.metadata as md, json, os, resource, socket, subprocess, sys, time, traceback
sys.dont_write_bytecode = True
W = Path(__file__).resolve().parent
R = W.parents[1]
O = W / 'attempt1'
O.mkdir(exist_ok=False)
start = time.perf_counter()
utc = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
report = {'schema': 's20-artificial-codec-smoke-v1', 'status': 'RUNNING', 'started_utc': utc(), 'checks': [], 'stage': 'start', 'denied_events': [], 'input_kind': 'SYNTHETIC_FOUR_SOLID_COLOR_FRAMES', 'real_photo_decodes': 0, 'weights_read': 0, 'model_constructions': 0, 'inferences': 0, 'GT_reads': 0}
def check(name, condition):
    report['checks'].append({'name': name, 'pass': bool(condition)})
    assert condition, name
def progress(stage):
    report['stage'] = stage
    (O / 'progress.json').write_text(json.dumps(report, indent=2) + '\n')
def audit(event, args):
    if event.startswith('socket.') and event not in ('socket.__new__', 'socket.gethostname'):
        report['denied_events'].append(event)
        raise RuntimeError('No network in codec smoke')
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        p = Path(os.fsdecode(args[0])).resolve()
        if p.suffix.lower() in {'.pth', '.pt', '.ckpt', '.safetensors'} or p.is_relative_to(R / 'results') or p.is_relative_to(R / 'data'):
            report['denied_events'].append(str(p))
            raise RuntimeError('No weight or dataset reads in codec smoke')
sys.addaudithook(audit)
os.environ.update(PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_IMPLICIT_TOKEN='1', KORNIA_CHECK_VERSION='0', OMP_NUM_THREADS='8', MKL_NUM_THREADS='8')
sys.path[:0] = [str(R / 'work/S20_environment/site-packages'), str(R / 'work/S17C_environment/site-packages')]
try:
    contract = json.loads((W / 'contract.json').read_text())
    for path, expected in contract['identities'].items():
        check('identity ' + path, sha(path) == expected)
    report['contract_sha256'] = sha(W / 'contract.json')
    original = Path(contract['original_util'])
    original_text = original.read_text()
    node = next(n for n in ast.parse(original_text).body if isinstance(n, ast.FunctionDef) and n.name == 'save_video')
    isolated_text = Path(contract['isolated_util']).read_text()
    isolated_node = next(n for n in ast.parse(isolated_text).body if isinstance(n, ast.FunctionDef) and n.name == 'save_video')
    check('original and isolated save_video AST exact', ast.dump(node, include_attributes=False) == ast.dump(isolated_node, include_attributes=False))
    function_text = ast.get_source_segment(original_text, node) + '\n'
    (O / 'original_save_video.py').write_text(function_text)
    report['original_function'] = {'file': str(original), 'file_sha256': sha(original), 'line_start': node.lineno, 'line_end': node.end_lineno, 'function_text_sha256': hashlib.sha256(function_text.encode()).hexdigest(), 'ast_sha256': hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()}
    progress('import dependencies')
    import numpy as np
    import torch, torchvision, av, imageio_ffmpeg
    from torchvision.io import write_video
    torch.set_num_threads(8)
    torch.manual_seed(0)
    report['distributions'] = {}
    for name, expected in [('numpy','1.26.4'), ('torch','2.7.0'), ('torchvision','0.22.0'), ('av','14.2.0'), ('imageio-ffmpeg','0.6.0')]:
        d = md.distribution(name)
        report['distributions'][name] = {'version': d.version, 'path': str(d._path)}
        check(name + ' pinned version', d.version == expected)
        root = R / ('work/S20_environment/site-packages' if name in ('av','imageio-ffmpeg') else '.venv-cut3r')
        check(name + ' intended environment', Path(d._path).resolve().is_relative_to(root))
    report['module_paths'] = {m.__name__: {'path': m.__file__, 'sha256': sha(m.__file__)} for m in (np, torch, torchvision, av, imageio_ffmpeg)}
    report['pyav_library_versions'] = {k: list(v) for k, v in av.library_versions.items()}
    ffmpeg_exe = Path(imageio_ffmpeg.get_ffmpeg_exe()).resolve()
    check('imageio executable bundled in S20 overlay', ffmpeg_exe.is_relative_to(R / 'work/S20_environment/site-packages'))
    q = subprocess.run([str(ffmpeg_exe), '-version'], capture_output=True, text=True, timeout=5)
    report['imageio_ffmpeg_version_probe'] = {'path': str(ffmpeg_exe), 'sha256': sha(ffmpeg_exe), 'returncode': q.returncode, 'stdout': q.stdout, 'stderr': q.stderr, 'used_by_original_writer': False}
    check('imageio bundled FFmpeg version invocation', q.returncode == 0)
    namespace = {'write_video': write_video}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(original), 'exec'), namespace)
    colors = np.array([[220,30,30], [30,220,30], [30,30,220], [220,220,30]], dtype=np.uint8)
    input_rgb = np.broadcast_to(colors[:,None,None,:], (4,32,32,3)).copy()
    np.savez_compressed(O / 'synthetic_input.npz', rgb_uint8=input_rgb)
    video = torch.from_numpy(input_rgb).permute(0,3,1,2).contiguous()
    progress('original save_video encode')
    encode_start = time.perf_counter()
    namespace['save_video'](video, O / 'SYNTHETIC_four_colors.mp4', fps=10)
    report['encode_seconds'] = time.perf_counter() - encode_start
    progress('PyAV decode and checks')
    frames, pts, times, bases = [], [], [], []
    with av.open(str(O / 'SYNTHETIC_four_colors.mp4')) as container:
        report['stream_count'] = len(container.streams.video)
        stream = container.streams.video[0]
        report['stream'] = {'width': stream.width, 'height': stream.height, 'codec': stream.codec_context.name, 'average_rate': str(stream.average_rate), 'time_base': str(stream.time_base), 'duration': stream.duration}
        for frame in container.decode(video=0):
            frames.append(frame.to_ndarray(format='rgb24'))
            pts.append(frame.pts)
            times.append(float(frame.time))
            bases.append(str(frame.time_base))
    decoded = np.stack(frames)
    np.savez_compressed(O / 'synthetic_decoded.npz', rgb_uint8=decoded)
    means = decoded.mean(axis=(1,2))
    costs = ((means[:,None,:] - colors[None,:,:].astype(float))**2).sum(axis=2)
    matched = costs.argmin(axis=1).tolist()
    check('four decoded frames', len(frames) == 4)
    check('dimensions and channels', decoded.shape == (4,32,32,3))
    check('H264 codec', report['stream']['codec'] == 'h264')
    check('original ten frames per second', report['stream']['average_rate'] == '10')
    check('timestamp present', all(x is not None for x in pts))
    check('timestamp strictly increasing', all(pts[i+1] > pts[i] for i in range(3)))
    check('timestamp spacing 0.1s', bool(np.allclose(times, [0.,.1,.2,.3], rtol=0, atol=1e-6)))
    check('fixed color temporal order', matched == [0,1,2,3])
    check('lossy mean color error <=15 per channel', bool(np.max(np.abs(means-colors.astype(float))) <= 15))
    hashes = [hashlib.sha256(x.tobytes()).hexdigest() for x in frames]
    check('all four decoded frames different', len(set(hashes)) == 4)
    report['decode'] = {'frame_count': len(frames), 'shape': list(decoded.shape), 'pts': pts, 'time_seconds': times, 'time_bases': bases, 'mean_rgb': means.tolist(), 'nearest_fixed_color_indices': matched, 'max_mean_channel_error': float(np.max(np.abs(means-colors.astype(float)))), 'decoded_frame_sha256': hashes, 'decoded_equals_input_exactly': bool(np.array_equal(decoded,input_rgb)), 'exact_pixel_equality_required': False}
    check('source unchanged after run', sha(original) == contract['identities'][str(original)])
    check('no denied data/network accesses', not report['denied_events'])
    report['status'] = 'PASS_SYNTHETIC_CODEC_ONLY'
except BaseException:
    report['status'] = 'FAIL_SYNTHETIC_CODEC_ONLY'
    report['failure'] = traceback.format_exc()
finally:
    report['ended_utc'] = utc()
    report['elapsed_seconds'] = time.perf_counter()-start
    report['peak_rss_bytes_macos_self'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report['script_sha256'] = sha(__file__)
    report['checks_passed'] = sum(c['pass'] for c in report['checks'])
    report['files'] = {p.name: {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in O.iterdir() if p.is_file() and p.name != 'run_metadata.json'}
    (O / 'run_metadata.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['status','checks_passed','elapsed_seconds','peak_rss_bytes_macos_self']}))
    if report.get('failure'): print(report['failure'])
sys.exit(0 if report['status'].startswith('PASS') else 1)
