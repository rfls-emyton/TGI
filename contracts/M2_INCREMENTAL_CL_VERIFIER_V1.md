# Incremental verification of source-owned C/L port classes

This is a post-implementation validation contract for a verifier execution
change. It preserves the previously defined TGI class decision and does not
introduce a new knowledge operator.

## Derivation and invariant

TGI retains each original NMU occurrence and its ordered source experience.
For a currently live port class `M`, an action `a`, and an epoch beginning at
`e`, the verifier can replay C/L evidence by recurrence rather than scanning
`e..t` again for every phase:

- `C_t(M,a)` is the set of original before-NMU contexts observed with all
  members changed under `a`; each new matching source adds its exact context.
- `L_t(M,a)` counts original all-stable observations under `a`.
- `S_t(M)` contains actions with an all-stable class and a changed port outside
  the class. The comparator for `a` is true iff `S_t(M)` contains a different
  action.
- `Omega_t = |C_t|`; `xi` and winner/revocation rules remain unchanged.

The cache belongs to the exact `(epoch, members)` class. A new class replays
its original sources from the current epoch; an epoch fracture discards the
prior cache. Port signatures still use the full ordered history and cannot
merge identities. The verifier still checks every raw contrast, source,
certificate phase, and final decision. It does not call the certificate
producer.

## Falsifiers and evidence

- Compare the incremental verifier with the frozen exhaustive raw replay on
  randomized Unicode streams, class fractures, response-incidence cases,
  altered certificate phases, and endpoint decisions.
- The complete endpoint certificate must be byte-identical to the public
  baseline under the same original raw sources.
- A growth panel must retain the supported output and exact direct-conflict
  rejection while recording time and peak allocation through at least 1,005
  new-epoch sources. Report actual cost growth; parity alone does not prove
  production-scale economics.

The retained exhaustive checker is a test reference; the optimized checker
is the runtime verifier. Both implement the same source-owned C/L criterion.
