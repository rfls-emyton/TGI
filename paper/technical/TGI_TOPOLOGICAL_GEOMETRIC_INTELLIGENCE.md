# TGI: Topological Geometric Intelligence

Emylton Leunufna  
Foundational manuscript, 4 October 2026  
No affiliation

## Abstract

Topological Geometric Intelligence (TGI) is proposed as an independent
computational research program in which raw character identity, source-owned
experience, discrete spatial organization, and certified traversal form a
continuous learning and resolution chain. Its starting point is the NINMENI
axiom that one Unicode character has one static identity. TGI derives its own
objects and operators from the goal of forming inspectable, revisable
knowledge rather than transplanting an existing neural implementation. This
paper states the paradigm contract and connects five separately specified
mechanisms: character identity and crystal-lattice addressing; C/L-band-owned
phase and organization; interventional formation of spatial referents;
deterministic resolution with continual revision; and owned spatial execution.
It distinguishes a stored route from a source-valid organization and an
intervention-supported relation. The published experimental set includes
exact two-stream reconstruction, phase and counterexample controls,
interventional physical traces, complete-frontier resolution checks,
checkpoint recovery, and locked scale measurements. Each result is tied to a
specific contract and falsifier. This foundation paper defines how the
components jointly constitute TGI; each technical paper supplies its own
formal details and reproducibility path.

## 1. Research question and position

The central question is whether a machine can form, revise, and use knowledge
through discrete identity and geometry while preserving an inspectable chain
from experience to answer. A successful answer must identify the source of a
claim, show how its organization formed, expose the route by which a query
reaches it, and state when no complete route is available. TGI treats this as
an architectural question, not a renaming of an existing model.

The original `KONSEP.txt` places TGI alongside machine learning as a proposed
AI paradigm, with derived subfields beneath it. That is a research taxonomy:
its legitimacy comes from independently specified mechanisms and their
falsifiers. Earlier six-branch labels in the manifesto describe exploration,
not a requirement that six software modules or six papers must exist. The
present publication series instead follows mechanism ownership, as the four
NINMENI reference preprints do. This foundational paper owns the joint
contract; its companions each own a narrower technical question.

TGI adopts the NINMENI identity axiom without copying a VEYRA NYRA model.
Within the TGI foundation, subword segmentation, gradient descent,
softmax scaled dot-product attention, and continuous vector embeddings are
excluded as learning or resolution operators. Programming languages, arrays,
indexes, hashes used with equality checks, and compiled kernels are neutral
implementation instruments. They become relevant to the paradigm only through
the identity, ownership, and provenance invariants they preserve.

## 2. The common objects and their invariants

Let a raw stream be an ordered sequence of Unicode scalar values. The TGI
codec assigns one static ID to each scalar, currently `ord(c)+16`, with 0-15
reserved. Distinct occurrences of the same character retain that identity
while acquiring distinct source, time, and position records. No phrase ID or
subword ID replaces the constituent identities. Event order is part of the
observable input and must survive checkpoint replay.

An admitted frame consists of these occurrences, source provenance, and a
bounded event interval. A crystal address is discrete and is allocated to an
occurrence in a context lane; an adjacency bond can connect only source-valid
neighbors. The five-coordinate layout in the present implementation is a
specific addressing contract, not a proof that every conceptual relation is
intrinsically five-dimensional. Complete traversal requires an explicit end
condition. Missing, ambiguous, and incomplete routes are distinguishable
outcomes, because a work ceiling cannot certify absence.

The C bands own local adjacency positions and the L bands own temporal
coverage. An occurrence phase receipt, denoted Omega and xi in the technical
paper, checks structural admission. Organization-level Omega_H instead counts
distinct realizations across source-valid episodes. These values have
different types and purposes; a large scalar by itself is not knowledge. A
counterexample can revoke an organization without deleting the historical
events from which it formed. Source validation recomputes ownership and phase
receipts before a stored claim is allowed to authorize an answer.

Knowledge in this architecture is consequently not just a lattice edge.
The joint record is a source-valid organization with an explicit domain of
application, support, counterexamples, phase state, and a verifiable route to
an output or action. Physical referent relations add an intervention record:
the system changes an actuator variable, observes the resulting sensor trace,
and compares it with the unaltered course. A repeated linguistic surface
alone does not establish that two descriptions share a world referent.

## 3. Derivation of the TGI chain

The derivation starts with the goal of preserving exact experience. Static
character identity and ordered occurrences give the substrate. Source-owned
C/L organization then determines which local and long-range relations were
actually witnessed. Discrete address allocation makes those witnesses
retrievable without replacing the characters with continuous learned tokens.
Phase admission prevents an unverified receipt from becoming a crystal.

The next goal is useful knowledge beyond verbatim replay. Organization is
formed from contrasted episodes, including what remains fixed and what varies.
It is eligible only under its stated coverage and evidence rule. The physical
branch tests a further step: whether changes in the world support a relation
that survives a novel intervention. Observed counterexamples can fracture a
class and trigger a revised organization; they are retained as evidence, not
averaged away by a score.

