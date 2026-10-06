# TGI: Topological Geometric Intelligence

Emylton Leunufna

Independent researcher (no institutional affiliation)

4 October 2026

## Abstract

Topological Geometric Intelligence (TGI) is a discrete, source-owned approach
to forming and revising inspectable knowledge from raw character and event
streams. It preserves the NINMENI invariant of one static identity per Unicode
character while deriving TGI-specific spatial addresses, C/L-band ownership,
phase admission, interventional relations, deterministic resolution and
state-owned execution. We specify the objects and operators as one connected
system and test them using shared-prefix reconstruction, source and phase
counterexamples, signed intervention traces, complete-frontier decisions,
actual feedback with cold recovery, and locked scale protocols. The resulting
claims are attached to their own falsifiers: exact traversal does not by
itself establish a world referent, while a source-valid relation requires
observational or interventional support. This article consolidates the
mechanism, experiment and falsifier chain in one auditable technical account.

**Keywords:** Topological Geometric Intelligence; NINMENI; NMU; discrete
geometry; crystallization; source provenance; interventional learning;
deterministic resolution.

## 1. Introduction

The research question is whether a machine can form, revise, and use
knowledge through discrete identity and geometry while preserving an
inspectable chain from raw experience to answer. The NINMENI NMU study fixes
one character as one static identity (Leunufna, 2026a). MULTIPITA gives a
principle of band-owned computation without replacing that identity
(Leunufna, 2026b). The Emylton and Crystal Memory studies distinguish
organizational state from persistent memory and retrieval (Leunufna, 2026c;
2026d). TGI adopts those principles, then derives its own geometric,
source-valid decision operators. It does not import a VEYRA NYRA model.

For a raw stream of Unicode scalars, a static ID belongs to a character,
while a source, event time and position belong to an occurrence. A discrete
address makes an occurrence retrievable; a bond and phase receipt determine
whether traversal is admitted; organization measures support across
source-valid experience; intervention distinguishes a world relation from
linguistic repetition. Resolution must examine the complete relevant
frontier, retain counterevidence and report incomplete work distinctly from
an absent path. These are successive proof obligations rather than
interchangeable scores.

The implementation excludes subword identities, gradient descent,
backpropagation, softmax scaled dot-product attention, and continuous vector
embeddings as TGI learning or resolution operators. The use of arrays,
indexes, hashes and compiled code is an implementation choice constrained by
identity and provenance preservation. The paper gives the definitions,
falsification protocols, experimental outcomes and execution costs of the
integrated system.

## 2. Mechanisms and formal method

### 2.1. Character identity and discrete lattice

#### Identity and occurrence definitions

Let `U` be the declared admitted Unicode scalar space. The TGI codec is
`I: U -> N`, `I(c)=ord(c)+16`. The low 16 integers are not character IDs.
For admitted scalars, the map is injective and static. A surrogate is rejected
before it can become a stored identity. Input is neither NFC-normalized nor
segmented. This is an explicit TGI instantiation choice. In the NMU study (Leunufna, 2026a), NINMENI's
measured corpus and 10,240-slot registry use a declared normalization and
hash-bound table; importing that registry's implementation into TGI would be
an unjustified architectural shortcut. What TGI takes from the NMU study (Leunufna, 2026a) is the
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

#### Discrete layout and route certificate

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

#### Formal invariants and a constructive argument

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

### 2.2. Band-owned phase and organization

#### Band ownership without identity pooling

For a frame `f=(c_0,...,c_{T-1})`, fast bank `j mod 8` owns the adjacency
witness between positions `j` and `j+1`. Ownership answers *where the check
is maintained*, not which characters exist. Every character still has its
own static NMU ID and ordered event. The eight slow banks receive temporal
coverage through binary carry. A completed block can be incorporated into a
larger block while the raw occurrence order and source remain recoverable.
An empty bank is not filled with inferred support.

The invariant is stronger than equal output after processing. Given a stored
receipt, an independent checker must recompute the expected owner of each
adjacency and temporal block from the original frame length and event order.
A receipt that attributes a valid-looking value to the wrong bank is invalid.
This protects against the common failure in which a plausible scalar is
accepted while the mechanism purported to produce it never ran. The C/L
organization here is a TGI structural implementation; it is not the trained
channel-partitioned MP2 cell of (Leunufna, 2026b).

