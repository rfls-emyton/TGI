# Version map for the TGI paper series and later code releases

The six manuscripts in this directory cite Git commit `de95c4c` and
`tgi-foundation==0.2.0.dev0`. That pair identifies the implementation revision
used in the submitted manuscripts. Their PDFs and source claims are unchanged
by later package releases.

| Code revision | Distribution | Change relevant to the series |
|---|---|---|
| [`de95c4c`](https://github.com/rfls-emyton/TGI/tree/de95c4c) | [`0.2.0.dev0`](https://pypi.org/project/tgi-foundation/0.2.0.dev0/) | Revision cited by all six manuscripts. |
| [`a54da4f`](https://github.com/rfls-emyton/TGI/commit/a54da4f56ff1cf1c2eb471c4618dbf436c63bb97) | [`0.2.0.dev10`](https://pypi.org/project/tgi-foundation/0.2.0.dev10/) | Curated 45-module package with source-bound M2 response atlas, endpoint transport, and one-NMU substitution. |
| [`5438299`](https://github.com/rfls-emyton/TGI/commit/543829991596f073bb7c65a11f90943abce44630) | [`0.2.0.dev11`](https://pypi.org/project/tgi-foundation/0.2.0.dev11/) | Atlas verifier reuses prepared per-event NMU and change state; certificate parity and isolated package tests passed. |
| [`a6b2ce0`](https://github.com/rfls-emyton/TGI/commit/a6b2ce0d3a3e345bc9b538d2e6622fda6d53281b) | [`0.2.0.dev12`](https://pypi.org/project/tgi-foundation/0.2.0.dev12/) | Exact direct source conflict remains visible when C/L opposition revokes a response role; see [the mechanism contract](../../contracts/M2_REVOKED_ROLE_DIRECT_CONFLICT_V1.md). |
| [`3c5c5ea`](https://github.com/rfls-emyton/TGI/commit/3c5c5eaa8c9494ff49561a9150d386d0ca4e579c) | [`0.2.0.dev13`](https://pypi.org/project/tgi-foundation/0.2.0.dev13/) | The independent C/L verifier accumulates exact source-owned support and control states per live class; see [the recurrence contract](../../contracts/M2_INCREMENTAL_CL_VERIFIER_V1.md). |

The later M2 versions extend the public implementation. They do not
retroactively change the methods, results, or evidence cited by the six
submitted papers. A claim about a later operator should cite its own code
revision, contract, fixture, and evaluation rather than the earlier paper
revision. Raw research captures and their provenance remain in the author's
research archive unless separately released.
