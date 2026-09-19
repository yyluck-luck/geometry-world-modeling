# SOCF-A pre-Gate source-conflict diagnostic

This directory contains a provenance-safe, retrospective diagnostic for the
conditional SOCF-A hypothesis (source-level geometry conflict plus abstention).

The runner reads only the sealed S100 candidate-pair selection and saved
low/conf prediction tensors. It does not read future RGB, future depth, future
pose, future metrics, or any new model output. The experiment therefore tests
whether the saved consumer outputs contain a repeatable source-conflict signal;
it cannot test future prediction benefit, calibrated risk, causal effect, or
method novelty.

Run:

```text
python run.py
```

The output is a fresh `run_01/` directory. Existing S100 and S103 artifacts
are preserved. A result marked `PASS` means the diagnostic executed and its
files are internally consistent, not that SOCF-A is validated.