#### Two levels of density and the lock

The foundation occurrence law uses `c_i,l_i in {0,1}` as validity witnesses
for the local and temporal paths:

`Omega_i = (c_i + l_i)/2`, with `Omega_crit = 1`.

An occurrence becomes structurally eligible only if both checks pass. The
versioned `xi_i` lock additionally requires a complete frame, an owned
coordinate, and a unique occurrence. This is a certificate bit or scalar
projection of the checked state, not an independent source of truth. In
particular, a high value caused by a normalization invariant is not a health
metric and cannot license a world claim.

An organization `H` is inferred from multiple raw episodes. Stable intervals
remain literal NMU occurrences. Intervals that vary together may become
binding axes, but the axis is an organizational relation over occurrences,
not a new token identity. An episode supports `H` only when its complete raw
sequence has exactly one valid interpretation under `H`. Let `D_k(H)` be the
set of distinct realizations of axis `k` among such episodes. The frozen
candidate measure is `Omega_H = min_k |D_k(H)|` with threshold three.
`Omega_H` and `Omega_i` have different domains and should never be substituted
for one another in a derivation or in a plot.

The phase decision is therefore source-bound. A candidate with enough
realizations cannot be promoted if a contributing source has a malformed
frame, false C/L ownership, invalid receipt, or counterexample. The checker
stores the original evidence scope used for the decision, making a later
revocation and re-evaluation possible. No negative raw event is deleted to
make a crystal appear stable.

#### Phase verification algorithm and failure analysis

The independent phase check can be described without relying on a particular
Python data structure. It first decodes the declared raw frame and rejects
invalid scalar identities. It then reconstructs every fast-bank owner from
its adjacency index and every slow-bank block from chronological binary
carry. It compares these reconstructed structures with the stored receipt.
Only after this equality holds does it compute occurrence validity and the
candidate lock. At the organization level it enumerates source episodes,
requires complete unambiguous interpretation, derives the set of distinct
axis realizations, and checks the current source-validity state. A later
counterexample forces a new evaluation over the preserved event history.

This order matters causally. If the checker read an asserted `xi` first and
used it to excuse a malformed C/L record, it would make the claimed
mechanism self-certifying. If it counted every episode that resembles an
axis but has two valid interpretations, `Omega_H` would be inflated by an
undecided source. If it removed an opposing source, the subsequent crystal
would appear stronger only because evidence was destroyed. The tested
implementation rejects those routes and exposes why promotion is withheld.

| Evidence object | Unit of observation | What it may justify | What it cannot justify alone |
|---|---|---|---|
| `c_i,l_i` | one occurrence check | local and temporal ownership | factual truth of text |
| `Omega_i,xi_i` | source/frame phase receipt | structurally readable occurrence | organization across episodes |
| `Omega_H` | distinct unambiguous axis realizations | candidate organization | correct world referent |
| counterexample | later original source event | revocation or context refinement | deletion of older source history |

The table also prevents a nomenclature failure. NINMENI's Emylton state
uses `Omega` for organization history and `xi` as a projected observation;
TGI's occurrence and organization receipts use similar letters but own
different objects. The shared principle is that organization and projection
must be separated. Equality of symbols is not a derivation from Emylton.

### 2.3. Interventional spatial relations

#### Raw edit contrast and transport

For a port `p`, an event is
`e_t(p)=(source_t, I(a_t), I(before_t(p)), I(after_t(p)))`, where `I` maps
each scalar to its fixed NMU ID. The contrast operator first identifies the
valid one-NMU edit kind: `STABLE`, `SUBSTITUTE`, `INSERT`, or `DELETE`.
Ambiguous insertion/deletion positions are all retained. Multi-atom changes
cannot be silently simplified into a one-atom response. The earlier signed
three-port audit is useful precisely because some inputs failed these
conditions and returned `NO_PATH` rather than being selected as positive
evidence.

The first response-class rule compared edit kind and absolute offset. A
falsifier showed it separated `T0 -> T1` from `LONG:0 -> LONG:1` even
though both changed `0` to `1`, and could equate different changed atoms at
the same offset. The V4 transport rule instead uses the changed identity:

`tau(SUBSTITUTE)=(SUBSTITUTE, old_ID, new_ID)`;

