# S17 CPU candidate derived from NAVER curope.cpp mathematical layout.
# Original cuRoPE code: Copyright (C) 2022-present NAVER Corporation.
# Licensed under CC BY-NC-SA 4.0. See author checkout LICENSE.
import math
import torch


class RoPE2DPyTorch(torch.nn.Module):
    """Signed positions; B,H,N,D tokens and B,N,2 int64 (y,x) positions.

    The official blocks cast q/k to float16 before RoPE even under FP32 inference.
    This CPU candidate computes rotations in float32 and restores the input dtype.
    It returns a new tensor; mutation/alias behavior and training are not validated.
    """
    def __init__(self, freq=100.0, F0=1.0):
        super().__init__()
        if not math.isfinite(freq) or freq <= 0 or not math.isfinite(F0):
            raise ValueError("finite positive base and finite F0 required")
        self.base, self.F0 = float(freq), float(F0)

    def forward(self, tokens, positions):
        if tokens.device.type != "cpu" or positions.device != tokens.device:
            raise ValueError("CPU tokens and positions on the same device required")
        if tokens.dtype not in (torch.float32, torch.float16):
            raise ValueError("Only FP32 and the official FP16 RoPE input are validated")
        if tokens.ndim != 4 or tokens.shape[-1] % 4:
            raise ValueError("Expected B,H,N,D with D divisible by four")
        if positions.shape != (tokens.shape[0], tokens.shape[2], 2) or positions.dtype != torch.int64:
            raise ValueError("Expected B,N,2 int64 signed positions")
        quarter = tokens.shape[-1] // 4
        denominator = self.base ** (torch.arange(quarter, dtype=torch.float32) / quarter)
        theta = self.F0 * positions.to(torch.float32)[..., None] / denominator
        cost, sint = theta.cos()[:, None], theta.sin()[:, None]
        pieces = tokens.float().reshape(*tokens.shape[:-1], 2, 2, quarter)
        u, v = pieces[..., 0, :], pieces[..., 1, :]
        result = torch.stack((u * cost - v * sint, v * cost + u * sint), dim=-2)
        return result.flatten(-3).to(tokens.dtype)
