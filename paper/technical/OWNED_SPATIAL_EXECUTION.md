# Owned Spatial Execution and Reproducible Scale Measurement for Native TGI

Emylton Leunufna  
Technical manuscript, 4 October 2026  
No affiliation

## Abstract

Native character identity and complete geometric proof can become costly
when every new event copies the entire certificate or recomputes every
candidate from the first source. This paper isolates TGI's execution
problem from its semantic and relation laws. It studies source-owned state,
local append, internal certificate access, exact checkpoint parity, and
locked CPU scale protocols. The V11 ownership correction removes a repeated
full `deepcopy` on internal transitions while retaining defensive copies at
the public boundary and full independent verification before commit.
Three untraced measurements per size and a separate traced run compare
32/64/128/256-source, 256-NMU workloads against a hash-bound V10 baseline.
At 256 sources, the median append times fall to 7.496 s for the spatial
panel and 9.903 s for the temporal-phase panel, ratios 0.55 and 0.57 to
their locked baselines; all eight sizes/panels meet the preregistered append
criterion, while replay remains within its declared 20% tolerance. The
paper reports these as CPU panel measurements, not as evidence of a general
hardware superiority or model capability. Source extraction, wheel tests,
and the publication ZIP make the claimed revision reproducible.

## 1. Question and performance contract

TGI is not allowed to reduce cost by merging adjacent character IDs, dropping
event positions, or skipping a checker because its output is expensive.
The performance question is therefore: can an implementation do less
unnecessary copying and recomputation while leaving the identity stream,
proof, and decisions exactly the same? This parallels the *principle* of
band-owned computation in MULTIPITA [1], but TGI's owned spatial state is
not MP2's trained cell, channel tensor, or optimizer.

The object of this paper is an execution transition over an owned runtime
state. A public observer may request a defensive certificate copy. The
internal `observe` transition already owns the current state and need not
obtain that copy just to inspect its own fields. After deriving a candidate,
the runtime still forks the raw model, recomputes the full independent proof,
and commits atomically. This separates an avoidable Python copy from the
validation that makes the result admissible.

The correctness contract for optimization is unusually strict: old and new
paths must agree on phase decision, route resolution, certificate hash,
checkpoint bytes, and cold recovery at matched inputs. A faster result that
omits a witness or admits a previously rejected history is not a performance
improvement under TGI's native goal.

## 2. V10 diagnosis and V11 ownership correction

The V10 function profile [2] attributed a dominant cumulative cost to
`copy.deepcopy` of the full certificate on repeated `observe` calls. At
256 sources, the recorded cumulative deepcopy time was 32.245 s for the
V9 control and 32.679 s for the V10 cycle under `cProfile`. Those figures
are attribution diagnostics, **not** untraced throughput comparisons.
The candidate V11 repair [3] changes internal ownership access only. It does
not remove the defensive public property, discard raw history, weaken the
checker, or change an event's NMU identity.

An explicit parity probe [4] compares V10 source distribution bytes with
the V11 candidate. It records matching checkpoint hash, certificate hash,
byte count, resolution, and cold recovery for the declared synthetic probe.
The full regression [5] and extracted package tests guard against effects
outside the microbenchmark. These controls are required before reading the
timing table as evidence of a valid optimization.

## 3. Frozen scale design

The V11 protocol [6] was written before collecting three new untraced
replications; a fourth traced run is kept separate. Every workload uses
256-NMU frames, a fixed count of sources in `{32,64,128,256}`, and the
same functional controls. There are two panels: the spatial V9-form
decision and the temporal-phase decision. The comparator is a locked V10
baseline identified by SHA-256. For each size/panel the report retains
individual append times, median append, full-replay times, checkpoint size,
peak allocated bytes, PID, and hash. The criterion was lower median append
than the baseline at all eight points, with replay within 20% of baseline.

The principle of *matched workload* matters. A `cProfile` run is not used
as an untraced timing replicate; a source count of 256 is not presented as
a whole production corpus; and a lower append time is not taken to mean
the scientific relation learned is more accurate. The same distinction
appears in the MULTIPITA paper [1], which separates arithmetic, isolated
kernels, full trainer, and training observation. TGI applies that discipline
to its own operators.

## 4. Results

The terminal V11 measurement [7] reports that all eight median append
comparisons satisfy the frozen improvement criterion and all eight replay
medians remain within the 20% guard. At 256 sources, append medians are
7.496 s for the spatial panel and 9.903 s for the temporal-phase panel,
ratios 0.55 and 0.57 to their respective old baselines. Peak allocations
reported for these two 256-source panels are 153,887,631 and 158,527,276
bytes. The reported values are process measurements for a declared CPU
workload. They are not extrapolated to arbitrary source counts or a GPU
implementation.

The local edit-transport operator used by the referent manuscript has a
separate frozen cost criterion [8]. Relative to the previous response-class
implementation at a 64-event equal-outcome workload, its median time ratio
is 1.012 and peak allocation ratio is 1.032, both below a declared 1.2
ceiling. This is not the V11 panel and cannot be averaged with it. It answers
a narrower question: whether wrapper-invariant NMU edit transport adds
excessive local overhead.

The full source distribution [9] contains 247 runtime modules in the V71R
paper binding. Its six gates check required material, hash parity,
unexpected evidence exclusion, historical virtual-environment exclusion,
raw phase from extraction, and distribution from extraction. Wheel tests for
the physical fracture and selector run in the isolated installed
environment. These checks establish that measurements and mechanisms are
not dependent on an accidental workspace import path.

## 5. Bulk-native interpretation and negative controls