`tau(INSERT)=(INSERT, inserted_ID)`;

`tau(DELETE)=(DELETE, deleted_ID)`;

`tau(STABLE)=(STABLE)`.

The complete before/after frames, positions, and source remain in the
certificate. Discarding the absolute offset from the **class key** is not
discarding it from evidence. The operator makes a limited invariance claim:
stable textual wrappers may change while the local NMU edit is conserved.
It does not equate arbitrary paraphrases or unseen sensor transformations.

#### Class formation and phase law

Let `h_t(p)` be the chronological sequence of certified `tau` values for
port `p`. Two ports are in the same observational class at time `t` if their
histories agree under the declared transport rule. This equivalence is
operational: it says available interventions have not separated them.
Members retain distinct addresses and raw histories.

For a candidate class and action, C support counts distinct raw contexts
before a class-wide change. L requires (i) a same-action stable control and
(ii) an appropriate comparator from another action while the candidate class
remains stable. The candidate reaches an Omega support threshold only with
distinct contexts. xi locks only one eligible action-class pair; ties or
missing controls return `NO_PATH`. These requirements were frozen before
the signed positive capture . They prevent repeated identical observations
or a target label from masquerading as independent support.

The phase transition is reversible. Suppose class `{p,q}` is `CRYSTAL` and
the next actual action changes `q` but not `p`. The event must return
`REVOKED`. A V1 falsifier showed that immediate promotion of `{q}`
from old support was wrong. The repaired law starts a new evidence epoch at
the fracture. The old events remain in the certificate, but only fresh
support, controls, and comparator evidence may crystallize `{q}`. This is a
specific mechanism of source-preserving forgetting of a decision right;
it is not deletion of experience.

#### Active choice without an effect oracle

After an ambiguous class crystallizes, TGI may seek a separating experience.
Given a verified class certificate and a finite available-action catalogue,
the V5 selector computes which action strings have already occurred in the
current epoch. It preserves all untried alternatives and selects one by
lexicographic NMU-ID order . The catalogue is an interface affordance,
not a complete ontology of world actions. The certificate explicitly reports
`effect_predicted=false` and `separation_claimed=false`. If no action remains,
the outcome is `NO_UNTRIED_ACTION`, not a proof that two physical entities
are identical. Both source certificate and choice are independently checked.

#### Event-level decision trace and causal reading

| Event range | Raw action | Class evidence state | Native decision |
|---|---|---|---|
| 1-4 | `a,a,a,a` | distinct changing contexts and a same-action control accrue | `NO_PATH` at each prefix |
| 5 | `b` | cross-action comparator closes eligibility | two-port `CRYSTAL` |
| 6 | `c` | port responses diverge for the first time | `REVOKED` |
| 7-10 | `c,c,c,c` | support and a control accrue after the fracture epoch | `NO_PATH` at each prefix |
| 11 | `b` | comparator for the fresh candidate is observed | one-port `CRYSTAL` |

The significance of event 6 is not that the letter `c` possesses a
predefined semantic role. It is that a measured action changes one port's
response history while leaving its former class mate different. If the
collector had supplied `target=q` to native input, the same status sequence
would not prove endogenous class formation. The protocol instead stores the
port/component mapping as evaluator-only metadata and runs a label-invariance
control. Likewise, the new one-port crystal at event 11 is not inherited
from the pre-fracture support: the event trace checks the epoch boundary and
fresh support explicitly.

An observational class is therefore a **quotient of recorded response
histories**, not a metaphysical equivalence relation over hidden physical
objects. It is symmetric and transitive for the fixed history because
equality of verified `tau` sequences is symmetric and transitive. It can
refine after a new event; that change is not a contradiction in the
definition because the time index has changed. Treating a past class as
immutable would be the actual contradiction. The phase lock gives the
class a current reading right and the fracture law removes that right when
its premises cease to hold.

### 2.4. Deterministic resolution and continual revision

#### Source-derived operators and context guards

An actual transition records a complete before frame, raw action, after
frame, source ID, port set, and ordering. Minimal context families are
computed from original measured relations. A guard is a conjunction over
the ports in one family. A transition law may be an exact literal case for
one observed before frame or a whole-before operator such as prepend,
append, interleave, or repetition. The operator is not inferred from the
surface similarity of two examples alone. Its admission requires:

