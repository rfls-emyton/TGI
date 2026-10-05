# TGI: Topological Geometric Intelligence

Research implementation by Emylton Leunufna. This repository contains the
public Python source, a reproducible acceptance example, selected regression
tests, and six manuscripts with PDF renderings. NMU retains one static ID per
Unicode scalar. The M2 source-bound response atlas, endpoint transport, and
one-NMU substitution mechanisms are included with independent checkers.

Python >=3.11. Run repository tests with
`python -m unittest discover -s tests -q`. The foundation CLI is available
with `python -m tgi --help`. The foundational and five technical papers are
listed in `paper/technical/README.md`.

The PyPI distribution is built from the explicit 45-module list in
`publication/TGI_M2_PUBLIC_MODULE_ALLOWLIST_V1.json`. To reproduce a local
package from this checkout, run
`python tools/build_public_m2.py --output ../tgi-m2-package --version 0.2.0.dev12`
with a fresh output directory. The six paper PDFs and repository examples are
separate from that minimal distribution. Raw research evidence, historical
hypotheses, checkpoints, and credentials are outside this public code tree.

Copyright (c) 2026 Emylton Leunufna. No reuse allowed without permission.