Finally, a query must resolve through a complete, inspectable path. The
resolution engine evaluates admissible alternatives and source dependencies,
including guarded transformations and actual feedback from action. A
certificate records why a selected output is authorized. A rejection
certificate must account for the full relevant frontier; an exhausted budget
produces INCOMPLETE rather than a false claim that no route exists. Atomic
checkpoint and recovery preserve this decision chain over time. Spatial
execution work studies the cost of these same owned computations without
changing their semantics.

## 4. Technical division of the publication series

| Independent technical paper | Mechanism it owns | Main falsifier |
|---|---|---|
| Character Identity and Discrete Crystal-Lattice Addressing | NMU occurrences, five-coordinate lane, exact route | repeated prefix crosses lanes or replay changes allocation |
| Band-Owned Phase Formation and Source-Valid Organization | C/L ownership, phase receipt, raw organization | invalid receipt enters the active crystal |
| Interventional Formation and Fracture of Spatial Referent Classes | edit contrast, sensor response, class fracture | held-out intervention violates the formed relation |
| Deterministic Resolution and Continual Learning | guarded closure, complete frontier, feedback and recovery | uncertified selection or false NO_PATH after incomplete search |
| Owned Spatial Execution | semantic parity and cost of state-owned kernels | speed claim lacks locked protocol or changes output |

The papers are not an ordinal maturity ladder. An identity or phase mechanism
is not itself a theory of referents; an execution kernel is not an independent
decision rule. Each paper contains definitions, method, result, limitation,
and reproduction instructions for its own operator. The current series and
its hash index are in `paper/technical/README.md` and
`paper/technical/validation.json`.

## 5. Method, evidence, and falsification

The acceptance seed is deliberately small and adversarial. Two raw streams,
"SISTEM TGI AMAN DARI HALUSINASI" and "SISTEM REAKTOR NUKLIR MEMBUTUHKAN
PENDINGIN", share a prefix but must remain in separate crystal lanes. A
query anchored to the first or second lane must reproduce its entire stream
character for character; an unformed third anchor must return no path. This
tests address and traversal isolation. It does not substitute for the separate
test of knowledge formation.

The phase and organization work tests source-valid receipts, positive support,
counterexamples, and recovery of the same state after reload. Interventional
work adds signed physical captures, edit transport to unseen prefixes,
class-fracture controls, and independent checking of source and action
provenance. Resolution work tests every relevant alternative, distinction of
NO_PATH from INCOMPLETE, dependency validity, actual feedback, and atomic
recovery. The execution study fixes input sizes and compares a state-owned
implementation with its prior version under parity checks. These are
different evidential claims and cannot be exchanged for a single accuracy
number.

The historical foundation manuscript `paper/TGI_FOUNDATION_DRAFT.md` records
the longer development chain and negative results. The compact publication
set references exact contracts and receipts rather than reproducing a large
test log in prose. The complete evidence bundle is indexed in
`publication/TGI_V1_20261004/RELEASE.json`; its archive members and hashes
are independently verifiable. Local validation of the six manuscript/PDF
pairs and the publication ZIP is recorded in the series release metadata.

## 6. Scope of the resulting claim

TGI's defining claim is mechanistic: raw identity and experience ownership
can support a connected cycle of formation, intervention, revision, and
certified resolution without making a probabilistic next-token choice the
governing operator. The component papers give the concrete laws and tests of
that cycle. Exact path reconstruction, source validity, physical action
traces, and scale parity are each stated at their own experimental boundary.
No scalar phase metric alone proves truth in the world, and a closed route
claim applies to the complete frontier certified for a query. This explicit
division makes the architecture open to decisive counterexamples and permits
each mechanism to improve without silently changing the common axiom.

## References

[1] E. Leunufna, *NMU: One Character, One Identity*, revision V2, 2026,
`REFERENSI_NINMENI/NMU_One_Character_One_Identity_Revision_V2.pdf`.

[2] E. Leunufna, *MULTIPITA: Band-Owned Iso-Budget Computation*, revision V3,
2026, `REFERENSI_NINMENI/MULTIPITA_Band-Owned_Iso-Budget_Revision_V3.pdf`.

[3] E. Leunufna, *Emylton: A Falsifiable Native Crystallization-State Chain*,
revision V2, 2026,
`REFERENSI_NINMENI/EMYLTON_Organization_Ownership_Revision_V2.pdf`.

[4] E. Leunufna, *Crystal Memory for Native Character-Identity Streams*,
revision V3, 2026,
`REFERENSI_NINMENI/CRYSTAL_MEMORY_Rangkaian_Aksi_Kristal_V3_Revision.pdf`.

[5] `KONSEP.txt` and the `HIPOTESIS` research archive.

[6] `paper/TGI_FOUNDATION_DRAFT.md` and
`paper/technical/validation.json`.

[7] `publication/TGI_V1_20261004/RELEASE.json`.

[8] `evidence/acceptance_20260924T201845597182Z/result.json`.

[9] `evidence/source_distribution_20261004T084916022662Z/result.json`.