1. a phase-valid single-axis whole-before organization;
2. every axis bound and every original organization agreeing with the
 proposed operator;
3. exact action applicability and replay of every original literal source;
4. agreement of all applicable minimal context families on the **full
 concrete output**, not merely on an abstract region name.

If an operator, guard, or literal case is missing, the decision records a
specific acquisition obligation. It does not create an implicit wildcard.
The V116 guarded-word decision details the admission conditions. This
differs from memorizing a list of source-output pairs: the admitted operator
can act on a new whole before string under a proved guard, while an unproved
operator remains unavailable even if it would happen to predict a test
answer correctly.

#### Finite proof dictionary and complete frontier

Let `D` contain all nonempty substrings of original source guards and
declared goals. The V116 proof treats an input outside `D` as nonmember
under an operator that preserves that whole input; a constant operator can
instead return to a known exact word. This gives an exact finite congruence
for the source-proved guarded-word system, not an unrestricted theorem about
all future language. The state for planning is the complete joint collection
of port regions and concrete values. All available actions, reachable
regions, self-loops, return edges, and shortest alternatives are enumerated
and checked independently (Leunufna, 2026a; 2026d).

A frontier certificate owns the search result. It may identify a complete
supported goal path, a shortest acquisition request, multiple unresolved
alternatives, or a closed no-path result within the declared state/action
system. A ceiling that stops enumeration yields incomplete status, not a
synthetic theorem of impossibility. Context-changing actions update the
entire joint state before the next step is selected. This is important when
two ports are correlated in the current experience but an actual separating
action later shows they require distinct context families.

For an answer `y`, the constructive claim is conditional:
`Certified(q,S,y)` requires that every selected edge have a source-valid
operator or literal witness, all competing applicable families agree on `y`,
the complete route is within the verified frontier, and the current source
history contains no revoking counterexample. If any premise fails, the
system must preserve the obligation or refuse the answer. This certificate
is the content of deterministic resolution; merely choosing the largest
bond score would not satisfy it.

#### Actual experience and knowledge renewal

Selection initiates a real action through the external interface. The
returned before/after frames are admitted as original NMU events, not as an
expected-output fixture. Unexpected effects are retained as knowledge or
opposition; they can interrupt the current plan and trigger a new frontier.
Repeated support does not delete the counterexample. Later contexts may
separate apparently conflicting laws, but that separation itself needs an
actual distinguishing witness .

The owned continuation cycle performs verified prefix, actual
continuation, learning, complete-history renewal, and atomic commit. The
checkpoint contains the original event history and the proof needed for a
fresh-process recovery. A malformed input, stale external digest, or
certificate that disagrees with the raw events is rejected before partial
mutation becomes visible. This avoids a common form of false continual
learning: a process whose in-memory state seems updated but cannot reproduce
the same decision after restart.

The V119 local acquisition integration adds source-owned updates above
the prior native runtime and keeps evaluator-label substitutions outside the
native input. The older integration decision is not used to assert every
later capability by inheritance. The current source archive and its
extracted phase are the reproducibility anchor for the latest packaged
runtime; older evidence retains its own frozen binding.

#### Resolution procedure and certificate decomposition

At a fixed current source state, the procedure first verifies the complete
original event ledger and phase validity. It then derives every minimal
context family and literal law from those events. Candidate whole-before
operators are admitted only after the four source tests in Section 2.
The proof dictionary is built from the finite guards and declared goals,
and all reachable joint-state edges are enumerated for the declared
available actions. The frontier checker recomputes the same graph from
source laws, compares all shortest alternatives, and checks each proposed
goal path's original NMU lineage. The selector may then choose one
certified action or an acquisition obligation. After an actual executor
result returns, the complete process repeats on the enlarged ledger.

This order avoids a subtle circular proof. The expected answer must not
be fed into the organization that later “proves” the answer. Nor may a
selected action's anticipated effect be substituted for the actual
before/after frames. The source-derived law and measured effect have
distinct provenance fields. When they disagree, the disagreement is
counterevidence and changes the knowledge decision. A fresh process
recovery verifies the same sequence without consulting an in-memory
shortcut or a hidden evaluator label.

