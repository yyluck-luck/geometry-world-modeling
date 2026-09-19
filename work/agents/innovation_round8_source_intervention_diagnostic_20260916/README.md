# Synthetic counterexample receipt

Run `python3 run_diagnostic.py` from this directory. The script uses only constants and a seeded standard-library RNG. It does not import VMem, load model weights, read images/depth/poses, connect to SSH, or read future answers.

`RESULTS.json` records four logical counterexamples: memory-count confounding, shared geometry bias, seed-versus-noise replay, and frozen descendants. `RECEIPT.json` records actual completion time plus script/results SHA-256. Passing these assertions is software/synthetic evidence only. It does not validate SOCF-A, GRC-Memory, SIFG or any real-data effect.
