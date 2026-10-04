# Interventional Formation and Fracture of Spatial Referent Classes in TGI

Emylton Leunufna  
Technical manuscript, 4 October 2026  
No affiliation

## Abstract

An addressable crystal lattice does not itself identify which observations
belong together. This manuscript defines an interventional relation operator
for TGI using raw NMU action strings and before/after frames from opaque
sensor ports. A one-NMU edit contrast distinguishes stable, substitution,
insertion, and deletion responses without creating subword identities. Local
edit transport compares changed NMU atoms across stable wrapper text while
retaining the full original alignment in the proof. Ports with the same
observed response history form an observational class, with C support from
distinct pre-action contexts, L controls and cross-action comparators, an
Omega threshold, and a unique xi lock. An actual distinguishing intervention
revokes a prior class; fresh-epoch evidence is required before any successor
class crystallizes. A signed three-port physical capture reproduces the
sequence `NO_PATH x4, CRYSTAL, REVOKED, NO_PATH x4, CRYSTAL`. An action selector
can choose an untried raw action from a finite available catalogue without
pretending to know its effect. This paper states exactly what a TGI referent
class means: an experience-owned relation among ports under interventions,
not a target label supplied by the evaluator.

## 1. Research question and causal interface

The first two TGI manuscripts define static identity, coordinates, and
source-valid phase. They do not decide whether two views are causally linked.
The TGI goal [1] requires relation formation from experience itself. The
input therefore consists of an actual action `a_t` and a mapping from opaque
port addresses to raw frame pairs `(before,after)`. The native operator sees
the action characters, ports, frames, and their order. It does not receive
component names, a target-port parameter, predicate labels, or the correct
answer to a future query. Physical apparatus metadata may be held by the
evaluator solely for independent checking.

The central contribution is a layered proof: raw edit contrast, response
equivalence, support and control accumulation, phase transition, fracture,
and fresh-epoch formation. Each layer retains the original event. A class
cannot be asserted merely because two sensors display the same word once.
The construction uses NINMENI's immutable NMU event identity [2] as a
substrate, not NINMENI's trained memory tensor or optimizer [3].

## 2. Raw edit contrast and transport

For a port `p`, an event is
`e_t(p)=(source_t, I(a_t), I(before_t(p)), I(after_t(p)))`, where `I` maps
each scalar to its fixed NMU ID. The contrast operator first identifies the
valid one-NMU edit kind: `STABLE`, `SUBSTITUTE`, `INSERT`, or `DELETE`.
Ambiguous insertion/deletion positions are all retained. Multi-atom changes
cannot be silently simplified into a one-atom response. The earlier signed
three-port audit [4] is useful precisely because some inputs failed these
conditions and returned `NO_PATH` rather than being selected as positive
evidence.

The first response-class rule compared edit kind and absolute offset. A
falsifier [5] showed it separated `T0 -> T1` from `LONG:0 -> LONG:1` even
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

## 3. Class formation and phase law

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
the signed positive capture [6]. They prevent repeated identical observations
or a target label from masquerading as independent support.

The phase transition is reversible. Suppose class `{p,q}` is `CRYSTAL` and
the next actual action changes `q` but not `p`. The event must return
`REVOKED`. A V1 falsifier [7] showed that immediate promotion of `{q}`
from old support was wrong. The repaired law starts a new evidence epoch at
the fracture. The old events remain in the certificate, but only fresh
support, controls, and comparator evidence may crystallize `{q}`. This is a
specific mechanism of source-preserving forgetting of a decision right;
it is not deletion of experience.

## 4. Active choice without an effect oracle

After an ambiguous class crystallizes, TGI may seek a separating experience.
Given a verified class certificate and a finite available-action catalogue,
the V5 selector computes which action strings have already occurred in the
current epoch. It preserves all untried alternatives and selects one by
lexicographic NMU-ID order [8]. The catalogue is an interface affordance,
not a complete ontology of world actions. The certificate explicitly reports
`effect_predicted=false` and `separation_claimed=false`. If no action remains,
the outcome is `NO_UNTRIED_ACTION`, not a proof that two physical entities
are identical. Both source certificate and choice are independently checked.

## 5. Frozen physical protocol and controls

The strongest local witness is a newly created state file with initial
`{x:0,y:0,z:0}` and three opaque sensor ports. The collector's fixed action
schedule is `a,a,a,a,b,c,c,c,c,c,b`. `a` increments x to ceiling three, `b`
increments y to ceiling two, and `c` increments z to ceiling four. The sensor
frames are `T(x)`, `VIEW:(x+z)`, and `D(y)` [9]. Each action reads physical file
bytes before and after; the collector records monotonic causal intervals,
raw-byte hashes, a no-reset state lineage, and a signature. The evaluator's
port-to-component mapping is stored apart from native input.