| Certificate layer | Owned premise | Typical falsifier |
|---|---|---|
| source/phase | raw event and valid organization | damaged or stale source receipt |
| operator | all bound axes and exact literal replay | forged universal-input witness |
| context | every applicable minimal family agrees | newly separating actual action |
| frontier | all reachable declared edges and shortest alternatives | omitted self-loop or return edge |
| actuation | actual action/result chronology | expected outcome substituted for observed outcome |
| checkpoint | atomic ledger and certificate | wrong external digest or partial write |

The statuses have operational consequences. `CERTIFIED` permits the
declared route's output or next action. `NO_PATH` means no supported route
in the completed declared graph. `REVOKED` means an earlier route's premise
has been contradicted or its source has lost validity. `INCOMPLETE`
means search, capture, or verification stopped before a decision could be
proved. Combining these into a single “low confidence” number would lose
information needed for the next experiment.

### 2.5. Owned spatial execution and scale

#### V10 diagnosis and V11 ownership correction

The V10 function profile attributed a dominant cumulative cost to
`copy.deepcopy` of the full certificate on repeated `observe` calls. At
256 sources, the recorded cumulative deepcopy time was 32.245 s for the
V9 control and 32.679 s for the V10 cycle under `cProfile`. Those figures
are attribution diagnostics, **not** untraced throughput comparisons.
The candidate V11 repair changes internal ownership access only. It does
not remove the defensive public property, discard raw history, weaken the
checker, or change an event's NMU identity.

An explicit parity probe compares V10 source distribution bytes with
the V11 candidate. It records matching checkpoint hash, certificate hash,
byte count, resolution, and cold recovery for the declared synthetic probe.
The full regression and extracted package tests guard against effects
outside the microbenchmark. These controls are required before reading the
timing table as evidence of a valid optimization.

#### Frozen scale design

The V11 protocol was written before collecting three new untraced
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
appears in the MULTIPITA paper (Leunufna, 2026b), which separates arithmetic, isolated
kernels, full trainer, and training observation. TGI applies that discipline
to its own operators.

## 3. Experimental protocols and results

### 3.1. Character identity and discrete lattice

#### Method and falsifiers

The frozen user acceptance case contains two raw streams:

1. `SISTEM TGI AMAN DARI HALUSINASI`;
2. `SISTEM REAKTOR NUKLIR MEMBUTUHKAN PENDINGIN`.

The two streams share the first six characters. The accepted anchors are the
first `S` in lane A and the first `S` in lane B; a third unformed anchor is an
absence control. Successful evaluation requires exact reconstruction of both
strings, zero cross-lane jumps after `SISTEM`, and no output from the absent
anchor. The acceptance report executes the route and the broader project
regression in the same chain.

Output equality is not sufficient to verify spatial ownership. A historical
checkpoint fault sorted sources before replay, producing the same text while
changing which frame obtained which lane. The spatial retention decision
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

#### Results and inference

The source acceptance report records both exact reconstructions and the
absent-context decision. The checkpoint-order falsifier and fix are retained
in . The phase-validity requirements required before a frame contributes
are defined separately in ; they prevent an invalid source receipt from
silently serving as a route. The source distribution report checks that
the relevant implementation and tests can be reproduced from extracted
package bytes. These evidence classes should not be collapsed: a regression
checks behavior, a checkpoint check tests state transport, and a source archive
check tests reproducibility.

This establishes the TGI substrate and exact route behavior for the declared
states. It does not claim that `P(n,i)` alone discovers a physical referent or
that the original integral expression for `xi` in the original TGI research statement has been derived
from this layout. That expression is a source hypothesis. The tested placement
law is an explicit implementation whose premises and consequences are visible.

#### Test matrix and state provenance

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

### 3.2. Band-owned phase and organization

#### Falsification protocol

The tests challenge four separable properties:

| Challenge | Required outcome | Why it matters |
|---|---|---|
| C/L owner altered, output unchanged | reject receipt | output parity alone misses wrong ownership |
| incomplete or fabricated bank support | no crystallization | prevents support from an empty path |
| counterexample after crystal | revoke affected reading right | tests knowledge validity through time |
| old certificate after new evidence | reject or revalidate against full history | prevents stale confidence |

The raw-organization and phase acceptance reports carry the first
versioned evidence. The source distribution rebuilds and evaluates the
phase from extracted archive bytes, rather than relying on a workspace whose
history can change. Historical negative audits are retained in the long-form
TGI evidence ledger . The experiment classification follows (Leunufna, 2026b): a
structural check, a regression pass, a systems measurement, and a functional
capability claim are distinct kinds of evidence.

