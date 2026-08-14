# Category brief — Mathematics & Formal Reasoning

Read this when a slot lands in this category. It is the entry point; the evidence for anything
cited here lives in `hardness-laws.md` at the section given.

Two slots have been assigned in this category and **both cleared**:

| | sub-category | final | cost |
|---|---|---|---|
| **Math-1** | Computational Linear algebra | 0/5 solved · 5 good-valid · avg 0.000 | 3 designs killed pre-build, then one classification fix |
| **Math-2** | Computational Geometry | 2/5 solved · 3 good-valid · avg 0.400 | 4 CI runs, one variable each |

---

## The category's own law

**In clean mathematics the natural way to specify a transform is to write it down — and
writing it down performs the derivation for the agent.**

Every other category can state its rules in prose without handing over the answer. This one
cannot, because here the rule *is* the answer. That asymmetry generates most of what follows,
and it is why the printed-formula law (§4.2) was first measured in this category rather than
anywhere else.

**Corollary, measured twice on prototypes: optimization margin is dead here.** A min-degree
heuristic hit the optimum on **399/400** min-fill instances; textbook Paar landed within **±1
operation** of strong search on min-XOR SLP synthesis. Clean math has clean heuristics — never
build a task whose difficulty is "beat the obvious algorithm by a margin".

---

## The band you are aiming for

This is the synthesis the two slots produce together, and it is the most useful thing in this
brief. **De-disclosure and coaching pull in opposite directions on two axes at once:**

| | difficulty | implementation volume |
|---|---|---|
| de-disclose the transform | ▲ up | ▲ up (agent must derive it) |
| coach the working method | ▼ down | ▼ down |

Push disclosure and you gain difficulty but risk trials running out of agent clock. Add
coaching to recover the clock and you give the strategy away. Clearing means finding the
narrow band between them:

> **De-disclosed core · always-emit discipline · no method coaching.**

Math-2's four-run ladder maps that band exactly — see §4.4 for the table. The operational
distinction:

| Safe — about the **deliverable** | Leak — about the **method** |
|---|---|
| "emit your best artifact even if you cannot certify optimality" | "get something running end-to-end early, then refine" |
| "a plan is scored even when incomplete" | "start with the simplest case and generalise" |

One process-strategy sentence was worth **more than the entire de-disclosure gain** (0/5 →
4/5 solved). State what to emit and when it counts; never state the working strategy.

---

## Timeouts bite from both ends here

Both slots lost trials to timeouts, by **opposite mechanisms**, and both kinds count for
*neither* side of the gate arithmetic. In a category where the agent may have to derive a
transform before it can write a line, expect both.

| | cause | symptom | fix |
|---|---|---|---|
| **infra / setup** (Math-1) | `n_items × per_item_cap` exceeded the verifier budget | pytest never finishes → no `ctrf.json` → real analytical failures logged as missing infrastructure. First pass@5 was **0/5 solved and still blocked** on 4 infra | arithmetic: cap 120 s → 25 s, budget 600 s → 900 s, `TimeoutExpired` → clean `pytest.fail`. Result: 1 valid + 4 infra → **5 valid + 0 infra**, solve rate unchanged at 0 |
| **in-progress** (Math-2 run 2) | implementation volume exceeded the **3600 s agent cap** | one trial spent the hour in 7 LLM calls (last four 688 s, 530 s, 748 s, 1070 s) and never wrote its deliverable | cut implementation *volume*, never the semantic core. The cap is project-wide and not tunable |

**Difficulty was never the problem in either case. Classification was.**

Cheap habit that would have caught both: **read `low_timeout` per trial before concluding
anything from a pass@5 number.** On Math-2 run 2 the two countable fails were exactly the two
trials with `low_timeout` PASS.

Math-2 designed the hazard out rather than managing it: **12 items × 40 s = 480 s against a
900 s budget, worst reference item 0.46 s.** Compute that product before you ship, and
disclose the cap in `instruction.md` and `verification_explanation`.

---

## Instance selection: traps must be discovered, not designed

Hand-designing trap instances **failed twice** on Math-1 — the author kept missing alternate
supports that quietly rescued a span meant to be fatal.

What worked, and the numbers worth reusing as bars:

- **Battery as fitness function** over a randomized instance search: hit rate ~**1.4%**, and
  **8 robust instances found in ~600 tries**.
- **Prove structure, not luck:** the surviving instances failed the gate attacker under
  **100% of 25 randomized candidate orderings each**.
- Battery archetypes that earned their place: macro-collapse + pairwise fusion without
  lookahead (10/12), phase-separated (11/12), eager-delete (9/12), complete DFS refusing the
  freeze case (10/12).

