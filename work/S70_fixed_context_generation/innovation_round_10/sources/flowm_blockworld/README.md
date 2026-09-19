---
pipeline_tag: image-to-video
---

# Blockworld Models

This repository hosts a curated set of checkpoints used for experiments of **FloWM**, as presented in the paper [Flow Equivariant World Models: Memory for Partially Observed Dynamic Environments](https://huggingface.co/papers/2601.01075).

[**Project Page**](https://flowequivariantworldmodels.github.io/) | [**GitHub Repository**](https://github.com/hlillemark/flowm)

## Contents
- `blockworld/dynamic/flowm/v2_dynamic.ckpt` — blockworld dynamic flowm v2_dynamic
- `blockworld/dynamic/dfot/v2_dynamic.ckpt` — blockworld dynamic dfot v2_dynamic
- `blockworld/dynamic/dfot-ssm/v2_dynamic.ckpt` — blockworld dynamic dfot-ssm v2_dynamic
- `blockworld/dynamic/rssm/v2_dynamic_50m.ckpt` — blockworld dynamic Dreamer RSSM v2_dynamic, 50M parameters
- `blockworld/dynamic/rssm/v2_dynamic_400m.ckpt` — blockworld dynamic Dreamer RSSM v2_dynamic, 400M parameters
- `blockworld/static/flowm/v2_static.ckpt` — blockworld static flowm v2_static
- `blockworld/static/dfot/v2_static.ckpt` — blockworld static dfot v2_static
- `blockworld/static/dfot-ssm/v2_static.ckpt` — blockworld static dfot-ssm v2_static
- `blockworld/tex/flowm/tex.ckpt` — blockworld tex flowm tex
- `blockworld/tex/dfot/tex.ckpt` — blockworld tex dfot tex
- `blockworld/tex/dfot-ssm/tex.ckpt` — blockworld tex dfot-ssm tex
- `blockworld/vae/blockworld_vae.ckpt` — blockworld vae
- `blockworld/vae/blockworld_tex_vae.ckpt` — blockworld tex vae

Hub: https://huggingface.co/flowm123/blockworld-models

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