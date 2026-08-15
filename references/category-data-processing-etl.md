# Category brief — Data Processing & ETL

Three slots, **all three cleared** — and this category produced more of the manual's core laws
than any other. If you get an ETL slot you are working in the best-documented territory in the
corpus.

| | sub-category | final | what it taught |
|---|---|---|---|
| **ETL-1** | Media data processing | 1/5 · avg 0.200 | four PRs; the **de-disclosure law** (4/5 → 1/5 on a prose cut alone) |
| **ETL-2** | Text processing | 0/5 · 5 good-valid · avg 0.000 | the **factorising-predicate law** and the union-of-boxes repair |
| **ETL-3** | Streaming data processing | 0/5 · 5 good-valid · avg 0.000 | the **self-cancelling-rule law**; four cores before one held |

---

## The category's own hazard: everything here decomposes

ETL is *definitionally* per-record work. Rows, events, fields, batches — the domain hands you a
structure that factorises, and a legality predicate built on it is measurable one coordinate at
a time (§5.2). This is why the factorising-predicate law was discovered here rather than
anywhere else.

**ETL-2 is the cleanest A/B on it in the whole corpus** — same fiction, same artifact, same
floor, same grading, same generator, *only the requirement changed*:

| version | requirement | result |
|---|---|---|
| v1 | disjoint per-field banks → admission is a conjunction of independent equalities | **2/5 solved**, `difficulty_crux = NA` |
| v2 | **one shared pool** → admissible state is a *union of boxes* | **0/5 · 5 good-valid · avg 0.000** |

In v1 the cheapest route was probing one field at a time: ~18 decodes, 0.31 s against the
reference's 0.16 s. **A 2× ratio no cap, scaling or length change can separate.** In v2 per-field
probing is wrong in *both* directions — it accepts configurations that grade wrong and rejects
valid ones — while the union stays exactly computable in a bounded number of cheap passes, so
exactness survives. Three of five gate agents then converged on the exact archetype `task.toml`
named as the crux.

> **The exactness corollary, landed verbatim three times: the property you chose to make your
> floor provably exact is often the very thing that makes it cheaply measurable.** ETL-2's
> disjoint banks were chosen deliberately to make the exactness proof easy — the proof was the
> leak. **When your exactness proof feels easy, run the factorising test immediately.**

The false defence to watch for: *"the rules interact because F1 and F3 both read what F2
resolves."* A **shared input is not an interaction** — resolve the shared object once and each
condition is separately decidable.

---

## The de-disclosure law was measured here first

ETL-1 took four PRs. Its decisive experiment: **the same core, with only SPEC prose cut, moved
4/5 solved → 1/5.** `difficulty_crux = NA` is the tell that agents never reached your decision
point.

State **premises**; never state **inferences**. See §4.1. Two further findings from that slot:

- A **13-agent panel recommended RELEASE and was wrong** — the slot cleared. Panels kill designs
  cheaply; they do not deliver verdicts.
- **A mutation battery proves a belief is PUNISHED, not that it is HELD.** Kill-given-belief and
  belief-rate are unrelated quantities (§5.5).

---

## The trap ETL-3 found: self-cancelling rules

ETL-3 needed four semantic cores. The one that failed most instructively added a rule that
*lowered demand* on the very resource its floor was defined over. Measured: **0 of 300
candidate instances stayed minimal** — the rule made the hard instances trivially optimal.

> **Before adding any rule, ask: does this lower demand on the resource my floor counts?**
> If yes, the rule cancels the floor.

ETL-3 also carries the sharpest self-inflicted lesson in the corpus. What finally cleared it was
**the platform's own pass@2 suggestion**: one mis-calibrated threshold percentile (0.55 →
0.08–0.18) took the intended carrier from 1/11 to 10/11. The carrier had been written into
`task.toml` as the crux all along and was inert at the shipped calibration.

> **Read your own `task.toml` disclosure adversarially before building another core.** Two
> cycles were spent inventing new semantics when the named carrier was simply mis-tuned.

---

## What the cleared shapes share

**A union or a fold, not a product.** All three winners make the admissible set something the
agent must *derive* — a union of boxes, a replayed hidden state, a stage-consuming fold — rather
than a per-item range it can check independently.

**Recovering hidden state by replay** is this category's most natural constructive core, and it
appears in every clear. The agent reconstructs what the pipeline *must have done* rather than
validating what it did.

**Exactness and difficulty as one knob** (ETL-2): the same structural choice that makes the
floor exactly computable can be tuned to make the natural measurement wrong. When they are the
same knob, you can move difficulty without giving up exact grading.

**The blind public sample.** ETL-2's public case uses one register with no variation, so the
exact-state and admissible-state sets coincide there — the sample passes for a wrong belief and
the sealed set does not. Every wrong-belief archetype must be byte-identical to the reference
on the sample, asserted (§4.3).

---

## Pre-build checklist

1. **Does your legality predicate decompose over independent fields?** It probably does — this
   is the category where it hides best. Run the pre-build test: change ONE field of a true
   configuration and see whether the graded property moves.
2. **Was your exactness proof easy?** Then run the factorising test immediately.
3. **Are you calling a shared input an interaction?** It is not.
4. **Does any rule lower demand on the resource your floor counts?** Self-cancelling.
5. **Is the carrier named in `task.toml` actually live at your shipped calibration?** Measure
   its kill rate before designing a replacement core.
6. **Is the public sample blind** — does it pass for every wrong-belief archetype?
7. **Are you stating premises or inferences?** `difficulty_crux = NA` means you stated too much.
8. **Does the agent RECONSTRUCT hidden state**, or merely validate visible state?
9. **Have you confused kill-given-belief with belief rate?**
10. **Is the union derivable in a bounded number of cheap passes**, so exactness survives?

---

## Honest limits

Three slots, three clears — but ETL-1 needed four PRs and ETL-3 needed four semantic cores, so
"cleared" understates the cost. Budget several cycles here.

All three sub-categories used so far (media, text, streaming) are transformation-shaped. Five
remain untouched: ETL pipelines proper, file-format parsing and serialization, tabular
transformation, data validation, and geospatial processing. **Data validation in particular
should be approached carefully** — it is a checked predicate by name (§3.1 #1).
