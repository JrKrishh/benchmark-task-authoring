# Category briefs — thin evidence

Four categories with one slot each or none. Each section is short because the evidence is
short. Read the cross-cutting laws in `hardness-laws.md` as your primary guide here; treat
everything below as a single observation unless it says otherwise.

---

## Data Science & Reporting

| | sub-category | final |
|---|---|---|
| **DataSci-1** | Exploratory data analysis | 0/5 · 5 good-valid · **0 infra** |

**Its contribution is the second confirmation of *probe-dead ≠ gate-dead*** (§9.1), and it is
the cleaner of the two. The author's own DFS — pruned with the SPEC's own printed floor —
solved **13/13 sealed instances in 0.1 s**. It was pushed anyway as a disclosed-flaw
measurement, with the probe finding stated verbatim in `difficulty_explanation` and the PR body
the whole way, and cleared at 0/5. **Honesty cost nothing at any grader.**

The kill anatomy is worth copying because it is fully accounted for: three agents wrote
greedy-policy archetypes straight out of the wrong-solver battery — **one explicitly considered
DFS at step 26 and chose greedy because it passed the mild public case**, which is the blind-public
lure working verbatim. One computed carrier counts per-entity instead of globally, an unscripted
trap the cross-entity pollution instances caught for free. One was a heredoc harness wedge, the
predicted ~1-in-5.

**The category hazard:** analysis and reporting are naturally *checked* work — compute these
figures, validate this dataset. That is a checked predicate (§3.1 #1). This slot escaped by
making the agent construct an audit plan under interacting constraints rather than compute a
report.

**Also from this slot:** an order-independent end state cannot produce deep doom. If every
correct plan reaches the same end state, ordering changes only local legality, a fatal move
strands something immediately, and backtracking is free. Clean grading and deep doom are in
direct tension.

---

## Regulated Knowledge Work & Business Operations

| | sub-category | final |
|---|---|---|
| **RegOps-1** | Cadence planning | 0/5 — **after being blocked at 2/2** |

**Its contribution is the fourth repair type: the data-only rebuild** (§6.4, §9.2). The
semantics were left completely intact. What changed was the sealed set: reproduce the archetype
that solved the task, measure its per-instance rate over a large sample, then regenerate
instances driving that rate toward zero — validating every candidate through the *real*
reference and the *real* verifier. Mean rate went **77% → ~6–8%** over 70 candidates.

> **This is the only repair that leaves your core untouched.** Reach for it when your design
> survives the kill-list but the shipped instances were simply too kind — and only then. A shape
> that lands on a kill-list row cannot be repaired with data.

**The category hazard:** business-operations framing invites checklists and compliance rules —
breadth of independent conditions, which is kill-list #7. The escape is the same as everywhere:
a constructed schedule under interacting constraints, not a validated one.

Four sub-categories untouched: finance and quantitative workflows, legal and compliance,
medical and clinical workflows, personal-assistant productivity.

---

## Systems Infrastructure & Operations

| | sub-category | status |
|---|---|---|
| **SysInfra-1** | Shell & environment configuration | ⚠️ **paused mid-build — never reached the gate** |

**No slot in this category has ever been measured at the difficulty gate.** Everything here is
`design-kill` evidence: killed by argument or local measurement, never by the platform.

**The one law it produced, and it is a good one:**

> **Refutation must be SHARED and LATE.** A wrong choice that is refuted locally and
> independently costs the agent exactly one retry. It must be irrefutable until the **last stage
> of its block**, or your search space is `options^blocklength` only on paper.

**Measure refutation lag twice** — checkpoint lag *and* prune lag. Both measured 3 and uniform
on this slot, which made backtracking cheap.

The decisive kill was a companion measurement: **measure the reference planner's cost against
the JOINT space.** Removing the gradient an attacker climbs does not stop it enumerating — you
have to show the joint space is *unreachable*, not merely *un-guidable*. One collapsing bit per
block made per-block hardness trivial jointly. (The kill-gate NO_GO that finally landed had two
of its own clauses mutually exclusive by construction — a reminder to check your own gate's
consistency.)

**Treat this category as unproven.** It has consumed a slot without producing a measurement.

---

## Debugging & Repair

| | status |
|---|---|
| — | ⚠️ **never assigned. Zero slots, zero measurements.** |

Everything here is `prospective`.

**The strongest untested candidate is the repair mold** — sometimes called "green is the trap":
ship a pipeline that *looks* working, carrying one visible bait defect and one or more dormant
ones, and require the agent to produce a correct artifact rather than a passing test run.

⚠️ **One caution about that playbook**: its "a visible rule means solved" claim is **overstated**
— a Build-and-Release task is a measured counterexample that cleared at 0/5 with its rules
visible. Do not treat visibility alone as disqualifying.

The category's structural risk is that debugging is *definitionally* a checked activity — find
the bug, fix the test. To carry difficulty it needs a **constructed** repair whose correctness is
not verifiable by re-running the suite the agent can already see. The blind-sealed-set discipline
matters more here than anywhere.

---

## What to do in a thin category

1. Lean on the cross-cutting laws — the kill-list (§3.1) and the proven floor shapes (§3.2) are
   category-independent.
2. Expect to spend your first slot learning the category rather than clearing it, and budget for
   a redesign.
3. Write down what fails. A negative result in an unmeasured category is worth more than a clear
   in a well-mapped one.
4. Check the two structural questions first: **is the natural framing a checked predicate?** and
   **does the natural structure factorise?** In thin categories, those two account for most
   deaths.
