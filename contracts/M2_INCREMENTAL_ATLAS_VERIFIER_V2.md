# Incremental verification of phase-bound response atlas cells

This is a post-implementation validation contract for runtime verification
cost. It preserves the existing TGI atlas decision, source ownership, and
independent producer/verifier boundary.

For each original raw event, append the per-port changed/stable observation
to the action's complete response trace. Classes remain the equivalence
partition of those full traces; no port identities or NMU occurrences are
pooled. For an unchanged live `(action, members)` class, add only the new
event's C/L context to its support, all-changed, all-stable, control, and
comparator state. A newly appearing class replays every original event to
establish its birth and history. Omega, opposition, xi, admitted roles, and
revoked roles are computed with the same criterion as exhaustive replay.

The verifier must still check every phase and the final decision against
the raw input. Its implementation does not call the atlas producer. A frozen
exhaustive verifier remains in the test suite; randomized Unicode streams,
fracture/revocation, forged phases, and held-out endpoint certificates must
agree with it. At least 1,005 new-epoch sources must produce an identical
complete endpoint certificate against the published predecessor. Measure
decision and verification cost on the same sources. This is an efficiency
change, not a new knowledge or generalization result.
