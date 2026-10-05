# M2 direct conflict under a revoked response role

## Derivation

TGI must stop when a claimed action would leave a crystallized path without a
single source-bound successor. NMU identity stays one Unicode scalar per ID.
The phase-bound C/L atlas can revoke a response role when changed and stable
experiences oppose one another. Role revocation blocks traversal; it must not
erase the raw fact that two live sources at the exact same before state and
action have different after states.

## Contract

After source-bound state selection and current atlas-role lookup, when the
current port has no admitted role for an action, inspect only its live raw
sources with exactly the current before string and the same raw action. If at
least two distinct after strings occur, the step is `OBSERVED_CONFLICT`, with
sorted IDs of all matching direct sources, empty output, no mode and no suffix.
The result is `OBSERVATION_CONTRADICTION` at that step. Otherwise it remains
`NO_ROLE` and `NO_PATH`. No role is restored and no traversal is attempted.
The independent verifier must derive the same decision directly from source
observations, without calling the producer.

## Falsifiers

- A revoked role with two divergent direct outcomes yields the conflict status
  and a valid independent certificate after neutral append.
- A role missing for an unobserved action remains `NO_PATH`.
- A missing bridge remains `NO_PATH`; unrelated or merely similar before
  strings never suffice for the direct conflict label.
- Changing a source outcome, dropping one conflict source, or forging the
  certificate invalidates verification against the current raw organization.

This contract classifies an observed local contradiction. It does not infer a
general rule from the contradictory sources or relax the C/L crystal gate.