See §6.3 for the general law. The mandatory member applies here as everywhere: **correct rules
+ naive search**, under the real disclosed cap.

**Red-team to kill designs cheaply, never for final verdicts.** Attacker panels killed three
Math-1 designs for the cost of tokens rather than build-hours plus billed CI — but the judge
red-teamed the design that ultimately cleared as **NO-GO at P ≈ 0.17–0.20**, and was wrong.

---

## The three shapes that died here, and why

All three passed every quality gate and were **solved 2/2 at pass@2** — the screen doing its
job at the cheapest possible price.

| shape | why it died |
|---|---|
| integer-kernel certificate | A library call returns the saturated integer kernel directly — one line. ~10 min per agent |
| factor a matrix into restricted generators | The commutator identity at its heart **is textbook**. The "construction-hard not knowledge-hard" reframe was wrong: the author hit a staging bug while prototyping; the model did not. 18 and 40 min |
| wide multi-field audit, ~300 sub-results | Once the kernel is right, everything downstream is mechanical post-processing. Breadth is not depth. 19 and ~50 min |

Two kill-list rows (§3.1 #5 named-crux/library-returned, #7 breadth of independent rules) were
each confirmed here. And note the structural constraint: **you cannot remove the symbolic-math
library from the image** — `allow_internet = true` is mandated, so the agent pip-installs it.

---

## Build technique specific to this category

**Exact integers, or do not ship.** Math-2's enabling move was restricting to 90° folds:
placements become products of quarter turns composed along the tree in parent frames, pure
integer arithmetic, evaluated incrementally. Free regions ship as **stacks of integer
intervals — never as a raster.** Floats are a rejection risk here above all other categories.

**The cost axis is dead on interval-walk shapes** (design-kill, measured). Materialising the
channel as a raster instead of walking intervals gives only a **3.7× ratio at ×20 scaling**
(5.5 s against a 40 s cap). Reaching the cap needs roughly ×50, where one item's raster is
~6.5 GB against a 2048 MB container — **the agent OOMs rather than failing slow, which is a
memory limit dressed as difficulty and reads as gaming.** If de-disclosure does not move the
gate, cost is not your fallback; the remaining lever is making the test of *one candidate*
expensive, which is a new semantic core rather than an edit.

**Generator hygiene that cost real hours:**

- **Never hand-write target matrices.** 5 of 18 transcribed by hand had `det ≠ ±1` —
  non-unimodular, therefore unreachable. Generate programmatically, then verify determinant,
  protected rows, and oracle-solvability.
- Feasibility needs non-protected slots spanning **≥ 2 banks**, or same-bank pairs can never
  be combined.
- Keep walk length and coefficients small, or coefficient splitting blows schedule length into
  the millions.
- Euclid needs exact round-to-nearest `(2*num+den)//(2*den)`; floor division can fail to
  progress and loop forever.
- **`sympy.rank()` explodes at ~26×28 (10.5 s) while SNF / `invariant_factors` stay ~0.01 s** —
  derive rank from SNF at scale.

---

## Pre-build checklist

Every item is a measured failure from one of these two slots.

1. **Is the crux a library call?** Search for it before designing around it.
2. **Is the crux named in the literature?** Then it is knowledge, not difficulty.
3. **Are you grading a margin?** Dead here — 399/400 and ±1 op.
4. **Can the spec state the rules without printing the transform?** If the only honest
   specification is the matrices themselves, you will leak the answer. Find a fold you can
   state in words.
5. **Does `instruction.md` contain any sentence about *how to work*?** Delete it.
6. **Is every graded number an exact integer?**
7. **Does `n_items × per_item_cap < verifier timeout_sec` hold, with margin?** Compute it, then
   disclose the cap.
8. **Is the implementation volume inside 3600 s** for an agent that must derive the fold
   itself? Time your reference honestly, then assume the agent is slower.
9. **Were your trap instances discovered by a battery-scored search, or designed by hand?**
10. **Does the battery include correct-rules + naive search** under the real cap?

---

## Honest limits

**n = 2, and both cleared** — so this brief has no example of a slot in this category that was
abandoned. It is rich on failures *within* those two journeys and survivor-weighted on
outcomes.

Math-2's run 3 changed **two** variables at once (an encoding change alongside the instruction
rewrite), so the coaching effect is attributed rather than isolated. Recorded as a methodology
fault worth avoiding: one variable per run, or the ladder stops being readable.

The disclosure axis is measured cleanly on one geometry core. Whether the *magnitudes* transfer
to the five sub-categories never attempted here — symbolic computation, number theory and exact
arithmetic, combinatorics and enumeration, algorithms and optimization theory, formal
verification — is untested. Those five also carry clear similarity margin.
