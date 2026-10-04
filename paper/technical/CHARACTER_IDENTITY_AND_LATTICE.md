# Character Identity and Discrete Crystal-Lattice Addressing in Topological Geometric Intelligence

Emylton Leunufna  
Technical manuscript, 4 October 2026  
No affiliation

## Abstract

Topological Geometric Intelligence (TGI) treats a raw character stream as an
ordered sequence of persistent identities whose occurrences can acquire
distinct geometric addresses. This manuscript defines the identity substrate,
the distinction between a character ID and its event occurrence, a discrete
five-coordinate frame layout, and the conditions under which traversal may
reconstruct an output. The TGI instantiation maps each admitted Unicode scalar
to `ord(c)+16`, reserves 0–15 for structural uses, rejects surrogate values,
and does not normalize input. This differs from the normalized registry
instantiation described in the companion NINMENI NMU preprint while preserving
its one-character/one-identity axiom. A two-stream acceptance experiment places
the repeated prefix `SISTEM` into separate context lanes. The specified
queries reconstruct each complete raw sentence and return no path for an
unformed third anchor. The outcome follows from a complete route certificate,
not from an assumed semantic value of a coordinate or a probabilistic guess.
Checkpoint-order falsifiers show why the original event sequence is part of the
addressing contract. The manuscript separates the established exact-route
result from the later tasks of forming knowledge and referents.

## 1. Research question and contribution

The NINMENI NMU paper [1] fixes identity granularity. TGI begins where that
paper stops: if two experiences contain the same character and even the same
initial phrase, how can a geometric memory keep their occurrences distinct
and read a justified continuation? The answer must preserve the axiom
`one Unicode character -> one static ID`; it may not create a new identity for
`SISTEM`, replace positions by a pooled vector, or change identity according
to frequency. The problem is one of **addressing and route validity**, not a
new tokenization scheme.

This manuscript contributes (a) a typed separation of identity, occurrence,
frame, coordinate, and route; (b) a concrete discrete placement law that
separates source lanes; (c) a complete-route versus absent-route decision; and
(d) falsifiers that distinguish correct text output from correct geometric
state. These responsibilities are upstream of band and phase formation in the
companion phase manuscript. A route can be well-formed even when its text is
false about the world; world-relation evidence is owned by the interventional
relations manuscript.

## 2. Identity and occurrence definitions

Let `U` be the declared admitted Unicode scalar space. The TGI codec is
`I: U -> N`, `I(c)=ord(c)+16`. The low 16 integers are not character IDs.
For admitted scalars, the map is injective and static. A surrogate is rejected
before it can become a stored identity. Input is neither NFC-normalized nor
segmented. This is an explicit TGI instantiation choice. In [1], NINMENI's
measured corpus and 10,240-slot registry use a declared normalization and
hash-bound table; importing that registry's implementation into TGI would be
an unjustified architectural shortcut. What TGI takes from [1] is the
identity **axiom**, not its corpus-specific table.

For a source `s`, frame `f`, and position `i`, define the occurrence
`o=(s,f,i,I(c_i))`. The projection `identity(o)=I(c_i)` forgets event ownership,
so two occurrences can share an identity without being interchangeable.
The ordered stream is `O_f=(o_0,...,o_{T-1})`; its chronology and raw source
must survive checkpointing. A valid bulk-native operator may process several
occurrences together, but it must project back to every original identity and
position in the same order. This is a stronger invariant than equality of the
final rendered string.

The distinction matters for repeated letters and shared prefixes. In the
sentence `SISTEM TGI ...`, both `S` occurrences have the same static ID but
not the same occurrence address. The `S` at the start of the other sentence
also has that ID, while its source lane differs. Neither a numerical ID nor a
single coordinate carries a meaning label such as *safe* or *reactor*.

## 3. Discrete layout and route certificate

The versioned foundation layout places occurrence `i` of the `n`th distinct
frame at

