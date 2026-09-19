---
pipeline_tag: image-to-video
---

# MNIST World Models

This repository hosts a curated set of checkpoints used for experiments in the paper [Flow Equivariant World Models: Memory for Partially Observed Dynamic Environments](https://huggingface.co/papers/2601.01075).

[**Project Page**](https://flowequivariantworldmodels.github.io/) | [**GitHub**](https://github.com/hlillemark/flowm)

## Description
Flow Equivariant World Modeling (FloWM) is a framework that leverages time-parameterized symmetries within a latent memory for stable and accurate dynamics prediction over long horizons. The latent memory shifts and transforms equivariantly with self-motion and inferred external object motion, keeping information about out-of-view regions aligned as time progresses. These specific checkpoints correspond to the **MNIST World** (2D) environment benchmarks.

## Contents
This repository contains the following checkpoints:
- `mnistworld/dfot/dynamic_po.ckpt` — MNIST World Diffusion Forcing Transformer (DFoT)
- `mnistworld/dfot-ssm/dynamic_po.ckpt` — MNIST World Diffusion State Space Model (DFoT-SSM)
- `mnistworld/flowm-fernn/dynamic_po_flowm.pt` — MNIST World FloWM (FERN-N)
- `mnistworld/vae/mnist_world_vae.ckpt` — MNIST World VAE

## Usage
For detailed instructions on environment setup, training, and inference (including replicating the paper's results), please refer to the [official GitHub repository](https://github.com/hlillemark/flowm) and its [wiki](https://github.com/hlillemark/flowm/wiki).

## Citation
```bibtex
@misc{lillemark2026flowequivariantworldmodels,
    title={Flow Equivariant World Models: Memory for Partially Observed Dynamic Environments}, 
    author={Hansen Jin Lillemark and Benhao Huang and Fangneng Zhan and Yilun Du and Thomas Anderson Keller},
    year={2026},
    eprint={2601.01075},
    archivePrefix={arXiv},
    primaryClass={cs.LG},
    url={https://arxiv.org/abs/2601.01075}, 
  }
```