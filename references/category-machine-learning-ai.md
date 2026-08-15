# Category brief — Machine Learning & AI

Four slots, the most of any category. **All four cleared the difficulty gate**, and three of
them produced laws the whole manual now runs on.

| | sub-category | final | what it taught |
|---|---|---|---|
| **ML-1** | Interpretability | 0/5 · 5 good-valid | released on probe evidence, reopened, cleared — the origin of *probe-dead ≠ gate-dead* |
| **ML-2** | Model evaluation & benchmarking | 0/5 · 5 good-valid · avg 0.000 | the probe solved 8/9 sealed instances in under a second; it cleared anyway |
| **ML-3** | Computer vision | 0/5 · 5 good-valid | fully green in **one** run; the orbit-count floor |
| **ML-4** | Interpretability (2nd) | 1/5 · 4 good-valid | *probe measures your own solver, not theirs* |

---

## The category's own hazard: you will be your own third or fourth author

By the fourth slot, similarity is the binding constraint on every new design. ML-3 was the
third ML/AI slot and had to name its disjoint mechanics explicitly in the differentiating-surface
paragraph before it could clear. ML-4 landed in a sub-category **already used by ML-1**.

Both passed — so a repeat sub-category is survivable — but only with loud differentiation:
different counted quantity, different emitted artifact, different semantic core, different
coupling mechanism. See §6. Assume from your second slot onward that the surface, not the idea,
is what gets you blocked.

---

## The law this category owns: probe-dead ≠ gate-dead

This is the most expensive lesson in the corpus and it was learned here, twice.

**ML-2**: the author's own correct-rules + random-restart probe solved **8 of 9 sealed
instances in under a second** — feasible fractions of 0.0027%–2.3%, irrelevant at ~0.1 ms per
draw, and one instance that even defeated unpruned DFS at 12 s. By every local measure the task
was dead. It was pushed anyway as a disclosed-flaw measurement and went **fully green: pass@2
0/2, pass@5 0/5 with 5 good-valid-fails, avg 0.000.** Across seven live trials **no agent ever
reached the exploit** — they all died earlier, failing to model or construct a backtracking
search at all.

> **The probe proves a shortcut EXISTS. The gate measures whether the agent FINDS it.**

**ML-1** is the counterweight and the warning: it was *released* on probe evidence alone, then
reopened and cleared. Three slots were released in a single day on that same probe's evidence;
the one that was actually measured turned out to be hard.

The practical rule, and it costs nothing: when a slot is probe-dead but build-green, **push the
disclosed-flaw measurement PR and let the live gate decide.** Static-stage failures cost no
quota. Disclose the probe finding verbatim in `difficulty_explanation` and the PR body —
measured on the EDA slot, honesty cost nothing at any grader.

See §9.1 for the general asymmetry: *"too easy" is authoritative, "too hard" is weak.*

---

## The sharpening ML-4 added: whose solver are you measuring?

ML-4 cleared at 1/5, and **all four kills landed on a layer the author had explicitly
de-claimed as the easy part.** Agents wrote DFS where the author's hill-climb took 0.5 s.

> **Ask *what will the agent plausibly write, and what does that cost* — never *can my solver
> do this cheaply*.**

Those are different questions with different answers, and the second one is the one that feels
like measurement while telling you nothing. A probe you wrote is a statement about your own
implementation.

---

## What the cleared shapes have in common

**A printed optimum with a construction that is hard to attain.** ML-3's floor is an
**orbit count under a symmetry group** — the agent must derive *which things are the same
thing* (canonical multiset labels) before any counting is possible. That is the
computed-object-identity pattern (§5.2), and it is the most reliable floor shape in this
category because ML domains are full of natural equivalences: augmentations, permutations of
channels, relabelings, symmetric transforms.

**Wrong-belief archetypes built as one parameterised planner.** ML-3's battery was a single
sem-parameterised planner with exactly one belief function swapped per archetype, used
consistently at every site — demand reading, realisation, archive test, self-check. **The
consistency is what makes a slip silent.**

Two measured battery laws from ML-3 worth carrying:

- **Any optimisation gated on a semantic property needs a per-sem flag**, and the battery must
  be **re-run on the selected set after any planner-core change**. A rotation dedupe that was
  sound for shift-invariant canons silently broke the one phase-sensitive archetype and
  corrupted a 150-seed sweep.
- **A resource/assignment archetype cannot die unless the instance space contains the choice it
  gets wrong.** On random instances every class had one admissible resource, so first-fit was
  optimal everywhere. The kill needed *engineered* cross-realisability — a shift-clone resource
  pair differing at one unique cell, planted bait classes, and a budget tightened to the forced
  load. **Verify each archetype's decision actually EXISTS in your shipped instances.**

---

## Category-specific traps

**`ctrf` collapses parametrized tests.** Measured on ML-3: `pytest-json-ctrf` reports 15
collected parametrized cases as "3 tests", and the platform reads `ctrf.json`. Ship **one
explicit test function per graded case** — loop-generated with per-case docstrings passes the
rubric.

**`artifacts` is the agent's PROGRAM, not its output.** ML-3 ships `["/app/plan.py"]`, so the
verifier re-runs the agent's program on sealed instances. This is strictly stronger than
grading one emitted file, and it is the right default in this category because ML tasks
otherwise invite a single-output submission the agent can special-case.

**Round-up archetypes must trust their own formula.** An overclaiming archetype that re-scans
its own sites will catch its own overclaim and never fire. Let it skip the re-scan.

**Record internal alarms per archetype run** — empty candidate set, budget exhaustion — and
classify silent-vs-loud **empirically**. Loud kills still score as valid fails at the gate: two
loud-only archetypes at 12/12 preceded a pass@5 of 0/5.

---

## Pre-build checklist

1. **Which ML/AI sub-categories have you already used?** From your second slot on, differentiate
   loudly: counted quantity, emitted artifact, semantic core, coupling mechanism.
2. **Is there a natural equivalence to exploit?** Orbit counts and canonical-identity floors are
   this category's most reliable shape.
3. **Is the crux a named method or a library call?** ML is the most documented domain there is.
4. **Does your probe solve it?** That is a warning, not a verdict — push the disclosed-flaw
   measurement rather than releasing.
5. **Are you measuring what the agent will write, or what you wrote?**
6. **Is your battery one parameterised planner with one belief swapped**, used at every site?
7. **Does each archetype's wrong decision actually exist in the shipped instances?**
8. **One test function per graded case** — do not rely on parametrization.
9. **Is `artifacts` the agent's program?**
10. **Re-run the battery after any planner-core change**, on the selected set.

---

## Honest limits

Four slots, four clears — no abandoned design in this category to learn from, so the sample is
survivor-weighted on outcomes even though it is rich on within-slot failure.

Two of the four sit in the same sub-category (Interpretability), so the "loud differentiation
works" finding rests on two data points, not a trend. Three sub-categories have never been
attempted here: feature engineering, NLP and language models, ML serving and deployment, and
unsupervised/representation learning.