`P(n,i)=(2+i, 1, 0, 3+5n, (5-3n) mod 11)`.

The first coordinate orders characters; the fourth and fifth create source
lanes. This is a constructive address allocation, not a proof that Euclidean
or hyperbolic geometry by itself forms knowledge. For an admitted frame, a
forward adjacency bond joins `P(n,i)` to `P(n,i+1)` only within its own lane.
The route certificate records source, ordered occurrence identities, addresses,
bond validity, and an explicit terminal marker. A reader returns the original
character stream only after reaching the terminal marker through checked
bonds. Three outcome categories are kept distinct:

| Outcome | Necessary observation | Interpretation |
|---|---|---|
| `COMPLETE` | every ordered occurrence and terminal bond verified | exact reconstruction of a stored route |
| `NO_PATH` | requested anchor is absent from valid state | no certified continuation |
| `INCOMPLETE` | a route is present but broken or stopped by a ceiling | no complete output claim |

The codec can decode each visited ID back to its scalar. A complete certificate
therefore implies exact output character by character for that stored route.
It does not imply factual truth of the decoded sentence. The no-path rule is a
decision about the current geometric memory, not a universal statement that a
sentence is impossible.

## 4. Method and falsifiers

The frozen user acceptance case contains two raw streams:

1. `SISTEM TGI AMAN DARI HALUSINASI`;
2. `SISTEM REAKTOR NUKLIR MEMBUTUHKAN PENDINGIN`.

The two streams share the first six characters. The accepted anchors are the
first `S` in lane A and the first `S` in lane B; a third unformed anchor is an
absence control. Successful evaluation requires exact reconstruction of both
strings, zero cross-lane jumps after `SISTEM`, and no output from the absent
anchor. The acceptance report [5] executes the route and the broader project
regression in the same chain.

Output equality is not sufficient to verify spatial ownership. A historical
checkpoint fault sorted sources before replay, producing the same text while
changing which frame obtained which lane. The spatial retention decision [6]
therefore freezes the original raw insertion journal and verifies the lattice
after fresh-process recovery. Frame equality is checked from the complete NMU
sequence rather than trusting a potentially colliding digest. A broken bond,
modified coordinate, or mismatched receipt must fail validation rather than
fall back to a plausible text completion.

The acceptance test is deliberately sharp: shared prefixes make a shallow
character lookup appear sufficient for the first few positions, but only a
lane-bound route can preserve the correct continuation. Conversely, an absent
anchor should not be mapped to the closest observed source. The reader has no
softmax sampling step that could hide absence behind an output string.

## 5. Results and inference

The source acceptance report [5] records both exact reconstructions and the
absent-context decision. The checkpoint-order falsifier and fix are retained
in [6]. The phase-validity requirements required before a frame contributes
are defined separately in [7]; they prevent an invalid source receipt from
silently serving as a route. The source distribution report [8] checks that
the relevant implementation and tests can be reproduced from extracted
package bytes. These evidence classes should not be collapsed: a regression
checks behavior, a checkpoint check tests state transport, and a source archive
check tests reproducibility.

This establishes the TGI substrate and exact route behavior for the declared
states. It does not claim that `P(n,i)` alone discovers a physical referent or
that the original integral expression for `xi` in `KONSEP.txt` has been derived
from this layout. That expression is a source hypothesis. The tested placement
law is an explicit implementation whose premises and consequences are visible.

## 6. Reproducibility and artifact statement

The authoritative source is `KONSEP.txt` [4], the four NINMENI reference
preprints, the acceptance contract and raw receipt [5], source-preserving
checkpoint decision [6], and the hash-bound source distribution [8]. The
relevant implementation entry points are `tgi/identity.py`, `tgi/spatial.py`,
`tgi/frame_engine.py`, and their tests in the distribution. The publication
bundle identifies exact SHA-256 bytes for the manuscript, source, and
evidence. No training checkpoint or private corpus is required to reproduce
the acceptance case.