#### Results, interpretation, and successor interfaces

The accepted raw-organization report records nine gate decisions; the
phase report records source-valid phase, counterexample, and polarity
checks. The source archive passes its material/hash gates and runs both
phase and distribution verifiers from extraction. These results establish a
reproducible mechanism for source-valid structural promotion and withdrawal
on the tested inputs. The acceptance chain also tests the exact route
consequence when the source and frame are valid.

The earlier TGI formulation writes a general resonance accumulation for
Omega and an integral expression for xi. The equations above are operational
laws for this implementation. Matching names or dimensions would not prove
mathematical equivalence to the exploratory manifesto expressions. The paper
therefore states the implemented operator and its falsifier directly. This
choice makes the chain testable: the relation analysis below may form relations only
from events whose source and phase are certified. It may not relabel the phase
scalar as a semantic predicate.

#### What the results test

The organization report's nine gates and the phase report's six checks
are meaningful only with their input scope, exact source bytes, and
negative controls. The source-distribution verifier adds a different
guarantee: it checks that the same files appear inside the archive with
the expected hashes, then executes phase and distribution checks from
the extracted tree. It cannot by itself enlarge the functional input
class beyond the declared contracts. The functional consequence relevant
to this article is narrower and constructive: a route can be read only
through source-valid crystals; when a counterexample revokes that source
or organization, the old certificate cannot continue to authorize
resolution. The actual query-level effect is checked by the separate
resolution analysis.

### 3.3. Interventional spatial relations

#### Frozen physical protocol and controls

The strongest local witness is a newly created state file with initial
`{x:0,y:0,z:0}` and three opaque sensor ports. The collector's fixed action
schedule is `a,a,a,a,b,c,c,c,c,c,b`. `a` increments x to ceiling three, `b`
increments y to ceiling two, and `c` increments z to ceiling four. The sensor
frames are `T(x)`, `VIEW:(x+z)`, and `D(y)` . Each action reads physical file
bytes before and after; the collector records monotonic causal intervals,
raw-byte hashes, a no-reset state lineage, and a signature. The evaluator's
port-to-component mapping is stored apart from native input.

An independent verifier checks the Ed25519 signature, collector and
executable hashes, state bytes, action effect, sensor projection, port
inventory, and chronological lineage. A tampered capture is rejected. The
native replay produces four initial `NO_PATH` decisions, a two-port
`CRYSTAL` after the same-action control and comparator, `REVOKED` on the first
`c`, four `NO_PATH` decisions during fresh-epoch accumulation, and a
one-port `CRYSTAL` after the final comparator. A wrong checkpoint digest and
forged epoch are rejected; full recovery succeeds in a fresh process.

At the fifth event, `a` and `b` have already been observed; the selector
chooses `c` from the catalogue `{a,b,c}` . The sixth physical event
actually fractures the class. This alignment between selection and outcome
is an observed consequence of this protocol, not a promise that the selector
always picks a separator. The withheld edit-transport panel contains
60 positive, 60 negative, and 60 wrapper/address-permutation cases across
substitution, insertion, deletion, and four Unicode alphabets. Its 900
prefixes are checked by the independent oracle.

#### Results and inference boundary

The experiment establishes an intervention-owned observational relation,
its revocation under actual counterevidence, and reconstruction from fresh
evidence. A semantic label or designated target is not required by the
operator. The physical setup still supplies the port inventory and action
affordances. Two entities with indistinguishable responses to every supplied
action remain one observational class until new experience separates them.
This is a precise and useful referent mechanism, not a claim that the universe
of possible separators was exhausted by the experiment.

The full V4 cost protocol measures the changed-atom transport against
the preceding offset-based class rule at equal outcome. The median ratio at
64 events is 1.012 and peak-allocation ratio is 1.032, below preregistered
1.2 limits. These are local panel costs, not end-to-end production throughput.
The final source package reproduces the relevant runtime and tests from
extracted bytes and an isolated wheel.

#### Independent checking and attack surface