Bulk-native computation means reorganizing **execution** while retaining
every character's static identity, source ownership, event order, and
resolution target. It does not mean pooling characters into a new latent
identity. V11 improves one cost center without changing the mechanism's
mathematical meaning. The proof-bearing append remains more expensive than
an unchecked in-memory update because it preserves source history and
verifies a complete certificate. The correct economic comparison therefore
has at least three independent axes: event throughput, proof/replay cost,
and functional decision parity. A fast transition with an unverified
partial certificate is a failed implementation, even if it returns a
plausible sentence.

The retained failures are informative. Previous allocation repair work
encountered host-memory `MemoryError` during an oversized verifier copy;
localizing and removing the unnecessary copy allowed CPU recovery without
reducing the proof. The V10 profile itself is not a speed result, and the
V4 cost measurement does not prove V11 scale behavior. Preserving those
separate experimental roles prevents selection of a convenient number as
the whole-system result.

## 6. Artifact and reproduction statement

The source package [9] is hash-bound; its extracted phase and distribution
results identify exact runtime bytes. The V11 protocol, raw repetitions,
summary, and terminal receipt are [6,7]. The V10 source-bound parity
receipt is [4]. The 4,575-member publication bundle has a SHA-256 index and
was independently read member by member after construction [10]. The
bundle includes the paper set's antecedent monolithic evidence ledger,
source distribution, author metadata, and historical negative evidence.
These are reproducibility assets rather than substitutes for a scientific
claim about a workload not measured here.

## 7. Full locked-panel results

The following table reproduces the median append and ratio fields from
the terminal V11 protocol [7]. Ratios compare each V11 point only with
its matching frozen V10 baseline; they are not normalized across panels.

| Panel | Sources | Median append (s) | V11/V10 append | V11/V10 replay | Checkpoint bytes |
|---|---|---|---|---|---|
| spatial | 32 | 0.491 | 0.815 | 0.976 | 229,563 |
| spatial | 64 | 1.102 | 0.756 | 0.969 | 457,829 |
| spatial | 128 | 2.646 | 0.655 | 1.024 | 914,367 |
| spatial | 256 | 7.496 | 0.545 | 1.014 | 1,827,865 |
| temporal phase | 32 | 0.635 | 0.875 | 0.999 | 335,895 |
| temporal phase | 64 | 1.374 | 0.761 | 0.988 | 669,222 |
| temporal phase | 128 | 3.335 | 0.667 | 0.998 | 1,335,885 |
| temporal phase | 256 | 9.903 | 0.573 | 1.019 | 2,669,846 |

The trend is not represented by a single global speedup. Within this
panel, the append ratio improves as source count rises, while replay
ratios remain near one. That pattern is consistent with removal of
repeated full-certificate copying during append, whereas complete replay
still performs its full proof. The profiler diagnosis and this table
together support the causal explanation for the matched implementation;
they do not measure every possible input distribution. The checkpoint
sizes increase with source count, which is expected because the original
history and proof are preserved rather than compressed away.

## 8. Reproduction protocol and interpretation rules

A reproducer should verify the hash-bound baseline, use the same source
counts and 256-NMU frame size, run the three untraced repetitions separately
from the diagnostic traced run, then compute medians from the raw files.
It should run functional parity and cold recovery before interpreting a
timing improvement. Finally it should compare the source-extracted runtime
hashes and installed wheel behavior with the workspace run. Changing the
frame size, source composition, proof budget, or checker invocation creates
a different experiment and cannot be silently pooled with this table.

The larger public evidence bundle is 1.49 GB compressed and 16.8 GiB in
manifest-bound raw files. Its verifier reads every ZIP entry and compares
its SHA-256 with the embedded index [10]. A compact PDF alone therefore
is not asked to carry all raw evidence; it identifies the immutable
artifact needed to reproduce each number. This is the systems analogue
of NINMENI's deposit-package practice: a paper explains the mechanism and
result, while exact bytes and falsifiers remain inspectable.

## Code and artifact availability

The public TGI runtime and selected regression tests are available at
https://github.com/rfls-emyton/TGI/tree/de95c4c and as the
`tgi-foundation` version `0.2.0.dev0` distribution at
https://pypi.org/project/tgi-foundation/0.2.0.dev0/. The GitHub commit fixes
the code revision used for this publication series. Paths under `evidence/`,
the historical `KONSEP.txt` and `HIPOTESIS` archive, and other unpublished
workspace reports identify research provenance retained by the author; they
are not files in the public GitHub repository or PyPI distribution. Results
requiring those receipts are therefore identified by their archived source
paths rather than presented as independently downloadable from the code
release.

## References

[1] E. Leunufna, *MULTIPITA: Band-Owned Iso-Budget Computation*, revision V3,
2026, https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7341819.

[2] `evidence/spatial_temporal_action_v10_profile_20261004/terminal_receipt.json`.

[3] `contracts/S2_V11_INTERNAL_OWNERSHIP_OPTIMIZATION.md`.

[4] `evidence/spatial_temporal_action_v11_checkpoint_parity_20261004/terminal_receipt.json`.

[5] `evidence/spatial_temporal_action_v11_full_regression_20261004/terminal_receipt.json`.

[6] `contracts/S2_V11_SCALE_REMEASUREMENT_V1.md`.

[7] `evidence/spatial_temporal_action_v11_scale_protocol_20261004/terminal_receipt.json`
and `summary.json` in the same directory.

[8] `evidence/m1_v4_transport_cost/terminal_receipt.json`.

[9] `evidence/source_distribution_20261004T084916022662Z/result.json`.

[10] `publication/TGI_V1_20261004/RELEASE.json` and `verification.txt`.