An independent verifier checks the Ed25519 signature, collector and
executable hashes, state bytes, action effect, sensor projection, port
inventory, and chronological lineage. A tampered capture is rejected. The
native replay [10] produces four initial `NO_PATH` decisions, a two-port
`CRYSTAL` after the same-action control and comparator, `REVOKED` on the first
`c`, four `NO_PATH` decisions during fresh-epoch accumulation, and a
one-port `CRYSTAL` after the final comparator. A wrong checkpoint digest and
forged epoch are rejected; full recovery succeeds in a fresh process.

At the fifth event, `a` and `b` have already been observed; the selector
chooses `c` from the catalogue `{a,b,c}` [11]. The sixth physical event
actually fractures the class. This alignment between selection and outcome
is an observed consequence of this protocol, not a promise that the selector
always picks a separator. The withheld edit-transport panel [12] contains
60 positive, 60 negative, and 60 wrapper/address-permutation cases across
substitution, insertion, deletion, and four Unicode alphabets. Its 900
prefixes are checked by the independent oracle.

## 6. Results and inference boundary

The experiment establishes an intervention-owned observational relation,
its revocation under actual counterevidence, and reconstruction from fresh
evidence. A semantic label or designated target is not required by the
operator. The physical setup still supplies the port inventory and action
affordances. Two entities with indistinguishable responses to every supplied
action remain one observational class until new experience separates them.
This is a precise and useful referent mechanism, not a claim that the universe
of possible separators was exhausted by the experiment.

The full V4 cost protocol [13] measures the changed-atom transport against
the preceding offset-based class rule at equal outcome. The median ratio at
64 events is 1.012 and peak-allocation ratio is 1.032, below preregistered
1.2 limits. These are local panel costs, not end-to-end production throughput.
The final source package [14] reproduces the relevant runtime and tests from
extracted bytes and an isolated wheel.

## 7. Reproducibility and references

The primary runtime and checker are `tgi/local_edit_transport_classes.py`
and `tgi/local_edit_transport_classes_check.py`; the selector and its checker
are `tgi/port_distinction_exploration.py` and
`tgi/port_distinction_exploration_check.py`. The signed capture, raw state,
collector, verifier, and receipt are bound by hashes in the publication
bundle. The sequence of failed and repaired hypotheses remains available
for replication rather than being suppressed in favor of the final pass.

## 8. Event-level decision trace and causal reading

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

## 9. Independent checking and attack surface

Four layers are checked separately. The Node verifier checks that the
physical capture could have resulted from the recorded state transitions
and that the signed body was not modified. The Python raw-contrast checker
checks edit kind and all alignments. The class checker rebuilds every phase
from original events, including epoch boundaries. The selector checker
recomputes action coverage and deterministic choice. Agreement of all four
is materially stronger than a test that compares only the final selected
port with an evaluator label.

The negative controls illustrate different failure modes. The older signed
panel with no same-action target control remains `NO_PATH` [4]; it cannot
be rescued by post-hoc threshold adjustment. A cross-format positive that
failed the offset rule motivated a changed-atom rule [5], but a different
changed atom at the same offset remains negative. Forged phase or epoch
fields are rejected against the raw history [10]. Duplicate available
actions are rejected before selector ordering [11]. A catalogue containing
only already tried actions returns `NO_UNTRIED_ACTION`; adding an untried
action changes the available experiment, not past evidence. These controls
bind the precise scope of the positive physical result.

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

[1] `KONSEP.txt` and `contracts/M1_INTERVENTION_CORRESPONDENCE_RESEARCH_V1.md`.

[2] E. Leunufna, *NMU: One Character, One Identity*, revision V2, 2026.

[3] E. Leunufna, *Crystal Memory for Native Character-Identity Streams*,
revision V3, 2026.

[4] `evidence/m1_signed_three_port_v2_audit/terminal_receipt.json`.

[5] `evidence/m1_cross_format_edit_v3/terminal_receipt.json`.

[6] `contracts/M1_SIGNED_THREE_PORT_INTERVENTION_PROTOCOL_V1.md`.

[7] `evidence/m1_unlabeled_port_fracture_v1/terminal_receipt.json`.

[8] `contracts/M1_PORT_DISTINCTION_EXPLORATION_V1.md`.

[9] `contracts/M1_SIGNED_PHYSICAL_FRACTURE_PROTOCOL_V1.md`.

[10] `evidence/m1_signed_physical_fracture_v1/terminal_receipt.json`.

[11] `evidence/m1_port_distinction_exploration_v1/terminal_receipt.json`.

[12] `evidence/m1_v4_heldout_transport/terminal_receipt.json`.

[13] `evidence/m1_v4_transport_cost/terminal_receipt.json`.

[14] `evidence/source_distribution_20261004T084916022662Z/result.json`.