Four layers are checked separately. The Node verifier checks that the
physical capture could have resulted from the recorded state transitions
and that the signed body was not modified. The Python raw-contrast checker
checks edit kind and all alignments. The class checker rebuilds every phase
from original events, including epoch boundaries. The selector checker
recomputes action coverage and deterministic choice. Agreement of all four
is materially stronger than a test that compares only the final selected
port with an evaluator label.

The negative controls illustrate different failure modes. The older signed
panel with no same-action target control remains `NO_PATH` ; it cannot
be rescued by post-hoc threshold adjustment. A cross-format positive that
failed the offset rule motivated a changed-atom rule , but a different
changed atom at the same offset remains negative. Forged phase or epoch
fields are rejected against the raw history . Duplicate available
actions are rejected before selector ordering . A catalogue containing
only already tried actions returns `NO_UNTRIED_ACTION`; adding an untried
action changes the available experiment, not past evidence. These controls
bind the precise scope of the positive physical result.

### 3.4. Deterministic resolution and continual revision

#### Falsification and result classes

The experiments separate logical completeness, actual feedback, and systems
transport. In V116, a forged universal-input certificate is rejected; a
past-only correlated context cannot erase the later separating experience;
and unsupported guards remain acquisition obligations. Workspace and
source-extracted audits each execute nine signed actual transitions across
context exclusion, two-step context-changing goals, prepend, literal
interleaving, distinguishing acquisition, counterevidence, and a newly
acquired command . The decision records 18 transitions and cold recoveries
across both audits, 10 observed goals, two quantified exclusions, four
retained replans, two counterevidence interruptions, and two unique context
discoveries. The 34 captures preserve native input under evaluator-label
substitution. These are counts of a declared panel, not an extrapolated
frequency in arbitrary worlds.

The V106 continuation API reports seven focused ownership/failure tests,
649 extracted regressions, 159 installed tests, and six physical transactions
through actual cycles. V119 reports 40 focused tests, 957 source
regressions, 467 installed tests, four actual transitions and commits,
four cold recoveries, and eight label-invariant captures for its integration
scope. The present source distribution runs its own complete phase and
distribution checks from extracted bytes. These records should be read in
their version order: later modules do not rewrite historical results.

Negative cases are essential. A no-path result after an unsupported guard is
not counted as successful generalization. A changed action outcome is not
silently normalized into the predicted state. A partial frontier produced
by a resource ceiling is not rebranded as complete resolution. The paper's
decision categories preserve these distinctions so that further learning
can target a concrete missing witness.

#### Reproducibility and relation to NINMENI

NINMENI contributes the immutable NMU event substrate (Leunufna, 2026a) and a research
discipline that separates organization, memory, material update, and output
capability (Leunufna, 2026c; 2026d). TGI's guarded-law, frontier, actual-feedback, and atomic
knowledge operators are its own derivations. The relevant modules are
`tgi/guarded_word_closure.py`, its independent checker,
`tgi/guarded_word_goal_frontier.py`, `tgi/guarded_word_goal_workflow.py`,
and `tgi/local_acquisition_runtime.py`. Contracts and receipts
identify the source scopes and exact commands. The publication bundle
contains the article, source archive, frozen controls, and SHA-256 index.

#### Continual-learning protocol and failure preservation

Continual learning is a chain of transactions, not a single successful
append. The V106 cycle API checks owned input/output, invalid plan,
valid refusal, atomic failure, external digest, scope upgrade, and exact
work boundaries. Six physical transactions include no-reset rollovers and
an unexpected outcome. V116 then tests actual separating experience,
counterevidence interruption, retained replans, and a newly learned
command under signed capture. V119 re-bases local acquisition on the
current native source while preserving the previous runtime modules.
These are complementary rather than interchangeable tests: API recovery
does not prove a context law, and an operator proof does not prove an
atomic checkpoint.

The negative ledger is part of the method. A past-only prefix cannot
resolve two continuations after the same prefix without another witness;
false certainty there is a falsifier, not a minor quality reduction.
Similarly, a completed test with its input instrument later found invalid
must be retracted as an instrument failure. A resource exhaustion during
proof construction yields no partial certified answer. Preservation of
these cases is necessary to tell whether a later mechanism actually
closes an obligation or merely hides it behind a new name.

### 3.5. Owned spatial execution and scale

#### Results

