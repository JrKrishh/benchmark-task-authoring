# Category brief — Security

Three slots, **all three cleared**. Two of them were the first same-author, same-sub-category
pair ever claimed *simultaneously*, which forced a discipline this category now depends on.

| | sub-category | final | what it taught |
|---|---|---|---|
| **Sec-1** | Security hardening | 0/5 · 5 good-valid | green in one run; the rate-based robustness law |
| **Sec-2** | Digital Forensics | 1/5 · 4 good-valid | seven CI runs, only the first about difficulty; *advisories are latent blocks* |
| **Sec-3** | Digital Forensics | 1/5 · 4 good-valid | *dead coverage* — a mutation battery over rules is not coverage over instances |

---

## The category's own hazard: forensics is magnetically a CHECKED predicate

Every natural forensics framing is *"identify the evidence"*, *"find what was deleted"*,
*"determine who did it"*. All of those are **checked predicates** and all of them are dead
(§3.1 #1, §5.1). The verifier can produce the answer by simulation, so there is nothing the
agent must construct.

Both forensics slots cleared only by forcing a **constructed object**: a reconstruction, a
reconciled timeline, an allocation map — something a wrong belief makes *illegal* rather than
merely mislabelled (§3.1, legality-not-naming).

The second magnet is just as strong: **evidence validity naturally decomposes into per-field
checks**, which is the factorising-predicate law (§5.2) in its most seductive form. If your
admission test is "field A valid AND field B consistent AND field C in range", the agent probes
one coordinate at a time. Run the pre-build test before committing.

---

## Twin slots: the territory split

Sec-2 and Sec-3 were claimed the same night in the *same sub-category*. Whichever opened a PR
first would become the similarity denominator for the other, so distinctness had to be designed
in **before either draft began**, not argued afterwards.

The split that worked — disjoint families, assigned up front and treated as binding:

| | family |
|---|---|
| Sec-2 | **storage-side**: filesystems, allocation chains, deleted-data reconstruction, journal replay |
| Sec-3 | **event-side**: multi-source timelines, clock-skew reconciliation, ordering and attribution |

Measured outcome: twin cosine **0.078** (corpus median), core sections orthogonal, both
cleared. A vocabulary partition was also ratified — each twin owned distinct nouns and neither
could use the other's.

> **If you hold two slots in one sub-category, assign disjoint families before drafting.**
> Counted quantity, emitted artifact and semantic core must all differ — not just the story.

⚠️ **The measured vocabulary trap:** Sec-1's shipped `task.toml` carries the author's own
house-recipe sentences. Any later build that reuses those phrasings gets seen by the task-text
cosine. **Rephrase the graded prose fields every time.**

---

## The two laws this category contributed

### Advisories are blocks that have not fired yet (Sec-2)

Sec-2 took **seven CI runs, and only the first was about difficulty.** Three of the four
post-difficulty blockers were **advisories that an earlier run had graded PASS** — non-blocking
notes that later became hard failures.

> **Treat every advisory as a block with a delay.** Fix it the run you see it, not the run it
> stops you.

It also carries the **AVA loose/strict oscillation**: `sound_verifier` complains the verifier is
too loose, you tighten it, then `no_false_rejection` complains it is too strict. The fixed point
is *enforce strict AND state the strictness in the spec* — the pair only stabilises when the
spec and the verifier agree at the strict end.

### Dead coverage: rule coverage is not instance coverage (Sec-3)

Sec-3's QC mutated a SPEC rule and the mutant scored **13/13 — passing 9 archetypes, a
43-bundle fuzz and 48/48 corruption checks.** The rule was stated in the spec and tested
nowhere.

The mechanism is worth internalising because it is invisible: **the reference and the grader
both hardcoded a value the task tells agents to read from the instance.** Two author-written
components agreeing is not evidence; they shared the omission.

> **Every stated rule needs a shipped instance that punishes getting it wrong.** And **your own
> constants are where it hides** — a reference that hardcodes a per-instance input cannot test
> that input.

See §8.5. This is the same failure family as the harness-is-not-the-task law (§ci-stages):
routes that agree with each other prove nothing if they share an omission.

---

## What Sec-1 added: robustness is a rate, not a property

Sec-1 went green in a single run. Its transferable finding is that a hardening task's
difficulty should be expressed as a **rate over a population of attempts**, not as a single
pass/fail property — which is what makes the floor countable and the grading independent of any
one attack path.

---

## Category-specific notes

**Forensics data is naturally stratified — use it.** Sec-2's local probe went 0/2 with zero
exceptions, and the failure pattern *was* the diagnosis: agents failed exactly the
ancestor-delta images and passed the sub-range ones. Stratifying the sealed set per designed
axis turns a pass@ result into a per-axis readout instead of a single number.

**Security vocabulary is a rubric hazard.** This category's natural nouns — credentials,
attacks, exploits — sit close to graded criteria about reward hacking and anti-cheat. Keep the
task's domain vocabulary separable from the vocabulary the rubric uses about *your* task.

---

## Pre-build checklist

1. **Is your core "identify / find / determine"?** That is a checked predicate. Force a
   constructed object.
2. **Does evidence validity decompose per field?** Then it factorises — repair with a union of
   boxes or move difficulty onto computed identity (§5.2).
3. **Does a wrong belief make something ILLEGAL**, or only misnamed?
4. **Holding two slots in one sub-category?** Assign disjoint families before drafting, and
   partition the vocabulary.
5. **Have you rephrased the graded prose fields** away from your previous tasks' sentences?
6. **Is every stated SPEC rule punished by at least one shipped instance?**
7. **Does your reference or grader hardcode anything the task tells the agent to read?**
8. **Are you treating advisories as passes?** They are blocks with a delay.
9. **Is the sealed set stratified per designed axis**, so a probe result reads as a diagnosis?
10. **Does the verifier enforce exactly what the spec states** — strict, and stated (§8.3)?

---

## Honest limits

Three slots, three clears, but two are the same sub-category and were designed as a
deliberately-separated pair — so the "forensics works" evidence is really one design problem
solved twice with enforced distinctness.

Sec-2 needed seven runs. Its difficulty landed on run one; the remaining six were spent on
verifier strictness, advisories and coverage. Budget accordingly: in this category the gate is
rarely what costs you.

Six sub-categories have never been attempted here: cryptography, cryptanalysis, authentication
and authorization, vulnerability analysis, exploit and CTF tasks, reverse engineering, and
network forensics.