## 7. Formal invariants and a constructive argument

The character mapping is injective because adding a fixed offset to two
different Unicode scalar numbers cannot make them equal. This is an identity
property, not a statistical observation. The occurrence projection is not
injective: two events may share `I(c)`. Thus no proof about event ownership
may be based on ID equality alone. The address allocation must additionally
bind the frame number, within-frame position, and source journal. For two
frames `n != m`, their fourth coordinates differ by `5(n-m)`; hence their
lanes cannot coincide under the declared layout. For two positions in the
same frame, first coordinates differ. This establishes occurrence separation
inside the admitted finite frame set independently of the wording of the
sentences. The fifth coordinate is an additional consistency check, not the
only source of uniqueness.

For exact reconstruction, take the route whose bonds connect the ordered
occurrences `o_0,...,o_(T-1),END`. The base case reads `I(c_0)` from `o_0`.
At step `i<T-1`, the validated forward bond has the same frame lane and
the unique successor `P(n,i+1)`; decoding it appends `c_(i+1)`. Induction
gives the original scalar sequence after `T` occurrences, provided the
terminal bond is present. If a bond is missing, the induction premise fails
and the route cannot emit a complete result. This is the scope of the
constructive theorem. It does not establish that a different unstored
sentence should have the same result.

The absence decision is equally precise. An unformed anchor has no initial
valid occurrence and therefore no initial route certificate. Returning an
empty result is a property of the current state; returning one of the two
stored sentences would be a counterexample to the contract. A safety ceiling
interrupting a nonempty route is recorded as `INCOMPLETE`, avoiding the
mistake of conflating unobserved data with a proof of absence.

## 8. Test matrix and state provenance

| Probe | Perturbation | Required certificate consequence |
|---|---|---|
| same prefix, two sources | trigger first `S` under each lane | exact respective full stream, no cross-lane edge |
| third anchor | request a lane never formed | `NO_PATH`, no guessed phrase |
| source order swap on recovery | reorder journal while keeping text | reject changed coordinate ownership |
| damaged bond or terminal | remove one required route edge | `INCOMPLETE` or invalid certificate, never partial text labeled complete |
| Unicode distinction | feed different scalar sequences with similar display | preserve distinct IDs and raw order |

The journal and the certificate carry different roles. The journal is
provenance of what entered and when; the certificate is a derivation from
that journal under current rules. A certificate recovered without the
underlying raw history would be insufficient to test whether source order
changed. Conversely, merely retaining the journal does not prove that the
current lattice still obeys the placement law. Both are checked after
recovery. This mirrors the NINMENI papers' distinction between a declared
identity rule and a measured state, while keeping TGI's own discrete
addressing rule explicit.

## References

[1] E. Leunufna, *NMU: One Character, One Identity*, revision V2, 2026,
`REFERENSI_NINMENI/NMU_One_Character_One_Identity_Revision_V2.pdf`.

[2] E. Leunufna, *MULTIPITA: Band-Owned Iso-Budget Computation*, revision V3,
2026, `REFERENSI_NINMENI/MULTIPITA_Band-Owned_Iso-Budget_Revision_V3.pdf`.

[3] E. Leunufna, *Emylton: A Falsifiable Native Crystallization-State Chain*,
revision V2, 2026, `REFERENSI_NINMENI/EMYLTON_Organization_Ownership_Revision_V2.pdf`.

[4] E. Leunufna, *Topological Geometric Intelligence*, `KONSEP.txt`, 2026.

[5] `evidence/acceptance_20260924T201845597182Z/result.json`.

[6] `contracts/CHECKPOINT_SPATIAL_DECISION_V1.md`.

[7] `contracts/FRAME_CRYSTAL_V1.md`.

[8] `evidence/source_distribution_20261004T084916022662Z/result.json`.