The terminal V11 measurement reports that all eight median append
comparisons satisfy the frozen improvement criterion and all eight replay
medians remain within the 20% guard. At 256 sources, append medians are
7.496 s for the spatial panel and 9.903 s for the temporal-phase panel,
ratios 0.55 and 0.57 to their respective old baselines. Peak allocations
reported for these two 256-source panels are 153,887,631 and 158,527,276
bytes. The reported values are process measurements for a declared CPU
workload. They are not extrapolated to arbitrary source counts or a GPU
implementation.

The local edit-transport operator used by the interventional relation analysis has a
separate frozen cost criterion. Relative to the previous response-class
implementation at a 64-event equal-outcome workload, its median time ratio
is 1.012 and peak allocation ratio is 1.032, both below a declared 1.2
ceiling. This is not the V11 panel and cannot be averaged with it. It answers
a narrower question: whether wrapper-invariant NMU edit transport adds
excessive local overhead.

The full source distribution contains 247 runtime modules in the V71R
paper binding. Its six gates check required material, hash parity,
unexpected evidence exclusion, historical virtual-environment exclusion,
raw phase from extraction, and distribution from extraction. Wheel tests for
the physical fracture and selector run in the isolated installed
environment. These checks establish that measurements and mechanisms are
not dependent on an accidental workspace import path.

#### Bulk-native interpretation and negative controls

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

#### Full locked-panel results

The following table reproduces the median append and ratio fields from
the terminal V11 protocol . Ratios compare each V11 point only with
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

#### Reproduction protocol and interpretation rules

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
its SHA-256 with the embedded index . A compact PDF alone therefore
is not asked to carry all raw evidence; it identifies the immutable
artifact needed to reproduce each number. This is the systems analogue
of NINMENI's deposit-package practice: a paper explains the mechanism and
result, while exact bytes and falsifiers remain inspectable.

## 4. Discussion

The five mechanism families address distinct obligations of the same TGI
chain. Exact reconstruction tests source-lane isolation and route closure;
phase controls test admissible structural organization; intervention tests
whether a relation survives changes in observed physical state; resolution
tests complete alternatives, feedback and recovery; and scale experiments
test the cost of preserving these same decisions. A matching output without
its source and certificate cannot substitute for any of these tests.

The experiments distinguish no path, unresolved alternatives and an
incomplete search. Counterevidence is retained so a prior conclusion can be
revised. A deterministic answer is therefore a decision under declared
experience and scope, rather than a universal guarantee about unobserved
world states. The signed physical traces test the specified intervention
interface; hidden physical identity remains underdetermined when different
referent assignments induce the same complete observations. This is an
observability condition to test, not a label to inject into training.

## 5. Reproducibility, data and code availability

The public implementation and selected regression tests are available at
https://github.com/rfls-emyton/TGI/tree/de95c4c and in the
`tgi-foundation` version `0.2.0.dev0` package at
https://pypi.org/project/tgi-foundation/0.2.0.dev0/. This code revision binds
the methods and results reported here.
Later public M2 releases have a separate version map and are not silently
substituted for the paper's tested code. The original evidence archive,
including raw intervention captures, source receipts and locked scale
measurements, is retained by the author. The public repository supplies
source and selected tests; records that are not deposited there must be
requested from the author for independent reanalysis. Local paths and
contract filenames are provenance identifiers, not literature citations.

The experimental protocols require preservation of original Unicode IDs,
event order, source scope, phase receipts, negative controls, exact version
and independent certificate checking. Timing comparisons require the same
locked input panel and output parity before a speed ratio is interpreted.

## References

Leunufna, E. (2026a). *NMU: One Character, One Identity: A Static
Character-Identity Substrate and Character-Level Characterisation of an
Indonesian Corpus* (Version 2, revised preprint). SSRN.
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7341318

Leunufna, E. (2026b). *MULTIPITA: Band-Owned Iso-Budget Computation for
Native Character-Identity Streams* (Version 3, revised preprint). SSRN.
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7341819

Leunufna, E. (2026c). *Emylton: A Falsifiable Native Crystallization-State
Chain for Character-Identity Streams* (Version 2, revised preprint). SSRN.
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7345360

Leunufna, E. (2026d). *Crystal Memory for Native Character-Identity Streams:
Local Retrieval, Cycle-Bound Retention, and the Boundary of Causal Learning*
(Version 3, revised preprint). SSRN.
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7355679
