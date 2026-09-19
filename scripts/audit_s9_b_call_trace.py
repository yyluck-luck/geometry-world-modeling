#!/usr/bin/env python3
"""Synthetic control-flow audit of pinned VMem; never loads a model or real images."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace as NS

import numpy as np
import torch


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lift(path, name, namespace):
    tree = ast.parse(path.read_text())
    nodes = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(nodes) == 1
    node = nodes[0]
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), namespace)
    return namespace[name], {"start": node.lineno, "end": node.end_lineno}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--vmem", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    began = datetime.now(timezone.utc).isoformat()
    pipeline = a.vmem / "modeling/pipeline.py"
    util = a.vmem / "utils/util.py"
    config = a.vmem / "configs/inference/inference.yaml"
    config_text = config.read_text()
    for key, value in [("context_num_frames", 4), ("target_num_frames", 4), ("num_frames", 8)]:
        assert f"    {key}: {value}\n" in config_text
    sources = {str(x): sha(x) for x in [pipeline, util, config, Path(__file__).resolve()]}
    frozen = {"started_utc": began, "source_sha256": sources,
              "cases": [{"initial_frames": n, "motion": m, "target_frames": t}
                        for n, t in [(1, 13), (9, 12)] for m in ["translation", "stationary"]],
              "scope": "Artificial poses and stubbed sampling/reconstruction; unmodified lifted generation-loop body. No models, real pixels, renderer, timing or cache-hit estimates."}
    (a.out / "pre_run.json").write_text(json.dumps(frozen, indent=2))

    def fake_sample(*args, **kwargs):
        masks = args[8]
        return torch.zeros((len(masks), 3, 1, 1)), torch.zeros((len(masks), 1))

    ns = {"np": np, "torch": torch, "do_sample": fake_sample,
          "tensor_to_pil": lambda x: "SYNTHETIC_STUB",
          "encode_image": lambda x, *args: torch.zeros((len(x), 1))}
    generate, gen_lines = lift(pipeline, "_generate_frames_for_trajectory", ns)
    average, avg_lines = lift(util, "average_camera_pose", ns)
    # Evaluate the exact active call argument, preserving Python slice precedence.
    tree = ast.parse(pipeline.read_text())
    context = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "get_context_info")
    average_calls = [n for n in ast.walk(context) if isinstance(n, ast.Call)
                     and isinstance(n.func, ast.Name) and n.func.id == "average_camera_pose"]
    assert len(average_calls) == 1
    avg_arg = compile(ast.Expression(average_calls[0].args[0]), str(pipeline), "eval")

    class Stub:
        _generate_frames_for_trajectory = generate

        def __init__(self, count):
            self.config = NS(model=NS(context_num_frames=4, target_num_frames=4, num_frames=8, cfg=2),
                             inference=NS(visualize=False), surfel=NS(niter=400, lr=.01))
            self.device, self.dtype = "cpu", torch.float32
            self.pil_frames = ["SYNTHETIC_STUB"] * count
            self.c2ws = [np.eye(4)] * count
            self.Ks = [np.eye(3)] * count
            self.latents = [np.zeros(1)] * count
            self.encoder_embeddings = [np.zeros(1)] * count
            self.model_wrapper = self.vae = self.denoiser = self.image_encoder = None
            self.sampler, self.global_step, self.events = [None], 0, []

        def get_context_info(self, target_c2ws, *args):
            first = len(self.pil_frames) == 1
            subset = eval(avg_arg, {"self": self, "target_c2ws": target_c2ws})
            pose = None if first else average(subset)
            self.events.append({"event": "context", "history_count": len(self.pil_frames),
                                "target_x": target_c2ws[:, 0, 3].tolist(),
                                "retrieval_needed": not first,
                                "query_pose": None if pose is None else pose.tolist(),
                                "average_input_count": 0 if first else len(subset)})
            k = 1 if first else 4
            return {"context_c2ws": torch.eye(4).repeat(k, 1, 1),
                    "context_Ks": torch.eye(3).repeat(k, 1, 1),
                    "context_latents": torch.zeros((k, 1)),
                    "context_encoder_embeddings": torch.zeros((k, 1)),
                    "context_time_indices": list(range(k))}

        def get_translation_scaling_factor(self, poses):
            return 1., poses

        def get_cond(self, latents, poses, intrinsics, scale, embeddings, masks):
            return {"c": None, "uc": None, "all_c2ws": poses, "all_Ks": intrinsics}

        def construct_and_store_scene(self, *args, **kwargs):
            self.events.append({"event": "reconstruction_stub", "history_count": len(self.pil_frames)})

    cases = []
    for spec in frozen["cases"]:
        obj = Stub(spec["initial_frames"])
        count = spec["target_frames"]
        poses = torch.eye(4).repeat(count, 1, 1)
        if spec["motion"] == "translation":
            poses[:, 0, 3] = torch.arange(1, count+1, dtype=torch.float32) * .025
        obj._generate_frames_for_trajectory(poses, torch.eye(3).repeat(count, 1, 1))
        contexts = [e for e in obj.events if e["event"] == "context"]
        queries = [e for e in contexts if e["retrieval_needed"]]
        assert len(contexts) == 3
        assert [e["event"] for e in obj.events] == ["context", "reconstruction_stub"] * 3
        assert len(obj.pil_frames) == spec["initial_frames"] + count
        assert all(e["average_input_count"] == 1 for e in queries)
        same = [np.array_equal(queries[i-1]["query_pose"], queries[i]["query_pose"])
                for i in range(1, len(queries))]
        assert all(x == (spec["motion"] == "stationary") for x in same)
        cases.append({**spec, "events": obj.events, "adjacent_equal_query_pose": same,
                      "not_checked": ["actual map changes", "renderer intrinsics", "source memberships", "cache eligibility", "latency"]})
    assert all(sha(Path(x)) == s for x, s in sources.items())
    result = {"status": "passed", "started_utc": began,
              "completed_utc": datetime.now(timezone.utc).isoformat(),
              "scope": frozen["scope"], "sources": sources,
              "original_function_lines": {"generation_loop": gen_lines, "average_camera_pose": avg_lines,
                                            "average_call_line": average_calls[0].lineno},
              "cases": cases, "source_unchanged": True,
              "claim_limit": "Stationary poses repeat by construction; neither these nor moving fixtures measure real navigation frequency or speed."}
    (a.out / "verification.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"status": result["status"], "cases": len(cases), "output": str(a.out)}))


if __name__ == "__main__":
    main()
