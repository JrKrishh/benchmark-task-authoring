# Category brief — Build, Dependency & Release Management

Two slots, both cleared. One of them produced the **ceiling law** — the most important negative
result in the corpus, and the reason the printed-optimum skeleton has a known upper bound.

| | sub-category | final | what it taught |
|---|---|---|---|
| **Build-1** | Cross-compilation & platform targeting | 0/5 | went **2/2 → 0/5 by swapping only the semantic core**; the ceiling law |
| **Build-2** | Container builds | cleared | v2 after a 3-agent red-team; the inert-stratum law |

---

## The ceiling law — measured here, applies everywhere

Build-1's first version came back **pass@2 2/2 solved, `difficulty_crux = NA` twice.**

> 🚨 **Fairness + a closed-form floor + small instances JOINTLY cap difficulty at "will the
> agent bother to backtrack".**

Each term does its own damage:

- **Fairness** forces every graded rule to be stated, so a transcribing agent gets a perfect
  legality oracle.
- **A closed-form one-pass floor** plus per-instance attainability certification forces the
  placement layer to be cheaply solvable *by code the author writes* — so the agent solves it
  too.
- **Small instances** make the residual search enumerable.

What is left is conception, never computation. **You cannot engineer that to 0/5; you can only
hope for it.**

Two corollaries, both measured:

**Placement scarcity cannot be added without announcing itself.** Fairness requires you to state
the constraint — and stating it tells the agent that placement is the crux. The fix that makes
greedy terminal is the same fix that warns against greedy.

**A stated rule is worth its MEASURED wrong-belief rate — and here that was 0/8**, on rules
harder than anything a 9-agent hardening panel could add.

**The escape, and it is narrow:** difficulty that is *announced but not crossable*. The two
corpus tasks that escaped did it with a narrowing belief that hid the correct move, or with
extreme feasible density (5.97e-12). Build-1 itself escaped by **swapping only the semantic
core** — same everything else, 2/2 → 0/5.

⚠️ **The hazard that comes with the escape:** hardening toward search converts good-valid-fails
into 3600 s timeouts, which score as in-progress and count for **neither** side. A genuinely
hard task can become ungatable (§7).

---

## The direction that matters on "probe-dead ≠ gate-dead"

This category is where the distinction gets sharp:

> *Probe-dead ≠ gate-dead* says never release on your **own local probe**. It does **not** apply
> when the **platform** measures 2/2 solved. That is the authoritative instrument saying *too
> easy*, and no amount of local re-measurement overturns it.

---

## Build-2's contribution: the inert-stratum law, and red-teaming that worked

Build-2 shipped **v2 after a 3-agent red-team judged v1 a coin flip.** The panel earned its
keep here — killing a design pre-build for the cost of tokens.

Its law: a **stratum of the design can be inert** — present, plausible, and doing no work at the
gate. Ship a stratum only if you can name the instance that punishes getting it wrong (which is
the same discipline as the dead-coverage law, §8.5).

**The measured trap this slot left for everyone else:** Build-2's worked example let the winning
agent converge by **diffing intermediates** rather than deriving. A worked example is a
convergence oracle (§4.3). The winning trajectory logged 45× "DERIVATION", 88× "diff", 97×
"verify".

> **Ship the public instance with no derivation and no expected answer, and assert that in a
> spec check.**

---

## Category-specific mechanics

**The Dockerfile is a minefield for the static gate.** The stock Dockerfile's own **comments**
contain `solution/`, `tests/` and `test.sh` — all forbidden substrings the static stage matches
*even inside comments*. Rewrite them. Also: `tests/test.sh` ships CRLF; rewrite to LF and verify
the **committed blob**, not your working copy.

This category touches those files more than any other, so the three greps in `ci-stages.md` are
not optional here.

**Build reproduction is a natural shape** — rebuilding artefacts that match published digests —
and it is constructive rather than checked, which is why it survives. But the digest chain means
one wrong convention silently changes everything downstream, so your differential fuzz must
include every implementation whose output you ever quote.

---

## Pre-build checklist

1. **Do fairness + a closed-form floor + small instances describe your task?** Then you are at
   the ceiling. Only an uncrossable narrowing belief or extreme density escapes it.
2. **Does stating your scarcity constraint announce the crux?** It usually does — that is the
   corollary, not a bug you can fix.
3. **Have you measured your stated rule's wrong-belief rate**, rather than assuming it?
4. **Are you hardening toward search?** That converts countable fails into timeouts.
5. **Did the platform say 2/2?** That is authoritative. Do not re-measure locally to argue.
6. **Is any stratum of your design inert** — present but punished by no instance?
7. **Does your public example show a derivation or an expected answer?** It is then an oracle.
8. **Have you grepped the Dockerfile for the three forbidden substrings, comments included?**
9. **Is `tests/test.sh` LF in the committed blob?**
10. **Does your fuzz include every implementation you quote a number from?**

---

## Honest limits

Two slots, two clears, but Build-1 needed a full semantic-core swap after a 2/2 and Build-2
needed a v2 after a red-team. Neither cleared first time.

The ceiling law is stated from one measured instance plus corroboration from tasks that escaped
it — strong, but it is a claim about a *family*, and the family is exactly the skeleton most of
the corpus uses. Treat it as the bound on your default shape.

Five sub-categories are untouched: build system configuration, dependency and lockfile
resolution, CI/CD pipelines, package publishing, and release artifacts. **Dependency and
lockfile resolution is worth flagging** — SAT-solver territory, and `allow_internet = true` means
the agent installs one.
