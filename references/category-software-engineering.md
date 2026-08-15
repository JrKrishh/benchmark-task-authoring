# Category brief — Software Engineering

Two slots, both cleared. The first slot in this category was the **first task ever to clear the
difficulty gate** in the whole corpus.

| | sub-category | final | what it taught |
|---|---|---|---|
| **SE-1** | Scripting & automation | cleared | the first clear; the rubric grader is non-deterministic |
| **SE-2** | Version control & repository ops | 1/5 · 4 good-valid · **0 timeouts** | inference-only, search-free tasks can clear; the QC law |

---

## SE-2's finding: you do not need a search space

Most cleared tasks in the corpus make the agent search — over orders, placements, schedules.
SE-2 cleared **without one**. Its difficulty is pure inference: which history is safe to
rewrite, what must be preserved, what has to be added forward. Zero timeouts, because there is
nothing to explore.

> **An inference-only, search-free task can clear the gate.** If your domain resists a search
> space, that is not disqualifying.

This matters practically: search-shaped tasks are the ones that lose trials to the agent clock
(§7). A task with no search has no exposure to that failure mode at all.

---

## The kill that landed, and why it is uncomfortable

**All four of SE-2's kills were the same crux — and it was the author's own misreading.**

The author's floor computation had a bug in exactly the place agents later failed. Closing the
gap an auditor found turned that bug into the task's kill mechanism. The lesson is not
"introduce bugs"; it is that **the place you found confusing is the place agents will find
confusing**, and it deserves to be designed into the task rather than quietly fixed.

---

## The QC law this slot contributed

> **The oracle must be right on every IN-CONTRACT input — not merely on the inputs your
> generator happens to produce.**

A reference that is correct on generated instances but wrong on a legal-but-unusual one will be
caught by QC, not by your own tests, because your tests use your generator. Fuzz the contract,
not the distribution.

---

## Self-containment is this category's specific move

SE-2 ships **no `git` in the image**. The version-control model is rendered in the platform's
own format, and the specification **certifies its divergences from real VCS conventions rather
than hiding them.**

That is the answer to this category's central hazard: software engineering is the most
tool-saturated domain there is. If a real tool can solve your task, it will — the agent
pip-installs whatever it needs (`allow_internet = true` is mandated). **Model the domain
yourself, ship no tool that solves it, and state honestly where your model differs from the
real thing.** Hiding the divergences reads as a bug; certifying them reads as a spec.

---

## The grader warning SE-1 left

The LLM rubric grader is **non-deterministic**. Identical text has passed `review` on one run
and failed it on the next. Do not tune against a single roll, and once a run is green, stop
pushing — you can lose a pass you already earned.

---

## Pre-build checklist

1. **Can a real tool solve this?** In this category, assume yes unless you have modelled the
   domain yourself and shipped no such tool.
2. **Have you certified your model's divergences from the real convention**, or hidden them?
3. **Is there an inference core that does not need a search space?** That is a strength here,
   not a gap — and it removes agent-clock exposure entirely.
4. **What confused you while building?** That is the crux candidate. Design it in rather than
   silently fixing it.
5. **Is your oracle right on every in-contract input**, or only on generated ones? Fuzz the
   contract.
6. **Does a wrong belief make a history illegal**, or merely differently-named?
7. **Are you re-pushing a green run?** Don't — the LLM stages re-roll.
8. **Exact integers in the graded path.**
9. **Blind public sample.**
10. **Sharing a sub-category with an earlier slot?** Differentiate on all four axes.

---

## Honest limits

Two slots and only one with a full recorded pass@5 breakdown, so this brief leans heavily on
SE-2. SE-1's value is historical — it proved the gate was clearable at all — and its detailed
mechanics predate most of the current manual.

Six sub-categories are untouched: feature implementation, refactoring and code modernization,
testing and quality engineering, compilers/interpreters/programming languages, porting and
migration, and web/API/networking software. **Compilers is worth flagging** — it is
tool-saturated in exactly the way this category punishes, and most of its named problems have
textbook answers (§3.1 #5).
